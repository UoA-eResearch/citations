"""Calibration and hypotheses (plan sections 1, 4, 6). Reads data/signals_eligible.csv, data/recomputed.csv and
data/negative_controls_computed.csv. Writes results/tables/primary.json and results/tables/signals_results.csv."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import optimize, stats

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
B = 2000


def fit_null_mle(logr, se):
    """N(mu, sigma^2) systematic error, each estimate observed with its own SE (Schuemie et al. 2014)."""
    def nll(p):
        mu, ls = p
        s2 = np.exp(2 * ls) + se ** 2
        return 0.5 * np.sum(np.log(2 * np.pi * s2) + (logr - mu) ** 2 / s2)
    r = optimize.minimize(nll, [np.mean(logr), np.log(max(np.std(logr), 0.05))], method="Nelder-Mead")
    return float(r.x[0]), float(np.exp(r.x[1]))


def calibrated_p(logr, se, mu, sigma):
    z = (logr - mu) / np.sqrt(sigma ** 2 + se ** 2)
    return 2 * np.minimum(stats.norm.cdf(z), 1 - stats.norm.cdf(z))


def bh(p):
    p = np.asarray(p, float); n = np.sum(np.isfinite(p)); q = np.full_like(p, np.nan)
    idx = np.where(np.isfinite(p))[0]; o = idx[np.argsort(p[idx])]
    ranked = p[o] * n / np.arange(1, n + 1)
    q[o] = np.minimum.accumulate(ranked[::-1])[::-1]
    return np.minimum(q, 1)


def cluster_boot(df, f, seed=20261018):
    rng = np.random.default_rng(seed); papers = df.paper.unique(); g = {p: x for p, x in df.groupby("paper")}
    vals = []
    for _ in range(B):
        s = pd.concat([g[p] for p in rng.choice(papers, len(papers))])
        vals.append(f(s))
    vals = np.asarray(vals, float)
    return [float(np.nanpercentile(vals, 2.5)), float(np.nanpercentile(vals, 97.5))]


def main():
    e = pd.read_csv(RUN / "data" / "signals_eligible.csv", dtype={"paper": str})
    r = pd.read_csv(RUN / "data" / "recomputed.csv", dtype={"paper": str})
    nc = pd.read_csv(RUN / "data" / "negative_controls_computed.csv")
    d = e.merge(r, on=["paper", "k"], how="left", suffixes=("", "_r"))
    out = dict(eligible_signals=int(len(e)), papers=int(e.paper.nunique()), status=d.status.value_counts(dropna=False).to_dict())
    ok = d[d.status == "ok"].copy()
    ncv = nc[(nc.status == "ok") & (nc.a >= 1) & np.isfinite(nc.se)]
    out["negative_controls_used"] = int(len(ncv))
    lr, se = np.log(ncv.ror.values), ncv.se.values
    nulls = {"mle": fit_null_mle(lr, se), "sd": (float(np.mean(lr)), float(np.std(lr, ddof=1)))}
    out["null"] = {k: dict(mu=v[0], sigma=v[1], exp_mu=float(np.exp(v[0]))) for k, v in nulls.items()}
    out["negative_controls_uncalibrated_significant"] = int(((ncv.lo > 1) & (ncv.a >= 3)).sum())
    VARS = ("primary", "allsuspect", "nodedup", "fullwindow") + (("faersonly",) if "faersonly_ror" in ok else ())   # D4
    for v in VARS:
        lrv, sev = np.log(ok[f"{v}_ror"]), ok[f"{v}_se"]
        ok[f"{v}_sig_uncal"] = (ok[f"{v}_lo"] > 1) & (ok[f"{v}_a"] >= 3)
        for nm, (mu, sg) in nulls.items():
            p = calibrated_p(lrv.values, sev.values, mu, sg)
            ok[f"{v}_p_{nm}"] = p
            ok[f"{v}_q_{nm}"] = bh(p)
            ok[f"{v}_survive_{nm}"] = (ok[f"{v}_ror"] > 1) & (ok[f"{v}_q_{nm}"] < 0.05)
    # signals whose recomputation gives no estimate (a zero cell) count as not surviving; ineligible events are reported, not counted
    surv = lambda x: float(x.primary_survive_mle.fillna(False).mean())
    h1 = dict(n=int(len(ok)), share_surviving=surv(ok), ci=cluster_boot(ok, surv))
    h1["verdict"] = "Supported" if h1["ci"][1] < 0.60 else "Refuted" if h1["ci"][0] >= 0.60 else "Inconclusive"
    out["H1"] = h1
    out["H1_sd_null"] = dict(share=float(ok.primary_survive_sd.fillna(False).mean()),
                             ci=cluster_boot(ok, lambda x: float(x.primary_survive_sd.fillna(False).mean())))
    out["uncalibrated_replication"] = dict(share=float(ok.primary_sig_uncal.mean()), ci=cluster_boot(ok, lambda x: float(x.primary_sig_uncal.mean())))
    out["variants"] = {v: dict(uncal=float(ok[f"{v}_sig_uncal"].mean()), survive_mle=float(ok[f"{v}_survive_mle"].fillna(False).mean()))
                       for v in ("primary", "allsuspect", "nodedup", "fullwindow")}
    if "faersonly_ror" in ok:   # D4: the preregistered FAERS-only sensitivity, among signals with a window reaching 2012Q4
        fo = ok[ok.faersonly_status == "ok"]
        mu, sg = nulls["mle"]
        q = bh(calibrated_p(np.log(fo.faersonly_ror.values), fo.faersonly_se.values, mu, sg))
        fs = (fo.faersonly_ror.values > 1) & (q < 0.05)
        out["variants"]["faersonly"] = dict(n=int(len(fo)), n_not_computable=int((ok.faersonly_status != "ok").sum()),
                                            uncal=float(fo.faersonly_sig_uncal.mean()), survive_mle=float(fs.mean()),
                                            primary_survive_same_signals=float(fo.primary_survive_mle.fillna(False).mean()))
    # D4: H1 with the null's own sampling uncertainty (papers and negative controls resampled jointly, null refitted,
    # BH within each draw)
    rng = np.random.default_rng(20261018); papers = ok.paper.unique(); g = {p_: x for p_, x in ok.groupby("paper")}
    ncs = np.arange(len(ncv)); draws = []
    for _ in range(B):
        s_ = pd.concat([g[p_] for p_ in rng.choice(papers, len(papers))]); j = rng.choice(ncs, len(ncs))
        mu_b, sg_b = fit_null_mle(lr[j], se[j])
        q_b = bh(calibrated_p(np.log(s_.primary_ror.values), s_.primary_se.values, mu_b, sg_b))
        draws.append(float(np.nanmean(np.where(np.isfinite(q_b), (s_.primary_ror.values > 1) & (q_b < 0.05), False))))
    out["H1_null_propagated"] = dict(ci=[float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))])
    sv = ok.primary_survive_mle.fillna(False).astype(bool)
    out["survival_threshold"] = dict(smallest_surviving_ror=float(ok.primary_ror[sv].min()),
                                     largest_nonsurviving_ror_a3=float(ok.primary_ror[~sv & (ok.primary_a >= 3)].max()),
                                     survivors_with_a_below_3=int((sv & (ok.primary_a < 3)).sum()))
    out["control_median_ror"] = float(np.exp(np.median(lr)))
    out["controls_designated"] = int(len(nc)); out["controls_a0"] = int(((nc.status == "ok") & (nc.a == 0)).sum())
    # D2 sensitivity: only signals whose published comparison is against all other drugs (BH recomputed within the subset)
    sub = ok[ok.comparison == "all drugs"].copy()
    mu, sg = nulls["mle"]
    sub["q_sub"] = bh(calibrated_p(np.log(sub.primary_ror.values), sub.primary_se.values, mu, sg))
    sub["surv_sub"] = (sub.primary_ror > 1) & (sub.q_sub < 0.05)
    out["all_drugs_only"] = dict(n=int(len(sub)), share_surviving=float(sub.surv_sub.mean()),
                                 ci=cluster_boot(sub, lambda x: float(x.surv_sub.mean())),
                                 median_ratio=float(np.median((sub.estimate / sub.primary_ror)[lambda r: np.isfinite(r) & (r > 0)])))
    out["windows_starting_before_2004"] = int((ok.win.str.slice(0, 4).astype(int) < 2004).sum())
    ok["ratio"] = ok.estimate / ok.primary_ror
    rr = ok[np.isfinite(ok.ratio) & (ok.ratio > 0)]
    med = lambda x: float(np.median(x.ratio))
    h2 = dict(n=int(len(rr)), median_ratio=med(rr), ci=cluster_boot(rr, med))
    h2["verdict"] = "Supported" if h2["ci"][0] >= 1.25 else "Refuted" if h2["ci"][1] < 1.25 else "Inconclusive"
    out["H2"] = h2
    # secondary: predictors of non-survival (paper-clustered SEs)
    x = ok.copy()
    x["nonsurv"] = (~x.primary_survive_mle.fillna(False)).astype(int)
    x["log_pub"] = np.log(x.estimate)
    x["win_years"] = x.win.str.slice(7, 11).astype(float) - x.win.str.slice(0, 4).astype(float)
    recs = {str(json.loads(l)["id"]): json.loads(l) for l in open(RUN / "data" / "raw" / "epmc" / "records.jsonl")}
    x["journal"] = x.paper.map(lambda p: ((recs.get(p, {}).get("journalInfo") or {}).get("journal") or {}).get("title", "?"))
    top5 = x.journal.value_counts().head(5).index
    x["top5_journal"] = x.journal.isin(top5).astype(int)
    x["year"] = x.paper.map(lambda p: int(recs.get(p, {}).get("pubYear") or 0))
    x["log_cases"] = np.log(x.n_cases.where(x.n_cases > 0))
    # plan section 6: (1) all signals without the case count; (2) the subset reporting a case count, with log cases
    for name, cols, xx in (("secondary", ["log_pub", "win_years", "top5_journal", "year"], x),
                           ("secondary_with_cases", ["log_pub", "log_cases", "win_years", "top5_journal", "year"], x[x.log_cases.notna()])):
        try:
            m = sm.Logit(xx.nonsurv, sm.add_constant(xx[cols].astype(float))).fit(disp=0, cov_type="cluster", cov_kwds={"groups": pd.factorize(xx.paper)[0]})
            out[name] = dict(n=int(len(xx)), coef=dict(zip(["const"] + cols, map(float, m.params))), p=dict(zip(["const"] + cols, map(float, m.pvalues))))
        except Exception as ex:  # noqa: BLE001
            out[name] = dict(n=int(len(xx)), error=str(ex)[:200])
    ok.to_csv(T / "signals_results.csv", index=False)
    json.dump(out, open(T / "primary.json", "w"), indent=1, default=float)
    print(json.dumps({k: out[k] for k in ("eligible_signals", "papers", "status", "negative_controls_used", "null", "H1", "H1_sd_null", "H1_null_propagated", "survival_threshold", "H2", "uncalibrated_replication", "variants")}, indent=1, default=float))


if __name__ == "__main__":
    main()
