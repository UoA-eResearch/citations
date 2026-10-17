"""Blind validation of the exploratory v2 strict crossings (deviations D3.2).

  sample   up to 100 strict crossings and 50 strict non-crossings from the v1 population, seeded. Shown in random
           order with the version order and stratum hidden; the aligned statistic is marked ⟦like this⟧ in each
           sentence and its value shown. Writes data/validation/sample_v2.jsonl and key_v2.csv.
  merge    joins results/tables/alignment_validation_v2_raw.csv (id,correct,note) with the key ->
           results/tables/alignment_validation_v2.csv.
"""
import gzip
import json
import random
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis_v2 import CROSS, strict  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
V, TAB = RUN / "data" / "validation", RUN / "results" / "tables"


def mark(x):
    s, i, n = x["sentence"], x["pos"], len(x["raw"])
    return s[:i] + "⟦" + s[i:i + n] + "⟧" + s[i + n:]


def show(x):
    return f'{x["test"] or "p"} {x["cmp"]} {x["p"]:g}'


def sample():
    pairs = pd.DataFrame([json.loads(l) for l in open(RUN / "data" / "aligned_v2" / "pairs.jsonl")])
    v1 = set(pairs[pairs.version_used.astype(str) == "1"].preprint_doi)
    st_ = [r for r in (json.loads(l) for l in gzip.open(RUN / "data" / "aligned_v2" / "statistics.jsonl.gz", "rt"))
           if r["status"] == "aligned" and r["pair"] in v1 and strict(r)]
    cross = [r for r in st_ if r["cls"] in CROSS]
    other = [r for r in st_ if r["cls"] not in CROSS and r["pre"]["p"] is not None and r["pub"]["p"] is not None]
    rnd = random.Random(20261018)
    pick = [("crossing", r) for r in rnd.sample(cross, min(100, len(cross)))] + \
           [("other", r) for r in rnd.sample(other, min(50, len(other)))]
    rnd.shuffle(pick)
    V.mkdir(parents=True, exist_ok=True)
    keys = []
    with open(V / "sample_v2.jsonl", "w") as fh:
        for i, (stratum, r) in enumerate(pick):
            a, b = (mark(r["pre"]), show(r["pre"])), (mark(r["pub"]), show(r["pub"]))
            flip = rnd.random() < 0.5
            (s1, t1), (s2, t2) = (b, a) if flip else (a, b)
            fh.write(json.dumps(dict(id=f"w{i:03d}", sentence_1=s1, sentence_2=s2, stat_1=t1, stat_2=t2),
                                ensure_ascii=False) + "\n")
            keys.append(dict(id=f"w{i:03d}", stratum=stratum, pre_is=2 if flip else 1, pair=r["pair"], how=r["how"]))
    pd.DataFrame(keys).to_csv(V / "key_v2.csv", index=False)
    print(len(pick), "sampled:", pd.DataFrame(keys).stratum.value_counts().to_dict())


def merge():
    m = pd.read_csv(TAB / "alignment_validation_v2_raw.csv").merge(pd.read_csv(V / "key_v2.csv"), on="id")
    m.to_csv(TAB / "alignment_validation_v2.csv", index=False)
    print(m.groupby("stratum").correct.agg(["mean", "count"]))


if __name__ == "__main__":
    {"sample": sample, "merge": merge}[sys.argv[1]]()
