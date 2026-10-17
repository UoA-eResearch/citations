"""Fetch every selected Common Crawl homepage record (deviations D4; replaces fetch.py): an HTTP range request for the
WARC record on data.commoncrawl.org, decompressed, WARC and HTTP headers stripped; the HTML body is stored gzipped
with its sha256. Common Crawl truncates bodies above 1 MiB (flagged). 6 concurrent, resumable. Writes
data/html/<domain>/<target>.html.gz and data/html/fetch_log.jsonl."""
import gzip
import hashlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

RUN = Path(__file__).resolve().parents[1]
S = requests.Session(); S.headers["User-Agent"] = "research-lab accessibility study (mailto:noreply@anthropic.com)"


def one(job):
    d, t, x = job
    f = RUN / "data" / "html" / d / f"{t}.html.gz"
    if f.exists():
        return dict(domain=d, target=t, status="have")
    a, n = int(x["offset"]), int(x["length"])
    for k in range(5):
        try:
            r = S.get("https://data.commoncrawl.org/" + x["filename"], headers={"Range": f"bytes={a}-{a + n - 1}"}, timeout=120)
            if r.status_code in (200, 206):
                raw = gzip.decompress(r.content)
                i = raw.find(b"\r\n\r\n"); j = raw.find(b"\r\n\r\n", i + 4)
                body = raw[j + 4:]
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_bytes(gzip.compress(body))
                return dict(domain=d, target=t, status="ok", bytes=len(body), sha256=hashlib.sha256(body).hexdigest(),
                            timestamp=x["timestamp"], url=x["url"], truncated=b"WARC-Truncated" in raw[:j])
            time.sleep(5 * (k + 1))
        except Exception as e:
            err = str(e)[:100]; time.sleep(5 * (k + 1))
    return dict(domain=d, target=t, status="error")


def main():
    rows = [json.loads(l) for l in open(RUN / "data" / "cdx" / "eligible.jsonl")]
    jobs = [(r["domain"], t, x) for r in rows for t, x in r["snapshots"].items()]
    log = RUN / "data" / "html" / "fetch_log.jsonl"; log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a") as fh, ThreadPoolExecutor(6) as ex:
        for k, r in enumerate(ex.map(one, jobs)):
            fh.write(json.dumps(r) + "\n"); fh.flush()
            if k % 2000 == 0:
                print("fetch", k, "/", len(jobs), flush=True)
    print("fetch done", flush=True)


if __name__ == "__main__":
    sys.exit(main())
