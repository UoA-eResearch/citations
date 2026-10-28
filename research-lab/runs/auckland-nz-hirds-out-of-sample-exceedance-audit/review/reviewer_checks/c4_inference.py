"""Reviewer check 4: the 9-block water-year bootstrap (reproduce; alternatives; coverage by simulation) and the storm
bootstrap's variance."""
import json
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-hirds-out-of-sample-exceedance-audit")
T = RUN / "results" / "tables"
y = pd.read_csv(T / "year_by_year.csv"); o, n = y.exceed.to_numpy(float), y.gauges.to_numpy(float); e = 0.1 * n
B = 2000
def pct_boot(o, e, rng, B=B):
    k = rng.integers(0, len(o), (B, len(o))); d = o[k].sum(1) / e[k].sum(1); return np.percentile(d, [2.5, 97.5]), d
rng = np.random.default_rng(20261028)
ci, d = pct_boot(o, e, rng)
print("reproduced block bootstrap (same seed, same draw order):", np.round(ci, 3), "| reported 0.781-2.346")
print("yearly O/E:", np.round(o / e, 2))
r = o / e
print("t-interval on the 9 yearly O/E (unweighted):", np.round(stats.t.interval(0.95, 8, loc=r.mean(), scale=r.std(ddof=1) / 3), 3))
lr = np.log(r); m, s = lr.mean(), lr.std(ddof=1) / 3
print("t-interval on log O/E, back-transformed:", np.round(np.exp(stats.t.interval(0.95, 8, loc=m, scale=s)), 3), "(geometric mean %.2f)" % np.exp(m))
# ratio estimator with a linearised (delta) variance over 9 clusters, t(8)
R = o.sum() / e.sum(); u = (o - R * e) / e.mean(); se = u.std(ddof=1) / 3
print("ratio estimator, cluster-robust t(8) interval:", np.round(R + np.array(stats.t.interval(0.95, 8)) * se, 3))
# studentised / BCa-ish: bootstrap-t
boots = []
for _ in range(B):
    k = rng.integers(0, 9, 9); ob, eb = o[k], e[k]; Rb = ob.sum() / eb.sum(); ub = (ob - Rb * eb) / eb.mean(); seb = ub.std(ddof=1) / 3
    boots.append((Rb - R) / seb if seb > 0 else np.nan)
q = np.nanpercentile(boots, [2.5, 97.5])
print("bootstrap-t interval:", np.round([R - q[1] * se, R - q[0] * se], 3))
# overdispersion: Poisson-lognormal year effects, method of moments
var_r = r.var(ddof=1); pois = np.mean(R / e)       # Poisson part of var(O/E) ~ R/e_y
tau2 = max(var_r - pois, 0); print("between-year variance of O/E %.3f, of which Poisson ~%.3f; extra-Poisson %.3f (CV %.2f)" % (var_r, pois, tau2, np.sqrt(tau2) / R))
# coverage simulation: 9 years, counts Poisson with lognormal year effects matched to the data; percentile bootstrap coverage
sim_rng = np.random.default_rng(1); cover = 0; width = []; S = 2000
cv = np.sqrt(tau2) / R; sig = np.sqrt(np.log(1 + cv ** 2)); mu = np.log(R) - sig ** 2 / 2
for _ in range(S):
    th = np.exp(sim_rng.normal(mu, sig, 9)); os_ = sim_rng.poisson(th * e)
    k = sim_rng.integers(0, 9, (B // 4, 9)); dd = os_[k].sum(1) / e[k].sum(1); lo, hi = np.percentile(dd, [2.5, 97.5])
    cover += lo <= R <= hi; width.append(hi - lo)
print("simulated coverage of the 9-block percentile bootstrap at the fitted dispersion: %.3f (nominal 0.95); mean width %.2f (observed %.2f)" % (cover / S, np.mean(width), ci[1] - ci[0]))
# same simulation, for the probability the preregistered rule would call Supported / Refuted under the fitted model and under the null (R=1)
for Rtrue, lab in ((R, "fitted O/E"), (1.0, "null O/E=1"), (1.3, "O/E=1.3")):
    mu_ = np.log(Rtrue) - sig ** 2 / 2; sup = ref = 0
    for _ in range(S):
        th = np.exp(sim_rng.normal(mu_, sig, 9)); os_ = sim_rng.poisson(th * e); Rs = os_.sum() / e.sum()
        k = sim_rng.integers(0, 9, (B // 4, 9)); dd = os_[k].sum(1) / e[k].sum(1); lo, hi = np.percentile(dd, [2.5, 97.5])
        sup += (Rs >= 1.3) and (lo > 1.0); ref += hi < 1.3
    print(f"   under {lab}: P(Supported) = {sup / S:.3f}, P(Refuted) = {ref / S:.3f}")
# storm bootstrap as coded vs a version that also resamples the number of storms (Poisson)
sizes = np.array([1] * 34 + [2] * 15 + [3] * 8 + [4] * 2 + [5] * 3 + [7] * 2 + [8, 9, 10] + [13] * 2 + [28, 52]); assert sizes.sum() == 258 and len(sizes) == 71
E_ = 0.1 * 1729; sd = np.random.default_rng(3)
as_coded = np.array([sizes[sd.integers(0, 71, 71)].sum() for _ in range(B)]) / E_
poisson_n = np.array([sizes[sd.integers(0, 71, sd.poisson(71))].sum() for _ in range(B)]) / E_
print("storm bootstrap as coded: %.3f-%.3f (SD %.3f); with Poisson storm count: %.3f-%.3f (SD %.3f)" % (*np.percentile(as_coded, [2.5, 97.5]), as_coded.std(), *np.percentile(poisson_n, [2.5, 97.5]), poisson_n.std()))
print("compound-Poisson SD of O/E implied by the cluster sizes: %.3f; year-block bootstrap SD: %.3f" % (np.sqrt(71 * np.mean(sizes ** 2)) / E_, d.std()))
