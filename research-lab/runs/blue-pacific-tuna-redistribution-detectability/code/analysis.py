"""Estimators, decision rules and the power analysis, exactly as preregistered in plan.md.

Every series is an annual share (a fraction). Trends are reported in percentage points per year.

The ENSO-adjusted trend is the coefficient b in
    share_t = a + b (year_t - 2000) + c nino34_t + d nino34_{t-1} + e wpe_t + error_t
fitted by OLS. Its interval comes from a moving-block residual bootstrap (block 4 years, 2000 draws,
seed 20261016), which keeps the serial correlation that ENSO cycles leave in annual fishery data; a
Newey-West (HAC, 3 lags) interval is reported alongside as a sensitivity.

The threshold tau is not chosen here. It is SEAPODYM's own projected rate of change in the identical
share (same domain, same 12 EEZ areas), averaged over the four ESMs for 2011-2050, computed from model
output alone by code/model_targets.py before any observation was examined.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
SEED = 20261016
NBOOT = 2000
BLOCK = 4
ALPHA = 0.05
POWER = 0.80
COVARS = ("nino34", "nino34_lag", "wpe")
CENTRE_YEAR = 2000


def tau_pp():
    """The preregistered threshold, in pp/yr, read from the model-only target file."""
    m = json.load(open(TAB / "model_targets.json"))
    return 100.0 * m["skipjack_share"]["proj_trend_per_year_2011_2050_mean"]


def design(years, idx, covars=COVARS, trend=True):
    cols = [np.ones(len(years))]
    if trend:
        cols.append(np.asarray(years, float) - CENTRE_YEAR)
    for c in covars:
        cols.append(idx.loc[years, c].to_numpy(float))
    return np.column_stack(cols)


def ols(y, X):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def fit_trend(y, years, idx, covars=COVARS):
    """ENSO-adjusted trend b (fraction per year), with fitted values and residuals."""
    X = design(years, idx, covars)
    beta = ols(y, X)
    fitted = X @ beta
    return dict(b=float(beta[1]), beta=beta, X=X, fitted=fitted, resid=y - fitted)


def block_indices(n, block, rng):
    """Moving-block bootstrap, circular, length n."""
    starts = rng.integers(0, n, int(np.ceil(n / block)))
    idx = np.concatenate([(s + np.arange(block)) % n for s in starts])
    return idx[:n]


def trend_ci(y, years, idx, covars=COVARS, nboot=NBOOT, block=BLOCK, seed=SEED):
    """Point estimate and 95% block-bootstrap interval for the ENSO-adjusted trend, in pp/yr."""
    y = np.asarray(y, float)
    f = fit_trend(y, years, idx, covars)
    rng = np.random.default_rng(seed)
    draws = np.empty(nboot)
    for k in range(nboot):
        ystar = f["fitted"] + f["resid"][block_indices(len(y), block, rng)]
        draws[k] = ols(ystar, f["X"])[1]
    lo, hi = np.percentile(draws, [2.5, 97.5])
    hac = sm.OLS(y, f["X"]).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    hlo, hhi = hac.conf_int(alpha=ALPHA)[1]
    ac1 = float(np.corrcoef(f["resid"][:-1], f["resid"][1:])[0, 1])
    return dict(point=100 * f["b"], lo=100 * lo, hi=100 * hi, hac_lo=100 * hlo, hac_hi=100 * hhi,
                resid_sd_pp=100 * float(np.std(f["resid"], ddof=len(f["beta"]))), resid_ac1=ac1,
                n_years=int(len(y)), covars=list(covars))


def verdict_h1(lo, hi, tau):
    """plan.md section 6: is the observed trend less steep than SEAPODYM's projected decline?"""
    if lo > tau:
        return "Supported"
    if hi < tau:
        return "Refuted"
    return "Inconclusive"


def h2_difference(y_obs, y_mod, years, idx, covars=COVARS, nboot=NBOOT, block=BLOCK, seed=SEED):
    """Observed minus SEAPODYM-hist ENSO-adjusted trend over the same years, by a paired block bootstrap
    over years - resampling the same years for both series keeps the ENSO signal they share."""
    years = np.asarray(years)
    y_obs, y_mod = np.asarray(y_obs, float), np.asarray(y_mod, float)
    b_o, b_m = fit_trend(y_obs, years, idx, covars)["b"], fit_trend(y_mod, years, idx, covars)["b"]
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(nboot):
        ii = block_indices(len(years), block, rng)
        X = design(years[ii], idx, covars)
        X[:, 1] = years[ii] - CENTRE_YEAR
        draws.append(ols(y_obs[ii], X)[1] - ols(y_mod[ii], X)[1])
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return dict(obs=100 * b_o, model=100 * b_m, diff=100 * (b_o - b_m), lo=100 * lo, hi=100 * hi)


def r2_oos(y, pred):
    y, pred = np.asarray(y, float), np.asarray(pred, float)
    return float(1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2))


def h3_skill(y_obs, y_mod, years, idx, train=(1980, 1999), test=(2000, 2010), nboot=NBOOT, seed=SEED):
    """Out-of-sample skill on 2000-2010, both predictors fitted on 1980-1999 only.
      A: the ENSO/warm-pool regression, share ~ nino34 + nino34_lag + wpe (no trend term)
      B: SEAPODYM-hist, linearly calibrated: share ~ a + b * model_share
    dR2 = R2_B - R2_A; the interval resamples test years."""
    years = np.asarray(years)
    y_obs, y_mod = np.asarray(y_obs, float), np.asarray(y_mod, float)
    tr = (years >= train[0]) & (years <= train[1])
    te = (years >= test[0]) & (years <= test[1])
    XA_tr, XA_te = design(years[tr], idx, trend=False), design(years[te], idx, trend=False)
    pa = XA_te @ ols(y_obs[tr], XA_tr)
    XB_tr = np.column_stack([np.ones(tr.sum()), y_mod[tr]])
    XB_te = np.column_stack([np.ones(te.sum()), y_mod[te]])
    pb = XB_te @ ols(y_obs[tr], XB_tr)
    yt = y_obs[te]
    rng = np.random.default_rng(seed)
    d = []
    for _ in range(nboot):
        k = rng.integers(0, te.sum(), te.sum())
        if np.std(yt[k]) == 0:
            continue
        d.append(r2_oos(yt[k], pb[k]) - r2_oos(yt[k], pa[k]))
    lo, hi = np.percentile(d, [2.5, 97.5])
    ra, rb = r2_oos(yt, pa), r2_oos(yt, pb)
    return dict(r2_enso=ra, r2_seapodym=rb, d_r2=rb - ra, lo=float(lo), hi=float(hi),
                train=list(train), test=list(test), n_test=int(te.sum()))


def _one_sided_detect(y, X, col, alpha=ALPHA):
    """Detect a DECLINE: HAC t-test that the coefficient in column `col` is below zero."""
    r = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    return r.params[col] < 0 and r.pvalues[col] / 2 < alpha


def h4_power(y, years, idx, deltas_pp, nsim=1000, block=BLOCK, seed=SEED):
    """Injection-recovery on the observed record: strip the fitted trend, add a known linear decline of
    delta pp/yr, re-add block-resampled residuals, and see how often the same estimator detects it."""
    y = np.asarray(y, float)
    f = fit_trend(y, years, idx)
    base = f["fitted"] - f["beta"][1] * f["X"][:, 1]          # fitted values with the trend set to zero
    rng = np.random.default_rng(seed)
    curve = {}
    for d in deltas_pp:
        hits = 0
        for _ in range(nsim):
            ystar = base + (-abs(d) / 100) * f["X"][:, 1] + f["resid"][block_indices(len(y), block, rng)]
            hits += _one_sided_detect(ystar, f["X"], 1)
        curve[float(d)] = hits / nsim
    mde = next((d for d in sorted(curve) if curve[d] >= POWER), None)
    return dict(curve=curve, mde_pp=mde, power_at_tau=None)


def h4_detection_year(resid, tau, start=2011, first=1980, last_obs=2021, horizon=2100, nsim=1000, seed=SEED):
    """When does a decline at SEAPODYM's projected rate become detectable at 80% power?

    The projection begins in 2011, so the signal is a hinge, tau x max(0, year - 2011), on an otherwise
    flat series. Noise is AR(1) with the observed ENSO-adjusted residuals' standard deviation and lag-1
    autocorrelation - future analysts will have the ENSO indices, so the ENSO-explained variance is not
    added back. Returns the first year Y such that a record from `first` to Y detects the hinge (one-sided
    HAC test) in at least 80% of simulations."""
    resid = np.asarray(resid, float)
    sd, phi = float(np.std(resid, ddof=1)), float(np.corrcoef(resid[:-1], resid[1:])[0, 1])
    phi = max(min(phi, 0.95), -0.95)
    innov = sd * np.sqrt(1 - phi ** 2)
    rng = np.random.default_rng(seed)
    out = {}
    for Y in range(last_obs, horizon + 1, 1):
        yrs = np.arange(first, Y + 1)
        hinge = np.maximum(0, yrs - start).astype(float)
        X = np.column_stack([np.ones(len(yrs)), hinge])
        hits = 0
        for _ in range(nsim):
            e = np.empty(len(yrs))
            e[0] = rng.normal(0, sd)
            for t in range(1, len(yrs)):
                e[t] = phi * e[t - 1] + rng.normal(0, innov)
            hits += _one_sided_detect((tau / 100) * hinge + e, X, 1)
        out[Y] = hits / nsim
        if out[Y] >= POWER:
            return dict(year=Y, power=out[Y], resid_sd_pp=100 * sd, resid_ac1=phi, path=out)
    return dict(year=None, power=out[horizon], resid_sd_pp=100 * sd, resid_ac1=phi, path=out)
