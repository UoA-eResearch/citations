"""Panel and staggered DiD (plan section 2) and secondaries 1-5 (section 3).

Panel: linked works x calendar years 2008-2025; outcome = Open Library editions with that publish year.
Treated cohorts: renewed works registered 1923-1929 (expiry 2019-2025). Controls: never-renewed works of 1923-1930 and
renewed 1930 works (expiry 2026, outside the window). PPML with work and year fixed effects and saturated cohort x
event-time dummies (Sun-Abraham), event time binned to [-8, +6], reference -1; SEs clustered by work.
Primary: RR = exp(cohort-size-weighted mean of the event 0..2 coefficients) with a delta-method interval; pre-trend =
joint Wald test of the event -5..-2 coefficients (cohort-weighted per event time).

  did.py [primary|nopod|lag|placebo|ols|binary|cells]   (primary/binary also write event-study CSVs)
  did.py sensitivity                        D2: leave-one-cohort-out, calendar-year limits, reprint exclusion, and the
                                            exploratory binary / capped outcomes -> results/tables/sensitivity.csv
Writes results/tables/primary.json (or secondary_<variant>.json).
D2 (after review): a cohort whose reference cell (event -1) has zero editions is unidentified (all its dummies are
measured against zero) and is dropped and recorded, alongside D1's separated cells.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
DATA, T = RUN / "data", RUN / "results" / "tables"
Y0, Y1, EMIN, EMAX = 2008, 2025, -8, 6
POD = re.compile(r"createspace|independently published|lulu|kessinger|forgotten books|hansebooks|alpha editions|"
                 r"creative media partners|legare street|wentworth|gale ecco|general books|nabu", re.I)


def panel(variant="primary", outcome="count", drop_cohort=None, max_year=Y1, no_reprints=False):
    r = pd.read_parquet(DATA / "registrations.parquet")
    links = pd.read_parquet(DATA / "links.parquet").merge(r[["entry_id", "reg_year", "renewed"]], on="entry_id")
    links = links[links.reg_year.between(1923, 1930)]
    if no_reprints:                     # D2 sensitivity: treated works whose OL first-publish year predates registration
        links = links[~(links.renewed & (links.first_year < links.reg_year))]
    e = pd.read_parquet(DATA / "editions.parquet")
    e = e[e.pub_year.between(Y0, Y1)]
    if variant == "nopod":
        e = e[~e.publishers.fillna("").str.contains(POD)]
    if variant == "lag":
        cy = pd.to_numeric(e.created.str[:4], errors="coerce")
        cm = pd.to_numeric(e.created.str[5:7], errors="coerce")
        e = e[(cy * 12 + cm) >= (e.pub_year * 12 + 1 + 12)]
    cnt = e.groupby(["work", "pub_year"]).size().rename("y").reset_index()
    years = np.arange(Y0, Y1 + 1)
    p = pd.DataFrame([(w, t) for w in links.work for t in years], columns=["work", "year"])
    p = p.merge(cnt.rename(columns={"pub_year": "year"}), on=["work", "year"], how="left").fillna({"y": 0})
    p = p.merge(links[["work", "reg_year", "renewed"]], on="work")
    p["cohort"] = np.where(p.renewed & (p.reg_year <= 1929), p.reg_year + 96, 0)
    if outcome == "binary":             # D2 exploratory: any new edition in the year
        p["y"] = (p.y > 0).astype(float)
    elif outcome == "cap5":             # D2 exploratory: editions capped at 5 per work-year
        p["y"] = p.y.clip(upper=5)
    if drop_cohort:
        p = p[p.cohort != drop_cohort]
    p = p[p.year <= max_year]
    return p


def fit(p, shift=0):
    import pyfixest as pf
    q = p.copy()
    if shift:
        q = q[(q.cohort == 0) | (q.year < q.cohort)].copy()
        q.loc[q.cohort > 0, "cohort"] = q.loc[q.cohort > 0, "cohort"] - shift
    q["ev"] = np.where(q.cohort > 0, (q.year - q.cohort).clip(EMIN, EMAX), -999)
    cols = []
    for g in sorted(q.cohort[q.cohort > 0].unique()):
        for e in range(EMIN, EMAX + 1):
            if e == -1:
                continue
            m = (q.cohort == g) & (q.ev == e)
            if m.any():
                c = f"d_{g}_{e + 10}"
                q[c] = m.astype(float)
                cols.append((c, g, e))
    q = q[q.groupby("work").y.transform("sum") > 0]               # all-zero works carry no information in PPML
    # D1: a cohort x event dummy whose cells sum to zero is perfectly separated (MLE -inf): drop its observations and
    # do not estimate it (the ppmlhdfe convention); aggregates then average the identified cells only
    separated, ref_separated = [], []
    while True:
        sep = [(c, g, e) for c, g, e in cols if q.loc[q[c] == 1, "y"].sum() == 0]
        for c, _, _ in sep:
            q = q[q[c] == 0].drop(columns=c)
        cols = [x for x in cols if x not in sep]
        separated += sep
        # D2: a cohort with zero editions in its reference cell is unidentified: drop the cohort
        ref = [g for g in sorted(q.cohort[q.cohort > 0].unique()) if q.loc[(q.cohort == g) & (q.ev == -1), "y"].sum() == 0]
        for g in ref:
            q = q[q.cohort != g]
            for c in [c for c, gg, _ in cols if gg == g]:
                q = q.drop(columns=c)
            cols = [x for x in cols if x[1] != g]
        ref_separated += [int(g) for g in ref]
        q = q[q.groupby("work").y.transform("sum") > 0]
        if not sep and not ref:
            break
    fml = "y ~ " + " + ".join(c for c, _, _ in cols) + " | work + year"
    m = pf.fepois(fml, data=q, vcov={"CRV1": "work"})
    b = m.coef()
    names = list(b.index)
    Vm = pd.DataFrame(np.asarray(m._vcov), index=names, columns=names)
    size = q[q.cohort > 0].groupby("cohort").work.nunique()

    def agg(evs):
        w = pd.Series(0.0, index=names)
        for c, g, e in cols:
            if e in evs and c in names:
                w[c] = size[g]
        if w.sum() == 0:
            return float("nan"), float("nan")
        w = w / w.sum()
        est = float(w @ b)
        se = float(np.sqrt(w @ Vm @ w))
        return est, se
    ev_rows = []
    for e in range(EMIN, EMAX + 1):
        if e == -1:
            continue
        est, se = agg([e])
        ev_rows.append({"event": e, "coef": est, "se": se, "rr": np.exp(est)})
    est, se = agg([0, 1, 2])
    # pre-trend: joint test of the cohort-weighted event -5..-2 coefficients
    W = []
    for e in (-5, -4, -3, -2):
        w = pd.Series(0.0, index=names)
        for c, g, ee in cols:
            if ee == e and c in names:
                w[c] = size[g]
        if w.sum() > 0:
            W.append((w / w.sum()).to_numpy())
    W = np.array(W)
    v = W @ b.to_numpy()
    S = W @ Vm.to_numpy() @ W.T
    from scipy import stats
    wald = float(v @ np.linalg.pinv(S) @ v)
    p_pre = float(1 - stats.chi2.cdf(wald, df=len(v)))
    out = {"separated_cells_dropped": [f"{g}:{e}" for _, g, e in separated], "reference_separated_cohorts": ref_separated,
           "cohorts_in_model": [int(g) for g in size.index], "works_in_model": int(q.work.nunique()), "treated_works": int(q[q.cohort > 0].work.nunique()),
           "control_works": int(q[q.cohort == 0].work.nunique()), "obs": int(len(q)),
           "cohort_sizes": {int(k): int(v_) for k, v_ in size.items()},
           "rr": round(float(np.exp(est)), 4), "rr_ci": [round(float(np.exp(est - 1.96 * se)), 4), round(float(np.exp(est + 1.96 * se)), 4)],
           "log_rr": round(est, 4), "se": round(se, 4), "pretrend_wald_p": round(p_pre, 4)}
    return out, pd.DataFrame(ev_rows)


def verdict(o):
    lo, hi = o["rr_ci"]
    v = "Supported" if (o["rr"] >= 1.5 and lo > 1) else "Refuted" if hi < 1.2 else "Inconclusive"
    if o["pretrend_wald_p"] <= 0.1:
        v = "Inconclusive (pre-trend)"
    return v


def sensitivity():
    """D2, post hoc: the count outcome (preregistered) and two exploratory outcomes under a set of restrictions."""
    rows = []
    for outcome in ("count", "binary", "cap5"):
        full = panel(outcome=outcome)
        specs = [("full", {}), ("years<=2023", {"max_year": 2023}), ("years<=2022", {"max_year": 2022}),
                 ("no reprints", {"no_reprints": True}), ("no POD", {"variant": "nopod"}), ("lag filter", {"variant": "lag"})]
        specs += [(f"without cohort {g}", {"drop_cohort": g}) for g in sorted(full.cohort[full.cohort > 0].unique())]
        specs += [("placebo (-3 years)", {"shift": 3})]
        for name, kw in specs:
            kw = dict(kw)
            shift = kw.pop("shift", 0)
            try:
                o, _ = fit(panel(outcome=outcome, **kw), shift=shift)
                rows.append({"outcome": outcome, "spec": name, "rr": o["rr"], "lo": o["rr_ci"][0], "hi": o["rr_ci"][1],
                             "pretrend_p": o["pretrend_wald_p"], "treated_works": o["treated_works"],
                             "cohorts": " ".join(map(str, o["cohorts_in_model"])),
                             "ref_separated": " ".join(map(str, o["reference_separated_cohorts"])),
                             "cells_dropped": len(o["separated_cells_dropped"])})
            except Exception as ex:
                rows.append({"outcome": outcome, "spec": name, "error": str(ex)[:100]})
            print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(T / "sensitivity.csv", index=False)


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "primary"
    if variant == "sensitivity":
        sensitivity()
        return
    if variant == "cells":              # D2: generating code for the cohort x event cell counts (primary panel)
        p = panel()
        q = p[p.cohort > 0].copy()
        q["ev"] = (q.year - q.cohort).clip(EMIN, EMAX)
        c = q.groupby(["cohort", "ev"]).agg(works=("work", "nunique"), editions=("y", "sum")).reset_index()
        c.to_csv(T / "cell_counts.csv", index=False)
        print(c.pivot(index="cohort", columns="ev", values="editions").to_string())
        return
    if variant == "ols":
        import pyfixest as pf
        p = panel()
        p["ly"] = np.log1p(p.y)
        q = p.copy()
        q["post02"] = ((q.cohort > 0) & (q.year - q.cohort).between(0, 2)).astype(float)
        q["post_other"] = ((q.cohort > 0) & ((q.year - q.cohort) > 2)).astype(float)
        m = pf.feols("ly ~ post02 + post_other | work + year", data=q, vcov={"CRV1": "work"})
        base = float(q.loc[(q.cohort > 0) & (q.year < q.cohort), "ly"].mean())     # D2: treated pre-period mean
        b, se = float(m.coef()["post02"]), float(m.se()["post02"])
        out = {"model": "two-way FE OLS (post 0-2 and post >2 indicators), not Sun-Abraham",
               "coef_post02_log1p": round(b, 4), "se": round(se, 4), "treated_pre_mean_log1p": round(base, 5),
               "relative_to_pre_mean": round(b / base, 3), "relative_ci": [round((b - 1.96 * se) / base, 3), round((b + 1.96 * se) / base, 3)]}
        json.dump(out, open(T / "secondary_ols.json", "w"), indent=1)
        print(out)
        return
    p = panel(outcome="binary") if variant == "binary" else panel("primary" if variant in ("primary", "placebo") else variant)
    o, ev = fit(p, shift=3 if variant == "placebo" else 0)
    o["verdict_rule"] = verdict(o) if variant == "primary" else None
    o["variant"] = variant
    o["panel_summary"] = {"works": int(p.work.nunique()), "editions_in_window": int(p.y.sum()),
                          "share_works_with_any_edition": round(float((p.groupby("work").y.sum() > 0).mean()), 4)}
    name = "primary.json" if variant == "primary" else f"secondary_{variant}.json"
    json.dump(o, open(T / name, "w"), indent=1)
    if variant in ("primary", "binary"):
        ev.round(4).to_csv(T / ("event_study.csv" if variant == "primary" else "event_study_binary.csv"), index=False)
    print(json.dumps(o, indent=1))


if __name__ == "__main__":
    main()
