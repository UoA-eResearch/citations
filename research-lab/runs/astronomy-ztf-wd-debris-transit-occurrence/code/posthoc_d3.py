"""Post hoc checks after the confirmation pass (D3). -> results/tables/posthoc_d3.json, zg_gaia_mismatch.csv

  1. calendar null: each long-dip candidate's low 30-day bins re-drawn at random among its own bins with >= 5 epochs
     (same number of low bins, 1,000 draws); how many candidates would have a low bin in the ten crowded windows by
     coverage alone, against the observed 454 (posthoc_review.json);
  2. G4, three readings of the g/r check on long-dip candidates' low bins (>= 3 g and >= 3 r epochs): both bands more
     than 2.5% below the pooled median (D2's reading), both bands at least 5% below their own median (the rule's depth),
     and the plan's own rule (dip epochs coincide in g and r within a night) on 30 random flags, all flags and the
     recovered known systems. A dip epoch is a short-rule faint outlier (> 3 robust sigma below its filter's median) or
     an epoch at least 5% below the pooled median inside one of the star's low bins. A star is testable if it has a
     night with both g and r epochs and at least one dip epoch on such a night; it passes if one such night has a dip
     epoch in each band;
  3. the sum-of-class lower rate beside the preregistered best-class one (first review, finding 9);
  4. faint-outlier asymmetry and the short-rule flag rate by Gaia G (finding 11);
  5. ZTF-Gaia magnitude mismatch: stars whose median g or r is more than 0.75 mag brighter than predicted from Gaia G
     and BP-RP (median relation in 0.1-mag colour bins), a sign that the most-epochs ZTF object is a brighter neighbour
     or blend (finding 8). Listed, not vetoed.
Uses the 30-day bins of posthoc_review.py (calendar-aligned, MJD / 30) for 1 and 2.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
T, D = RUN / "results" / "tables", RUN / "data"
det = pd.read_parquet(T / "detect.parquet")
cand = pd.read_csv(T / "candidates.csv")
k = pd.read_csv(T / "known_systems.csv")
pr = json.load(open(T / "posthoc_review.json"))
prim = json.load(open(T / "primary.json"))
s = pd.read_parquet(D / "sample.parquet")[["source_id", "phot_g_mean_mag", "bp_rp"]]
flag = det[det.short.fillna(False) | det.long.fillna(False)]
known_ids = set(k.gaia_dr3_source_id_in_sample.dropna().astype("int64"))
known_rec = set(flag.source_id) & known_ids
longc = set(cand[cand.long].source_id)
top10 = {v // 30 for v in pr["top10_windows_mjd_start"]}
rng = np.random.default_rng(20261110)
r30 = set(rng.choice(sorted(flag.source_id), 30, replace=False).tolist())
quiet = set(det[(det.n_epochs >= 100) & ~(det.short.fillna(False) | det.long.fillna(False))].sample(2000, random_state=1).source_id)

med = []                                   # per-star median g, r (all stars)
low_info, quiet_bins = {}, []
both25 = both5 = nb = 0
night = {}
for f in sorted((D / "lc_v2").glob("shard_*.parquet")):
    t = pd.read_parquet(f, columns=["source_id", "filt", "mjd", "mag"])
    t = t[t.filt.isin(["zg", "zr"])]
    mm = t.groupby(["source_id", "filt"]).mag.median().unstack()
    med.append(mm)
    sub = t[t.source_id.isin(longc | quiet | set(flag.source_id))]
    for sid, g in sub.groupby("source_id"):
        fl, mag, mjd = g.filt.to_numpy(), g.mag.to_numpy(), g.mjd.to_numpy()
        rel = np.empty(len(g))
        faint = np.zeros(len(g), bool)
        for b in ("zg", "zr"):
            m = fl == b
            if m.sum() == 0:
                continue
            md = np.median(mag[m])
            rel[m] = 10 ** (-0.4 * (mag[m] - md))
            sig = 1.4826 * np.median(np.abs(mag[m] - md))
            if m.sum() >= 5 and sig > 0:
                faint[m] = mag[m] > md + 3 * sig
        gmed = np.median(rel)
        b30 = np.floor(mjd / 30).astype(int)
        usable, low = [], []
        inlow = np.zeros(len(g), bool)
        for v in np.unique(b30):
            m = b30 == v
            x = rel[m]
            if len(x) < 5:
                continue
            usable.append(int(v))
            se = x.std(ddof=1) / np.sqrt(len(x))
            if (gmed - np.median(x)) > 5 * se and (gmed - np.median(x)) >= 0.05:
                low.append(int(v))
                inlow |= m
                if sid in longc:
                    xg, xr = x[fl[m] == "zg"], x[fl[m] == "zr"]
                    if len(xg) >= 3 and len(xr) >= 3:
                        nb += 1
                        both25 += (gmed - np.median(xg) > 0.025) and (gmed - np.median(xr) > 0.025)
                        both5 += (1 - np.median(xg) >= 0.05) and (1 - np.median(xr) >= 0.05)
        if sid in quiet:
            quiet_bins += usable
        if sid in longc:
            low_info[sid] = (low, usable)
        if sid in set(flag.source_id):
            dip = faint | (inlow & (rel <= gmed - 0.05))
            n_ = np.floor(mjd).astype(int)
            nights_both = {v for v in np.unique(n_) if {"zg", "zr"} <= set(fl[n_ == v])}
            dn = [v for v in nights_both if dip[n_ == v].any()]
            testable = len(dn) > 0
            ok = any(dip[(n_ == v) & (fl == "zg")].any() and dip[(n_ == v) & (fl == "zr")].any() for v in dn)
            night[sid] = (testable, ok)

# 1. calendar null
obs = sum(1 for low, _ in low_info.values() if set(low) & top10)
draws = []
for _ in range(1000):
    c = 0
    for low, usable in low_info.values():
        if low and usable:
            pick = rng.choice(usable, min(len(low), len(usable)), replace=False)
            c += bool(set(pick.tolist()) & top10)
    draws.append(c)
qb = np.array(quiet_bins)
lowall = np.array([v for low, _ in low_info.values() for v in low])
out = {"calendar_null": {"long_dip_candidates": len(low_info), "observed_with_low_bin_in_top10": obs,
                         "null_median": float(np.median(draws)), "null_95": [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))],
                         "excess_over_null": float(obs - np.median(draws)),
                         "share_of_quiet_star_usable_bins_in_top10": round(float(np.isin(qb, list(top10)).mean()), 4),
                         "share_of_candidate_low_bins_in_top10": round(float(np.isin(lowall, list(top10)).mean()), 4)}}


# 2. G4 readings
def rate(ids):
    tt = [night[i] for i in ids if i in night]
    te = [ok for testable, ok in tt if testable]
    return {"stars": len(tt), "testable": len(te), "pass": int(sum(te)), "share": round(sum(te) / len(te), 3) if te else None}


out["g4"] = {"low_bins_with_3g_3r": nb, "both_bands_gt_2.5pct_below_pooled_median": int(both25),
             "share_2.5pct": round(both25 / nb, 3) if nb else None,
             "both_bands_ge_5pct_below_own_median": int(both5), "share_5pct": round(both5 / nb, 3) if nb else None,
             "plan_rule_night_coincidence": {"random_30_flags": rate(r30), "all_flags": rate(set(flag.source_id)),
                                             "all_flags_excluding_known": rate(set(flag.source_id) - known_ids),
                                             "recovered_known_systems": rate(known_rec)}}
# 3. sum-of-class lower rate
rc = prim["rates"]
out["sum_of_class_lower_rate"] = {"sum": float(sum(rc[c]["rate_lower"] for c in rc if c != "combined")),
                                  "by_class": {c: rc[c]["rate_lower"] for c in rc if c != "combined"},
                                  "preregistered_best_class": rc["combined"]["rate_lower"]}
# 4. asymmetry by G
e = det[det.n_epochs >= 100].merge(s, on="source_id")
e["Gbin"] = pd.cut(e.phot_g_mean_mag, [0, 17, 18, 19, 19.5, 20.01], labels=["<17", "17-18", "18-19", "19-19.5", "19.5-20"])
out["asymmetry_by_G"] = {str(b): {"stars": int(len(x)), "share_negative_excess": round(float((x.excess < 0).mean()), 3),
                                  "median_excess": float(x.excess.median()), "short_flag_rate": round(float(x.short.fillna(False).mean()), 5)}
                         for b, x in e.groupby("Gbin", observed=True)}
# 5. ZTF-Gaia magnitude mismatch
M = pd.concat(med).reset_index().merge(s, on="source_id")
M["cbin"] = (M.bp_rp / 0.1).round()
mis = np.zeros(len(M), bool)
scat = {}
for b in ("zg", "zr"):
    dlt = M[b] - M.phot_g_mean_mag
    pred = dlt.groupby(M.cbin).transform("median")
    res = dlt - pred
    scat[b] = round(float(1.4826 * np.nanmedian(np.abs(res - np.nanmedian(res)))), 3)
    mis |= (res < -0.75).fillna(False).to_numpy()
M["mismatch"] = mis
el = set(det[det.n_epochs >= 100].source_id)
Me = M[M.source_id.isin(el)]
fl_ids = set(flag.source_id)
out["ztf_gaia_mismatch"] = {"robust_scatter_mag": scat, "eligible_mismatched": int(Me.mismatch.sum()),
                            "flag_rate_mismatched": round(float(Me[Me.mismatch].source_id.isin(fl_ids).mean()), 4),
                            "flag_rate_others": round(float(Me[~Me.mismatch].source_id.isin(fl_ids).mean()), 4),
                            "candidates_mismatched": int(Me[Me.mismatch].source_id.isin(set(cand.source_id)).sum()),
                            "known_mismatched": int(Me[Me.mismatch].source_id.isin(known_ids).sum())}
Me[Me.mismatch][["source_id", "zg", "zr", "phot_g_mean_mag", "bp_rp"]].assign(source_id=lambda x: x.source_id.astype(str)).to_csv(T / "zg_gaia_mismatch.csv", index=False)
(T / "posthoc_d3.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
print(json.dumps(out, indent=1, default=float))
