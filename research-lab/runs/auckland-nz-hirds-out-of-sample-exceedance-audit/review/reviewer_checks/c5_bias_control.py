"""Reviewer check 5: do the completeness rules select on rainfall? dense vs non-dense gauge-years; dropped years' partial
maxima; completeness-threshold sensitivity; MIN_OOS sensitivity; the in-sample control on the gauges shared with the
primary and by council; multi-duration overlap of exceedances."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-hirds-out-of-sample-exceedance-audit")
sys.path.insert(0, str(RUN / "code"))
import analyse as A
M, H, S = A.load()
g = A.gauge_meta(H, S); m6 = A.qualify(M, 6, "primary")
g, dup = A.dedupe(g, m6[m6.ok].groupby("file").size())
dep = A.depth_of(H, 6, 0.1)
yrs = list(range(2017, 2026))
inc = A.included(m6, g) & set(dep.file)
mo = A.oos_rows(m6, g); mo = mo[mo.file.isin(set(g.file) & set(dep.file))].merge(dep, on="file")
mo["exceed"] = mo.max_point > mo.mm; mo["server"] = mo.file.str.split("__").str[0]
def oe(df):
    return (int(df.exceed.sum()), len(df), round(float(df.exceed.sum() / (0.1 * len(df))), 3)) if len(df) else None
rng = np.random.default_rng(5)
def oe_ci(df):
    r = A.ratio_ci(df, 0.1, yrs, rng); return f"{r['OE']} ({r['ci'][0]}-{r['ci'][1]}), n={r['gauge_years']}, gauges={r['gauges']}"
x = mo[mo.file.isin(inc) & mo.ok]
print("primary reproduced:", oe(x))
print("\n== dense vs non-dense gauge-years (included, ok):")
for dz, df in x.groupby("dense"):
    print("  dense" if dz else "  non-dense", oe_ci(df))
print("  non-dense gauge-years with a zero-closed silence > 14 d (S2 would drop) -> see S2 in secondary.json")
print("\n== exceedance rate by known_frac band (included ok gauge-years):")
for lo, hi in ((0.9, 0.95), (0.95, 0.99), (0.99, 1.01)):
    df = x[(x.known_frac >= lo) & (x.known_frac < hi)]; print(f"  [{lo},{hi}): ", oe(df))
print("\n== included gauges' dropped (not ok) out-of-sample years:")
dr = mo[mo.file.isin(inc) & ~mo.ok]
print("  count:", len(dr), "| known_frac quantiles:", np.round(np.percentile(dr.known_frac, [10, 50, 90]), 2), "| partial max_point > depth in", int(dr.exceed.sum()), "| upper bound > depth in", int((dr.max_upper > dr.mm).sum()))
print("  by year:", dr.groupby("wy").size().to_dict())
print("  dropped years with partial max > depth (would be exceedances if kept):", dr[dr.exceed][["file", "wy", "known_frac"]].to_string(index=False) if dr.exceed.any() else "none")
print("\n== all ok out-of-sample gauge-years regardless of the 8-year rule (MIN_OOS=1):", oe_ci(mo[mo.ok]))
print("   ok gauge-years at gauges excluded by the 8-year rule:", oe_ci(mo[mo.ok & ~mo.file.isin(inc)]))
print("\n== completeness threshold sensitivity (8-year rule re-applied):")
for thr in (0.8, 0.85, 0.9, 0.95):
    A.COMPLETE = thr; mq = A.qualify(M, 6, "primary"); inc_t = A.included(mq, g) & set(dep.file)
    xt = A.oe_table(A.oos_rows(mq, g), dep, yrs, inc_t); print(f"  known >= {thr}:", oe_ci(xt))
A.COMPLETE = 0.9
print("\n== MIN_OOS sensitivity:")
for k in (5, 6, 7, 8, 9):
    A.MIN_OOS = k; inc_k = A.included(m6, g) & set(dep.file); xk = A.oe_table(A.oos_rows(m6, g), dep, yrs, inc_k); print(f"  >= {k} years:", oe_ci(xk))
A.MIN_OOS = 8
print("\n== in-sample control")
inc_in = A.included(m6, g, oos=False) & set(dep.file) & set(g.file)
ins_years = list(range(1995, 2015))
xi = A.oe_table(m6, dep, ins_years, inc_in); xi["server"] = xi.file.str.split("__").str[0]
rng_i = np.random.default_rng(6)
def oe_ci_in(df):
    r = A.ratio_ci(df, 0.1, ins_years, rng_i); return f"{r['OE']} ({r['ci'][0]}-{r['ci'][1]}), n={r['gauge_years']}, gauges={r['gauges']}"
print("  all 113:", oe_ci_in(xi))
both = inc_in & inc
print("  the", len(both), "gauges also in the primary, in sample:", oe_ci_in(xi[xi.file.isin(both)]), "| same gauges out of sample:", oe_ci(x[x.file.isin(both)]))
print("  in-sample by council:", {s: oe(df) for s, df in xi.groupby("server")})
print("  in-sample by period:", {p: oe(xi[(xi.wy >= a) & (xi.wy <= b)]) for p, (a, b) in {"1995-2004": (1995, 2004), "2005-2014": (2005, 2014)}.items()})
print("  in-sample dense vs not:", {("dense" if dz else "non-dense"): oe(df) for dz, df in xi.groupby("dense")})
print("  out-of-sample for the 131 primary gauges NOT in the control:", oe_ci(x[~x.file.isin(both)]))
# wet_median_min of in-sample ok years for control gauges (same resolution as OOS?)
print("  in-sample 2015/16-2016/17 (fitted by HIRDS, excluded from both):", oe(mo[mo.file.isin(inc)].iloc[0:0]) , "->", oe(A.oe_table(m6, dep, [2015, 2016], inc).assign(exceed=lambda d: d.max_point > d.mm)))
print("\n== multi-duration overlap among the 201 primary gauges' ok gauge-years")
ex6 = x[["file", "wy", "exceed"]].rename(columns={"exceed": "e6"})
for d_, lab in ((1, "e1"), (24, "e24")):
    md = A.qualify(M, d_, "primary"); dd = A.depth_of(H, d_, 0.1); xd = A.oe_table(A.oos_rows(md, g), dd, yrs, set(g.file)); ex6 = ex6.merge(xd[["file", "wy", "exceed"]].rename(columns={"exceed": lab}), on=["file", "wy"], how="left")
print("  6-h exceedances that also exceed at 24 h: %d of %d (with a 24-h value); at 1 h: %d of %d" % (int((ex6.e6 & (ex6.e24 == True)).sum()), int((ex6.e6 & ex6.e24.notna()).sum()), int((ex6.e6 & (ex6.e1 == True)).sum()), int((ex6.e6 & ex6.e1.notna()).sum())))
print("  24-h exceedances (same gauge-years) that also exceed at 6 h: %d of %d" % (int(((ex6.e24 == True) & ex6.e6).sum()), int((ex6.e24 == True).sum())))
yy = ex6.groupby("wy")[["e6", "e24", "e1"]].sum(); print("  by year:\n", yy.T.to_string())
