"""H1, H2 and the secondary analyses across datasets (plan sections 1 and 2; D1-D4).

Reads results/tables/group/<ds>.json (grouplevel.py).
  H1: OLS of R on log10 N and tSNR across datasets; R^2 with 2,000 bootstrap resamples of datasets (seed 20261110).
      Supported if the lower bound exceeds 0.4; Refuted if the upper bound is below 0.4; otherwise Inconclusive.
  H2: datasets with N < 25: median R, 2,000 bootstrap resamples of those datasets. Supported if the upper bound is
      below 0.5; Refuted if the lower bound is at least 0.5; otherwise Inconclusive. Not testable if fewer than 5.
Secondary: the same with the secondary threshold, the task-positive contrast and the correlation index; per-axis
Dice pooled; the software comparison (D3); R against the descriptive predictors; the atlas table.

  analyse.py -> results/tables/primary.json, results/tables/atlas.csv
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
SEED, B = 20261110, 2000


def r2(y, X):
    X1 = np.c_[np.ones(len(y)), X]
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    res = y - X1 @ beta
    tot = ((y - y.mean()) ** 2).sum()
    return 1 - (res ** 2).sum() / tot if tot > 0 else np.nan, beta


def h1(df, col):
    d = df.dropna(subset=[col, "N", "tsnr"])
    y, X = d[col].to_numpy(float), np.c_[np.log10(d.N.to_numpy(float)), d.tsnr.to_numpy(float)]
    est, beta = r2(y, X)
    rng = np.random.default_rng(SEED)
    bs = []
    for _ in range(B):
        i = rng.integers(0, len(y), len(y))
        v, _ = r2(y[i], X[i])
        if np.isfinite(v):
            bs.append(v)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    verdict = "Supported" if lo > 0.4 else "Refuted" if hi < 0.4 else "Inconclusive"
    return {"R2": round(float(est), 4), "ci": [round(float(lo), 4), round(float(hi), 4)], "datasets": int(len(y)),
            "coef_log10N": round(float(beta[1]), 4), "coef_tsnr": round(float(beta[2]), 5), "verdict": verdict}


def h2(df, col):
    d = df[(df.N < 25)].dropna(subset=[col])
    if len(d) < 5:
        return {"datasets": int(len(d)), "verdict": "not testable"}
    y = d[col].to_numpy(float)
    rng = np.random.default_rng(SEED)
    bs = [np.median(y[rng.integers(0, len(y), len(y))]) for _ in range(B)]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    verdict = "Supported" if hi < 0.5 else "Refuted" if lo >= 0.5 else "Inconclusive"
    return {"median": round(float(np.median(y)), 4), "ci": [round(float(lo), 4), round(float(hi), 4)],
            "datasets": int(len(y)), "verdict": verdict}


def main():
    rows = []
    for f in sorted((T / "group").glob("ds*.json")):
        g = json.loads(f.read_text())
        if g.get("status") != "ok":
            continue
        r = {"ds": g["ds"], "N": g["N"], "tsnr": g["tsnr"], "runs_per_subject": g["runs_per_subject"],
             "volumes_per_subject": g["volumes_per_subject"], "fd_median": g["fd_median"], "voxels": g["voxels"],
             "R": g["primary"]["R"], "R_sec": g["secondary_threshold"]["R"], "corr": g["primary"]["corr"],
             "peak": g["primary"]["peak"], "any": g["primary"]["any"], "pairs_both_empty": g["primary"]["pairs_both_empty"],
             "supra_median": g["suprathreshold_voxels_median"],
             "R_task_positive": (g.get("task_positive") or {}).get("R")}
        for ax, v in g["axis_dice"].items():
            r[f"axis_{ax}"] = v
        if g.get("software"):
            r["software_dice"] = float(np.mean([x for x in g["software"]["dice_fsl_vs_nilearn"] if x is not None]))
            r["software_corr"] = float(np.mean(g["software"]["corr_fsl_vs_nilearn"]))
            cp = [x for x in g["software"]["dice_nilearn_confound_pairs"] if x is not None]
            r["confound_dice_subset"] = float(np.mean(cp)) if cp else None
        rows.append(r)
    df = pd.DataFrame(rows)
    E = pd.read_csv(T / "eligible.csv").set_index("ds")
    df["task"] = df.ds.map(E.task)
    df["contrast"] = df.ds.map(E.contrast)
    out = {"datasets": int(len(df)), "H1": h1(df, "R"), "H2": h2(df, "R")}
    out["secondary"] = {
        "H1_secondary_threshold": h1(df, "R_sec"), "H2_secondary_threshold": h2(df, "R_sec"),
        "H1_correlation_index": h1(df, "corr"),
        "H1_task_positive": h1(df, "R_task_positive") if df.R_task_positive.notna().sum() >= 5 else None,
        "axis_dice_mean": {ax: round(float(df[f"axis_{ax}"].mean()), 4) for ax in ("smoothing", "hrf", "confounds", "noise")},
        "software": ({"datasets": int(df.software_dice.notna().sum()), "dice_mean": round(float(df.software_dice.mean()), 4),
                      "corr_mean": round(float(df.software_corr.mean()), 4),
                      "confound_dice_on_same_subjects": round(float(df.confound_dice_subset.mean()), 4)}
                     if "software_dice" in df else None),
        "R_vs_descriptives_spearman": {c: round(float(df[["R", c]].corr("spearman").iloc[0, 1]), 3)
                                       for c in ("runs_per_subject", "volumes_per_subject", "fd_median", "supra_median")},
        "R_median_all": round(float(df.R.median()), 4)}
    df.sort_values("ds").to_csv(T / "atlas.csv", index=False)
    (T / "primary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
