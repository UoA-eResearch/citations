"""H4 frozen forecast (plan section 7). Training: snapshots on 1 November 2012-2024 of substances Medsafe-consented and
not yet funded; outcome = funded (T3) within the next 12 months. Logistic regression (L2, C = 1). Features: EMA orphan,
ATC first level, years since T0, years since T2, FDA priority review, Australian listing by the snapshot (Website
era only, so 'unknown' before 2019), snapshot year. Forecast for everything consented and unfunded at the cutoff.
Writes results/forecast_2026.csv (+ .sha256) and results/tables/forecast_training.json."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis import load  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def features(d, snap):
    x = pd.DataFrame(index=d.index)
    x["orphan"] = (d.ema_orphan == "Yes").astype(float)
    x["priority"] = (d.fda_priority.fillna("").str.upper() == "PRIORITY").astype(float)
    x["yrs_t0"] = (snap - d.t0).dt.days / 365.25
    x["yrs_t2"] = (snap - d.t2).dt.days / 365.25
    au_known = snap >= pd.Timestamp("2019-01-01")
    x["au_listed"] = ((d.t3_au.notna() & (d.t3_au <= snap)) if au_known else pd.Series(False, index=d.index)).astype(float)
    x["au_unknown"] = float(not au_known)
    x["year"] = snap.year - 2018
    atc = d.atc.fillna("?").str[:1]
    for a in "ABCDGHJLMNPRSV?":
        x[f"atc_{a}"] = (atc == a).astype(float)
    return x


def at_risk(d, snap):
    return d[d.t2.notna() & (d.t2 <= snap) & (d.t3.isna() | (d.t3 > snap))]


def main():
    d, cutoff = load()
    X, y = [], []
    for yr in range(2012, 2025):
        snap = pd.Timestamp(f"{yr}-11-01")
        if snap + pd.DateOffset(months=12) > cutoff:
            continue
        r = at_risk(d, snap)
        X.append(features(r, snap)); y.append((r.t3.notna() & (r.t3 <= snap + pd.DateOffset(months=12))).astype(int))
    X, y = pd.concat(X), pd.concat(y)
    m = LogisticRegression(C=1.0, max_iter=2000).fit(X, y)
    snap = cutoff
    r = at_risk(d, snap)
    p = m.predict_proba(features(r, snap))[:, 1]
    f = pd.DataFrame(dict(substance=r.substance, t0=r.t0.dt.date, t2=r.t2.dt.date, p_funded_12m=np.round(p, 4)))
    f["base_rate"] = round(float(y.mean()), 4)
    f["forecast_origin"] = str(snap.date())
    f["score_after"] = str((snap + pd.DateOffset(months=12)).date())
    out = RUN / "results" / "forecast_2026.csv"
    f.sort_values("p_funded_12m", ascending=False).to_csv(out, index=False)
    (RUN / "results" / "forecast_2026.sha256").write_text(hashlib.sha256(out.read_bytes()).hexdigest() + "  forecast_2026.csv\n")
    json.dump(dict(n_train=int(len(y)), base_rate=float(y.mean()), n_forecast=int(len(f)), origin=str(snap.date()),
                   coef=dict(zip(X.columns, map(float, m.coef_[0]))), intercept=float(m.intercept_[0])),
              open(RUN / "results" / "tables" / "forecast_training.json", "w"), indent=1)
    print(len(y), "training rows; base rate", round(float(y.mean()), 3), ";", len(f), "forecasts from", snap.date())


if __name__ == "__main__":
    sys.exit(main())
