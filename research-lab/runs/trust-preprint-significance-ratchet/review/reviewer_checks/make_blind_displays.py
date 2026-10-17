"""Blind displays for the reviewer's re-adjudication: all 64 v2 crossings (identified from the key only to select
them; the display itself hides stratum and version order) and 60 v1 items = the 12 crossings the agent judged correct
plus a seeded random 48 of the other 188. Output: blind_v1.md, blind_v2.md (id, two sentences, two stats only)."""
import json, random
import pandas as pd
from pathlib import Path
RUN = Path(__file__).resolve().parents[2]
V, TAB, OUT = RUN / "data" / "validation", RUN / "results" / "tables", Path(__file__).resolve().parent

def load(sample):
    return {json.loads(l)["id"]: json.loads(l) for l in open(V / sample)}

def write(name, ids, s):
    with open(OUT / name, "w") as fh:
        for i in ids:
            x = s[i]
            fh.write(f"## {i}\nS1: {x['sentence_1']}\n   [{x['stat_1']}]\nS2: {x['sentence_2']}\n   [{x['stat_2']}]\n\n")

s1, s2 = load("sample.jsonl"), load("sample_v2.jsonl")
k1 = pd.read_csv(TAB / "alignment_validation.csv"); k2 = pd.read_csv(TAB / "alignment_validation_v2.csv")
cross_ok = list(k1[(k1.stratum == "crossing") & (k1.correct == 1)].id)
rest = [i for i in k1.id if i not in cross_ok]
rnd = random.Random(20261017)
extra = sorted(rnd.sample(rest, 48))
ids1 = sorted(cross_ok + extra)
ids2 = sorted(k2[k2.stratum == "crossing"].id)
write("blind_v1.md", ids1, s1); write("blind_v2.md", ids2, s2)
json.dump(dict(v1=ids1, v2=ids2), open(OUT / "readjudication_ids.json", "w"), indent=1)
print(len(ids1), "v1 items;", len(ids2), "v2 items")
