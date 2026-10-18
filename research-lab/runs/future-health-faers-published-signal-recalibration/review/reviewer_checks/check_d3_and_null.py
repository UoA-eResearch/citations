"""Reviewer checks 2, 5, 6: (a) D3 as-run vs corrected: survival among signals added and dropped by the correction;
(b) an independent MLE fit of the null, profile-likelihood CI for mu, leave-one-PT-out and leave-one-drug-out ranges,
variance decomposition of control log RORs by PT and by drug; (c) H1/H2 recomputed from recomputed.csv with my own
BH and bootstrap."""
import json
from pathlib import Path
import numpy as np, pandas as pd
from scipy import optimize, stats
RUN = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
e = pd.read_csv(RUN / "data" / "signals_eligible.csv", dtype={"paper": str})
ea = pd.read_csv(RUN / "data" / "signals_eligible_asrun.csv", dtype={"paper": str})
r = pd.read_csv(RUN / "data" / "recomputed.csv", dtype={"paper": str})
ra = pd.read_csv(RUN / "data" / "recomputed_asrun.csv", dtype={"paper": str})
s = pd.read_csv(RUN / "results" / "tables" / "signals_results.csv", dtype={"paper": str})
sa = pd.read_csv(RUN / "results" / "asrun" / "signals_results.csv", dtype={"paper": str})
key = lambda d: set(zip(d.paper, d.k))
print("== D3 ==")
print("as-run capped", len(ea), "of which status ok", (ra.status == "ok").sum(), "| corrected capped", len(e))
new = key(e) - key(ea); dropped = key(ea) - key(e); common = key(e) & key(ea)
print("new", len(new), "dropped (all)", len(dropped), "common", len(common))
sa_ok = sa.set_index(["paper", "k"]); s_i = s.set_index(["paper", "k"])
drop_ok = [k for k in dropped if k in sa_ok.index]
print("dropped that had been computed (ok) in as-run:", len(drop_ok), "| dropped that were non-PT in as-run:", len(dropped) - len(drop_ok))
print("survival among dropped-ok (as-run q):", round(sa_ok.loc[drop_ok].primary_survive_mle.fillna(False).mean(), 3))
print("survival among new (corrected q):", round(s_i.loc[list(new)].primary_survive_mle.fillna(False).mean(), 3))
print("survival among common (corrected q):", round(s_i.loc[list(common)].primary_survive_mle.fillna(False).mean(), 3))
# did the recomputed rows reused from as-run match exactly?
m = r.merge(ra, on=["paper", "k"], suffixes=("", "_a"))
print("rows in both recomputed files:", len(m), "| primary_a identical:", int((m.primary_a == m.primary_a_a).sum()))
# as-run: how many papers lost eligible signals to the cap-before-PT ordering
aa = pd.read_csv(RUN / "data" / "signals_all.csv", dtype={"paper": str})
print("fully eligible (corrected signals_all):", (aa.reason.isna() | (aa.reason == "")).sum())
print()
print("== NULL ==")
nc = pd.read_csv(RUN / "data" / "negative_controls_computed.csv")
v = nc[(nc.status == "ok") & (nc.a >= 1) & np.isfinite(nc.se)].copy()
lr, se = np.log(v.ror.values), v.se.values
def nll(mu, ls, lr=lr, se=se):
    s2 = np.exp(2 * ls) + se ** 2
    return 0.5 * np.sum(np.log(2 * np.pi * s2) + (lr - mu) ** 2 / s2)
res = optimize.minimize(lambda p: nll(*p), [lr.mean(), np.log(lr.std())], method="Nelder-Mead", options=dict(xatol=1e-8, fatol=1e-10, maxiter=5000))
mu, sg = res.x[0], np.exp(res.x[1])
print(f"independent MLE: mu={mu:.4f} sigma={sg:.4f} exp(mu)={np.exp(mu):.3f}  (report: -0.8489, 0.9621)")
# profile-likelihood CI for mu
prof = lambda m: optimize.minimize_scalar(lambda ls: nll(m, ls), bounds=(-3, 2), method="bounded").fun
lo = optimize.brentq(lambda m: prof(m) - res.fun - 1.92, mu - 2, mu); hi = optimize.brentq(lambda m: prof(m) - res.fun - 1.92, mu, mu + 2)
print(f"profile 95% CI for mu: {lo:.3f} to {hi:.3f}; SE-weighted mean of log ROR: {np.average(lr, weights=1/(sg**2+se**2)):.3f}")
print(f"sample: mean={lr.mean():.4f} sd={lr.std(ddof=1):.4f} median={np.median(lr):.4f} exp(median)={np.exp(np.median(lr)):.3f}")
print("controls with a>=3 and lo>1 (uncalibrated positive):", int(((v.lo > 1) & (v.a >= 3)).sum()), "| hi<1 (uncalibrated negative):", int((v.hi < 1).sum()))
# leave-one-PT-out / leave-one-drug-out
def fit(idx):
    l, s_ = lr[idx], se[idx]
    rr = optimize.minimize(lambda p: nll(p[0], p[1], l, s_), [l.mean(), np.log(max(l.std(), .05))], method="Nelder-Mead")
    return rr.x[0], np.exp(rr.x[1])
mus = {pt: fit((v.pt != pt).values)[0] for pt in v.pt.unique()}
print(f"leave-one-PT-out mu range: {min(mus.values()):.3f} to {max(mus.values()):.3f}")
mud = {d: fit((v.drug != d).values)[0] for d in v.drug.unique()}
print(f"leave-one-drug-out mu range: {min(mud.values()):.3f} to {max(mud.values()):.3f}")
# variance decomposition (one-way, by PT and by drug) of log ROR
import statsmodels.formula.api as smf
v["lr"] = lr
for f in ("pt", "drug"):
    m1 = smf.ols(f"lr ~ C({f})", data=v).fit()
    print(f"one-way ANOVA by {f}: R2={m1.rsquared:.3f}, F p={m1.f_pvalue:.2e}, groups={v[f].nunique()}")
m2 = smf.ols("lr ~ C(pt) + C(drug)", data=v).fit(); print(f"two-way (PT + drug): R2={m2.rsquared:.3f}")
# null by PT class: outcomes that are chronic diseases / indications vs acute events (reviewer's split)
acute = {"PANCREATITIS ACUTE", "GASTROINTESTINAL HAEMORRHAGE", "CEREBROVASCULAR ACCIDENT", "HYDRONEPHROSIS", "PROTEINURIA", "ATELECTASIS",
         "MIGRAINE WITH AURA", "DIAPHRAGMATIC HERNIA", "BRONCHITIS", "OTITIS MEDIA", "GASTROINTESTINAL INFECTION", "SKIN INFECTION", "CROUP INFECTIOUS",
         "ALCOHOL WITHDRAWAL SYNDROME", "EAR PAIN", "IRON DEFICIENCY ANAEMIA", "VITAMIN D DEFICIENCY", "LYME DISEASE", "TINEA PEDIS", "SCIATICA"}
v["acute"] = v.pt.isin(acute)
for lab, idx in (("acute-type PTs", v.acute.values), ("chronic/indication-type PTs", ~v.acute.values)):
    m_, s_ = fit(idx); print(f"MLE on {lab}: n={idx.sum()} mu={m_:.3f} sigma={s_:.3f}")
# the drug's total PS report count vs its mean log ROR (do big-b drugs sit lower?)
g = v.groupby("drug").agg(n=("lr", "size"), mean_lr=("lr", "mean"), b=("b", "first"))
print("Spearman(log b, mean log ROR) across drugs:", stats.spearmanr(np.log(g.b), g.mean_lr))
# the event's background count c vs mean log ROR
gp = v.groupby("pt").agg(n=("lr", "size"), mean_lr=("lr", "mean"), c=("c", "first"))
print("Spearman(log c, mean log ROR) across PTs:", stats.spearmanr(np.log(gp.c), gp.mean_lr))
print()
print("== H1/H2 recomputed independently ==")
def bh(p):
    p = np.asarray(p, float); fin = np.isfinite(p); n = fin.sum(); q = np.full(p.shape, np.nan)
    o = np.argsort(np.where(fin, p, np.inf)); ranked = p[o][:n] * n / np.arange(1, n + 1)
    q[o[:n]] = np.minimum(1, np.minimum.accumulate(ranked[::-1])[::-1]); return q
d = e.merge(r, on=["paper", "k"]); assert len(d) == 406 and (d.status == "ok").all()
lrs, ses = np.log(d.primary_ror.values), d.primary_se.values
z = (lrs - mu) / np.sqrt(sg ** 2 + ses ** 2); p = 2 * stats.norm.sf(np.abs(z)); q = bh(p)
surv = (d.primary_ror.values > 1) & (q < 0.05)
print("survive:", surv.sum(), "of", len(d), "=", round(surv.mean(), 4), "(report 289/406)")
rng = np.random.default_rng(1); papers = d.paper.unique(); idx = {pp: np.where(d.paper.values == pp)[0] for pp in papers}
bs = [surv[np.concatenate([idx[pp] for pp in rng.choice(papers, len(papers))])].mean() for _ in range(2000)]
print("cluster bootstrap 95%:", np.round(np.percentile(bs, [2.5, 97.5]), 3), "(report 0.653-0.768)")
# BH re-run inside each bootstrap sample (the pipeline keeps q fixed)
bs2 = []
for _ in range(1000):
    ii = np.concatenate([idx[pp] for pp in rng.choice(papers, len(papers))]); qq = bh(p[ii]); bs2.append(((d.primary_ror.values[ii] > 1) & (qq < 0.05)).mean())
print("cluster bootstrap with BH inside each resample:", np.round(np.percentile(bs2, [2.5, 97.5]), 3))
# also propagate null uncertainty: refit the null on a bootstrap of the controls inside each resample
bs3 = []
for _ in range(500):
    jj = rng.integers(0, len(lr), len(lr)); m_, s_ = fit(jj) if False else (None, None)
    rr = optimize.minimize(lambda pq: nll(pq[0], pq[1], lr[jj], se[jj]), [lr[jj].mean(), np.log(lr[jj].std())], method="Nelder-Mead"); m_, s_ = rr.x[0], np.exp(rr.x[1])
    ii = np.concatenate([idx[pp] for pp in rng.choice(papers, len(papers))])
    zz = (lrs[ii] - m_) / np.sqrt(s_ ** 2 + ses[ii] ** 2); qq = bh(2 * stats.norm.sf(np.abs(zz))); bs3.append(((d.primary_ror.values[ii] > 1) & (qq < 0.05)).mean())
print("cluster bootstrap + control bootstrap (null uncertainty):", np.round(np.percentile(bs3, [2.5, 97.5]), 3))
ratio = d.estimate.values / d.primary_ror.values; fin = np.isfinite(ratio) & (ratio > 0)
print("H2 median ratio:", round(np.median(ratio[fin]), 4), "n", fin.sum())
# zero-cell: which cell
zc = d[~np.isfinite(d.primary_ror)]
print("zero cell rows:", len(zc), "| a==0:", int((zc.primary_a == 0).sum()), "| c==0:", int((zc.primary_c == 0).sum()), "| b==0:", int((zc.primary_b == 0).sum()))
# survival threshold implied: smallest surviving recomputed ROR and largest non-surviving
print("smallest surviving recomputed ROR:", round(d.primary_ror.values[surv].min(), 2), "| largest non-surviving finite ROR with a>=3:",
      round(np.nanmax(np.where(~surv & (d.primary_a.values >= 3), d.primary_ror.values, np.nan)), 2))
json.dump(dict(mu=mu, sigma=sg, mu_ci=[lo, hi], loo_pt=mus, loo_drug=mud), open(OUT / "null_refit.json", "w"), indent=1)
