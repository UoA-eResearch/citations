#!/usr/bin/env python
"""Group data, subsampling experiment and hypothesis tests (plan.md sec 2, 5, 6, 8).

Usage: analysis.py [--R 500] [--contrasts all|key,key] [--unconstrained]
Output (results/tables/): inclusion.csv, prior_quality.csv, draws_{key}{suffix}.parquet, gains{suffix}.csv,
hypotheses{suffix}.csv
"""
from __future__ import annotations

import argparse
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eb  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
FL = RUN / "data" / "first_level"
# key: (domain, matched query, mismatched query, primary?)
CONTRASTS = {
    "ds002785_workingmemory": ("Working memory", "working memory", "face perception", True),
    "ds002785_emomatching": ("Emotion processing", "emotional faces", "working memory", True),
    "ds002785_gstroop": ("Cognitive conflict", "stroop", "face perception", True),
    "ds002785_faces": ("Face perception", "face perception", "working memory", True),
    "ds002785_anticipation": ("Anticipation", "anticipation", "finger tapping", True),
    "ds002790_stopsignal": ("Response inhibition", "stop signal", "emotional faces", True),
    "ds002790_workingmemory": ("Working memory (PIOP2 replication)", "working memory", "face perception", False),
    "ds002790_emomatching": ("Emotion processing (PIOP2 replication)", "emotional faces", "working memory", False),
}


def load(key):
    """Subjects x voxels matrix over the group mask, after the plan's inclusion rules; plus an inclusion record."""
    recs, effs = [], []
    for f in sorted((FL / key).glob("sub-*.npz")):
        z = np.load(f)
        recs.append(dict(sub=f.stem, coverage=float(z["coverage"]), mean_fd=float(z["mean_fd"])))
        effs.append(z["effect"])
    errs = sorted(p.stem for p in (FL / key).glob("sub-*.err"))
    rec = pd.DataFrame(recs)
    keep = (rec.coverage >= 0.90) & (rec.mean_fd <= 0.5)
    E = np.array(effs)[keep.values]
    gmask = np.isfinite(E).all(0)
    man = pd.read_csv(RUN / "data" / "manifest.tsv", sep="\t")
    inc = dict(key=key, manifest=int((man.dataset + "_" + man.task == key).sum()),
               fit_failed=len(errs), low_coverage=int((rec.coverage < 0.90).sum()),
               high_motion=int(((rec.coverage >= 0.90) & (rec.mean_fd > 0.5)).sum()), included=int(keep.sum()),
               mask_voxels=int(gmask.sum()))
    return E[:, gmask], gmask, inc


def _job(args):
    key, n, R, nonneg = args
    Y, gmask, _ = load(key)
    pri = np.load(RUN / "results" / "priors" / "priors.npz")
    _, q, w, _ = CONTRASTS[key]
    d = eb.run_draws(Y, pri[q][gmask], pri[w][gmask], n_grid=[n], R=R, seed=list(CONTRASTS).index(key),
                     nonneg=nonneg, n_gt=Y.shape[0] - max(eb.N_GRID))
    d["key"] = key
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--R", type=int, default=500)
    ap.add_argument("--contrasts", default="all")
    ap.add_argument("--unconstrained", action="store_true")
    a = ap.parse_args()
    keys = list(CONTRASTS) if a.contrasts == "all" else a.contrasts.split(",")
    suffix = "_unconstrained" if a.unconstrained else ""
    inc, pq = [], []
    pri = np.load(RUN / "results" / "priors" / "priors.npz")
    for k in keys:
        Y, gmask, rec = load(k)
        inc.append(rec)
        full = Y.mean(0)
        _, q, w, _ = CONTRASTS[k]
        pq.append(dict(key=k, r_matched=np.corrcoef(pri[q][gmask], full)[0, 1],
                       r_mismatched=np.corrcoef(pri[w][gmask], full)[0, 1]))
    if not a.unconstrained:
        pd.DataFrame(inc).to_csv(TAB / "inclusion.csv", index=False)
        pd.DataFrame(pq).to_csv(TAB / "prior_quality.csv", index=False)
    print(pd.DataFrame(inc).to_string(index=False))
    print(pd.DataFrame(pq).round(3).to_string(index=False), flush=True)
    jobs = [(k, n, a.R, not a.unconstrained) for k in keys for n in eb.N_GRID]
    with Pool(min(26, len(jobs))) as pool:
        parts = pool.map(_job, jobs)
    draws = pd.concat(parts, ignore_index=True)
    gain_rows, hyp_rows = [], []
    for k in keys:
        d = draws[draws.key == k].drop(columns="key")
        d.to_parquet(TAB / f"draws_{k}{suffix}.parquet", index=False)
        dom, _, _, primary = CONTRASTS[k]
        for n0 in (10, 15, 20, 30):
            for metric in ("r", "r_alt", "dice10", "dice5"):
                g = eb.gains(d, n0=n0, metric=metric)
                g["key"], g["domain"], g["metric"] = k, dom, metric
                gain_rows.append(g)
        g15 = eb.gains(d, n0=15).set_index("method")
        G, lo, hi = g15.loc["EB-Q", ["G", "G_lo", "G_hi"]]
        h1 = "met" if lo >= 2 else ("not met" if hi < 2 else "unclear")
        dr, dr_lo, dr_hi = eb.paired_diff(d, "EB-W", "S")
        fr, fr_lo, fr_hi = eb.paired_diff(d, "EB-W", "S", metric="fpr", ratio=True)
        harm = (dr_hi < -0.02) or (fr_lo > 1.5)
        q0, q0_lo, q0_hi = eb.paired_diff(d, "EB-Q", "EB-0")
        hyp_rows.append(dict(key=k, domain=dom, primary=primary, G_EBQ=G, G_lo=lo, G_hi=hi,
                             flag=g15.loc["EB-Q", "flag"], H1_domain=h1, dr_EBW_S=dr, dr_lo=dr_lo, dr_hi=dr_hi,
                             fpr_ratio_EBW_S=fr, fpr_ratio_lo=fr_lo, fpr_ratio_hi=fr_hi, H2_harm=harm,
                             dr_EBQ_EB0=q0, dr_EBQ_EB0_lo=q0_lo, dr_EBQ_EB0_hi=q0_hi, H3_domain=q0_lo > 0))
    gains = pd.concat(gain_rows, ignore_index=True)
    gains.to_csv(TAB / f"gains{suffix}.csv", index=False)
    hyp = pd.DataFrame(hyp_rows)
    prim = hyp[hyp.primary]
    if len(prim) == 6:
        nm, nn = (prim.H1_domain == "met").sum(), (prim.H1_domain == "not met").sum()
        v1 = "supported" if nm >= 5 else ("contradicted" if nn >= 2 else "inconclusive")
        v2 = "contradicted" if prim.H2_harm.any() else "supported"
        v3 = "supported" if prim.H3_domain.sum() >= 5 else "not supported"
        hyp["verdict_H1"], hyp["verdict_H2"], hyp["verdict_H3"] = v1, v2, v3
        print(f"H1 {v1} ({nm} met, {nn} not met) | H2 {v2} | H3 {v3}")
    hyp.to_csv(TAB / f"hypotheses{suffix}.csv", index=False)
    print(hyp.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
