"""The observed series: what share of tropical purse-seine skipjack sits inside the ten SIDS' EEZs?

Built from the WCPFC public-domain 1x1-degree monthly purse-seine file (SPC THREDDS mirror, 1967-2021;
1980-2021 is complete, every month present). Committed before it is run, and run only after plan.md is.

Two annual series over the fixed domain D (20S-20N, 120E-228E), 1980-2021:

  O1  catch share    sum(skipjack catch x EEZ fraction) / sum(skipjack catch), over D.
                     The quantity WCPFC itself reports and the one tied to access revenue. It confounds
                     where the fish are with where the fleet is allowed and chooses to fish.
  O2  density share  sum(area x EEZ fraction x CPUE) / sum(area x CPUE), over cells in D fished on at
                     least MIN_DAYS days that year, CPUE = annual skipjack catch / days fished.
                     Removes the effort-allocation component: a cell counts by how dense the fish
                     were where the fleet looked, not by how much fishing it received.

Three coordinate conventions, because the file does not say what its integer coordinates mean, and
they differ only for cells that straddle an EEZ boundary:
  sw      integer = south-west corner, cell spans [lat, lat+1] x [lon, lon+1]   (primary)
  centre  integer = cell centre,       cell spans [lat-0.5, lat+0.5]
  eqnear  integer = the corner nearest the equator (southern cells span [lat-1, lat])

Also quantifies the public-domain masking footprint - catch reported in cells with no effort recorded,
which is how suppressed low-vessel-count cells appear - because it bounds O2.

Writes results/tables/observed_annual.csv and results/tables/masking.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_targets import DOMAIN, cell_area_km2, eez_union, fractional_mask  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
OUT = RUN / "results" / "tables"
PROC = RUN / "data" / "processed"

YEARS = (1980, 2021)
MIN_DAYS = 5          # a cell-year needs >= 5 fishing days before its CPUE counts in O2
SCHOOLS = ["una", "log", "dfad", "afad", "oth"]
SPECIES = ["skj", "yft", "bet"]
OFFSETS = {"sw": (0.5, 0.5), "centre": (0.0, 0.0)}


def centres(lat, lon, conv):
    """Cell-centre coordinates under each convention."""
    if conv in OFFSETS:
        dy, dx = OFFSETS[conv]
        return lat + dy, lon + dx
    # eqnear: northern cells span [lat, lat+1], southern cells span [lat-1, lat]
    return np.where(lat >= 0, lat + 0.5, lat - 0.5), lon + 0.5


def load():
    ds = xr.open_dataset(RAW / "WCPFC_S_PUBLIC_BY_1x1_MM.nc")
    ds = ds.sel(time=slice(f"{YEARS[0]}-01-01", f"{YEARS[1]}-12-31"))
    catch = {sp: sum(ds[f"{sp}_c_{s}"].fillna(0) for s in SCHOOLS) for sp in SPECIES}
    days = ds["days"]
    return ds, catch, days


def annual(da):
    return da.groupby("time.year").sum("time", min_count=1)


def build(conv, ds, catch, days, shape):
    lat_c, lon_c = centres(ds.latitude.values, ds.longitude.values, conv)
    frac = fractional_mask(lat_c, lon_c, shape, 1.0)
    area = cell_area_km2(lat_c, 1.0, 1.0)[:, None] * np.ones((1, lon_c.size))
    in_d = ((lat_c >= DOMAIN["lat"][0]) & (lat_c <= DOMAIN["lat"][1]))[:, None] & \
           ((lon_c >= DOMAIN["lon"][0]) & (lon_c <= DOMAIN["lon"][1]))[None, :]
    F = xr.DataArray(frac * in_d, dims=("latitude", "longitude"))
    Dm = xr.DataArray(in_d.astype(float), dims=("latitude", "longitude"))
    A = xr.DataArray(area, dims=("latitude", "longitude"))

    rows = {}
    d_yr = annual(days).fillna(0)
    for sp in SPECIES:
        c_yr = annual(catch[sp]).fillna(0)
        c_eez = (c_yr * F).sum(("latitude", "longitude"))
        c_dom = (c_yr * Dm).sum(("latitude", "longitude"))
        rows[f"{sp}_catch_share"] = (c_eez / c_dom).to_series()
        rows[f"{sp}_catch_dom_t"] = c_dom.to_series()
        fished = d_yr >= MIN_DAYS
        cpue = xr.where(fished, c_yr / d_yr.where(d_yr > 0), 0.0)
        num = (A * F * cpue).sum(("latitude", "longitude"))
        den = (A * Dm * cpue).sum(("latitude", "longitude"))
        rows[f"{sp}_density_share"] = (num / den).to_series()
    # O2u: density share from unassociated (free-school) sets only, CPUE = skipjack per unassociated set.
    # Free schools are the set type least touched by FAD technology, so if O2 and O2u disagree, a
    # different FAD mix inside and outside the EEZs - which a within-year share does not cancel - is
    # the likely reason.
    cu = annual(ds["skj_c_una"].fillna(0)).fillna(0)
    su = annual(ds["sets_una"].fillna(0)).fillna(0)
    ok = su >= MIN_DAYS
    cpue_u = xr.where(ok, cu / su.where(su > 0), 0.0)
    rows["skj_density_share_una"] = ((A * F * cpue_u).sum(("latitude", "longitude")) /
                                     (A * Dm * cpue_u).sum(("latitude", "longitude"))).to_series()
    rows["days_eez_share"] = ((d_yr * F).sum(("latitude", "longitude")) /
                              (d_yr * Dm).sum(("latitude", "longitude"))).to_series()
    rows["n_fished_cells_dom"] = ((d_yr >= MIN_DAYS) * Dm).sum(("latitude", "longitude")).to_series()
    # sensitivity: the purse-seine core band, 10S-10N, where nearly all the fishing is
    core = xr.DataArray((np.abs(lat_c) <= 10)[:, None] * in_d, dims=("latitude", "longitude")).astype(float)
    c_yr = annual(catch["skj"]).fillna(0)
    rows["skj_catch_share_core10"] = ((c_yr * F * core).sum(("latitude", "longitude")) /
                                      (c_yr * core).sum(("latitude", "longitude"))).to_series()
    out = pd.DataFrame(rows)
    out.index.name = "year"
    out["convention"] = conv
    return out, frac


def masking(ds, catch, days, frac_sw):
    """Catch recorded where effort is missing or zero - the visible trace of public-domain suppression."""
    lat_c, lon_c = centres(ds.latitude.values, ds.longitude.values, "sw")
    in_d = ((lat_c >= DOMAIN["lat"][0]) & (lat_c <= DOMAIN["lat"][1]))[:, None] & \
           ((lon_c >= DOMAIN["lon"][0]) & (lon_c <= DOMAIN["lon"][1]))[None, :]
    F = xr.DataArray(frac_sw * in_d, dims=("latitude", "longitude"))
    Dm = xr.DataArray(in_d.astype(float), dims=("latitude", "longitude"))
    c = catch["skj"]
    no_eff = (days.isnull() | (days <= 0)) & (c > 0)
    rec = []
    for name, W in (("domain", Dm), ("eez", F)):
        tot = annual(c * W).sum(("latitude", "longitude")).to_series()
        orphan = annual(c.where(no_eff, 0) * W).sum(("latitude", "longitude")).to_series()
        rec.append(pd.DataFrame({f"{name}_catch_t": tot, f"{name}_catch_without_effort_t": orphan}))
    m = pd.concat(rec, axis=1)
    m["decade"] = (m.index // 10) * 10
    by_dec = m.groupby("decade").sum()
    for name in ("domain", "eez"):
        by_dec[f"{name}_share_without_effort"] = by_dec[f"{name}_catch_without_effort_t"] / by_dec[f"{name}_catch_t"]
    return by_dec


def main():
    shape, _ = eez_union()
    ds, catch, days = load()
    frames, frac_sw = [], None
    for conv in ("sw", "centre", "eqnear"):
        df, frac = build(conv, ds, catch, days, shape)
        frames.append(df)
        if conv == "sw":
            frac_sw = frac
    allc = pd.concat(frames)
    allc.to_csv(OUT / "observed_annual.csv")
    m = masking(ds, catch, days, frac_sw)
    m.to_csv(OUT / "masking.csv")
    print("wrote observed_annual.csv (3 conventions x", YEARS[1] - YEARS[0] + 1, "years) and masking.csv")
    print(m[[c for c in m.columns if c.endswith("share_without_effort")]].round(4))


if __name__ == "__main__":
    sys.exit(main())
