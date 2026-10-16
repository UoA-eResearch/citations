#!/usr/bin/env python
"""Reviewer check (items 5, 6, 12): recompute H1's trend and intervals independently, probe the interval's
honesty under the observed autocorrelation, recompute H2/H3 and the 2010 step."""
import json
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
from statsmodels.tsa.stattools import acf, pacf
from statsmodels.stats.diagnostic import acorr_ljungbox

RUN = Path('/mnt/citations/research-lab/runs/blue-pacific-tuna-redistribution-detectability')
OUT = RUN / 'review/reviewer_checks'
obs = pd.read_csv(RUN / 'results/tables/observed_annual.csv', index_col=0); obs = obs[obs.convention == 'sw']
idx = pd.read_csv(RUN / 'results/tables/indices.csv', index_col=0)
mt = json.load(open(RUN / 'results/tables/model_targets.json'))
hist = pd.Series({int(k): v for k, v in mt['series']['hist_share'].items()})
TAU = 100 * mt['skipjack_share']['proj_trend_per_year_2011_2050_mean']
yrs = np.arange(1980, 2022); y = obs.loc[yrs, 'skj_catch_share'].to_numpy(float)
res = {}


def X_of(yrs, cov=('nino34', 'nino34_lag', 'wpe'), extra=None):
    cols = [np.ones(len(yrs)), yrs - 2000] + [idx.loc[yrs, c].to_numpy(float) for c in cov]
    if extra is not None: cols.append(extra)
    return np.column_stack(cols)


def block_boot(y, X, nboot=4000, block=4, seed=99, col=1):
    """moving-block (circular) residual bootstrap, vectorised"""
    n = len(y); P = np.linalg.pinv(X); beta = P @ y; fitted = X @ beta; e = y - fitted
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / block))
    starts = rng.integers(0, n, (nboot, nb))
    ii = ((starts[:, :, None] + np.arange(block)[None, None, :]) % n).reshape(nboot, -1)[:, :n]
    Ystar = fitted[None, :] + e[ii]                     # nboot x n
    B = Ystar @ P.T                                     # nboot x k
    return np.percentile(B[:, col], [2.5, 97.5])


X = X_of(yrs)
ols = sm.OLS(y, X).fit()
b = 100 * ols.params[1]
lo4, hi4 = 100 * block_boot(y, X, block=4)
lo8, hi8 = 100 * block_boot(y, X, block=8)
lo2, hi2 = 100 * block_boot(y, X, block=2)
hac = {L: 100 * np.array(sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': L}).conf_int()[1]) for L in (1, 3, 5, 8)}
hac_c = 100 * np.array(sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': 3, 'use_correction': True}).conf_int()[1])
e = ols.resid
ac = acf(e, nlags=6, fft=False); pac = pacf(e, nlags=6)
lb = acorr_ljungbox(e, lags=[4], return_df=True)
print(f'H1 trend {b:+.4f} pp/yr; block-4 boot ({lo4:+.3f},{hi4:+.3f}); block-2 ({lo2:+.3f},{hi2:+.3f}); block-8 ({lo8:+.3f},{hi8:+.3f})')
for L, v in hac.items(): print(f'   HAC maxlags {L}: ({v[0]:+.3f},{v[1]:+.3f})')
print(f'   HAC 3 with small-sample correction: ({hac_c[0]:+.3f},{hac_c[1]:+.3f})')
print(f'   OLS iid CI: ({100*ols.conf_int()[1][0]:+.3f},{100*ols.conf_int()[1][1]:+.3f}); R2 {ols.rsquared:.3f}; resid sd {100*np.std(e, ddof=5):.2f} pp')
print('   residual ACF lags1-6:', np.round(ac[1:], 3), ' PACF:', np.round(pac[1:], 3), ' Ljung-Box(4) p=%.4f' % lb.lb_pvalue.iloc[0])
# GLS AR(1) (iterative Cochrane-Orcutt via GLSAR)
gls = sm.GLSAR(y, X, rho=1).iterative_fit(maxiter=20)
gci = 100 * np.array(gls.conf_int()[1])
print(f'   GLSAR(1): rho {gls.model.rho[0]:.3f}, trend {100*gls.params[1]:+.4f} ({gci[0]:+.3f},{gci[1]:+.3f})')
# parametric AR(1) residual bootstrap
rng = np.random.default_rng(3); phi = ac[1]; sd = np.std(e, ddof=5); nb = 4000; n = len(y)
E = np.empty((nb, n)); E[:, 0] = rng.normal(0, sd, nb)
for t in range(1, n): E[:, t] = phi * E[:, t - 1] + rng.normal(0, sd * np.sqrt(1 - phi ** 2), nb)
P = np.linalg.pinv(X); B = (ols.fittedvalues[None, :] + E) @ P.T
plo, phi_ = 100 * np.percentile(B[:, 1], [2.5, 97.5])
print(f'   parametric AR(1) residual bootstrap: ({plo:+.3f},{phi_:+.3f})')
res['H1'] = dict(point=b, boot4=[lo4, hi4], boot2=[lo2, hi2], boot8=[lo8, hi8], hac={k: list(v) for k, v in hac.items()}, hac3_corrected=list(hac_c),
                 glsar=[gls.model.rho[0], 100 * gls.params[1], gci[0], gci[1]], ar1_param_boot=[plo, phi_], acf=list(ac[1:]), ljung_box_p=float(lb.lb_pvalue.iloc[0]))
print(f'   verdict vs tau {TAU:+.4f}: block-4 ->', 'Supported' if lo4 > TAU else ('Refuted' if hi4 < TAU else 'Inconclusive'))

# ---- coverage of the block-4 bootstrap and HAC(3) intervals when the noise is AR(1) with phi=0.56, sd=7.9 (n=42)
print('\nCoverage simulation (true trend 0, AR(1) noise phi=0.56 sd 7.9pp, real covariates, n=42):')
rng = np.random.default_rng(11); reps = 600; nboot = 600
cov_b = cov_h = cov_h8 = cov_iid = 0
for r in range(reps):
    eps = np.empty(n); eps[0] = rng.normal(0, 0.079)
    for t in range(1, n): eps[t] = 0.56 * eps[t - 1] + rng.normal(0, 0.079 * np.sqrt(1 - 0.56 ** 2))
    ys = X[:, 0] * 0.84 + 0.0 * X[:, 1] + 0.01 * X[:, 2] + eps
    lo, hi = block_boot(ys, X, nboot=nboot, block=4, seed=r)
    cov_b += lo <= 0 <= hi
    f3 = sm.OLS(ys, X).fit(cov_type='HAC', cov_kwds={'maxlags': 3}).conf_int()[1]; cov_h += f3[0] <= 0 <= f3[1]
    f8 = sm.OLS(ys, X).fit(cov_type='HAC', cov_kwds={'maxlags': 8}).conf_int()[1]; cov_h8 += f8[0] <= 0 <= f8[1]
    fi = sm.OLS(ys, X).fit().conf_int()[1]; cov_iid += fi[0] <= 0 <= fi[1]
print(f'   block-4 bootstrap {cov_b/reps:.3f}   HAC(3) {cov_h/reps:.3f}   HAC(8) {cov_h8/reps:.3f}   OLS iid {cov_iid/reps:.3f}   (nominal 0.95)')
res['coverage_ar1'] = dict(block4=cov_b / reps, hac3=cov_h / reps, hac8=cov_h8 / reps, iid=cov_iid / reps)
# ... and with white noise, as test_analysis.py used
cov_b = cov_h = 0
for r in range(300):
    ys = 0.84 + rng.normal(0, 0.079, n)
    lo, hi = block_boot(ys, X, nboot=nboot, block=4, seed=r); cov_b += lo <= 0 <= hi
    f3 = sm.OLS(ys, X).fit(cov_type='HAC', cov_kwds={'maxlags': 3}).conf_int()[1]; cov_h += f3[0] <= 0 <= f3[1]
print(f'   with white noise instead: block-4 {cov_b/300:.3f}  HAC(3) {cov_h/300:.3f}')
res['coverage_white'] = dict(block4=cov_b / 300, hac3=cov_h / 300)

# ---- the 2010 step
Xs = X_of(yrs, extra=(yrs >= 2010).astype(float))
fs = sm.OLS(y, Xs).fit(cov_type='HAC', cov_kwds={'maxlags': 3})
ci = fs.conf_int()
print(f'\nstep-2010 model: step {100*fs.params[5]:+.2f} pp HAC({100*ci[5][0]:+.2f},{100*ci[5][1]:+.2f}); trend {100*fs.params[1]:+.4f} HAC({100*ci[1][0]:+.3f},{100*ci[1][1]:+.3f}); resid sd {100*np.std(fs.resid, ddof=6):.2f}')
slo, shi = 100 * block_boot(y, Xs, block=4, col=5)
print(f'   step block-4 bootstrap ({slo:+.2f},{shi:+.2f})')
# a step in 2011 instead (PNA 3IA eastern pockets from 2011), and both
for sy in (2009, 2011):
    Xk = X_of(yrs, extra=(yrs >= sy).astype(float)); fk = sm.OLS(y, Xk).fit(cov_type='HAC', cov_kwds={'maxlags': 3})
    print(f'   step at {sy}: {100*fk.params[5]:+.2f} pp; trend {100*fk.params[1]:+.4f}')
res['step2010'] = dict(step=100 * fs.params[5], hac=[100 * ci[5][0], 100 * ci[5][1]], trend=100 * fs.params[1], trend_hac=[100 * ci[1][0], 100 * ci[1][1]], resid_sd=100 * np.std(fs.resid, ddof=6))
# ENSO explains how much?
r2_none = sm.OLS(y, X_of(yrs, cov=())).fit().rsquared
print(f'   R2 with trend only {r2_none:.3f}; with trend+ENSO {ols.rsquared:.3f}; with step too {sm.OLS(y, Xs).fit().rsquared:.3f}')

# ---- H2 (paired block bootstrap over years) and H3
hy = np.arange(1980, 2011)
def trend(yv, yrs_): return np.linalg.lstsq(X_of(yrs_), yv, rcond=None)[0][1]
for col in ['skj_catch_share', 'skj_density_share', 'skj_density_share_una']:
    yo = obs.loc[hy, col].to_numpy(float); ym = hist.loc[hy].to_numpy(float)
    bo, bm = trend(yo, hy), trend(ym, hy)
    rng = np.random.default_rng(5); d = []
    for _ in range(3000):
        starts = rng.integers(0, 31, 8); ii = np.concatenate([(s + np.arange(4)) % 31 for s in starts])[:31]
        Xb = X_of(hy[ii]); d.append(np.linalg.lstsq(Xb, yo[ii], rcond=None)[0][1] - np.linalg.lstsq(Xb, ym[ii], rcond=None)[0][1])
    lo, hi = 100 * np.percentile(d, [2.5, 97.5])
    print(f'H2 {col:24s} obs {100*bo:+.3f} model {100*bm:+.3f} diff {100*(bo-bm):+.3f} ({lo:+.3f},{hi:+.3f})')
    res[f'H2_{col}'] = dict(obs=100 * bo, model=100 * bm, diff=100 * (bo - bm), lo=lo, hi=hi)
    # the same over 1990-2010 only (after the fleet's development years)
    h2 = np.arange(1990, 2011); yo2 = obs.loc[h2, col].to_numpy(float); ym2 = hist.loc[h2].to_numpy(float)
    f_o = sm.OLS(yo2, X_of(h2)).fit(cov_type='HAC', cov_kwds={'maxlags': 3}); f_m = sm.OLS(ym2, X_of(h2)).fit(cov_type='HAC', cov_kwds={'maxlags': 3})
    print(f'      1990-2010: obs {100*f_o.params[1]:+.3f} HAC({100*f_o.conf_int()[1][0]:+.3f},{100*f_o.conf_int()[1][1]:+.3f})  model {100*f_m.params[1]:+.3f}')
    res[f'H2_{col}_1990_2010'] = dict(obs=100 * f_o.params[1], obs_hac=[100 * f_o.conf_int()[1][0], 100 * f_o.conf_int()[1][1]], model=100 * f_m.params[1])
# H3
tr = (hy >= 1980) & (hy <= 1999); te = (hy >= 2000) & (hy <= 2010)
yo = obs.loc[hy, 'skj_catch_share'].to_numpy(float); ym = hist.loc[hy].to_numpy(float)
XA = np.column_stack([np.ones(31), idx.loc[hy, 'nino34'], idx.loc[hy, 'nino34_lag'], idx.loc[hy, 'wpe']])
pa = XA[te] @ np.linalg.lstsq(XA[tr], yo[tr], rcond=None)[0]
XB = np.column_stack([np.ones(31), ym]); cb = np.linalg.lstsq(XB[tr], yo[tr], rcond=None)[0]; pb = XB[te] @ cb
r2 = lambda yt, p: 1 - np.sum((yt - p) ** 2) / np.sum((yt - yt.mean()) ** 2)
print(f'H3: R2 ENSO {r2(yo[te], pa):+.3f}, R2 SEAPODYM {r2(yo[te], pb):+.3f}, dR2 {r2(yo[te], pb)-r2(yo[te], pa):+.3f}; SEAPODYM calibration slope {cb[1]:+.3f} (train corr {np.corrcoef(ym[tr], yo[tr])[0,1]:+.3f}); test corr {np.corrcoef(ym[te], yo[te])[0,1]:+.3f}')
print(f'    RMSE: ENSO {100*np.sqrt(np.mean((yo[te]-pa)**2)):.2f} pp, SEAPODYM {100*np.sqrt(np.mean((yo[te]-pb)**2)):.2f} pp, test-mean {100*np.std(yo[te]):.2f} pp, train-mean as forecast {100*np.sqrt(np.mean((yo[te]-yo[tr].mean())**2)):.2f} pp')
res['H3'] = dict(r2_enso=r2(yo[te], pa), r2_sea=r2(yo[te], pb), calib_slope=float(cb[1]), train_corr=float(np.corrcoef(ym[tr], yo[tr])[0, 1]))
json.dump(res, open(OUT / 'check_h1.json', 'w'), indent=1, default=float)
