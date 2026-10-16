"""Coverage of GLSAR(rho=1 iterative) trend intervals vs SARIMAX-AR(1) ML intervals at the autocorrelations seen
in the real segments (0.25-0.94) and their lengths; monthly seasonal dummies included as in analysis.py."""
import numpy as np, pandas as pd, statsmodels.api as sm, warnings
from statsmodels.tsa.statespace.sarimax import SARIMAX
warnings.filterwarnings("ignore")
rng = np.random.default_rng(7)
def design(n):
    m = pd.period_range("2000-01", periods=n, freq="M")
    t = np.array(m.year + (m.month - 0.5) / 12, dtype=float); t = t - t.mean()
    X = pd.get_dummies(m.month, drop_first=True).astype(float).to_numpy()
    return np.column_stack([np.ones(n), t, X])
print(f"{'n':>4s} {'phi':>5s} | {'GLSAR cover':>11s} {'median se':>9s} | {'SARIMAX cover':>13s} {'median se':>9s} | {'OLS cover':>9s}  (true se of GLSAR b, empirical)")
for n, phi in [(93, 0.67), (150, 0.25), (194, 0.74), (148, 0.87), (318, 0.94), (225, 0.48), (97, 0.71)]:
    X = design(n); b0 = np.log(0.99) 
    cg = cs = co = 0; seg = []; ses = []; bs = []
    R = 300
    for _ in range(R):
        e = np.zeros(n); u = rng.normal(0, 0.03 * np.sqrt(1 - phi**2), n); e[0] = rng.normal(0, 0.03)
        for i in range(1, n): e[i] = phi * e[i-1] + u[i]
        y = X[:, 1] * b0 + e
        g = sm.GLSAR(y, X, rho=1).iterative_fit(maxiter=20)
        cg += abs(g.params[1] - b0) < 1.96 * g.bse[1]; seg.append(g.bse[1]); bs.append(g.params[1])
        s = SARIMAX(y, exog=X, order=(1, 0, 0), trend="n").fit(disp=False)
        cs += abs(s.params[1] - b0) < 1.96 * s.bse[1]; ses.append(s.bse[1])
        o = sm.OLS(y, X).fit(); co += abs(o.params[1] - b0) < 1.96 * o.bse[1]
    print(f"{n:4d} {phi:5.2f} | {cg/R:11.3f} {100*np.median(seg):9.3f} | {cs/R:13.3f} {100*np.median(ses):9.3f} | {co/R:9.3f}  {100*np.std(bs):.3f}")
