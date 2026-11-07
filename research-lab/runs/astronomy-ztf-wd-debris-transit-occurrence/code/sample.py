"""Sample (plan section 0): Gentile Fusillo et al. (2021) white dwarfs with P_WD > 0.75, G < 20, dec > -28 deg and
parallax > 2 mas (within 500 pc). Positions are propagated to epoch 2019.0 (the middle of ZTF) with the Gaia proper
motions.

  sample.py -> data/sample.parquet, results/tables/coverage.json (stage "catalogue")
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.io import fits

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402

COLS = ["WDJ_name", "source_id", "ra", "dec", "pmra", "pmdec", "ref_epoch", "parallax", "phot_g_mean_mag", "bp_rp", "Pwd"]
with fits.open(D / "raw_cat" / "gaiaedr3_wd_main.fits.gz", memmap=False) as h:
    t = h[1].data
    d = pd.DataFrame({c: np.asarray(t[c]).astype(np.float64) if c not in ("WDJ_name", "source_id") else np.asarray(t[c]).astype(str) for c in COLS})
    d["source_id"] = np.asarray(t["source_id"]).astype("int64")      # D1: read as int64; the float64 cast rounded 19-digit IDs
n0 = len(d)
c = Coverage("catalogue", T / "coverage.json")
s1 = d[d.Pwd > 0.75]; s2 = s1[s1.phot_g_mean_mag < 20]; s3 = s2[s2.dec > -28]; s4 = s3[s3.parallax > 2]
c.add_counts(ok=len(s4), drops={"P_WD <= 0.75": n0 - len(s1), "G >= 20": len(s1) - len(s2), "dec <= -28": len(s2) - len(s3),
                                "parallax <= 2 mas (beyond 500 pc)": len(s3) - len(s4)})
c.save()
s = s4.copy()
dt = 2019.0 - s.ref_epoch
s["ra2019"] = s.ra + dt * s.pmra.fillna(0) / 3.6e6 / np.cos(np.radians(s.dec))
s["dec2019"] = s.dec + dt * s.pmdec.fillna(0) / 3.6e6
s.to_parquet(D / "sample.parquet")
print(len(s), "sample white dwarfs; G quantiles", s.phot_g_mean_mag.quantile([.1, .5, .9]).round(2).tolist())
