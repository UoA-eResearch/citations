"""Secondary analyses 3, 5 and 6 (plan section 4) -> results/tables/secondary.json. Reported, not confirmatory.

3. Record-wet January-February 2023: held-out residuals and observed dv/v in those months, scored pairs covering them.
5. Temperature: ERA5 daily mean 2 m temperature lagged L days (L in 0, 5, ..., 90, chosen with tau by training R^2)
   in place of the annual sinusoid; same training/held-out split and scoring.
6. Pair type: borehole-borehole pairs (AWAZ, EPAZ, ETAZ, HBAZ, RVAZ, KBAZ, MBAZ) against pairs with a surface sensor.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dvv as D  # noqa: E402
import model as M  # noqa: E402

T = M.T
BORE = {"AWAZ", "EPAZ", "ETAZ", "HBAZ", "RVAZ", "KBAZ", "MBAZ"}
LAGS = range(0, 91, 5)


def temperature_variant():
    dv = pd.read_parquet(T / "dvv_daily.parquet")
    era = pd.read_csv(M.RUN / "data" / "raw" / "era5_daily.csv", parse_dates=["date"]).set_index("date")
    days = pd.date_range(era.index.min(), M.REC_END, freq="D")
    rain = era.precip_mm.reindex(days).fillna(0).to_numpy()
    temp = era.t2m_c.reindex(days).interpolate().to_numpy()
    temp = temp - temp[(days >= M.T0) & (days <= M.TRAIN_END)].mean()
    feats = M.rain_features(days, rain)
    segs = M.load_segments("plan")
    rows = []
    for pair, g in dv.groupby("pair"):
        a, b = pair.split("-")
        ho_end = M.held_out_end(segs, a, b)
        sm, seg, ty, ph, ok, tr = M.fit_pair(g, feats, days)
        coh = float(g[g.date <= M.TRAIN_END].cc.mean()) if (g.date <= M.TRAIN_END).any() else np.nan
        ho = ok & (days >= M.HO_START) & (days <= (ho_end if ho_end is not None else M.HO_START))
        lv = np.unique(seg[tr])
        if tr.sum() < 365 or len(lv) == 0 or ho.sum() == 0 or not np.isin(seg[ho], lv).all():
            rows.append({"pair": pair, "train_coherence": coh, "heldout_days": int(ho.sum())})
            continue

        def X(rows_, tau, lag):
            tl = np.concatenate([np.full(lag, temp[0]), temp[:len(temp) - lag]]) if lag else temp
            return np.hstack([np.column_stack([(seg[rows_] == s).astype(float) for s in lv]),
                              np.column_stack([feats[tau][rows_], tl[rows_], ty[rows_]])])
        best = None
        for tau in M.TAUS:
            for lag in LAGS:
                Xt = X(tr, tau, lag)
                beta, *_ = np.linalg.lstsq(Xt, sm[tr], rcond=None)
                rt = M.r2(sm[tr], Xt @ beta)
                if best is None or rt > best[0]:
                    best = (rt, tau, lag, beta)
        rt, tau, lag, beta = best
        yh = X(ho, tau, lag) @ beta
        rows.append({"pair": pair, "train_coherence": coh, "heldout_days": int(ho.sum()), "tau": tau, "lag": lag,
                     "train_r2": rt, "heldout_r2": M.r2(sm[ho], yh), "resid_2sd_pct": 2 * float(np.std(sm[ho] - yh))})
    f = pd.DataFrame(rows)
    sc = f[(f.train_coherence >= 0.5) & (f.heldout_days >= 180) & f.heldout_r2.notna()]
    return {"pairs_scored": int(len(sc)), "median_heldout_r2": round(float(sc.heldout_r2.median()), 4),
            "median_train_r2": round(float(sc.train_r2.median()), 4), "median_resid_2sd_pct": round(float(sc.resid_2sd_pct.median()), 4),
            "lag_counts": sc.lag.value_counts().to_dict()}


def main():
    f = pd.read_csv(T / "fit.csv")
    sc = f[(f.train_coherence >= 0.5) & (f.heldout_days >= 180) & f.heldout_r2.notna()].copy()
    out = {}
    w = sc[sc.jan_feb_2023_mean_resid.notna()]
    out["jan_feb_2023"] = {"pairs": int(len(w)), "median_mean_resid_pct": round(float(w.jan_feb_2023_mean_resid.median()), 4),
                           "pairs_beyond_resid_2sd": int((w.jan_feb_2023_mean_resid.abs() > w.resid_2sd_pct).sum())}
    dv = pd.read_parquet(T / "dvv_daily.parquet")
    obs = []
    for p in w.pair:
        g = dv[dv.pair == p].set_index("date").dvv_pct
        ho = g["2021-01-01":]
        obs.append(float(g["2023-01-01":"2023-02-28"].mean() - ho.mean()))
    out["jan_feb_2023"]["median_observed_dvv_minus_heldout_mean_pct"] = round(float(np.median(obs)), 4) if obs else None
    sc["type"] = ["borehole-borehole" if set(p.split("-")) <= BORE else "with surface" for p in sc.pair]
    out["pair_type"] = {k: {"pairs": int(len(g)), "median_heldout_r2": round(float(g.heldout_r2.median()), 4),
                            "median_train_r2": round(float(g.train_r2.median()), 4),
                            "median_resid_2sd_pct": round(float(g.resid_2sd_pct.median()), 4)}
                        for k, g in sc.groupby("type")}
    out["coherence"] = {"pairs_with_dvv": int(len(f)), "train_coherence_ge_0_5": int((f.train_coherence >= 0.5).sum()),
                        "median_train_coherence": round(float(f.train_coherence.median()), 4),
                        "median_train_r2_scored": round(float(sc.train_r2.median()), 4)}
    out["temperature"] = temperature_variant()
    (T / "secondary.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
