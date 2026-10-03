#!/usr/bin/env python
"""Checks added after independent review (deviations.md D5).

(1) Model check: among all similar pairs, observed counts of |d| > 2, 3, 4 versus the counts expected from noise ALONE
    under each noise model (a valid noise model cannot predict more extreme differences than are observed).
(2) Shared documents: share of similar and cliff pairs whose two molecules appear in a common pre-2022 ChEMBL document
    (lab-to-lab offsets cancel within a document), and the share of cliff-pair molecules with exactly one document.
(3) Gaussian-arm confidences saved (pairs and the fitted prior), for the null's restricted-gap analogue and the report.
(4) Shared-document sensitivity (Gaussian): pairs sharing a document get per-measurement noise sigma_w = 0.3 instead of
    the inter-document sigma.
Output: results/tables/review_model_check.csv, review_shared_docs.csv, cliff_pairs_conf_normal.parquet,
        npmle_prior_normal.npy, review_shared_doc_sensitivity.csv, molecule_docs.parquet
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import models as MD  # noqa: E402
import noise_eb as NE  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"


def tdiff_sf(k, scale, n=200000, seed=0):
    """P(|e1 - e2| > k) for e1, e2 iid t4 with the given scale (Monte Carlo)."""
    rng = np.random.default_rng(seed)
    e = (rng.standard_t(4, n) - rng.standard_t(4, n))
    return float(np.mean(np.abs(e) > k / scale))


def main():
    cp = pd.read_parquet(TAB / "cliff_pairs_conf.parquet")
    mol = pd.read_parquet(TAB / "molecules.parquet")
    nm = pd.read_csv(TAB / "noise_model.csv").set_index("standard_type")
    cp["type"] = cp.dataset.str.split("_").str[1]
    # (1) model check
    rows = []
    for k in (2, 3, 4):
        obs = int((cp.d.abs() > k).sum())
        exp_g = float((2 * stats.norm.sf(k / cp.sd.values)).sum())
        # t: per pair, the noise of a difference of two single measurements with per-type scale (n_i = 1 for ~96%)
        exp_t = float(sum(tdiff_sf(k, nm.sigma[t]) * (cp.type == t).sum() for t in ("Ki", "EC50")))
        rows.append(dict(threshold=k, observed=obs, expected_noise_only_gaussian=round(exp_g, 1),
                         expected_noise_only_t=round(exp_t, 1)))
    mc = pd.DataFrame(rows)
    mc.to_csv(TAB / "review_model_check.csv", index=False)
    print(mc.to_string(index=False))
    # (2) shared documents
    ch = pd.read_parquet(RUN / "data" / "chembl_bench.parquet")
    pre = ch[ch.year.fillna(0) <= 2021]
    docs_rows = []
    for p in sorted(MD.BENCH.glob("*.csv")):
        df = pd.read_csv(p)
        sub = pre[pre.dataset == p.stem]
        by_key = sub.groupby("inchikey").doc_id.apply(lambda x: frozenset(x.dropna().astype(int)))
        for idx, smi in enumerate(df.smiles):
            k = NE.inchikey(smi)
            docs_rows.append(dict(dataset=p.stem, idx=idx, docs=sorted(by_key.get(k, frozenset()))))
    md = pd.DataFrame(docs_rows)
    md.to_parquet(TAB / "molecule_docs.parquet", index=False)
    dmap = {(r.dataset, r.idx): set(r.docs) for r in md.itertuples()}
    cp["shared_doc"] = [bool(dmap[(d, i)] & dmap[(d, j)]) for d, i, j in zip(cp.dataset, cp.i, cp.j)]
    cl = cp[cp.cliff]
    clm = set(zip(cl.dataset, cl.i)) | set(zip(cl.dataset, cl.j))
    one_doc = np.mean([len(dmap[m]) == 1 for m in clm])
    sd = pd.DataFrame([dict(similar_pairs_shared_doc=cp.shared_doc.mean(), cliff_pairs_shared_doc=cl.shared_doc.mean(),
                            cliff_molecules_with_one_doc=one_doc)])
    sd.to_csv(TAB / "review_shared_docs.csv", index=False)
    print(sd.round(3).to_string(index=False))
    # (3) Gaussian-arm confidences and prior
    w = NE.npmle(cp.d.values, cp.sd.values, "normal")
    np.save(TAB / "npmle_prior_normal.npy", w)
    cp["conf_normal"] = NE.confidence(cp.d.values, cp.sd.values, w, "normal")
    cp[["dataset", "i", "j", "d", "sd", "cliff", "conf", "conf_normal", "shared_doc"]].to_parquet(
        TAB / "cliff_pairs_conf_normal.parquet", index=False)
    c = cp[cp.cliff].conf_normal
    print("Gaussian arm: cliffs conf<=0.8 %.3f, >=0.9 %.3f; prior mass |delta|>1 %.3f; min |d| among conf>=0.9 cliffs %.2f"
          % ((c <= 0.8).mean(), (c >= 0.9).mean(), w[np.abs(NE.GRID) > 1].sum(), cp[cp.cliff & (cp.conf_normal >= 0.9)].d.abs().min()))
    # (4) shared-document sensitivity (Gaussian)
    sd2 = np.where(cp.shared_doc, np.sqrt(2) * 0.3, cp.sd.values)
    w2 = NE.npmle(cp.d.values, sd2, "normal")
    c2 = NE.confidence(cp.d.values, sd2, w2, "normal")[cp.cliff.values]
    sens = pd.DataFrame([dict(sigma_within_shared_doc=0.3, frac_conf_le_0p8=float((c2 <= 0.8).mean()),
                              frac_conf_ge_0p9=float((c2 >= 0.9).mean()))])
    sens.to_csv(TAB / "review_shared_doc_sensitivity.csv", index=False)
    print(sens.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
