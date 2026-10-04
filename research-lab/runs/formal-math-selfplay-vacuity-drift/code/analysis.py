"""Primary and secondary analyses (plan.md sections 4-5; deviations D2). Reads results/rows/*.jsonl + samples.
Usage: analysis.py [rows_dir] (default results/rows). Writes results/tables/*.csv and prints the verdict.
Eligible rows: re-verified and split check passed. V = swap or automation certificate."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
EARLY, LATE = list(range(1, 10)), list(range(38, 48))
CONTRASTS = {"primary: 38-47 vs 1-9": (LATE, EARLY), "phase 1: 14-23 vs 1-9": (list(range(14, 24)), EARLY),
             "phase 2: 38-47 vs 25-33": (LATE, list(range(25, 34))), "phase 2 (25-47) vs phase 1 (1-23)": (list(range(25, 48)), list(range(1, 24)))}


def load(rows_dir, name, sample):
    d = pd.DataFrame([json.loads(line) for line in open(rows_dir / f"{name}.jsonl")])
    s = pd.read_parquet(RUN / "data" / "samples" / sample).drop(columns=["target"], errors="ignore")
    d = s.merge(d, on="row_id", how="inner")
    d["eligible"] = (d.reverify == True) & (d.split_ok == True)  # noqa: E712
    d["V"] = d.vacuous.fillna(False).astype(bool)
    return d


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (c - h, c + h)


def window(d, iters, col="V", weight_col="N_iter"):
    """Population-weighted rate over iteration strata: (p, var, n_eligible, k_vacuous)."""
    g = d[d.eligible & d.iteration.isin(iters)].groupby("iteration").agg(k=(col, "sum"), n=(col, "size"), N=(weight_col, "first"))
    W = g.N / g.N.sum()
    ph = g.k / g.n
    return float((W * ph).sum()), float((W ** 2 * ph * (1 - ph) / g.n).sum()), int(g.n.sum()), int(g.k.sum())


def contrast(d, late, early, col="V", weight_col="N_iter"):
    pL, vL, nL, kL = window(d, late, col, weight_col)
    pE, vE, nE, kE = window(d, early, col, weight_col)
    se = np.sqrt(vL + vE)
    z = (pL - pE) / se if se > 0 else np.nan
    p1 = 1 - stats.norm.cdf(z) if se > 0 else np.nan
    if pL > 0 and pE > 0:
        lrr = np.log(pL / pE)
        s = np.sqrt(vL / pL ** 2 + vE / pE ** 2)
        rr, lo, hi = pL / pE, np.exp(lrr - 1.96 * s), np.exp(lrr + 1.96 * s)
    else:
        rr, lo, hi = (np.inf if pL > 0 else np.nan), np.nan, np.nan
    return dict(p_late=pL, p_early=pE, n_late=nL, n_early=nE, k_late=kL, k_early=kE, RR=rr, RR_lo=lo, RR_hi=hi, z=z, p_one_sided=p1)


def verdict(c):
    if c["k_late"] + c["k_early"] < 10:
        return "Inconclusive (fewer than 10 certified vacuous rows)"
    if c["RR"] >= 2 and c["p_one_sided"] < 0.01:
        return "Supported"
    if np.isfinite(c["RR_hi"]) and c["RR_hi"] < 2:
        return "Refuted"
    return "Inconclusive"


def population_unique():
    """Unique conjecture statements per iteration in the full corpus (cached in results/tables/stp_unique_statements.csv)."""
    f = TAB / "stp_unique_statements.csv"
    if not f.exists():
        fs = sorted((RUN / "data" / "raw" / "STP_Lean_0320" / "data").glob("*.parquet"))
        df = pd.concat([pd.read_parquet(x, columns=["prompt", "iteration", "tag"]) for x in fs], ignore_index=True)
        df = df[df.tag.astype(str).str.contains("conjecture")]
        df.groupby("iteration").prompt.nunique().rename("unique_statements").to_csv(f)
    return pd.read_csv(f, index_col=0).unique_statements


def statement_level(d):
    """Unique (iteration, statement) units; vacuous if any sampled row is certified. Weights: unique statements per iteration."""
    e = d[d.eligible].copy()
    e["stmt"] = e.prompt.str.split("```lean4\n").str[1]
    u = e.groupby(["iteration", "stmt"]).agg(V=("V", "max")).reset_index()
    u["eligible"] = True
    u["N_u"] = u.iteration.map(population_unique())
    return u


def main(rows_dir=RUN / "results" / "rows"):
    rows_dir = Path(rows_dir)
    out = {}
    c = load(rows_dir, "stp_conjecture", "stp_conjecture.parquet")
    # pipeline health by iteration
    health = c.groupby("iteration").agg(n=("row_id", "size"), reverify=("reverify", lambda x: x.fillna(False).mean()),
                                        split_ok=("split_ok", lambda x: x.fillna(False).mean()), eligible=("eligible", "sum"), k=("V", "sum"))
    per = c[c.eligible].groupby("iteration").agg(k=("V", "sum"), n=("V", "size"), N=("N_iter", "first"))
    per["rate"] = per.k / per.n
    per[["lo", "hi"]] = [wilson(k, n) for k, n in zip(per.k, per.n)]
    per["swap"] = c[c.eligible].groupby("iteration").swap.apply(lambda x: x.fillna(False).mean())
    per["auto"] = c[c.eligible].groupby("iteration").auto.apply(lambda x: x.notna().mean())
    per = per.join(health[["reverify", "split_ok"]])
    per.to_csv(TAB / "per_iteration.csv")
    res = []
    for name, (L, E) in CONTRASTS.items():
        r = contrast(c, L, E)
        r["contrast"] = name
        res.append(r)
    # statement-level primary
    u = statement_level(c)
    r = contrast(u, LATE, EARLY, weight_col="N_u"); r["contrast"] = "primary, statement level"; res.append(r)
    # unweighted pooled sensitivity
    cc = c.copy(); cc["one"] = 1
    r = contrast(cc, LATE, EARLY, weight_col="one"); r["contrast"] = "primary, unweighted"; res.append(r)
    # split repair sensitivity (D2)
    rp = rows_dir / "stp_conjecture_repair.jsonl"
    if rp.exists():
        rr = pd.DataFrame([json.loads(line) for line in open(rp)])
        rr = rr[rr.get("repair_ok", False) == True]  # noqa: E712
        c2 = c.copy()
        m = c2.row_id.isin(rr.row_id)
        c2.loc[m, "eligible"] = True
        c2.loc[m, "V"] = c2.loc[m, "row_id"].map(rr.set_index("row_id").vacuous_repair.fillna(False)).astype(bool)
        r = contrast(c2, LATE, EARLY); r["contrast"] = f"primary, split repair (+{int(m.sum())} rows)"; res.append(r)
    con = pd.DataFrame(res).set_index("contrast")
    con.to_csv(TAB / "contrasts.csv")
    prim = con.loc["primary: 38-47 vs 1-9"].to_dict()
    out["verdict"] = verdict(prim)
    out["verdict_statement_level"] = verdict(con.loc["primary, statement level"].to_dict())
    # trend
    tr = []
    for name, rng in [("all", range(1, 48)), ("phase 1", range(1, 24)), ("phase 2", range(25, 48))]:
        p = per[per.index.isin(rng)]
        rho, pv = stats.spearmanr(p.index, p.rate)
        tr.append(dict(scope=name, n_iter=len(p), spearman_rho=rho, p=pv))
    pd.DataFrame(tr).to_csv(TAB / "trend.csv", index=False)
    # methods and triviality (primary windows)
    e = c[c.eligible & c.iteration.isin(EARLY + LATE)]
    vac = e[e.V]
    meth = dict(n_vacuous=len(vac), swap_only=int((vac.swap.fillna(False) & vac.auto.isna()).sum()), auto_only=int((~vac.swap.fillna(False).astype(bool) & vac.auto.notna()).sum()),
                both=int((vac.swap.fillna(False).astype(bool) & vac.auto.notna()).sum()), trivial_rate_early=e[e.iteration.isin(EARLY)].trivial.fillna(False).mean(),
                trivial_rate_late=e[e.iteration.isin(LATE)].trivial.fillna(False).mean())
    meth.update({f"auto_{t}": int((vac.auto == t).sum()) for t in vac.auto.dropna().unique()})
    pd.DataFrame([meth]).to_csv(TAB / "methods.csv", index=False)
    # STP weight
    try:
        import statsmodels.formula.api as smf
        ce = c[c.eligible].copy(); ce["Vi"] = ce.V.astype(int); ce["w10"] = ce.weight * 10
        fit = smf.logit("Vi ~ w10 + C(iteration)", data=ce).fit(disp=0)
        out["weight_OR_per_0.1"] = float(np.exp(fit.params["w10"])); out["weight_OR_ci"] = [float(x) for x in np.exp(fit.conf_int().loc["w10"])]
    except Exception as ex:  # noqa: BLE001
        out["weight_logit_error"] = str(ex)[:200]
    # statement-tag control
    sname = rows_dir / "stp_statement.jsonl"
    if sname.exists():
        s = load(rows_dir, "stp_statement", "stp_statement.parquet")
        sp = s[s.eligible].groupby("iteration").agg(k=("V", "sum"), n=("V", "size"))
        sp["rate"] = sp.k / sp.n
        sp.to_csv(TAB / "statement_per_iteration.csv")
        r = contrast(s, LATE, list(range(0, 10)))
        out["statement_control_38_47_vs_0_9"] = {k: r[k] for k in ("p_late", "p_early", "RR", "RR_lo", "RR_hi", "k_late", "k_early")}
        out["statement_spearman"] = list(stats.spearmanr(sp.index, sp.rate))
    # other corpora
    oc = []
    for name in ["workbook", "dsp1", "sftv2", "numina"]:
        f = rows_dir / f"{name}.jsonl"
        if not f.exists():
            continue
        o = load(rows_dir, name, f"{name}.parquet")
        e = o[o.eligible]
        k, n = int(e.V.sum()), len(e)
        row = dict(corpus=name, sampled=len(o), reverify=o.reverify.fillna(False).mean(), eligible=n, vacuous=k, rate=k / n if n else np.nan,
                   lo=wilson(k, n)[0], hi=wilson(k, n)[1])
        if name == "sftv2":
            en = e[~e.negation]
            row.update(rate_excl_negation=en.V.mean(), n_excl_negation=len(en))
        if name == "numina":
            for a in ["autoformalizer", "human"]:
                ea = e[e.author == a]
                row[f"rate_{a}"] = ea.V.mean(); row[f"n_{a}"] = len(ea)
            ew = e.dropna(subset=["win_rate"])
            if ew.V.sum() > 0:
                row["win_rate_mean_vacuous"] = ew[ew.V].win_rate.mean(); row["win_rate_mean_nonvacuous"] = ew[~ew.V].win_rate.mean()
                row["win_rate_mannwhitney_p"] = stats.mannwhitneyu(ew[ew.V].win_rate, ew[~ew.V].win_rate).pvalue
        oc.append(row)
    if oc:
        pd.DataFrame(oc).to_csv(TAB / "other_corpora.csv", index=False)
    # random sample of 100 certified-vacuous rows for cause categorisation
    allv = c[c.eligible & c.V]
    if len(allv):
        smp = allv.sample(min(100, len(allv)), random_state=7)
        smp.assign(statement=smp.prompt.str.split("```lean4\n").str[1].str.split("open BigOperators Real Nat Topology Rat").str[-1].str.strip())[
            ["row_id", "iteration", "swap", "auto", "statement"]].to_csv(TAB / "vacuous_sample_100.csv", index=False)
    json.dump(out, open(TAB / "summary.json", "w"), indent=1, default=float)
    pd.set_option("display.width", 250)
    print(con.round(4).to_string())
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main(*sys.argv[1:])
