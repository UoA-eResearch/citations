"""Read CHIRP and CHIRPS pentad values at every gauge by HTTP range request (plan section 2). One request stream at a
time per product; resumable; a failed read is written as an error row, never as a value.
Usage: venv/bin/python code/extract_pentads.py chirp|chirps
Writes data/extract/<product>.csv: pentad (yyyy.mm.k), station, value (mm/pentad; NaN where the cell is masked)."""
import csv
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.env import Env

RUN = Path(__file__).resolve().parents[1]
URL = {"chirp": "https://data.chc.ucsb.edu/products/CHIRP/pentads/CHIRP.{y}.{m:02d}.{k}.tif",
       "chirps": "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_pentad/cogs/chirps-v2.0.{y}.{m:02d}.{k}.cog"}
ENV = dict(GDAL_HTTP_USERAGENT="research-lab rainfall study (mailto:noreply@anthropic.com)", GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
           CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.cog", GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="10", GDAL_HTTP_MULTIRANGE="YES",
           GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="YES", VSI_CACHE="FALSE")


def main(prod):
    st = pd.read_csv(RUN / "data" / "raw" / "ghcn" / "stations.csv")
    out = RUN / "data" / "extract" / f"{prod}.csv"; out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        done = set(pd.read_csv(out, usecols=["pentad", "status"]).query("status == 'ok'").pentad)
    pts = list(zip(st.lon, st.lat))
    with open(out, "a", newline="") as fh, Env(**ENV):
        w = csv.writer(fh)
        if out.stat().st_size == 0:
            w.writerow(["pentad", "status", "station", "value"])
        n = 0
        for y in range(1981, 2026):
            for m in range(1, 13):
                for k in range(1, 7):
                    pid = f"{y}.{m:02d}.{k}"
                    if pid in done:
                        continue
                    try:
                        with rasterio.open("/vsicurl/" + URL[prod].format(y=y, m=m, k=k)) as r:
                            vals = np.array([v[0] for v in r.sample(pts)], dtype=float)
                        vals[(vals <= -999) | ~np.isfinite(vals)] = np.nan
                        w.writerows([pid, "ok", s, "" if np.isnan(v) else round(float(v), 3)] for s, v in zip(st.id, vals))
                    except Exception as e:  # noqa: BLE001
                        w.writerow([pid, "error", "", str(e)[:120]])
                        time.sleep(30)
                    fh.flush(); n += 1
                    if n % 50 == 0:
                        print(prod, pid, n, flush=True)
    print(prod, "done", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
