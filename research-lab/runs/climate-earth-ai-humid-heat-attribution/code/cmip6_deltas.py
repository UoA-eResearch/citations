#!/usr/bin/env python
"""Warming signal per CMIP6 model (plan.md sec 3): event-month (May-September) climatology for 2014-2033 (historical 2014
+ SSP2-4.5 2015-2033) minus 1850-1900 (historical), r1i1p1f1, for ta (13 AIFS levels), tas and ts. Models: the first six
alphabetically with ta, hus, tas, huss and ts in both experiments (Amon).
Output: data/processed/deltas/{model}.nc, results/tables/cmip6_models.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "data" / "processed" / "deltas"
LEVELS_PA = [100000, 92500, 85000, 70000, 60000, 50000, 40000, 30000, 25000, 20000, 15000, 10000, 5000]
MONTHS = [5, 6, 7, 8, 9]


def open_store(z):
    return xr.open_zarr(z, storage_options=dict(token="anon"), consolidated=True, use_cftime=True)


def clim(da, y0, y1):
    sel = da.sel(time=(da["time.year"] >= y0) & (da["time.year"] <= y1))
    sel = sel.sel(time=sel["time.month"].isin(MONTHS))
    return sel.groupby("time.month").mean("time").load()


def main():
    cat = pd.read_csv("https://storage.googleapis.com/cmip6/cmip6-zarr-consolidated-stores.csv")
    q = cat[(cat.table_id == "Amon") & (cat.member_id == "r1i1p1f1") & cat.experiment_id.isin(["historical", "ssp245"])]
    need = {"ta", "hus", "tas", "huss", "ts"}
    ok = [m for m, g in q.groupby("source_id")
          if all(need <= set(g[g.experiment_id == e].variable_id) for e in ("historical", "ssp245"))]
    models = sorted(ok)[:6]
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for m in models:
        out = {}
        for v in ("ta", "tas", "ts"):
            st = {e: q[(q.source_id == m) & (q.experiment_id == e) & (q.variable_id == v)].sort_values("version").zstore.iloc[-1]
                  for e in ("historical", "ssp245")}
            h, s = open_store(st["historical"])[v], open_store(st["ssp245"])[v]
            if v == "ta":
                h = h.sel(plev=LEVELS_PA, method="nearest")
                s = s.sel(plev=LEVELS_PA, method="nearest")
            pi = clim(h, 1850, 1900)
            recent = xr.concat([h.sel(time=h["time.year"] == 2014), s.sel(time=(s["time.year"] >= 2015) & (s["time.year"] <= 2033))], "time")
            recent = recent.sel(time=recent["time.month"].isin(MONTHS)).groupby("time.month").mean("time").load()
            d = recent - pi
            if v == "ta":
                d = d.assign_coords(plev=LEVELS_PA)
            out[v] = d
            rows.append(dict(model=m, variable=v, historical=st["historical"], ssp245=st["ssp245"],
                             global_mean_delta_jja=float(d.sel(month=[6, 7, 8]).mean().values) if v != "ta" else np.nan))
        ds = xr.Dataset({k: v.drop_vars([c for c in v.coords if c not in ("month", "plev", "lat", "lon")], errors="ignore")
                         for k, v in out.items()})
        ds.to_netcdf(OUT / f"{m}.nc")
        print(m, "done; tas JJA mean delta (unweighted)", round(rows[-2]["global_mean_delta_jja"], 2), flush=True)
    pd.DataFrame(rows).to_csv(RUN / "results" / "tables" / "cmip6_models.csv", index=False)


if __name__ == "__main__":
    sys.exit(main())
