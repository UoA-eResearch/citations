"""Reviewer check 1: data formats, HIRDS depths/sites, inclusion-rule distributions, report numbers vs tables."""
import json, re, sys
from pathlib import Path
import numpy as np, pandas as pd
RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-hirds-out-of-sample-exceedance-audit")
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
import analyse as A

M, H, S = A.load()
print("maxima rows", len(M), "files", M.file.nunique(), "| depth files", H.file.nunique(), "| HIRDS sites", len(S))
print("\n== HIRDS site list columns:", list(S.columns))
for c in S.columns:
    if "coverage" in c:
        print(c, "examples:", S[c].dropna().astype(str).sample(5, random_state=1).tolist())
S = S.assign(end=S.apply(A.hirds_coverage_end, axis=1))
print("coverage end year counts (top):", S.end.value_counts().sort_index().tail(8).to_dict())
print("sites with no parsed end:", int(S.end.isna().sum()), "of", len(S))
print("site list other cols sample:\n", S.drop(columns=[c for c in S.columns if 'coverage' in c]).head(3).to_string())
if "source" in S.columns or any('source' in c.lower() for c in S.columns):
    sc = [c for c in S.columns if 'source' in c.lower()][0]
    print("sources x end>=2017:", S[S.end >= 2017].groupby(sc).size().to_dict())
    print("sources overall:", S.groupby(sc).size().to_dict())

print("\n== depths table")
print(H.table.value_counts().to_dict())
h10 = H[(H.table == "historical") & (H.duration_h == 6) & np.isclose(H.ari, 10)]
print("6h 10yr depth by server:\n", h10.assign(server=h10.file.str.split("__").str[0]).groupby("server").mm.describe()[["count", "min", "50%", "max"]].round(1).to_string())
print("aep for ari 10:", H[np.isclose(H.ari, 10)].aep.unique(), "| ari list:", sorted(H.ari.unique()))
se = H[(H.table == "historical_se") & (H.duration_h == 6) & np.isclose(H.ari, 10)].set_index("file").mm
print("SE/depth 6h 10yr: median %.3f, IQR %.3f-%.3f" % (np.median(se / h10.set_index("file").mm), *np.percentile(se / h10.set_index("file").mm, [25, 75])))
r45 = H[(H.table == "rcp45_2031_2050") & (H.duration_h == 6) & np.isclose(H.ari, 10)].set_index("file").mm
r85 = H[(H.table == "rcp85_2031_2050") & (H.duration_h == 6) & np.isclose(H.ari, 10)].set_index("file").mm
print("RCP4.5/hist ratio median %.3f ; RCP8.5/hist %.3f" % (np.median(r45 / h10.set_index("file").mm), np.median(r85 / h10.set_index("file").mm)))
# monotonicity
piv = H[H.table == "historical"].pivot_table(index=["file", "duration_h"], columns="ari", values="mm")
print("depth monotone in ARI for all file x duration:", bool((piv.diff(axis=1).iloc[:, 1:] > 0).all().all()))
piv2 = H[H.table == "historical"].pivot_table(index=["file", "ari"], columns="duration_h", values="mm")
print("depth monotone in duration:", bool((piv2.diff(axis=1).iloc[:, 1:] > 0).all().all()))

print("\n== gauge meta / G1")
g = A.gauge_meta(H, S)
m6 = A.qualify(M, 6, "primary")
years_ok = m6[m6.ok].groupby("file").size()
g, dup = A.dedupe(g, years_ok)
inc = A.included(m6, g) & set(A.depth_of(H, 6, 0.1).file)
print("included:", len(inc))
gi = g[g.file.isin(inc)].copy()
gi["server"] = gi.file.str.split("__").str[0]
print("nearest HIRDS site distance (km) for included gauges, quantiles:", np.round(np.percentile(gi.hirds_site_km, [0, 10, 25, 50, 75, 90, 100]), 3))
print("included within 100 m:", int(gi.fitting_site.sum()), "| 100 m-500 m:", int(((gi.hirds_site_km > 0.1) & (gi.hirds_site_km <= 0.5)).sum()), "| 0.5-2 km:", int(((gi.hirds_site_km > 0.5) & (gi.hirds_site_km <= 2)).sum()))
print("hirds_end for included fitting sites:", gi[gi.fitting_site].hirds_end.value_counts().sort_index().to_dict())
# all gauges with depth: hirds_end distribution by server
g["server"] = g.file.str.split("__").str[0]
print("hirds_end >= 2017 by server (all gauges w/ depth):", g[g.hirds_end >= 2017].groupby("server").size().to_dict())
print("fitting sites by server (all):", g[g.fitting_site].groupby("server").size().to_dict(), "| of", g.groupby("server").size().to_dict())

# name match between included non-fitting gauges and HIRDS sites (crude token overlap), to look for missed overlaps
namecol = [c for c in S.columns if c.lower() in ("name", "site_name", "sitename", "site")]
print("site name column:", namecol)
if namecol:
    nm = namecol[0]
    def toks(s):
        return set(w for w in re.split(r"[^a-z0-9]+", str(s).lower()) if len(w) > 3 and w not in {"river", "stream", "rainfall", "creek", "road", "station"})
    St = S[nm].map(toks)
    out = []
    for r in gi[~gi.fitting_site].itertuples():
        gt = toks(r.file.split("__", 1)[1].replace("_", " "))
        dx = (r.lon - S.longitude.to_numpy()) * 111.32 * np.cos(np.radians(r.lat)); dy = (r.lat - S.latitude.to_numpy()) * 110.57
        dist = np.hypot(dx, dy)
        near = np.flatnonzero(dist <= 3)
        best = [(dist[j], S[nm].iloc[j], len(gt & St.iloc[j]), S.end.iloc[j]) for j in near if len(gt & St.iloc[j]) >= 1]
        if best:
            best.sort()
            out.append((r.file, round(best[0][0], 2), best[0][1], best[0][3]))
    print("non-fitting included gauges with a name-sharing HIRDS site within 3 km:", len(out))
    for o in out[:25]:
        print("  ", o)
    print("  ... ends >= 2017 among them:", sum(1 for o in out if o[3] >= 2017))

print("\n== inclusion-rule distributions (6 h primary, OOS rows, gauges with depth, post-dedupe)")
mo = A.oos_rows(m6, g)
mo = mo[mo.file.isin(set(g.file))]
print("OOS gauge-years:", len(mo), "| ok:", int(mo.ok.sum()))
print("known_frac quantiles (all OOS):", np.round(np.percentile(mo.known_frac, [10, 25, 50, 75, 90]), 3))
print("known_frac of ok gauge-years: share < 0.95:", round(float((mo[mo.ok].known_frac < 0.95).mean()), 3), " mean:", round(float(mo[mo.ok].known_frac.mean()), 4))
print("wet_median_min among complete gauge-years:", mo[mo.complete].wet_median_min.round(0).value_counts().sort_index().head(20).to_dict())
print("dense share among ok gauge-years:", round(float(mo[mo.ok].dense.mean()), 3))
mi = mo[mo.file.isin(inc)]
print("included gauge-years: dense share", round(float(mi[mi.ok].dense.mean()), 3), "| by server:", mi[mi.ok].groupby(mi[mi.ok].file.str.split("__").str[0]).dense.mean().round(2).to_dict())
# within-gauge variation of resolution status among included gauges
res_var = mi[mi.complete].groupby("file").resolved.agg(["mean", "size"])
print("included gauges whose complete years are not all resolved:", int(((res_var["mean"] < 1) & (res_var["mean"] > 0)).sum()), "of", len(res_var))
print("included gauge-years complete but unresolved:", int((mi.complete & ~mi.resolved).sum()))
print("wet_median_min of included ok gauge-years, quantiles:", np.round(np.percentile(mi[mi.ok].wet_median_min, [50, 75, 90, 95, 99, 100]), 1))

print("\n== report numbers")
dep = A.depth_of(H, 6, 0.1)
x = A.oe_table(mo, dep, list(range(2017, 2026)), inc)
print("O", int(x.exceed.sum()), "n", len(x), "gauges", x.file.nunique())
ex = x[x.exceed].copy(); ex["t"] = pd.to_datetime(ex.t_max, unit="m")
print("exceedances in Jan 2023:", int(((ex.t >= "2023-01-01") & (ex.t < "2023-02-01")).sum()), "| Feb 2023:", int(((ex.t >= "2023-02-01") & (ex.t < "2023-03-01")).sum()),
      "| Feb 2023 HB:", int(((ex.t >= "2023-02-01") & (ex.t < "2023-03-01") & ex.file.str.startswith("HawkesBay")).sum()))
print("Mar 2022:", int(((ex.t >= "2022-03-01") & (ex.t < "2022-04-01")).sum()), "| Feb 2018:", int(((ex.t >= "2018-02-01") & (ex.t < "2018-03-01")).sum()))
exs = ex.sort_values("t_max"); storm = np.r_[0, np.cumsum(np.diff(exs.t_max.to_numpy()) > 72 * 60)]
sizes = pd.Series(storm).value_counts()
print("storms:", len(sizes), "largest:", int(sizes.max()), "| span of largest (days):", round(float((exs.t_max[storm == sizes.idxmax()].max() - exs.t_max[storm == sizes.idxmax()].min()) / 1440), 1))
print("storm size distribution:", sizes.value_counts().sort_index().to_dict())
# without 2022/23 entirely
yb = pd.read_csv(T / "year_by_year.csv")
print("O/E dropping the whole 2022/23 year:", round((yb.exceed.sum() - yb[yb.wy == 2022].exceed.iloc[0]) / (0.1 * (yb.gauges.sum() - yb[yb.wy == 2022].gauges.iloc[0])), 3))
# in-sample control gauges vs primary
inc_in = A.included(m6, g, oos=False) & set(dep.file) & set(g.file)
print("in-sample control gauges:", len(inc_in), "| also in primary:", len(inc_in & inc), "| by server:", pd.Series([f.split("__")[0] for f in inc_in]).value_counts().to_dict())
# undetermined and exceedance margins
x["margin"] = x.max_point / x.mm
print("exceedances within 2% of depth:", int(((x.margin > 1) & (x.margin <= 1.02)).sum()), "| non-exceedances within 2%:", int(((x.margin <= 1) & (x.margin > 0.98)).sum()))
print("gauge-years with max_upper > mm >= max_point:", int(((x.max_upper > x.mm) & (x.max_point <= x.mm)).sum()))
# per-gauge exceedance counts: concentration
gc = x.groupby("file").exceed.sum()
print("gauges with 0/1/2/3+ exceedances:", (gc.clip(upper=3)).value_counts().sort_index().to_dict())
# measurement names used by included gauges
inv = pd.read_parquet(D / "inventory.parquet")
inv["stem"] = inv.server + "__" + inv.site.map(lambda s: re.sub(r"[^A-Za-z0-9._-]+", "_", s))
used = []
for f in sorted(inc):
    if f.startswith("Auckland__"):
        continue
    z = np.load(D / "series" / f"{f}.npz", allow_pickle=False)
    used.append((f, str(z["measurement"])))
u = pd.DataFrame(used, columns=["file", "measurement"])
print("measurement names used (included Hilltop gauges):", u.measurement.value_counts().to_dict())
mi2 = u.merge(inv[["stem", "measurement", "interpolation", "datasource"]], left_on=["file", "measurement"], right_on=["stem", "measurement"], how="left").drop_duplicates("file")
print("interpolation types:", mi2.interpolation.value_counts(dropna=False).to_dict())
print("datasources:", mi2.datasource.value_counts().head(8).to_dict())
print("interpolation x measurement (all candidate inventory rows, non-virtual, rain):", inv[(inv.virtual == False) & inv.measurement.notna()].groupby(["interpolation"]).size().to_dict())
# Auckland counterfactual: oos_first=2017 under primary rules
ga = g[g.server == "Auckland"].copy()
ma = mo[mo.file.isin(ga.file)]
for first in (2018, 2017):
    q = m6[(m6.file.isin(ga.file)) & (m6.wy >= first) & (m6.wy <= 2025) & m6.ok].groupby("file").size()
    print(f"Auckland gauges with >=8 ok years from wy {first} (primary rules):", int((q >= 8).sum()), "| >=7:", int((q >= 7).sum()))
m6s3 = A.qualify(M, 6, "S3")
for first in (2018, 2017):
    q = m6s3[(m6s3.file.isin(ga.file)) & (m6s3.wy >= first) & (m6s3.wy <= 2025) & m6s3.ok].groupby("file").size()
    print(f"Auckland gauges with >=8 ok years from wy {first} (S3 rules):", int((q >= 8).sum()))
ak = m6[m6.file.isin(ga.file) & (m6.wy >= 2017)]
print("Auckland complete share by wy (primary):", ak.groupby("wy").ok.mean().round(2).to_dict())
print("Auckland complete share by wy (S3):", m6s3[m6s3.file.isin(ga.file) & (m6s3.wy >= 2017)].groupby("wy").ok.mean().round(2).to_dict())
# per-year completeness of all candidates: 2025/26
print("complete share by wy, all OOS rows:", mo.groupby("wy").ok.mean().round(2).to_dict())
