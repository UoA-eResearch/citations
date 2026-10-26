"""Targets, training sets and prospective sets (plan sections 2-3); delta audit sample (G4). No model is trained here.

-> data/train.parquet (target, inchikey, smiles, pchembl median, first_doc, first_year, first_assay, authors)
   data/prospective.parquet (target, set in {primary, lenient, alldelta}, inchikey, smiles, pchembl median)
   results/tables/targets.csv, results/tables/delta_audit.csv, coverage.json stages
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402

SEED, MIN33, MINNEW, CAP, FALLBACK = 20261026, 100, 50, 250, 60


def agg(df):
    return df.groupby(["target", "inchikey"]).agg(smiles=("smiles", "first"), pchembl=("pchembl", "median")).reset_index()


def main():
    a33 = pd.read_parquet(D / "act_33.parquet")
    a37 = pd.read_parquet(D / "act_37.parquet")
    ik33 = set(pd.read_parquet(D / "inchikeys_33.parquet").inchikey)
    id33 = set(pd.read_parquet(D / "activity_ids_33.parquet").activity_id)
    # training sets: per (target, compound) median; provenance from the earliest document measuring it on the target
    a33 = a33.dropna(subset=["inchikey"])
    a33["yr"] = a33.doc_year.fillna(9999)
    first = a33.sort_values(["yr", "doc_id"]).drop_duplicates(["target", "inchikey"])[
        ["target", "inchikey", "doc_id", "doc_year", "assay_id", "authors"]].rename(
        columns={"doc_id": "first_doc", "doc_year": "first_year", "assay_id": "first_assay"})
    tr = agg(a33).merge(first, on=["target", "inchikey"])
    new = a37[~a37.activity_id.isin(id33)].dropna(subset=["inchikey"])
    measured = set(zip(tr.target, tr.inchikey))
    sets = {
        "primary": new[(new.doc_year >= 2023) & ~new.inchikey.isin(ik33)],
        "lenient": new[(new.doc_year >= 2023) & new.inchikey.isin(ik33) &
                       ~pd.Series(list(zip(new.target, new.inchikey)), index=new.index).isin(measured)],
        "alldelta": new[~new.inchikey.isin(ik33)],
    }
    pros = pd.concat([agg(v).assign(set=k) for k, v in sets.items()], ignore_index=True)
    n33 = tr.groupby("target").size()
    nnew = pros[pros.set == "primary"].groupby("target").size()
    elig = sorted(set(n33[n33 >= MIN33].index) & set(nnew[nnew >= MINNEW].index))
    primary_def = "primary"
    if len(elig) < FALLBACK:                                   # plan section 3 fallback
        nlen = pros[pros.set == "lenient"].groupby("target").size()
        elig = sorted(set(n33[n33 >= MIN33].index) & set(nlen[nlen >= MINNEW].index))
        primary_def = "lenient"
    n_elig = len(elig)
    if len(elig) > CAP:
        elig = sorted(np.random.default_rng(SEED).choice(elig, CAP, replace=False))
    tg = pd.DataFrame({"target": elig, "n_train": n33.reindex(elig).values,
                       "n_primary": nnew.reindex(elig).fillna(0).astype(int).values})
    tg.to_csv(T / "targets.csv", index=False)
    tr[tr.target.isin(elig)].to_parquet(D / "train.parquet", index=False)
    pros[pros.target.isin(elig)].to_parquet(D / "prospective.parquet", index=False)
    cov = Coverage("targets", T / "coverage.json")
    for t in n33.index:
        cov.attempt(t)
        if t in set(elig):
            cov.ok(t)
        elif n33[t] < MIN33:
            cov.drop(t, "fewer than 100 compounds in ChEMBL 33")
        elif nnew.get(t, 0) < MINNEW and primary_def == "primary":
            cov.drop(t, "fewer than 50 primary prospective compounds")
        else:
            cov.drop(t, f"eligible but not in the random {CAP}" if n_elig > CAP else "not eligible")
    cov.save()
    # delta audit (G4): 60 new activities classified from their document records only
    smp = new.sample(60, random_state=SEED)
    a33k = a33.set_index(["target", "inchikey", "pchembl", "doc_id"]).index
    rows = []
    for r in smp.itertuples():
        if (r.target, r.inchikey, r.pchembl, r.doc_id) in a33k:
            cls = "re-deposited or corrected record"
        elif pd.notna(r.doc_year) and r.doc_year >= 2023:
            cls = "publication of 2023 or later"
        elif pd.notna(r.doc_year):
            cls = "older publication newly curated"
        else:
            cls = "other (no document year)"
        rows.append({"activity_id": r.activity_id, "target": r.target, "doc_id": r.doc_id, "doc_year": r.doc_year, "class": cls})
    au = pd.DataFrame(rows)
    au.to_csv(T / "delta_audit.csv", index=False)
    summary = {"activities_33": int(len(a33)), "activities_37": int(len(a37)), "new_activities": int(len(new)),
               "new_from_2023_docs": int((new.doc_year >= 2023).sum()), "primary_definition": primary_def,
               "eligible_targets": n_elig, "targets_used": len(elig),
               "prospective_compounds": {k: int((pros[pros.target.isin(elig)].set == k).sum()) for k in sets},
               "delta_audit": au["class"].value_counts().to_dict()}
    (T / "selection.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
