"""Download every record of Auckland Council's 'Ruru ObsKauri Tiaki (Valid and Public)' layer (attributes and NZTM
point geometry), paged at the service's 2,000-record limit. Writes data/raw/obskauri.parquet and its sha256."""
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
URL = ("https://services1.arcgis.com/n4yPwebTjJCmXB6W/arcgis/rest/services/"
       "Ruru_ObsKauri_Tiaki_(Valid_and_Public)/FeatureServer/0/query")


def main():
    rows, offset = [], 0
    while True:
        q = {"where": "1=1", "outFields": "*", "outSR": 2193, "f": "json", "orderByFields": "OBJECTID",
             "resultOffset": offset, "resultRecordCount": 2000}
        r = json.load(urllib.request.urlopen(URL + "?" + urllib.parse.urlencode(q), timeout=120))
        feats = r.get("features", [])
        for f in feats:
            a = dict(f["attributes"])
            g = f.get("geometry") or {}
            a["x"], a["y"] = g.get("x"), g.get("y")
            rows.append(a)
        offset += len(feats)
        if not feats or not r.get("exceededTransferLimit"):
            break
    d = pd.DataFrame(rows)
    out = RUN / "data" / "raw" / "obskauri.parquet"
    d.to_parquet(out, index=False)
    print(len(d), "records;", hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
