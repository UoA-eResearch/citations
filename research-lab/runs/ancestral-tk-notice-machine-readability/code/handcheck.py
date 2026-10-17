"""Hand check of 100 record-views (plan section 3). Sample (seed 20261022): per view, 9 record-views at random from
its most common result plus up to 2 from its rarer results (so the scorer's rare calls are checked too), then one
more at random; unavailable views are excluded, as they are from H2. Writes data/validation/handcheck_sheet.txt
(the scorer's call, the element the DOI carries in DataCite, and body excerpts around every element match or, if
none, around rights/licence fields) and data/validation/handcheck_sample.csv. The adjudication is entered in
results/tables/handcheck.csv."""
import gzip
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detect import LABEL_RES, NOTICE_RES, URI_RE  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def main():
    V = [json.loads(l) for l in open(RUN / "data" / "views.jsonl")]
    V = [v for v in V if v["result"] != "unavailable"]
    cen = {}
    for l in open(RUN / "data" / "census.jsonl"):
        r = json.loads(l)
        if r.get("doi"):
            cen[r["doi"].lower()] = r
    rnd = random.Random(20261022)
    pick = []
    for view in sorted({v["view"] for v in V}):
        vv = [v for v in V if v["view"] == view]
        common = Counter(v["result"] for v in vv).most_common(1)[0][0]
        rare = [v for v in vv if v["result"] != common]
        pick += rnd.sample([v for v in vv if v["result"] == common], 9) + rnd.sample(rare, min(2, len(rare)))
    rest = [v for v in V if v not in pick]
    pick += rnd.sample(rest, 100 - len(pick))
    pats = [URI_RE] + list(LABEL_RES.values()) + list(NOTICE_RES.values())
    out = []
    for i, v in enumerate(pick):
        body = gzip.decompress((RUN / "data" / "raw" / "views" / f"{v['doi'].replace('/', '_')}__{v['view']}.gz").read_bytes()).decode("utf-8", "replace")
        c = cen.get(v["doi"].lower(), {})
        el = {k: c.get(k) for k in ("uri_labels", "uri_notices", "hub_projects", "name_labels", "name_notices") if c.get(k)}
        spans = sorted({m.start() for p in pats for m in p.finditer(body)})
        if spans:
            ex = [body[max(0, s - 160):s + 160].replace("\n", " ") for s in spans[:3]]
        else:
            ex = [body[max(0, m.start() - 40):m.start() + 260].replace("\n", " ") for m in re.finditer(r"rights|licen[cs]e|usageInfo", body, re.I)][:2] or [body[:300]]
        out.append(f"### h{i:03d} {v['doi']} | view={v['view']} | scorer={v['result']} | body {len(body)} chars\nDataCite element: {el}\n" +
                   "\n".join(f"  > {e}" for e in ex) + "\n")
    (RUN / "data" / "validation").mkdir(parents=True, exist_ok=True)
    (RUN / "data" / "validation" / "handcheck_sheet.txt").write_text("\n".join(out))
    import csv
    with open(RUN / "data" / "validation" / "handcheck_sample.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "doi", "view", "scorer"])
        for i, v in enumerate(pick):
            w.writerow([f"h{i:03d}", v["doi"], v["view"], v["result"]])
    print(len(pick), Counter((v["view"], v["result"]) for v in pick))


if __name__ == "__main__":
    main()
