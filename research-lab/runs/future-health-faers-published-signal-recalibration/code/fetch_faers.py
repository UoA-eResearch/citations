"""Download the quarterly FAERS ASCII extracts (legacy AERS 2004Q1-2012Q3; FAERS 2012Q4 onward) from fis.fda.gov.
Three connections at most (the host serves ~70 KB/s per connection to this machine), resumable, each zip verified;
a failed quarter is logged in data/raw/faers/fetch_log.jsonl and retried on the next run, never treated as empty."""
import json
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "data" / "raw" / "faers"
UA = {"User-Agent": "research-lab pharmacovigilance study (mailto:noreply@anthropic.com)"}


def quarters():
    for y in range(2004, 2027):
        for q in range(1, 5):
            if (y, q) > (2026, 2):
                return
            yield y, q, ("aers" if (y, q) <= (2012, 3) else "faers")


def one(job):
    y, q, kind = job
    f = OUT / f"{kind}_ascii_{y}q{q}.zip"
    try:
        if f.exists():
            zipfile.ZipFile(f).testzip(); return dict(file=f.name, status="have")
    except Exception:
        f.unlink()
    url = f"https://fis.fda.gov/content/Exports/{kind}_ascii_{y}q{q}.zip"
    for k in range(4):
        try:
            with requests.get(url, headers=UA, stream=True, timeout=600) as r:
                if r.status_code != 200:
                    err = f"HTTP {r.status_code}"; time.sleep(30 * (k + 1)); continue
                tmp = f.with_suffix(".part")
                with open(tmp, "wb") as fh:
                    for chunk in r.iter_content(1 << 20):
                        fh.write(chunk)
            zipfile.ZipFile(tmp).testzip(); tmp.rename(f)
            return dict(file=f.name, status="ok", bytes=f.stat().st_size)
        except Exception as e:  # noqa: BLE001
            err = str(e)[:150]; time.sleep(30 * (k + 1))
    return dict(file=f.name, status="error", error=err)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(3) as ex, open(OUT / "fetch_log.jsonl", "a") as log:
        for r in ex.map(one, list(quarters())):
            log.write(json.dumps(r) + "\n"); log.flush(); print(r, flush=True)


if __name__ == "__main__":
    main()
