"""Panel and staggered DiD (plan section 2) and secondaries 1-5 (section 3).

Panel: linked works x calendar years 2008-2025; outcome = Open Library editions with that publish year.
Treated cohorts: renewed works registered 1923-1929 (expiry 2019-2025). Controls: never-renewed works of 1923-1930 and
renewed 1930 works (expiry 2026, outside the window). PPML with work and year fixed effects and saturated cohort x
event-time dummies (Sun-Abraham), event time binned to [-8, +6], reference -1; SEs clustered by work.
Primary: RR = exp(cohort-size-weighted mean of the event 0..2 coefficients) with a delta-method interval; pre-trend =
joint Wald test of the event -5..-2 coefficients (cohort-weighted per event time).

  did.py [primary|nopod|lag|placebo|ols]   (primary also writes event_study.csv)
Writes results/tables/primary.json (or secondary_<variant>.json).
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


def panel(variant="primary"):
    r = pd.read_parquet(DATA / "registrations.parquet")
    links = pd.read_parquet(DATA / "links.parquet").merge(r[["entry_id", "reg_year", "renewed"]], on="entry_id")
    links = links[links.reg_year.between(1923, 1930)]
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
    separated = [(c, g, e) for c, g, e in cols if q.loc[q[c] == 1, "y"].sum() == 0]
    for c, _, _ in separated:
        q = q[q[c] == 0].drop(columns=c)
    cols = [x for x in cols if x not in separated]
    q = q[q.groupby("work").y.transform("sum") > 0]
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
    out = {"separated_cells_dropped": [f"{g}:{e}" for _, g, e in separated], "works_in_model": int(q.work.nunique()), "treated_works": int(q[q.cohort > 0].work.nunique()),
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


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "primary"
    if variant == "ols":
        import pyfixest as pf
        p = panel()
        p["ly"] = np.log1p(p.y)
        q = p.copy()
        q["post02"] = ((q.cohort > 0) & (q.year - q.cohort).between(0, 2)).astype(float)
        q["post_other"] = ((q.cohort > 0) & ((q.year - q.cohort) > 2)).astype(float)
        m = pf.feols("ly ~ post02 + post_other | work + year", data=q, vcov={"CRV1": "work"})
        out = {"coef_post02_log1p": round(float(m.coef()["post02"]), 4), "se": round(float(m.se()["post02"]), 4)}
        json.dump(out, open(T / "secondary_ols.json", "w"), indent=1)
        print(out)
        return
    p = panel("primary" if variant in ("primary", "placebo") else variant)
    o, ev = fit(p, shift=3 if variant == "placebo" else 0)
    o["verdict_rule"] = verdict(o) if variant == "primary" else None
    o["variant"] = variant
    o["panel_summary"] = {"works": int(p.work.nunique()), "editions_in_window": int(p.y.sum()),
                          "share_works_with_any_edition": round(float((p.groupby("work").y.sum() > 0).mean()), 4)}
    name = "primary.json" if variant == "primary" else f"secondary_{variant}.json"
    json.dump(o, open(T / name, "w"), indent=1)
    if variant == "primary":
        ev.round(4).to_csv(T / "event_study.csv", index=False)
    print(json.dumps(o, indent=1))


if __name__ == "__main__":
    main()
