"""Exceedance audit (plan sections 0-4, with D1-D3): O/E of HIRDS v4 depths, out of sample and in sample.

  analyse.py -> results/tables/primary.json, results/tables/secondary.json, results/tables/coverage.json (G2),
                results/tables/gauges.csv (per included gauge), results/tables/year_by_year.csv
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402

SEED, B = 20261028, 2000
RES = {1: 5, 6: 15, 24: 60}                   # D3: longest median wet interval (min) per duration
OOS_FIRST, OOS_LAST, INS_LAST = 2017, 2025, 2014
MIN_OOS, MIN_INS, COMPLETE = 8, 10, 0.9
ARI = {0.1: 10.0, 0.02: 50.0}


def hirds_coverage_end(row):
    ends = [int(m) for c in ("daily_coverage", "sub_daily_coverage", "sub_hourly_coverage")
            for m in re.findall(r"\d{4}-(\d{4})", str(row.get(c, "")))]
    return max(ends) if ends else np.nan


def load():
    M = pd.read_parquet(D / "maxima.parquet")
    H = pd.read_parquet(D / "hirds_depths.parquet")
    S = pd.read_parquet(D / "hirds_sites.parquet")
    return M, H, S


def gauge_meta(H, S):
    """Per gauge: lat/lon, nearest HIRDS fitting site within 100 m and its last listed year (G1, D1)."""
    g = H.groupby("file")[["lat", "lon"]].first().reset_index()
    S = S.assign(end=S.apply(hirds_coverage_end, axis=1))
    lat0 = np.radians(g.lat.to_numpy())[:, None]
    dx = (g.lon.to_numpy()[:, None] - S.longitude.to_numpy()[None, :]) * 111.32 * np.cos(lat0)
    dy = (g.lat.to_numpy()[:, None] - S.latitude.to_numpy()[None, :]) * 110.57
    dist = np.hypot(dx, dy)
    j = dist.argmin(1)
    g["hirds_site_km"] = dist[np.arange(len(g)), j]
    g["fitting_site"] = g.hirds_site_km <= 0.1
    g["hirds_end"] = np.where(g.fitting_site, S.end.to_numpy()[j], np.nan)
    g["oos_first"] = np.where(g.hirds_end >= OOS_FIRST, g.hirds_end + 1, OOS_FIRST).astype(int)
    g["server"] = g.file.str.split("__").str[0]
    return g


def qualify(M, d, variant):
    m = M[(M.d == d) & (M.variant == variant)].copy()
    m["complete"] = m.known_frac >= COMPLETE
    m["resolved"] = m.wet_median_min <= RES[d]
    m["ok"] = m.complete & m.resolved
    return m


def dedupe(g, years_ok):
    """Plan section 1: co-located duplicates (within 100 m, overlapping qualified years) keep the longer record."""
    g = g.assign(n_ok=g.file.map(years_ok).fillna(0)).sort_values(["n_ok", "file"], ascending=[False, True])
    keep, dropped = [], []
    for r in g.itertuples():
        close = [k for k in keep if np.hypot((r.lon - k.lon) * 111.32 * np.cos(np.radians(r.lat)), (r.lat - k.lat) * 110.57) <= 0.1]
        (dropped if close else keep).append(r)
    return pd.DataFrame(keep), [r.file for r in dropped]


def oe_table(m, depth, years, include):
    x = m[m.file.isin(include) & m.wy.isin(years) & m.ok].merge(depth, on="file")
    x["exceed"] = x.max_point > x.mm
    return x


def ratio_ci(x, aep, years, rng, col="exceed"):
    by = x.groupby("wy").agg(o=(col, "sum"), n=(col, "size")).reindex(years, fill_value=0)
    o, e = by.o.to_numpy(float), by.n.to_numpy(float) * aep
    est = o.sum() / e.sum() if e.sum() else np.nan
    draws = []
    for _ in range(B):
        k = rng.integers(0, len(years), len(years))
        draws.append(o[k].sum() / e[k].sum() if e[k].sum() else np.nan)
    lo, hi = np.nanpercentile(draws, [2.5, 97.5])
    return {"O": int(o.sum()), "E": round(float(e.sum()), 2), "gauge_years": int(by.n.sum()), "gauges": int(x.file.nunique()),
            "OE": round(float(est), 3), "ci": [round(float(lo), 3), round(float(hi), 3)]}


def verdict(r):
    if r["OE"] >= 1.3 and r["ci"][0] > 1.0:
        return "Supported"
    if r["ci"][1] < 1.3:
        return "Refuted"
    return "Inconclusive"


def depth_of(H, d, aep, table="historical"):
    x = H[(H.table == table) & (H.duration_h == d) & (np.isclose(H.ari, ARI[aep]))]
    return x[["file", "mm"]]


def included(m, g, oos=True):
    if oos:
        q = m.merge(g[["file", "oos_first"]], on="file")
        q = q[(q.wy >= q.oos_first) & (q.wy <= OOS_LAST) & q.ok]
        n = q.groupby("file").size()
        return set(n[n >= MIN_OOS].index)
    q = m[(m.wy <= INS_LAST) & m.ok]
    n = q.groupby("file").size()
    return set(n[n >= MIN_INS].index)


def oos_rows(m, g):
    q = m.merge(g[["file", "oos_first"]], on="file")
    return q[(q.wy >= q.oos_first) & (q.wy <= OOS_LAST)].drop(columns="oos_first")


def run(M, H, g, d=6, aep=0.1, variant="primary", rng=None, col="max_point", depth_table="historical", depth_shift=None,
        servers=None):
    m = qualify(M, d, variant)
    if col != "max_point":
        m = m.assign(max_point=m[col].where(m[col].notna(), m.max_point))
    dep = depth_of(H, d, aep, depth_table)
    if depth_shift is not None:
        se = depth_of(H, d, aep, "historical_se").rename(columns={"mm": "se"})
        dep = dep.merge(se, on="file").assign(mm=lambda x: x.mm + depth_shift * x.se)[["file", "mm"]]
    gg = g if servers is None else g[g.server.isin(servers)]
    inc = included(m, gg) & set(dep.file)
    x = oe_table(oos_rows(m, gg), dep, list(range(OOS_FIRST, OOS_LAST + 1)), inc)
    return ratio_ci(x, aep, list(range(OOS_FIRST, OOS_LAST + 1)), rng), x


def main():
    M, H, S = load()
    rng = np.random.default_rng(SEED)
    g = gauge_meta(H, S)
    m6 = qualify(M, 6, "primary")
    years_ok = m6[m6.ok].groupby("file").size()
    g, dup = dedupe(g, years_ok)
    out = {"duplicates_dropped": dup, "g1_oos_start_moved": g.loc[g.oos_first > OOS_FIRST, ["file", "hirds_end", "oos_first"]].to_dict("records")}

    # primary: 6 h, 10% AEP, out of sample
    r, x = run(M, H, g, rng=rng)
    r["verdict"] = verdict(r)
    out["H1"] = r
    # sanity control: in-sample years, gauges with >= 10 complete in-sample years
    dep = depth_of(H, 6, 0.1)
    inc_in = included(m6, g, oos=False) & set(dep.file) & set(g.file)
    ins_years = list(range(1995, INS_LAST + 1))
    xi = oe_table(m6, dep, ins_years, inc_in)
    out["sanity_in_sample"] = ratio_ci(xi, 0.1, ins_years, np.random.default_rng(SEED + 1))
    out["sanity_in_sample"]["holds"] = out["sanity_in_sample"]["ci"][0] <= 1.0 <= out["sanity_in_sample"]["ci"][1]
    (T / "primary.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps(out, indent=1, default=str))

    # gauges and year-by-year
    gx = x.groupby("file").agg(years=("wy", "size"), exceed=("exceed", "sum")).reset_index().merge(g, on="file")
    gx.to_csv(T / "gauges.csv", index=False)
    x.groupby("wy").agg(gauges=("file", "size"), exceed=("exceed", "sum")).assign(OE=lambda t: t.exceed / (0.1 * t.gauges)).to_csv(T / "year_by_year.csv")

    # secondary analyses (plan section 3, D1, D2)
    sec, rs = {}, lambda k: np.random.default_rng(SEED + 100 + k)
    k = 0
    for d in (1, 6, 24):
        for aep in (0.1, 0.02):
            k += 1
            sec[f"{d}h_{int(aep * 100)}pct"] = run(M, H, g, d=d, aep=aep, rng=rs(k))[0]
    for sv in sorted(g.server.unique()):
        k += 1
        sec[f"council_{sv}"] = run(M, H, g, rng=rs(k), servers=[sv])[0]
    k += 1; sec["without_janfeb2023"] = run(M, H, g, rng=rs(k), col="max_point_no_janfeb2023")[0]
    for name, tab in (("rcp45_2031_2050", "rcp45_2031_2050"), ("rcp85_2031_2050", "rcp85_2031_2050")):
        k += 1; sec[f"against_{name}"] = run(M, H, g, rng=rs(k), depth_table=tab)[0]
    for sh in (-1, 1):
        k += 1; sec[f"depth_{'minus' if sh < 0 else 'plus'}_1se"] = run(M, H, g, rng=rs(k), depth_shift=sh)[0]
    for v in ("S2", "S3", "S4"):
        k += 1; sec[v] = run(M, H, g, rng=rs(k), variant=v)[0]
    # S1: undetermined gauge-years counted as exceedances
    dep6 = depth_of(H, 6, 0.1)
    xs = x.copy()                                  # x carries max_upper from maxima.parquet
    xs["exceed_upper"] = xs.exceed | (xs.max_upper > xs.mm)
    sec["S1_undetermined_as_exceed"] = ratio_ci(xs, 0.1, list(range(OOS_FIRST, OOS_LAST + 1)), rs(99), col="exceed_upper")
    sec["S1_undetermined_gauge_years"] = int((xs.exceed_upper & ~xs.exceed).sum())
    # fitting vs non-fitting sites
    for flag in (True, False):
        xx = x[x.file.isin(g[g.fitting_site == flag].file)]
        sec[f"{'fitting' if flag else 'non_fitting'}_sites"] = ratio_ci(xx, 0.1, list(range(OOS_FIRST, OOS_LAST + 1)), rs(200 + flag))
    # storm-cluster bootstrap: exceedances within 72 h of each other, across gauges, are one storm
    ex = x[x.exceed].sort_values("t_max")
    storm = np.r_[0, np.cumsum(np.diff(ex.t_max.to_numpy()) > 72 * 60)] if len(ex) else np.array([], int)
    sizes = pd.Series(storm).value_counts().to_numpy()
    E = 0.1 * len(x)
    sd = rs(300)
    draws = [sizes[sd.integers(0, len(sizes), len(sizes))].sum() / E for _ in range(B)] if len(sizes) else [np.nan]
    sec["storm_cluster_bootstrap"] = {"storms": int(len(sizes)), "largest_storm_exceedances": int(sizes.max()) if len(sizes) else 0,
                                      "OE": round(float(len(ex) / E), 3), "ci": [round(float(np.percentile(draws, q)), 3) for q in (2.5, 97.5)]}
    (T / "secondary.json").write_text(json.dumps(sec, indent=1, default=str) + "\n")
    print(json.dumps({k_: (v_.get("OE"), v_.get("ci"), v_.get("gauges")) if isinstance(v_, dict) else v_ for k_, v_ in sec.items()}, indent=0))

    # G2 coverage
    cov_path = T / "coverage.json"
    if cov_path.exists():
        cov_path.unlink()
    inv = pd.read_parquet(D / "inventory.parquet")
    fl = pd.concat([pd.read_csv(D / "fetch_log.csv"), pd.read_csv(D / "fetch_log_auckland.csv")])
    skipped = pd.read_csv(D / "hirds_depths_skipped.csv") if (D / "hirds_depths_skipped.csv").exists() else pd.DataFrame(columns=["file", "reason"])
    c = Coverage("gauges", cov_path)
    all_files = set(M.file.unique())
    no_depth = all_files - set(H.file)
    m_oos = oos_rows(m6, g)
    inc = included(m6, g) & set(dep6.file)
    c.add_counts(ok=len(inc), drops={
        "series empty or failed to fetch": int((~fl.status.str.match(r"^(ok|done)")).sum()),
        "no HIRDS depth (coordinates missing or outside NZ)": len(no_depth),
        "co-located duplicate (plan: keep the longer record)": len(dup),
        f"fewer than {MIN_OOS} complete, resolved out-of-sample years": len((all_files - no_depth - set(dup)) - inc)})
    c.save()
    c2 = Coverage("gauge_years_out_of_sample_6h", cov_path)
    mo = m_oos[m_oos.file.isin(set(g.file))]
    c2.add_counts(ok=int(mo.ok.sum()), drops={
        "incomplete (<90% known time: quality-excluded, outage or unresolved)": int((~mo.complete).sum()),
        "complete but too coarse (median wet interval > 15 min)": int((mo.complete & ~mo.resolved).sum())})
    c2.save()


if __name__ == "__main__":
    main()
