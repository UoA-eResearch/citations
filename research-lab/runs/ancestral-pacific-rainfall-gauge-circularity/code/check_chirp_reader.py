"""Check the direct CHIRP reader (code/extract_pentads.py chirp_read) against values GDAL read for the same pentads
(data/extract/chirp.csv rows written by rasterio's sample()). Prints the number of compared cells and mismatches."""
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.env import Env

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_pentads as ep  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def main(n=12):
    st = pd.read_csv(RUN / "data" / "raw" / "ghcn" / "stations.csv")
    g = pd.read_csv(RUN / "data" / "extract" / "chirp.csv", nrows=257 * len(st) + 10).query("status == 'ok'")
    pents = sorted(random.Random(1).sample(sorted(g.pentad.unique()), n))
    pts = list(zip(st.lon, st.lat))
    with Env(**ep.ENV), rasterio.open("/vsicurl/" + ep.URL["chirp"].format(y=1981, m=1, k=1)) as r:
        rc = [r.index(x, y) for x, y in pts]
    cells = mism = 0
    for p in pents:
        y, m, k = p.split(".")
        v = ep.chirp_read(ep.URL["chirp"].format(y=int(y), m=int(m), k=int(k)), [a for a, _ in rc], [b for _, b in rc])
        v[(v <= -999) | ~np.isfinite(v)] = np.nan
        ref = g[g.pentad == p].set_index("station").value.reindex(st.id).to_numpy(float)
        new = np.round(v, 3)
        same = (np.isnan(ref) & np.isnan(new)) | (np.abs(ref - new) < 1e-6)
        cells += len(ref); mism += int((~same).sum())
        print(p, int((~same).sum()), "mismatches of", len(ref), flush=True)
    print("TOTAL", cells, "cells,", mism, "mismatches")


if __name__ == "__main__":
    main()
