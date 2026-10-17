"""Find one archived homepage snapshot per domain per target quarter-month (plan section 4).

Targets: 2024-01, 2024-04, 2024-07, 2024-10 (pre), 2025-01, 2025-04 (anticipation), 2025-07 (transition; the Act
applies from 2025-06-28), 2025-10, 2026-01, 2026-04 (post). For each target month, the 200-status text/html capture of the homepage
(https://<domain>/ or https://www.<domain>/, whichever the index holds) closest to the 15th within that month.
Polite: 4 concurrent requests, exponential backoff on 429/5xx, resumable. Writes data/cdx/snapshots.jsonl.
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import requests

RUN = Path(__file__).resolve().parents[1]
TARGETS = ["202401", "202404", "202407", "202410", "202501", "202504", "202507", "202510", "202601", "202604"]
UA = {"User-Agent": "research-lab accessibility study (mailto:noreply@anthropic.com)"}


def query(domain):
    for host in (domain, "www." + domain):
        url = ("http://web.archive.org/cdx/search/cdx?url=" + host + "/&from=202401&to=202604&output=json"
               "&filter=statuscode:200&filter=mimetype:text/html&fl=timestamp,original,digest")
        for k in range(6):
            try:
                r = requests.get(url, headers=UA, timeout=120)
                if r.status_code in (429, 503, 502, 504):
                    time.sleep(min(300, 10 * 2 ** k)); continue
                rows = r.json() if r.text.strip() else []
                rows = rows[1:] if rows and rows[0][0] == "timestamp" else rows
                if rows:
                    return host, rows
                break
            except Exception:
                time.sleep(min(300, 5 * 2 ** k))
    return None, []


def pick(rows):
    out = {}
    for t in TARGETS:
        mid = datetime.strptime(t + "15", "%Y%m%d")
        cand = [r for r in rows if r[0].startswith(t)]
        if cand:
            best = min(cand, key=lambda r: abs((datetime.strptime(r[0][:8], "%Y%m%d") - mid).days))
            out[t] = dict(timestamp=best[0], original=best[1], digest=best[2])
    return out


def main():
    import csv
    dom = [r["domain"] for r in csv.DictReader(open(RUN / "data" / "frame" / "sample.csv"))]
    outp = RUN / "data" / "cdx" / "snapshots.jsonl"
    outp.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(l)["domain"] for l in open(outp)} if outp.exists() else set()
    todo = [d for d in dom if d not in done]

    def one(d):
        host, rows = query(d)
        return dict(domain=d, host=host, n_captures=len(rows), snapshots=pick(rows))
    with open(outp, "a") as fh, ThreadPoolExecutor(4) as ex:
        for k, r in enumerate(ex.map(one, todo)):
            fh.write(json.dumps(r) + "\n"); fh.flush()
            if k % 200 == 0:
                print("cdx", k, "/", len(todo), flush=True)
    print("cdx done")


PRE = ["202401", "202404", "202407", "202410"]
POST = ["202510", "202601", "202604"]


def eligible():
    """Coverage rule (plan section 4): >= 2 of the 4 pre targets and >= 2 of the 3 post targets. Writes
    data/cdx/eligible.jsonl and prints counts by group."""
    import csv
    grp = {r["domain"]: r["group"] for r in csv.DictReader(open(RUN / "data" / "frame" / "sample.csv"))}
    rows = [json.loads(l) for l in open(RUN / "data" / "cdx" / "snapshots.jsonl")]
    keep = [r for r in rows if sum(t in r["snapshots"] for t in PRE) >= 2 and sum(t in r["snapshots"] for t in POST) >= 2]
    with open(RUN / "data" / "cdx" / "eligible.jsonl", "w") as fh:
        for r in keep:
            fh.write(json.dumps(r) + "\n")
    from collections import Counter
    print("eligible", len(keep), "of", len(rows), dict(Counter(grp[r["domain"]] for r in keep)))


if __name__ == "__main__":
    sys.exit(eligible() if len(sys.argv) > 1 and sys.argv[1] == "eligible" else main())
