"""POST HOC (after the primary result): held-out R^2 with the linear drift term held at its end-of-training value
instead of extrapolated, to separate drift extrapolation from the absence of a hydrological signal. Same fits as
model.py (same tau, same coefficients). Writes results/tables/posthoc_drift.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dvv as D  # noqa: E402
import model as M  # noqa: E402


def main():
    dv = pd.read_parquet(M.T / "dvv_daily.parquet")
    era = pd.read_csv(M.RUN / "data" / "raw" / "era5_daily.csv", parse_dates=["date"]).set_index("date")
    days = pd.date_range(era.index.min(), M.REC_END, freq="D")
    feats = M.rain_features(days, era.precip_mm.reindex(days).fillna(0).to_numpy())
    segs = M.load_segments("plan")
    fit = pd.read_csv(M.T / "fit.csv").set_index("pair")
    rows = []
    for pair, g in dv.groupby("pair"):
        if pair not in fit.index or pd.isna(fit.loc[pair, "heldout_r2"]):
            continue
        a, b = pair.split("-")
        ho_end = M.held_out_end(segs, a, b)
        sm, seg, ty, ph, ok, tr = M.fit_pair(g, feats, days)
        ho = ok & (days >= M.HO_START) & (days <= ho_end)
        lv = np.unique(seg[tr])
        tau = int(fit.loc[pair, "tau_days"])
        X = M.design(seg, ty, ph, feats[tau], tr, lv)
        beta, *_ = np.linalg.lstsq(X, sm[tr], rcond=None)
        ty2 = ty.copy()
        ty2[ho] = ty[tr].max()
        Xh = M.design(seg, ty2, ph, feats[tau], ho, lv)
        yh = Xh @ beta
        rows.append({"pair": pair, "heldout_r2_frozen_drift": M.r2(sm[ho], yh), "drift_pct_per_yr": float(beta[-1]),
                     "heldout_r2": float(fit.loc[pair, "heldout_r2"]), "train_coherence": float(fit.loc[pair, "train_coherence"]),
                     "heldout_days": int(fit.loc[pair, "heldout_days"])})
    f = pd.DataFrame(rows)
    sc = f[(f.train_coherence >= 0.5) & (f.heldout_days >= 180)]
    out = {"pairs_scored": int(len(sc)), "median_heldout_r2_frozen_drift": round(float(sc.heldout_r2_frozen_drift.median()), 4),
           "median_heldout_r2_preregistered": round(float(sc.heldout_r2.median()), 4),
           "share_ge_0_5_frozen_drift": round(float((sc.heldout_r2_frozen_drift >= 0.5).mean()), 3),
           "median_abs_drift_pct_per_yr": round(float(sc.drift_pct_per_yr.abs().median()), 4)}
    (M.T / "posthoc_drift.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
