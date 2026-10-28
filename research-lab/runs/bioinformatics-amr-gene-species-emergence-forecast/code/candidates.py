"""Candidate pairs, labels and features for one forecast task (plan section 0).

A task is a cutoff year C and a horizon C+1..H. Candidates are (gene, species) pairs not established by C, where the
gene is established in at least one species by C and the species has at least 20 isolates by C. The label is
emergence in the horizon. "Established by Y" means the pair reached two isolates from different BioProjects by Y.

Every feature is computed from data through C, except the horizon isolate count of the species (and the null
probability built from it), which is the realised sampling effort and is given to the null and the model alike
(plan section 3).

  candidates.py C H NAME -> data/task_NAME.parquet, results/tables/task_NAME.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
MIN_ISOLATES = 20


def null_prob(n, f):
    """P(at least 2 carriers among n isolates) for a gene at frequency f."""
    n = np.asarray(n, float); f = np.asarray(f, float)
    q = np.clip(1 - f, 0, 1)
    return np.clip(1 - q ** n - n * f * q ** np.maximum(n - 1, 0), 0, 1)


def main(C, H, name):
    iso = pd.read_parquet(D / "isolates.parquet", columns=["year", "species", "genes"])
    pairs = pd.read_parquet(D / "pairs.parquet")
    tax = pd.read_parquet(D / "taxonomy.parquet").set_index("species")
    emb = pd.read_parquet(D / "gene_embeddings.parquet").set_index("gene") if (D / "gene_embeddings.parquet").exists() else None

    est = pairs[pairs.first_year_2bp <= C]                                  # established by the cutoff
    new = pairs[(pairs.first_year_2bp > C) & (pairs.first_year_2bp <= H)]   # emerged in the horizon
    n_cut = iso[iso.year <= C].species.value_counts()
    n_hor = iso[(iso.year > C) & (iso.year <= H)].species.value_counts()
    species = sorted(n_cut[n_cut >= MIN_ISOLATES].index)
    genes = sorted(est.gene.unique())
    gi = {g: i for i, g in enumerate(genes)}; si = {s: i for i, s in enumerate(species)}

    # gene frequency through the cutoff, and in the two three-year windows before it
    def freq(lo, hi):
        sub = iso[(iso.year >= lo) & (iso.year <= hi)]
        n = len(sub)
        c = pd.Series([g for gs in sub.genes for g in gs]).value_counts() if n else pd.Series(dtype=float)
        return (c / max(n, 1)).reindex(genes).fillna(0).to_numpy()
    f_cut = freq(1990, C)
    f_recent, f_older = freq(C - 2, C), freq(C - 5, C - 3)
    growth = np.log(f_recent + 1e-6) - np.log(f_older + 1e-6)

    A = np.zeros((len(genes), len(species)), dtype=np.float32)              # established gene x species at the cutoff
    e = est[est.gene.isin(gi) & est.species.isin(si)]
    A[[gi[g] for g in e.gene], [si[s] for s in e.species]] = 1
    n_species_g, n_genes_s = A.sum(1), A.sum(0)

    gen = tax.genus.reindex(species).to_numpy(); fam = tax.family.reindex(species).to_numpy()
    byg = pd.Series(range(len(species))).groupby(pd.Series(gen)).apply(list).to_dict()
    byf = pd.Series(range(len(species))).groupby(pd.Series(fam)).apply(list).to_dict()

    E = None
    if emb is not None:
        M = emb.reindex(genes)
        E = np.vstack([np.asarray(v, dtype=np.float32) if isinstance(v, (list, np.ndarray)) else np.zeros(emb.iloc[0, 0].shape, np.float32)
                       for v in M.embedding.to_numpy()])
        E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-9

    label = set(zip(new.gene, new.species))
    out = []
    for s in species:
        j = si[s]
        own = np.flatnonzero(A[:, j] > 0)                                   # genes the species already carries
        cand = np.flatnonzero(A[:, j] == 0)
        if not len(cand):
            continue
        nh, nc = float(n_hor.get(s, 0)), float(n_cut.get(s, 0))
        # co-occurrence: Jaccard of species sets, against the species' own genes
        if len(own):
            inter = A[:, :] @ A[own, :].T                                   # genes x own
            union = n_species_g[:, None] + n_species_g[own][None, :] - inter
            J = inter / np.maximum(union, 1)
            jmax = J[cand].max(1)
            k = min(5, J.shape[1])
            jtop5 = -np.sort(-J[cand], axis=1)[:, :k].mean(1)
        else:
            jmax = np.zeros(len(cand), np.float32); jtop5 = jmax
        if E is not None and len(own):
            sim = E[cand] @ E[own].T
            cmax = sim.max(1)
        else:
            cmax = np.zeros(len(cand), np.float32)
        gsib = [x for x in byg.get(gen[j], []) if x != j]
        fsib = [x for x in byf.get(fam[j], []) if x != j] if fam[j] is not None and fam[j] == fam[j] else []
        gcount = A[cand][:, gsib].sum(1) if gsib else np.zeros(len(cand), np.float32)
        fcount = A[cand][:, fsib].sum(1) if fsib else np.zeros(len(cand), np.float32)
        out.append(pd.DataFrame({
            "gene": pd.Categorical([genes[i] for i in cand], categories=genes), "species": s,
            "log_n_hor": np.log1p(nh), "log_n_cut": np.log1p(nc), "null_p": null_prob(nh, f_cut[cand]),
            "log_n_species_g": np.log1p(n_species_g[cand]), "log_freq_g": np.log(f_cut[cand] + 1e-6),
            "growth_g": growth[cand], "log_n_genes_s": np.log1p(n_genes_s[j]),
            "genus_count": gcount, "genus_has": (gcount > 0).astype(np.float32),
            "family_count": fcount, "family_has": (fcount > 0).astype(np.float32),
            "jaccard_max": jmax.astype(np.float32), "jaccard_top5": jtop5.astype(np.float32),
            "emb_cos_max": cmax.astype(np.float32),
            "y": [1 if (genes[i], s) in label else 0 for i in cand]}))
    d = pd.concat(out, ignore_index=True)
    for c in d.columns:
        if d[c].dtype == np.float64:
            d[c] = d[c].astype(np.float32)
    d.to_parquet(D / f"task_{name}.parquet")
    stats = {"cutoff": C, "horizon_end": H, "species": len(species), "genes": len(genes), "candidates": len(d),
             "positives": int(d.y.sum()), "base_rate": round(float(d.y.mean()), 8),
             "emerged_pairs_total": len(new), "emerged_in_candidates": int(d.y.sum()),
             "embedding_feature": E is not None}
    (T / f"task_{name}.json").write_text(json.dumps(stats, indent=1) + "\n")
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
