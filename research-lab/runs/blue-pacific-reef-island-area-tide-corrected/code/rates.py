"""Tide correction, rates, the sensor-step guard, H1 and H2 (plan sections 3-4).

Inputs:
- data/areas/<atoll>_<s2|ls>.parquet: per islet and scene;
- data/tides/<gauge>.parquet: hourly sea level;
- data/inventory.csv.

Writes:
- results/tables/islet_rates.csv: one row per islet x epoch x series;
- results/tables/h1_h2.json.

Families and epochs:
  E1     Landsat 5/7/8 Collection 1 Level-1 (D1), 1999-2015 (corrected with a Landsat slope fitted on E1)
  E2     Sentinel-2 at 10 m, 2016-2026-09 (corrected with a Sentinel-2 slope fitted on E2)
  guard  2016-2021 (D1): Collection 1 Landsat 8, and Sentinel-2 at 30 m, each corrected with its own slope
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inventory import ATOLLS  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
SEED, B = 20261022, 2000
MIN_SCENES, MIN_SPAN, GUARD_MIN_SPAN = 20, 6.0, 4.5      # D6: the guard window is 2016-2021


def load_areas():
    parts = []
    for p in sorted((RUN / "data" / "areas").glob("*.parquet")):
        d = pd.read_parquet(p)
        if d.empty or "islet" not in d:
            continue
        if "error" in d:
            d = d[d.error.isna()]
        parts.append(d[d.islet.astype(str) != ""])
    a = pd.concat(parts, ignore_index=True)
    a["time"] = pd.to_datetime(a.datetime, utc=True, format="ISO8601")
    # one row per islet and acquisition (overlapping Sentinel-2 tiles list the same pass twice)
    a["tmin"] = a.time.dt.floor("min")
    # D7: for Landsat Collection 1, keep the final tier of an acquisition (T1, then T2, then Real-Time RT)
    a["tier_rank"] = a.scene.astype(str).str[-2:].map({"T1": 0, "T2": 1, "RT": 2}).fillna(0)
    a = a.sort_values(["tier_rank", "aoi_pixels", "clear"], ascending=[True, False, False]) \
         .drop_duplicates(["islet", "sensor", "tmin"])
    return a


LAND_RATIO, LAND_SHARE, MAD_Z = 0.10, 0.5, 5.0
AREA_COLS = ["area_otsu", "area_fixed", "area_ndwi", "area_otsu_30m"]


def land_screen(a, inv):
    """D5 (revised): an OSM feature is an islet if dry land -- MNDWI below 0, SWIR brighter than green, which no water
    depth gives -- covers at least 10% of its OSM area in at least half of its clear Sentinel-2 scenes. Otsu cannot
    decide this: in an all-water window it splits shallow from deep water. One decision from Sentinel-2 covers both
    epochs."""
    s = a[(a.sensor == "s2") & a.area_otsu.notna()].copy()
    s["osm_m2"] = inv.area_ha.reindex(s.islet).to_numpy() * 1e4
    s["land"] = s.area_fixed >= LAND_RATIO * s.osm_m2
    s["ratio"] = s.area_otsu / s.osm_m2
    g = s.groupby("islet")
    t = pd.DataFrame({"atoll": g.atoll.first(), "osm_ha": g.osm_m2.first() / 1e4, "scenes": g.size(),
                      "land_share": g.land.mean(), "median_s2_to_osm": g.ratio.median()})
    by_year = s.groupby(["islet", "year"]).land.mean().unstack()
    early = s[s.year <= 2018].groupby("islet").land.mean()
    late = s[s.year >= 2024].groupby("islet").land.mean()
    t["share_2016_18"], t["share_2024_26"] = early, late
    t["retained"] = t.land_share >= LAND_SHARE
    t["possible_loss"] = ~t.retained & (t.share_2016_18 >= LAND_SHARE) & (t.share_2024_26 < LAND_SHARE)
    t = t.join(by_year.add_prefix("share_"), how="left")
    t.reset_index().to_csv(T / "land_screen.csv", index=False)
    return t


def gross_filter(a):
    """D5: within each islet, sensor family and area series, a value more than 5 scaled MADs of log area from the
    islet's median is set aside (NaN). Returns the filtered frame and the share set aside per series and family."""
    a = a.copy()
    fam = np.where(a.sensor == "s2", "s2", "landsat")
    dropped = {}
    for col in AREA_COLS:
        if col not in a:
            continue
        lg = np.log(a[col].where(a[col] > 0))
        key = [a.islet, fam]
        med = lg.groupby(key).transform("median")
        mad = (lg - med).abs().groupby(key).transform("median") * 1.4826
        z = (lg - med) / mad.where(mad > 0)
        bad = (z.abs() > MAD_Z) | (a[col].notna() & ~(a[col] > 0))
        for f in ("s2", "landsat"):
            m = (fam == f) & a[col].notna()
            dropped[f"{col}_{f}"] = round(float(bad[m].mean()), 4) if m.any() else None
        a.loc[bad, col] = np.nan
    return a, dropped


def attach_levels(a):
    out = []
    for name, (gid, _) in ATOLLS.items():
        g = pd.read_parquet(RUN / "data" / "tides" / f"{gid:03d}.parquet").sort_values("time")
        mean = g[(g.time >= "1999-01-01") & (g.time < "2026-10-01")].level_mm.mean()
        tg = g.time.astype("int64").to_numpy() / 3.6e12          # hours
        lv = (g.level_mm.to_numpy() - mean) / 1000.0             # metres relative to the 1999-2026 mean
        x = a[a.atoll == name].copy()
        tx = x.time.astype("int64").to_numpy() / 3.6e12
        i = np.searchsorted(tg, tx)
        ok = (i > 0) & (i < len(tg))
        i = np.clip(i, 1, len(tg) - 1)
        before, after = tx - tg[i - 1], tg[i] - tx
        ok &= (before <= 2.0) & (after <= 2.0)                    # a gauge reading within 2 h on each side
        x["level_m"] = np.where(ok, np.interp(tx, tg, lv), np.nan)
        out.append(x)
    return pd.concat(out, ignore_index=True)


def theil_sen(t, y):
    """Median of pairwise slopes over every pair with distinct times (D7: the earlier dt > 0 mask on unsorted rows
    dropped about half of the pairs)."""
    i, j = np.triu_indices(len(t), 1)
    dt = t[j] - t[i]
    m = np.abs(dt) > 1e-6
    return float(np.median((y[j] - y[i])[m] / dt[m])) if m.any() else np.nan


def islet_rate(df, col, ref_m2, robust=False, min_span=MIN_SPAN):
    """(rate %/yr corrected, rate %/yr uncorrected, tide slope m2/m, n, span) for one islet's series. D3: the Theil-Sen
    slope is taken on area in m2 and expressed as a percentage of one sensor-independent reference, the islet's OSM
    area, so that Landsat's mixed-pixel inflation of absolute area does not rescale its rates."""
    d = df.dropna(subset=[col, "level_m"])
    if len(d) < MIN_SCENES:
        return None
    t = (d.time.dt.year + (d.time.dt.dayofyear - 1) / 365.25).to_numpy()
    span = t.max() - t.min()
    if span < min_span:
        return None
    y, h = d[col].to_numpy(float), d.level_m.to_numpy(float)
    if robust:
        from sklearn.linear_model import HuberRegressor
        beta = float(HuberRegressor().fit(h.reshape(-1, 1), y).coef_[0])
    else:
        beta = float(np.polyfit(h, y, 1)[0]) if np.ptp(h) > 0 else 0.0
    yc = y - beta * h
    rc = theil_sen(t, 100 * yc / ref_m2)
    ru = theil_sen(t, 100 * y / ref_m2)
    return {"rate_corr": rc, "rate_uncorr": ru, "tide_slope_m2_per_m": beta, "n": len(d), "span": round(span, 2),
            "median_area_ha": float(np.median(yc) / 1e4)}


def boot_mean(df, col, by="atoll"):
    rng = np.random.default_rng(SEED)
    groups = [g[col].to_numpy() for _, g in df.groupby(by)]
    m = []
    for _ in range(B):
        m.append(np.mean(np.concatenate([g[rng.integers(0, len(g), len(g))] for g in groups])))
    return [round(float(np.percentile(m, 2.5)), 4), round(float(np.percentile(m, 97.5)), 4)]


def mixed(df, col):
    import statsmodels.formula.api as smf
    try:
        r = smf.mixedlm(f"{col} ~ 1", df, groups=df["atoll"]).fit(reml=True)
        lo, hi = r.conf_int().loc["Intercept"]
        return {"estimate": round(float(r.params["Intercept"]), 4), "ci": [round(float(lo), 4), round(float(hi), 4)]}
    except Exception as e:
        return {"error": repr(e)[:120]}


def main():
    inv = pd.read_csv(RUN / "data" / "inventory.csv").set_index("islet")
    a = attach_levels(load_areas())
    a["year"] = a.time.dt.year
    # D5: the land screen, then gross-failure values
    ls_ = land_screen(a, inv)
    keep = set(ls_.index[ls_.retained])
    loss = set(ls_.index[ls_.possible_loss])
    a_all = a
    a = a[a.islet.isin(keep | loss)]       # possible-loss features are rated for the sensitivity analysis only
    a, dropped = gross_filter(a)
    qa = {"features_measured": int(len(ls_)), "retained": int(len(keep)), "failed_land_screen": int((~ls_.retained).sum()),
          "possible_loss": sorted(loss), "values_set_aside_share": dropped,
          "retained_by_atoll": {k: int(v) for k, v in ls_[ls_.retained].groupby("atoll").size().items()},
          "failed_by_atoll": {k: int(v) for k, v in ls_[~ls_.retained].groupby("atoll").size().items()},
          "median_s2_to_osm_retained": round(float(ls_[ls_.retained].median_s2_to_osm.median()), 3),
          "not_measured_by_s2_ge_1ha": sorted(set(inv.index[inv.area_ha >= 1]) - set(a_all[(a_all.sensor == "s2") & a_all.area_otsu.notna()].islet))}
    is_s2 = a.sensor == "s2"
    l1 = a.sensor.isin(["LT05", "LE07", "LC08"])        # Collection 1 Level-1 (D1)
    fams = {
        "E1": a[l1 & (a.year <= 2015)],
        "E2": a[is_s2],
        # D7: the Landsat side of the guard is restricted to each islet's Sentinel-2 window
        "guard_ls": a[(a.sensor == "LC08") & (a.year >= 2016) & (a.year <= 2021)
                      & (a.time >= a.islet.map(a[is_s2].groupby("islet").time.min()))],
        "guard_s2_30m": a[is_s2 & (a.year >= 2016) & (a.year <= 2021)],
    }
    series = {"E1": ["area_otsu", "area_fixed", "area_ndwi"], "E2": ["area_otsu", "area_fixed", "area_ndwi"],
              "guard_ls": ["area_otsu"], "guard_s2_30m": ["area_otsu_30m"]}
    rows = []
    for fam, d in fams.items():
        for col in series[fam]:
            if col not in d:
                continue
            for islet, g in d.groupby("islet"):
                for robust in ((False, True) if (fam in ("E1", "E2") and col == "area_otsu") else (False,)):
                    r = islet_rate(g, col, inv.area_ha[islet] * 1e4, robust=robust,
                                   min_span=GUARD_MIN_SPAN if fam.startswith("guard") else MIN_SPAN)
                    if r:
                        rows.append({"islet": islet, "atoll": inv.atoll[islet], "area_ha": inv.area_ha[islet],
                                     "engineered": int(inv.engineered[islet]), "possible_loss": int(islet in loss),
                                     "family": fam, "series": col,
                                     "robust_slope": int(robust), **r})
    R = pd.DataFrame(rows)
    R.to_csv(T / "islet_rates.csv", index=False)
    R_all = R
    R = R[R.possible_loss == 0]
    prim = lambda fam, col="area_otsu", rob=0: R[(R.family == fam) & (R.series == col) & (R.robust_slope == rob)]
    out = {"qa_d5": qa, "scenes_used": {f: int(len(d)) for f, d in fams.items()},
           "levels_missing_share": round(float(a.level_m.isna().mean()), 4)}
    # sensor-step guard
    gl, gs = prim("guard_ls").set_index("islet"), prim("guard_s2_30m", "area_otsu_30m").set_index("islet")
    gj = gl[["rate_corr", "atoll", "engineered", "area_ha"]].join(gs[["rate_corr"]], rsuffix="_s2", how="inner")
    gj = gj[(gj.engineered == 0) & (gj.area_ha >= 5)]
    gj["diff"] = gj.rate_corr - gj.rate_corr_s2
    gci = boot_mean(gj, "diff") if len(gj) else [np.nan, np.nan]
    out["guard"] = {"islets": int(len(gj)), "mean_diff": round(float(gj["diff"].mean()), 4) if len(gj) else None,
                    "ci": gci, "valid": bool(len(gj) and gci[0] >= -0.2 and gci[1] <= 0.2)}
    # H1
    e1 = prim("E1").set_index("islet"); e2 = prim("E2").set_index("islet")
    x = e1[["rate_corr", "atoll", "engineered", "area_ha"]].join(e2[["rate_corr"]], rsuffix="_e2", how="inner")
    x = x[(x.engineered == 0) & (x.area_ha >= 5)].reset_index()
    x["D"] = x.rate_corr_e2 - x.rate_corr
    ci = boot_mean(x, "D") if len(x) else [np.nan, np.nan]
    v = ("not testable (sensor-step guard fails)" if not out["guard"]["valid"] else
         "Supported" if ci[0] >= -0.2 else "Refuted" if ci[1] < -0.2 else "Inconclusive")
    out["H1"] = {"islets": int(len(x)), "atolls": int(x.atoll.nunique()) if len(x) else 0,
                 "mean_rate_E1": round(float(x.rate_corr.mean()), 4) if len(x) else None,
                 "mean_rate_E2": round(float(x.rate_corr_e2.mean()), 4) if len(x) else None,
                 "D": round(float(x.D.mean()), 4) if len(x) else None, "ci": ci,
                 "mixed_model": mixed(x, "D") if len(x) > 3 else None, "verdict": v,
                 "verdict_ignoring_guard": "Supported" if ci[0] >= -0.2 else "Refuted" if ci[1] < -0.2 else "Inconclusive"}
    # H2
    y = e2[(e2.engineered == 0) & (e2.area_ha >= 1)].reset_index()
    y["bias"] = (y.rate_uncorr - y.rate_corr).abs()
    ci2 = boot_mean(y, "bias") if len(y) else [np.nan, np.nan]
    out["H2"] = {"islets": int(len(y)), "mean_abs_bias": round(float(y.bias.mean()), 4) if len(y) else None, "ci": ci2,
                 "mean_signed_bias": round(float((y.rate_uncorr - y.rate_corr).mean()), 4) if len(y) else None,
                 "verdict": "Supported" if ci2[0] >= 0.3 else "Refuted" if ci2[1] < 0.3 else "Inconclusive"}
    # secondaries
    out["by_atoll_E2"] = {k: {"islets": int(len(g)), "mean_rate": round(float(g.rate_corr.mean()), 4)}
                          for k, g in e2[(e2.engineered == 0)].groupby("atoll")}
    out["engineered_E2"] = {"islets": int((e2.engineered == 1).sum()),
                            "mean_rate": round(float(e2[e2.engineered == 1].rate_corr.mean()), 4) if (e2.engineered == 1).any() else None}
    sens = {}
    for col in ("area_fixed", "area_ndwi"):
        s1, s2 = prim("E1", col).set_index("islet"), prim("E2", col).set_index("islet")
        z = s1[["rate_corr", "atoll", "engineered", "area_ha"]].join(s2[["rate_corr"]], rsuffix="_e2", how="inner")
        z = z[(z.engineered == 0) & (z.area_ha >= 5)].reset_index()
        z["D"] = z.rate_corr_e2 - z.rate_corr
        sens[col] = {"islets": int(len(z)), "D": round(float(z.D.mean()), 4) if len(z) else None,
                     "ci": boot_mean(z, "D") if len(z) else None}
    r1, r2 = prim("E1", rob=1).set_index("islet"), prim("E2", rob=1).set_index("islet")
    z = r1[["rate_corr", "atoll", "engineered", "area_ha"]].join(r2[["rate_corr"]], rsuffix="_e2", how="inner")
    z = z[(z.engineered == 0) & (z.area_ha >= 5)].reset_index()
    z["D"] = z.rate_corr_e2 - z.rate_corr
    sens["robust_tide_slope"] = {"islets": int(len(z)), "D": round(float(z.D.mean()), 4) if len(z) else None,
                                 "ci": boot_mean(z, "D") if len(z) else None}
    if loss:
        q = lambda fam: R_all[(R_all.family == fam) & (R_all.series == "area_otsu") & (R_all.robust_slope == 0)].set_index("islet")
        z = q("E1")[["rate_corr", "atoll", "engineered", "area_ha"]].join(q("E2")[["rate_corr"]], rsuffix="_e2", how="inner")
        z = z[(z.engineered == 0) & (z.area_ha >= 5)].reset_index()
        z["D"] = z.rate_corr_e2 - z.rate_corr
        sens["with_possible_loss_features"] = {"islets": int(len(z)), "D": round(float(z.D.mean()), 4) if len(z) else None,
                                               "ci": boot_mean(z, "D") if len(z) else None}
    small = e2[(e2.engineered == 0) & (e2.area_ha >= 1) & (e2.area_ha < 5)]
    sens["E2_islets_1_to_5_ha"] = {"islets": int(len(small)),
                                   "mean_rate": round(float(small.rate_corr.mean()), 4) if len(small) else None}
    out["sensitivity"] = sens
    json.dump(out, open(T / "h1_h2.json", "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
