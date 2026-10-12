"""Post-cutoff replication arm (plan.md §5.3), built from the local ChEMBL 37 SQLite copy.

Boltz-2's affinity training data are ChEMBL v34 (March 2024) plus BindingDB/PubChem/CeMM/MIDAS, so a
compound whose *earliest* ChEMBL document is 2025 or later cannot have been in that ChEMBL snapshot. For
each such compound we take every activity against an eligible human kinase measured in a document dated
2025 or later, and keep compounds with at least MIN_K distinct kinases, at least 4 distinct values and a
range of at least one log unit.

  python code/postcutoff.py select   -> data/postcut.json, results/tables/postcut_pairs.csv, MSA seq list
  python code/postcutoff.py yaml     -> data/inputs_postcut/
"""
import csv
import json
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import boltzrun as B  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
DB = ("/mnt/citations/research-lab/runs/cheminformatics-drug-discovery-cliff-noise-ceiling/"
      "data/chembl_37/chembl_37_sqlite/chembl_37.db")
YEAR = 2025
MIN_K = 6
FLANK = 20


def kinase_crops():
    """Eligible kinases by accession: exactly one annotated protein kinase domain of 220-350 aa."""
    out = {}
    for r in csv.DictReader(open(RUN / "data" / "uniprot_kinases.tsv"), delimiter="\t"):
        hits = re.findall(r'DOMAIN (\d+)\.\.(\d+); /note="Protein kinase', r["Domain [FT]"])
        if len(hits) != 1:
            continue
        s, e = int(hits[0][0]), int(hits[0][1])
        if not 220 <= e - s + 1 <= 350:
            continue
        seq = r["Sequence"]
        a, b = max(1, s - FLANK), min(len(seq), e + FLANK)
        out[r["Entry"]] = dict(acc=r["Entry"], gene=r["Gene Names (primary)"], dom_start=s, dom_end=e,
                              crop_start=a, crop_end=b, crop_seq=seq[a - 1:b], crop_len=b - a + 1,
                              similarity=r["Sequence similarities"])
    return out


def select():
    from rdkit import Chem
    from rdkit.Chem import Descriptors
    crops = kinase_crops()
    accs = sorted(crops)
    ph = ",".join("?" * len(accs))
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    q = f"""
    select md.chembl_id, cs2.canonical_smiles, cs.accession, a.standard_type, a.standard_relation,
           a.standard_value, d.year
    from activities a
    join assays ass on ass.assay_id = a.assay_id
    join target_dictionary td on td.tid = ass.tid
    join target_components tc on tc.tid = td.tid
    join component_sequences cs on cs.component_id = tc.component_id
    join docs d on d.doc_id = a.doc_id
    join molecule_dictionary md on md.molregno = a.molregno
    left join compound_structures cs2 on cs2.molregno = a.molregno
    where cs.accession in ({ph}) and a.standard_type in ('Kd','Ki','IC50')
      and a.standard_relation in ('=','>','<') and a.standard_units = 'nM' and a.standard_value > 0
      and td.target_type = 'SINGLE PROTEIN' and ass.confidence_score >= 8 and d.year >= ?
      and a.molregno in (select molregno from activities aa join docs dd on dd.doc_id = aa.doc_id
                         group by molregno having min(dd.year) >= ?)
    """
    rows = list(c.execute(q, accs + [YEAR, YEAR]))
    print(f"{len(rows)} post-cutoff activity rows")
    by = {}
    for chembl, smi, acc, typ, rel, val, year in rows:
        by.setdefault((chembl, smi), {}).setdefault(acc, []).append((typ, rel, float(val), year))
    out, pairs = [], []
    for (chembl, smi), ks in sorted(by.items()):
        if smi is None:
            continue
        m = Chem.MolFromSmiles(smi)
        if m is None or len(Chem.GetMolFrags(m)) != 1 or Descriptors.MolWt(m) > 700 \
           or m.GetNumHeavyAtoms() > 128:
            continue
        vals = {}
        for acc, obs in ks.items():
            v = float(np.median([o[2] for o in obs]))
            vals[acc] = dict(pact=9.0 - np.log10(v), nm=v, n_obs=len(obs),
                             types=sorted({o[0] for o in obs}), rels=sorted({o[1] for o in obs}))
        if len(vals) < MIN_K:
            continue
        p = np.array([v["pact"] for v in vals.values()])
        if np.unique(np.round(p, 6)).size < 4 or p.max() - p.min() < 1.0:
            continue
        out.append(dict(chembl_id=chembl, smiles=smi, mw=round(Descriptors.MolWt(m), 2),
                        kinases={a: v for a, v in sorted(vals.items())}))
        for acc, v in sorted(vals.items()):
            pairs.append(dict(chembl_id=chembl, acc=acc, gene=crops[acc]["gene"], **v))
    print(f"{len(out)} compounds qualify; {len(pairs)} pairs; "
          f"{len({p['acc'] for p in pairs})} distinct kinases")
    for o in out:
        print(f"  {o['chembl_id']:16s} {len(o['kinases']):2d} kinases  MW {o['mw']:.0f}")
    json.dump(dict(year=YEAR, min_k=MIN_K, compounds=out), open(RUN / "data" / "postcut.json", "w"), indent=1)
    with open(RUN / "results" / "tables" / "postcut_pairs.csv", "w", newline="") as f:
        w = csv.DictWriter(f, list(pairs[0]))
        w.writeheader()
        w.writerows(pairs)
    seqs = {f"{a}_pc": crops[a]["crop_seq"] for a in sorted({p["acc"] for p in pairs})}
    json.dump(seqs, open(RUN / "data" / "msa_seqs_postcut.json", "w"), indent=0)
    json.dump({a: crops[a] for a in sorted({p["acc"] for p in pairs})},
              open(RUN / "data" / "postcut_kinases.json", "w"), indent=1)
    print(f"wrote msa_seqs_postcut.json with {len(seqs)} kinase crops")


def yaml():
    P = json.load(open(RUN / "data" / "postcut.json"))
    crops = json.load(open(RUN / "data" / "postcut_kinases.json"))
    d = RUN / "data" / "inputs_postcut"
    d.mkdir(parents=True, exist_ok=True)
    n = 0
    for comp in P["compounds"]:
        for acc in comp["kinases"]:
            B.write_yaml(d, f"{acc}_pc__{comp['chembl_id']}", f"{acc}_pc", crops[acc]["crop_seq"],
                         comp["smiles"])
            n += 1
    print(f"postcut: {n} complexes -> {d}")


if __name__ == "__main__":
    dict(select=select, yaml=yaml)[sys.argv[1]]()
