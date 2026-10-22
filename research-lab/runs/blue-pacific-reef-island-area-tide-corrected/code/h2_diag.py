"""Post hoc (not preregistered): what the H2 tide bias is made of.

H2 is the mean absolute difference between uncorrected and corrected Sentinel-2 rates. An absolute difference also
picks up noise, so two diagnostics:
1. Noise floor: within each islet, the water levels are permuted across scenes (breaking any link between level and
   date) and the corrected rate recomputed; the mean |uncorrected - corrected| under permutation (20 permutations)
   is the bias that noise alone produces.
2. Mechanism: per atoll, the Theil-Sen trend of overpass-time water level (m/yr) and the median tide slope; the bias
   a trend in sampled water level should produce is -beta x level trend, as % of the reference area per year.

Writes results/tables/h2_diagnostics.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rates as R  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
NPERM, SEED = 20, 20261023


def main():
    inv = pd.read_csv(RUN / "data" / "inventory.csv").set_index("islet")
    a = R.attach_levels(R.load_areas())
    a["year"] = a.time.dt.year
    keep = set(pd.read_csv(RUN / "results" / "tables" / "land_screen.csv").query("retained").islet)
    a = a[a.islet.isin(keep) & (a.sensor == "s2")]
    a, _ = R.gross_filter(a)
    rng = np.random.default_rng(SEED)
    rows = []
    for islet, g in a.groupby("islet"):
        if inv.engineered[islet] or inv.area_ha[islet] < 1:
            continue
        ref = inv.area_ha[islet] * 1e4
        r = R.islet_rate(g, "area_otsu", ref)
        if not r:
            continue
        d = g.dropna(subset=["area_otsu", "level_m"])
        t = (d.time.dt.year + (d.time.dt.dayofyear - 1) / 365.25).to_numpy()
        perm = []
        for _ in range(NPERM):
            gp = d.copy()
            gp["level_m"] = rng.permutation(gp.level_m.to_numpy())
            rp = R.islet_rate(gp, "area_otsu", ref)
            perm.append(abs(rp["rate_uncorr"] - rp["rate_corr"]))
        lvl_trend = R.theil_sen(t, d.level_m.to_numpy())
        rows.append({"islet": islet, "atoll": inv.atoll[islet], "area_ha": inv.area_ha[islet],
                     "bias": r["rate_uncorr"] - r["rate_corr"], "abs_bias": abs(r["rate_uncorr"] - r["rate_corr"]),
                     "perm_abs_bias": float(np.mean(perm)), "beta_pct_per_m": 100 * r["tide_slope_m2_per_m"] / ref,
                     "level_trend_m_yr": lvl_trend})
    x = pd.DataFrame(rows)
    # sign: uncorrected = corrected + beta*h, so its rate exceeds the corrected rate by beta x (level trend)
    x["predicted_bias"] = x.beta_pct_per_m * x.level_trend_m_yr
    out = {"islets": int(len(x)), "mean_abs_bias": round(float(x.abs_bias.mean()), 3),
           "mean_abs_bias_under_permuted_levels": round(float(x.perm_abs_bias.mean()), 3),
           "excess_over_noise": round(float(x.abs_bias.mean() - x.perm_abs_bias.mean()), 3),
           "share_islets_abs_bias_above_perm": round(float((x.abs_bias > x.perm_abs_bias).mean()), 3),
           "corr_bias_vs_predicted": round(float(np.corrcoef(x.bias, x.predicted_bias)[0, 1]), 3),
           "by_atoll": {k: {"islets": int(len(g)), "mean_bias": round(float(g.bias.mean()), 3),
                            "mean_abs_bias": round(float(g.abs_bias.mean()), 3),
                            "mean_perm_abs_bias": round(float(g.perm_abs_bias.mean()), 3),
                            "level_trend_mm_yr": round(1000 * float(g.level_trend_m_yr.median()), 1),
                            "median_beta_pct_per_m": round(float(g.beta_pct_per_m.median()), 1)}
                        for k, g in x.groupby("atoll")},
           "by_size": {str(k): {"islets": int(len(g)), "mean_abs_bias": round(float(g.abs_bias.mean()), 3),
                                "mean_perm_abs_bias": round(float(g.perm_abs_bias.mean()), 3)}
                       for k, g in x.groupby(pd.cut(x.area_ha, [1, 5, 20, 1e6]), observed=True)}}
    x.to_csv(RUN / "results" / "tables" / "h2_diagnostics_islets.csv", index=False)
    json.dump(out, open(RUN / "results" / "tables" / "h2_diagnostics.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
