"""Crawl every PBS Medicine Status Website record (plan section 6): /medicinestatus/document/<id> for id 1..2200,
one request at a time, 1.2 s apart, resumable. Parses drug name, submission type, PBAC meeting, and the "Medicine
listed on the PBS" date. Writes data/raw/pbs/msw/<id>.html.gz and data/msw.csv."""
import gzip
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data" / "raw" / "pbs" / "msw"
S = requests.Session(); S.headers["User-Agent"] = "research-lab medicines-access study (mailto:noreply@anthropic.com)"
FIELDS = {"brand": "Brand name:", "sponsor": "Submission sponsor:", "subtype": "PBAC Submission type:",
          "meeting": "Submission received for:", "pbac_held": "PBAC meeting:", "outcome": "PBAC outcome published:",
          "listed": "Medicine listed on the PBS:", "status": "Status:", "current": "Information current as at:"}


def text(h):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S)
    t = re.sub(r"<[^>]+>", "|", t); t = re.sub(r"\s+", " ", t)
    return re.sub(r"(\s*\|\s*)+", " | ", t)


def parse(i, h):
    t = text(h)
    m = re.search(r"Medicine Status \| News \| Contact \| Medicine Status \| News \| Contact \| ([^|]+) \|", t)
    if not m:
        return None
    r = dict(id=i, drug=m.group(1).strip())
    for k, lab in FIELDS.items():
        mm = re.search(re.escape(lab) + r" \| ([^|]+)", t)
        r[k] = mm.group(1).strip() if mm else None
    d = re.search(r"(\d{2}/\d{2}/\d{4})", r["listed"] or "")
    r["listed_date"] = d.group(1) if d else None
    return r


def main():
    D.mkdir(parents=True, exist_ok=True)
    for i in range(1, 2201):
        f = D / f"{i}.html.gz"
        if f.exists():
            continue
        for k in range(3):
            try:
                r = S.get(f"https://www.pbs.gov.au/medicinestatus/document/{i}", timeout=60)
                f.write_bytes(gzip.compress(r.content if r.status_code == 200 else b""))
                break
            except Exception:
                time.sleep(10 * (k + 1))
        time.sleep(1.2)
        if i % 200 == 0:
            print("msw", i, flush=True)
    rows = []
    for f in sorted(D.glob("*.html.gz"), key=lambda p: int(p.name.split(".")[0])):
        h = gzip.decompress(f.read_bytes()).decode("utf-8", "ignore")
        if h:
            r = parse(int(f.name.split(".")[0]), h)
            if r:
                rows.append(r)
    pd.DataFrame(rows).to_csv(RUN / "data" / "msw.csv", index=False)
    print("msw done", len(rows), "records", flush=True)


if __name__ == "__main__":
    sys.exit(main())
