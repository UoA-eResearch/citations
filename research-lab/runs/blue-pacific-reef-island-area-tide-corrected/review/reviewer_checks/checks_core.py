"""Reviewer checks on the study's own data (read-only on the study; writes only to review/reviewer_checks/).
Run: venv/bin/python -I review/reviewer_checks/checks_core.py
Sections: A tide alignment (lag), B gauge vs overpass-time trends, C joint/quadratic tide fits, D H2 decomposition,
E guard sensitivity and tiers, F E1 internal L7->L8 step, G S2 baseline step and offsets, H land screen, I coverage and
report numbers, J gross filter."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(RUN / "code"))
import rates as R  # noqa: E402
from inventory import ATOLLS  # noqa: E402

pd.set_option("display.width", 220, "display.max_columns", 40, "display.max_rows", 200)
P = lambda *a, **k: print(*a, flush=True, **k)
T = RUN / "results" / "tables"

inv = pd.read_csv(RUN / "data" / "inventory.csv").set_index("islet")
a = R.attach_levels(R.load_areas())
a["year"] = a.time.dt.year
ls_ = pd.read_csv(T / "land_screen.csv").set_index("islet")
keep = set(ls_.index[ls_.retained])
loss = set(ls_.index[ls_.possible_loss])
a_k = a[a.islet.isin(keep | loss)]
a_f, dropped = R.gross_filter(a_k)
rates = pd.read_csv(T / "islet_rates.csv")
prim = lambda fam, col="area_otsu", rob=0: rates[(rates.family == fam) & (rates.series == col) & (rates.robust_slope == rob)
                                                 & (rates.possible_loss == 0)]
e2 = prim("E2").set_index("islet")
y150 = e2[(e2.engineered == 0) & (e2.area_ha >= 1)]
P("E2 primary set:", len(y150), "islets; atolls", y150.atoll.value_counts().to_dict())
s2 = a_f[(a_f.sensor == "s2") & a_f.islet.isin(y150.index)].dropna(subset=["area_otsu", "level_m"]).copy()
s2["osm"] = inv.area_ha.reindex(s2.islet).to_numpy() * 1e4
s2["norm"] = s2.area_otsu / s2.osm
tyr = lambda d: (d.time.dt.year + (d.time.dt.dayofyear - 1) / 365.25).to_numpy()


def gauge(name):
    gid = ATOLLS[name][0]
    g = pd.read_parquet(RUN / "data" / "tides" / f"{gid:03d}.parquet").sort_values("time")
    mean = g[(g.time >= "1999-01-01") & (g.time < "2026-10-01")].level_mm.mean()
    return g, (g.time.astype("int64").to_numpy() / 3.6e12), (g.level_mm.to_numpy() - mean) / 1000.0, mean


# ---------------------------------------------------------------- A. tide alignment: correlation by lag
P("\n=== A. area-level correlation by lag (hours added to the image time), E2 primary islets, pooled within-islet z-scores")
rowsA = []
for name in sorted(s2.atoll.unique()):
    g, tg, lv, _ = gauge(name)
    x = s2[s2.atoll == name].copy()
    tx = x.time.astype("int64").to_numpy() / 3.6e12
    z = x.groupby("islet").norm.transform(lambda v: (v - v.mean()) / (v.std() + 1e-12)).to_numpy()
    out = {}
    for lag in range(-6, 7):
        h = np.interp(tx + lag, tg, lv)
        hz = pd.Series(h).groupby(x.islet.to_numpy()).transform(lambda v: (v - v.mean()) / (v.std() + 1e-12)).to_numpy()
        out[lag] = round(float(np.corrcoef(z, hz)[0, 1]), 3)
    best = min(out, key=lambda k: out[k])
    rowsA.append({"atoll": name, "n": len(x), "r_lag0": out[0], "best_lag_h": best, "r_best": out[best],
                  **{f"r{l:+d}": out[l] for l in (-3, -2, -1, 1, 2, 3)}})
P(pd.DataFrame(rowsA).to_string(index=False))
# per-islet correlation at lag 0 by atoll
pc = s2.groupby("islet").apply(lambda d: np.corrcoef(d.norm, d.level_m)[0, 1] if len(d) > 5 else np.nan).rename("r")
pc = pc.to_frame().join(inv[["atoll", "area_ha"]])
P("per-islet corr(area, level) at lag 0, by atoll: median, share r<-0.3, share r>+0.3")
P(pc.groupby("atoll").r.agg(median="median", neg=lambda v: (v < -0.3).mean(), pos=lambda v: (v > 0.3).mean(), n="size").round(2).to_string())

for col in ("area_fixed", "area_ndwi", "area_otsu_30m"):
    rows = []
    for name in sorted(s2.atoll.unique()):
        x = s2[s2.atoll == name].dropna(subset=[col])
        z = x.groupby("islet")[col].transform(lambda v: (v - v.mean()) / (v.std() + 1e-12))
        hz = x.groupby("islet").level_m.transform(lambda v: (v - v.mean()) / (v.std() + 1e-12))
        rows.append((name, round(float(np.corrcoef(z, hz)[0, 1]), 3)))
    P(f"pooled lag-0 correlation with {col}:", dict(rows))
P("Tarawa and Kiritimati per islet (E2 primary):")
rows = []
for islet, d in s2[s2.atoll.isin(["tarawa", "kiritimati"])].groupby("islet"):
    rows.append({"islet": islet, "ha": inv.area_ha[islet], "n": len(d), "r_otsu": np.corrcoef(d.area_otsu, d.level_m)[0, 1],
                 "r_fixed": np.corrcoef(d.area_fixed.fillna(d.area_fixed.median()), d.level_m)[0, 1],
                 "r_ndwi": np.corrcoef(d.area_ndwi.fillna(d.area_ndwi.median()), d.level_m)[0, 1],
                 "beta_pct_m": 100 * np.polyfit(d.level_m, d.area_otsu, 1)[0] / d.osm.iloc[0], "otsu_over_osm": d.norm.median(),
                 "fixed_over_osm": (d.area_fixed / d.osm).median(), "otsu_t": d.otsu_t.median(), "cv_otsu": d.area_otsu.std() / d.area_otsu.mean(),
                 "rate_corr": y150.rate_corr[islet], "rate_uncorr": y150.rate_uncorr[islet]})
P(pd.DataFrame(rows).round(2).to_string(index=False))
P("for comparison, Funafuti per islet:")
rows = []
for islet, d in s2[s2.atoll == "funafuti"].groupby("islet"):
    rows.append({"islet": islet, "ha": inv.area_ha[islet], "n": len(d), "r_otsu": np.corrcoef(d.area_otsu, d.level_m)[0, 1],
                 "beta_pct_m": 100 * np.polyfit(d.level_m, d.area_otsu, 1)[0] / d.osm.iloc[0], "otsu_over_osm": d.norm.median(),
                 "fixed_over_osm": (d.area_fixed / d.osm).median(), "otsu_t": d.otsu_t.median(), "cv_otsu": d.area_otsu.std() / d.area_otsu.mean()})
P(pd.DataFrame(rows).round(2).to_string(index=False))

# ---------------------------------------------------------------- B. gauge trend vs overpass-time trend
P("\n=== B. per atoll: trend of the water level at image times vs the gauge's own trend over the same window (mm/yr)")
rng = np.random.default_rng(1)
rowsB, annual = [], {}
for name in sorted(s2.atoll.unique()):
    g, tg, lv, mean = gauge(name)
    x = s2[s2.atoll == name]
    u = x.drop_duplicates("tmin").sort_values("time")              # unique image times at this atoll
    tu = tyr(u); hu = u.level_m.to_numpy()
    t0, t1 = u.time.min(), u.time.max()
    gw = g[(g.time >= t0) & (g.time <= t1)].copy()
    daily = gw.groupby(gw.time.dt.floor("D")).level_mm.agg(["mean", "size"])
    daily = daily[daily["size"] >= 20]
    dmean = (daily["mean"].reindex(u.time.dt.floor("D")).to_numpy() - mean) / 1000.0
    okd = np.isfinite(dmean)
    monthly = gw.groupby(gw.time.dt.to_period("M")).level_mm.mean()
    tm = np.array([p.year + (p.month - 0.5) / 12 for p in monthly.index]); mm = (monthly.to_numpy() - mean) / 1000
    boots = [R.theil_sen(tu[i], hu[i]) for i in (rng.integers(0, len(u), len(u)) for _ in range(300))]
    rowsB.append({"atoll": name, "images": len(u), "window": f"{t0.date()}..{t1.date()}",
                  "ts_level_at_images": 1000 * R.theil_sen(tu, hu),
                  "boot95": f"{1000*np.percentile(boots,2.5):.0f}..{1000*np.percentile(boots,97.5):.0f}",
                  "ts_dailymean_on_image_days": 1000 * R.theil_sen(tu[okd], dmean[okd]),
                  "ts_tidal_anomaly_at_images": 1000 * R.theil_sen(tu[okd], hu[okd] - dmean[okd]),
                  "ols_gauge_monthly_means": 1000 * np.polyfit(tm, mm, 1)[0],
                  "ts_gauge_monthly_means": 1000 * R.theil_sen(tm, mm),
                  "mean_hour_utc": round(float(u.time.dt.hour.mean() + u.time.dt.minute.mean() / 60), 2)})
    ann = g[(g.time >= "2014-01-01")].groupby(g.time.dt.year).agg(mean=("level_mm", "mean"), n=("level_mm", "size"),
                                                                     fd=("source", lambda s: (s == "FD").mean()))
    ann["mean"] = (ann["mean"] - mean).round(0)
    annual[name] = ann
B = pd.DataFrame(rowsB)
for c in B.columns:
    if B[c].dtype == float:
        B[c] = B[c].round(1)
P(B.to_string(index=False))
P("\ngauge annual means (mm, relative to the 1999-2026 mean), hours, FD share -- the RQ->FD seam is where fd goes 0->1")
P(pd.concat(annual, axis=1).swaplevel(axis=1).sort_index(axis=1, level=0, sort_remaining=False)[["mean", "fd"]].astype(float).round(2).to_string())

# ---------------------------------------------------------------- C. joint and quadratic tide fits
P("\n=== C. tide regression variants on the E2 primary set: two-step OLS (study), joint area~level+time, quadratic in level")
rowsC = []
for islet, d in s2.groupby("islet"):
    if len(d) < 20:
        continue
    ref = inv.area_ha[islet] * 1e4
    t, yv, h = tyr(d), d.area_otsu.to_numpy(float), d.level_m.to_numpy(float)
    b_ts = np.polyfit(h, yv, 1)[0]
    X = np.column_stack([np.ones_like(h), h, t - t.mean()])
    cj = np.linalg.lstsq(X, yv, rcond=None)[0]
    Xq = np.column_stack([np.ones_like(h), h, h ** 2])
    cq, res, *_ = np.linalg.lstsq(Xq, yv, rcond=None)
    # t-stat of the quadratic term
    dof = len(h) - 3
    s2e = float(((yv - Xq @ cq) ** 2).sum() / dof)
    cov = s2e * np.linalg.inv(Xq.T @ Xq)
    tq = cq[2] / np.sqrt(cov[2, 2])
    rc = R.theil_sen(t, 100 * (yv - b_ts * h) / ref)
    ru = R.theil_sen(t, 100 * yv / ref)
    rj = R.theil_sen(t, 100 * (yv - cj[1] * h) / ref)
    rq = R.theil_sen(t, 100 * (yv - cq[1] * h - cq[2] * h ** 2) / ref)
    # curvature index: mean linear-fit residual in the top level tertile minus the middle tertile, as % of ref
    resid = yv - np.polyval(np.polyfit(h, yv, 1), h)
    q = np.quantile(h, [1 / 3, 2 / 3])
    curv = 100 * (resid[h > q[1]].mean() - resid[(h > q[0]) & (h <= q[1])].mean()) / ref
    rowsC.append({"islet": islet, "atoll": inv.atoll[islet], "area_ha": inv.area_ha[islet], "n": len(d),
                  "beta_pct_m": 100 * b_ts / ref, "beta_joint_pct_m": 100 * cj[1] / ref, "ols_trend_pct_yr": 100 * cj[2] / ref,
                  "rate_corr": rc, "rate_uncorr": ru, "rate_joint": rj, "rate_quad": rq, "t_quad": tq, "curv_pct": curv,
                  "level_range_m": np.ptp(h), "r2_lin": 1 - resid.var() / yv.var()})
C = pd.DataFrame(rowsC).set_index("islet")
C.to_csv(OUT / "c_tide_fit_variants.csv")
P("islets:", len(C))
P("mean |uncorr-corr| (H2 stat): two-step %.3f  joint %.3f  quadratic %.3f" % (
    (C.rate_uncorr - C.rate_corr).abs().mean(), (C.rate_uncorr - C.rate_joint).abs().mean(), (C.rate_uncorr - C.rate_quad).abs().mean()))
P("pooled mean corrected rate: two-step %.3f  joint %.3f  quadratic %.3f;  mean |joint-two-step| %.3f, mean |quad-two-step| %.3f" % (
    C.rate_corr.mean(), C.rate_joint.mean(), C.rate_quad.mean(), (C.rate_joint - C.rate_corr).abs().mean(), (C.rate_quad - C.rate_corr).abs().mean()))
P("beta two-step vs joint: median |diff| %.1f %%/m; corr %.3f" % ((C.beta_pct_m - C.beta_joint_pct_m).abs().median(), np.corrcoef(C.beta_pct_m, C.beta_joint_pct_m)[0, 1]))
P("quadratic term |t|>2.6 (p<0.01) in %.0f%% of islets; median curvature index %.2f%% of area (top vs middle level tertile); median R2 linear %.2f" % (
    100 * (C.t_quad.abs() > 2.6).mean(), C.curv_pct.median(), C.r2_lin.median()))
P(C.groupby("atoll").agg(n=("n", "size"), beta=("beta_pct_m", "median"), r2=("r2_lin", "median"), curv=("curv_pct", "median"),
                         sig_quad=("t_quad", lambda v: (v.abs() > 2.6).mean()), rate_corr=("rate_corr", "mean"),
                         rate_joint=("rate_joint", "mean"), rate_quad=("rate_quad", "mean"), lvl_range=("level_range_m", "median")).round(2).to_string())
P("by size: mean |bias| two-step / quadratic; mean corrected rate two-step / quadratic")
P(C.groupby(pd.cut(C.area_ha, [0, 5, 20, 1e9]), observed=True).apply(lambda g: pd.Series({
    "n": len(g), "abs_bias": (g.rate_uncorr - g.rate_corr).abs().mean(), "abs_bias_quad": (g.rate_uncorr - g.rate_quad).abs().mean(),
    "median_abs_bias": (g.rate_uncorr - g.rate_corr).abs().median(), "rate": g.rate_corr.mean(), "rate_quad": g.rate_quad.mean(),
    "median_beta": g.beta_pct_m.median()})).round(3).to_string())
# wrong-sign or insignificant tide slopes
rows = []
for islet, d in s2.groupby("islet"):
    if islet not in C.index:
        continue
    ref = inv.area_ha[islet] * 1e4; t, yv, h = tyr(d), d.area_otsu.to_numpy(float), d.level_m.to_numpy(float)
    b, c0 = np.polyfit(h, yv, 1); r = yv - (b * h + c0)
    se_b = np.sqrt(r.var(ddof=2) / ((h - h.mean()) ** 2).sum())
    tb = b / se_b
    b_c = b if tb < -2 else 0.0                      # keep the slope only if it is negative beyond 2 SE
    rows.append({"islet": islet, "atoll": inv.atoll[islet], "t_beta": tb, "beta_pos": b > 0, "rate_corr_constrained": R.theil_sen(t, 100 * (yv - b_c * h) / ref)})
W = pd.DataFrame(rows).set_index("islet").join(C[["rate_corr", "rate_uncorr", "area_ha"]])
P("tide slope positive (wrong sign) in %d of %d islets; not significantly negative (t > -2) in %d; by atoll:" % (W.beta_pos.sum(), len(W), (W.t_beta > -2).sum()))
P(W.groupby("atoll").agg(n=("beta_pos", "size"), beta_pos=("beta_pos", "sum"), not_sig=("t_beta", lambda v: (v > -2).sum())).to_string())
P("islets with positive beta: mean |uncorr-corr| %.2f, mean corrected rate %.2f, mean uncorrected rate %.2f" % (
    (W[W.beta_pos].rate_uncorr - W[W.beta_pos].rate_corr).abs().mean(), W[W.beta_pos].rate_corr.mean(), W[W.beta_pos].rate_uncorr.mean()))
W["bias_c"] = (W.rate_uncorr - W.rate_corr_constrained).abs()
P("with the slope set to 0 unless significantly negative: H2 mean |bias| %.3f CI %s; pooled corrected rate %.3f; by atoll %s" % (
    W.bias_c.mean(), R.boot_mean(W.reset_index(), "bias_c"), W.rate_corr_constrained.mean(), W.groupby("atoll").rate_corr_constrained.mean().round(2).to_dict()))
# H2 restricted to >= 5 ha, and median statistic
big = C[C.area_ha >= 5].copy(); big["bias"] = (big.rate_uncorr - big.rate_corr).abs()
P("H2 on >=5 ha only: n %d mean |bias| %.3f  CI %s" % (len(big), big.bias.mean(), R.boot_mean(big, "bias")))

# ---------------------------------------------------------------- D. H2 decomposition
P("\n=== D. H2: bias against beta x level trend (near-identity?)")
h2i = pd.read_csv(T / "h2_diagnostics_islets.csv").set_index("islet")
C2 = C.join(h2i[["level_trend_m_yr", "perm_abs_bias"]])
pred = C2.beta_pct_m * C2.level_trend_m_yr
bias = C2.rate_uncorr - C2.rate_corr
P("corr(bias, beta x TS level trend) = %.3f; regression slope %.2f; mean |bias - pred| %.3f vs mean |bias| %.3f" % (
    np.corrcoef(bias, pred)[0, 1], np.polyfit(pred, bias, 1)[0], (bias - pred).abs().mean(), bias.abs().mean()))
P("per-islet TS trend of level at that islet's own image times (recomputed) vs h2_diagnostics_islets.csv; and the union-of-acquisitions value above")
rows = []
for islet, d in s2.groupby("islet"):
    rows.append({"islet": islet, "atoll": inv.atoll[islet], "n": len(d), "lt_mm": 1000 * R.theil_sen(tyr(d), d.level_m.to_numpy()),
                 "study_lt_mm": 1000 * h2i.level_trend_m_yr.get(islet, np.nan), "first": d.time.min().year, "last": d.time.max().year})
LT = pd.DataFrame(rows).set_index("islet")
P(LT.groupby("atoll").agg(n_islets=("n", "size"), median_recomputed=("lt_mm", "median"), median_study=("study_lt_mm", "median"),
                          p10=("lt_mm", lambda v: v.quantile(.1)), p90=("lt_mm", lambda v: v.quantile(.9)), first=("first", "median"), last=("last", "median")).round(1).to_string())
P("max |recomputed - study| per islet: %.2f mm/yr" % (LT.lt_mm - LT.study_lt_mm).abs().max())
P("the same with OLS instead of Theil-Sen (exact identity expected):")
ols_b = []
for islet, d in s2.groupby("islet"):
    if islet not in C.index:
        continue
    ref = inv.area_ha[islet] * 1e4; t, yv, h = tyr(d), d.area_otsu.to_numpy(float), d.level_m.to_numpy(float)
    b = np.polyfit(h, yv, 1)[0]
    ols_b.append((100 * np.polyfit(t, yv, 1)[0] / ref - 100 * np.polyfit(t, yv - b * h, 1)[0] / ref, 100 * b / ref * np.polyfit(t, h, 1)[0]))
ols_b = np.array(ols_b)
P("corr %.4f" % np.corrcoef(ols_b[:, 0], ols_b[:, 1])[0, 1])
P("noise floor with beta kept (SE(beta) x |level trend|), mean over islets:")
se_terms = []
for islet, d in s2.groupby("islet"):
    if islet not in C.index:
        continue
    ref = inv.area_ha[islet] * 1e4; t, yv, h = tyr(d), d.area_otsu.to_numpy(float), d.level_m.to_numpy(float)
    b, c0 = np.polyfit(h, yv, 1); r = yv - (b * h + c0)
    se_b = np.sqrt(r.var(ddof=2) / ((h - h.mean()) ** 2).sum())
    se_terms.append(100 * se_b / ref * abs(C2.level_trend_m_yr[islet]))
P("%.3f %%/yr" % np.mean(se_terms))

# ---------------------------------------------------------------- E. guard
P("\n=== E. the sensor-step guard")
gl_all = a_f[(a_f.sensor == "LC08") & (a_f.year >= 2016) & (a_f.year <= 2021)]
gs_all = a_f[(a_f.sensor == "s2") & (a_f.year >= 2016) & (a_f.year <= 2021)]
cand = [i for i in inv.index if i in keep and inv.engineered[i] == 0 and inv.area_ha[i] >= 5]


def guard_set(min_scenes, min_span, ls_filter=None, s2col="area_otsu_30m"):
    R.MIN_SCENES = min_scenes
    rows = []
    for islet in cand:
        gl = gl_all[gl_all.islet == islet]
        if ls_filter is not None:
            gl = gl[ls_filter(gl)]
        gs = gs_all[gs_all.islet == islet]
        ref = inv.area_ha[islet] * 1e4
        rl = R.islet_rate(gl, "area_otsu", ref, min_span=min_span) if len(gl) else None
        rs = R.islet_rate(gs, s2col, ref, min_span=min_span) if len(gs) else None
        if rl and rs:
            rows.append({"islet": islet, "atoll": inv.atoll[islet], "area_ha": inv.area_ha[islet], "n_ls": rl["n"], "n_s2": rs["n"],
                         "span_ls": rl["span"], "span_s2": rs["span"], "rate_ls": rl["rate_corr"], "rate_s2": rs["rate_corr"],
                         "beta_ls": 100 * rl["tide_slope_m2_per_m"] / ref, "beta_s2": 100 * rs["tide_slope_m2_per_m"] / ref,
                         "diff": rl["rate_corr"] - rs["rate_corr"]})
    R.MIN_SCENES = 20
    return pd.DataFrame(rows)


base = guard_set(20, 4.5)
P("baseline guard set (20 scenes, 4.5 y):")
P(base.round(2).to_string(index=False))
P("mean diff %.3f CI %s" % (base["diff"].mean(), R.boot_mean(base, "diff")))
P("\nscan over minimum scenes x minimum span:")
for ms in (15, 20):
    for sp in (3.0, 3.5, 4.0, 4.5, 5.0, 5.5):
        gset = guard_set(ms, sp)
        if len(gset):
            P(f"  min_scenes {ms} min_span {sp}: islets {len(gset):3d}  mean diff {gset['diff'].mean():+.2f}  CI {R.boot_mean(gset, 'diff')}  "
              f"atolls {gset.atoll.value_counts().to_dict()}  median diff {gset['diff'].median():+.2f}")
        else:
            P(f"  min_scenes {ms} min_span {sp}: 0 islets")
P("\nS2 at 10 m vs S2 at 30 m for the same islets/window (same scenes): ", end="")
g10 = guard_set(20, 4.5, s2col="area_otsu")
m = base.set_index("islet").join(g10.set_index("islet")[["rate_s2"]], rsuffix="_10m")
P("mean (30m - 10m) %.3f; mean (LS - S2_10m) %.3f" % ((m.rate_s2 - m.rate_s2_10m).mean(), (m.rate_ls - m.rate_s2_10m).mean()))
gl_all = gl_all.copy(); gl_all["tier"] = gl_all.scene.str[-2:]
used = gl_all[gl_all.islet.isin(base.islet)].dropna(subset=["area_otsu"])
P("\nLandsat 8 scenes used by the 13 guard islets, tier by year:")
P(pd.crosstab(used.year, used.tier).to_string())
P("tier of the row kept after de-duplication by acquisition minute (all LC08 2016-2021 rows, guard islets):",
  used.drop_duplicates(["islet", "tmin"]).tier.value_counts().to_dict())
# how many acquisitions had several processings available
dup = a[(a.sensor == "LC08")].groupby(["islet", "tmin"]).size()
P("LC08 rows per (islet, acquisition minute) after load_areas dedup: max", int(dup.max()), "(load_areas already dedups; raw parquet check below)")
raw = pd.concat([pd.read_parquet(p, columns=["islet", "scene", "datetime", "sensor"]) for p in sorted((RUN / "data" / "areas").glob("*_l1.parquet"))])
raw = raw[raw.sensor == "LC08"]; raw["tmin"] = pd.to_datetime(raw.datetime, utc=True, format="ISO8601").dt.floor("min"); raw["tier"] = raw.scene.str[-2:]
multi = raw.groupby(["islet", "tmin"]).tier.agg(lambda s: "+".join(sorted(set(s))))
P("raw LC08 (islet, acquisition) tier combinations:", multi.value_counts().head(8).to_dict())
P("\nnormalised corrected area by tier within the guard islets (tier mean minus islet mean, % of OSM area):")
rows = []
for islet, d in used.groupby("islet"):
    d = d.dropna(subset=["level_m"]); ref = inv.area_ha[islet] * 1e4
    b = np.polyfit(d.level_m, d.area_otsu, 1)[0]
    nc = 100 * (d.area_otsu - b * d.level_m) / ref
    for tier, v in nc.groupby(d.tier):
        rows.append({"islet": islet, "tier": tier, "n": len(v), "dev": v.mean() - nc.mean()})
tv = pd.DataFrame(rows)
P(tv.groupby("tier").apply(lambda g: pd.Series({"islets": len(g), "scenes": g.n.sum(), "mean_dev": g.dev.mean(), "median_dev": g.dev.median()})).round(2).to_string())
P("\nguard with T1-only Landsat 8 scenes:")
t1 = guard_set(20, 4.5, ls_filter=lambda g: g.scene.str.endswith("T1"))
P("  islets %d mean diff %s" % (len(t1), (round(t1['diff'].mean(), 3), R.boot_mean(t1, 'diff')) if len(t1) else None))
t12 = guard_set(20, 4.5, ls_filter=lambda g: ~g.scene.str.endswith("RT"))
P("guard without RT scenes: islets %d mean diff %s" % (len(t12), (round(t12['diff'].mean(), 3), R.boot_mean(t12, 'diff')) if len(t12) else None))
t15 = guard_set(15, 4.5, ls_filter=lambda g: ~g.scene.str.endswith("RT"))
P("guard without RT scenes, min 15 scenes: islets %d mean diff %s" % (len(t15), (round(t15['diff'].mean(), 3), R.boot_mean(t15, 'diff')) if len(t15) else None))
P("\nyear means of normalised corrected area, Landsat 8 vs S2-30m, averaged over the 13 guard islets (% of OSM area, islet-demeaned):")
rows = []
for islet in base.islet:
    ref = inv.area_ha[islet] * 1e4
    for lab, d, col in (("LS", gl_all[gl_all.islet == islet], "area_otsu"), ("S2", gs_all[gs_all.islet == islet], "area_otsu_30m")):
        d = d.dropna(subset=[col, "level_m"])
        b = np.polyfit(d.level_m, d[col], 1)[0]
        nc = 100 * (d[col] - b * d.level_m) / ref
        for yv, v in nc.groupby(d.year):
            rows.append({"islet": islet, "sensor": lab, "year": yv, "n": len(v), "dev": v.mean() - nc.mean(), "level": nc.mean()})
ym = pd.DataFrame(rows)
P(ym.groupby(["sensor", "year"]).agg(islets=("islet", "nunique"), scenes=("n", "sum"), dev=("dev", "mean")).round(2).unstack(0).to_string())
P("mean normalised area level (uncorrected for tide) LS vs S2-30m, guard islets:",
  ym.drop_duplicates(["islet", "sensor"]).groupby("sensor")["level"].mean().round(1).to_dict())

# ---------------------------------------------------------------- F. E1 internal step
P("\n=== F. E1 (1999-2015): a Landsat 7 -> Landsat 8 step inside the early epoch?")
e1 = prim("E1").set_index("islet")
h1 = e1[["rate_corr", "atoll", "engineered", "area_ha"]].join(e2[["rate_corr"]], rsuffix="_e2", how="inner")
h1 = h1[(h1.engineered == 0) & (h1.area_ha >= 5)]
P("H1 islets:", len(h1), h1.atoll.value_counts().to_dict())
E1 = a_f[a_f.sensor.isin(["LT05", "LE07", "LC08"]) & (a_f.year <= 2015) & a_f.islet.isin(h1.index)].dropna(subset=["area_otsu", "level_m"]).copy()
E1["tier"] = E1.scene.str[-2:]
P("E1 usable scenes for the H1 islets by platform and period:")
E1["period"] = pd.cut(E1.year, [1998, 2003, 2012, 2015], labels=["1999-2003", "2004-2012", "2013-2015"])
P(pd.crosstab(E1.platform if "platform" in E1 else E1.sensor, E1.period).to_string())
P(pd.crosstab(E1.sensor, E1.tier).to_string())
rows = []
for islet, d in E1.groupby("islet"):
    ref = inv.area_ha[islet] * 1e4
    t, yv, h = tyr(d), d.area_otsu.to_numpy(float), d.level_m.to_numpy(float)
    l8 = (d.sensor == "LC08").to_numpy().astype(float)
    b = np.polyfit(h, yv, 1)[0]
    nc = 100 * (yv - b * h) / ref
    X1 = np.column_stack([np.ones_like(t), h, t - t.mean()])
    X2 = np.column_stack([np.ones_like(t), h, t - t.mean(), l8])
    c1 = np.linalg.lstsq(X1, yv, rcond=None)[0]
    c2 = np.linalg.lstsq(X2, yv, rcond=None)[0] if 0 < l8.sum() < len(l8) else [np.nan] * 4
    rows.append({"islet": islet, "atoll": inv.atoll[islet], "n": len(d), "n_l7": int((d.sensor == "LE07").sum()), "n_l8": int(l8.sum()),
                 "n_l5": int((d.sensor == "LT05").sum()), "rate_ts": h1.rate_corr[islet],
                 "ols_trend": 100 * c1[2] / ref, "ols_trend_with_platform_fe": 100 * c2[2] / ref, "l8_step_pct": 100 * c2[3] / ref,
                 "l8_minus_l7_mean_nc": nc[l8 == 1].mean() - nc[l8 == 0].mean() if 0 < l8.sum() < len(l8) else np.nan,
                 "resid_sd_pct": 100 * np.std(yv - np.polyval(np.polyfit(h, yv, 1), h)) / ref})
F = pd.DataFrame(rows).set_index("islet")
F.to_csv(OUT / "f_e1_platform_step.csv")
P(F.describe().loc[["mean", "50%", "min", "max"]].round(2).to_string())
P("corr(E1 Theil-Sen rate, L8-minus-L7 corrected-area step) = %.2f; mean E1 rate %.2f -> with a platform fixed effect (OLS) %.2f (plain OLS %.2f)" % (
    np.corrcoef(F.dropna().rate_ts, F.dropna().l8_minus_l7_mean_nc)[0, 1], F.rate_ts.mean(), F.ols_trend_with_platform_fe.mean(), F.ols_trend.mean()))
P("E1 Landsat residual SD after the tide fit, median %.0f%% of OSM area (E2 Sentinel-2: %.0f%%)" % (
    F.resid_sd_pct.median(), (100 * np.sqrt(1 - C.r2_lin) * s2.groupby("islet").norm.std().reindex(C.index)).median()))

# ---------------------------------------------------------------- G. S2 baseline step, offsets
P("\n=== G. Sentinel-2: a step at the processing-baseline change (2022-01-25)? islet-level mean of normalised corrected area, +/-2 y")
scn = pd.concat([pd.read_parquet(p, columns=["id", "boa_offset_applied", "swir16_offset", "baseline"]) for p in sorted((RUN / "data" / "scenes").glob("*_s2.parquet"))]).drop_duplicates("id").set_index("id")
s2c = s2.copy()
for islet, d in s2c.groupby("islet"):
    b = np.polyfit(d.level_m, d.area_otsu, 1)[0]
    s2c.loc[d.index, "nc"] = 100 * (d.area_otsu - b * d.level_m) / (inv.area_ha[islet] * 1e4)
s2c["nc_dm"] = s2c.nc - s2c.groupby("islet").nc.transform("mean")
for cut in ("2020-01-25", "2022-01-25", "2024-01-25"):
    c = pd.Timestamp(cut, tz="UTC")
    w = s2c[(s2c.time >= c - pd.Timedelta(days=730)) & (s2c.time < c + pd.Timedelta(days=730))]
    per = w.groupby(["islet", w.time >= c]).nc_dm.agg(["mean", "size"]).unstack()
    per = per[(per["size"][False] >= 10) & (per["size"][True] >= 10)]
    step = per["mean"][True] - per["mean"][False]
    P(f"  cut {cut}: islets {len(step)}, mean after-minus-before {step.mean():+.2f}% of area (median {step.median():+.2f}); by atoll "
      f"{step.groupby(inv.atoll.reindex(step.index)).mean().round(2).to_dict()}")
s2c = s2c.join(scn, on="scene")
s2c["grp"] = s2c.boa_offset_applied.astype(str) + "/" + s2c.swir16_offset.astype(str)
P("scene groups (boa_offset_applied/metadata offset) among used E2 records:", s2c.grp.value_counts().to_dict())
P("Otsu threshold and normalised area by offset group, islet-demeaned within the same calendar year (2022+ where groups coexist):")
late = s2c[s2c.year >= 2022].copy()
for col in ("otsu_t", "nc"):
    late[col + "_dm"] = late[col] - late.groupby(["islet", "year"])[col].transform("mean")
P(late.groupby("grp").agg(n=("nc", "size"), otsu_t_dm=("otsu_t_dm", "mean"), nc_dm=("nc_dm", "mean")).round(3).to_string())
P("otsu_t by group overall (median):", s2c.groupby("grp").otsu_t.median().round(3).to_dict())

# ---------------------------------------------------------------- H. land screen
P("\n=== H. the land screen (D5)")
P("land_share distribution by atoll (counts in bins):")
P(pd.crosstab(ls_.atoll, pd.cut(ls_.land_share, [-0.01, 0.05, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0])).to_string())
bord = ls_[(ls_.land_share > 0.3) & (ls_.land_share < 0.7)][["atoll", "osm_ha", "scenes", "land_share", "median_s2_to_osm", "share_2016_18", "share_2024_26", "retained"]]
P("borderline features (0.3 < share < 0.7):"); P(bord.round(2).to_string())
gain = ls_[~ls_.retained & (ls_.share_2024_26 >= 0.5) & (ls_.share_2016_18 < 0.5)]
P("non-retained features dry in >= half of 2024-26 scenes but not in 2016-18 (no 'possible gain' flag exists):", len(gain), gain.index.tolist()[:10])
P("removed features outside Penrhyn:")
P(ls_[~ls_.retained & (ls_.atoll != "penrhyn")][["atoll", "osm_ha", "scenes", "land_share", "median_s2_to_osm", "share_2016_18", "share_2024_26"]].round(2).to_string())
P("Penrhyn removed: median S2-Otsu/OSM ratio %.2f (IQR %.2f-%.2f); Penrhyn kept: %.2f" % (
    ls_[~ls_.retained & (ls_.atoll == "penrhyn")].median_s2_to_osm.median(), *ls_[~ls_.retained & (ls_.atoll == "penrhyn")].median_s2_to_osm.quantile([.25, .75]),
    ls_[ls_.retained & (ls_.atoll == "penrhyn")].median_s2_to_osm.median()))
# tide dependence of 'dry land' for retained small islets and borderline features
ss = a[(a.sensor == "s2") & a.area_otsu.notna() & a.level_m.notna()].copy()
ss["osm"] = inv.area_ha.reindex(ss.islet).to_numpy() * 1e4
ss["land"] = ss.area_fixed >= 0.1 * ss.osm
ss["lq"] = ss.groupby("atoll").level_m.transform(lambda v: pd.qcut(v, 4, labels=["low", "midlow", "midhigh", "high"]))
small_keep = ss[ss.islet.isin(ls_.index[ls_.retained & (ls_.osm_ha < 5)])]
P("retained islets < 5 ha: share of scenes 'dry' by level quartile:", small_keep.groupby("lq", observed=True).land.mean().round(3).to_dict())
bb = ss[ss.islet.isin(bord.index)]
P("borderline features: share 'dry' by level quartile:", bb.groupby("lq", observed=True).land.mean().round(3).to_dict())
P("kwajalein_078 by year: dry share and S2/OSM ratio")
k = ss[ss.islet == "kwajalein_078"]
P(k.groupby("year").agg(n=("land", "size"), dry=("land", "mean"), ratio=("area_otsu", lambda v: (v / k.osm.iloc[0]).median()), fixed_ratio=("area_fixed", lambda v: (v / k.osm.iloc[0]).median())).round(2).T.to_string())

# ---------------------------------------------------------------- I. coverage, report numbers
P("\n=== I. coverage and the report's numbers")
cov = s2.groupby("atoll").agg(first=("time", "min"), last=("time", "max"), islets=("islet", "nunique"))
cov["span_y"] = ((cov["last"] - cov["first"]).dt.days / 365.25).round(1)
cov["first"] = cov["first"].dt.date; cov["last"] = cov["last"].dt.date
P(cov.to_string())
P("median per-islet span (years) in the E2 primary set by atoll:", y150.groupby("atoll").span.median().round(1).to_dict())
P("median usable images per islet: E2 primary %d; E1 (H1 islets) %d; E2 (H1 islets) %d" % (y150.n.median(), e1.reindex(h1.index).n.median(), e2.reindex(h1.index).n.median()))
P("pooled E2 corrected rate: mean %.3f median %.3f CI %s" % (y150.rate_corr.mean(), y150.rate_corr.median(), R.boot_mean(y150.reset_index(), "rate_corr")))
P("inventory features >= 1 ha:", int((inv.area_ha >= 1).sum()), "; measured (land_screen rows):", len(ls_),
  "; never got an Otsu area:", sorted(set(inv.index[inv.area_ha >= 1]) - set(ls_.index)))
P("engineered >= 1 ha:", int(((inv.area_ha >= 1) & (inv.engineered == 1)).sum()), "non-engineered >= 1 ha:", int(((inv.area_ha >= 1) & (inv.engineered == 0)).sum()))
P("retained non-engineered >= 1 ha by atoll:", ls_[ls_.retained & (inv.engineered.reindex(ls_.index) == 0)].groupby("atoll").size().to_dict())
P("of which with an E2 rate:", y150.atoll.value_counts().to_dict())
P("1-5 ha count: [1,5) %d, (1,5] %d" % (((y150.area_ha >= 1) & (y150.area_ha < 5)).sum(), ((y150.area_ha > 1) & (y150.area_ha <= 5)).sum()))
P("E2 usable images per year (primary islets, unique acquisitions per atoll summed):", s2.drop_duplicates(["atoll", "tmin"]).groupby("year").size().to_dict())

# ---------------------------------------------------------------- J. gross filter
P("\n=== J. without the gross-failure filter")
s2n = a_k[(a_k.sensor == "s2") & a_k.islet.isin(y150.index)].dropna(subset=["area_otsu", "level_m"])
rows = []
for islet, d in s2n.groupby("islet"):
    r = R.islet_rate(d, "area_otsu", inv.area_ha[islet] * 1e4)
    if r:
        rows.append({"islet": islet, "atoll": inv.atoll[islet], "bias": abs(r["rate_uncorr"] - r["rate_corr"]), "rate_corr": r["rate_corr"]})
J = pd.DataFrame(rows)
P("islets %d; H2 mean |bias| %.3f CI %s; pooled rate %.3f" % (len(J), J.bias.mean(), R.boot_mean(J, "bias"), J.rate_corr.mean()))
P("\ndone")
