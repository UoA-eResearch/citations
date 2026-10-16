"""Reproduce Bell et al. (2021) using the paper's own equation (1). Added after review (deviations D8).

The paper is internally inconsistent about its baseline. Fig. 3's caption says the 2050 change is relative to
2009-2018; Methods equation (1) defines it as the mean, over the 120 months of 2011-2020, of B(t + 33 years) /
B(t) - 1 - a month-by-month ratio against a 2011-2020 base. model_targets.py used annual-mean windows
(2044-2053 against 2011-2018, and against a spliced 2009-2018); this computes equation (1) itself.

Writes results/tables/bell_eq1.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_targets import ESMS, SPECIES, open_run  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB, PROC = RUN / "results" / "tables", RUN / "data" / "processed"
LAG_MONTHS = 33 * 12


def eez_monthly(sp, esm, w):
    da = open_run(sp, esm)
    W = xr.DataArray(w, dims=("lat", "lon"), coords={"lat": da.lat, "lon": da.lon})
    s = (da.fillna(0) * W).sum(("lat", "lon")).to_series()
    s.index = pd.PeriodIndex(s.index, freq="M")
    return s


def main():
    m = xr.open_dataset(PROC / "eez_mask_2deg.nc")
    w = (m.eez_frac * m.cell_area_km2).values
    out = {"definition": "mean over the 120 months t of 2011-2020 of B(t+33y)/B(t) - 1, B = biomass in the 12 EEZ areas"}
    per = {}
    for esm in ESMS:
        series = {sp: eez_monthly(sp, esm, w) for sp in SPECIES}
        tot = sum(series.values())
        def eq1(s):
            base = s.loc[pd.Period("2011-01", "M"):pd.Period("2020-12", "M")]
            fut = s.reindex([p + LAG_MONTHS for p in base.index]).to_numpy()
            return float(np.mean(fut / base.to_numpy() - 1))
        per[esm] = dict(three_species=eq1(tot), **{sp: eq1(s) for sp, s in series.items()})
    vals = np.array([v["three_species"] for v in per.values()])
    out["per_esm"] = per
    out["three_species_mean"] = float(vals.mean())
    out["three_species_range"] = [float(vals.min()), float(vals.max())]
    out["per_species_mean"] = {sp: float(np.mean([per[e][sp] for e in ESMS])) for sp in SPECIES}
    out["published"] = dict(mean=-0.13, range=[-0.20, -0.05])
    json.dump(out, open(TAB / "bell_eq1.json", "w"), indent=1)
    print(f"Bell eq. (1): {100*out['three_species_mean']:.1f}% (range {100*vals.min():.1f} to {100*vals.max():.1f})")
    print("  per ESM:", {e: round(100 * v["three_species"], 1) for e, v in per.items()})
    print("  per species (4-ESM mean):", {k: round(100 * v, 1) for k, v in out["per_species_mean"].items()})


if __name__ == "__main__":
    sys.exit(main())
