"""Exploratory, added after the plan (logged as a deviation): if the affinity head does not track the
measured selectivity profile, does it respond to the protein *at all*?

Three ways to ask:
  1. Mantel-style: build a kinase-by-kinase distance matrix from the predictions (Euclidean distance
     between the 32-ligand prediction vectors of two kinases, after removing each ligand's mean) and
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


def main():
    d = S.davis()
    pred, prob, meas, accs, cids = S.matrices("panel", d)
    kin = {k["acc"]: k for k in d["panel"]["kinases"]}
    seqs = [kin[a]["crop_seq"] for a in accs]
    n = len(accs)
    ident = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            ident[i, j] = ident[j, i] = seq_identity(seqs[i], seqs[j])
        print(f"  identity row {i + 1}/{n}", flush=True)
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
        identity_range=[float(tri(ident).min()), float(tri(ident).max())],
        median_identity=float(np.median(tri(ident))),
        same_group=dict(pred_within=float(np.median(dp[same & ~np.eye(n, dtype=bool)])),
                        pred_across=float(np.median(dp[~same])),
                        meas_within=float(np.median(dm[same & ~np.eye(n, dtype=bool)])),
                        meas_across=float(np.median(dm[~same]))),
        spread=dict(pred_ligand_sd=float(np.median(np.nanstd(pred, axis=1))),
                    meas_ligand_sd=float(np.median(np.nanstd(meas, axis=1))),
                    pred_kinase_effect_sd=float(np.nanstd(np.nanmean(pred, axis=0))),
                    meas_kinase_effect_sd=float(np.nanstd(np.nanmean(meas, axis=0)))))
    np.save(TAB / "kinase_identity.npy", ident)
    pd.DataFrame(ident, index=accs, columns=accs).to_csv(TAB / "kinase_identity.csv")
    A.save(out, "geometry.json")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
