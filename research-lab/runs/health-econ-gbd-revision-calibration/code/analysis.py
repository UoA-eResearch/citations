"""Primary and secondary analyses (plan sections 5-7). Inputs: data/panel.parquet (build.py), data/quality.parquet
(quality.py). Outputs: results/tables/.

Cells: country x cause x year (2019, 2021). Point estimate p, 95% UI [L, U], release r in {21, 23}.

C1 (naive coverage): share of eligible cells with L21 <= p23 <= U21. Eligible: U21 > L21.
C2 (combined calibration): share of eligible cells with |z| <= 1.96, where
    z = (ln p23 - ln p21) / sqrt(s21^2 + s23^2),   s_r = (ln U_r - ln L_r) / (2 * 1.959964).
    Eligible: p, L > 0 in both releases and U > L in both. If both releases' intervals are calibrated (log-normal) and
    their errors are not negatively correlated, P(|z| <= 1.96) >= 0.95.
E1 (benchmark for C1): the C1 expected if both releases were calibrated with independent errors:
    Phi((ln U21 - ln p21)/sd) - Phi((ln L21 - ln p21)/sd), sd = sqrt(s21^2 + s23^2).
Intervals: two-way (country x cause) pigeonhole bootstrap, B = 2000, seed 20261012; a country-only bootstrap as a
sensitivity check. Group contrasts resample countries within each group and causes jointly."""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
SEED = 20261012
B = 2000
Z = 1.959964
SESOI = 0.05


def metrics(p):
    """Adds eligibility flags and outcomes; p is the panel (optionally with rates already substituted)."""
    p = p.copy()
    p["elig1"] = p.U21 > p.L21
    p["cov1"] = (p.L21 <= p.p23) & (p.p23 <= p.U21)
    pos = (p[["p21", "L21", "p23", "L23"]] > 0).all(axis=1) & (p.U21 > p.L21) & (p.U23 > p.L23)
    p["elig2"] = pos
    with np.errstate(divide="ignore", invalid="ignore"):
        s21 = (np.log(p.U21) - np.log(p.L21)) / (2 * Z)
        s23 = (np.log(p.U23) - np.log(p.L23)) / (2 * Z)
        sd = np.sqrt(s21 ** 2 + s23 ** 2)
        p["z"] = np.where(pos, (np.log(p.p23) - np.log(p.p21)) / sd, np.nan)
        p["e1"] = np.where(pos, norm.cdf((np.log(p.U21) - np.log(p.p21)) / sd) - norm.cdf((np.log(p.L21) - np.log(p.p21)) / sd), np.nan)
        p["width_ratio"] = np.where(pos, s23 / s21, np.nan)
    p["cov2"] = np.abs(p.z) <= Z
    p["above"] = p.p23 > p.U21
    p["below"] = p.p23 < p.L21
    return p


def matrices(p, ycol, ecol, countries, causes):
    """Country x cause sums of outcome and eligibility (over years)."""
    ci = {c: i for i, c in enumerate(countries)}
    ki = {k: i for i, k in enumerate(causes)}
    Y = np.zeros((len(countries), len(causes)))
    E = np.zeros_like(Y)
    q = p[p[ecol] & p.location_id.isin(ci) & p.cause_id.isin(ki)]
    np.add.at(Y, (q.location_id.map(ci).values, q.cause_id.map(ki).values), q[ycol].astype(float).values)
    np.add.at(E, (q.location_id.map(ci).values, q.cause_id.map(ki).values), 1.0)
    return Y, E


def boot_share(p, ycol, ecol, groups=None, two_way=True, b=B, seed=SEED):
    """Share of ycol among ecol cells, overall or by group (dict name -> country ids), with bootstrap draws.
    Returns dict name -> (estimate, draws). Groups share the cause draw in each replicate."""
    causes = np.array(sorted(p.cause_id.unique()))
    groups = groups or {"all": np.array(sorted(p.location_id.unique()))}
    mats = {g: matrices(p, ycol, ecol, cs, causes) for g, cs in groups.items()}
    rng = np.random.default_rng(seed)
    draws = {g: np.empty(b) for g in groups}
    for i in range(b):
        bk = rng.multinomial(len(causes), np.full(len(causes), 1 / len(causes))) if two_way else np.ones(len(causes))
        for g, (Y, E) in mats.items():
            a = rng.multinomial(Y.shape[0], np.full(Y.shape[0], 1 / Y.shape[0]))
            num, den = a @ Y @ bk, a @ E @ bk
            draws[g][i] = num / den if den > 0 else np.nan
    return {g: (float(Y.sum() / E.sum()) if E.sum() else np.nan, draws[g]) for g, (Y, E) in mats.items()}


def ci(d):
    lo, hi = np.nanpercentile(d, [2.5, 97.5])
    return float(lo), float(hi)


def summary(est, draws):
    lo, hi = ci(draws)
    return dict(estimate=est, lower95=lo, upper95=hi)


def verdict_below(s, thr):
    return "Supported" if s["upper95"] < thr else "Refuted" if s["lower95"] >= thr else "Inconclusive"


def groups_of(q, col="quality_group"):
    return {g: np.array(sorted(q[q[col] == g].location_id)) for g in sorted(q[col].dropna().unique())}


def primary(p, q):
    out = {}
    n1, n2 = int(p.elig1.sum()), int(p.elig2.sum())
    out["n_cells"] = int(len(p))
    out["n_eligible_C1"] = n1
    out["n_eligible_C2"] = n2
    g = groups_of(q)
    out["n_countries_by_group"] = {k: int(len(v)) for k, v in g.items()}
    # H1: overall C1 < 0.95
    est, d = boot_share(p, "cov1", "elig1")["all"]
    out["H1"] = summary(est, d) | {"verdict": verdict_below(summary(est, d), 0.95)}
    # H2: C1 by quality group; low < 0.80 and high > 0.90
    r = boot_share(p, "cov1", "elig1", groups=g)
    s = {k: summary(*v) for k, v in r.items()}
    diff = r["high"][1] - r["low"][1]
    dsum = dict(estimate=r["high"][0] - r["low"][0], lower95=ci(diff)[0], upper95=ci(diff)[1])
    sup = s["low"]["upper95"] < 0.80 and s["high"]["lower95"] > 0.90
    ref = s["low"]["lower95"] >= 0.80 or s["high"]["upper95"] <= 0.90 or dsum["upper95"] <= 0
    out["H2"] = dict(by_group=s, high_minus_low=dsum, verdict="Supported" if sup else "Refuted" if ref else "Inconclusive")
    # H3: overall C2 < 0.95
    est, d = boot_share(p, "cov2", "elig2")["all"]
    out["H3"] = summary(est, d) | {"verdict": verdict_below(summary(est, d), 0.95)}
    # H4: C2 high - low >= SESOI
    r = boot_share(p, "cov2", "elig2", groups=g)
    s = {k: summary(*v) for k, v in r.items()}
    diff = r["high"][1] - r["low"][1]
    dsum = dict(estimate=r["high"][0] - r["low"][0], lower95=ci(diff)[0], upper95=ci(diff)[1])
    v = "Supported" if (dsum["lower95"] > 0 and dsum["estimate"] >= SESOI) else "Refuted" if dsum["upper95"] < SESOI else "Inconclusive"
    out["H4"] = dict(by_group=s, high_minus_low=dsum, verdict=v)
    return out


def row(name, p, ycol, ecol, groups=None, two_way=True):
    r = boot_share(p, ycol, ecol, groups=groups, two_way=two_way, b=1000)
    return [dict(analysis=name, group=k, n_cells=int(p[ecol].sum()) if k == "all" else None, **summary(*v)) for k, v in r.items()]


def secondary(p, q):
    rows = []
    g = groups_of(q)
    # country-only bootstrap (sensitivity of the interval method)
    rows += row("C1, country-only bootstrap", p, "cov1", "elig1", two_way=False)
    rows += row("C2, country-only bootstrap", p, "cov2", "elig2", two_way=False)
    # by year
    for y in (2019, 2021):
        py = p[p.year == y]
        rows += row(f"C1, year {y}", py, "cov1", "elig1", groups=g)
        rows += row(f"C2, year {y}", py, "cov2", "elig2", groups=g)
    # rates (each release's own population)
    pr = p.copy()
    for c in ("p21", "L21", "U21"):
        pr[c] = p[c] / p.pop21
    for c in ("p23", "L23", "U23"):
        pr[c] = p[c] / p.pop23
    pr = metrics(pr)
    rows += row("C1, all-age death rates", pr, "cov1", "elig1", groups=g)
    rows += row("C2, all-age death rates", pr, "cov2", "elig2", groups=g)
    # by level-1 cause group
    for l1 in sorted(p.l1_name.dropna().unique()):
        rows += row(f"C1, {l1}", p[p.l1_name == l1], "cov1", "elig1")
        rows += row(f"C2, {l1}", p[p.l1_name == l1], "cov2", "elig2")
    # excluding COVID-19-related causes
    nc = p[~(p.cause_name.str.contains("COVID", case=False) | p.l2_name.fillna("").str.contains("COVID", case=False))]
    rows += row("C1, excluding COVID-19 causes", nc, "cov1", "elig1", groups=g)
    rows += row("C2, excluding COVID-19 causes", nc, "cov2", "elig2", groups=g)
    # cells with at least 10 deaths in GBD 2021
    big = p[p.p21 >= 10]
    rows += row("C1, cells with >= 10 deaths (GBD 2021)", big, "cov1", "elig1", groups=g)
    rows += row("C2, cells with >= 10 deaths (GBD 2021)", big, "cov2", "elig2", groups=g)
    # benchmark E1 and direction of misses, width ratio
    for k, cs in ({"all": None} | g).items():
        x = p if cs is None else p[p.location_id.isin(cs)]
        e = x[x.elig1 & x.elig2]
        rows.append(dict(analysis="E1, expected C1 if calibrated and independent (mean over cells eligible for both)", group=k,
                         n_cells=len(e), estimate=float(e.e1.mean())))
        rows.append(dict(analysis="C1 over the same cells as E1", group=k, n_cells=len(e), estimate=float(e.cov1.mean())))
        m = x[x.elig1 & ~x.cov1]
        rows.append(dict(analysis="share of C1 misses with p23 above U21", group=k, n_cells=len(m), estimate=float(m.above.mean()) if len(m) else np.nan))
        rows.append(dict(analysis="median width ratio s23/s21", group=k, n_cells=int(x.elig2.sum()), estimate=float(np.nanmedian(x.width_ratio))))
    # alternative quality measures
    qg = q.copy()
    t = qg.garbage_pct_2010_21
    qg["garbage_group"] = np.where(t.isna(), "no VR in GBD table", pd.qcut(t, 3, labels=["garbage low tertile", "garbage mid tertile", "garbage high tertile"]).astype(str))
    rows += row("C1 by GBD garbage-code tertile (2010-21)", p, "cov1", "elig1", groups=groups_of(qg, "garbage_group"))
    rows += row("C2 by GBD garbage-code tertile (2010-21)", p, "cov2", "elig2", groups=groups_of(qg, "garbage_group"))
    qg["who5"] = qg.who_quality
    rows += row("C1 by WHO class (5 levels)", p, "cov1", "elig1", groups=groups_of(qg, "who5"))
    rows += row("C2 by WHO class (5 levels)", p, "cov2", "elig2", groups=groups_of(qg, "who5"))
    sec = pd.DataFrame(rows)
    sec.to_csv(TAB / "secondary.csv", index=False)
    return sec


def mixed(p, q):
    """Secondary: miss2 ~ quality group + year + level-1 group, with country and cause variance components (VB)."""
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    x = p[p.elig2].merge(q[["location_id", "quality_group"]], on="location_id")
    x["miss"] = (~x.cov2).astype(float)
    x["yr"] = x.year.astype(str)
    out = {}
    m = BinomialBayesMixedGLM.from_formula("miss ~ C(quality_group, Treatment('high')) + yr + l1_name",
                                           {"country": "0 + C(location_id)", "cause": "0 + C(cause_id)"}, x)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        r = m.fit_vb(minim_opts={"maxiter": 5000})
    for n, b, s in zip(m.exog_names, r.fe_mean, r.fe_sd):
        if "quality_group" in n:
            out[n] = dict(OR=float(np.exp(b)), lower95=float(np.exp(b - Z * s)), upper95=float(np.exp(b + Z * s)))
    out["sd_country_logit"] = float(np.exp(r.vcp_mean[0]))
    out["sd_cause_logit"] = float(np.exp(r.vcp_mean[1]))
    out["optimiser_converged_flag"] = not any("converge" in str(z.message).lower() for z in w)
    return out


def tables(p, q):
    by_c = p.groupby(["location_id", "location_name"]).apply(lambda x: pd.Series(dict(
        n1=int(x.elig1.sum()), C1=x.cov1[x.elig1].mean(), n2=int(x.elig2.sum()), C2=x.cov2[x.elig2].mean())), include_groups=False).reset_index()
    by_c.merge(q[["location_id", "who_quality", "quality_group", "usability_mid", "garbage_pct_2010_21"]], on="location_id").to_csv(TAB / "by_country.csv", index=False)
    by_k = p.groupby(["cause_id", "cause_name", "l1_name"]).apply(lambda x: pd.Series(dict(
        n1=int(x.elig1.sum()), C1=x.cov1[x.elig1].mean(), n2=int(x.elig2.sum()), C2=x.cov2[x.elig2].mean(),
        median_abs_z=float(np.nanmedian(np.abs(x.z))))), include_groups=False).reset_index()
    by_k.to_csv(TAB / "by_cause.csv", index=False)


def main():
    TAB.mkdir(parents=True, exist_ok=True)
    p = metrics(pd.read_parquet(RUN / "data" / "panel.parquet"))
    q = pd.read_parquet(RUN / "data" / "quality.parquet")
    out = primary(p, q)
    json.dump(out, open(TAB / "primary.json", "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))
    sec = secondary(p, q)
    print(sec.to_string())
    mm = mixed(p, q)
    json.dump(mm, open(TAB / "mixed_model.json", "w"), indent=1)
    print(mm)
    tables(p, q)


if __name__ == "__main__":
    main(*sys.argv[1:])
