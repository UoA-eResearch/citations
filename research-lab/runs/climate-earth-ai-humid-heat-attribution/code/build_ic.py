#!/usr/bin/env python
"""Factual AIFS initial conditions (plan.md sec 3): ERA5 (ARCO) at 00 UTC on event day - L (L = 2, 4, 6 days) and
18 UTC the day before, regridded 0.25 deg -> N320 with earthkit-regrid; geopotential height is already geopotential in
ERA5 (m2 s-2). Also writes the N320 latitudes / longitudes (by regridding the coordinate fields).
Output: data/processed/ic/{event_id}_L{L}.npz (float32, fields x 2 times x 542080), data/processed/n320_latlon.npz,
data/processed/era5_event/{event_id}.npz (event-day 2t, 2d, sp, lsm at 06, 12, 18 UTC on N320)
"""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import earthkit.regrid as ekr
import numpy as np
import pandas as pd
import xarray as xr

RUN = Path(__file__).resolve().parents[1]
PROC, TAB = RUN / "data" / "processed", RUN / "results" / "tables"
ARCO = "gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3"
SFC = {"10u": "10m_u_component_of_wind", "10v": "10m_v_component_of_wind", "2d": "2m_dewpoint_temperature",
       "2t": "2m_temperature", "msl": "mean_sea_level_pressure", "skt": "skin_temperature", "sp": "surface_pressure",
       "tcw": "total_column_water", "lsm": "land_sea_mask", "z": "geopotential_at_surface",
       "slor": "slope_of_sub_gridscale_orography", "sdor": "standard_deviation_of_orography",
       "swvl1": "volumetric_soil_water_layer_1", "swvl2": "volumetric_soil_water_layer_2",
       "stl1": "soil_temperature_level_1", "stl2": "soil_temperature_level_2"}
PL = {"z": "geopotential", "t": "temperature", "u": "u_component_of_wind", "v": "v_component_of_wind",
      "w": "vertical_velocity", "q": "specific_humidity"}
LEVELS = [1000, 925, 850, 700, 600, 500, 400, 300, 250, 200, 150, 100, 50]
LEADS = (2, 4, 6)


def regrid(x):
    return ekr.interpolate(np.asarray(x, dtype=np.float64), {"grid": (0.25, 0.25)}, {"grid": "N320"}).astype(np.float32)


def latlon(ds):
    path = PROC / "n320_latlon.npz"
    if path.exists():
        return
    lat2 = np.repeat(ds.latitude.values[:, None], ds.longitude.size, axis=1)
    lon = np.radians(ds.longitude.values)[None, :].repeat(ds.latitude.size, axis=0)
    la = regrid(lat2)
    lo = np.degrees(np.arctan2(regrid(np.sin(lon)), regrid(np.cos(lon)))) % 360
    np.savez(path, lat=la, lon=lo)


def fetch(ds, when):
    jobs = [(k, v, None) for k, v in SFC.items()] + [(f"{p}_{lev}", v, lev) for p, v in PL.items() for lev in LEVELS]

    def one(job):
        name, var, lev = job
        da = ds[var].sel(time=when) if lev is None else ds[var].sel(time=when, level=lev)
        if "time" in da.dims:
            da = da.isel(time=0)
        return name, regrid(da.values)
    with ThreadPoolExecutor(12) as ex:
        return dict(ex.map(one, jobs))


def main():
    ds = xr.open_zarr(ARCO, storage_options=dict(token="anon"), chunks=None)
    latlon(ds)
    ev = pd.read_csv(TAB / "events.csv", parse_dates=["date", "time"])
    ev["event_id"] = [f"E{i + 1}" for i in range(len(ev))]
    ev.to_csv(TAB / "events.csv", index=False)
    (PROC / "ic").mkdir(parents=True, exist_ok=True)
    (PROC / "era5_event").mkdir(parents=True, exist_ok=True)
    for _, e in ev.iterrows():                                          # event-day truth for V1 and the static estimate
        path = PROC / "era5_event" / f"{e.event_id}.npz"
        if not path.exists():
            arrs = {}
            for h in (6, 12, 18):
                when = e.date + pd.Timedelta(hours=h)
                for k in ("2t", "2d", "sp", "lsm"):
                    da = ds[SFC[k]].sel(time=when)
                    arrs[f"{k}_{h:02d}"] = regrid(da.values)
            np.savez(path, **arrs)
    for _, e in ev.iterrows():
        for L in LEADS:
            path = PROC / "ic" / f"{e.event_id}_L{L}.npz"
            if path.exists():
                continue
            t0 = e.date - pd.Timedelta(days=L)
            a, b = fetch(ds, t0 - pd.Timedelta(hours=6)), fetch(ds, t0)
            np.savez(path, t0=str(t0), **{k: np.stack([a[k], b[k]]) for k in a})
            print(e.event_id, e.region, "L", L, "t0", t0, flush=True)


if __name__ == "__main__":
    sys.exit(main())
