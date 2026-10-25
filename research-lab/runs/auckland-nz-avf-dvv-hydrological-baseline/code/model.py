"""The hydrological model and H1 (plan section 3), plus the secondary analyses (section 4).

dv/v is smoothed with a 30-day centred running mean (at least 10 valid days). For each pair:
  y(t) = segment constants + a * P_tau(t) + b1 sin(2 pi t / 365.25) + b2 cos(...) + c * t
P_tau(t) = sum over days before t of (r_i - mean training rain) * erfc(sqrt(tau / (t - t_i))): rainfall anomaly (the
training mean is subtracted only for conditioning; with the drift term the fit is the same as with raw rain) diffused
to depth, tau = z^2 / 4D from {1, 2, 5, 10, 20, 50, 100, 200, 500} days, chosen by training R^2; OLS otherwise.
Training 2013-01-01..2020-12-31; held-out 2021-01-01..the end of the segment holding 2021-01-01 for either station;
nothing is fitted on held-out data. Scored pairs: mean training coherence >= 0.5 and >= 180 held-out days.
Writes results/tables/fit.csv (per pair) and results/tables/primary.json.
D1 (after review): segments come from dvv.py's segments file for the rule (dip changes and data gaps break segments);
beside the preregistered residual floor, the held-out dv/v's own 2 SD about its mean (no model) and the residual of a
season-only model (segment constants + annual sinusoid) are reported; the lockdown windows get a 15-day guard
against the 30-day smoother; results by coda SNR are reported post hoc.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import erfc

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dvv as D  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
TAUS = (1, 2, 5, 10, 20, 50, 100, 200, 500)
T0, TRAIN_END, HO_START = pd.Timestamp("2013-01-01"), pd.Timestamp("2020-12-31"), pd.Timestamp("2021-01-01")
REC_END = pd.Timestamp("2026-09-30")


def rain_features(days, rain):
    """P_tau on each calendar day (index = days), from the daily rain series (aligned to days)."""
    r = rain - rain[(days >= T0) & (days <= TRAIN_END)].mean()
    n = len(r)
    lag = np.arange(1, n + 1)
    out = {}
    for tau in TAUS:
        k = erfc(np.sqrt(tau / lag))
        conv = np.convolve(r, k)[:n]                      # sum_i r_i k(t - t_i), i < t (lag >= 1)
        out[tau] = np.concatenate([[0.0], conv[:-1]])
    return out


def held_out_end(segs, a, b):
    ends = []
    for st in (a, b):
        for s0, s1 in segs[st]:
            if s0 <= HO_START <= s1:
                ends.append(min(s1, REC_END))
    return min(ends) if len(ends) == 2 else None


def fit_pair(g, feats, days, segs_breaks=None):
    g = g.set_index("date").sort_index()
    s = g.dvv_pct.reindex(days)
    sm = s.rolling(30, center=True, min_periods=10).mean()
    seg = g.seg.reindex(days).ffill().bfill()
    t_years = (days - T0).days.to_numpy() / 365.25
    ph = 2 * np.pi * (days.dayofyear.to_numpy() / 365.25)
    ok = sm.notna().to_numpy() & s.notna().to_numpy()
    tr = ok & (days <= TRAIN_END)
    return sm.to_numpy(), seg.to_numpy(), t_years, ph, ok, tr


def design(seg, t_years, ph, P, rows, seg_levels):
    X = [np.column_stack([(seg[rows] == s).astype(float) for s in seg_levels])]
    X.append(np.column_stack([P[rows], np.sin(ph[rows]), np.cos(ph[rows]), t_years[rows]]))
    return np.hstack(X)


def r2(y, yhat):
    return 1 - np.sum((y - yhat) ** 2) / np.sum((y - y.mean()) ** 2)


def load_segments(rule):
    sg = pd.read_csv(T / ("segments.csv" if rule == "plan" else f"segments_{rule}.csv"), parse_dates=["start", "end"])
    return {st: list(zip(g.start, g.end)) for st, g in sg.sort_values(["station", "k"]).groupby("station")}


def main(segment_rule="plan", out_name="primary.json"):
    suffix = "" if segment_rule == "plan" else f"_{segment_rule}"
    dv = pd.read_parquet(T / f"dvv_daily{suffix}.parquet")
    pairs = pd.read_csv(T / f"pairs{suffix}.csv")
    era = pd.read_csv(RUN / "data" / "raw" / "era5_daily.csv", parse_dates=["date"]).set_index("date")
    days = pd.date_range(era.index.min(), REC_END, freq="D")
    rain = era.precip_mm.reindex(days).fillna(0).to_numpy()
    feats = rain_features(days, rain)
    segs = load_segments(segment_rule)
    rows = []
    for pair, g in dv.groupby("pair"):
        a, b = pair.split("-")
        ho_end = held_out_end(segs, a, b)
        sm, seg, ty, ph, ok, tr = fit_pair(g, feats, days)
        coh = float(g[g.date <= TRAIN_END].cc.mean()) if (g.date <= TRAIN_END).any() else np.nan
        coh0 = float(g[g.date <= TRAIN_END].cc0.median()) if "cc0" in g and (g.date <= TRAIN_END).any() else np.nan
        ho = ok & (days >= HO_START) & (days <= (ho_end if ho_end is not None else HO_START))
        seg_levels = np.unique(seg[tr])
        best = None
        for tau in TAUS:
            if tr.sum() < 365 or len(seg_levels) == 0:
                break
            X = design(seg, ty, ph, feats[tau], tr, seg_levels)
            beta, *_ = np.linalg.lstsq(X, sm[tr], rcond=None)
            rt = r2(sm[tr], X @ beta)
            if best is None or rt > best[1]:
                best = (tau, rt, beta)
        row = {"pair": pair, "train_coherence": coh, "train_cc0_median": coh0, "train_days": int(tr.sum()), "heldout_days": int(ho.sum()),
               "heldout_end": str(ho_end.date()) if ho_end is not None else None}
        if best is not None and ho.sum() > 0 and np.isin(seg[ho], seg_levels).all():
            tau, rt, beta = best
            Xh = design(seg, ty, ph, feats[tau], ho, seg_levels)
            yh = Xh @ beta
            res = sm[ho] - yh
            row.update({"tau_days": tau, "train_r2": rt, "heldout_r2": r2(sm[ho], yh), "rain_coef": beta[len(seg_levels)],
                        "resid_2sd_pct": 2 * float(np.std(res)),
                        "jan_feb_2023_mean_resid": float(np.mean(res[(days[ho] >= "2023-01-01") & (days[ho] < "2023-03-01")]))
                        if ((days[ho] >= "2023-01-01") & (days[ho] < "2023-03-01")).any() else None})
            # lockdown step in the training residuals (plan windows, and with a 15-day guard each side, D1)
            Xt = design(seg, ty, ph, feats[tau], tr, seg_levels)
            rtr = pd.Series(sm[tr] - Xt @ beta, index=days[tr])
            pre = rtr["2020-02-25":"2020-03-25"]
            post = rtr["2020-03-26":"2020-04-24"]
            row["lockdown_step_pct"] = float(post.mean() - pre.mean()) if len(pre) > 10 and len(post) > 10 else None
            pre_g, post_g = rtr["2020-01-26":"2020-02-24"], rtr["2020-04-25":"2020-05-24"]
            row["lockdown_step_guarded_pct"] = float(post_g.mean() - pre_g.mean()) if len(pre_g) > 10 and len(post_g) > 10 else None
            row["train_resid_2sd_pct"] = 2 * float(rtr.std())
            # D1: floors without the model: held-out dv/v about its own mean; season-only model residual
            row["nomodel_2sd_pct"] = 2 * float(np.std(sm[ho] - sm[ho].mean()))
            Xs = np.hstack([np.column_stack([(seg[tr] == s_).astype(float) for s_ in seg_levels]),
                            np.column_stack([np.sin(ph[tr]), np.cos(ph[tr])])])
            bs_, *_ = np.linalg.lstsq(Xs, sm[tr], rcond=None)
            Xsh = np.hstack([np.column_stack([(seg[ho] == s_).astype(float) for s_ in seg_levels]),
                             np.column_stack([np.sin(ph[ho]), np.cos(ph[ho])])])
            ysh = Xsh @ bs_
            row["season_only_r2"] = r2(sm[ho], ysh)
            row["season_only_2sd_pct"] = 2 * float(np.std(sm[ho] - ysh))
        rows.append(row)
    f = pd.DataFrame(rows).merge(pairs[["pair", "coda_snr"]], on="pair", how="left")
    f.to_csv(T / ("fit.csv" if out_name == "primary.json" else out_name.replace(".json", "_fit.csv")), index=False)
    sc = f[(f.train_coherence >= 0.5) & (f.heldout_days >= 180) & f.get("heldout_r2", pd.Series(dtype=float)).notna()]
    out = {"segment_rule": segment_rule, "pairs_with_dvv": int(len(f)), "pairs_scored": int(len(sc))}
    if len(sc):
        rng = np.random.default_rng(20261023)
        v = sc.heldout_r2.to_numpy()
        bs = [np.median(v[rng.integers(0, len(v), len(v))]) for _ in range(2000)]
        lo, hi = np.percentile(bs, [2.5, 97.5])
        med = float(np.median(v))
        out.update({"median_heldout_r2": round(med, 4), "ci": [round(float(lo), 4), round(float(hi), 4)],
                    "share_pairs_r2_ge_0_5": round(float((v >= 0.5).mean()), 3),
                    "verdict": "Inconclusive" if len(sc) < 5 else ("Supported" if (med >= 0.5 and lo >= 0.4) else
                                                                     "Refuted" if hi < 0.5 else "Inconclusive"),
                    "median_resid_2sd_pct": round(float(sc.resid_2sd_pct.median()), 4),
                    "noise_floor_le_0_05pct": bool(sc.resid_2sd_pct.median() <= 0.05),
                    "lockdown": {"median_step_pct": round(float(sc.lockdown_step_pct.median()), 4),
                                 "pairs_step_gt_2sd": int((sc.lockdown_step_pct.abs() > sc.train_resid_2sd_pct).sum()),
                                 "median_step_guarded_pct": round(float(sc.lockdown_step_guarded_pct.median()), 4),
                                 "pairs_step_guarded_gt_2sd": int((sc.lockdown_step_guarded_pct.abs() > sc.train_resid_2sd_pct).sum())},
                    "floors_d1": {"median_nomodel_2sd_pct": round(float(sc.nomodel_2sd_pct.median()), 4),
                                  "median_season_only_2sd_pct": round(float(sc.season_only_2sd_pct.median()), 4),
                                  "median_season_only_r2": round(float(sc.season_only_r2.median()), 4)},
                    "pairs_negative_r2": int((v < 0).sum()),
                    "median_train_coherence_all": round(float(f.train_coherence.median()), 4),
                    "by_zero_stretch_coherence_posthoc": {f"cc0>={t}": {"pairs": int((sc.train_cc0_median >= t).sum()),
                        "median_heldout_r2": round(float(sc[sc.train_cc0_median >= t].heldout_r2.median()), 4)
                        if (sc.train_cc0_median >= t).any() else None,
                        "median_nomodel_2sd_pct": round(float(sc[sc.train_cc0_median >= t].nomodel_2sd_pct.median()), 4)
                        if (sc.train_cc0_median >= t).any() else None} for t in (0.3, 0.5, 0.7)},
                    "tau_counts": sc.tau_days.value_counts().to_dict()})
    json.dump(out, open(T / out_name, "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


def every_epoch_segments():          # superseded by dvv.py RULE=every_epoch and segments_every_epoch.csv (D1)
    """Secondary 4: every channel epoch boundary is a segment break."""
    d = pd.read_csv(T / "fdsn_channels.txt", sep="|")
    d.columns = [c.strip("# ").strip() for c in d.columns]
    d = d[(d.Location == 10) & d.Channel.isin(["EHZ", "HHZ"])]
    out = {}
    for st, g in d.groupby("Station"):
        out[st] = [(pd.Timestamp(str(r.StartTime)[:10]),
                    pd.Timestamp(str(r.EndTime)[:10]) if str(r.EndTime) not in ("nan", "") else REC_END)
                   for r in g.sort_values("StartTime").itertuples()]
    return out


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "every_epoch":
        main("every_epoch", "secondary_every_epoch.json")
    else:
        main()
