#!/usr/bin/env python
"""Reviewer check (item 7): the power and detection-year claims. Vectorised Newey-West t-tests so that the
sensitivities (AR(1) coefficient, residual SD, hinge start, baseline length, projected rate, seed) can be run."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm

RUN = Path('/mnt/citations/research-lab/runs/blue-pacific-tuna-redistribution-detectability')
OUT = RUN / 'review/reviewer_checks'
obs = pd.read_csv(RUN / 'results/tables/observed_annual.csv', index_col=0); obs = obs[obs.convention == 'sw']
idx = pd.read_csv(RUN / 'results/tables/indices.csv', index_col=0)
mt = json.load(open(RUN / 'results/tables/model_targets.json'))
TAU = 100 * mt['skipjack_share']['proj_trend_per_year_2011_2050_mean']          # -0.1174
TAU30 = 100 * mt['skipjack_share']['proj_trend_per_year_2011_2030_mean']        # -0.336
yrs = np.arange(1980, 2022); y = obs.loc[yrs, 'skj_catch_share'].to_numpy(float)
res = {}


def hac_t(X, Y, col, L=3):
    """Newey-West (Bartlett, maxlags L, no small-sample correction) t-statistics of beta[col], for every column of Y."""
    n, k = X.shape
    A = np.linalg.inv(X.T @ X)
    B = A @ X.T @ Y                                  # k x S
    E = Y - X @ B                                    # n x S
    U = X[:, None, :] * E[:, :, None]                # n x S x k
    S = np.einsum('tsi,tsj->sij', U, U)
    for l in range(1, L + 1):
        w = 1 - l / (L + 1)
        G = np.einsum('tsi,tsj->sij', U[l:], U[:-l])
        S += w * (G + np.transpose(G, (0, 2, 1)))
    V = np.einsum('ij,sjk,kl->sil', A, S, A)
    return B[col] / np.sqrt(V[:, col, col])


# verify against statsmodels
Xv = np.column_stack([np.ones(42), yrs - 2000, idx.loc[yrs, 'nino34'], idx.loc[yrs, 'nino34_lag'], idx.loc[yrs, 'wpe']])
t_sm = sm.OLS(y, Xv).fit(cov_type='HAC', cov_kwds={'maxlags': 3}).tvalues[1]
t_me = hac_t(Xv, y[:, None], 1)[0]
print(f'HAC t check: statsmodels {t_sm:.6f} mine {t_me:.6f}')
assert abs(t_sm - t_me) < 1e-6


def ar1(n, S, sd, phi, rng):
    E = np.empty((n, S)); E[0] = rng.normal(0, sd, S)
    innov = sd * np.sqrt(1 - phi ** 2)
    for t in range(1, n): E[t] = phi * E[t - 1] + rng.normal(0, innov, S)
    return E


def detection_year(sd_pp, phi, rate_pp, start=2011, first=1980, last=2021, horizon=2160, nsim=3000, seed=1, calibrated=True, step=1):
    rng = np.random.default_rng(seed); path = {}
    for Y in range(last, horizon + 1, step):
        yy = np.arange(first, Y + 1); n = len(yy)
        hinge = np.maximum(0, yy - start).astype(float)
        X = np.column_stack([np.ones(n), hinge])
        t0 = hac_t(X, ar1(n, nsim, sd_pp / 100, phi, rng), 1)
        t1 = hac_t(X, (rate_pp / 100) * hinge[:, None] + ar1(n, nsim, sd_pp / 100, phi, rng), 1)
        crit = np.percentile(t0, 5) if calibrated else -1.6449
        p = float(np.mean(t1 < crit)); path[Y] = p
        if p >= 0.8: return Y, path
    return None, path


# residual quantities from the study's primary fit
f = sm.OLS(y, Xv).fit(); e = f.resid
sd_full = 100 * np.std(e, ddof=1); phi_full = np.corrcoef(e[:-1], e[1:])[0, 1]
Xs = np.column_stack([Xv, (yrs >= 2010).astype(float)]); es = sm.OLS(y, Xs).fit().resid
sd_step = 100 * np.std(es, ddof=1); phi_step = np.corrcoef(es[:-1], es[1:])[0, 1]
post = y[yrs >= 2010]; sd_post = 100 * np.std(post - post.mean(), ddof=1)
X90 = Xs[yrs >= 1990]; e90 = sm.OLS(y[yrs >= 1990], X90).fit().resid; sd_90 = 100 * np.std(e90, ddof=1); phi_90 = np.corrcoef(e90[:-1], e90[1:])[0, 1]
print(f'residual sd/phi: full-sample ENSO-adjusted {sd_full:.2f}/{phi_full:.2f}; with 2010 step {sd_step:.2f}/{phi_step:.2f}; 1990-2021 with step {sd_90:.2f}/{phi_90:.2f}; raw post-2010 sd {sd_post:.2f}')
res['resid'] = dict(sd_full=sd_full, phi_full=phi_full, sd_step=sd_step, phi_step=phi_step, sd_90=sd_90, phi_90=phi_90, sd_post2010=sd_post)

scen = [
    ('baseline (study): sd 7.50 phi 0.56, hinge 2011, record from 1980', dict(sd_pp=sd_full, phi=phi_full, rate_pp=TAU)),
    ('seed 2', dict(sd_pp=sd_full, phi=phi_full, rate_pp=TAU, seed=2)),
    ('seed 3', dict(sd_pp=sd_full, phi=phi_full, rate_pp=TAU, seed=3)),
    ('white noise phi=0', dict(sd_pp=sd_full, phi=0.0, rate_pp=TAU)),
    ('phi=0.3', dict(sd_pp=sd_full, phi=0.3, rate_pp=TAU)),
    ('phi=0.75', dict(sd_pp=sd_full, phi=0.75, rate_pp=TAU)),
    ('sd from step-adjusted residuals (6.1)', dict(sd_pp=sd_step, phi=phi_step, rate_pp=TAU)),
    ('sd/phi from 1990-2021 step-adjusted residuals', dict(sd_pp=sd_90, phi=phi_90, rate_pp=TAU)),
    ('sd 5.0 phi 0.56 (post-2010 variability)', dict(sd_pp=5.0, phi=phi_full, rate_pp=TAU)),
    ('record starts 2011 (no 1980-2010 baseline)', dict(sd_pp=sd_full, phi=phi_full, rate_pp=TAU, first=2011)),
    ('record starts 1990', dict(sd_pp=sd_full, phi=phi_full, rate_pp=TAU, first=1990)),
    ('rate = model 2011-2030 mean (-0.336)', dict(sd_pp=sd_full, phi=phi_full, rate_pp=TAU30)),
    ('rate = steepest ESM, IPSL (-0.216)', dict(sd_pp=sd_full, phi=phi_full, rate_pp=100 * mt['skipjack_share']['proj_trend_per_year_2011_2050']['IPSL'])),
    ('fishery-independent index with SEAPODYM-like noise (sd 1.26, phi 0.63)', dict(sd_pp=1.26, phi=0.63, rate_pp=TAU)),
    ('uncalibrated (nominal 1.645) baseline', dict(sd_pp=sd_full, phi=phi_full, rate_pp=TAU, calibrated=False)),
]
print('\nDetection year (first year with >=80% power), calibrated one-sided 5% test unless stated:')
res['detection'] = {}
for name, kw in scen:
    Y, path = detection_year(**kw)
    # the power at a few checkpoints
    chk = {k: round(path[k], 2) for k in (2030, 2050, 2070, 2090) if k in path}
    print(f'  {name:70s} -> {Y}   power at {chk}')
    res['detection'][name] = dict(year=Y, checkpoints=chk)

# ---- power on the 42-year record: injection-recovery with block-resampled residuals (nominal and calibrated)
print('\nInjection-recovery power on 1980-2021 (block-4 bootstrap residuals), one-sided:')
P = np.linalg.pinv(Xv); beta = P @ y; fitted = Xv @ beta; e = y - fitted
base = fitted - beta[1] * Xv[:, 1]
rng = np.random.default_rng(7); S = 6000; n = 42
def resample(S):
    starts = rng.integers(0, n, (S, 11)); ii = ((starts[:, :, None] + np.arange(4)) % n).reshape(S, -1)[:, :n]
    return e[ii].T                                   # n x S
t0 = hac_t(Xv, base[:, None] + resample(S), 1)
crit = np.percentile(t0, 5)
print(f'  size of nominal test at delta=0: {np.mean(t0 < -1.6449):.3f}; calibrated critical t {crit:.3f}')
res['power42'] = {}
for d in (0.0, abs(TAU), 0.2, 0.3, 0.325, 0.4, 0.425, 0.5):
    t1 = hac_t(Xv, base[:, None] - (d / 100) * Xv[:, 1][:, None] + resample(S), 1)
    pn, pc = float(np.mean(t1 < -1.6449)), float(np.mean(t1 < crit))
    print(f'  delta {d:.3f} pp/yr: nominal power {pn:.3f}  calibrated {pc:.3f}')
    res['power42'][str(round(d, 3))] = dict(nominal=pn, calibrated=pc)
# the question the plain-language section implies: a decline at tau that BEGAN in 2011, seen with data to 2021
hinge = np.maximum(0, yrs - 2011).astype(float)
Xh = np.column_stack([Xv, hinge])
t0 = hac_t(Xh, base[:, None] + resample(S), 5); crit_h = np.percentile(t0, 5)
t1 = hac_t(Xh, base[:, None] + (TAU / 100) * hinge[:, None] + resample(S), 5)
print(f'  hinge from 2011 at tau, record to 2021: nominal power {np.mean(t1 < -1.6449):.3f}, calibrated {np.mean(t1 < crit_h):.3f}')
res['power_hinge_2011_to_2021'] = dict(nominal=float(np.mean(t1 < -1.6449)), calibrated=float(np.mean(t1 < crit_h)))
# with the step-adjusted residuals as the noise
Ps = np.linalg.pinv(Xs); bs = Ps @ y; fs = Xs @ bs; es = y - fs; bases = fs - bs[1] * Xs[:, 1]
def resample_s(S):
    starts = rng.integers(0, n, (S, 11)); ii = ((starts[:, :, None] + np.arange(4)) % n).reshape(S, -1)[:, :n]
    return es[ii].T
t0 = hac_t(Xs, bases[:, None] + resample_s(S), 1); crit_s = np.percentile(t0, 5)
res['power42_step'] = {}
for d in (abs(TAU), 0.3, 0.4):
    t1 = hac_t(Xs, bases[:, None] - (d / 100) * Xs[:, 1][:, None] + resample_s(S), 1)
    print(f'  with the 2010 step as a covariate, delta {d:.3f}: nominal {np.mean(t1 < -1.6449):.3f} calibrated {np.mean(t1 < crit_s):.3f}')
    res['power42_step'][str(round(d, 3))] = dict(nominal=float(np.mean(t1 < -1.6449)), calibrated=float(np.mean(t1 < crit_s)))
json.dump(res, open(OUT / 'check_power.json', 'w'), indent=1, default=float)
