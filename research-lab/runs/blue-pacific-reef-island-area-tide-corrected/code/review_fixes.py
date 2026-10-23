"""D7 post hoc checks after the independent review. Reads the same areas, levels and screens as rates.py.

1. Tide response per atoll: pooled within-islet correlation of area with gauge level (Sentinel-2, retained islets),
   for the Otsu, fixed-threshold and NDWI series. r > -0.2 for Otsu marks a measurement failure.
2. Water level at image times, per atoll, on the union of Sentinel-2 acquisitions (one level per acquisition):
   Theil-Sen trend (mm/yr) with an acquisition bootstrap (B = 1,000).
3. E1 composition per H1 islet (>= 5 ha, non-engineered, E1 and E2 rates): Landsat 7 and Landsat 8 usable images,
   and the correlation of the E1 rate with the islet's Landsat 8 minus Landsat 7 corrected-area step (% of OSM area).
4. Sentinel-2 span per atoll (first and last usable image).
5. The guard by atoll (mean Landsat-minus-Sentinel-2 rate difference) from results/tables/islet_rates.csv.
6. H2 with tide slopes set to 0 unless negative beyond 2 SE (OLS SE), and per-atoll corrected rates from NDWI.
Writes results/tables/review_fixes.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rates as R  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"


def pooled_r(d, col):
    x = d.dropna(subset=[col, "level_m"])
    if len(x) < 30:
        return None
    a = x[col] - x.groupby("islet")[col].transform("mean")
    h = x.level_m - x.groupby("islet").level_m.transform("mean")
    return round(float(np.corrcoef(a, h)[0, 1]), 3)


def main():
    inv = pd.read_csv(RUN / "data" / "inventory.csv").set_index("islet")
    keep = set(pd.read_csv(T / "land_screen.csv").query("retained").islet)
    a = R.attach_levels(R.load_areas())
    a["year"] = a.time.dt.year
    a = a[a.islet.isin(keep)]
    a, _ = R.gross_filter(a)
    s2 = a[(a.sensor == "s2")]
    out = {"tide_response": {}, "level_trend_union": {}, "s2_span": {}}
    rng = np.random.default_rng(20261023)
    for at, g in s2.groupby("atoll"):
        g = g[g.islet.map(inv.engineered) == 0]
        out["tide_response"][at] = {c: pooled_r(g, c) for c in ("area_otsu", "area_fixed", "area_ndwi")}
        u = g.dropna(subset=["level_m"]).drop_duplicates("tmin")
        t = (u.time.dt.year + (u.time.dt.dayofyear - 1) / 365.25).to_numpy()
        lv = u.level_m.to_numpy()
        est = R.theil_sen(t, lv) * 1000
        bs = []
        for _ in range(1000):
            i = rng.integers(0, len(t), len(t))
            bs.append(R.theil_sen(t[i], lv[i]) * 1000)
        out["level_trend_union"][at] = {"acquisitions": int(len(u)), "mm_per_yr": round(float(est), 1),
                                        "ci": [round(float(np.nanpercentile(bs, 2.5)), 1), round(float(np.nanpercentile(bs, 97.5)), 1)]}
        ok = g.dropna(subset=["area_otsu"])
        out["s2_span"][at] = {"first": str(ok.time.min().date()), "last": str(ok.time.max().date())}
    # E1 composition and the Landsat 7 -> 8 step
    r = pd.read_csv(T / "islet_rates.csv")
    prim = lambda fam, col="area_otsu": r[(r.family == fam) & (r.series == col) & (r.robust_slope == 0) & (r.possible_loss == 0)]
    e1, e2 = prim("E1").set_index("islet"), prim("E2").set_index("islet")
    h1 = e1.join(e2[["rate_corr"]], rsuffix="_e2", how="inner")
    h1 = h1[(h1.engineered == 0) & (h1.area_ha >= 5)]
    l1 = a[a.sensor.isin(["LE07", "LC08", "LT05"]) & (a.year <= 2015) & a.islet.isin(h1.index)].dropna(subset=["area_otsu", "level_m"])
    rows = []
    for isl, g in l1.groupby("islet"):
        beta = np.polyfit(g.level_m, g.area_otsu, 1)[0] if g.level_m.std() > 0 else 0.0
        corr = 100 * (g.area_otsu - beta * g.level_m) / (inv.area_ha[isl] * 1e4)
        l7, l8 = corr[g.sensor == "LE07"], corr[g.sensor == "LC08"]
        rows.append({"islet": isl, "n_l7": int(len(l7)), "n_l8": int(len(l8)), "n_l5": int((g.sensor == "LT05").sum()),
                     "step_l8_minus_l7": float(l8.median() - l7.median()) if len(l7) and len(l8) else np.nan,
                     "e1_rate": float(h1.rate_corr[isl])})
    c = pd.DataFrame(rows)
    out["e1_composition"] = {"islets": int(len(c)), "median_l7_images": float(c.n_l7.median()), "median_l8_images": float(c.n_l8.median()),
                             "l5_images_total": int(c.n_l5.sum()),
                             "corr_e1_rate_vs_l8_l7_step": round(float(c[["e1_rate", "step_l8_minus_l7"]].dropna().corr().iloc[0, 1]), 3)}
    # guard by atoll
    gl = prim("guard_ls").set_index("islet")
    gs = r[(r.family == "guard_s2_30m") & (r.series == "area_otsu_30m") & (r.robust_slope == 0)].set_index("islet")
    gj = gl[["rate_corr", "atoll", "engineered", "area_ha"]].join(gs[["rate_corr"]], rsuffix="_s2", how="inner")
    gj = gj[(gj.engineered == 0) & (gj.area_ha >= 5)]
    gj["diff"] = gj.rate_corr - gj.rate_corr_s2
    out["guard_by_atoll"] = {at: {"islets": int(len(g)), "mean_diff": round(float(g["diff"].mean()), 3)} for at, g in gj.groupby("atoll")}
    # H2 with only significantly negative slopes used, and NDWI rates per atoll
    rows = []
    for isl, g in s2[s2.islet.map(inv.engineered) == 0].groupby("islet"):
        d = g.dropna(subset=["area_otsu", "level_m"])
        if len(d) < R.MIN_SCENES:
            continue
        t = (d.time.dt.year + (d.time.dt.dayofyear - 1) / 365.25).to_numpy()
        if t.max() - t.min() < R.MIN_SPAN:
            continue
        X = np.column_stack([np.ones(len(d)), d.level_m.to_numpy()])
        y = d.area_otsu.to_numpy()
        b, res, *_ = np.linalg.lstsq(X, y, rcond=None)
        sig2 = float(np.sum((y - X @ b) ** 2) / max(len(y) - 2, 1))
        se = float(np.sqrt(sig2 * np.linalg.inv(X.T @ X)[1, 1]))
        beta = b[1] if b[1] < -2 * se else 0.0
        ref = inv.area_ha[isl] * 1e4
        rc = R.theil_sen(t, 100 * (y - beta * d.level_m.to_numpy()) / ref)
        ru = R.theil_sen(t, 100 * y / ref)
        rows.append({"islet": isl, "atoll": inv.atoll[isl], "beta_used": bool(beta != 0), "bias": abs(ru - rc), "rate_corr": rc})
    z = pd.DataFrame(rows)
    out["h2_significant_slopes_only"] = {"islets": int(len(z)), "slopes_used": int(z.beta_used.sum()),
                                         "mean_abs_bias": round(float(z.bias.mean()), 3), "ci": R.boot_mean(z, "bias"),
                                         "by_atoll_rate": {k: round(float(g.rate_corr.mean()), 3) for k, g in z.groupby("atoll")}}
    nd = prim("E2", "area_ndwi")
    out["e2_ndwi_rate_by_atoll"] = {k: {"islets": int(len(g)), "mean_rate": round(float(g.rate_corr.mean()), 3)}
                                    for k, g in nd[nd.engineered == 0].groupby("atoll")}
    json.dump(out, open(T / "review_fixes.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
