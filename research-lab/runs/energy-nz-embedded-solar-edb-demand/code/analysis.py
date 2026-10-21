"""Estimate H1-H4 and the fixed robustness set (plan sections 3-4). Writes results/tables/primary.json and
results/tables/robustness.json.

Main form: outcome per average ICP on solar kW per ICP (so the slope is GWh per MW, or MW per MW for demand), weighted
by ICPs, distributor (or unit) and year (or summer) fixed effects, heating degree-days (H4: mean daily maximum).
Intervals: distributor-cluster pairs bootstrap, 4,999 resamples, percentile, seed 20261021. A cluster drawn twice
enters as two clusters with their own fixed effects.

Reading of the plan for H4: section 3 lists "ICPs" among its controls; in the per-ICP form the ICPs enter through the
normalisation and the weight, and the levels form with ICPs as a control is reported in the robustness set.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
B, SEED = 4999, 20261021


def fe_ols(df, y, x, controls, unit, time, w=None, unit_fe=True):
    """Two-way FE weighted least squares; returns the coefficient on x (first regressor). With unit_fe=False (first
    differences) the unit effects are replaced by a constant."""
    d = df.dropna(subset=[y, x] + controls + ([w] if w else []))
    X = [d[x].to_numpy()] + [d[c].to_numpy() for c in controls]
    U = (pd.get_dummies(d[unit], drop_first=False, dtype=float).to_numpy() if unit_fe
         else np.ones((len(d), 1)))
    T = pd.get_dummies(d[time], drop_first=True, dtype=float).to_numpy()
    M = np.column_stack(X + [U, T])
    yy = d[y].to_numpy(dtype=float)
    if w:
        s = np.sqrt(d[w].to_numpy(dtype=float))
        M, yy = M * s[:, None], yy * s
    beta, *_ = np.linalg.lstsq(M, yy, rcond=None)
    return float(beta[0]), len(d)


def bootstrap(df, fit, unit, b=B, seed=SEED):
    rng = np.random.default_rng(seed)
    units = df[unit].unique()
    groups = {u: g for u, g in df.groupby(unit)}
    draws = []
    for _ in range(b):
        pick = rng.choice(units, size=len(units), replace=True)
        bs = pd.concat([groups[u].assign(**{unit: f"{u}#{k}"}) for k, u in enumerate(pick)], ignore_index=True)
        try:
            draws.append(fit(bs))
        except np.linalg.LinAlgError:
            continue
    draws = np.array(draws)
    return draws


def summarise(est, n, draws):
    lo, hi = np.percentile(draws, [2.5, 97.5])
    se = float(np.std(draws, ddof=1))
    return dict(estimate=round(est, 4), ci=[round(float(lo), 4), round(float(hi), 4)], se=round(se, 4),
                mde_80=round(2.8 * se, 4), n=n, draws=int(len(draws)))


def at_least_fall(r, thr):
    if r["estimate"] <= thr and r["ci"][1] < 0:
        return "Supported"
    if r["ci"][0] > thr:
        return "Refuted"
    return "Inconclusive"


def equivalence(r, band):
    lo, hi = r["ci"]
    if lo >= -band and hi <= band:
        return "Supported"
    if abs(r["estimate"]) > band and (lo > 0 or hi < 0):
        return "Refuted"
    return "Inconclusive"


def per_icp(a):
    a = a.copy()
    for c in ("delivered_gwh", "grid_net_gwh", "dg_supplied_gwh", "entering_gwh"):
        a[c.replace("_gwh", "_pi")] = a[c] * 1000 / a.icps            # MWh per ICP
    a["peak_pi"] = a.peak_mw * 1000 / a.icps                            # kW per ICP
    for c in ("btm_mw", "solar_all_mw", "res_mw", "nonsolar_dg_mw", "lead2_btm_mw", "lead2_solar_all_mw"):
        if c in a:
            a[c.replace("_mw", "_pi")] = a[c] * 1000 / a.icps               # kW per ICP
    return a


def spec(a, y, x, controls, unit="edb", time="disc_yr", w="icps", unit_fe=True):
    f = lambda d: fe_ols(d, y, x, controls, unit, time, w, unit_fe)[0]
    est, n = fe_ols(a, y, x, controls, unit, time, w, unit_fe)
    return summarise(est, n, bootstrap(a.dropna(subset=[y, x] + controls), f, unit))


def main():
    a = pd.read_csv(TAB / "panel_annual.csv")
    lead = a[["edb", "disc_yr", "btm_mw", "solar_all_mw"]].copy()
    lead["disc_yr"] -= 2
    lead = lead.rename(columns={"btm_mw": "lead2_btm_mw", "solar_all_mw": "lead2_solar_all_mw"})
    a = a.merge(lead, on=["edb", "disc_yr"], how="left")
    a = per_icp(a)
    s = pd.read_csv(TAB / "panel_summer.csv")
    s["mid_pi"] = s.mid_mw * 1000 / s.icps
    s["solar_all_pi"] = s.solar_all_mw * 1000 / s.icps

    H = {
        "H1": dict(y="grid_net_pi", x="solar_all_pi", c=["hdd", "nonsolar_dg_pi"], thr=-1.0),
        "H2": dict(y="delivered_pi", x="btm_pi", c=["hdd"], thr=-0.3),
        "H3": dict(y="peak_pi", x="btm_pi", c=["hdd"], band=0.2),
    }
    primary = {}
    for k, h in H.items():
        r = spec(a, h["y"], h["x"], h["c"])
        r["verdict"] = equivalence(r, h["band"]) if "band" in h else at_least_fall(r, h["thr"])
        primary[k] = r
    r = spec(s, "mid_pi", "solar_all_pi", ["tmax"], unit="unit", time="summer")
    r["verdict"] = at_least_fall(r, -0.3)
    primary["H4"] = r
    ex = spec(a, "dg_supplied_pi", "btm_pi", ["hdd"])
    primary["export_slope"] = ex
    sc = -primary["H2"]["estimate"] / (-primary["H2"]["estimate"] + ex["estimate"])
    primary["implied_self_consumption_share"] = round(sc, 3)
    json.dump(primary, open(TAB / "primary.json", "w"), indent=1)
    print(json.dumps(primary, indent=1))

    rob = {}
    for k in ("H1", "H2", "H3"):
        h = H[k]
        lv = {"H1": ("grid_net_gwh", "solar_all_mw", ["hdd", "nonsolar_dg_mw", "icps"]),
              "H2": ("delivered_gwh", "btm_mw", ["hdd", "icps"]),
              "H3": ("peak_mw", "btm_mw", ["hdd", "icps"])}[k]
        rk = {"levels": spec(a, lv[0], lv[1], lv[2], w=None),
              "unweighted": spec(a, h["y"], h["x"], h["c"], w=None),
              "no_hdd": spec(a, h["y"], h["x"], [c for c in h["c"] if c != "hdd"]),
              "drop_dy2021": spec(a[a.disc_yr != 2021], h["y"], h["x"], h["c"])}
        d = a.sort_values(["edb", "disc_yr"]).copy()
        for c in [h["y"], h["x"]] + h["c"]:
            d["d_" + c] = d.groupby("edb")[c].diff()
        rk["first_differences"] = spec(d, "d_" + h["y"], "d_" + h["x"], ["d_" + c for c in h["c"]], unit_fe=False)
        raw = {"H1": "grid_net_gwh", "H2": "delivered_gwh", "H3": "peak_mw"}[k]
        d["jump"] = np.log(d[raw]).groupby(d.edb).diff().abs()
        rk["drop_jumps_15pct"] = spec(d[~(d.jump > 0.15)], h["y"], h["x"], h["c"])
        if k in ("H2", "H3"):
            rk["residential_only"] = spec(a, h["y"], "res_pi", h["c"])
        loo = []
        for e in sorted(a.edb.unique()):
            loo.append(fe_ols(a[a.edb != e], h["y"], h["x"], h["c"], "edb", "disc_yr", "icps")[0])
        rk["leave_one_out_range"] = [round(min(loo), 4), round(max(loo), 4)]
        if k in ("H1", "H2"):
            lx = "lead2_solar_all_pi" if k == "H1" else "lead2_btm_pi"
            sub = a.dropna(subset=[lx])
            f = lambda dd: fe_ols(dd, h["y"], lx, [h["x"]] + h["c"], "edb", "disc_yr", "icps")[0]
            est, n = fe_ols(sub, h["y"], lx, [h["x"]] + h["c"], "edb", "disc_yr", "icps")
            rk["placebo_lead2_coefficient"] = summarise(est, n, bootstrap(sub, f, "edb"))
        rob[k] = rk
    # D2 sensitivity: ICPs derived from the disclosures (energy delivered / kWh per ICP), Westpower 2024 excluded
    # (its disclosed ratio implies 91,158 ICPs against about 14,300 in the registry)
    dsc = pd.read_csv(TAB / "panel_annual.csv")
    dsc = dsc[~((dsc.edb == "Westpower") & (dsc.disc_yr == 2024))].copy()
    dsc["icps"] = dsc.icps_disclosure
    dsc = per_icp(dsc)
    for k in ("H1", "H2", "H3"):
        h = H[k]
        rob[k]["disclosure_icps"] = spec(dsc, h["y"], h["x"], h["c"])
    s2 = s.copy()
    rob["H4"] = {"levels_with_icps": spec(s2, "mid_mw", "solar_all_mw", ["tmax", "icps"], unit="unit", time="summer",
                                          w=None),
                 "unweighted": spec(s2, "mid_pi", "solar_all_pi", ["tmax"], unit="unit", time="summer", w=None)}
    # plan section 4 applies to H4 too: leave-one-unit-out and first differences (D3)
    loo = [fe_ols(s[s.unit != u], "mid_pi", "solar_all_pi", ["tmax"], "unit", "summer", "icps")[0]
           for u in sorted(s.unit.unique())]
    rob["H4"]["leave_one_out_range"] = [round(min(loo), 4), round(max(loo), 4)]
    rob["H4"]["leave_one_out"] = {u: round(v, 4) for u, v in zip(sorted(s.unit.unique()), loo)}
    sd = s.sort_values(["unit", "summer"]).copy()
    for c in ("mid_pi", "solar_all_pi", "tmax"):
        sd["d_" + c] = sd.groupby("unit")[c].diff()
    rob["H4"]["first_differences"] = spec(sd, "d_mid_pi", "d_solar_all_pi", ["d_tmax"], unit="unit", time="summer",
                                          unit_fe=False)
    # post hoc placebo (D3): offtake when solar output is nil should not respond to installed solar
    for w in ("eve", "night"):
        s[w + "_pi"] = s[w + "_mw"] * 1000 / s.icps
        rob["H4"][f"placebo_{w}"] = spec(s, w + "_pi", "solar_all_pi", ["tmax"], unit="unit", time="summer")
    json.dump(rob, open(TAB / "robustness.json", "w"), indent=1)
    print(json.dumps({k: {kk: (vv["estimate"] if isinstance(vv, dict) else vv) for kk, vv in v.items()}
                      for k, v in rob.items()}, indent=1))


if __name__ == "__main__":
    main()
