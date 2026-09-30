#!/usr/bin/env python
"""Harvest citing papers and citation contexts for every FLoRA original (Semantic Scholar Graph API, public, no key).
One JSON file per original in data/raw/s2/ (resumable). Usage: fetch_contexts.py [SHARD NSHARD | rev]. Fields: contexts, intents, isInfluential, year,
publicationDate of each citing paper. The API caps offset + limit at 10,000 citing papers per original.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "data" / "raw" / "s2"
URL = "https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}/citations"
FIELDS = "contexts,intents,isInfluential,year,publicationDate,externalIds"
PAUSE = 3.0                                                               # the public API throttles faster clients


def get(session, url, params):
    for attempt in range(8):
        try:
            r = session.get(url, params=params, timeout=90)
        except requests.RequestException:
            time.sleep(5 * (attempt + 1))
            continue
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(min(60, 3 * 2 ** attempt))
            continue
        return r
    return r


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    f = pd.read_csv(RUN / "data" / "raw" / "flora_filtered.csv", low_memory=False)
    dois = sorted(f[(f.type == "replication") & f.doi_o.notna()].doi_o.str.strip().str.lower().unique())
    if len(sys.argv) > 1 and sys.argv[1] == "rev":                          # a second worker from the other end
        dois = dois[::-1]
    elif len(sys.argv) > 2:
        dois = dois[int(sys.argv[1])::int(sys.argv[2])]
    s = requests.Session()
    done = 0
    for doi in dois:
        path = OUT / (hashlib.sha1(doi.encode()).hexdigest()[:16] + ".json")
        if path.exists():
            continue
        rows, offset, status = [], 0, None
        while True:
            r = get(s, URL.format(doi=doi), {"fields": FIELDS, "limit": 1000, "offset": offset})
            status = r.status_code
            if status != 200:
                break
            js = r.json()
            rows += js.get("data", [])
            time.sleep(PAUSE)
            if js.get("next") is None or js["next"] + 1000 > 10000:
                break
            offset = js["next"]
        if status not in (200, 400, 404):                                  # throttled or server error: retry later
            time.sleep(30)
            continue
        path.write_text(json.dumps(dict(doi=doi, status=status, n=len(rows), data=rows)))
        done += 1
        if done % 50 == 0:
            print(time.strftime("%H:%M:%S"), done, "fetched", flush=True)
        time.sleep(PAUSE)
    print("finished", len(dois), flush=True)


if __name__ == "__main__":
    sys.exit(main())
