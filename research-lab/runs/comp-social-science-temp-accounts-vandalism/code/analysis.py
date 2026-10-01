#!/usr/bin/env python
"""Staggered difference-in-differences (plan.md sec 4-5; deviations.md D3).

Inputs: data/processed/agg/*.tsv (wiki, date, group LO/REG/ACCT, n, n_temp, rev24, rev48) from code/extract.awk.
Treatment date per wiki: first day on which temporary-account edits are >= THRESH of logged-out content edits.
Panel: wiki x calendar month, 2024-01 to 2026-06; the treatment month is dropped.
Estimator: Callaway & Sant'Anna (2021) group-time ATTs with not-yet-treated controls and the universal base period g-1;
event-time aggregation weights cohorts by their number of wikis; overall ATT = mean of event months +1..+6.
Inference: cluster bootstrap over wikis (2,000 draws).

Usage: analysis.py [--thresh 0.01] [--window 48] [--exclude enwiki] [--tag NAME]
Output: results/tables/did_{tag}.csv (estimates), results/tables/eventstudy_{tag}.csv, results/tables/treatment_dates_{tag}.csv,
        results/tables/panel_{tag}.parquet
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
PROC, TAB = RUN / "data" / "processed", RUN / "results" / "tables"
LAST_MONTH = pd.Period("2026-07", "M")                                # deviations.md D5 (snapshot runs through August 2026)
EVENTS = list(range(-12, 0)) + list(range(1, 7))
NBOOT = 2000
AGG = "agg_v2"                                                         # cross-wiki imports excluded (deviations.md D5)


def load():
    parts = [pd.read_csv(f, sep="\t", header=None, names=["wiki", "date", "group", "n", "n_temp", "rev24", "rev48"])
             for f in sorted((PROC / AGG).glob("*.tsv")) if f.stat().st_size > 0]
    d = pd.concat(parts, ignore_index=True)
    return d.groupby(["wiki", "date", "group"], as_index=False)[["n", "n_temp", "rev24", "rev48"]].sum()


def treatment_dates(d, thresh):
    lo = d[d.group == "LO"].copy()
    lo["share"] = lo.n_temp / lo.n
    first = lo[lo.share >= thresh].groupby("wiki").date.min()
    return pd.to_datetime(first)


def panel(d, tdates, window):
    d = d.copy()
    d["month"] = pd.to_datetime(d.date).dt.to_period("M")
    d = d[d.month <= LAST_MONTH]
    rv = f"rev{window}"
    p = d.pivot_table(index=["wiki", "month"], columns="group", values=["n", rv, "n_temp"], aggfunc="sum").fillna(0)
    p.columns = [f"{a}_{b}" for a, b in p.columns]
    p = p.reset_index()
    p["Y_LO"] = p[f"{rv}_LO"] / p["n_LO"].replace(0, np.nan)
    p["Y_REG"] = p[f"{rv}_REG"] / p["n_REG"].replace(0, np.nan)
    p["GAP"] = p.Y_LO - p.Y_REG
    p["logN_LO"] = np.log(p.n_LO.replace(0, np.nan))
    p["logACCT"] = np.log(p.get("n_ACCT", pd.Series(0, index=p.index)).replace(0, np.nan))
    p["temp_share"] = p["n_temp_LO"] / p["n_LO"].replace(0, np.nan)
    p["g"] = p.wiki.map(lambda w: tdates[w].to_period("M") if w in tdates.index else pd.NaT)
    p = p[~(p.month == p.g)]                                             # drop the partial treatment month
    return p


def matrices(p, outcome):
    Y = p.pivot(index="wiki", columns="month", values=outcome)
    months = list(Y.columns)
    gser = p.groupby("wiki").g.first().reindex(Y.index)
    # -1: never treated; beyond the last month: not yet treated throughout; BEFORE the first month: already treated when the
    # window opens, so such wikis can be neither treated nor controls and are dropped (deviations.md D5)
    code = []
    for x in gser:
        if pd.isna(x):
            code.append(-1)
        elif x in months:
            code.append(months.index(x))
        elif x > months[-1]:
            code.append(len(months) + 100)
        else:
            code.append(-2)
    gidx = np.array(code)
    keep = gidx != -2
    return Y.values.astype(float)[keep], gidx[keep], months


def att_es(Y, gidx, months, w=None, cells=None):
    """Callaway-Sant'Anna ATT(g, t) with not-yet-treated controls and universal base period g - 1, aggregated to event
    time with cohort weights = (bootstrap-weighted) number of treated wikis. w: per-wiki bootstrap counts."""
    W, M = Y.shape
    w = np.ones(W) if w is None else w
    es_num, es_den, pre_num = {}, {}, {}
    for c in sorted(set(gidx[(gidx >= 1) & (gidx < M)])):
        b = c - 1
        T = gidx == c
        for e in EVENTS:
            t = c + e
            if t < 0 or t >= M or t == b:
                continue
            C = (gidx == -1) | (gidx > max(t, b))
            C &= ~T
            dT, dC = Y[:, t] - Y[:, b], Y[:, t] - Y[:, b]
            wt = w * T * np.isfinite(dT)
            wc = w * C * np.isfinite(dC)
            if wt.sum() == 0 or wc.sum() == 0:
                continue
            att = np.nansum(wt * dT) / wt.sum() - np.nansum(wc * dC) / wc.sum()
            if cells is not None:
                cells.append(dict(cohort=str(months[c]), e=e, att=att, weight=wt.sum(), n_controls=int((wc > 0).sum())))
            es_num[e] = es_num.get(e, 0) + att * wt.sum()
            es_den[e] = es_den.get(e, 0) + wt.sum()
            if 1 <= e <= 6:
                pre = Y[:, max(0, c - 12):c]
                pm = np.nanmean(pre, axis=1)
                ok = wt > 0
                pre_num[e] = pre_num.get(e, 0) + np.nansum(wt[ok] * pm[ok])
    es = pd.Series({e: es_num[e] / es_den[e] for e in es_num}).sort_index()
    post = [e for e in range(1, 7) if e in es_den]
    if not post:
        return es, np.nan, np.nan
    tot = sum(es_den[e] for e in post)
    overall = sum(es_num[e] for e in post) / tot
    pre_mean = sum(pre_num[e] for e in post) / tot
    return es, overall, pre_mean


def bootstrap(Y, gidx, months, nboot=NBOOT, seed=0, vol=None):
    rng = np.random.default_rng(seed)
    W = Y.shape[0]
    ov, rel, ess = [], [], []
    for _ in range(nboot):
        w = np.bincount(rng.integers(0, W, W), minlength=W).astype(float)
        if vol is not None:
            w = w * vol
        es, o, pm = att_es(Y, gidx, months, w)
        ov.append(o)
        rel.append(o / pm if pm else np.nan)
        ess.append(es)
    return np.array(ov), np.array(rel), pd.DataFrame(ess)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thresh", type=float, default=0.01)
    ap.add_argument("--window", type=int, default=48)
    ap.add_argument("--exclude", default="")
    ap.add_argument("--tag", default="primary")
    ap.add_argument("--nboot", type=int, default=NBOOT)
    ap.add_argument("--weight", default="wikis", choices=["wikis", "edits"])
    a = ap.parse_args()
    d = load()
    if a.exclude:
        d = d[~d.wiki.isin(a.exclude.split(","))]
    td = treatment_dates(d, a.thresh)
    td.rename("treatment_date").to_csv(TAB / f"treatment_dates_{a.tag}.csv")
    p = panel(d, td, a.window)
    p.to_parquet(TAB / f"panel_{a.tag}.parquet", index=False)
    rows, es_rows = [], []
    for outcome in ("Y_LO", "Y_REG", "GAP", "logN_LO", "logACCT"):
        Y, gidx, months = matrices(p, outcome)
        vol = None
        if a.weight == "edits":                                          # weight wikis by pre-window logged-out edits
            nl = p.pivot(index="wiki", columns="month", values="n_LO")
            vol = nl.loc[:, [m for m in nl.columns if m < pd.Period("2024-11", "M")]].sum(axis=1).values.astype(float)
            vol = vol / vol.mean()
        cells = []
        es, ov, pm = att_es(Y, gidx, months, vol, cells)
        b_ov, b_rel, b_es = bootstrap(Y, gidx, months, a.nboot, vol=vol)
        if outcome == "Y_LO":
            c = pd.DataFrame(cells)
            post = c[c.e.between(1, 6)]
            coh = post.groupby("cohort").apply(lambda x: pd.Series(dict(att=np.average(x.att, weights=x.weight), weight=x.weight.sum())))
            coh["weight_share"] = coh.weight / coh.weight.sum()
            coh.to_csv(TAB / f"cohort_att_{a.tag}.csv")
            single = post[post.n_controls == 1].weight.sum() / post.weight.sum()
            print("per-cohort post ATT (Y_LO):", coh.att.round(4).to_dict(), "| share of post weight with a single control wiki: %.2f" % single, flush=True)
        lo, hi = np.nanpercentile(b_ov, [2.5, 97.5])
        rel = ov / pm if outcome in ("Y_LO", "Y_REG") and pm else np.nan
        rlo, rhi = (np.nanpercentile(b_rel, [2.5, 97.5]) if outcome in ("Y_LO", "Y_REG") else (np.nan, np.nan))
        # pre-trend joint test: Wald on leads -12..-2 with bootstrap covariance
        leads = [e for e in range(-12, -1) if e in es.index and e in b_es.columns]
        if leads:
            v = es[leads].values
            cov = np.cov(b_es[leads].dropna().values, rowvar=False)
            wald = float(v @ np.linalg.pinv(cov) @ v)
            from scipy.stats import chi2
            p_pre = float(1 - chi2.cdf(wald, len(leads)))
        else:
            p_pre = np.nan
        near = [e for e in range(-6, -1) if e in es.index and e in b_es.columns]
        cov_n = np.cov(b_es[near].dropna().values, rowvar=False)
        from scipy.stats import chi2 as _chi2
        p_near = float(1 - _chi2.cdf(float(es[near].values @ np.linalg.pinv(cov_n) @ es[near].values), len(near)))
        if outcome.startswith("log"):                                    # log points -> percentage change
            rel, rlo, rhi = np.expm1(ov), np.expm1(lo), np.expm1(hi)
        rows.append(dict(outcome=outcome, att=ov, lo=lo, hi=hi, pre_mean=pm, rel=rel, rel_lo=rlo, rel_hi=rhi,
                         pretrend_p=p_pre, pretrend_p_near=p_near, n_wikis=p.wiki.nunique(), n_cohorts=int(len(set(gidx[(gidx >= 1) & (gidx < len(months))]))),
                         thresh=a.thresh, window=a.window, exclude=a.exclude))
        for e in es.index:
            ci = np.nanpercentile(b_es[e], [2.5, 97.5]) if e in b_es.columns else (np.nan, np.nan)
            es_rows.append(dict(outcome=outcome, e=e, att=es[e], lo=ci[0], hi=ci[1]))
        print(f"{outcome:8s} ATT {ov:+.5f} [{lo:+.5f}, {hi:+.5f}]  rel {rel:+.3f} [{rlo:+.3f}, {rhi:+.3f}]  pre-trend p {p_pre:.3f} (leads -6..-2: {p_near:.3f})", flush=True)
    out = pd.DataFrame(rows)
    r = out.set_index("outcome").loc["Y_LO"]
    out["verdict_H1"] = ""
    v = "supported" if (r.rel >= 0.10 and r.rel_lo > 0) else ("contradicted" if r.rel_hi < 0.10 else "inconclusive")
    out.loc[out.outcome == "Y_LO", "verdict_H1"] = v
    out.to_csv(TAB / f"did_{a.tag}.csv", index=False)
    pd.DataFrame(es_rows).to_csv(TAB / f"eventstudy_{a.tag}.csv", index=False)
    print("H1 verdict:", v)


if __name__ == "__main__":
    sys.exit(main())
