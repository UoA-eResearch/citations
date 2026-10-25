"""Catalogue-free local-event proxy (plan section 2), month by month across all networks.

  proxy.py table          -> data/taup_p.npz: first P-type arrival (iasp91) on a distance x depth grid
  proxy.py run [WORKERS] [VARIANT]
                          -> data/proxy[_<variant>]/<YYYY>-<MM>.parquet: tid, hour (hours since epoch), n_pair, n_local;
                             nbr_<YYYY>-<MM>.parquet (neighbours with picks within 50 km); for the 100 validation
                             days, valpairs_<YYYY>-<MM>.parquet (every local-event pair: tid, t0)
                             VARIANT sp5: S-P 0.8-5.0 s; conf07: confidence >= 0.7
                             data/proxy_counts.csv: per month, picks in/after merge/after mask, pairs, local pairs

Per month:
  1. picks of stations in stations.parquet; per station and phase, picks within 0.5 s (any channel) merged, keeping
     the highest confidence;
  2. picks within +-60 s of the predicted first P arrival of any ComCat global M >= 4.5 event more than 1,000 km from
     the station removed;
  3. P-S pairs: each P with the first S 0.8-8.0 s later at the same station, no P between (up to 3 picks ahead);
  4. t0 = tP - 1.37 (tS - tP);
  5. local-event pair: >= 2 other stations within 50 km with a pair whose t0 is within +-2.5 s.
"""
import csv
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
OUT = D / "proxy"
SP_MAX, CONF_MIN = 8000, 0.5
R_EARTH = 6371.0088
DEPTHS = np.array([0, 15, 35, 70, 150, 300, 500, 700], float)
DISTS = np.arange(0, 180.01, 0.25)


def table():
    from obspy.taup import TauPyModel
    m = TauPyModel("iasp91")
    T = np.full((len(DEPTHS), len(DISTS)), np.nan)
    for i, z in enumerate(DEPTHS):
        for j, d in enumerate(DISTS):
            a = m.get_travel_times(source_depth_in_km=z, distance_in_degree=d,
                                   phase_list=["p", "P", "Pdiff", "PKP", "PKIKP", "PKiKP"])
            if a:
                T[i, j] = min(x.time for x in a)
    np.savez(D / "taup_p.npz", T=T, depths=DEPTHS, dists=DISTS)
    print("table", np.isnan(T).sum(), "gaps", flush=True)


def ptime(dist_deg, depth_km, tab):
    T = tab["T"]
    zi = np.clip(np.searchsorted(DEPTHS, depth_km) - 1, 0, len(DEPTHS) - 2)
    wz = np.clip((depth_km - DEPTHS[zi]) / (DEPTHS[zi + 1] - DEPTHS[zi]), 0, 1)
    x = np.clip(dist_deg / 0.25, 0, len(DISTS) - 1.001)
    j = x.astype(int)
    wx = x - j
    t0 = T[zi, j] * (1 - wx) + T[zi, j + 1] * wx
    t1 = T[zi + 1, j] * (1 - wx) + T[zi + 1, j + 1] * wx
    return t0 * (1 - wz) + t1 * wz


def gc_deg(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    h = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return np.degrees(2 * np.arcsin(np.sqrt(np.clip(h, 0, 1))))


def stations():
    s = pd.read_parquet(D / "raw" / "stations.parquet", columns=["id", "latitude", "longitude"])
    return s.groupby("id")[["latitude", "longitude"]].median()


def month(ym):
    y, m = ym
    out = OUT / f"{y}-{m:02d}.parquet"
    if out.exists():
        return None
    files = sorted(D.glob(f"picks/network=*/year={y}/month={m}.parquet"))
    empty = {"month": f"{y}-{m:02d}", "picks": 0, "picks_known_station": 0, "after_merge": 0, "after_mask": 0,
             "pairs": 0, "local_pairs": 0, "stations": 0}
    if not files:
        return empty
    con = duckdb.connect()
    con.execute("SET threads TO 2")
    pk = con.execute(f"SELECT tid, pha, peak_ms, conf FROM read_parquet({[str(f) for f in files]}) WHERE conf >= {CONF_MIN}").df()
    st = stations()
    n0 = len(pk)
    pk = pk[pk.tid.isin(st.index)]
    nk = len(pk)
    if not nk:
        return empty | {"picks": n0}
    pk = pk.sort_values(["tid", "pha", "peak_ms"], kind="stable").reset_index(drop=True)
    new = (pk.tid != pk.tid.shift()) | (pk.pha != pk.pha.shift()) | (pk.peak_ms.diff() > 500)
    pk["g"] = new.cumsum()
    pk = pk.loc[pk.groupby("g").conf.idxmax()].drop(columns="g")
    n1 = len(pk)
    # teleseismic masking
    tab = np.load(D / "taup_p.npz")
    lo = pd.Timestamp(year=y, month=m, day=1, tz="UTC")
    hi = lo + pd.offsets.MonthBegin(1)
    g = pd.read_csv(D / "cat" / "global_m45.csv", usecols=["time", "latitude", "longitude", "depth"], parse_dates=["time"])
    g = g[(g.time >= lo - pd.Timedelta(hours=1)) & (g.time < hi)]
    used = st.loc[pk.tid.unique()]
    sidx = {t: i for i, t in enumerate(used.index)}
    pk["s"] = pk.tid.map(sidx).astype(np.int32)
    keep = np.ones(len(pk), bool)
    if len(g):
        dd = gc_deg(used.latitude.to_numpy()[:, None], used.longitude.to_numpy()[:, None],
                    g.latitude.to_numpy()[None, :], g.longitude.to_numpy()[None, :])
        far = dd * np.pi * R_EARTH / 180 > 1000
        arr = (g.time.astype("int64").to_numpy() // 10**6)[None, :] + 1000 * ptime(dd, np.clip(g.depth.fillna(10).to_numpy(), 0, 700)[None, :], tab)
        pk = pk.sort_values(["s", "peak_ms"]).reset_index(drop=True)
        keep = np.ones(len(pk), bool)
        bounds = np.searchsorted(pk.s.to_numpy(), np.arange(len(used) + 1))
        t = pk.peak_ms.to_numpy()
        for i in range(len(used)):
            a = arr[i][far[i] & np.isfinite(arr[i])]
            if not len(a) or bounds[i] == bounds[i + 1]:
                continue
            tt = t[bounds[i]:bounds[i + 1]]
            a = np.sort(a)
            j = np.searchsorted(a, tt)
            near = np.zeros(len(tt), bool)
            for jj in (j - 1, j):
                ok = (jj >= 0) & (jj < len(a))
                near[ok] |= np.abs(tt[ok] - a[jj[ok]]) <= 60000
            keep[bounds[i]:bounds[i + 1]] = ~near
    pk = pk[keep].sort_values(["s", "peak_ms"]).reset_index(drop=True)
    n2 = len(pk)
    # P-S pairs
    s_, t_, isp = pk.s.to_numpy(), pk.peak_ms.to_numpy(), (pk.pha.to_numpy() == "P")
    n = len(pk)
    pair_s = np.full(n, -1, np.int64)
    blocked = np.zeros(n, bool)
    for k in (1, 2, 3):
        idx = np.arange(n - k)
        same = (s_[idx + k] == s_[idx]) & isp[idx] & ~blocked[idx]
        is_s = ~isp[idx + k]
        dt = t_[idx + k] - t_[idx]
        hit = same & is_s & (dt >= 800) & (dt <= SP_MAX) & (pair_s[idx] < 0)
        pair_s[idx[hit]] = idx[hit] + k
        blocked[idx[same & isp[idx + k]]] = True                    # a later P ends the search
    pi = np.flatnonzero(pair_s >= 0)
    pairs = pd.DataFrame({"s": s_[pi], "tp": t_[pi], "t0": t_[pi] - 1.37 * (t_[pair_s[pi]] - t_[pi])})
    pairs["id"] = np.arange(len(pairs))
    # coincidence
    lat, lon = used.latitude.to_numpy(), used.longitude.to_numpy()
    dkm = gc_deg(lat[:, None], lon[:, None], lat[None, :], lon[None, :]) * np.pi * R_EARTH / 180
    a, b = np.nonzero((dkm <= 50) & (dkm > 0))
    nb = pd.DataFrame({"a": a.astype(np.int32), "b": b.astype(np.int32)})
    pairs["bk"] = np.floor(pairs.t0 / 2500).astype(np.int64)
    con.register("p", pairs)
    con.register("nb", nb)
    loc = con.execute("""
        WITH x AS (SELECT p1.id, count(DISTINCT p2.s) AS k FROM p p1
                   JOIN nb ON nb.a = p1.s
                   JOIN p p2 ON p2.s = nb.b AND p2.bk BETWEEN p1.bk - 1 AND p1.bk + 1 AND abs(p2.t0 - p1.t0) <= 2500
                   GROUP BY p1.id)
        SELECT id FROM x WHERE k >= 2""").df()
    pairs["local"] = pairs.id.isin(set(loc.id))
    pairs["hour"] = (pairs.tp // 3_600_000).astype(np.int64)
    vd = D / "cat" / "validation_days.csv"
    if vd.exists():
        days = pd.to_datetime(pd.read_csv(vd).day, utc=True)
        dn = set((days.astype("int64") // (86400 * 10**9)).tolist())
        sel = pairs.local & pairs.t0.floordiv(86_400_000).isin(dn)
        if sel.any():
            vp = pairs[sel][["s", "t0"]].copy()
            vp["tid"] = used.index.to_numpy()[vp.s]
            vp[["tid", "t0"]].to_parquet(OUT / f"valpairs_{y}-{m:02d}.parquet", index=False)
    h = pairs.groupby(["s", "hour"]).agg(n_pair=("id", "size"), n_local=("local", "sum")).reset_index()
    h["tid"] = used.index.to_numpy()[h.s]
    h = h[["tid", "hour", "n_pair", "n_local"]].astype({"n_pair": np.int32, "n_local": np.int32})
    OUT.mkdir(parents=True, exist_ok=True)
    nbc = nb.groupby("a").size().reindex(range(len(used)), fill_value=0)       # neighbours with picks this month
    pd.DataFrame({"tid": used.index.to_numpy(), "neighbours_50km": nbc.to_numpy().astype(np.int32)}).to_parquet(
        OUT / f"nbr_{y}-{m:02d}.parquet", index=False)
    tmp = out.with_suffix(".tmp")
    h.to_parquet(tmp, index=False)
    tmp.rename(out)
    return {"month": f"{y}-{m:02d}", "picks": n0, "picks_known_station": nk, "after_merge": n1, "after_mask": n2,
            "pairs": int(len(pairs)), "local_pairs": int(pairs.local.sum()), "stations": int(len(used))}


def run(workers=10, variant="primary"):
    global OUT, SP_MAX, CONF_MIN
    if variant != "primary":
        OUT = D / f"proxy_{variant}"
        SP_MAX, CONF_MIN = {"sp5": (5000, 0.5), "conf07": (8000, 0.7)}[variant]
    months = [(y, m) for y in range(2002, 2026) for m in range(1, 13)]
    cnt = D / ("proxy_counts.csv" if variant == "primary" else f"proxy_counts_{variant}.csv")
    with ProcessPoolExecutor(workers) as ex:
        for r in ex.map(month, months):
            if r:
                new = not cnt.exists()
                with open(cnt, "a", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=list(r.keys()))
                    if new:
                        w.writeheader()
                    w.writerow(r)
                print(time.strftime("%H:%M:%S"), r, flush=True)
    print("== done", flush=True)


if __name__ == "__main__":
    {"table": table, "run": lambda: run(int(sys.argv[2]) if len(sys.argv) > 2 else 10,
                                        sys.argv[3] if len(sys.argv) > 3 else "primary")}[sys.argv[1]]()
