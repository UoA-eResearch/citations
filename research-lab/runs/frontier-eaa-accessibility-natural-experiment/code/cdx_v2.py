"""Wayback CDX discovery, gentle version (deviations D5; replaces cdx.py and cc_index.py). One HTTPS CDX query per
domain (all captures 2024-01..2026-04, status 200, text/html, one per day) for https://<domain>/ then
https://www.<domain>/, ONE request at a time with 2 s between requests. Picks the capture closest to the 15th of each
target month (cdx.py's rule). A failed query is recorded under "errors" and retried on the next run - never written
as absence. After 20 consecutive connection failures the job stops (the archive is blocking; do not push).
Sample: the D5 half-sample (data/frame/sample_d5.csv). Writes data/cdx/snapshots_v2.jsonl."""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

RUN = Path(__file__).resolve().parents[1]
TARGETS = ["202401", "202404", "202407", "202410", "202501", "202504", "202507", "202510", "202601", "202604"]
PRE, POST = TARGETS[:4], TARGETS[7:]
S = requests.Session(); S.headers["User-Agent"] = "research-lab accessibility study (mailto:noreply@anthropic.com)"
OUT = RUN / "data" / "cdx" / "snapshots_v2.jsonl"
FAILS = 0


def query(host):
    global FAILS
    url = ("https://web.archive.org/cdx/search/cdx?url=" + host + "/&from=202401&to=202604&output=json"
           "&filter=statuscode:200&filter=mimetype:text/html&fl=timestamp,original,digest&collapse=timestamp:8")
    for k in range(4):
        time.sleep(2)
        try:
            r = S.get(url, timeout=120)
            FAILS = 0
            if r.status_code == 200:
                rows = r.json() if r.text.strip() else []
                return "ok", (rows[1:] if rows and rows[0][0] == "timestamp" else rows)
            time.sleep(30 * (k + 1))                      # 429/5xx: back off hard
        except requests.exceptions.ConnectionError:
            FAILS += 1
            if FAILS >= 20:
                raise SystemExit("20 consecutive connection failures: the archive is refusing this host; stopping")
            time.sleep(30)
        except Exception:
            time.sleep(30)
    return "error", None


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
    dom = list(pd.read_csv(RUN / "data" / "frame" / "sample_d5.csv").domain)
    prev = {}
    if OUT.exists():
        for l in open(OUT):
            r = json.loads(l); prev[r["domain"]] = r
    with open(OUT, "a") as fh:
        for k, d in enumerate(dom):
            if d in prev and not prev[d].get("error"):
                continue
            rec = dict(domain=d, host=None, n_days=0, snapshots={}, error=False)
            for host in (d, "www." + d):
                st, rows = query(host)
                if st == "error":
                    rec["error"] = True; break
                if rows:
                    rec.update(host=host, n_days=len(rows), snapshots=pick(rows)); break
            fh.write(json.dumps(rec) + "\n"); fh.flush()
            if k % 100 == 0:
                print("cdx", k, "/", len(dom), flush=True)
    print("cdx done", flush=True)


def eligible():
    grp = pd.read_csv(RUN / "data" / "frame" / "sample_d5.csv").set_index("domain").group.to_dict()
    last = {}
    for l in open(OUT):
        r = json.loads(l); last[r["domain"]] = r
    rows = list(last.values())
    keep = [r for r in rows if not r["error"] and sum(t in r["snapshots"] for t in PRE) >= 2 and sum(t in r["snapshots"] for t in POST) >= 2]
    with open(RUN / "data" / "cdx" / "eligible.jsonl", "w") as fh:
        for r in keep:
            fh.write(json.dumps(r) + "\n")
    from collections import Counter
    print("eligible", len(keep), "of", len(rows), dict(Counter(grp[r["domain"]] for r in keep)), "; errors", sum(r["error"] for r in rows))


if __name__ == "__main__":
    sys.exit(eligible() if len(sys.argv) > 1 and sys.argv[1] == "eligible" else main())
