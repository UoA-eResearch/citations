"""Annual climate covariates for the ENSO adjustment: Nino 3.4 anomaly and the warm-pool edge.

These are forcing variables, not outcomes, so they are computed before plan.md is committed.

  nino34      annual mean of the monthly Nino 3.4 SST anomaly against a 1981-2010 monthly climatology
              (NOAA PSL nina34.data, which reports absolute SST from ERSST)
  nino34_lag  the same, one year earlier - skipjack respond to ENSO with a lag, and the PIPA exchange
              (Hanich et al. 2018; McDermott et al. 2019) turned on exactly this
  wpe         warm-pool edge: annual mean longitude of the eastern edge of the 29 C isotherm along the
              equator (ERSST v5, mean over 5S-5N), the classic index of where skipjack habitat sits
              (Lehodey et al. 1997)

Writes results/tables/indices.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

RUN = Path(__file__).resolve().parents[1]
IDX = RUN / "data" / "raw" / "indices"
OUT = RUN / "results" / "tables"
WPE_ISOTHERM = 29.0


def nino34():
    rows = []
    for line in open(IDX / "nina34.data"):
        parts = line.split()
        if len(parts) == 13 and parts[0].isdigit():
            y = int(parts[0])
            for m, v in enumerate(parts[1:], 1):
                v = float(v)
                if v > -90:                      # -99.99 marks missing months
                    rows.append((y, m, v))
    s = pd.DataFrame(rows, columns=["year", "month", "sst"])
    clim = s[(s.year >= 1981) & (s.year <= 2010)].groupby("month").sst.mean()
    s["anom"] = s.sst - s.month.map(clim)
    full = s.groupby("year").anom.agg(["mean", "count"])
    return full.loc[full["count"] == 12, "mean"]


def warm_pool_edge():
    """Eastern edge of the contiguous >=29 C region along the equator, scanning east from 140E.

    Read from NCEI's one-file-per-month ERSST v5 archive (ersst.v5.YYYYMM.nc, 1975-2023): PSL's
    single-file copy downloaded at ~45 KB/s and its OPeNDAP endpoint returned 429."""
    files = sorted((IDX / "ersst_monthly").glob("ersst.v5.*.nc"))
    # the monthly files do not agree on a calendar (some decode as 360-day, some as Gregorian), so the
    # date is taken from the filename and the file's own time axis is ignored
    rows, stamps = [], []
    for f in files:
        ym = f.stem.split(".")[-1]
        d = xr.open_dataset(f, decode_times=False)["sst"].squeeze(drop=True)
        band = d.sel(lat=slice(-5, 5)) if d.lat[0] < d.lat[-1] else d.sel(lat=slice(5, -5))
        rows.append(band.mean("lat"))
        stamps.append(pd.Timestamp(int(ym[:4]), int(ym[4:]), 15))
    sst = xr.concat(rows, dim="time").assign_coords(time=pd.DatetimeIndex(stamps))
    sst = sst.sel(lon=slice(130, 290))
    lon = sst.lon.values
    core = (lon >= 130) & (lon <= 200)
    edge = []
    for t in range(sst.sizes["time"]):
        row = sst.isel(time=t).values
        # Anchor on the warm-pool maximum, then walk east to where SST first drops below the isotherm,
        # interpolating the crossing. An earlier version anchored at a fixed 140E and lost every month
        # the pool sat west of it - 27 of 42 years - which was a definition bug, not a data gap.
        j = int(np.nanargmax(np.where(core, row, -np.inf)))
        if not np.isfinite(row[j]) or row[j] < WPE_ISOTHERM:
            edge.append(np.nan)                  # no water at the isotherm at all this month
            continue
        while j + 1 < lon.size and row[j + 1] >= WPE_ISOTHERM:
            j += 1
        if j + 1 < lon.size:
            x0, x1, y0, y1 = lon[j], lon[j + 1], row[j], row[j + 1]
            edge.append(x0 + (y0 - WPE_ISOTHERM) / (y0 - y1) * (x1 - x0))
        else:
            edge.append(lon[j])
    s = pd.Series(edge, index=pd.DatetimeIndex(sst.time.values))
    annual = s.groupby(s.index.year).agg(["mean", "count"])
    # a year needs at least 9 months with the isotherm present; cool months with no 29 C water are rare
    return annual.loc[annual["count"] >= 9, "mean"]


def main():
    n = nino34()
    w = warm_pool_edge()
    df = pd.DataFrame({"nino34": n, "wpe": w})
    df["nino34_lag"] = df["nino34"].shift(1)
    df = df.loc[1975:2023]
    df.index.name = "year"
    df.to_csv(OUT / "indices.csv")
    print(df.loc[1980:2021].describe().round(3))
    print("\ncorr nino34 vs wpe (1980-2021):", round(df.loc[1980:2021, ["nino34", "wpe"]].corr().iloc[0, 1], 3))


if __name__ == "__main__":
    sys.exit(main())
