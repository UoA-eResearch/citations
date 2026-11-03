"""G3 invariant (D4, review G3): the largest daily 6-hour maximum in each gauge water year equals the HIRDS lead's
annual 6-hour maximum (variant S3, the one rain_daily.py uses) for every gauge-year present in both.

  g3_invariant.py -> results/tables/g3_invariant.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
HL = RUN.parent / "auckland-nz-hirds-out-of-sample-exceedance-audit"
T = RUN / "results" / "tables"

R = pd.read_parquet(RUN / "data" / "rain_daily.parquet", columns=["file", "day", "d6"])
R["wy"] = np.where(R.day.dt.month >= 7, R.day.dt.year, R.day.dt.year - 1)
daily = R.groupby(["file", "wy"]).d6.max()
mx = pd.read_parquet(HL / "data" / "maxima.parquet")
mx = mx[(mx.d == 6) & (mx.variant == "S3")].set_index(["file", "wy"]).max_point
j = pd.concat([daily.rename("daily"), mx.rename("annual")], axis=1, join="inner").dropna()
diff = (j.daily - j.annual).abs()
out = {"gauge_years_compared": int(len(j)), "exact_within_0p001_mm": int((diff < 1e-3).sum()), "max_abs_diff_mm": round(float(diff.max()), 6)}
(T / "g3_invariant.json").write_text(json.dumps(out, indent=1) + "\n")
print(out)
