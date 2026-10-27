"""Benchmark construction (plan sections 1 and 3). Written before any outcome was read.

  build.py new -> data/new.parquet (target, aid, cid, smiles, key14, label, pains, frequent_hitter), coverage stages
  build.py lit -> data/lit.parquet (target, split, smiles, key14, label) from LIT-PCBA full_data
"""
import json
import sys
import tarfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW, D, T = RUN / "data" / "raw", RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402

MIN_ACTIVE, MIN_TESTED, MIN_TARGETS, FALLBACK_ACTIVE, STOP_TARGETS = 50, 5050, 20, 30, 15


def canon(smiles):
    """RDKit parse; returns (canonical SMILES, PAINS flag) or (None, None)."""
    from rdkit import Chem, RDLogger
    from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams
    RDLogger.DisableLog("rdApp.*")
    global _FC
    if "_FC" not in globals():
        p = FilterCatalogParams(); p.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS)
        _FC = FilterCatalog(p)
    m = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) and smiles else None
    if m is None:
        return None, None
    return Chem.MolToSmiles(m), bool(_FC.HasMatch(m))


def new():
    T.mkdir(parents=True, exist_ok=True)
    chosen = json.loads((RAW / "chosen.json").read_text())
    sm = pd.read_csv(RAW / "cid_smiles.csv").drop_duplicates("CID").set_index("CID")
    ca = Coverage("assays", T / "coverage.json")
    cs = Coverage("substances", T / "coverage.json")
    rows = []
    for r in chosen:
        aid, gene = r["aid"], r["genes"][0]
        ca.attempt(aid)
        lab = {}
        for kind, y in (("active", 1), ("inactive", 0)):
            for c in json.loads((RAW / "cids" / f"{aid}_{kind}.json").read_text()):
                lab.setdefault(c, set()).add(y)
        n_other = len(set(json.loads((RAW / "cids" / f"{aid}_all.json").read_text())) - set(lab))
        drops = Counter({"inconclusive or unspecified outcome": n_other})
        recs = []
        for c, ys in lab.items():
            if len(ys) > 1:
                drops["CID both active and inactive"] += 1; continue
            if c not in sm.index or not isinstance(sm.at[c, "SMILES"], str):
                drops["no structure for CID"] += 1; continue
            recs.append((c, sm.at[c, "SMILES"], str(sm.at[c, "InChIKey"])[:14], ys.pop()))
        df = pd.DataFrame(recs, columns=["cid", "smiles_pc", "key14", "label"])
        g = df.groupby("key14").label.agg(["nunique", "first", "size"])
        conflict = set(g[g["nunique"] > 1].index)
        drops["connectivity group with conflicting outcomes"] += int(df.key14.isin(conflict).sum())
        df = df[~df.key14.isin(conflict)].drop_duplicates("key14")
        drops["duplicate connectivity (kept one)"] += int(g.loc[~g.index.isin(conflict), "size"].sum() - (~g.index.isin(conflict)).sum())
        parsed = [canon(s) for s in df.smiles_pc]
        df["smiles"] = [p[0] for p in parsed]; df["pains"] = [p[1] for p in parsed]
        drops["RDKit cannot parse"] += int(df.smiles.isna().sum())
        df = df.dropna(subset=["smiles"])
        cs.add_counts(ok=int(len(df)), drops=dict(drops))
        df = df.assign(target=gene, aid=aid, deposit_year=int(str(r["deposit_date"])[:4] or 0))
        rows.append(df)
        n_act = int(df.label.sum())
        if n_act >= MIN_ACTIVE and len(df) >= MIN_TESTED:
            ca.ok(aid)
        else:
            ca.drop(aid, f"after the funnel: {n_act} actives, {len(df)} compounds")
    ca.save(); cs.save()
    allc = pd.concat(rows, ignore_index=True)
    keep = {r["aid"] for r in chosen if ca.status.get(r["aid"]) == "ok"}
    if len(keep) < MIN_TARGETS:      # plan: lower the active threshold, then stop below 15
        keep = {a for a, g in allc.groupby("aid") if g.label.sum() >= FALLBACK_ACTIVE and len(g) >= MIN_TESTED}
        note = f"fallback: >= {FALLBACK_ACTIVE} actives"
        if len(keep) < STOP_TARGETS:
            raise SystemExit(f"only {len(keep)} targets after the funnel; the plan stops here")
    else:
        note = f">= {MIN_ACTIVE} actives"
    allc = allc[allc.aid.isin(keep)]
    # frequent hitters: active in >= 30% of the NEW assays where tested, among compounds tested in >= 5
    t = allc.groupby("key14").label.agg(["mean", "size"])
    fh = set(t[(t["size"] >= 5) & (t["mean"] >= 0.30)].index)
    allc["frequent_hitter"] = allc.key14.isin(fh)
    allc.to_parquet(D / "new.parquet")
    summ = allc.groupby(["target", "aid", "deposit_year"]).agg(compounds=("key14", "size"), actives=("label", "sum"),
                                                               pains_share=("pains", "mean"), fh_actives=("frequent_hitter", "sum")).reset_index()
    summ.to_csv(T / "targets_new.csv", index=False)
    print(len(keep), "targets", note, "|", len(allc), "compound-target rows |", len(fh), "frequent hitters")
    (T / "build_new.json").write_text(json.dumps({"targets": len(keep), "rule": note, "rows": int(len(allc)),
                                                  "frequent_hitters": len(fh), "targets_2023plus": int((summ.deposit_year >= 2023).sum())}, indent=1))


def lit():
    # full_data.tgz: every target's complete actives/inactives (the analog-disjoint control, plan section 2)
    # AVE_unbiased.tgz: the published training (_T) and validation (_V) sets (plan section 3, as corrected in D1)
    rows = []
    for arch, kinds in (("full_data.tgz", {"actives.smi": ("all", 1), "inactives.smi": ("all", 0)}),
                        ("AVE_unbiased.tgz", {"active_T.smi": ("training", 1), "inactive_T.smi": ("training", 0),
                                              "active_V.smi": ("validation", 1), "inactive_V.smi": ("validation", 0)})):
        with tarfile.open(RAW / "LIT-PCBA" / arch) as tf:
            seen = 0
            for n in tf.getnames():
                parts = Path(n).parts
                if len(parts) < 2 or parts[-1] not in kinds:
                    continue
                split, label = kinds[parts[-1]]
                seen += 1
                for line in tf.extractfile(n).read().decode().splitlines():
                    f = line.split()
                    if f:
                        rows.append((parts[-2], split, f[0], label, arch))
            assert seen == 15 * len(kinds), f"{arch}: found {seen} split files, expected {15 * len(kinds)}"
    df = pd.DataFrame(rows, columns=["target", "split", "smiles_raw", "label", "archive"])
    print(df.groupby(["split", "label"]).agg(rows=("target", "size"), targets=("target", "nunique")).to_string())
    parsed = [canon(s) for s in df.smiles_raw]
    df["smiles"] = [x[0] for x in parsed]
    cov = Coverage("lit_compounds", T / "coverage.json")
    cov.add_counts(ok=int(df.smiles.notna().sum()), drops={"RDKit cannot parse": int(df.smiles.isna().sum())})
    cov.save()
    df.dropna(subset=["smiles"]).to_parquet(D / "lit.parquet")


if __name__ == "__main__":
    {"new": new, "lit": lit}[sys.argv[1]]()
