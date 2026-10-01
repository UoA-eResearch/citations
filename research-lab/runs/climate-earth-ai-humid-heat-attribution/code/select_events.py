#!/usr/bin/env python
"""Event selection by rule (plan.md sec 2), from ERA5 only: per region, the two days in May-September 2023-2025 (in
different years) with the highest regional maximum of 2 m wet-bulb temperature at 06, 12 and 18 UTC.
Output: results/tables/event_candidates.csv (daily regional max TW), results/tables/events.csv (the six events)
"""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wetbulb import wetbulb  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
ARCO = "gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3"
REGIONS = {"South Asia": (22, 32, 68, 88), "Persian Gulf": (23, 31, 47, 57), "US Gulf coast": (27, 33, 263, 279)}


def open_arco():
    return xr.open_zarr(ARCO, storage_options=dict(token="anon"), chunks=None)


def region_max_tw(ds, when):
    out = {}
    f = {v: ds[v].sel(time=when).values for v in ("2m_temperature", "2m_dewpoint_temperature", "surface_pressure")}
    lat, lon = ds.latitude.values, ds.longitude.values
    for name, (la0, la1, lo0, lo1) in REGIONS.items():
        i = (lat >= la0) & (lat <= la1)
        j = (lon >= lo0) & (lon <= lo1)
        tw = wetbulb(f["2m_temperature"][np.ix_(i, j)], f["2m_dewpoint_temperature"][np.ix_(i, j)], f["surface_pressure"][np.ix_(i, j)])
        k = np.unravel_index(np.nanargmax(tw), tw.shape)
        out[name] = (float(tw[k]) - 273.15, float(lat[i][k[0]]), float(lon[j][k[1]]))
    return when, out


def main():
    ds = open_arco()
    times = [pd.Timestamp(f"{d:%Y-%m-%d} {h:02d}:00") for y in (2023, 2024, 2025)
             for d in pd.date_range(f"{y}-05-01", f"{y}-09-30") for h in (6, 12, 18)]
    with ThreadPoolExecutor(16) as ex:
        res = list(ex.map(lambda t: region_max_tw(ds, t), times))
    rows = [dict(time=t, region=r, tw_max=v[0], lat=v[1], lon=v[2]) for t, out in res for r, v in out.items()]
    d = pd.DataFrame(rows)
    d["date"] = d.time.dt.normalize()
    daily = d.loc[d.groupby(["region", "date"]).tw_max.idxmax()].reset_index(drop=True)
    TAB.mkdir(parents=True, exist_ok=True)
    daily.to_csv(TAB / "event_candidates.csv", index=False)
    ev = []
    for r, g in daily.groupby("region"):
        g = g.sort_values("tw_max", ascending=False)
        first = g.iloc[0]
        second = g[g.date.dt.year != first.date.year].iloc[0]
        ev += [first, second]
    ev = pd.DataFrame(ev)[["region", "date", "time", "tw_max", "lat", "lon"]]
    ev.to_csv(TAB / "events.csv", index=False)
    print(ev.round(2).to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
