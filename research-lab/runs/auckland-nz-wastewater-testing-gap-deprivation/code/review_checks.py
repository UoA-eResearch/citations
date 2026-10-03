"""Checks added after independent review (deviations.md D3-D7). The preregistered verdicts use analysis.py; nothing here
changes them. The CR2 / Bell-McCaffrey, wild-cluster-bootstrap and interval-censored count-model code follows the
reviewer's scratch implementation.

1. Small-sample inference for H1: CR2 SE with Bell-McCaffrey dof; restricted wild-cluster bootstrap (Rademacher)
   p-value and grid-inverted CI.
2. Integer rounding of case_7d_avg (a recorded 0 = 0-3 cases a week): pseudo-count 0.25 / 1 / 3.5, bin midpoint,
   drop recorded-zero weeks (an upper bound: selects on the outcome), site zero-share covariate, interval-censored NB.
3. 500 gc/L quantification floor: drop weeks whose samples are all at the floor; drop floor and zero weeks.
4. Assumed-flow sites (copies/gc ratio constant): flag covariate; measured-flow sites only.
5. Adjustment ladder and two-step site-level regressions.
6. Holiday towns (post hoc, exploratory).
7. Power: MDE of H1 and H2 at the realised SEs.
Output: results/tables/review_checks.csv
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import optimize, special, stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis import COV, RUN, Z, h1, h2, load, ols, sample  # noqa: E402

warnings.filterwarnings("ignore")
TAB = RUN / "results" / "tables"
HOLIDAY = ["Whangamata", "Whitianga", "Wanaka", "Mangawhai", "Taupo", "Picton", "Cromwell", "Maketu"]


def ratio_row(label, b, se, crit=Z, **kw):
    return dict(analysis=label, value=np.exp(b), lo=np.exp(b - crit * se), hi=np.exp(b + crit * se), b=b, se=se, **kw)


def small_sample(d, rows):
    mod = smf.ols(f"ai ~ C(week) + zdep + {COV}", data=d)
    X, y = np.asarray(mod.exog), np.asarray(mod.endog)
    j = mod.exog_names.index("zdep")
    g = pd.factorize(d.SampleLocation)[0]
    G, (N, K) = g.max() + 1, X.shape
    XtXi = np.linalg.pinv(X.T @ X)
    beta = XtXi @ X.T @ y
    e = y - X @ beta
    cl = [np.where(g == c)[0] for c in range(G)]
    A = []
    for idx in cl:
        Hg = X[idx] @ XtXi @ X[idx].T
        w, v = np.linalg.eigh(np.eye(len(idx)) - Hg)
        A.append(v @ np.diag(np.clip(w, 1e-10, None) ** -0.5) @ v.T)

    def V(res, cr2=False):
        meat = np.zeros((K, K))
        for c, idx in enumerate(cl):
            u = X[idx].T @ (A[c] @ res[idx] if cr2 else res[idx])
            meat += np.outer(u, u)
        return XtXi @ meat @ XtXi
    se1 = np.sqrt(V(e)[j, j] * (G / (G - 1)) * ((N - 1) / (N - K)))
    se2 = np.sqrt(V(e, cr2=True)[j, j])
    ej = np.zeros(K); ej[j] = 1
    B = np.zeros((N, G))
    for c, idx in enumerate(cl):
        B[idx, c] = A[c] @ X[idx] @ XtXi @ ej
    IHB = B - X @ (XtXi @ (X.T @ B))
    ev = np.linalg.eigvalsh(IHB.T @ IHB)
    dof = ev.sum() ** 2 / (ev ** 2).sum()
    rows.append(ratio_row("H1 with CR2 SE (Bell-McCaffrey dof)", beta[j], se2, crit=stats.t.ppf(0.975, dof),
                          dof=dof, p=2 * stats.t.sf(abs(beta[j] / se2), dof)))
    rng = np.random.default_rng(20261003)

    def wcr_p(b0, reps):
        Xr = np.delete(X, j, axis=1)
        yr = y - X[:, j] * b0
        br = np.linalg.pinv(Xr.T @ Xr) @ Xr.T @ yr
        er, fr = yr - Xr @ br, Xr @ br
        t_obs = (beta[j] - b0) / se1
        ts = np.empty(reps)
        for r in range(reps):
            w = rng.choice([-1.0, 1.0], size=G)
            ys = fr + w[g] * er + X[:, j] * b0
            bs = XtXi @ X.T @ ys
            es = ys - X @ bs
            ts[r] = (bs[j] - b0) / np.sqrt(V(es)[j, j] * (G / (G - 1)) * ((N - 1) / (N - K)))
        return (np.abs(ts) >= abs(t_obs)).mean()
    p0 = wcr_p(0.0, 1999)
    grid = np.linspace(beta[j] - 4 * se1, beta[j] + 4 * se1, 33)
    ps = np.array([wcr_p(b0, 599) for b0 in grid])
    inside = grid[ps >= 0.05]
    rows.append(dict(analysis="H1 wild-cluster bootstrap (restricted, Rademacher)", value=np.exp(beta[j]),
                     lo=np.exp(inside.min()), hi=np.exp(inside.max()), b=beta[j], p=p0))


def censored_nb(d, alpha):
    """Interval-censored NB: weeks with case_7d_avg k <= 10 are censored to [7k-3, 7k+3] (0 -> [0, 3])."""
    mod = smf.ols(f"ai ~ C(week) + zdep + {COV}", data=d)
    X = np.asarray(mod.exog); j = mod.exog_names.index("zdep"); K = X.shape[1]
    g = pd.factorize(d.SampleLocation)[0]; G = g.max() + 1
    kd = d.case_7d_avg.values.astype(int); y = (7 * kd).astype(float); cens = kd <= 10
    lo = np.where(kd == 0, 0, 7 * kd - 3).astype(float); hi = (7 * kd + 3).astype(float)
    off = np.log(d.copies_per_day_per_person.values * d.esr_pop.values); off = off - off.mean()
    n_ = 1 / alpha

    def P_dP(mu):
        p_ = n_ / (n_ + mu)
        Fhi = special.betainc(n_, hi + 1, p_)
        Flo = np.where(lo > 0, special.betainc(n_, np.maximum(lo, 1), p_), 0.0)

        def dF(kk):
            logt = (n_ - 1) * np.log(p_) + kk * np.log1p(-p_) - special.betaln(n_, kk + 1)
            return -n_ / (n_ + mu) ** 2 * np.exp(logt)
        return Fhi - Flo, dF(hi) - np.where(lo > 0, dF(np.maximum(lo, 1) - 1), 0.0)

    def parts(beta):
        mu = np.exp(np.clip(X @ beta + off, -30, 30))
        P, dP = P_dP(mu); ok = P > 1e-100; P = np.clip(P, 1e-300, None)
        p_ = n_ / (n_ + mu)
        lpe, se_ = stats.nbinom.logpmf(y, n_, p_), (y - mu) / (1 + alpha * mu)
        ll = np.where(cens & ok, np.log(P), lpe)
        s = np.where(cens & ok, mu * dP / P, se_)
        return -ll.sum(), -(X * s[:, None]).sum(0), X * s[:, None]
    start = smf.glm(f"c ~ C(week) + zdep + {COV}", d.assign(c=y), family=sm.families.NegativeBinomial(alpha=alpha),
                    offset=off).fit().params.values
    res = optimize.minimize(lambda b: parts(b)[0], start, jac=lambda b: parts(b)[1], method="L-BFGS-B",
                            options=dict(maxiter=20000, maxfun=100000, ftol=1e-13, gtol=1e-7))
    beta = res.x; S = parts(beta)[2]
    H = np.zeros((K, K))
    for i in range(K):
        bp, bm = beta.copy(), beta.copy(); bp[i] += 1e-4; bm[i] -= 1e-4
        H[:, i] = (parts(bp)[1] - parts(bm)[1]) / 2e-4
    Hi = np.linalg.pinv((H + H.T) / 2)
    meat = sum(np.outer(S[g == c].sum(0), S[g == c].sum(0)) for c in range(G))
    se = np.sqrt((Hi @ meat @ Hi)[j, j] * G / (G - 1))
    return ratio_row(f"interval-censored NB (alpha {alpha}) on weekly cases", beta[j], se, converged=bool(res.success))


def main():
    m = load()
    d, k = sample(m)
    rows = []
    base = h1(d, "PRIMARY H1 (CR1, preregistered)")
    rows.append(base)
    small_sample(d, rows)
    # 2. rounding
    for off_ in (0.25, 1.0, 3.5):
        q = d.assign(ai=np.log((7 * d.case_7d_avg + off_) / d.esr_pop * 1e5) - np.log(d.copies_per_day_per_person))
        rows.append(h1(q, f"pseudo-count {off_} instead of 0.5"))
    mid = np.where(d.case_7d_avg == 0, 1.75, 7 * d.case_7d_avg)
    rows.append(h1(d.assign(ai=np.log(mid / d.esr_pop * 1e5) - np.log(d.copies_per_day_per_person)),
                   "bin midpoint (recorded 0 -> 1.75 cases/week)"))
    rows.append(h1(d[d.case_7d_avg > 0], "drop recorded-zero weeks (upper bound; selects on outcome)"))
    zs = d.groupby("SampleLocation").case_7d_avg.apply(lambda s: (s == 0).mean())
    rows.append(h1(d.assign(zshare=d.SampleLocation.map(zs)), "site share of zero weeks as covariate", cov=COV + " + zshare"))
    for a in (0.171, 0.5, 1.0):
        rows.append(censored_nb(d, a))
    # 3. 500 gc/L floor
    s = pd.read_csv(RUN / "data/raw/covid_in_wastewater/data_historic/ww_data_all.csv", parse_dates=["Collected"])
    s["week_end_date"] = s.Collected + pd.to_timedelta((6 - s.Collected.dt.dayofweek) % 7, unit="D")
    wk = s.groupby(["SampleLocation", "week_end_date"]).agg(gmax=("sars_gcl", "max"), gmean=("sars_gcl", "mean")).reset_index()
    d2 = d.merge(wk, on=["SampleLocation", "week_end_date"], how="left")
    floor = d2.gmax == 500
    rows.append(h1(d2[~floor], "drop weeks with all samples at the 500 gc/L floor"))
    rows.append(h1(d2[~floor & (d2.case_7d_avg > 0)], "drop floor weeks and recorded-zero weeks"))
    # 4. assumed flow: copies per gc/L constant within site
    d2["cg"] = d2.copies_per_day_per_person / d2.gmean
    cv = d2[d2.gmean > 0].groupby("SampleLocation").cg.agg(lambda x: x.std() / x.mean())
    assumed = set(cv[cv < 1e-6].index)
    rows.append(h1(d.assign(assumed=d.SampleLocation.isin(assumed).astype(int)), "assumed-flow site flag as covariate",
                   cov=COV + " + assumed"))
    rows.append(h1(d[~d.SampleLocation.isin(assumed)], "measured-flow sites only"))
    # 5. adjustment ladder and two-step
    for lab, f in [("unadjusted site-week (week FE only)", "ai ~ C(week) + zdep"),
                   ("+ sampler", "ai ~ C(week) + zdep + C(sampler)"),
                   ("+ log population", "ai ~ C(week) + zdep + C(sampler) + logpop"),
                   ("+ share 65+", "ai ~ C(week) + zdep + C(sampler) + logpop + z65")]:
        mm = ols(d, f)
        rows.append(ratio_row(f"ladder: {lab}", mm.params["zdep"], mm.bse["zdep"]))
    d["ai_dm"] = d.ai - d.groupby("week").ai.transform("mean")
    sm_ = d.groupby("SampleLocation").agg(ai=("ai_dm", "mean"), n=("ai", "size")).join(k.set_index("SampleLocation"))
    sm_["region"] = sm_.region
    for lab, w in [("two-step site means, unweighted", None), ("two-step site means, weighted by weeks", sm_.n)]:
        f = "ai ~ zdep + C(sampler) + logpop + z65 + C(region)"
        mm = (smf.wls(f, sm_, weights=w) if w is not None else smf.ols(f, sm_)).fit(cov_type="HC3")
        rows.append(ratio_row(lab, mm.params["zdep"], mm.bse["zdep"]))
    # 6. holiday towns (post hoc)
    hol = d.DisplayName.isin(HOLIDAY)
    rows.append(h1(d[~hol], "exploratory, post hoc: drop holiday towns"))
    # 7. power
    se = base["se"]
    r2 = h2(d, "H2")
    rows.append(dict(analysis="MDE H1 (80% power, two-sided 5%)", value=np.exp(-(1.96 + 0.8416) * se), se=se,
                     p=stats.norm.cdf(abs(np.log(0.85)) / se - 1.96)))
    rows.append(dict(analysis="MDE H2 interaction (log scale)", value=(1.96 + 0.8416) * r2["se"], se=r2["se"]))
    out = pd.DataFrame(rows)
    out.to_csv(TAB / "review_checks.csv", index=False)
    print(out[["analysis", "value", "lo", "hi"]].round(3).to_string(index=False))
    print("zero-week share", round((d.case_7d_avg == 0).mean(), 3), "| floor weeks", int(floor.sum()),
          "| assumed-flow sites", len(assumed), "| power for 0.85:", round(rows[-2]["p"], 2),
          "| CR2 dof", round([r for r in rows if "CR2" in r["analysis"]][0]["dof"], 1))


if __name__ == "__main__":
    main()
