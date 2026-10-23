"""Reviewer checks on the gold construct: which 'inapplicable' records are arguably field/agricultural material,
the judgement-call rows, the pass-3 readings, and the three D5 s5 readings."""
import json
import re
import sys
import collections
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))

R = {x["record"]: x for x in (json.loads(l) for l in open(RUN / "data" / "gold" / "records.jsonl"))}
rows = pd.read_csv(RUN / "results" / "tables" / "limb2_rows.csv", keep_default_na=False).set_index("record")


def pass_labels(k):
    key = pd.read_csv(RUN / "data" / "gold" / f"pass{k}_key.csv").set_index("sheet_id").record
    lab = pd.read_csv(RUN / "data" / "gold" / f"pass{k}_labels.csv", keep_default_na=False)
    lab["record"] = lab.sheet_id.map(key)
    return lab


l1, l2, l3 = pass_labels(1), pass_labels(2), pass_labels(3)
b1, b2 = l1.set_index("record").basis, l2.set_index("record").basis

FIELD = re.compile(r"field|farm|cultivar|breed|orchard|pond|paddy|greenhouse|plantation|variety|landrace|livestock"
                   r"|pig\b|cattle|chicken|sheep|goat|aquacultur|hatchery|vineyard|crop|wheat|rice|maize|soy"
                   r"|tomato|cotton|dairy|genebank|germplasm|accession", re.I)

print("=== 'inapplicable' finals whose stated basis mentions field/agricultural/genebank material")
n = 0
for i in rows.index[rows.label == "inapplicable"]:
    b = f"{b1.get(i, '')} // {b2.get(i, '')}"
    if FIELD.search(b):
        n += 1
        print(f"  {i} [{(R[i]['organism'] or '')[:34]}] {b[:190]}")
print(n, "such records of", int((rows.label == 'inapplicable').sum()), "inapplicable")

print("\n=== organism counts, inapplicable (top 20)")
print(collections.Counter((R[i]['organism'] or '') for i in rows.index[rows.label == "inapplicable"]).most_common(20))
print("\n=== organism counts, not stated (top 12)")
print(collections.Counter((R[i]['organism'] or '') for i in rows.index[rows.label == "not stated"]).most_common(12))

print("\n=== JUDGEMENT CALL rows and their final labels")
for df, nm in ((l1, "pass1"), (l2, "pass2"), (l3, "pass3")):
    for r in df[df.basis.str.contains("JUDGEMENT CALL", case=False, na=False)].itertuples():
        fin = rows.label.get(r.record, "EXCLUDED")
        print(f"  {nm} {r.record} ({r.sheet_id}) -> {r.label!r}; final={fin!r}\n      {r.basis[:260]}")

print("\n=== pass 3: all 17 records, both earlier labels and the final")
for r in l3.itertuples():
    i = r.record
    print(f"  {i} p1={b1.get(i, '')[:0]}{l1.set_index('record').label.get(i)!r:16s} "
          f"p2={l2.set_index('record').label.get(i)!r:16s} p3={r.label!r:16s} final={rows.label.get(i, 'EXCL')!r}")
    print(f"      p3 basis: {r.basis[:220]}")

print("\n=== the three D5 s5 country readings (final label is a country, decided in pass 3)")
for r in l3.itertuples():
    if rows.label.get(r.record, "") not in ("inapplicable", "not stated", ""):
        x = R[r.record]
        print(f"\n  {r.record} -> {rows.label.get(r.record)}  organism={x['organism']}")
        print(f"    basis: {r.basis}")
        for f in ("sample_title", "isolation_source", "attributes", "comment", "bioproject_title"):
            if x.get(f):
                print(f"    {f}: {str(x[f])[:400]}")
        for p in x["publications"]:
            print(f"    pub {p['pmid']}: {p['title'][:160]}")
            if p.get("methods_sentences"):
                print(f"      sampling: {p['methods_sentences'][:700]}")
