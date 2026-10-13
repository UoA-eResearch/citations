"""Exploratory, added after the plan (logged as a deviation): if the affinity head does not track the
measured selectivity profile, does it respond to the protein *at all*?

Three ways to ask:
  1. Mantel-style: build a kinase-by-kinase distance matrix from the predictions (Euclidean distance
     between the 32-ligand prediction vectors of two kinases; each ligand's mean is removed first, which
     is cosmetic rather than a control -- a per-ligand constant cancels in the difference of two kinases'
     vectors, so the distances are identical either way) and
     correlate it with (a) the same distance built from the measurements and (b) pairwise sequence
     distance between the kinase-domain crops. A protein-blind head gives near-zero correlation with
     both; a protein-aware but mis-calibrated head correlates with sequence while missing the
     measurements.
  2. The share of a ligand's prediction spread that survives removing the kinase main effect.
  3. Whether predictions for kinases in the same Manning group are closer than across groups, measured
     and predicted.

Sequence distance is 1 - (identity from a global pairwise alignment of the crops, Biopython
PairwiseAligner with BLOSUM62). Writes results/tables/geometry.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
import assemble as S  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"


def seq_identity(a, b):
    from Bio import Align
    from Bio.Align import substitution_matrices
    al = Align.PairwiseAligner(mode="global", open_gap_score=-11, extend_gap_score=-1,
                               substitution_matrix=substitution_matrices.load("BLOSUM62"))
    aln = al.align(a, b)[0]
    s1, s2 = aln[0], aln[1]
    same = sum(x == y and x != "-" for x, y in zip(s1, s2))
    return same / max(len(a), len(b))


def centred_distance(m):
    """Kinase-by-kinase Euclidean distance between prediction vectors after removing ligand means."""
    c = m - np.nanmean(m, axis=1, keepdims=True)
    k = c.shape[1]
    d = np.zeros((k, k))
    for i in range(k):
        for j in range(i + 1, k):
            v = c[:, i] - c[:, j]
            d[i, j] = d[j, i] = np.sqrt(np.nanmean(v ** 2))
    return d


def tri(m):
    i, j = np.triu_indices(m.shape[0], 1)
    return m[i, j]


def identity_matrix(accs, kin):
    """Pairwise identity between the kinase-domain crops, cached: it depends only on the panel."""
    f = TAB / "kinase_identity.csv"
    if f.exists():
        t = pd.read_csv(f, index_col=0)
        if list(t.columns) == list(accs):
            return t.to_numpy(float)
    seqs = [kin[a]["crop_seq"] for a in accs]
    n = len(accs)
    ident = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            ident[i, j] = ident[j, i] = seq_identity(seqs[i], seqs[j])
        print(f"  identity row {i + 1}/{n}", flush=True)
    pd.DataFrame(ident, index=accs, columns=accs).to_csv(f)
    return ident


def mantel_test(da, db, nperm=9999, seed=20261013):
    """Permutation test for a Mantel-style correlation: permute one matrix's kinase labels, which keeps
    the dyadic dependence structure that makes a naive p-value on 496 non-independent pairs meaningless."""
    rng = np.random.default_rng(seed)
    obs = A.rho(tri(da), tri(db))
    n = da.shape[0]
    null = np.empty(nperm)
    for i in range(nperm):
        p = rng.permutation(n)
        null[i] = A.rho(tri(da[np.ix_(p, p)]), tri(db))
    return dict(rho=float(obs), p=float((1 + (np.abs(null) >= abs(obs)).sum()) / (nperm + 1)),
                null_95=[float(np.percentile(null, 2.5)), float(np.percentile(null, 97.5))], nperm=nperm)


def sequence_reliance(pred, meas, sd, nboot=2000, seed=20261013):
    """Is the model's kinase geometry more tightly tied to sequence than the measurements' own geometry is?

    The report makes this claim, so it needs an interval rather than two point estimates. Kinases are
    resampled (the unit the two distance matrices share), and both Mantel correlations and their
    difference are recomputed in each draw. Resampling kinases duplicates rows, which puts exact zeros on
    the diagonal blocks of the distance matrices; those are dropped rather than counted as real pairs.
    """
    rng = np.random.default_rng(seed)
    n = pred.shape[1]
    diffs, a_s, b_s = [], [], []
    for _ in range(nboot):
        idx = rng.integers(0, n, n)
        keep = np.triu(np.ones((n, n), bool), 1) & (idx[:, None] != idx[None, :])
        dp = centred_distance(pred[:, idx])[keep]
        dm = centred_distance(meas[:, idx])[keep]
        ds = sd[np.ix_(idx, idx)][keep]
        a, b = A.rho(dp, ds), A.rho(dm, ds)
        if np.isfinite(a) and np.isfinite(b):
            a_s.append(a), b_s.append(b), diffs.append(a - b)
    q = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]  # noqa: E731
    return dict(pred_vs_sequence_ci=q(a_s), meas_vs_sequence_ci=q(b_s), difference_ci=q(diffs),
                difference_point=float(np.median(diffs)),
                share_of_draws_positive=float(np.mean(np.asarray(diffs) > 0)), nboot=len(diffs))


def compression(pred, meas, ident, nperm=9999, nboot=2000, seed=20261013):
    """Per-pair ratio of predicted to measured mean absolute difference, and whether it depends on how
    similar the two kinases are.

    The first draft compared a ratio of medians (0.50) against a median of per-pair ratios (0.57) and
    called the result uniform. One estimator throughout, and a test of the dependence rather than an
    assertion: a dyadic permutation for the correlation with identity, and a kinase bootstrap for the
    near-versus-rest gap.
    """
    rng = np.random.default_rng(seed)
    n = pred.shape[1]
    iu = np.triu_indices(n, 1)
    dm = np.array([np.nanmean(np.abs(meas[:, i] - meas[:, j])) for i, j in zip(*iu)])
    dp = np.array([np.nanmean(np.abs(pred[:, i] - pred[:, j])) for i, j in zip(*iu)])
    ratio = dp / dm
    idv = ident[iu]
    near = idv >= 0.5
    obs = A.rho(idv, ratio)
    null = np.empty(nperm)
    for k in range(nperm):                      # permute kinase labels, preserving dyadic structure
        p = rng.permutation(n)
        null[k] = A.rho(ident[np.ix_(p, p)][iu], ratio)
    R = np.full((n, n), np.nan)             # dense ratio matrix, so a bootstrap draw is one index op
    R[iu] = ratio
    R.T[iu] = ratio
    gaps = []
    for _ in range(nboot):
        idx = rng.integers(0, n, n)
        keep = np.triu(np.ones((n, n), bool), 1) & (idx[:, None] != idx[None, :])
        im, rm = ident[np.ix_(idx, idx)][keep], R[np.ix_(idx, idx)][keep]
        m = np.isfinite(rm)
        if (im[m] >= 0.5).sum() >= 2 and (im[m] < 0.5).sum() >= 2:
            gaps.append(float(np.median(rm[m][im[m] >= 0.5]) - np.median(rm[m][im[m] < 0.5])))
    return dict(median_ratio_all_pairs=float(np.median(ratio)),
                median_ratio_near=float(np.median(ratio[near])),
                median_ratio_rest=float(np.median(ratio[~near])),
                ratio_range=[float(ratio.min()), float(ratio.max())],
                ratio_iqr=[float(np.percentile(ratio, 25)), float(np.percentile(ratio, 75))],
                n_pairs_expanded=int((ratio > 1).sum()),
                spearman_identity_vs_ratio=float(obs),
                permutation_p=float((1 + (np.abs(null) >= abs(obs)).sum()) / (nperm + 1)),
                near_minus_rest=dict(point=float(np.median(ratio[near]) - np.median(ratio[~near])),
                                     lo=float(np.percentile(gaps, 2.5)),
                                     hi=float(np.percentile(gaps, 97.5)), nboot=len(gaps)))


def main():
    d = S.davis()
    kin = {k["acc"]: k for k in d["panel"]["kinases"]}
    if len(sys.argv) > 1 and sys.argv[1] == "identity":
        ident = identity_matrix([k["acc"] for k in d["panel"]["kinases"]], kin)
        print("identity matrix cached;", f"median {np.median(tri(ident)):.3f}",
              f"range {tri(ident).min():.3f}-{tri(ident).max():.3f}")
        return
    pred, prob, meas, accs, cids = S.matrices("panel", d)
    n = len(accs)
    ident = identity_matrix(accs, kin)
    sd = 1 - ident
    dp, dm = centred_distance(pred), centred_distance(meas)
    groups = np.array([kin[a]["group"] for a in accs])
    same = (groups[:, None] == groups[None, :])
    out = dict(
        n_kinases=n,
        mantel_pred_vs_meas=float(A.rho(tri(dp), tri(dm))),
        mantel_pred_vs_sequence=float(A.rho(tri(dp), tri(sd))),
        mantel_meas_vs_sequence=float(A.rho(tri(dm), tri(sd))),
        mantel_prob_vs_meas=float(A.rho(tri(centred_distance(prob)), tri(dm))),
        # permutation tests and a kinase bootstrap, added because the report compares two of these
        # correlations with each other (see deviations D9)
        mantel_tests=dict(pred_vs_meas=mantel_test(dp, dm), pred_vs_sequence=mantel_test(dp, sd),
                          meas_vs_sequence=mantel_test(dm, sd)),
        sequence_reliance=sequence_reliance(pred, meas, sd),
        compression=compression(pred, meas, ident),
        identity_range=[float(tri(ident).min()), float(tri(ident).max())],
        median_identity=float(np.median(tri(ident))),
        same_group=dict(pred_within=float(np.median(dp[same & ~np.eye(n, dtype=bool)])),
                        pred_across=float(np.median(dp[~same])),
                        meas_within=float(np.median(dm[same & ~np.eye(n, dtype=bool)])),
                        meas_across=float(np.median(dm[~same]))),
        # the panel's four near-identical kinase pairs are natural test cases: CSNK1D/CSNK1E share 97% of
        # their kinase-domain sequence, so a protein-aware model should predict them almost alike, and the
        # measurements say how alike they really are
        near_pairs=[dict(a=kin[accs[i]]["davis_name"], b=kin[accs[j]]["davis_name"],
                         identity=round(float(ident[i, j]), 3),
                         meas_mean_abs_diff=float(np.nanmean(np.abs(meas[:, i] - meas[:, j]))),
                         pred_mean_abs_diff=float(np.nanmean(np.abs(pred[:, i] - pred[:, j]))),
                         meas_profile_rho=float(A.rho(meas[:, i], meas[:, j])),
                         pred_profile_rho=float(A.rho(pred[:, i], pred[:, j])))
                    for i in range(n) for j in range(i + 1, n) if ident[i, j] >= 0.5],
        all_pairs_median=dict(
            meas_mean_abs_diff=float(np.median([np.nanmean(np.abs(meas[:, i] - meas[:, j]))
                                                for i in range(n) for j in range(i + 1, n)])),
            pred_mean_abs_diff=float(np.median([np.nanmean(np.abs(pred[:, i] - pred[:, j]))
                                                for i in range(n) for j in range(i + 1, n)]))),
        spread=dict(pred_ligand_sd=float(np.median(np.nanstd(pred, axis=1))),
                    meas_ligand_sd=float(np.median(np.nanstd(meas, axis=1))),
                    pred_kinase_effect_sd=float(np.nanstd(np.nanmean(pred, axis=0))),
                    meas_kinase_effect_sd=float(np.nanstd(np.nanmean(meas, axis=0)))))
    A.save(out, "geometry.json")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
