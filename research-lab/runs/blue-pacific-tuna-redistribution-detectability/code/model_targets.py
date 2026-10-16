"""What does SEAPODYM itself predict, before any observation is looked at?

Run before plan.md is committed, on model output only. Three jobs:

  1. Build a fractional EEZ mask for the 12 EEZ areas of the ten Pacific SIDS in Bell et al. (2021)
     on the SEAPODYM 2-degree grid, and check it against Marine Regions' own area figures.
  2. Reproduce the published headline - total biomass of skipjack + yellowfin + bigeye in the combined
     EEZs falls by an average of 13% (range -5% to -20%) by 2050 (2044-2053) relative to 2009-2018,
     under RCP 8.5, across four ESMs - from the very files Bell et al. used. If the mask or the
     arithmetic is wrong, this is where it shows, and nothing downstream should be trusted until it
     reproduces.
  3. Derive the skipjack quantity the observations can actually be compared with: the share of
     skipjack biomass in a fixed tropical domain D that lies inside the ten-SIDS EEZs, and its trend,
     both in the historical run (1980-2010, ocean-reanalysis forced) and in the projections.

Writes results/tables/model_targets.json and data/processed/eez_mask_2deg.nc.
"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from shapely.affinity import translate
from shapely.geometry import MultiPolygon, Polygon, box
from shapely.ops import unary_union

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
SEA = RAW / "seapodym"
OUT = RUN / "results" / "tables"
PROC = RUN / "data" / "processed"

# Bell et al. (2021): the eight PNA members, Tokelau and the Cook Islands - 12 EEZ areas
SIDS10 = ["FSM", "KIR", "MHL", "NRU", "PLW", "PNG", "SLB", "TUV", "TKL", "COK"]
ESMS = ["GFDL", "IPSL", "MIROC", "MPI"]
SPECIES = ["skj", "yft", "bet"]
# the comparison domain: the tropical purse-seine band, east edge set by the WCPFC 1-degree data (228E)
DOMAIN = dict(lat=(-20.0, 20.0), lon=(120.0, 228.0))
R_EARTH = 6371.0088


def to_360(geom):
    """Marine Regions longitudes run -180..180; SEAPODYM runs 0..360. Shift any part west of 0."""
    parts = list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]
    out = []
    for p in parts:
        minx = p.bounds[0]
        out.append(translate(p, xoff=360.0) if minx < 0 else p)
    return unary_union(out)


def eez_union():
    g = gpd.read_file(RAW / "eez" / "sids10_eez.geojson")
    g = g[(g.iso_ter1.isin(SIDS10)) & (g.pol_type == "200NM")]   # drops the Torres Strait joint regime
    assert len(g) == 12, f"expected the 12 EEZ areas of Bell et al., got {len(g)}"
    return unary_union([to_360(geom) for geom in g.geometry]), g


def cell_area_km2(lat_c, dlat, dlon):
    """Area of a lat-lon cell on a sphere."""
    lat1, lat2 = np.radians(lat_c - dlat / 2), np.radians(lat_c + dlat / 2)
    return R_EARTH ** 2 * np.radians(dlon) * (np.sin(lat2) - np.sin(lat1))


def fractional_mask(lat, lon, shape, res):
    """Share of each cell's (spherical) area lying inside `shape`. Planar overlap in degrees is fine
    within a 2-degree cell; the cos(lat) weighting is carried separately by cell_area_km2."""
    frac = np.zeros((lat.size, lon.size))
    minx, miny, maxx, maxy = shape.bounds
    for i, la in enumerate(lat):
        if la + res / 2 < miny or la - res / 2 > maxy:
            continue
        for j, lo in enumerate(lon):
            if lo + res / 2 < minx or lo - res / 2 > maxx:
                continue
            c = box(lo - res / 2, la - res / 2, lo + res / 2, la + res / 2)
            if shape.intersects(c):
                frac[i, j] = shape.intersection(c).area / c.area
    return frac


def _load(sp, part, run):
    ds = xr.open_dataset(SEA / f"{sp}_{part}_{run}_F0.nc", decode_times=False)
    units = ds.time.attrs["units"]
    ref = pd.Timestamp(units.split("since")[1].strip())
    t = ds.time.values
    # the two runs encode time differently: hist is 'months since 1980-1-15', projections 'days since 2011-01-15'
    if units.startswith("months"):
        dates = [ref + pd.DateOffset(months=int(x)) for x in t]
    else:
        dates = [ref + pd.Timedelta(days=float(x)) for x in t]
    # take the single data variable by position, not by name: the bigeye projection 'Btot' files name
    # theirs 'bet_B_young' although they hold total biomass (checked: identical to adult + young)
    return ds[list(ds.data_vars)[0]].assign_coords(time=pd.DatetimeIndex(dates))


def open_run(sp, run):
    """Total biomass, defined as adult + young throughout.

    That is what 'Btot' holds in every file except one: the bigeye historical run, whose 'Btot' is
    identical to its 'Badult' file (maximum difference 0) - adult biomass only. (The first version of
    this note described it as 0.848 x (adult + young) varying by cell; that ratio was just the adult
    fraction, and the review identified what the file actually is - deviations D8.) It would put a
    definitional step into anything spliced across 2010/2011, so for that run alone adult + young is used.
    Skipjack and yellowfin agree to 1.0000 in every cell, so for them this changes nothing.
    """
    if sp == "bet" and run == "hist":
        return _load(sp, "Badult", run) + _load(sp, "Byoung", run)
    return _load(sp, "Btot", run)


def annual_biomass(da, weight):
    """Annual mean of sum(density x cell area x weight): biomass in the weighted region (density units x km2)."""
    w = xr.DataArray(weight, dims=("lat", "lon"), coords={"lat": da.lat, "lon": da.lon})
    tot = (da.fillna(0) * w).sum(("lat", "lon"))
    return tot.groupby("time.year").mean()


def main():
    shape, g = eez_union()
    ref = open_run("skj", "hist")
    lat, lon = ref.lat.values, ref.lon.values
    res = float(abs(lat[1] - lat[0]))
    area = cell_area_km2(lat, res, res)[:, None] * np.ones((1, lon.size))
    frac = fractional_mask(lat, lon, shape, res)

    # check 1: the mask's EEZ area against Marine Regions' own figures (ocean cells only differ a little)
    mask_area = float((frac * area).sum())
    mr_area = float(g["area_km2"].sum()) if "area_km2" in g else float("nan")

    dom = np.zeros_like(frac)
    la_ok = (lat >= DOMAIN["lat"][0]) & (lat <= DOMAIN["lat"][1])
    lo_ok = (lon >= DOMAIN["lon"][0]) & (lon <= DOMAIN["lon"][1])
    dom[np.ix_(la_ok, lo_ok)] = 1.0

    xr.Dataset({"eez_frac": (("lat", "lon"), frac), "domain": (("lat", "lon"), dom),
                "cell_area_km2": (("lat", "lon"), area)},
               coords={"lat": lat, "lon": lon}).to_netcdf(PROC / "eez_mask_2deg.nc")

    # check 2: reproduce Bell et al.'s 13%, three species, 2044-2053 vs 2009-2018
    # The projection files begin in 2011, so 2009-2010 come from the historical run. Splicing a
    # reanalysis-forced run onto an ESM-forced one is what the published baseline implies; the
    # projection-only baseline (2011-2018) is reported alongside so the choice is visible.
    w_eez = frac * area
    bell = {}
    for esm in ESMS:
        b_hist = sum(annual_biomass(open_run(sp, "hist"), w_eez) for sp in SPECIES)
        b_proj = sum(annual_biomass(open_run(sp, esm), w_eez) for sp in SPECIES)
        spliced = pd.concat([b_hist.to_series(), b_proj.to_series()])
        base = spliced.loc[2009:2018].mean()
        base_proj = b_proj.to_series().loc[2011:2018].mean()
        fut = b_proj.to_series().loc[2044:2053].mean()
        bell[esm] = dict(change_spliced_baseline=float(fut / base - 1),
                         change_projection_baseline=float(fut / base_proj - 1))
    chg = np.array([v["change_spliced_baseline"] for v in bell.values()])
    chg_p = np.array([v["change_projection_baseline"] for v in bell.values()])

    # 3: the comparable skipjack quantity - share of domain-D biomass inside the ten-SIDS EEZs
    w_dom = dom * area
    w_eez_dom = frac * dom * area

    def share(da):
        return (annual_biomass(da, w_eez_dom) / annual_biomass(da, w_dom)).to_series()

    def trend(s, y0, y1):
        s = s.loc[y0:y1]
        b = np.polyfit(s.index.values, s.values, 1)[0]
        return float(b)

    hist_share = share(open_run("skj", "hist"))
    proj = {esm: share(open_run("skj", esm)) for esm in ESMS}
    proj_mean = pd.concat(proj, axis=1).mean(axis=1)

    out = dict(
        eez_areas=sorted(g.geoname.tolist()),
        n_eez_areas=int(len(g)),
        mask_eez_area_km2=mask_area,
        marine_regions_eez_area_km2=mr_area,
        mask_area_ratio=mask_area / mr_area if mr_area == mr_area else None,
        domain=DOMAIN,
        bell_reproduction=dict(
            published=dict(mean=-0.13, range=[-0.20, -0.05],
                           definition="skj+yft+bet total biomass, 12 EEZ areas, 2044-2053 vs 2009-2018, RCP8.5"),
            per_esm=bell,
            mean_spliced=float(chg.mean()), range_spliced=[float(chg.min()), float(chg.max())],
            mean_projection_only=float(chg_p.mean()),
            range_projection_only=[float(chg_p.min()), float(chg_p.max())]),
        skipjack_share=dict(
            hist_mean_1980_2010=float(hist_share.mean()),
            hist_trend_per_year_1980_2010=trend(hist_share, 1980, 2010),
            proj_baseline_2011_2020=float(proj_mean.loc[2011:2020].mean()),
            proj_2044_2053=float(proj_mean.loc[2044:2053].mean()),
            proj_trend_per_year_2011_2050={e: trend(s, 2011, 2050) for e, s in proj.items()},
            proj_trend_per_year_2011_2050_mean=trend(proj_mean, 2011, 2050),
            proj_trend_per_year_2011_2030_mean=trend(proj_mean, 2011, 2030)),
        series=dict(hist_share={int(k): float(v) for k, v in hist_share.items()},
                    proj_share_mean={int(k): float(v) for k, v in proj_mean.loc[:2060].items()}),
    )
    json.dump(out, open(OUT / "model_targets.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "series"}, indent=1))


if __name__ == "__main__":
    sys.exit(main())
