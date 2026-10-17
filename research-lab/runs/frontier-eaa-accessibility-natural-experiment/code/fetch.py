"""Fetch the unrewritten archived HTML (id_ replay) of every selected snapshot; store gzipped with its sha256.
Gentle (deviations D5): one request at a time, 2 s apart, hard backoff on 429/5xx, stop after 20 consecutive
connection failures (the archive is refusing this host); resumable, failures logged as errors and retried next run. Writes data/html/<domain>/<target>.html.gz and
data/html/fetch_log.jsonl."""
import gzip
import hashlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

RUN = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "research-lab accessibility study (mailto:noreply@anthropic.com)"}


FAILS = [0]


def one(job):
    d, t, s = job
    f = RUN / "data" / "html" / d / f"{t}.html.gz"
    if f.exists():
        return dict(domain=d, target=t, status="have")
    url = f"https://web.archive.org/web/{s['timestamp']}id_/{s['original']}"
    err = ""
    for k in range(4):
        time.sleep(2)
        try:
            r = requests.get(url, headers=UA, timeout=120)
            FAILS[0] = 0
            if r.status_code in (429, 503, 502, 504):
                time.sleep(60 * (k + 1)); continue
            if r.status_code != 200:
                return dict(domain=d, target=t, status=f"http_{r.status_code}")
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(gzip.compress(r.content))
            return dict(domain=d, target=t, status="ok", bytes=len(r.content), sha256=hashlib.sha256(r.content).hexdigest(),
                        timestamp=s["timestamp"])
        except requests.exceptions.ConnectionError as e:
            FAILS[0] += 1; err = str(e)[:100]
            if FAILS[0] >= 20:
                raise SystemExit("20 consecutive connection failures: the archive is refusing this host; stopping")
            time.sleep(30)
        except Exception as e:
            err = str(e)[:100]; time.sleep(30)
    return dict(domain=d, target=t, status="error", error=err)


def main():
    rows = [json.loads(l) for l in open(RUN / "data" / "cdx" / "eligible.jsonl")]
    jobs = [(r["domain"], t, s) for r in rows for t, s in r["snapshots"].items()]
    log = RUN / "data" / "html" / "fetch_log.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a") as fh:
        for k, r in enumerate(map(one, jobs)):
            fh.write(json.dumps(r) + "\n"); fh.flush()
            if k % 1000 == 0:
                print("fetch", k, "/", len(jobs), flush=True)
    print("fetch done")


if __name__ == "__main__":
    sys.exit(main())
