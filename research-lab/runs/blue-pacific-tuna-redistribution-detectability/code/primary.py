"""Apply the preregistered analysis to the observed series. Committed before it is first run.

Reads results/tables/observed_annual.csv (code/observed.py), indices.csv (code/indices.py) and
model_targets.json (code/model_targets.py). Writes results/tables/primary.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
PRIMARY_SERIES = "skj_catch_share"
PRIMARY_CONV = "sw"
FULL = (1980, 2021)
HIST = (1980, 2010)
MASK_RULE = 0.10        # plan.md section 9.1


def main():
    obs = pd.read_csv(TAB / "observed_annual.csv", index_col=0)
    idx = pd.read_csv(TAB / "indices.csv", index_col=0)
    idx["step2010"] = (idx.index >= 2010).astype(float)       # high-seas-pocket closure, plan section 8
    m = json.load(open(TAB / "model_targets.json"))
    hist = pd.Series({int(k): v for k, v in m["series"]["hist_share"].items()})
    tau = A.tau_pp()

    prim = obs[obs.convention == PRIMARY_CONV]
    yrs = np.arange(FULL[0], FULL[1] + 1)
    hy = np.arange(HIST[0], HIST[1] + 1)
    y = prim.loc[yrs, PRIMARY_SERIES].to_numpy(float)
    out = dict(tau_pp=tau, primary_series=PRIMARY_SERIES, convention=PRIMARY_CONV, years=list(FULL))

    # H1 - the primary verdict
    h1 = A.trend_ci(y, yrs, idx)
    h1["verdict"] = A.verdict_h1(h1["lo"], h1["hi"], tau)
    h1["mean_share_pct"] = 100 * float(y.mean())
    out["H1"] = h1

    # H2 - does SEAPODYM-hist reproduce the observed historical trend? (1980-2010, both ENSO-adjusted)
    out["H2"] = A.h2_difference(prim.loc[hy, PRIMARY_SERIES].to_numpy(float), hist.loc[hy].to_numpy(float), hy, idx)
    out["H2"]["consistent"] = bool(out["H2"]["lo"] <= 0 <= out["H2"]["hi"])

    # H3 - out-of-sample skill, train 1980-1999, test 2000-2010
    out["H3"] = A.h3_skill(prim.loc[hy, PRIMARY_SERIES].to_numpy(float), hist.loc[hy].to_numpy(float), hy, idx)
    out["H3"]["seapodym_beats_enso"] = bool(out["H3"]["d_r2"] > 0)

    # H4 - power and detection year
    deltas = [round(x, 3) for x in np.arange(0.0, 0.81, 0.025)]
    pw = A.h4_power(y, yrs, idx, deltas_pp=deltas)
    f = A.fit_trend(y, yrs, idx)
    pw["power_at_tau"] = pw["curve"].get(min(pw["curve"], key=lambda d: abs(d - abs(tau))))
    out["H4_power"] = pw
    out["H4_detection_year"] = A.h4_detection_year(f["resid"], tau)
    out["H4_detection_year"].pop("path", None)

    # secondary series and sensitivities (plan section 8)
    sens = {}
    for col in ("skj_density_share", "skj_density_share_una", "skj_catch_share_core10",
                "yft_catch_share", "bet_catch_share", "days_eez_share"):
        t = A.trend_ci(prim.loc[yrs, col].to_numpy(float), yrs, idx)
        t["verdict_vs_tau"] = A.verdict_h1(t["lo"], t["hi"], tau)
        sens[f"series:{col}"] = t
    for conv in ("centre", "eqnear"):
        s = obs[obs.convention == conv].loc[yrs, PRIMARY_SERIES].to_numpy(float)
        sens[f"convention:{conv}"] = A.trend_ci(s, yrs, idx)
    for name, cv in (("covars:none", ()), ("covars:nino_only", ("nino34", "nino34_lag")),
                     ("covars:full+step2010", ("nino34", "nino34_lag", "wpe", "step2010"))):
        sens[name] = A.trend_ci(y, yrs, idx, covars=cv)
    sens["window:1980-2010"] = A.trend_ci(prim.loc[hy, PRIMARY_SERIES].to_numpy(float), hy, idx)
    for col in ("skj_density_share", "skj_density_share_una"):
        sens[f"H2:{col}"] = A.h2_difference(prim.loc[hy, col].to_numpy(float), hist.loc[hy].to_numpy(float), hy, idx)
    out["sensitivity"] = sens

    # masking rule (plan section 9.1)
    mk = pd.read_csv(TAB / "masking.csv", index_col=0)
    worst = float(mk["eez_share_without_effort"].max())
    out["masking"] = dict(by_decade=mk[["domain_share_without_effort", "eez_share_without_effort"]].to_dict(),
                          worst_decade_eez_share=worst, rule=MASK_RULE, triggered=bool(worst > MASK_RULE))

    json.dump(out, open(TAB / "primary.json", "w"), indent=1, default=float)
    print(f"tau = {tau:+.4f} pp/yr")
    print(f"H1  {PRIMARY_SERIES}: {h1['point']:+.3f} pp/yr [{h1['lo']:+.3f}, {h1['hi']:+.3f}]  -> {h1['verdict']}")
    print(f"H2  obs - model (1980-2010): {out['H2']['diff']:+.3f} [{out['H2']['lo']:+.3f}, {out['H2']['hi']:+.3f}]")
    print(f"H3  dR2 = {out['H3']['d_r2']:+.3f} [{out['H3']['lo']:+.3f}, {out['H3']['hi']:+.3f}]")
    print(f"H4  MDE = {pw['mde_pp']} pp/yr; power at |tau| = {pw['power_at_tau']}; "
          f"detectable by {out['H4_detection_year']['year']}")


if __name__ == "__main__":
    sys.exit(main())
