"""Download NZTA Crash Analysis System (CAS) records from the open FeatureServer (NZTM, EPSG:2193).

python cas_download.py pre   -> data/raw/cas_pre.parquet       crashFinancialYear <= 2024/2025 (open for design work)
python cas_download.py post  -> data/sealed/cas_post.json.gz   crashFinancialYear >= 2025/2026
The post file is written without being tabulated; its SHA-256 goes into data/sealed/cas_post.sha256 so the file used
after the preregistration is frozen can be shown to be the file downloaded before it. The record count is not printed.
"""
import gzip
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

SVC = "https://services.arcgis.com/CXBb7LAjgIIdcsPt/arcgis/rest/services/CAS_Data_Public/FeatureServer/0"
RUN = Path(__file__).resolve().parents[1]
PAGE = 2000
WHERE = {"pre": "crashFinancialYear <= '2024/2025'", "post": "crashFinancialYear >= '2025/2026'"}


def get(params, path="/query", tries=6):
    q = SVC + path + "?" + urllib.parse.urlencode(params)
    for k in range(tries):
        try:
            with urllib.request.urlopen(q, timeout=180) as r:
                d = json.load(r)
            if "error" in d:
                raise RuntimeError(d["error"])
            return d
        except Exception as e:  # noqa: BLE001
            if k == tries - 1:
                raise
            print("retry", k, e, file=sys.stderr)
            time.sleep(10 * (k + 1))


def fetch(which):
    where = WHERE[which]
    n = get({"where": where, "returnCountOnly": "true", "f": "json"})["count"]
    base = {"where": where, "outFields": "*", "orderByFields": "OBJECTID", "resultRecordCount": PAGE, "outSR": 2193,
            "returnGeometry": "true", "f": "json"}
    with ThreadPoolExecutor(4) as ex:
        feats = [f for p in ex.map(lambda o: get(base | {"resultOffset": o})["features"], range(0, n, PAGE)) for f in p]
    assert len(feats) == n and len({f["attributes"]["OBJECTID"] for f in feats}) == n, "incomplete download"
    meta = get({"f": "json"}, path="")["editingInfo"]
    return feats, meta


def main(which):
    feats, meta = fetch(which)
    if which == "pre":
        df = pd.DataFrame([f["attributes"] | {"X": f.get("geometry", {}).get("x"), "Y": f.get("geometry", {}).get("y")}
                           for f in feats])
        df.to_parquet(RUN / "data" / "raw" / "cas_pre.parquet", index=False)
        (RUN / "data" / "raw" / "cas_pre_meta.json").write_text(json.dumps(meta | {"count": len(df)}))
        print("pre:", len(df), "records;", df.crashFinancialYear.min(), "to", df.crashFinancialYear.max())
    else:
        out = RUN / "data" / "sealed"
        out.mkdir(parents=True, exist_ok=True)
        p = out / "cas_post.json.gz"
        with gzip.open(p, "wt") as fh:
            json.dump({"meta": meta, "features": feats}, fh)
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        (out / "cas_post.sha256").write_text(f"{h}  cas_post.json.gz\n")
        print("post: sealed, sha256", h)


if __name__ == "__main__":
    main(sys.argv[1])
