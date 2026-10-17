"""Free-text channel precision (plan section 2): up to 200 records whose element was found only by name (no
localcontexts URI anywhere), seeded (20261021), shown with +-200 characters around each match for hand adjudication
(1 = a genuine Local Contexts Notice/Label reference, 0 = an unrelated use of the words). Writes
data/precision_sample.txt and data/precision_key.csv; `merge` reads results/tables/precision_raw.csv (id,genuine,note)."""
import json
import random
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detect import LABEL_RES, NOTICE_RES  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def sample():
    c = [json.loads(l) for l in open(RUN / "data" / "census.jsonl")]
    name_only = [r for r in c if not (r["uri_labels"] or r["uri_notices"] or r["hub_projects"])]
    raw = {}
    for p in {r["platform"] for r in name_only}:
        for l in open(RUN / "data" / "raw" / p / "records.jsonl"):
            x = json.loads(l); raw[(p, str(x["id"]))] = json.dumps(x.get("full") or x["meta"], ensure_ascii=False)
    rnd = random.Random(20261021)
    pick = rnd.sample(name_only, min(200, len(name_only)))
    out, keys = [], []
    for i, r in enumerate(pick):
        t = raw[(r["platform"], str(r["id"]))]
        spans = []
        for rx in list(LABEL_RES.values()) + list(NOTICE_RES.values()):
            for m in rx.finditer(t):
                spans.append(t[max(0, m.start() - 200):m.end() + 200].replace("\\n", " "))
        out.append(f"=== p{i:03d} [{r['platform']}] {r['id']}\n" + "\n---\n".join(spans[:3]) + "\n")
        keys.append(dict(id=f"p{i:03d}", platform=r["platform"], record=r["id"]))
    (RUN / "data" / "precision_sample.txt").write_text("\n".join(out))
    pd.DataFrame(keys).to_csv(RUN / "data" / "precision_key.csv", index=False)
    print(len(name_only), "name-only records;", len(pick), "sampled")


def merge():
    m = pd.read_csv(RUN / "results" / "tables" / "precision_raw.csv").merge(pd.read_csv(RUN / "data" / "precision_key.csv"), on="id")
    m.to_csv(RUN / "results" / "tables" / "precision.csv", index=False)
    print(m.groupby("platform").genuine.agg(["mean", "count"]), "\noverall", m.genuine.mean())


if __name__ == "__main__":
    {"sample": sample, "merge": merge}[sys.argv[1]]()
