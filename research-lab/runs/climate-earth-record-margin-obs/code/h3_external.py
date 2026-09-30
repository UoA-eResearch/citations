#!/usr/bin/env python
"""H3 with the preregistered external covariate (plan.md sec 3, 5): the local warming rate from Berkeley Earth's 1-degree
gridded land temperature (Complete_TAVG_LatLong1.nc; monthly anomalies), as the OLS trend of annual-mean anomalies
over 1981-2024 (the file ends in December 2024; deviations.md). Each station takes its grid cell's rate. The station
excess shattering frequency in 2003-2025 (observed minus stationary-null expectation, per eligible year) is regressed
on it; 95% interval from the two-way bootstrap (5x5-degree cells x 3-year blocks; deviations.md D6), with the
preregistered cell-only interval kept as lo_cell/hi_cell.
Output: results/tables/h3_external.csv, data/processed/station_rates.parquet
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from netCDF4 import Dataset

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import E2, YEARS, stage1  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
PROC, TAB = RUN / "data" / "processed", RUN / "results" / "tables"


def grid_rates():
    nc = Dataset(RUN / "data" / "raw" / "berkeley" / "Complete_TAVG_LatLong1.nc")
    t = np.asarray(nc.variables["time"][:], float)
    lat = np.asarray(nc.variables["latitude"][:], float)
    lon = np.asarray(nc.variables["longitude"][:], float)
    sel = (t >= 1981) & (t < 2025)
    T = np.ma.filled(nc.variables["temperature"][np.where(sel)[0], :, :].astype(float), np.nan)   # (months, lat, lon)
    yrs = np.floor(t[sel]).astype(int)
    uy = np.unique(yrs)
    A = np.stack([np.nanmean(T[yrs == y], axis=0) for y in uy])                                  # annual means
    x = uy - uy.mean()
    ok = np.isfinite(A).sum(0) >= 35
    Ac = np.where(np.isfinite(A), A - np.nanmean(A, axis=0), 0.0)
    w = np.isfinite(A).astype(float)
    xs = (x[:, None, None] * w)
    slope = (Ac * xs).sum(0) / np.maximum((xs * x[:, None, None]).sum(0), 1e-9)
    slope = np.where(ok, slope * 10, np.nan)                                                     # degC per decade
    return lat, lon, slope


def main():
    method, resample = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ("hinge", "permute")
    df = stage1("txx", 3, method, resample)
    lat, lon, slope = grid_rates()
    i = np.abs(lat[None, :] - df.lat.values[:, None]).argmin(1)
    j = np.abs(((lon[None, :] - df.lon.values[:, None] + 180) % 360) - 180).argmin(1)
    df["rate_berkeley"] = slope[i, j]
    df[["station", "lat", "lon", "rate_berkeley", "rate_c_per_decade"]].to_parquet(PROC / "station_rates.parquet", index=False)
    e = ((df.obs_E2_gt1 - df.stat_E2_gt1) / df.elig_E2).values
    x = df.rate_berkeley.values
    ok = np.isfinite(e) & np.isfinite(x)
    e, x, cells = e[ok], x[ok], df.cell.values[ok]
    slope_hat = float(np.polyfit(x, e, 1)[0])
    uc, ci = np.unique(cells, return_inverse=True)
    groups = [np.where(ci == k)[0] for k in range(len(uc))]
    rng = np.random.default_rng(2)
    bs = [np.polyfit(x[idx], e[idx], 1)[0] for idx in
          (np.concatenate([groups[k] for k in rng.integers(0, len(uc), len(uc))]) for _ in range(1000))]
    # D6: two-way interval - cells resampled as above AND 3-year blocks of 2003-2025 resampled, with each station's
    # excess recomputed from its per-year observed indicators and null expectations under the resampled years
    O = np.array(df.m_obs.tolist())[ok]
    el = np.isfinite(O)
    D = np.where(el, (np.where(el, O, 0) > 1) - np.nan_to_num(np.array(df.stat_py_gt1.tolist())[ok]), 0.0)
    e2 = np.where((YEARS >= E2[0]) & (YEARS <= E2[1]))[0]
    blocks = [e2[j:j + 3] for j in range(0, len(e2), 3)]
    bs2 = []
    for _ in range(1000):
        w = np.bincount(rng.integers(0, len(uc), len(uc)), minlength=len(uc))[ci].astype(float)
        v = np.zeros(len(YEARS))
        for j in rng.integers(0, len(blocks), len(blocks)):
            v[blocks[j]] += 1
        den = el.astype(float) @ v
        keep = (w > 0) & (den > 0)
        eb = (D @ v)[keep] / den[keep]
        bs2.append(np.polyfit(x[keep], eb, 1, w=np.sqrt(w[keep]))[0])
    out = dict(predictor="Berkeley Earth 1981-2024 trend (degC/decade)", slope=slope_hat, lo=float(np.percentile(bs2, 2.5)),
               hi=float(np.percentile(bs2, 97.5)), lo_cell=float(np.percentile(bs, 2.5)), hi_cell=float(np.percentile(bs, 97.5)),
               n_stations=int(ok.sum()), n_cells=len(uc),
               rate_mean=float(x.mean()), rate_sd=float(x.std()), corr_with_station_rate=float(np.corrcoef(
                   df.rate_berkeley.values[ok], df.rate_c_per_decade.values[ok])[0, 1]))
    out.update(method=method, resample=resample)
    pd.DataFrame([out]).to_csv(TAB / f"h3_external_{method}_{resample}.csv", index=False)
    print(out)


if __name__ == "__main__":
    sys.exit(main())
