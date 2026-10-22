"""STAC scene lists per atoll (plan section 2). Sentinel-2 L2A (Earth Search, 2016-01-01..2026-09-30) and Landsat 5/7/8
Collection 2 Level-2 (Planetary Computer, 1999-01-01..2023-12-31: the 1999-2015 epoch plus the 2016-2023 overlap
with Sentinel-2 for the sensor-step guard), catalogue cloud cover <= 80%.
Writes data/scenes/<atoll>_s2.parquet and <atoll>_ls.parquet, and results/tables/scenes_log.json."""
import json
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inventory import ATOLLS  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "data" / "scenes"
ES = "https://earth-search.aws.element84.com/v1/search"
PC = "https://planetarycomputer.microsoft.com/api/stac/v1/search"


def post(url, body):
    for t in range(6):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json", "User-Agent": "research-lab"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())
        except Exception as e:
            print("retry", t, repr(e)[:100], flush=True)
            time.sleep(10 * (t + 1))
    raise RuntimeError(url)


def search(url, body):
    items, nxt = [], body
    while True:
        d = post(url, nxt)
        items += d.get("features", [])
        link = next((l for l in d.get("links", []) if l.get("rel") == "next"), None)
        if not link:
            return items
        nxt = link.get("body") or {**body, "token": link.get("href", "").split("token=")[-1]}
        if link.get("body") and link.get("merge"):
            nxt = {**body, **link["body"]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    log = {}
    for name, (gid, (s, w, n, e)) in ATOLLS.items():
        if (OUT / f"{name}_s2.parquet").exists() and (OUT / f"{name}_ls.parquet").exists():
            continue
        bbox = [w, s, e, n]
        s2 = search(ES, {"collections": ["sentinel-2-l2a"], "bbox": bbox, "limit": 50,
                         "datetime": "2016-01-01T00:00:00Z/2026-09-30T23:59:59Z",
                         "query": {"eo:cloud_cover": {"lte": 80}}})
        rows = [{"id": f["id"], "datetime": f["properties"]["datetime"], "cloud": f["properties"].get("eo:cloud_cover"),
                 "tile": f["properties"].get("grid:code") or f["properties"].get("s2:mgrs_tile"),
                 "epsg": f["properties"].get("proj:epsg"), "green": f["assets"]["green"]["href"],
                 "swir16": f["assets"]["swir16"]["href"], "nir": f["assets"]["nir"]["href"],
                 "scl": f["assets"]["scl"]["href"],
                 "boa_offset_applied": f["properties"].get("earthsearch:boa_offset_applied"),
                 "baseline": f["properties"].get("s2:processing_baseline"),
                 **{f"{b}_scale": (f["assets"][b].get("raster:bands") or [{}])[0].get("scale", 1e-4) for b in ("green", "swir16", "nir")},
                 **{f"{b}_offset": (f["assets"][b].get("raster:bands") or [{}])[0].get("offset", 0.0) for b in ("green", "swir16", "nir")}}
                for f in s2 if all(k in f["assets"] for k in ("green", "swir16", "nir", "scl"))]
        pd.DataFrame(rows).to_parquet(OUT / f"{name}_s2.parquet", index=False)
        ls = search(PC, {"collections": ["landsat-c2-l2"], "bbox": bbox, "limit": 200,
                         "datetime": "1999-01-01T00:00:00Z/2023-12-31T23:59:59Z",
                         "query": {"eo:cloud_cover": {"lte": 80},
                                   "platform": {"in": ["landsat-5", "landsat-7", "landsat-8", "landsat-9"]}}})
        rl = [{"id": f["id"], "datetime": f["properties"]["datetime"], "cloud": f["properties"].get("eo:cloud_cover"),
               "platform": f["properties"].get("platform"), "epsg": f["properties"].get("proj:epsg"),
               "green": f["assets"]["green"]["href"], "swir16": f["assets"]["swir16"]["href"],
               "nir": f["assets"]["nir08"]["href"], "qa": f["assets"]["qa_pixel"]["href"],
               **{f"{b}_scale": (f["assets"][a].get("raster:bands") or [{}])[0].get("scale", 2.75e-5)
                  for b, a in (("green", "green"), ("swir16", "swir16"), ("nir", "nir08"))},
               **{f"{b}_offset": (f["assets"][a].get("raster:bands") or [{}])[0].get("offset", -0.2)
                  for b, a in (("green", "green"), ("swir16", "swir16"), ("nir", "nir08"))}} for f in ls
              if all(k in f["assets"] for k in ("green", "swir16", "nir08", "qa_pixel"))]
        pd.DataFrame(rl).to_parquet(OUT / f"{name}_ls.parquet", index=False)
        log[name] = {"s2": len(rows), "s2_items_without_bands": len(s2) - len(rows), "landsat": len(rl),
                     "landsat_by_platform": pd.Series([r["platform"] for r in rl]).value_counts().to_dict() if rl else {}}
        print(name, log[name], flush=True)
    json.dump(log, open(RUN / "results" / "tables" / "scenes_log.json", "w"), indent=1)


if __name__ == "__main__":
    main()
