"""Fetch the published versions of confirmed pairs from the PMC Open Access subset.

  1. DOI -> PMCID: NCBI PMC ID converter, 200 DOIs per request.
  2. PMCID -> XML: the PMC OA open-data bucket on AWS (anonymous), latest version: pmc-oa-opendata/PMC<id>.<v>/PMC<id>.<v>.xml
Only OA articles are available; pairs whose published version is not OA are excluded and counted.
Writes data/raw/published/PMC<id>.xml and data/raw/links/doi_pmcid.jsonl.
"""
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

RUN = Path(__file__).resolve().parents[1]
L, PUB = RUN / "data" / "raw" / "links", RUN / "data" / "raw" / "published"
UA = {"User-Agent": "research-lab preprint study (mailto:noreply@anthropic.com)"}
S3 = "https://pmc-oa-opendata.s3.amazonaws.com"


def idconv(dois):
    out = L / "doi_pmcid.jsonl"
    have = {json.loads(l)["doi"] for l in open(out)} if out.exists() else set()
    todo = [d for d in dois if d not in have]
    with open(out, "a") as fh:
        for i in range(0, len(todo), 200):
            batch = todo[i:i + 200]
            for k in range(6):
                try:
                    r = requests.get("https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/",
                                     params=dict(ids=",".join(batch), format="json", tool="research-lab",
                                                 email="noreply@anthropic.com"), headers=UA, timeout=60)
                    recs = r.json().get("records", []); break
                except Exception:
                    time.sleep(2 ** k); recs = []
            got = {(x.get("doi") or "").lower(): x.get("pmcid") for x in recs}
            for d in batch:
                fh.write(json.dumps(dict(doi=d, pmcid=got.get(d))) + "\n")
            time.sleep(0.4)
            if i % 4000 == 0:
                print("idconv", i, "/", len(todo), flush=True)


def fetch_one(pmcid):
    f = PUB / f"{pmcid}.xml"
    if f.exists() and f.stat().st_size > 0:
        return pmcid, "have"
    for k in range(5):
        try:
            r = requests.get(f"{S3}/?list-type=2&prefix={pmcid}.", headers=UA, timeout=60)
            keys = re.findall(r"<Key>([^<]+\.xml)</Key>", r.text)
            if not keys:
                return pmcid, "not_oa"
            key = sorted(keys, key=lambda x: int(re.search(r"\.(\d+)/", x).group(1)))[-1]
            x = requests.get(f"{S3}/{key}", headers=UA, timeout=120)
            x.raise_for_status()
            f.write_bytes(x.content)
            return pmcid, "ok"
        except Exception:
            time.sleep(2 ** k)
    return pmcid, "error"


def main():
    PUB.mkdir(parents=True, exist_ok=True)
    pairs = [json.loads(l) for l in open(RUN / "data" / "pairs_candidates.jsonl")]
    dois = sorted({p["published_doi"] for p in pairs if p["confirmed"]})
    idconv(dois)
    m = {json.loads(l)["doi"]: json.loads(l)["pmcid"] for l in open(L / "doi_pmcid.jsonl")}
    pmcids = sorted({m[d] for d in dois if m.get(d)})
    print("published DOIs", len(dois), "with PMCID", len(pmcids), flush=True)
    status = {}
    with ThreadPoolExecutor(16) as ex:
        for k, (pid, st) in enumerate(ex.map(fetch_one, pmcids)):
            status[pid] = st
            if k % 2000 == 0:
                print("fetch", k, "/", len(pmcids), flush=True)
    json.dump(status, open(L / "pmc_fetch_status.json", "w"))
    from collections import Counter
    print(Counter(status.values()))


if __name__ == "__main__":
    sys.exit(main())
