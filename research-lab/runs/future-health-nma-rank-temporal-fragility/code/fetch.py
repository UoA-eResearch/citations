"""Download the nmadb catalogue and every verified network's dataset from the public REDCap API at ISPM Bern.

The API URL and the public token are read at run time from the archived CRAN package source
(data/raw/nmadb_pkg/src/nmadb/R/publictoken.R), so the token is never copied into this repository.
Writes data/raw/catalog.csv, data/raw/datasets/<record>.xlsx, data/raw/fetch_log.jsonl and data/raw/SHA256SUMS.
Requests are sequential, 1.5 s apart; a failure is logged as an error, never as an absent dataset."""
import hashlib
import json
import re
import time
from pathlib import Path

import requests

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
SRC = (RAW / "nmadb_pkg" / "src" / "nmadb" / "R" / "publictoken.R").read_text()
URL = re.search(r'NMADBURL\s*=\s*"([^"]+)"', SRC).group(1)
TOKEN = re.search(r'PUBLICTOKEN\s*=\s*"([^"]+)"', SRC).group(1)
UA = {"User-Agent": "research-lab NMA ranking study (mailto:noreply@anthropic.com)"}


def post(data, tries=3):
    for k in range(tries):
        try:
            r = requests.post(URL, data=dict(token=TOKEN, **data), headers=UA, timeout=120)
            if r.status_code == 200:
                return r
            err = f"HTTP {r.status_code}"
        except requests.RequestException as e:
            err = str(e)[:200]
        time.sleep(30 * (k + 1))
    raise RuntimeError(err)


def main():
    cat = post(dict(content="record", format="csv", type="flat", rawOrLabel="label", rawOrLabelHeaders="label", csvDelimiter=";"))
    (RAW / "catalog.csv").write_bytes(cat.content)
    import pandas as pd
    c = pd.read_csv(RAW / "catalog.csv", sep=";", dtype=str)
    ver = c[c["Verified"].fillna("").str.lower() == "true"]["Record ID"].tolist()
    print(len(c), "records;", len(ver), "verified", flush=True)
    out = RAW / "datasets"; out.mkdir(exist_ok=True)
    log = open(RAW / "fetch_log.jsonl", "a")
    for k, rid in enumerate(ver):
        f = out / f"{rid}.xlsx"
        if f.exists() and f.stat().st_size > 0:
            continue
        rec = dict(record=rid)
        try:
            r = post(dict(content="file", action="export", record=rid, field="dataset", event="", returnFormat="json"))
            f.write_bytes(r.content); rec.update(bytes=len(r.content), ctype=r.headers.get("Content-Type", ""))
        except RuntimeError as e:
            rec["error"] = str(e)
        log.write(json.dumps(rec) + "\n"); log.flush()
        time.sleep(1.5)
        if k % 25 == 0:
            print("datasets", k, "/", len(ver), flush=True)
    with open(RAW / "SHA256SUMS", "w") as fh:
        for p in sorted([RAW / "catalog.csv"] + list(out.glob("*.xlsx"))):
            fh.write(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(RAW)}\n")
    print("fetch done", flush=True)


if __name__ == "__main__":
    main()
