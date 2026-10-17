"""Find each sampled domain's homepage in Common Crawl, one crawl per target quarter-month (deviations D4; replaces
cdx.py after the Internet Archive blocked this host). One index request per domain per crawl: a domain match
filtered to the homepage URL (http/https, with or without www, trailing slash optional), status 200. The first
matching capture is used. Staged to save requests:
  1. the three post crawls; a domain needs >= 2 of 3 to continue;
  2. the four pre crawls; it needs >= 2 of 4 to be eligible;
  3. the anticipation and transition crawls, for eligible domains only.
A failed request (after retries) is recorded under "errors", never as absence, and is retried on the next run.
3 concurrent requests; transient 400/5xx errors (about a third of requests, 17 Oct 2026) are retried
up to 10 times with short linear backoff; resumable. Writes data/cdx/cc_snapshots.jsonl."""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests

RUN = Path(__file__).resolve().parents[1]
CRAWL = {"202401": "CC-MAIN-2024-10", "202404": "CC-MAIN-2024-18", "202407": "CC-MAIN-2024-30", "202410": "CC-MAIN-2024-42",
         "202501": "CC-MAIN-2025-05", "202504": "CC-MAIN-2025-18", "202507": "CC-MAIN-2025-30",
         "202510": "CC-MAIN-2025-43", "202601": "CC-MAIN-2026-04", "202604": "CC-MAIN-2026-17"}
PRE, POST, MID = ["202401", "202404", "202407", "202410"], ["202510", "202601", "202604"], ["202501", "202504", "202507"]
S = requests.Session(); S.headers["User-Agent"] = "research-lab accessibility study (mailto:noreply@anthropic.com)"
OUT = RUN / "data" / "cdx" / "cc_snapshots.jsonl"


def query(domain, target):
    rx = "^https?://(www\\.)?" + domain.replace(".", "\\.") + "/?$"
    url = (f"https://index.commoncrawl.org/{CRAWL[target]}-index?url={domain}&matchType=domain"
           f"&filter={quote('~url:' + rx)}&filter=status:200&output=json&limit=5"
           "&fl=url,timestamp,status,mime,mime-detected,length,offset,filename")
    for k in range(10):
        try:
            r = S.get(url, timeout=120)
            if r.status_code == 404 and "No Captures" in r.text:
                return "absent", None
            if r.status_code == 200:
                rows = [json.loads(l) for l in r.text.splitlines() if l.strip()]
                rows = [x for x in rows if "html" in (x.get("mime-detected") or x.get("mime") or "")]
                return ("found", rows[0]) if rows else ("absent", None)
            # the index server is overloaded: about a third of requests fail with a transient 400/502/503/504
            time.sleep(2 + 2 * k)
        except Exception:
            time.sleep(2 + 2 * k)
    return "error", None


def stage(rec, targets):
    for t in targets:
        if t in rec["snapshots"] or t in rec["absent"]:
            continue
        st, x = query(rec["domain"], t)
        if st == "found":
            rec["snapshots"][t] = x; rec["errors"].pop(t, None)
        elif st == "absent":
            rec["absent"].append(t); rec["errors"].pop(t, None)
        else:
            rec["errors"][t] = rec["errors"].get(t, 0) + 1
        time.sleep(0.5)


def one(rec):
    stage(rec, POST)
    if sum(t in rec["snapshots"] for t in POST) >= 2 or any(t in rec["errors"] for t in POST):
        stage(rec, PRE)
        if sum(t in rec["snapshots"] for t in PRE) >= 2:
            stage(rec, MID)
    return rec


def main():
    dom = list(pd.read_csv(RUN / "data" / "frame" / "sample.csv").domain)
    prev = {}
    if OUT.exists():
        for l in open(OUT):
            r = json.loads(l); prev[r["domain"]] = r
    recs = [prev.get(d, dict(domain=d, snapshots={}, absent=[], errors={})) for d in dom]
    todo = [r for r in recs if r["domain"] not in prev or r["errors"]]
    done = [r for r in recs if r["domain"] in prev and not r["errors"]]
    tmp = OUT.with_suffix(".tmp")
    with open(tmp, "w") as fh:
        for r in done:
            fh.write(json.dumps(r) + "\n")
        with ThreadPoolExecutor(3) as ex:
            for k, r in enumerate(ex.map(one, todo)):
                fh.write(json.dumps(r) + "\n"); fh.flush()
                if k % 100 == 0:
                    print("cc", k, "/", len(todo), flush=True)
    tmp.replace(OUT)
    print("cc done; domains with errors:", sum(bool(json.loads(l)["errors"]) for l in open(OUT)), flush=True)


def eligible():
    grp = pd.read_csv(RUN / "data" / "frame" / "sample.csv").set_index("domain").group.to_dict()
    rows = [json.loads(l) for l in open(OUT)]
    keep = [r for r in rows if sum(t in r["snapshots"] for t in PRE) >= 2 and sum(t in r["snapshots"] for t in POST) >= 2]
    with open(RUN / "data" / "cdx" / "eligible.jsonl", "w") as fh:
        for r in keep:
            fh.write(json.dumps(r) + "\n")
    from collections import Counter
    print("eligible", len(keep), "of", len(rows), dict(Counter(grp[r["domain"]] for r in keep)),
          "; with unresolved errors:", sum(bool(r["errors"]) for r in rows))


if __name__ == "__main__":
    sys.exit(eligible() if len(sys.argv) > 1 and sys.argv[1] == "eligible" else main())
