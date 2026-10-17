"""Blind check of the rule-based sector labels (plan section 5).

  sample   60 sites labelled in scope and 60 labelled out of scope by sector.py, seeded, shuffled. Each is shown as its
           domain, page title and the first 1,200 characters of visible text from the snapshot sector.py used; the rule
           label is hidden. Writes data/validation/sector_sample.jsonl and sector_key.csv.
  The adjudicator records id,label (ecommerce / banking / transport / telecom / out / unclear),note in
  results/tables/sector_validation_raw.csv. `merge` joins the key; agree = 1 when the adjudicated label is in scope
  (any of the four sectors) for a rule in-scope site, or "out" for a rule out-of-scope site; "unclear" counts as
  disagreement. Writes results/tables/sector_validation.csv (read by did.py).
"""
import gzip
import json
import random
import re
import sys
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
V, TAB = RUN / "data" / "validation", RUN / "results" / "tables"
IN = {"ecommerce", "banking", "transport", "telecom"}


def visible(html):
    t = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    body = re.sub(r"<script.*?</script>|<style.*?</style>|<noscript.*?</noscript>", " ", html, flags=re.S | re.I)
    return (t.group(1).strip()[:200] if t else ""), re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()[:1200]


def sample():
    s = pd.read_csv(RUN / "data" / "sector.csv")
    rnd = random.Random(20261019)
    pick = [("in_scope", d) for d in rnd.sample(list(s[s.status == "in_scope"].domain), 60)] + \
           [("out_of_scope", d) for d in rnd.sample(list(s[s.status == "out_of_scope"].domain), 60)]
    rnd.shuffle(pick)
    first = s.set_index("domain")["first"].to_dict()
    V.mkdir(parents=True, exist_ok=True)
    keys = []
    with open(V / "sector_sample.jsonl", "w") as fh:
        for i, (st, d) in enumerate(pick):
            html = gzip.decompress((RUN / "data" / "html" / d / f"{first[d]}.html.gz").read_bytes()).decode("utf-8", "ignore")
            title, text = visible(html)
            fh.write(json.dumps(dict(id=f"s{i:03d}", domain=d, title=title, text=text), ensure_ascii=False) + "\n")
            keys.append(dict(id=f"s{i:03d}", domain=d, rule_status=st))
    pd.DataFrame(keys).to_csv(V / "sector_key.csv", index=False)
    print(len(keys), "sampled")


def merge():
    m = pd.read_csv(TAB / "sector_validation_raw.csv").merge(pd.read_csv(V / "sector_key.csv"), on="id")
    m["agree"] = [int((r.label in IN) if r.rule_status == "in_scope" else (r.label == "out")) for r in m.itertuples()]
    m.to_csv(TAB / "sector_validation.csv", index=False)
    print(m.groupby("rule_status").agree.agg(["mean", "count"]))


if __name__ == "__main__":
    {"sample": sample, "merge": merge}[sys.argv[1]]()
