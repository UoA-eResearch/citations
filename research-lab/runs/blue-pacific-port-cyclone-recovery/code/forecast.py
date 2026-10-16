"""Freeze the forecast for the 2026-27 South Pacific cyclone season (1 Nov 2026 - 30 Apr 2027).

The procedure is preregistered in plan.md; the coefficients come from the primary-arm fit. This script writes
results/tables/forecast_model.json (every coefficient) and forecast_table.csv (the forecast for every active
Pacific island port at a grid of storm intensities and distances), and prints their sha256. Both files are
committed before 2026-11-01; code/score_forecast.py, also committed then, scores them in July 2027.

Model: the two-part model of analysis.py with BASE + import share + small-island indicator in both parts; part B
drops the indicator if fewer than 3 small-island events were disrupted (deviations D5).
Ports: the Pacific island ports (SPC's 22 PICTs) with >= 0.5 calls/day over 2019-2026.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
from events import PICT  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
RAW, TAB = RUN / "data" / "raw", RUN / "results" / "tables"
COVS = A.BASE + ["share", "sids"]
SEASON = ("2026-11-01", "2027-04-30")


def main():
    r = A.load("primary")
    a = A.part_a(r, COVS)
    # Part B drops the small-island indicator when too few small-island events were disrupted to estimate it
    # (deviations D5): with one such event its coefficient would be fitted to a single recovery time, and every
    # Pacific forecast (all sids = 1) would inherit it.
    n_sids_dis = int((r.D_ & (r.sids == 1)).sum())
    COVS_B = COVS if n_sids_dis >= A.MIN_SIDS_DISRUPTED else [c for c in COVS if c != "sids"]
    b = A.part_b(r, COVS_B)
    model = dict(season=SEASON, covariates=COVS, part_b_covariates=COVS_B,
                 fitted_on=dict(n_events=int(len(r)), n_disrupted=int(r.D_.sum()), n_storms=int(r.sid.nunique()),
                                n_sids_disrupted=n_sids_dis),
                 part_a_logit=a.params.to_dict(),
                 part_b_weibull_aft={f"{k[0]}|{k[1]}": float(v) for k, v in b.params_.items()},
                 benchmark_median_T_disrupted=float(r[r.D_].T_.clip(lower=1).median()),
                 benchmark_share_disrupted=float(r.D_.mean()))
    ports = pd.read_csv(RAW / "portwatch" / "ports.csv")
    act = pd.read_csv(RAW / "portwatch" / "daily.csv", usecols=["portid", "portcalls"]).groupby("portid").portcalls.mean()
    ports["mean_calls"] = ports.portid.map(act)
    pac = ports[ports.ISO3.isin(PICT) & (ports.mean_calls >= 0.5)].copy()
    rows = []
    for _, p in pac.iterrows():
        for cat in (3, 4, 5):
            for km in (25, 75, 125):
                x = dict(log_size=np.log(p.vessel_count_total + 1), log_activity=np.log(p.mean_calls), cat=cat,
                         closest_100km=km / 100, share=p.share_country_maritime_import / 100, sids=1.0)
                xa = np.array([1.0] + [x[c] for c in COVS])
                pa = float(1 / (1 + np.exp(-xa @ a.params.to_numpy())))
                med = float(b.predict_median(pd.DataFrame([x])[COVS_B]).iloc[0])
                # the scorer recomputes forecasts from the stored coefficients; check that formula reproduces lifelines
                pb = model["part_b_weibull_aft"]
                ls = pb["lambda_|Intercept"] + sum(pb[f"lambda_|{c}"] * x[c] for c in COVS_B)
                med2 = float(np.exp(ls) * np.log(2) ** (1 / np.exp(pb["rho_|Intercept"])))
                assert abs(med - med2) < 1e-6 * max(1.0, med), (med, med2)
                rows.append(dict(portid=p.portid, portname=p.portname, ISO3=p.ISO3, cat=cat, closest_km=km,
                                 p_disrupted=pa, median_T_if_disrupted=med))
    t = pd.DataFrame(rows)
    json.dump(model, open(TAB / "forecast_model.json", "w"), indent=1, default=float)
    t.to_csv(TAB / "forecast_table.csv", index=False)
    for f in ("forecast_model.json", "forecast_table.csv"):
        print(f, hashlib.sha256((TAB / f).read_bytes()).hexdigest())
    print(f"{len(pac)} ports, {len(t)} forecast rows")


if __name__ == "__main__":
    sys.exit(main())
