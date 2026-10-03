#!/usr/bin/env python
"""Similar pairs and activity cliffs exactly as MoleculeACE defines them (plan.md sec 2, 7).

MoleculeACE (benchmark/cliffs.py): a pair is similar if ANY of three similarities is >= 0.9:
  - Tanimoto on Morgan bit vectors (radius 2, 1024 bits) of the molecule;
  - Tanimoto on Morgan bit vectors (radius 2, 1024 bits) of RDKit's generic graph of the molecule (MakeScaffoldGeneric),
    falling back to the Murcko scaffold if that fails;
  - 1 - Levenshtein(smiles_i, smiles_j) / max(len_i, len_j).
A cliff is a similar pair whose fold change in exp_mean [nM] is > 10. A cliff molecule is in at least one cliff pair.
This file reimplements those matrices in vectorised form and writes every similar pair.

Usage: cliffs.py  -> results/tables/similar_pairs.parquet (dataset, i, j, tani, scaff, leve, fc, cliff),
                     results/tables/cliff_validation.csv (published vs recomputed cliff_mol)
"""
from pathlib import Path

import Levenshtein
import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.Scaffolds.MurckoScaffold import GetScaffoldForMol
from rdkit.Chem.Scaffolds.MurckoScaffold import MakeScaffoldGeneric as GraphFramework

RDLogger.DisableLog("rdApp.*")
RUN = Path(__file__).resolve().parents[1]
BENCH = RUN / "data" / "moleculeace" / "MoleculeACE" / "Data" / "benchmark_data"
GEN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=1024)


def fps(mols):
    return [GEN.GetFingerprint(m) for m in mols]


def generic(m):
    try:
        return GraphFramework(m)
    except Exception:
        return GetScaffoldForMol(m)


def tanimoto_matrix(fp):
    n = len(fp)
    M = np.zeros((n, n))
    for i in range(n):
        M[i, i:] = DataStructs.BulkTanimotoSimilarity(fp[i], fp[i:])
    M = M + M.T
    np.fill_diagonal(M, 0)
    return M


def levenshtein_matrix(smiles):
    n = len(smiles)
    M = np.zeros((n, n))
    L = np.array([len(s) for s in smiles])
    for i in range(n):
        d = np.array([Levenshtein.distance(smiles[i], smiles[j]) for j in range(i, n)])
        M[i, i:] = 1 - d / np.maximum(L[i], L[i:])
    M = M + M.T
    np.fill_diagonal(M, 0)
    return M


def dataset_pairs(path):
    df = pd.read_csv(path)
    smiles = df.smiles.tolist()
    mols = [Chem.MolFromSmiles(s) for s in smiles]
    T = tanimoto_matrix(fps(mols))
    S = tanimoto_matrix(fps([generic(m) for m in mols]))
    Lv = levenshtein_matrix(smiles)
    sim = (T >= 0.9) | (S >= 0.9) | (Lv >= 0.9)
    v = df["exp_mean [nM]"].values
    fc = np.maximum.outer(v, v) / np.minimum.outer(v, v)
    cliff = sim & (fc > 10)
    cliff_mol = cliff.any(1).astype(int)
    i, j = np.where(np.triu(sim, 1))
    pairs = pd.DataFrame(dict(dataset=path.stem, i=i, j=j, tani=T[i, j], scaff=S[i, j], leve=Lv[i, j], fc=fc[i, j],
                              cliff=cliff[i, j]))
    return df, pairs, cliff_mol


def main():
    allp, val = [], []
    for p in sorted(BENCH.glob("*.csv")):
        df, pairs, cm = dataset_pairs(p)
        allp.append(pairs)
        pub = df.cliff_mol.values
        val.append(dict(dataset=p.stem, n=len(df), n_test=int((df.split == "test").sum()), similar_pairs=len(pairs),
                        cliff_pairs=int(pairs.cliff.sum()), published_cliff_mols=int(pub.sum()),
                        recomputed_cliff_mols=int(cm.sum()), agreement=float((pub == cm).mean())))
        print(val[-1], flush=True)
    pd.concat(allp, ignore_index=True).to_parquet(RUN / "results" / "tables" / "similar_pairs.parquet", index=False)
    v = pd.DataFrame(val)
    v.to_csv(RUN / "results" / "tables" / "cliff_validation.csv", index=False)
    print("datasets with >= 99% agreement:", int((v.agreement >= 0.99).sum()), "of", len(v), "| min", v.agreement.min())


if __name__ == "__main__":
    main()
