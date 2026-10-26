"""Extract filtered activities from a ChEMBL SQLite release (plan section 1). No model or target selection here.

  build.py unpack REL       -> data/raw/chembl_<REL>/chembl_<REL>.db (checksum verified first)
  build.py extract REL      -> data/act_<REL>.parquet: activity_id, target, inchikey, smiles, pchembl, doc_id, doc_year,
                               authors, assay_id; data/inchikeys_<REL>.parquet (every standard InChIKey in the release);
                               data/activity_ids_<REL>.parquet (every activity_id, unfiltered: "absent from 33" uses it);
                               results/tables/coverage.json stage activities_<REL> (rows removed by each filter)
Filters: pChEMBL present; standard_relation '='; assay type B; confidence score 9; target type SINGLE PROTEIN;
data_validity_comment null; potential_duplicate 0.
"""
import hashlib
import sqlite3
import sys
import tarfile
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402

FILTERS = [("pChEMBL present", "a.pchembl_value IS NOT NULL"),
           ("standard_relation '='", "a.standard_relation = '='"),
           ("assay type B", "s.assay_type = 'B'"),
           ("confidence score 9", "s.confidence_score = 9"),
           ("target type SINGLE PROTEIN", "t.target_type = 'SINGLE PROTEIN'"),
           ("data_validity_comment null", "a.data_validity_comment IS NULL"),
           ("potential_duplicate 0", "COALESCE(a.potential_duplicate, 0) = 0")]


def unpack(rel):
    tgz = D / "raw" / f"chembl_{rel}_sqlite.tar.gz"
    want = [l.split()[0] for l in (D / "raw" / f"checksums_{rel}.txt").read_text().splitlines() if l.strip().endswith(f"chembl_{rel}_sqlite.tar.gz")][0]
    h = hashlib.sha256()
    with open(tgz, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    assert h.hexdigest() == want, f"checksum mismatch for {tgz}"
    with tarfile.open(tgz) as t:
        member = [m for m in t.getmembers() if m.name.endswith(".db")][0]
        member.name = f"chembl_{rel}.db"
        t.extract(member, D / "raw" / f"chembl_{rel}", filter="data")
    print("unpacked", rel, flush=True)


def extract(rel):
    con = sqlite3.connect(f"file:{D / 'raw' / f'chembl_{rel}' / f'chembl_{rel}.db'}?mode=ro", uri=True)
    base = """FROM activities a JOIN assays s ON s.assay_id = a.assay_id JOIN target_dictionary t ON t.tid = s.tid
              JOIN compound_structures c ON c.molregno = a.molregno"""
    n_all = con.execute("SELECT count(*) FROM activities").fetchone()[0]
    total = con.execute(f"SELECT count(*) {base}").fetchone()[0]
    drops, where = {"no compound structure (biologics etc.)": n_all - total}, []
    prev = total
    for name, cond in FILTERS:
        where.append(cond)
        n = con.execute(f"SELECT count(*) {base} WHERE {' AND '.join(where)}").fetchone()[0]
        drops[f"fails: {name}"] = prev - n
        prev = n
    q = f"""SELECT a.activity_id, t.chembl_id AS target, c.standard_inchi_key AS inchikey, c.canonical_smiles AS smiles,
                   a.pchembl_value AS pchembl, a.doc_id, d.year AS doc_year, d.authors, a.assay_id
            {base} LEFT JOIN docs d ON d.doc_id = a.doc_id WHERE {' AND '.join(where)}"""
    df = pd.read_sql_query(q, con)
    df.to_parquet(D / f"act_{rel}.parquet", index=False)
    pd.read_sql_query("SELECT DISTINCT standard_inchi_key AS inchikey FROM compound_structures", con).to_parquet(
        D / f"inchikeys_{rel}.parquet", index=False)
    pd.read_sql_query("SELECT activity_id FROM activities", con).to_parquet(D / f"activity_ids_{rel}.parquet", index=False)
    cov = Coverage(f"activities_{rel}", T / "coverage.json")
    cov.add_counts(ok=len(df), drops=drops)
    cov.save()
    print(rel, "activities with structures", total, "kept", len(df), "targets", df.target.nunique(), flush=True)


if __name__ == "__main__":
    {"unpack": unpack, "extract": extract}[sys.argv[1]](int(sys.argv[2]))
