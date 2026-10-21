"""The corpus snapshot (plan section 1): the PMC OA bucket's metadata/ inventory of 2026-10-21, reduced to the latest
version listed for each PMCID. Writes data/snapshot/latest_versions.parquet (pmcid, version, key, last_modified).
"""
import concurrent.futures as cf
import csv
import gzip
import io
import json
import re
import urllib.request
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "data" / "snapshot"
BUCKET = "https://pmc-oa-opendata.s3.amazonaws.com/"
INV = "inventory-reports/pmc-oa-opendata/metadata/2026-10-21T01-00Z/manifest.json"
KEY = re.compile(r"^metadata/(PMC\d+)\.(\d+)\.json$")


def fetch(key):
    p = OUT / "inventory" / key.rsplit("/", 1)[-1]
    if not p.exists():
        with urllib.request.urlopen(BUCKET + key, timeout=600) as r:
            p.write_bytes(r.read())
    return p


def main():
    (OUT / "inventory").mkdir(parents=True, exist_ok=True)
    man = json.loads(urllib.request.urlopen(BUCKET + INV, timeout=120).read())
    json.dump(man, open(OUT / "inventory" / "manifest.json", "w"), indent=1)
    with cf.ThreadPoolExecutor(16) as ex:
        paths = list(ex.map(fetch, [f["key"] for f in man["files"]]))
    rows = []
    for p in paths:
        for rec in csv.reader(io.TextIOWrapper(gzip.open(p), encoding="utf-8")):
            m = KEY.match(rec[1])
            if m:
                rows.append((m.group(1), int(m.group(2)), rec[1], rec[2]))
    d = pd.DataFrame(rows, columns=["pmcid", "version", "key", "last_modified"])
    n_all = len(d)
    d = d.sort_values(["pmcid", "version"]).groupby("pmcid").tail(1).reset_index(drop=True)
    d.to_parquet(OUT / "latest_versions.parquet", index=False)
    log = {"inventory": INV, "files": len(man["files"]), "metadata_objects": n_all, "pmcids": len(d),
           "version_counts": d.version.value_counts().sort_index().head(10).to_dict()}
    json.dump(log, open(RUN / "results" / "tables" / "snapshot_log.json", "w"), indent=1, default=str)
    print(log)


if __name__ == "__main__":
    main()
