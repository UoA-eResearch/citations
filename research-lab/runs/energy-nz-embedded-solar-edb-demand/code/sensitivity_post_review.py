"""Post-review sensitivity of H4 (deviations D5). Descriptive only; H4's verdict is the preregistered rule's.

The review found that H4 is identified mainly by the two units that added solar farms (EA Networks, Top Energy),
that behind-the-meter solar alone does not detect, that the 18:00-21:00 window still has sun in a New Zealand summer,
and that Top Energy's geothermal expansion turned it into a net grid injector. This recomputes those variants with the
study's own estimator (analysis.spec, same bootstrap and seed).

Writes results/tables/sensitivity_post_review.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
import build_panel as bp  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"


def exposures(log):
    """Per H4 unit and summer: behind-the-meter, industrial (farms) and non-solar DG capacity, MW (Dec-Feb mean)."""
    cap = bp.capacity()
    unit = {pid: u for u, members in log["h4_units"].items() for pid in members}
    c = cap[cap.pid.isin(unit)].copy()
    c["unit"] = c.pid.map(unit)
    c = c[c.month.dt.month.isin([12, 1, 2])]
    c["summer"] = c.month.dt.year - (c.month.dt.month <= 2)
    c["ind_mw"] = c.solar_all_mw - c.btm_mw
    g = c.groupby(["unit", "summer", "month"])[["btm_mw", "ind_mw", "nonsolar_dg_mw"]].sum()
    return g.groupby(["unit", "summer"]).mean().reset_index()


def main():
    log = json.load(open(TAB / "panel_log.json"))
    s = pd.read_csv(TAB / "panel_summer.csv").merge(exposures(log), on=["unit", "summer"], how="left")
    for c in ("mid", "eve", "night"):
        s[c + "_pi"] = s[c + "_mw"] * 1000 / s.icps
    for c in ("solar_all", "btm", "ind", "nonsolar_dg"):
        s[c + "_pi"] = s[c + "_mw"] * 1000 / s.icps
    s["mid_minus_night_pi"] = s.mid_pi - s.night_pi
    lead = s[["unit", "summer", "solar_all_pi"]].assign(summer=lambda x: x.summer - 2) \
        .rename(columns={"solar_all_pi": "lead2_solar_all_pi"})
    s = s.merge(lead, on=["unit", "summer"], how="left")
    sp = lambda d, y, x, c=("tmax",): A.spec(d, y, x, list(c), unit="unit", time="summer")
    farm_units = sorted(s.groupby("unit").ind_mw.max().loc[lambda v: v >= 5].index)
    two = ["EASH", "TOPE"]
    out = {"farm_units_industrial_solar_ge_5MW": farm_units, "preregistered": sp(s, "mid_pi", "solar_all_pi")}
    out["drop_EASH_TOPE"] = sp(s[~s.unit.isin(two)], "mid_pi", "solar_all_pi")
    out["drop_farm_units"] = sp(s[~s.unit.isin(farm_units)], "mid_pi", "solar_all_pi")
    out["btm_exposure_only"] = sp(s, "mid_pi", "btm_pi")
    out["industrial_exposure_only"] = sp(s, "mid_pi", "ind_pi")
    out["joint_btm_coefficient"] = sp(s, "mid_pi", "btm_pi", ("ind_pi", "tmax"))
    out["joint_ind_coefficient"] = sp(s, "mid_pi", "ind_pi", ("btm_pi", "tmax"))
    out["nonsolar_dg_control"] = sp(s, "mid_pi", "solar_all_pi", ("nonsolar_dg_pi", "tmax"))
    out["night_with_nonsolar_dg_control"] = sp(s, "night_pi", "solar_all_pi", ("nonsolar_dg_pi", "tmax"))
    out["mid_minus_night"] = sp(s, "mid_minus_night_pi", "solar_all_pi")
    out["mid_minus_night_drop_EASH_TOPE"] = sp(s[~s.unit.isin(two)], "mid_minus_night_pi", "solar_all_pi")
    sub = s.dropna(subset=["lead2_solar_all_pi"])
    out["placebo_lead2_midday"] = sp(sub, "mid_pi", "lead2_solar_all_pi", ("solar_all_pi", "tmax"))
    out["placebo_lead2_night"] = sp(sub, "night_pi", "lead2_solar_all_pi", ("solar_all_pi", "tmax"))
    d = s.sort_values(["unit", "summer"]).copy()
    ratio = d.mid_mw / d.groupby("unit").mid_mw.shift()
    d["jump"] = np.where(ratio > 0, np.abs(np.log(ratio.where(ratio > 0))), np.inf)
    d.loc[d.groupby("unit").head(1).index, "jump"] = 0.0
    out["drop_jumps_15pct"] = sp(d[d.jump <= 0.15], "mid_pi", "solar_all_pi")
    out["drop_jumps_15pct_rows_dropped"] = int((d.jump > 0.15).sum())
    json.dump(out, open(TAB / "sensitivity_post_review.json", "w"), indent=1)
    for k, v in out.items():
        print(k, v if not isinstance(v, dict) else (v["estimate"], v["ci"]))


if __name__ == "__main__":
    main()
