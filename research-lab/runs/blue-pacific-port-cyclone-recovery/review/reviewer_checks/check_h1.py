"""Reviewer checks 1, 5, 6, 8: independent recomputation of the two-part AIC (own Weibull-AFT and logit likelihoods in
scipy, not lifelines/statsmodels), a port-level permutation null for dAIC under the real storm clustering, the
UNGUARDED H2 (what the d12c3f0 code would have reported with cluster_col removed), a pooled two-part estimand for H2,
the share/SIDS collinearity, and the frozen forecast re-derived from forecast_model.json."""
import sys, json, hashlib
from pathlib import Path
import numpy as np, pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
import analysis as A
import score_forecast as S
pd.set_option("display.width", 220)

r = A.load("primary")
print("n", len(r), "storms", r.sid.nunique(), "disrupted", int(r.D_.sum()))
print("alpha exact values (unique, rounded 6):", sorted(set(np.round(r.alpha, 6)))[:12], "...; n alpha<=1e-4:", int((r.alpha <= 1e-4 + 1e-12).sum()))

def logit_ll(beta, X, y):
    z = X @ beta
    return np.sum(y * z - np.logaddexp(0, z))

def fit_logit(X, y):
    res = minimize(lambda b: -logit_ll(b, X, y), np.zeros(X.shape[1]), method="BFGS", options=dict(gtol=1e-8, maxiter=2000))
    return res.x, -res.fun

def weib_ll(theta, X, tt, ee):
    beta, lrho = theta[:-1], theta[-1]
    rho = np.exp(lrho)
    llam = X @ beta
    z = (np.log(tt) - llam) * rho          # log((t/lam)^rho)
    return np.sum(ee * (lrho - llam + (rho - 1) * (np.log(tt) - llam)) - np.exp(z))

def fit_weib(X, tt, ee):
    th0 = np.zeros(X.shape[1] + 1); th0[0] = np.log(tt.mean())
    res = minimize(lambda th: -weib_ll(th, X, tt, ee), th0, method="BFGS", options=dict(gtol=1e-8, maxiter=5000))
    res2 = minimize(lambda th: -weib_ll(th, X, tt, ee), res.x, method="Nelder-Mead", options=dict(xatol=1e-10, fatol=1e-12, maxiter=20000))
    th = res2.x if res2.fun < res.fun else res.x
    return th, -min(res.fun, res2.fun)

def two_part_aic(d, covs):
    Xa = np.column_stack([np.ones(len(d))] + [d[c].to_numpy(float) for c in covs])
    ba, lla = fit_logit(Xa, d.D_.to_numpy(float))
    dd = d[d.D_]
    Xb = np.column_stack([np.ones(len(dd))] + [dd[c].to_numpy(float) for c in covs])
    tb, llb = fit_weib(Xb, dd.T_.clip(lower=1).to_numpy(float), dd.E_.to_numpy(float))
    aic_a = -2 * lla + 2 * Xa.shape[1]; aic_b = -2 * llb + 2 * (Xb.shape[1] + 1)
    return aic_a, aic_b, ba, tb

aa0, ab0, _, _ = two_part_aic(r, A.BASE)
aa1, ab1, ba1, tb1 = two_part_aic(r, A.BASE + ["share"])
print(f"\n[H1 independent] AIC base: A {aa0:.3f} B {ab0:.3f} sum {aa0+ab0:.3f}; full: A {aa1:.3f} B {ab1:.3f} sum {aa1+ab1:.3f}")
print(f"  dAIC total {aa0+ab0-aa1-ab1:.3f}  part A {aa0-aa1:.3f}  part B {ab0-ab1:.3f}")
print(f"  part A share coef {ba1[-1]:.4f} -> OR per 10pp {np.exp(0.1*ba1[-1]):.4f};  part B share coef {tb1[-2]:.4f} -> TR {np.exp(tb1[-2]):.3f}")
# study's own numbers for comparison
sa0, sb0 = A.part_a(r, A.BASE), A.part_b(r, A.BASE)
sa1, sb1 = A.part_a(r, A.BASE + ["share"]), A.part_b(r, A.BASE + ["share"])
print(f"  study (statsmodels/lifelines): A {sa0.aic:.3f}/{sa1.aic:.3f}  B {sb0.AIC_:.3f}/{sb1.AIC_:.3f}  dAIC {sa0.aic+sb0.AIC_-sa1.aic-sb1.AIC_:.3f}")
print("  naive (non-clustered) Wald p for share in part A:", round(float(sm_p := __import__('statsmodels.api', fromlist=['x']).Logit(r.D_.astype(float), __import__('statsmodels.api', fromlist=['x']).add_constant(r[A.BASE+['share']].astype(float))).fit(disp=0).pvalues['share']), 4),
      "; clustered p:", round(float(sa1.pvalues["share"]), 4), "; LR p (1 df) for part A:", round(float(1 - __import__('scipy.stats').stats.chi2.cdf(aa0 - aa1 + 2, 1)), 4))

# port-level permutation null for dAIC: shuffle share across PORTS (keeps storm clustering and port repeats)
rng = np.random.default_rng(11)
port_share = r.groupby("portid").share.first()
null = []
for i in range(400):
    perm = pd.Series(rng.permutation(port_share.to_numpy()), index=port_share.index)
    rp = r.copy(); rp["share"] = rp.portid.map(perm)
    a0, b0, _, _ = two_part_aic(rp, A.BASE); a1, b1, _, _ = two_part_aic(rp, A.BASE + ["share"])
    null.append(a0 + b0 - a1 - b1)
null = np.array(null)
obs = aa0 + ab0 - aa1 - ab1
print(f"\n[permutation] dAIC null (share shuffled across ports, 400 draws): mean {null.mean():.2f}, 90th {np.percentile(null,90):.2f}, 95th {np.percentile(null,95):.2f}, 99th {np.percentile(null,99):.2f}; P(null >= {obs:.2f}) = {(null >= obs).mean():.3f}")
print(f"  share of permutations reaching dAIC >= 2: {(null >= 2).mean():.3f}; >= 10: {(null >= 10).mean():.3f}")

# share vs sids: joint model, and share's distribution
import statsmodels.api as sm
Xj = sm.add_constant(r[A.BASE + ["share", "sids"]].astype(float))
mj = sm.Logit(r.D_.astype(float), Xj).fit(disp=0, cov_type="cluster", cov_kwds={"groups": r.sid.astype("category").cat.codes})
print(f"\n[share & sids together, part A] share {mj.params['share']:.3f} (p {mj.pvalues['share']:.3f}), sids {mj.params['sids']:.3f} (p {mj.pvalues['sids']:.3f})")
Xs = sm.add_constant(r[A.BASE].astype(float)); 
print("  corr(share, sids) =", round(np.corrcoef(r.share, r.sids)[0, 1], 3), "; share>0.3: SIDS", int(((r.share > 0.3) & (r.sids == 1)).sum()), "non-SIDS", int(((r.share > 0.3) & (r.sids == 0)).sum()))
print("  non-SIDS ports with share > 0.3:", r[(r.share > 0.3) & (r.sids == 0)][["portname", "ISO3", "storm", "share", "D_"]].to_string(index=False))
# share is a within-country concentration: number of PortWatch ports per country for the events
ports = pd.read_csv(RUN / "data/raw/portwatch/ports.csv")
nports = ports.groupby("ISO3").size()
r["n_ports_country"] = r.ISO3.map(nports)
print("  corr(share, log n_ports_country) =", round(np.corrcoef(r.share, np.log(r.n_ports_country))[0, 1], 3))
Xn = sm.add_constant(r[A.BASE + ["share"]].assign(log_nports=np.log(r.n_ports_country)).astype(float))
mn = sm.Logit(r.D_.astype(float), Xn).fit(disp=0, cov_type="cluster", cov_kwds={"groups": r.sid.astype("category").cat.codes})
print(f"  part A with log(ports in country) added: share {mn.params['share']:.3f} (p {mn.pvalues['share']:.3f}), log_nports {mn.params['log_nports']:.3f} (p {mn.pvalues['log_nports']:.3f})")
# basin / country-group confound: non-SIDS disrupted are China/US/Japan typhoon & hurricane landfalls
r["region"] = np.where(r.sids == 1, "SIDS", np.where(r.ISO3.isin(["CHN", "HKG", "MAC", "TWN", "JPN", "VNM", "PHL"]), "E/SE Asia", np.where(r.ISO3 == "USA", "USA", "other")))
print("\n  disrupted by region:", r.groupby("region").agg(n=("D_", "size"), disrupted=("D_", "sum"), median_calls=("mean_calls", "median"), median_km=("closest_km", "median")).to_string())

# UNGUARDED H2: what the preregistered code (d12c3f0) would have given with only cluster_col removed
from lifelines import WeibullAFTFitter
d = r[r.D_].copy(); d["T_"] = d.T_.clip(lower=1)
f = WeibullAFTFitter().fit(d[A.BASE + ["sids", "T_", "E_"]], duration_col="T_", event_col="E_")
s = f.summary.loc[("lambda_", "sids")]
print(f"\n[H2 unguarded, lifelines CI on 1 disrupted SIDS event] TR {np.exp(s['coef']):.3f}  95% CI ({np.exp(s['coef lower 95%']):.3f}, {np.exp(s['coef upper 95%']):.3f})"
      f" -> preregistered rule gives: {'Supported' if (np.exp(s['coef lower 95%'])>1 and np.exp(s['coef'])>=2) else ('Refuted' if np.exp(s['coef upper 95%'])<2 else 'Inconclusive')}")
# storm bootstrap for that coefficient, as the D4 code would do (draws without Kingston fail -> dropped)
A.NBOOT = 400
bs = A.boot_b(r, A.BASE + ["sids"], "sids")
print("  D4 storm-bootstrap for sids with the guard removed:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in bs.items()},
      "-> exp:", (round(np.exp(bs['lo']), 3), round(np.exp(bs['hi']), 3)) if bs["lo"] is not None else None)

# pooled two-part estimand: expected recovery days per event (zeros included), SIDS vs non-SIDS, storm-cluster bootstrap
def pooled_ratio(df):
    s_, n_ = df[df.sids == 1], df[df.sids == 0]
    return (s_.T_.clip(lower=0).mean() + 1e-9) / (n_.T_.mean() + 1e-9)
rng = np.random.default_rng(5); storms = r.sid.unique(); groups = {s_: g for s_, g in r.groupby("sid")}
vals = []
for _ in range(2000):
    pick = rng.choice(storms, size=len(storms), replace=True)
    rb = pd.concat([groups[s_] for s_ in pick])
    if (rb.sids == 1).sum() and (rb.sids == 0).sum(): vals.append(pooled_ratio(rb))
print(f"\n[pooled estimand] mean recovery days incl. zeros: SIDS {r[r.sids==1].T_.mean():.2f} vs non-SIDS {r[r.sids==0].T_.mean():.2f}; ratio {pooled_ratio(r):.3f}, storm-bootstrap 95% ({np.percentile(vals,2.5):.3f}, {np.percentile(vals,97.5):.3f})")
print(f"  share disrupted ratio SIDS/non-SIDS: {r[r.sids==1].D_.mean()/r[r.sids==0].D_.mean():.3f}")

# forecast: re-derive every row from forecast_model.json with score_forecast.predict
model = json.load(open(RUN / "results/tables/forecast_model.json"))
print("\n[forecast] model sha256", hashlib.sha256((RUN / "results/tables/forecast_model.json").read_bytes()).hexdigest()[:16], "table sha256",
      hashlib.sha256((RUN / "results/tables/forecast_table.csv").read_bytes()).hexdigest()[:16])
ft = pd.read_csv(RUN / "results/tables/forecast_table.csv")
act = pd.read_csv(RUN / "data/raw/portwatch/daily.csv", usecols=["portid", "portcalls"]).groupby("portid").portcalls.mean()
pp = ports.set_index("portid")
maxdp = maxdm = 0
for _, row in ft.iterrows():
    p = pp.loc[row.portid]
    x = dict(log_size=np.log(p.vessel_count_total + 1), log_activity=np.log(act[row.portid]), cat=row.cat, closest_100km=row.closest_km / 100,
             share=p.share_country_maritime_import / 100, sids=1.0)
    pd_, md = S.predict(model, x)
    maxdp = max(maxdp, abs(pd_ - row.p_disrupted)); maxdm = max(maxdm, abs(md - row.median_T_if_disrupted))
print(f"  all 108 rows re-derived: max |dp| {maxdp:.2e}, max |dmedian| {maxdm:.2e}")
# alternative forecast: sids kept in part B (plan.md section 7 as written)
fb = WeibullAFTFitter().fit(d[A.BASE + ["share", "sids", "T_", "E_"]], duration_col="T_", event_col="E_")
lam = {k[1]: v for k, v in fb.params_.items() if k[0] == "lambda_"}; rho = np.exp(fb.params_.loc[("rho_", "Intercept")])
out = []
for _, row in ft[(ft.cat == 4) & (ft.closest_km == 75)].iterrows():
    p = pp.loc[row.portid]
    x = dict(log_size=np.log(p.vessel_count_total + 1), log_activity=np.log(act[row.portid]), cat=row.cat, closest_100km=row.closest_km / 100,
             share=p.share_country_maritime_import / 100, sids=1.0)
    ls = lam["Intercept"] + sum(lam[c] * x[c] for c in A.BASE + ["share", "sids"])
    out.append((row.portname, round(row.median_T_if_disrupted, 1), round(float(np.exp(ls) * np.log(2) ** (1 / rho)), 1)))
print("  sids coefficient in part B if kept (plan as written):", round(float(lam["sids"]), 3), "-> time ratio", round(float(np.exp(lam["sids"])), 3))
print("  Cat 4 / 75 km medians, frozen vs with-sids-in-part-B:", out)
# Brier benchmark fairness
print(f"  benchmark share disrupted {model['benchmark_share_disrupted']:.3f} vs SIDS-only historical {r[r.sids==1].D_.mean():.3f}; Brier of 'always 0.329' if no event is disrupted = {0.329**2:.3f}; of the forecast p~0.08 = {0.08**2:.4f}")
