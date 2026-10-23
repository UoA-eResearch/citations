"""Reviewer check: LINZ collection metadata (vertical datum, dates, density) and source-tile grid alignment (prompt item 1).
Fetches only the small STAC collection JSONs and one COG header per collection."""
import json
import urllib.request
from pathlib import Path

import rasterio

OUT = Path("/mnt/citations/research-lab/runs/auckland-nz-kauri-dieback-multitemporal-lidar/review/reviewer_checks")
BUCKET = "https://nz-elevation.s3.ap-southeast-2.amazonaws.com/"
COLL = {"e1_dsm": "auckland/auckland-north_2016-2018/dsm_1m/2193/", "e1_dem": "auckland/auckland-north_2016-2018/dem_1m/2193/",
        "e2p1_dsm": "auckland/auckland-part-1_2024/dsm_1m/2193/", "e2p1_dem": "auckland/auckland-part-1_2024/dem_1m/2193/",
        "e2p2_dsm": "auckland/auckland-part-2_2024/dsm_1m/2193/", "e2p2_dem": "auckland/auckland-part-2_2024/dem_1m/2193/"}
res = {}
for k, p in COLL.items():
    c = json.load(urllib.request.urlopen(BUCKET + p + "collection.json", timeout=60))
    keep = {kk: c.get(kk) for kk in ("title", "description", "linz:geospatial_category", "linz:lifecycle")}
    keep["extent_temporal"] = c.get("extent", {}).get("temporal")
    keep["n_items"] = sum(1 for l in c["links"] if l["rel"] == "item")
    summ = c.get("summaries") or {}
    keep["summaries"] = {kk: summ[kk] for kk in summ if any(s in kk.lower() for s in ("datum", "vertical", "density", "gsd", "crs", "epsg", "created", "updated"))}
    for kk, v in c.items():
        if "datum" in kk.lower() or "vertical" in kk.lower():
            keep[kk] = v
    # one COG header
    first = next(l for l in c["links"] if l["rel"] == "item")
    it = json.load(urllib.request.urlopen(BUCKET + p + first["href"].lstrip("./"), timeout=60))
    keep["item_props"] = {kk: v for kk, v in it.get("properties", {}).items()}
    href = next(iter(it["assets"].values()))["href"]
    href = href if href.startswith("http") else BUCKET + p + href.lstrip("./")
    with rasterio.open(href) as ds:
        keep["tile"] = {"transform_gdal": ds.transform.to_gdal(), "crs": str(ds.crs), "dtype": ds.dtypes[0], "nodata": ds.nodata,
                        "size": [ds.width, ds.height], "tags": {kk: v for kk, v in ds.tags().items() if len(str(v)) < 200}}
    res[k] = keep
json.dump(res, open(OUT / "linz_meta.json", "w"), indent=1, default=str)
for k, v in res.items():
    print(k, "|", v["title"], "|", v["extent_temporal"], "| items", v["n_items"])
    print("   summaries:", v["summaries"])
    print("   item props:", {kk: vv for kk, vv in v["item_props"].items() if kk not in ("proj:bbox",)})
    print("   tile:", v["tile"]["transform_gdal"], v["tile"]["crs"], v["tile"]["dtype"], v["tile"]["nodata"], v["tile"]["tags"])
