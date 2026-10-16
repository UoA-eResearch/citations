"""Independent refit of segment trends: Prais-Winsten/Cochrane-Orcutt by hand, SARIMAX with AR(1) and AR(2) errors,
annual-mean OLS; residual ACF/Ljung-Box of the GLSAR fit; and an independent fleet combination."""
import json, sys, warnings
import numpy as np, pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import acf
warnings.filterwarnings("ignore")
fm = pd.read_csv(sys.argv[1]); prim = json.load(open(sys.argv[2]))["primary"]
fm["m"] = pd.PeriodIndex(fm.month, freq="M")

def design(d):
    t = (d.m.dt.year + (d.m.dt.month - 0.5) / 12).to_numpy(float); t = t - t.mean()
    X = pd.get_dummies(d.m.dt.month, prefix="mo", drop_first=True).astype(float).to_numpy()
    return np.column_stack([np.ones(len(d)), t, X])

def prais_winsten(y, X, iters=50):
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    rho = 0.0
    for _ in range(iters):
        e = y - X @ b
        rho_new = float(np.sum(e[1:] * e[:-1]) / np.sum(e[:-1] ** 2))
        ys = np.r_[np.sqrt(1 - rho_new**2) * y[0], y[1:] - rho_new * y[:-1]]
        Xs = np.vstack([np.sqrt(1 - rho_new**2) * X[0], X[1:] - rho_new * X[:-1]])
        b = np.linalg.lstsq(Xs, ys, rcond=None)[0]
        if abs(rho_new - rho) < 1e-8: break
        rho = rho_new
    es = ys - Xs @ b; s2 = es @ es / (len(y) - X.shape[1])
    cov = s2 * np.linalg.inv(Xs.T @ Xs)
    return b[1], np.sqrt(cov[1, 1]), rho

pct = lambda b: 100 * (np.exp(b) - 1)
print(f"{'field':12s} {'segment':18s} {'n':>4s} | {'reported':>8s} {'se_rep':>7s} | {'PW b':>8s} {'se':>7s} {'rho':>5s} | {'SARIMAX AR1':>11s} {'se':>7s} | {'AR2 b':>8s} {'se':>7s} {'phi1,phi2':>12s} | {'annual OLS':>10s} {'se':>6s} | ACF(2..6) of GLSAR resid ; LB p(12)")
rows = []
for field, r in prim["fields"].items():
    for s in r["segments"]:
        d = fm[(fm.field == field) & (fm.m >= pd.Period(s["start"], "M")) & (fm.m <= pd.Period(s["end"], "M"))].copy()
        hh = d.m.map(lambda p: p.days_in_month * 48)
        ok = (d.n >= 0.8 * hh) & (d.p95 > 0.2 * d.p95.median()) & (d.p95 > 0)
        d = d[ok]
        y = np.log(d.p95.to_numpy(float)); X = design(d)
        b_pw, se_pw, rho = prais_winsten(y, X)
        m1 = SARIMAX(y, exog=X, order=(1, 0, 0), trend="n").fit(disp=False)
        m2 = SARIMAX(y, exog=X, order=(2, 0, 0), trend="n").fit(disp=False)
        b1, se1 = m1.params[1], m1.bse[1]; b2, se2 = m2.params[1], m2.bse[1]
        phis = m2.params[-3:-1]
        # annual means (calendar years with >= 10 months)
        a = d.groupby(d.m.dt.year).agg(ly=("p95", lambda v: np.log(v).mean()), k=("p95", "size"))
        a = a[a.k >= 10]
        ao = sm.OLS(a.ly.to_numpy(), sm.add_constant((a.index.to_numpy(float) - a.index.to_numpy(float).mean()))).fit()
        # GLSAR replicate for residual diagnostics
        g = sm.GLSAR(y, X, rho=1).iterative_fit(maxiter=20)
        # residuals of the whitened model are g.resid? GLSAR.resid are on transformed scale; use wresid
        e = np.asarray(g.wresid)
        ac = acf(e, nlags=6, fft=False)[2:7]
        lb = acorr_ljungbox(e, lags=[12], return_df=True).lb_pvalue.iloc[0]
        se_rep = (s["ci"][1] - s["ci"][0]) / (2 * 1.96)
        print(f"{field:12s} {s['start']}..{s['end']} {len(d):4d} | {s['pct_per_yr']:+8.3f} {se_rep:7.3f} | {pct(b_pw):+8.3f} {pct(b_pw+se_pw)-pct(b_pw):7.3f} {rho:5.2f} | {pct(b1):+11.3f} {pct(b1+se1)-pct(b1):7.3f} | {pct(b2):+8.3f} {pct(b2+se2)-pct(b2):7.3f} {phis[0]:+5.2f},{phis[1]:+5.2f} | {pct(ao.params[1]):+10.3f} {pct(ao.params[1]+ao.bse[1])-pct(ao.params[1]):6.3f} | {np.round(ac,2)} ; {lb:.3f}")
        rows.append(dict(field=field, start=s["start"], end=s["end"], b_glsar=g.params[1], se_glsar=g.bse[1], b_ar2=b2, se_ar2=se2, rho_glsar=float(g.rho[0]) if hasattr(g,'rho') else np.nan, n=len(d), mean=d.p95.mean()))
# independent field + fleet combination from my GLSAR refits
R = pd.DataFrame(rows)
fields = {}
for f, g in R.groupby("field"):
    w = 1 / g.se_glsar**2; b = (w * g.b_glsar).sum() / w.sum(); se = 1 / np.sqrt(w.sum())
    w2 = 1 / g.se_ar2**2; b2 = (w2 * g.b_ar2).sum() / w2.sum(); se2 = 1 / np.sqrt(w2.sum())
    mw = (g["mean"] * g.n).sum() / g.n.sum()
    fields[f] = (b, se, b2, se2, mw)
print("\nfield combos (GLSAR refit | AR2 refit):")
for f, (b, se, b2, se2, mw) in fields.items():
    print(f"  {f:12s} {pct(b):+6.3f} [{pct(b-1.96*se):+6.3f},{pct(b+1.96*se):+6.3f}]  AR2 {pct(b2):+6.3f} [{pct(b2-1.96*se2):+6.3f},{pct(b2+1.96*se2):+6.3f}]  mw {mw:6.1f}")
W = np.array([v[4] for v in fields.values()]); W = W / W.sum()
B = np.array([v[0] for v in fields.values()]); S = np.array([v[1] for v in fields.values()])
print(f"fleet (indep corr=0): {pct(W@B):+.4f}  se->ci [{pct(W@B-1.96*np.sqrt((W*S)@(W*S))):+.3f},{pct(W@B+1.96*np.sqrt((W*S)@(W*S))):+.3f}]  perfect corr [{pct(W@B-1.96*(W@S)):+.3f},{pct(W@B+1.96*(W@S)):+.3f}]")
B2 = np.array([v[2] for v in fields.values()]); S2 = np.array([v[3] for v in fields.values()])
print(f"fleet AR2 errors (indep): {pct(W@B2):+.4f} [{pct(W@B2-1.96*np.sqrt((W*S2)@(W*S2))):+.3f},{pct(W@B2+1.96*np.sqrt((W*S2)@(W*S2))):+.3f}]")
print("weights", dict(zip(fields, np.round(W, 4))))
