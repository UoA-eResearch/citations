"""The fixed-footprint check defined in deviations.md D6, before this ran.

A centroid or share computed over the cells fished in each year moves whenever the fished area changes.
Here only cells fished (>= 5 days) in at least FRAC of the 42 years count, every year, so no cell enters
or leaves. Primary FRAC = 0.8; sensitivity 0.5.

Writes results/tables/footprint.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
from model_targets import DOMAIN, cell_area_km2, eez_union, fractional_mask  # noqa: E402
from observed import MIN_DAYS, SCHOOLS, centres  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
RAW, TAB = RUN / "data" / "raw", RUN / "results" / "tables"
YEARS = np.arange(1980, 2022)


def main():
    idx = pd.read_csv(TAB / "indices.csv", index_col=0)
    tau = json.load(open(TAB / "primary.json"))["tau_pp"]
    ds = xr.open_dataset(RAW / "WCPFC_S_PUBLIC_BY_1x1_MM.nc").sel(time=slice("1980", "2021"))
    lat_c, lon_c = centres(ds.latitude.values, ds.longitude.values, "sw")
    in_d = ((lat_c >= DOMAIN["lat"][0]) & (lat_c <= DOMAIN["lat"][1]))[:, None] & \
           ((lon_c >= DOMAIN["lon"][0]) & (lon_c <= DOMAIN["lon"][1]))[None, :]
    skj = sum(ds[f"skj_c_{s}"].fillna(0) for s in SCHOOLS).groupby("time.year").sum("time")
    days = ds["days"].fillna(0).groupby("time.year").sum("time")
    fished = (days >= MIN_DAYS).values & in_d[None, :, :]
    freq = fished.mean(axis=0)
    area = cell_area_km2(lat_c, 1.0, 1.0)[:, None] * np.ones((1, lon_c.size))
    shape, _ = eez_union()
    frac = fractional_mask(lat_c, lon_c, shape, 1.0)
    lon2 = np.broadcast_to(lon_c[None, :], in_d.shape)
    out = {}
    for f_min in (0.8, 0.5):
        foot = (freq >= f_min) & in_d
        cpue = np.where(days.values > 0, skj.values / np.where(days.values > 0, days.values, 1), 0.0)
        cpue = np.where(days.values >= MIN_DAYS, cpue, np.nan)       # a footprint cell with too little effort that year
        w = area[None] * cpue * foot[None]                             # contributes nothing that year
        cen = np.nansum(w * lon2[None], axis=(1, 2)) / np.nansum(w, axis=(1, 2))
        dens = np.nansum(w * frac[None], axis=(1, 2)) / np.nansum(w, axis=(1, 2))
        cover = np.mean(np.isfinite(cpue[:, foot]), axis=1)            # share of footprint cells with data each year
        c_t = A.trend_ci(cen / 100, YEARS, idx)                         # trend_ci reports x100, so this is deg/yr
        d_t = A.trend_ci(dens, YEARS, idx)
        d_t["verdict_vs_tau"] = A.verdict_h1(d_t["lo"], d_t["hi"], tau)
        lon_f = lon_c[np.where(foot.any(0))[0]]
        # D7, post hoc: a fixed cell set is only fixed in years when its cells are actually fished, so refit
        # on the years with >= 80% of footprint cells covered
        good = YEARS[cover >= 0.8]
        c_cov = A.trend_ci(cen[cover >= 0.8] / 100, good, idx)
        c_cov["years"] = [int(good.min()), int(good.max())]
        c_cov["n"] = int(len(good))
        low = {int(y): float(c) for y, c in zip(YEARS, cover) if c < 0.8}
        out[f"min_frac_{f_min}"] = dict(
            centroid_trend_covered_years=c_cov, low_coverage_years=low,
            n_cells=int(foot.sum()), lon_range=[float(lon_f.min()), float(lon_f.max())],
            eez_area_share=float((area * frac * foot).sum() / (area * foot).sum()),
            mean_yearly_coverage=float(cover.mean()), min_yearly_coverage=float(cover.min()),
            centroid_trend_deg_per_yr=c_t, density_share_trend_pp=d_t,
            centroid_series={int(y): float(v) for y, v in zip(YEARS, cen)})
        print(f"footprint >= {int(f_min*100)}% of years: {foot.sum()} cells, lon {lon_f.min():.1f}-{lon_f.max():.1f}E, "
              f"coverage mean {cover.mean():.2f} (min {cover.min():.2f})")
        print(f"   centroid trend  {c_t['point']:+.3f} deg/yr [{c_t['lo']:+.3f}, {c_t['hi']:+.3f}]")
        print(f"   density share   {d_t['point']:+.3f} pp/yr  [{d_t['lo']:+.3f}, {d_t['hi']:+.3f}]  vs tau -> {d_t['verdict_vs_tau']}")
    json.dump(out, open(TAB / "footprint.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    sys.exit(main())
