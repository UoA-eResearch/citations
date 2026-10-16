"""The fixed-footprint check, done properly (deviations D8). Added after review.

D6 asked whether the density centroid moves east on a fixed set of grounds, and read "it vanishes" as proof
the eastward move was fleet expansion. It never asked what SEAPODYM's projected shift would look like on
those same grounds. On the narrow 80% footprint (86 cells, 141.5-159.5E) the model's own projected shift
registers as only about +0.01 deg/yr against +0.07 domain-wide, so a null there could not tell "no shift"
from "the projected shift". This reports the whole grid of footprint thresholds and coverage rules, each
paired with the model's projected 2011-2050 centroid trend computed on the same cells.

Writes results/tables/footprint_grid.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
from model_targets import DOMAIN, ESMS, cell_area_km2, eez_union, fractional_mask, open_run  # noqa: E402
from observed import MIN_DAYS, SCHOOLS, centres  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
RAW, TAB = RUN / "data" / "raw", RUN / "results" / "tables"
YEARS = np.arange(1980, 2022)
THRESHOLDS = (0.5, 0.6, 0.7, 0.8, 0.9)
COVERAGE = (0.6, 0.8, 0.9)


def model_centroid_on(da, pts):
    """Biomass-weighted centroid longitude using only the 2-degree cells that contain footprint cells."""
    lat, lon = da.lat.values, da.lon.values
    w = np.zeros((lat.size, lon.size))
    for la, lo in pts:
        w[np.argmin(np.abs(lat - la)), np.argmin(np.abs(lon - lo))] += 1
    w *= cell_area_km2(lat, 2.0, 2.0)[:, None]
    W = xr.DataArray(w, dims=("lat", "lon"), coords={"lat": da.lat, "lon": da.lon})
    L = xr.DataArray(np.broadcast_to(lon[None, :], w.shape), dims=("lat", "lon"), coords={"lat": da.lat, "lon": da.lon})
    b = da.fillna(0) * W
    return ((b * L).sum(("lat", "lon")) / b.sum(("lat", "lon"))).groupby("time.year").mean().to_series()


def main():
    idx = pd.read_csv(TAB / "indices.csv", index_col=0)
    ds = xr.open_dataset(RAW / "WCPFC_S_PUBLIC_BY_1x1_MM.nc").sel(time=slice("1980", "2021"))
    lat_c, lon_c = centres(ds.latitude.values, ds.longitude.values, "sw")
    in_d = ((lat_c >= DOMAIN["lat"][0]) & (lat_c <= DOMAIN["lat"][1]))[:, None] & \
           ((lon_c >= DOMAIN["lon"][0]) & (lon_c <= DOMAIN["lon"][1]))[None, :]
    skj = sum(ds[f"skj_c_{s}"].fillna(0) for s in SCHOOLS).groupby("time.year").sum("time").values
    days = ds["days"].fillna(0).groupby("time.year").sum("time").values
    fished = (days >= MIN_DAYS) & in_d[None]
    freq = fished.mean(0)
    area = cell_area_km2(lat_c, 1.0, 1.0)[:, None] * np.ones((1, lon_c.size))
    frac = fractional_mask(lat_c, lon_c, eez_union()[0], 1.0)
    lon2 = np.broadcast_to(lon_c[None, :], in_d.shape)
    cpue = np.where(days >= MIN_DAYS, skj / np.where(days > 0, days, 1), np.nan)
    runs = {e: open_run("skj", e) for e in ESMS}
    rows = []
    for th in THRESHOLDS:
        foot = (freq >= th) & in_d
        pts = [(lat_c[i], lon_c[j]) for i, j in zip(*np.where(foot))]
        mod = {e: float(np.polyfit(*(lambda s: (s.index, s.values))(model_centroid_on(r, pts).loc[2011:2050]), 1)[0])
               for e, r in runs.items()}
        w = area[None] * cpue * foot[None]
        cen = np.nansum(w * lon2[None], axis=(1, 2)) / np.nansum(w, axis=(1, 2))
        cover = np.mean(np.isfinite(cpue[:, foot]), axis=1)
        lon_f = lon_c[np.where(foot.any(0))[0]]
        base = dict(threshold=th, n_cells=int(foot.sum()), lon_range=[float(lon_f.min()), float(lon_f.max())],
                    eez_area_share=float((area * frac * foot).sum() / (area * foot).sum()),
                    model_proj_trend_in_footprint=float(np.mean(list(mod.values()))), model_per_esm=mod)
        for cv in COVERAGE:
            good = YEARS[cover >= cv]
            if len(good) < 12:
                rows.append(dict(base, coverage_rule=cv, n_years=int(len(good)), point=None, lo=None, hi=None))
                continue
            t = A.trend_ci(cen[cover >= cv] / 100, good, idx)
            rows.append(dict(base, coverage_rule=cv, n_years=int(len(good)), years=[int(good.min()), int(good.max())],
                             point=t["point"], lo=t["lo"], hi=t["hi"]))
    json.dump(dict(domain_wide_model_proj_trend=0.0704, grid=rows), open(TAB / "footprint_grid.json", "w"), indent=1)
    print(f"{'foot':>5s} {'cells':>5s} {'lon range':>14s} {'model proj':>10s} {'cov':>4s} {'years':>11s} {'observed trend':>26s}")
    for r in rows:
        tr = "too few years" if r["point"] is None else f"{r['point']:+.3f} [{r['lo']:+.3f}, {r['hi']:+.3f}]"
        yr = "" if r["point"] is None else f"{r['years'][0]}-{r['years'][1]}"
        print(f"{r['threshold']:>5.1f} {r['n_cells']:>5d} {r['lon_range'][0]:>6.1f}-{r['lon_range'][1]:<6.1f} "
              f"{r['model_proj_trend_in_footprint']:>+10.4f} {r['coverage_rule']:>4.1f} {yr:>11s} {tr:>26s}")


if __name__ == "__main__":
    sys.exit(main())
