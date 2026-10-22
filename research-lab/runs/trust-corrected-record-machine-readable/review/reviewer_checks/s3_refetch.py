"""Reviewer check (network, a few objects): refetch the sidecar, XML and text of four cohort documents from the PMC
bucket today, compare SHA-256 with the study's frozen table, and compare the objects' Last-Modified with the
inventory's. Run: venv/bin/python -I s3_refetch.py
"""
import gzip
import hashlib
import json
import urllib.request
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
HTTP = "https://pmc-oa-opendata.s3.amazonaws.com/"


def main():
    sha = pd.read_csv(RUN / "results" / "tables" / "snapshot_files_sha256.csv.gz").set_index("file").sha256
    c = pd.read_parquet(RUN / "data" / "cohort.parquet")
    snap = pd.read_parquet(RUN / "data" / "snapshot" / "latest_versions.parquet").set_index("pmcid")
    ov = pd.read_csv(RUN / "results" / "overlay" / "retraction_overlay.csv.gz")
    unm = ov[(ov.stratum == "primary") & ov.in_snapshot & ~ov.own_marker].pmcid.tolist()
    v2 = c[(c.stratum == "primary") & c.in_snapshot & (c.version == 2)].pmcid.tolist()
    picks = ["PMC10002988", unm[0], unm[len(unm) // 2], v2[0]]
    for pmcid in picks:
        key = c.set_index("pmcid").key[pmcid]
        print(f"\n{pmcid}  inventory key {key}  inventory last_modified {snap.last_modified[pmcid]}  retraction {c.set_index('pmcid').date[pmcid]}")
        meta = json.loads((RUN / "data" / "files" / f"{pmcid}.json").read_bytes())
        for ext, url in (("json", key), ("xml", meta["xml_url"].replace("s3://pmc-oa-opendata/", "").split("?")[0]),
                         ("txt", meta["text_url"].replace("s3://pmc-oa-opendata/", "").split("?")[0])):
            with urllib.request.urlopen(HTTP + url, timeout=120) as r:
                b = r.read()
                lm, etag = r.headers.get("Last-Modified"), r.headers.get("ETag")
            h = hashlib.sha256(b).hexdigest()
            same = h == sha.get(f"{pmcid}.{ext}")
            print(f"   {ext}: Last-Modified {lm}; sha256 {'SAME' if same else 'CHANGED'} as frozen table; size {len(b)}")
            if ext == "json":
                print("      is_retracted now:", json.loads(b).get("is_retracted"), "| frozen:", meta.get("is_retracted"))


if __name__ == "__main__":
    main()
