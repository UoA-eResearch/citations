"""Station x trigger tests, the matched pseudo-trigger null, and peak dynamic strain (plan sections 3-5).
Written before any window count was computed.

  windows.py [VARIANT] [WORKERS]  -> results/tables/pairs_<variant>.parquet (one row per station x trigger),
                                     results/tables/null_<variant>.parquet (p0 per station), coverage.json
VARIANT: primary | base24h (24 h baseline) | post6h (post window from the wave train end + 6 h); proxy variants
(sp5, conf07) read data/proxy_<variant>/.
POST HOC (D1, after the primary result): exposure | exposure_post6h — window lengths in beta's f use effective
exposure: each window minus the union of the +-60 s masks around predicted teleseismic P arrivals (ComCat M >= 4.5
more than 1,000 km away) that the proxy removed, for real and pseudo triggers alike.
EXPLORATORY (plan section 6): instant — the post window is the hours spanned by the surface-wave train itself
(origin + D/4.5 km/s to origin + D/2.5 km/s), against the same 7-day baseline.
"""
import sys
import zlib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402

R_EARTH, SEED, NPSEUDO, MIN_VALID = 6371.0088, 20261026, 500, 100
H = 3_600_000
G = {}


def gc_km(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    h = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * R_EARTH * np.arcsin(np.sqrt(np.clip(h, 0, 1)))


def strain(mw, dist_km):
    """Lay & Wallace surface-wave relation: log10(A/T [um/s]) = M - 1.66 log10(D deg) - 3.3; PGV = 2 pi A/T;
    strain = PGV / 3.5 km/s."""
    deg = dist_km / (np.pi * R_EARTH / 180)
    at = 10 ** (np.minimum(mw, 8.3) - 1.66 * np.log10(deg) - 3.3)          # um/s
    return 2 * np.pi * at * 1e-6 / 3500.0


def load(variant):
    pdir = D / ("proxy" if variant in ("primary", "base24h", "post6h", "exposure", "exposure_post6h", "instant") else f"proxy_{variant}")
    hrs = pd.concat([pd.read_parquet(f) for f in sorted(pdir.glob("????-??.parquet"))], ignore_index=True)
    nbr = pd.concat([pd.read_parquet(f).assign(month=f.stem[4:]) for f in sorted(pdir.glob("nbr_*.parquet"))])
    st = pd.read_parquet(D / "raw" / "stations.parquet", columns=["id", "latitude", "longitude", "state"])
    us = st[~st.state.fillna("").str.contains(r"\(")].groupby("id")[["latitude", "longitude"]].median()
    av = pd.concat([pd.read_parquet(f, columns=["tid", "date", "status"]) for f in sorted((D / "raw" / "availability").glob("*.parquet"))])
    av = av[av.tid.isin(us.index)]
    av["day"] = (pd.to_datetime(av.date).astype("int64") // (86400 * 10**9)).astype(np.int32)
    loaded = {t: set(g.day[g.status == "loaded"]) for t, g in av.groupby("tid")}
    hrs = hrs[hrs.tid.isin(us.index)]
    series = {}
    for t, g in hrs.groupby("tid"):
        g = g.sort_values("hour")
        series[t] = (g.hour.to_numpy(), np.cumsum(g.n_local.to_numpy()))
    nb = nbr.set_index(["tid", "month"]).neighbours_50km.to_dict()
    tr = pd.read_csv(D / "cat" / "triggers_m7.csv", parse_dates=["time"])
    tr = tr[(tr.time >= "2002-01-01") & (tr.time < "2026-01-01")].reset_index(drop=True)
    have = [t for t in us.index if t in series]
    dmin = gc_km(us.loc[have].latitude.to_numpy()[:, None], us.loc[have].longitude.to_numpy()[:, None],
                 tr.latitude.to_numpy()[None, :], tr.longitude.to_numpy()[None, :]).min(axis=0)
    tr["min_dist_km"] = dmin
    tr = tr[dmin >= 1000].reset_index(drop=True)
    g45 = pd.read_csv(D / "cat" / "global_m45.csv", usecols=["time", "mag"], parse_dates=["time"])
    big7 = np.sort(g45[g45.mag >= 7.0].time.astype("int64").to_numpy() // 10**6)
    big65 = np.sort(g45[g45.mag >= 6.5].time.astype("int64").to_numpy() // 10**6)
    loc = pd.read_csv(D / "cat" / "region_m35.csv", usecols=["time", "latitude", "longitude", "mag"], parse_dates=["time"])
    if variant.startswith("exposure"):
        sys.path.insert(0, str(RUN / "code"))
        import proxy as P
        e = pd.read_csv(D / "cat" / "global_m45.csv", usecols=["time", "latitude", "longitude", "depth"], parse_dates=["time"])
        e = e.sort_values("time")
        G.update(ev_t=e.time.astype("int64").to_numpy() // 10**6, ev_lat=e.latitude.to_numpy(), ev_lon=e.longitude.to_numpy(),
                 ev_dep=np.clip(e.depth.fillna(10).to_numpy(), 0, 700), taup=dict(np.load(D / "taup_p.npz")), ptime=P.ptime)
    G.update(variant=variant, series=series, loaded=loaded, us=us, tr=tr, nb=nb, big7=big7, big65=big65,
             loc_t=loc.time.astype("int64").to_numpy() // 10**6, loc_lat=loc.latitude.to_numpy(), loc_lon=loc.longitude.to_numpy())


def count(tid, h0, h1):
    """Local-event pairs in hours [h0, h1)."""
    hrs, cs = G["series"][tid]
    a, b = np.searchsorted(hrs, h0), np.searchsorted(hrs, h1)
    return int((cs[b - 1] if b > 0 else 0) - (cs[a - 1] if a > 0 else 0))


def test(tid, origin_ms, dist_km, lat, lon):
    """One station x (pseudo-)trigger: returns (beta, sig, n_post, n_base) or a drop reason string."""
    v = G["variant"]
    wave_end = origin_ms + dist_km / 2.5 * 1000
    post0 = int(np.ceil((wave_end + (6 if v in ("post6h", "exposure_post6h") else 2) * H) / H))
    post1 = post0 + 24
    if v == "instant":
        post0 = int((origin_ms + dist_km / 4.5 * 1000) // H)
        post1 = int(np.ceil(wave_end / H))
    base1 = int(origin_ms // H)
    base0 = base1 - (24 if v == "base24h" else 168)
    days = set(range(base0 // 24, (post1 - 1) // 24 + 1))
    if not days <= G["loaded"].get(tid, set()):
        return "a station-day in the windows not loaded"
    month = pd.Timestamp(origin_ms, unit="ms").strftime("%Y-%m")
    if G["nb"].get((tid, month), 0) < 2:
        return "fewer than 2 neighbours within 50 km with picks"
    if count(tid, base0 - 720, base0) < 1:
        return "no local-event pair in the 30 days before the baseline"
    t = G["loc_t"]
    i0, i1 = np.searchsorted(t, base0 * H), np.searchsorted(t, base1 * H)
    if i1 > i0 and (gc_km(lat, lon, G["loc_lat"][i0:i1], G["loc_lon"][i0:i1]) <= 100).any():
        return "local M>=3.5 within 100 km in the baseline"
    npost, nbase = count(tid, post0, post1), count(tid, base0, base1)
    tp, tb = float(post1 - post0), float(base1 - base0)
    if v.startswith("exposure"):
        tp -= masked(post0 * H, post1 * H, lat, lon) / H
        tb -= masked(base0 * H, base1 * H, lat, lon) / H
    n, f = npost + nbase, tp / (tp + tb)
    beta = 0.0 if n == 0 else (npost - n * f) / np.sqrt(n * f * (1 - f))
    return beta, bool(beta >= 2), npost, nbase


def masked(t0, t1, lat, lon):
    """ms of [t0, t1) inside the union of +-60 s masks around predicted P arrivals of far (> 1,000 km) M >= 4.5."""
    a, b = np.searchsorted(G["ev_t"], t0 - 25 * 60_000), np.searchsorted(G["ev_t"], t1)
    if b <= a:
        return 0.0
    dk = gc_km(lat, lon, G["ev_lat"][a:b], G["ev_lon"][a:b])
    far = dk > 1000
    if not far.any():
        return 0.0
    arr = G["ev_t"][a:b][far] + 1000 * G["ptime"](dk[far] / (np.pi * R_EARTH / 180), G["ev_dep"][a:b][far], G["taup"])
    iv = np.c_[np.clip(arr - 60_000, t0, t1), np.clip(arr + 60_000, t0, t1)]
    iv = iv[np.argsort(iv[:, 0])]
    tot, cur_s, cur_e = 0.0, None, None
    for s_, e_ in iv:
        if cur_e is None or s_ > cur_e:
            if cur_e is not None:
                tot += cur_e - cur_s
            cur_s, cur_e = s_, e_
        else:
            cur_e = max(cur_e, e_)
    if cur_e is not None:
        tot += cur_e - cur_s
    return tot


def station(tid):
    lat, lon = G["us"].loc[tid, ["latitude", "longitude"]]
    tr = G["tr"]
    dist = gc_km(lat, lon, tr.latitude.to_numpy(), tr.longitude.to_numpy())
    eps = strain(tr.mag.to_numpy(), dist)
    real = []
    for j, r in tr.iterrows():
        o = int(r.time.value // 10**6)
        res = test(tid, o, dist[j], lat, lon)
        row = {"tid": tid, "trigger": r.id, "mag": r.mag, "dist_km": dist[j], "strain": eps[j]}
        row.update({"drop": res} if isinstance(res, str) else {"drop": None, "beta": res[0], "sig": res[1], "n_post": res[2], "n_base": res[3]})
        real.append(row)
    rng = np.random.default_rng([SEED, zlib.crc32(tid.encode())])          # deterministic across processes
    lo, hi = pd.Timestamp("2002-01-01").value // 10**6, pd.Timestamp("2026-01-01").value // 10**6
    pseudo, tries = [], 0
    while len(pseudo) < NPSEUDO and tries < 50 * NPSEUDO:
        tries += 1
        j = int(rng.integers(len(tr)))
        o = int(tr.time.iloc[j].value // 10**6) + int(rng.integers(-45, 46)) * 86_400_000 + int(rng.integers(-12, 13)) * 365 * 86_400_000
        if not (lo <= o < hi - 10 * 86_400_000):
            continue
        b7, b65 = G["big7"], G["big65"]
        k7, k65 = np.searchsorted(b7, o), np.searchsorted(b65, o)
        near7 = any(0 <= k < len(b7) and abs(b7[k] - o) < 10 * 86_400_000 for k in (k7 - 1, k7))
        near65 = any(0 <= k < len(b65) and abs(b65[k] - o) < 3 * 86_400_000 for k in (k65 - 1, k65))
        if near7 or near65:
            continue
        pseudo.append((o, dist[j]))
    ps = [test(tid, o, d, lat, lon) for o, d in pseudo]
    valid = [p for p in ps if not isinstance(p, str)]
    drops = pd.Series([p for p in ps if isinstance(p, str)]).value_counts().to_dict()
    p0 = float(np.mean([p[1] for p in valid])) if valid else np.nan
    return real, {"tid": tid, "pseudo_drawn": len(pseudo), "pseudo_valid": len(valid), "p0": p0, "pseudo_drops": drops}


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "primary"
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    load(variant)
    tids = sorted(G["series"])
    print(variant, len(tids), "stations with proxy data;", len(G["tr"]), "triggers >= 1,000 km", flush=True)
    real, null = [], []
    with ProcessPoolExecutor(workers) as ex:
        for k, (r, n) in enumerate(ex.map(station, tids, chunksize=8)):
            real += r
            null.append(n)
            if (k + 1) % 500 == 0:
                print(k + 1, "stations", flush=True)
    pr = pd.DataFrame(real)
    nl = pd.DataFrame(null)
    pr = pr.merge(nl[["tid", "p0", "pseudo_valid"]], on="tid", how="left")
    cov = Coverage(f"pairs_{variant}", T / "coverage.json")
    for r in pr.itertuples():
        u = (r.tid, r.trigger)
        cov.attempt(u)
        if isinstance(r.drop, str):
            cov.drop(u, r.drop)
        elif not (r.pseudo_valid >= MIN_VALID):
            cov.drop(u, "station has fewer than 100 valid pseudo-triggers")
        else:
            cov.ok(u)
    cov.save()
    pr["in_population"] = pr["drop"].isna() & (pr.pseudo_valid >= MIN_VALID)
    pr["excess"] = np.where(pr.in_population, pr.sig.astype(float) - pr.p0, np.nan)
    T.mkdir(parents=True, exist_ok=True)
    pr.to_parquet(T / f"pairs_{variant}.parquet", index=False)
    nl.assign(pseudo_drops=nl.pseudo_drops.astype(str)).to_parquet(T / f"null_{variant}.parquet", index=False)
    print("population pairs", int(pr.in_population.sum()), "of", len(pr), flush=True)


if __name__ == "__main__":
    main()
