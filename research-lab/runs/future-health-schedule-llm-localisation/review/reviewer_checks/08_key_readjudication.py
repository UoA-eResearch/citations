"""Reviewer check 1: the reviewer's adjudication of the 96 fresh items in sheets/key_sample.txt (hand-read against the
NZ PDF blocks / SA blocks and the raw PBS JSON), written to reviewer_key_readjudication.csv with a per-cell summary.
Also: Youden's J for family (b) (a yes-bias-free comparison) with the same chemical-cluster bootstrap; the name of the
ATC2 group supplying most counterfactuals; report.html verdict line."""
import json, re, math
from pathlib import Path
import numpy as np, pandas as pd
import xml.etree.ElementTree as ET
RUN = Path(__file__).resolve().parents[2]; OUT = RUN / "review/reviewer_checks"
ids = json.load(open(OUT / "key_sample_ids.json"))
items = {json.loads(l)["id"]: json.loads(l) for l in open(RUN / "data/items.jsonl")}
wrong = {"NZ-d-0517": "own SA2548 has 'The individual has ECOG performance score 0-2' - restatement, correct answer is yes",
         "NZ-d-0472": "own SA2385 3.2.2 'Patient has experienced treatment-limiting toxicity with imatinib precluding further treatment' - restatement",
         "AU-d-0984": "own restriction has 'The treatment must be the sole PBS-subsidised systemic anti-cancer therapy for this condition' - differs only by 'PBS indication'/'condition'"}
border = {"NZ-d-0542": "narrower form of own 1.2.2.1 'Seizures are not adequately controlled with optimal treatment with other antiepilepsy agents' (key defensible)",
          "NZ-a-0022": "NZ lists omeprazole Cap 10 mg, not a tablet; key correct on form only", "NZ-a-0001": "NZ lists Cap 20 mg, not a tablet; form only",
          "AU-a-0569": "PBS lists omeprazole Tablet 10 mg (as magnesium), not a capsule; form only",
          "NZ-b-0216": "PDF heading is 'DIMETHYL FUMARATE' (normaliser joins the words); SA2274 applies; key correct"}
rows = []
for i in ids:
    x = items[i]
    rows.append(dict(id=i, jurisdiction=x["jurisdiction"], family=x["family"], answer=x["answer"], key_correct=0 if i in wrong else 1,
                     note=wrong.get(i, border.get(i, ""))))
df = pd.DataFrame(rows); df.to_csv(OUT / "reviewer_key_readjudication.csv", index=False)
print("== reviewer key re-adjudication (96 fresh items, none in either validation sample) ==")
print("overall wrong:", int((df.key_correct == 0).sum()), "/", len(df), f"= {(df.key_correct == 0).mean():.3f}")
print(df.assign(w=1 - df.key_correct).groupby(["family", "answer"]).w.agg(["size", "sum"]).rename(columns={"size": "n", "sum": "wrong"}).to_string())
print(df.assign(w=1 - df.key_correct).groupby(["jurisdiction", "family", "answer"]).w.agg(["size", "sum"]).rename(columns={"size": "n", "sum": "wrong"}).to_string())
# compare with agent's round-2 per-cell rates
kv = json.load(open(RUN / "results/tables/key_validation_round2.json"))
print("agent round 2 by cell:", kv["by_cell"])

print("\n== Youden's J (TPR + TNR - 1) for family (b), zero-shot, chemical-cluster bootstrap ==")
it = pd.DataFrame(items.values())
rn = pd.DataFrame([json.loads(l) for l in open(RUN / "data/runs.jsonl")])
d = rn.merge(it[["id", "family", "jurisdiction", "chemical", "answer"]].rename(columns={"answer": "truth"}), on="id")
d = d[(d.condition == "zero")]
def J(x, j):
    y = x[x.jurisdiction == j]
    tpr = (y[y.truth == "yes"].answer == "yes").mean(); tnr = (y[y.truth == "no"].answer == "no").mean()
    return tpr + tnr - 1
for fams in (["b"], ["a", "b"]):
    ab = d[d.family.isin(fams)]; chems = sorted(ab.chemical.unique()); grp = {c: x for c, x in ab.groupby("chemical")}
    rng = np.random.default_rng(20261018); draws = []
    for _ in range(2000):
        s = pd.concat([grp[c] for c in rng.choice(chems, len(chems))]); draws.append(J(s, "NZ") - J(s, "AU"))
    print(f"{'+'.join(fams)}: J_NZ={J(ab,'NZ'):.3f} J_AU={J(ab,'AU'):.3f} diff={J(ab,'NZ')-J(ab,'AU'):+.3f} CI=({np.percentile(draws,2.5):+.3f},{np.percentile(draws,97.5):+.3f})")

print("\n== ATC2 group names (NZ XML) for the groups supplying counterfactuals ==")
NS = "{http://schedule.pharmac.govt.nz/2006/07/Schedule#}"
r = ET.parse(RUN / "data/raw/nz/Schedule_2026-10.xml").getroot()
names = {a.get("ID"): a.findtext(NS + "Name") for a in r.iter(NS + "ATC2")}
for g in ("A2501", "A1604", "A2507", "A2207", "A1603", "A2504"): print(g, "->", names.get(g))
cf = [x for x in items.values() if x["family"] == "d" and x["answer"] == "no"]
import sys; sys.path.insert(0, str(RUN / "code")); import generate as G
_, _, atc2 = G.nz(RUN / "data/raw/nz/Schedule_2026-10.xml")
share = {j: sum(atc2.get(x["chemical"]) == "A2501" for x in cf if x["jurisdiction"] == j) for j in ("NZ", "AU")}
print("CF items whose target is in A2501:", share)
tr = [x for x in items.values() if x["family"] == "d" and x["answer"] == "yes"]
print("true-criterion items whose chemical is in A2501:", {j: sum(atc2.get(x["chemical"]) == "A2501" for x in tr if x["jurisdiction"] == j) for j in ("NZ", "AU")})
