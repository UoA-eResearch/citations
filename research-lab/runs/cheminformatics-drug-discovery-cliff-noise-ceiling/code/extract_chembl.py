#!/usr/bin/env python
"""ChEMBL 37 activities for the benchmark targets and replicate pairs (plan.md sec 2-3).

For each of the 30 MoleculeACE (target, activity type) pairs: all activities with standard_relation '=', non-null
pchembl_value and null data_validity_comment, with molregno, standard InChIKey, assay id and type, document id and
year. Also, for the "all targets" sensitivity arm: inter-document replicate pairs of Ki and EC50 over every ChEMBL
target (one random pair per compound-target-type group, seed 0).
Output: data/chembl_bench.parquet, data/chembl_alltargets_pairs.parquet
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
DB = next((RUN / "data").glob("chembl_37/chembl_37_sqlite/chembl_37.db"))
BENCH = RUN / "data" / "moleculeace" / "MoleculeACE" / "Data" / "benchmark_data"

Q = """
SELECT a.molregno, td.chembl_id AS target, a.standard_type, a.pchembl_value, a.assay_id, ass.assay_type,
       a.doc_id, d.year, cs.standard_inchi_key AS inchikey
FROM activities a
JOIN assays ass ON a.assay_id = ass.assay_id
JOIN target_dictionary td ON ass.tid = td.tid
LEFT JOIN docs d ON a.doc_id = d.doc_id
LEFT JOIN compound_structures cs ON a.molregno = cs.molregno
WHERE a.standard_relation = '=' AND a.pchembl_value IS NOT NULL AND a.data_validity_comment IS NULL
  AND a.standard_type = ? AND td.chembl_id = ?
"""

QALL = """
SELECT a.molregno, ass.tid, a.standard_type, a.pchembl_value, a.doc_id
FROM activities a JOIN assays ass ON a.assay_id = ass.assay_id
WHERE a.standard_relation = '=' AND a.pchembl_value IS NOT NULL AND a.data_validity_comment IS NULL
  AND a.standard_type IN ('Ki', 'EC50')
"""


def main():
    con = sqlite3.connect(DB)
    parts = []
    for p in sorted(BENCH.glob("*.csv")):
        target, typ = p.stem.split("_")
        d = pd.read_sql_query(Q, con, params=(typ, target))
        d["dataset"] = p.stem
        parts.append(d)
        print(p.stem, len(d), "activities", flush=True)
    bench = pd.concat(parts, ignore_index=True)
    bench.to_parquet(RUN / "data" / "chembl_bench.parquet", index=False)
    a = pd.read_sql_query(QALL, con)
    print("all-target Ki/EC50 activities:", len(a), flush=True)
    rng = np.random.default_rng(0)
    rows = []
    for (m, t, s), g in a.groupby(["molregno", "tid", "standard_type"]):
        if g.doc_id.nunique() < 2:
            continue
        docs = g.drop_duplicates("doc_id")
        i, j = rng.choice(len(docs), 2, replace=False)
        rows.append((s, docs.pchembl_value.iloc[i], docs.pchembl_value.iloc[j]))
    pd.DataFrame(rows, columns=["standard_type", "x1", "x2"]).to_parquet(RUN / "data" / "chembl_alltargets_pairs.parquet", index=False)
    print("all-target inter-document replicate pairs:", len(rows))


if __name__ == "__main__":
    main()
