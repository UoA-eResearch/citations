"""Exposure per site (plan section 2) and the frozen terciles. Reads no outcome.

E(site, R, def) = newly bare 10 m pixels / 10 m pixels valid in both windows, over the 20 m land cells of the site's
contributing land (def = route) or of all land within R km (def = radius, D1 sensitivity).
Primary: route, R = 5 km. Terciles of the primary E across the 56 sites (ties broken by site id).

Writes results/tables/exposure.csv (one row per site; E for every R and def; the primary tercile) and
results/tables/exposure_summary.json.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

RUN = Path(__file__).resolve().parents[1]
RADII = (2, 5, 10)


def main():
    with rasterio.open(RUN / "data" / "bare20.tif") as ds:
        bare, valid = ds.read(1).ravel().astype(np.int64), ds.read(2).ravel().astype(np.int64)
    with rasterio.open(RUN / "data" / "dem20.tif") as ds:
        filled = ds.read(2).ravel() > 0
    z = np.load(RUN / "data" / "contrib.npz")
    s = pd.read_csv(RUN / "results" / "tables" / "sites.csv")
    rows = []
    for site in s.site_id:
        row = {"site_id": site}
        for d in ("route", "radius"):
            for R in RADII:
                c = z[f"{site}|{d}|{R}"]
                v = valid[c].sum()
                row[f"E_{d}_{R}"] = float(bare[c].sum() / v) if v else np.nan
                row[f"valid_share_{d}_{R}"] = float(v / (4 * len(c))) if len(c) else np.nan
                row[f"land_km2_{d}_{R}"] = len(c) * 4e-4
                if d == "route":
                    row[f"contour_filled_share_{R}"] = float(filled[c].mean()) if len(c) else np.nan
        rows.append(row)
    x = pd.DataFrame(rows)
    e = x.E_route_5
    order = e.rank(method="first")
    x["tercile"] = pd.cut(order, [0, len(x) / 3, 2 * len(x) / 3, len(x)], labels=["bottom", "middle", "top"]).astype(str)
    x.loc[e.isna(), "tercile"] = "none"
    x.to_csv(RUN / "results" / "tables" / "exposure.csv", index=False)
    summ = {"sites": int(len(x)), "sites_without_primary_E": int(e.isna().sum()),
            "primary_E_quantiles": {str(q): round(float(e.quantile(q)), 5) for q in (0, 0.25, 0.5, 0.75, 1)},
            "primary_E_iqr": round(float(e.quantile(0.75) - e.quantile(0.25)), 5),
            "tercile_counts": x.tercile.value_counts().to_dict(),
            "tercile_cutpoints": [round(float(e[x.tercile == "bottom"].max()), 5), round(float(e[x.tercile == "top"].min()), 5)],
            "median_valid_share_route_5": round(float(x.valid_share_route_5.median()), 3),
            "median_land_km2_route_5": round(float(x.land_km2_route_5.median()), 1),
            "spearman_route5_vs": {c: round(float(x.E_route_5.corr(x[c], method="spearman")), 3)
                                   for c in ("E_route_2", "E_route_10", "E_radius_2", "E_radius_5", "E_radius_10")}}
    json.dump(summ, open(RUN / "results" / "tables" / "exposure_summary.json", "w"), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
