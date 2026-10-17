"""Alignment validation sample (plan section 6).

  sample   all crossings up to 100, plus 100 random other aligned pairs, seeded. Each is shown as two sentences in
           RANDOM order, unlabelled (which is the preprint is hidden), with the stratum hidden, so the adjudicator
           judges only "do these two sentences report the same statistic (same quantity, same comparison)?" and
           cannot see the direction of any change. Written to data/validation/sample.jsonl; the key (stratum,
           order) to data/validation/key.csv.
  The adjudicator records id,correct (1/0),note in results/tables/alignment_validation_raw.csv; `merge` joins the key
  and writes results/tables/alignment_validation.csv for analysis.py.
"""
import gzip
import json
import random
import sys
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
V, TAB = RUN / "data" / "validation", RUN / "results" / "tables"


def sample():
    rows = [json.loads(l) for l in gzip.open(RUN / "data" / "aligned" / "statistics.jsonl.gz", "rt")]
    al = [r for r in rows if r["status"] == "aligned"]
    cross = [r for r in al if r["cls"] in ("crossing_up", "crossing_down")]
    other = [r for r in al if r["cls"] not in ("crossing_up", "crossing_down")]
    rnd = random.Random(20261017)
    pick = [("crossing", r) for r in rnd.sample(cross, min(100, len(cross)))] + \
           [("other", r) for r in rnd.sample(other, min(100, len(other)))]
    rnd.shuffle(pick)
    V.mkdir(parents=True, exist_ok=True)
    keys = []
    with open(V / "sample.jsonl", "w") as fh:
        for i, (stratum, r) in enumerate(pick):
            a, b = r["pre"]["sentence"], r["pub"]["sentence"]
            sa = f'{r["pre"]["test"] or "p"} {r["pre"]["cmp"]} {r["pre"]["p"]:g}'
            sb = f'{r["pub"]["test"] or "p"} {r["pub"]["cmp"]} {r["pub"]["p"]:g}'
            flip = rnd.random() < 0.5
            s1, s2, t1, t2 = (b, a, sb, sa) if flip else (a, b, sa, sb)
            # the aligned statistic is shown for each side, in the same random order, so the adjudicator can judge
            # statistic identity (not just sentence correspondence) without knowing which side is the preprint
            fh.write(json.dumps(dict(id=f"v{i:03d}", sentence_1=s1, sentence_2=s2, stat_1=t1, stat_2=t2),
                                ensure_ascii=False) + "\n")
            keys.append(dict(id=f"v{i:03d}", stratum=stratum, pre_is=2 if flip else 1, pair=r["pair"], how=r["how"]))
    pd.DataFrame(keys).to_csv(V / "key.csv", index=False)
    print(len(pick), "sampled:", pd.DataFrame(keys).stratum.value_counts().to_dict())


def merge():
    raw = pd.read_csv(TAB / "alignment_validation_raw.csv")
    key = pd.read_csv(V / "key.csv")
    m = raw.merge(key, on="id")
    m.to_csv(TAB / "alignment_validation.csv", index=False)
    print(m.groupby("stratum").correct.agg(["mean", "count"]))


if __name__ == "__main__":
    {"sample": sample, "merge": merge}[sys.argv[1]]()
