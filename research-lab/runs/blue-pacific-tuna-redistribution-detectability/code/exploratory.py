"""Exploratory analyses added after the primary results (deviations.md D5). None changes a verdict.

  1. Per-EEZ catch shares, testing a prediction fixed in D5 before this ran: the 2010 jump in the pooled
     share should sit in the EEZs bordering the two high-seas pockets closed to purse seiners in 2010.
  2. Size-calibrated power: the preregistered one-sided HAC test fired 14% of the time with no trend
     injected; here the critical value comes from the injected-zero simulations, so size is 5%.
  3. The zonal centroid: catch-, density- and biomass-weighted mean longitude in domain D.

Writes results/tables/exploratory.json.
"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import statsmodels.api as sm
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
from model_targets import DOMAIN, SIDS10, cell_area_km2, fractional_mask, open_run, to_360  # noqa: E402
from observed import SCHOOLS, centres  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
RAW, TAB = RUN / "data" / "raw", RUN / "results" / "tables"
YEARS = np.arange(1980, 2022)
SEED = A.SEED

# fixed in deviations.md D5 before this file was run
POCKET_ADJACENT = {"Micronesian Exclusive Economic Zone", "Palauan Exclusive Economic Zone",
                   "Papua New Guinean Exclusive Economic Zone", "Solomon Islands Exclusive Economic Zone",
                   "Nauruan Exclusive Economic Zone", "Marshallese Exclusive Economic Zone",
                   "Kiribati Exclusive Economic Zone (Gilbert Islands)"}


def step_fit(y, idx):
    """ENSO-adjusted trend plus a 2010 step; returns the step in pp with a HAC interval."""
    X = A.design(YEARS, idx, ("nino34", "nino34_lag", "wpe", "step2010"))
    r = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    lo, hi = r.conf_int()[5]
    return 100 * r.params[5], 100 * lo, 100 * hi


def per_eez(ds, idx):
    g = gpd.read_file(RAW / "eez" / "sids10_eez.geojson")
    g = g[g.iso_ter1.isin(SIDS10) & (g.pol_type == "200NM")]
    lat_c, lon_c = centres(ds.latitude.values, ds.longitude.values, "sw")
    in_d = ((lat_c >= DOMAIN["lat"][0]) & (lat_c <= DOMAIN["lat"][1]))[:, None] & \
           ((lon_c >= DOMAIN["lon"][0]) & (lon_c <= DOMAIN["lon"][1]))[None, :]
    skj = sum(ds[f"skj_c_{s}"].fillna(0) for s in SCHOOLS).groupby("time.year").sum("time")
    total = (skj * xr.DataArray(in_d.astype(float), dims=("latitude", "longitude"))).sum(("latitude", "longitude"))
    rows = []
    for _, f in g.iterrows():
        frac = fractional_mask(lat_c, lon_c, to_360(f.geometry), 1.0)
        F = xr.DataArray(frac * in_d, dims=("latitude", "longitude"))
        share = ((skj * F).sum(("latitude", "longitude")) / total).to_series().loc[YEARS[0]:YEARS[-1]]
        step, lo, hi = step_fit(share.to_numpy(float), idx)
        rows.append(dict(eez=f.geoname, pocket_adjacent=f.geoname in POCKET_ADJACENT,
                         share_1980_2009=100 * float(share.loc[1980:2009].mean()),
                         share_2010_2021=100 * float(share.loc[2010:2021].mean()),
                         step_pp=step, step_lo=lo, step_hi=hi))
    t = pd.DataFrame(rows).sort_values("step_pp", ascending=False)
    grp = t.groupby("pocket_adjacent")[["share_1980_2009", "share_2010_2021", "step_pp"]].sum()
    return t, grp


def calibrated_power(y, idx, deltas, nsim=2000):
    """Power with the critical value taken from the injected-zero simulations (exact 5% size)."""
    f = A.fit_trend(y, YEARS, idx)
    base = f["fitted"] - f["beta"][1] * f["X"][:, 1]
    rng = np.random.default_rng(SEED)

    def tstats(delta):
        out = np.empty(nsim)
        for k in range(nsim):
            ys = base + (-abs(delta) / 100) * f["X"][:, 1] + f["resid"][A.block_indices(len(y), A.BLOCK, rng)]
            r = sm.OLS(ys, f["X"]).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
            out[k] = r.tvalues[1]
        return out

    null = tstats(0.0)
    crit = float(np.percentile(null, 100 * A.ALPHA))          # one-sided: a decline gives negative t
    nominal_size = float(np.mean(null < -1.6449))
    curve = {float(d): float(np.mean(tstats(d) < crit)) for d in deltas}
    mde = next((d for d in sorted(curve) if curve[d] >= A.POWER), None)
    return dict(critical_t=crit, nominal_test_size=nominal_size, curve=curve, mde_pp=mde)


def calibrated_detection_year(resid, tau, start=2011, first=1980, horizon=2200, step=1, nsim=600):
    sd, phi = float(np.std(resid, ddof=1)), float(np.corrcoef(resid[:-1], resid[1:])[0, 1])
    innov = sd * np.sqrt(1 - phi ** 2)
    rng = np.random.default_rng(SEED)

    def sim_t(Y, slope):
        yrs = np.arange(first, Y + 1)
        hinge = np.maximum(0, yrs - start).astype(float)
        X = np.column_stack([np.ones(len(yrs)), hinge])
        out = np.empty(nsim)
        for k in range(nsim):
            e = np.empty(len(yrs)); e[0] = rng.normal(0, sd)
            for t in range(1, len(yrs)):
                e[t] = phi * e[t - 1] + rng.normal(0, innov)
            out[k] = sm.OLS(slope * hinge + e, X).fit(cov_type="HAC", cov_kwds={"maxlags": 3}).tvalues[1]
        return out

    for Y in range(2021, horizon + 1, step):
        crit = np.percentile(sim_t(Y, 0.0), 100 * A.ALPHA)
        p = float(np.mean(sim_t(Y, tau / 100) < crit))
        if p >= A.POWER:
            return dict(year=Y, power=p)
    return dict(year=None, power=p)


def centroid_obs(ds, weight):
    lat_c, lon_c = centres(ds.latitude.values, ds.longitude.values, "sw")
    in_d = ((lat_c >= DOMAIN["lat"][0]) & (lat_c <= DOMAIN["lat"][1]))[:, None] & \
           ((lon_c >= DOMAIN["lon"][0]) & (lon_c <= DOMAIN["lon"][1]))[None, :]
    W = weight * xr.DataArray(in_d.astype(float), dims=("latitude", "longitude"))
    L = xr.DataArray(np.broadcast_to(lon_c[None, :], in_d.shape), dims=("latitude", "longitude"))
    return ((W * L).sum(("latitude", "longitude")) / W.sum(("latitude", "longitude"))).to_series()


def centroid_model(da):
    lat, lon = da.lat.values, da.lon.values
    area = cell_area_km2(lat, 2.0, 2.0)[:, None] * np.ones((1, lon.size))
    in_d = ((lat >= DOMAIN["lat"][0]) & (lat <= DOMAIN["lat"][1]))[:, None] & \
           ((lon >= DOMAIN["lon"][0]) & (lon <= DOMAIN["lon"][1]))[None, :]
    w = xr.DataArray(area * in_d, dims=("lat", "lon"), coords={"lat": da.lat, "lon": da.lon})
    L = xr.DataArray(np.broadcast_to(lon[None, :], in_d.shape), dims=("lat", "lon"),
                     coords={"lat": da.lat, "lon": da.lon})
    b = da.fillna(0) * w
    return ((b * L).sum(("lat", "lon")) / b.sum(("lat", "lon"))).groupby("time.year").mean().to_series()


def main():
    idx = pd.read_csv(TAB / "indices.csv", index_col=0)
    idx["step2010"] = (idx.index >= 2010).astype(float)
    obs = pd.read_csv(TAB / "observed_annual.csv", index_col=0)
    obs = obs[obs.convention == "sw"]
    prim = json.load(open(TAB / "primary.json"))
    tau = prim["tau_pp"]
    ds = xr.open_dataset(RAW / "WCPFC_S_PUBLIC_BY_1x1_MM.nc").sel(time=slice("1980", "2021"))
    out = {}

    t, grp = per_eez(ds, idx)
    out["per_eez"] = t.to_dict(orient="records")
    out["per_eez_by_group"] = grp.reset_index().to_dict(orient="records")
    print(t[["eez", "pocket_adjacent", "share_1980_2009", "share_2010_2021", "step_pp"]].round(2).to_string(index=False))
    print(grp.round(2))

    y = obs.loc[YEARS, "skj_catch_share"].to_numpy(float)
    deltas = [round(x, 3) for x in np.arange(0.0, 1.01, 0.025)]
    cp = calibrated_power(y, idx, deltas)
    f = A.fit_trend(y, YEARS, idx)
    cp["power_at_tau"] = cp["curve"][min(cp["curve"], key=lambda d: abs(d - abs(tau)))]
    out["calibrated_power"] = cp
    out["calibrated_detection_year"] = calibrated_detection_year(f["resid"], tau)
    print(f"\ncalibrated: nominal test size {cp['nominal_test_size']:.3f}, MDE {cp['mde_pp']} pp/yr, "
          f"power at |tau| {cp['power_at_tau']:.2f}, detectable by {out['calibrated_detection_year']['year']}")

    skj = sum(ds[f"skj_c_{s}"].fillna(0) for s in SCHOOLS).groupby("time.year").sum("time")
    days = ds["days"].fillna(0).groupby("time.year").sum("time")
    cpue = xr.where(days >= 5, skj / days.where(days > 0), 0.0)
    lat_c, _ = centres(ds.latitude.values, ds.longitude.values, "sw")
    area = xr.DataArray(cell_area_km2(lat_c, 1.0, 1.0)[:, None] * np.ones((1, ds.sizes["longitude"])),
                        dims=("latitude", "longitude"))
    cen = dict(catch=centroid_obs(ds, skj), density=centroid_obs(ds, cpue * area))
    hist = centroid_model(open_run("skj", "hist"))
    proj = pd.concat({e: centroid_model(open_run("skj", e)) for e in ("GFDL", "IPSL", "MIROC", "MPI")}, axis=1).mean(1)
    res = {}
    for k, s in cen.items():
        res[f"obs_{k}_1980_2021"] = A.trend_ci(s.loc[YEARS].to_numpy(float) / 100, YEARS, idx)
    hy = np.arange(1980, 2011)
    res["model_hist_1980_2010"] = A.trend_ci(hist.loc[hy].to_numpy(float) / 100, hy, idx)
    res["model_proj_2011_2050_deg_per_yr"] = float(np.polyfit(proj.loc[2011:2050].index, proj.loc[2011:2050].values, 1)[0])
    out["centroid_deg_per_yr"] = res      # trend_ci reports in 'pp' units; with the /100 above, that is degrees/yr
    for k, v in res.items():
        if isinstance(v, dict):
            print(f"centroid {k:28s} {v['point']:+.3f} deg/yr [{v['lo']:+.3f}, {v['hi']:+.3f}]")
        else:
            print(f"centroid {k:28s} {v:+.3f} deg/yr")
    json.dump(out, open(TAB / "exploratory.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    sys.exit(main())
