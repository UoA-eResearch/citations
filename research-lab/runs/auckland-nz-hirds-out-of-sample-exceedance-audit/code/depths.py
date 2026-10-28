"""HIRDS v4 depths at each gauge's coordinates (plan section 2 as changed by D1), from the HIRDS public API's point
report; and HIRDS's own site list, for the G1 coverage check.

  depths.py sites           -> data/hirds_sites.parquet
  depths.py points          -> data/hirds_depths.parquet (file, table, ari, aep, duration_h, mm)
"""
import http.client
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
KEEP = {"Rainfall depths (mm) :: Historical Data": "historical",
        "Depth standard error (mm) :: Historical Data": "historical_se",
        "Rainfall depths (mm) :: RCP4.5 for the period 2031-2050": "rcp45_2031_2050",
        "Rainfall depths (mm) :: RCP8.5 for the period 2031-2050": "rcp85_2031_2050"}
GRID = {"HawkesBay": 27200}            # NZ Map Grid (verified against HIRDS's own coordinates); every other server NZTM2000
HOURS = {"10m": 1 / 6, "20m": 1 / 3, "30m": 0.5, "1h": 1, "2h": 2, "6h": 6, "12h": 12, "24h": 24, "48h": 48, "72h": 72, "96h": 96, "120h": 120}


def call(method, path, body=None):
    hdr = {"x-apikey": Path("~/.config/niwa-hirds/key").expanduser().read_text().strip(),
           "Accept": "application/json", "Content-Type": "application/json"}
    for i in range(5):
        try:
            c = http.client.HTTPSConnection("api.niwa.co.nz", timeout=120)
            c.request(method, "/hirds" + path, body=json.dumps(body) if body else None, headers=hdr)
            r = c.getresponse()
            b = r.read().decode("utf-8", "replace")
            if r.status == 200:
                return json.loads(b)
            err = f"HTTP {r.status}"
        except Exception as e:
            err = type(e).__name__
        time.sleep(5 + 10 * i)
    raise RuntimeError(err)


def sites():
    d = pd.DataFrame(call("GET", "/sites"))
    d.to_parquet(D / "hirds_sites.parquet")
    print(len(d), "HIRDS sites")


def points():
    out_f = D / "hirds_depths.parquet"
    done = set(pd.read_parquet(out_f).file) if out_f.exists() else set()
    tf = {c: Transformer.from_crs(c, 4326, always_xy=True) for c in (2193, 27200)}
    skipped = []
    rows = [] if not done else [pd.read_parquet(out_f)]
    for f in sorted((D / "series").glob("*.npz")):
        if f.stem in done:
            continue
        z = np.load(f, allow_pickle=False)
        try:
            east, north = float(z["easting"]), float(z["northing"])
        except (KeyError, ValueError, TypeError):
            skipped.append((f.stem, "no coordinates")); continue
        lon, lat = tf[GRID.get(f.stem.split("__")[0], 2193)].transform(east, north)
        if not (-47.6 < lat < -34.0 and 166.0 < lon < 179.0):
            skipped.append((f.stem, "coordinates outside New Zealand")); continue
        assets = call("POST", "/report", {"latitude": round(lat, 6), "longitude": round(lon, 6), "site_name": "gauge", "idf": False})
        recs = []
        for a in assets:
            if a.get("title") in KEEP:
                tab = call("GET", a["url"])
                for row in tab["data"]:
                    for h, v in zip(tab["headers"][2:], row[2:]):
                        recs.append((f.stem, KEEP[a["title"]], float(row[0]), float(row[1]), HOURS[h], float(v)))
        rows.append(pd.DataFrame(recs, columns=["file", "table", "ari", "aep", "duration_h", "mm"]).assign(lat=lat, lon=lon))
        if len(rows) % 20 == 0:
            pd.concat(rows).to_parquet(out_f)
            print(time.strftime("%H:%M:%S"), len(rows), "gauges", flush=True)
        time.sleep(0.5)
    pd.concat(rows).to_parquet(out_f)
    pd.DataFrame(skipped, columns=["file", "reason"]).to_csv(D / "hirds_depths_skipped.csv", index=False)
    print("done", pd.concat(rows).file.nunique(), "gauges;", len(skipped), "skipped")


if __name__ == "__main__":
    {"sites": sites, "points": points}[sys.argv[1]]()
