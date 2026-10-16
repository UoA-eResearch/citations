"""The check D4 promised and the first draft never ran (review issue 11). Added after review.

The 1-degree public-domain file suppresses low-vessel cells by removing every variable, so suppression
cannot be seen inside it (D4). WCPFC's 5-degree public data, as harmonised in the FIRMS Global Tuna Atlas
(Zenodo 21114897, v2026.1.2, CC-BY), suppress far less. Comparing annual skipjack purse-seine totals over
the same domain bounds what the 1-degree file is missing. It cannot say WHERE the missing catch was, so it
bounds the size of the problem for the EEZ share, not its direction.

CWP grid codes: 6 = 5x5 degree square; next digit is the quadrant (1 NE, 2 SE, 3 SW, 4 NW); then two digits
of latitude and three of longitude, the corner nearest the origin.

Writes results/tables/firms_check.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_targets import DOMAIN  # noqa: E402
from observed import SCHOOLS, centres  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
RAW, TAB = RUN / "data" / "raw", RUN / "results" / "tables"


def cwp5_centre(code):
    s = str(code)
    if len(s) != 7 or s[0] != "6":
        return np.nan, np.nan
    q, lat, lon = int(s[1]), int(s[2:4]), int(s[4:7])
    lat_c = lat + 2.5 if q in (1, 4) else -(lat + 2.5)
    lon_c = lon + 2.5 if q in (1, 2) else -(lon + 2.5)
    return lat_c, lon_c % 360


def main():
    g = pd.read_parquet(RAW / "gta" / "gta_public.parquet",
                        columns=["source_authority", "geographic_identifier", "gear_type", "species",
                                 "measurement", "measurement_unit", "measurement_value", "year"])
    g = g[(g.source_authority == "WCPFC") & (g.species == "SKJ") & (g.gear_type == "01.1")
          & (g.measurement == "catch") & (g.measurement_unit == "t") & (g.year.between(1980, 2021))]
    cells = pd.DataFrame({"code": g.geographic_identifier.unique()})
    cells[["lat", "lon"]] = cells.code.apply(lambda c: pd.Series(cwp5_centre(c)))
    inside = cells[(cells.lat >= DOMAIN["lat"][0]) & (cells.lat <= DOMAIN["lat"][1])
                   & (cells.lon >= DOMAIN["lon"][0]) & (cells.lon <= DOMAIN["lon"][1])].code
    five = g[g.geographic_identifier.isin(inside)].groupby("year").measurement_value.sum() / 1000

    ds = xr.open_dataset(RAW / "WCPFC_S_PUBLIC_BY_1x1_MM.nc").sel(time=slice("1980", "2021"))
    lat_c, lon_c = centres(ds.latitude.values, ds.longitude.values, "sw")
    in_d = ((lat_c >= DOMAIN["lat"][0]) & (lat_c <= DOMAIN["lat"][1]))[:, None] & \
           ((lon_c >= DOMAIN["lon"][0]) & (lon_c <= DOMAIN["lon"][1]))[None, :]
    skj = sum(ds[f"skj_c_{s}"].fillna(0) for s in SCHOOLS).groupby("time.year").sum("time")
    one = (skj * xr.DataArray(in_d.astype(float), dims=("latitude", "longitude"))).sum(("latitude", "longitude")).to_series() / 1000

    t = pd.DataFrame({"one_deg_kt": one, "five_deg_kt": five}).loc[1980:2021]
    t["ratio"] = t.one_deg_kt / t.five_deg_kt
    t["decade"] = (t.index // 10) * 10
    dec = t.groupby("decade")[["one_deg_kt", "five_deg_kt"]].sum()
    dec["ratio"] = dec.one_deg_kt / dec.five_deg_kt
    out = dict(source="FIRMS Global Tuna Atlas level 0 public, WCPFC, SKJ, purse seine (01.1), 5-degree",
               note="5-degree cells assigned to the domain by centre; edge cells make the domains match only approximately",
               by_decade=dec.reset_index().to_dict(orient="records"),
               ratio_min_year=float(t.ratio.min()), ratio_max_year=float(t.ratio.max()),
               ratio_median=float(t.ratio.median()),
               by_year=t.reset_index().rename(columns={"index": "year"}).to_dict(orient="records"))
    json.dump(out, open(TAB / "firms_check.json", "w"), indent=1, default=float)
    print(dec.round(3).to_string())
    print(f"\nyearly 1-degree / 5-degree ratio: median {t.ratio.median():.3f}, range {t.ratio.min():.3f}-{t.ratio.max():.3f}")


if __name__ == "__main__":
    sys.exit(main())
