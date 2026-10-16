"""Numbers added in response to the adversarial review (deviations D8). None changes a preregistered verdict.

  gls        H1's trend with a GLS-AR(1) interval. The preregistered intervals undercover under the observed
             residual autocorrelation (0.56): about 0.79 (block bootstrap) and 0.76 (HAC) in simulation.
  h2_1990    H2 from 1990, after the fleet's development decade, when it fished 25-180 cells a year.
  hinge      Power for the hypothetical the projection actually makes - a decline beginning in 2011 - with the
             record ending in 2021, rather than a linear decline across all 42 years.
  detection  The year a decline at the projected rate becomes detectable at 80% power, under a range of noise
             models, not one. The preregistered figure treats the 1980s fleet development and the 2010 step as
             future noise.
  closure    A direct look at the 2010 high-seas-pocket closure: skipjack catch outside the twelve EEZ areas,
             by longitude band, before and after.

Writes results/tables/review_response.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
from model_targets import DOMAIN, eez_union, fractional_mask  # noqa: E402
from observed import SCHOOLS, centres  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
RAW, TAB = RUN / "data" / "raw", RUN / "results" / "tables"
YEARS = np.arange(1980, 2022)
NSIM = 1000


def ar1_noise(n, sd, phi, rng):
    innov = sd * np.sqrt(1 - phi ** 2)
    e = np.empty(n); e[0] = rng.normal(0, sd)
    for t in range(1, n):
        e[t] = phi * e[t - 1] + rng.normal(0, innov)
    return e


def hac_t(y, X, col=1):
    return sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 3}).tvalues[col]


def detection_year(sd, phi, tau, start=2011, first=1980, horizon=2160, nsim=NSIM, seed=A.SEED):
    """Size-calibrated: each year's critical value comes from simulations with no decline."""
    rng = np.random.default_rng(seed)
    for Y in range(2021, horizon + 1):
        yrs = np.arange(first, Y + 1)
        hinge = np.maximum(0, yrs - start).astype(float)
        X = np.column_stack([np.ones(len(yrs)), hinge])
        null = [hac_t(ar1_noise(len(yrs), sd, phi, rng), X) for _ in range(nsim)]
        crit = np.percentile(null, 5)
        alt = [hac_t((tau / 100) * hinge + ar1_noise(len(yrs), sd, phi, rng), X) for _ in range(nsim)]
        p = float(np.mean(np.array(alt) < crit))
        if p >= 0.8:
            return Y
    return None


def main():
    obs = pd.read_csv(TAB / "observed_annual.csv", index_col=0)
    obs = obs[obs.convention == "sw"]
    idx = pd.read_csv(TAB / "indices.csv", index_col=0)
    idx["step2010"] = (idx.index >= 2010).astype(float)
    m = json.load(open(TAB / "model_targets.json"))
    hist = pd.Series({int(k): v for k, v in m["series"]["hist_share"].items()})
    tau = A.tau_pp()
    y = obs.loc[YEARS, "skj_catch_share"].to_numpy(float)
    out = {}

    # gls
    g = sm.GLSAR(y, A.design(YEARS, idx), rho=1).iterative_fit(maxiter=20)
    lo, hi = g.conf_int()[1]
    out["gls"] = dict(rho=float(g.model.rho[0]), point=100 * float(g.params[1]), lo=100 * float(lo),
                      hi=100 * float(hi), verdict_vs_tau=A.verdict_h1(100 * lo, 100 * hi, tau))

    # h2 from 1990
    yy = np.arange(1990, 2011)
    out["h2_1990_2010"] = {c: A.h2_difference(obs.loc[yy, c].to_numpy(float), hist.loc[yy].to_numpy(float), yy, idx)
                           for c in ("skj_catch_share", "skj_density_share", "skj_density_share_una")}

    # hinge power with the record ending in 2021, size-calibrated on the observed residuals
    f = A.fit_trend(y, YEARS, idx)
    base = f["fitted"] - f["beta"][1] * f["X"][:, 1]
    hinge = np.maximum(0, YEARS - 2011).astype(float)
    Xh = np.column_stack([f["X"][:, [0, 2, 3, 4]], hinge])
    rng = np.random.default_rng(A.SEED)
    draw = lambda d: base + (d / 100) * hinge + f["resid"][A.block_indices(len(y), A.BLOCK, rng)]
    null = [hac_t(draw(0.0), Xh, col=4) for _ in range(NSIM)]
    crit = np.percentile(null, 5)
    out["hinge_power_to_2021"] = float(np.mean([hac_t(draw(tau), Xh, col=4) < crit for _ in range(NSIM)]))

    # detection year under a range of noise models
    def resid_stats(yrs, covars):
        r = A.fit_trend(obs.loc[yrs, "skj_catch_share"].to_numpy(float), yrs, idx, covars)["resid"]
        return float(np.std(r, ddof=1)), float(np.corrcoef(r[:-1], r[1:])[0, 1])
    full = resid_stats(YEARS, A.COVARS)
    step = resid_stats(YEARS, A.COVARS + ("step2010",))
    late = resid_stats(np.arange(1990, 2022), A.COVARS + ("step2010",))
    variants = {
        "full-period residuals (preregistered noise)": (full[0], full[1], tau),
        "residuals with the 2010 step removed": (step[0], step[1], tau),
        "1990-2021 residuals, 2010 step removed": (late[0], late[1], tau),
        "preregistered sd, no autocorrelation": (full[0], 0.0, tau),
        "preregistered sd, autocorrelation 0.75": (full[0], 0.75, tau),
        "SEAPODYM 2011-2030 rate (-0.336)": (full[0], full[1], -0.336),
        "IPSL rate (-0.216)": (full[0], full[1], -0.216),
        "fishery-independent-like noise (sd 1.26, ac1 0.63)": (0.0126, 0.63, tau),
    }
    out["detection_year"] = {}
    for name, (sd, phi, rate) in variants.items():
        yr = detection_year(sd, phi, rate)
        out["detection_year"][name] = dict(sd_pp=100 * sd, ac1=phi, rate=rate, year=yr)
        print(f"  detection year | {name:52s} sd {100*sd:4.2f} ac1 {phi:+.2f} -> {yr}", flush=True)

    # closure: catch outside the twelve EEZ areas, by longitude band
    ds = xr.open_dataset(RAW / "WCPFC_S_PUBLIC_BY_1x1_MM.nc").sel(time=slice("2000", "2019"))
    lat_c, lon_c = centres(ds.latitude.values, ds.longitude.values, "sw")
    in_d = ((lat_c >= DOMAIN["lat"][0]) & (lat_c <= DOMAIN["lat"][1]))[:, None] & \
           ((lon_c >= DOMAIN["lon"][0]) & (lon_c <= DOMAIN["lon"][1]))[None, :]
    frac = fractional_mask(lat_c, lon_c, eez_union()[0], 1.0)
    skj = sum(ds[f"skj_c_{s}"].fillna(0) for s in SCHOOLS).groupby("time.year").sum("time").values
    outside = skj * ((1 - frac) * in_d)[None]
    bands = {}
    for a, b in ((120, 140), (140, 160), (160, 180), (180, 200), (200, 228)):
        cols = (lon_c >= a) & (lon_c < b)
        s = outside[:, :, cols].sum(axis=(1, 2)) / 1000
        yrs = np.arange(2000, 2020)
        bands[f"{a}-{b}E"] = dict(kt_per_yr_2000_2009=float(s[yrs < 2010].mean()), kt_per_yr_2010_2019=float(s[yrs >= 2010].mean()))
    out["closure_outside_eez_catch_by_band"] = bands
    # timing east of the dateline (confirmation pass, D9): decade means hid that nothing rose at the closure
    cols = (lon_c >= 180) & (lon_c < 200)
    east = pd.Series(outside[:, :, cols].sum(axis=(1, 2)) / 1000, index=np.arange(2000, 2020))
    out["east_180_200E_timing"] = dict(kt_2000_2009=float(east.loc[2000:2009].mean()),
                                       kt_2010_2013=float(east.loc[2010:2013].mean()),
                                       kt_2014_2019=float(east.loc[2014:2019].mean()),
                                       kt_2015=float(east.loc[2015]),
                                       corr_nino34_2000_2019=float(np.corrcoef(east, idx.loc[2000:2019, "nino34"])[0, 1]))

    json.dump(out, open(TAB / "review_response.json", "w"), indent=1, default=float)
    print(f"GLS-AR(1) rho {out['gls']['rho']:.2f}: {out['gls']['point']:+.3f} [{out['gls']['lo']:+.3f}, {out['gls']['hi']:+.3f}] -> {out['gls']['verdict_vs_tau']}")
    for c, v in out["h2_1990_2010"].items():
        print(f"H2 1990-2010 {c:24s} obs {v['obs']:+.3f} model {v['model']:+.3f} diff {v['diff']:+.3f} [{v['lo']:+.3f}, {v['hi']:+.3f}]")
    print(f"power for the projected hinge, record to 2021: {out['hinge_power_to_2021']:.3f}")
    for k, v in bands.items():
        print(f"outside-EEZ skipjack {k:9s} {v['kt_per_yr_2000_2009']:7.1f} -> {v['kt_per_yr_2010_2019']:7.1f} kt/yr")


if __name__ == "__main__":
    sys.exit(main())
