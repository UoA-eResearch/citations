"""Parse the saved Medsafe search pages (plan section 4) into data/medsafe_products.csv and
data/medsafe_applications.csv, one row per table row, with the substance the search was for."""
import gzip
import html as H
import json
import re
import sys
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
M = RUN / "data" / "raw" / "medsafe"
PROD = ["product", "ingredients", "sponsor", "status", "approval_date", "notification_date"]
APPL = ["application_date", "type", "change", "status", "payment_received", "product", "ingredients", "sponsor", "priority"]


def rows(page):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", page, flags=re.S)
    tables = [tb for tb in re.findall(r"<table.*?</table>", t, re.S) if "ProductDetail" in tb]
    out = []
    for tb in tables:
        for tr in re.findall(r"<tr.*?</tr>", tb, re.S):
            cells = [H.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", td))).strip()
                     for td in re.findall(r"<td.*?</td>", tr, re.S)]
            pid = re.search(r"Product_id=(\d+)", tr)
            if cells and pid:
                out.append((cells, pid.group(1)))
    return out


def main():
    log = [json.loads(l) for l in open(M / "log.jsonl")]
    slug = lambda s: re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    P, A = [], []
    for r in log:
        f = M / "html" / r["type"] / f"{slug(r['substance'])}.html.gz"
        if not f.exists():
            continue
        for cells, pid in rows(gzip.decompress(f.read_bytes()).decode()):
            cols = PROD if r["type"] == "Product" else APPL
            d = dict(zip(cols, cells + [""] * (len(cols) - len(cells))))
            d.update(substance=r["substance"], term=r["term"], product_id=pid)
            (P if r["type"] == "Product" else A).append(d)
    pd.DataFrame(P).to_csv(RUN / "data" / "medsafe_products.csv", index=False)
    pd.DataFrame(A).to_csv(RUN / "data" / "medsafe_applications.csv", index=False)
    print(len(P), "product rows;", len(A), "application rows")


if __name__ == "__main__":
    sys.exit(main())
