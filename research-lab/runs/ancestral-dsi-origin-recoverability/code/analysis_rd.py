"""Limb 1 (plan section 2): the jump in country-field shares at the June 2023 INSDC rule.

Daily shares of usable / placeholder / malformed / absent among non-human BioSamples, by submission date. A
local-linear regression in time on daily shares, weighted by samples x a triangular kernel over the bandwidth, with
separate slopes either side of the cutoff and a donut of one month either side excluded. The jump is the coefficient
on the post indicator.

Intervals: cluster bootstrap over submitting organisations (Owner name), 1,000 resamples, seed 20261022, done on an
owner x day count matrix so each resample is a weighted sum.

Writes results/tables/rd_primary.json and rd_secondary.json.
"""
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
SEED, B = 20261022, 1000
CUT = pd.Timestamp("2023-06-01")
CLASSES = ["usable", "placeholder", "malformed", "absent"]
# INSDC missing-value terms for which a country is legitimately inapplicable (plan section 5 denominator variant)
INAPPLICABLE = ("missing: lab stock", "missing: synthetic construct", "missing: control sample",
                "missing: sample group", "not applicable")


def load():
    cols = ["submission_date", "owner", "country_class", "country_raw", "package"]
    parts = [pd.read_parquet(f, columns=cols) for f in sorted(glob.glob(str(RUN / "data" / "samples" / "*.parquet")))]
    d = pd.concat(parts, ignore_index=True)
    d["date"] = pd.to_datetime(d.submission_date, errors="coerce")
    d = d.dropna(subset=["date"])
    raw = d.country_raw.fillna("").str.strip().str.lower()
    d["inapplicable"] = raw.isin(INAPPLICABLE)
    return d


def counts(d, cls_col="country_class"):
    """owner x day sparse matrices of n and of each class count."""
    owners, oi = np.unique(d.owner.fillna("").to_numpy(), return_inverse=True)
    days = pd.Index(np.sort(d.date.unique()))
    di = days.get_indexer(d.date)
    shape = (len(owners), len(days))
    n = sparse.csr_matrix((np.ones(len(d)), (oi, di)), shape=shape)
    cm = {c: sparse.csr_matrix(((d[cls_col] == c).to_numpy().astype(float), (oi, di)), shape=shape) for c in CLASSES}
    return days, n, cm


def jump(days, n_day, k_day, cut, bw_days, donut_days):
    t = (days - cut).days.to_numpy().astype(float)
    keep = (np.abs(t) <= bw_days) & (np.abs(t) > donut_days) & (n_day > 0)
    if keep.sum() < 10:
        return np.nan
    tt, y, w = t[keep], k_day[keep] / n_day[keep], n_day[keep] * (1 - np.abs(t[keep]) / bw_days)
    post = (tt >= 0).astype(float)
    X = np.column_stack([np.ones_like(tt), post, tt, post * tt])
    sw = np.sqrt(w)
    beta, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    return float(beta[1])


def estimate(d, cut=CUT, bw_months=24, donut_months=1, boot=True, classes=CLASSES):
    lo, hi = cut - pd.DateOffset(months=bw_months), cut + pd.DateOffset(months=bw_months)
    w = d[(d.date >= lo) & (d.date < hi)]
    days, n, cm = counts(w)
    bw, dn = (hi - cut).days, (cut + pd.DateOffset(months=donut_months) - cut).days if donut_months else 0
    n_day = np.asarray(n.sum(axis=0)).ravel()
    out = {"n_samples": int(len(w)), "n_owners": int(n.shape[0]), "window": [str(lo.date()), str(hi.date())]}
    rng = np.random.default_rng(SEED)
    draws = None
    if boot:
        weights = rng.multinomial(n.shape[0], np.full(n.shape[0], 1 / n.shape[0]), size=B).astype(float)
        bn = weights @ n            # B x days (dense)
        bn = np.asarray(bn)
    for c in classes:
        k_day = np.asarray(cm[c].sum(axis=0)).ravel()
        est = jump(days, n_day, k_day, cut, bw, dn)
        pre = w[(w.date < cut - pd.DateOffset(months=donut_months))]
        post = w[(w.date >= cut + pd.DateOffset(months=donut_months))]
        r = {"jump_pp": round(100 * est, 3), "share_pre": round(float((pre.country_class == c).mean()), 4),
             "share_post": round(float((post.country_class == c).mean()), 4)}
        if boot:
            bk = np.asarray(weights @ cm[c])
            js = np.array([jump(days, bn[b], bk[b], cut, bw, dn) for b in range(B)])
            r["ci_pp"] = [round(100 * float(np.nanpercentile(js, 2.5)), 3), round(100 * float(np.nanpercentile(js, 97.5)), 3)]
        out[c] = r
    return out


def verdict(r):
    lo, hi = r["usable"]["ci_pp"]
    return "Supported" if hi < 10 else "Refuted" if lo >= 10 else "Inconclusive"


def main():
    d = load()
    prim = estimate(d)
    prim["H1"] = verdict(prim)
    json.dump(prim, open(TAB / "rd_primary.json", "w"), indent=1)
    print(json.dumps(prim, indent=1))
    sec = {}
    sec["second_cutoff_2025_01_01"] = estimate(d, cut=pd.Timestamp("2025-01-01"))
    sec["placebo_2021_06_01"] = estimate(d, cut=pd.Timestamp("2021-06-01"))
    sec["placebo_2022_06_01"] = estimate(d, cut=pd.Timestamp("2022-06-01"))
    sec["bandwidth_12m"] = estimate(d, bw_months=12)
    sec["bandwidth_36m"] = estimate(d, bw_months=36)
    sec["no_donut"] = estimate(d, donut_months=0)
    sec["inapplicable_terms_removed"] = estimate(d[~d.inapplicable])
    # package fixed effects: package-day shares, weighted regression with package dummies
    lo, hi = CUT - pd.DateOffset(months=24), CUT + pd.DateOffset(months=24)
    w = d[(d.date >= lo) & (d.date < hi)]
    w = w[(w.date < CUT - pd.DateOffset(months=1)) | (w.date >= CUT + pd.DateOffset(months=1))]
    g = w.groupby(["package", "date"]).agg(n=("country_class", "size"),
                                            k=("country_class", lambda s: (s == "usable").sum())).reset_index()
    t = (g.date - CUT).dt.days.to_numpy().astype(float)
    bw = (hi - CUT).days
    post = (t >= 0).astype(float)
    P = pd.get_dummies(g.package, dtype=float).to_numpy()
    X = np.column_stack([post, t, post * t, P])
    wt = np.sqrt(g.n.to_numpy() * (1 - np.abs(t) / bw))
    beta, *_ = np.linalg.lstsq(X * wt[:, None], (g.k / g.n).to_numpy() * wt, rcond=None)
    sec["package_fixed_effects"] = {"usable_jump_pp": round(100 * float(beta[0]), 3), "packages": int(P.shape[1])}
    # yearly shares
    d["year"] = d.date.dt.year
    sec["shares_by_year"] = d.groupby("year").country_class.value_counts(normalize=True).unstack().round(4).to_dict(orient="index")
    json.dump(sec, open(TAB / "rd_secondary.json", "w"), indent=1, default=str)
    print("secondary written")


if __name__ == "__main__":
    main()
