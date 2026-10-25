"""Secondary analyses 1, 2, 6 and 7 (plan section 3) -> results/tables/secondary.json. Reported, not confirmatory.

1. RR by cohort: the primary PPML (with D1's separation rule) on one treated cohort plus all controls at a time.
2. Sun-Abraham OLS on log(1 + editions): the same saturated cohort x event dummies, work and year fixed effects.
6. Project Gutenberg: linked works matched to the Gutenberg catalogue (normalised title equal, author surname present);
   share released within 0-2 years of expiry (renewed) against never-renewed works over the same calendar years.
7. HathiTrust: registrations matched to Hathifiles records (normalised title prefix + author surname, imprint year
   within reg_year +/- 1); share of matched volumes with rights code pd/pdus, by renewal status and cohort.
"""
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import did  # noqa: E402

RUN = did.RUN
RAW = RUN / "data" / "raw"
T = did.T


def norm(s):
    s = re.sub(r"[^a-z0-9 ]", " ", str(s).lower())
    s = re.sub(r"^(the|a|an) ", "", re.sub(r"\s+", " ", s).strip())
    return s


def surname(a):
    a = str(a)
    a = a.split(",")[0] if "," in a else (a.split()[-1] if a.split() else "")
    return norm(a).split(" ")[0] if norm(a) else ""


def by_cohort(p):
    out = {}
    for g in sorted(p.cohort[p.cohort > 0].unique()):
        q = p[(p.cohort == 0) | (p.cohort == g)]
        try:
            o, _ = did.fit(q)
            out[int(g)] = {"rr": o["rr"], "rr_ci": o["rr_ci"], "treated_works": o["treated_works"],
                           "separated": o["separated_cells_dropped"]}
        except Exception as ex:                               # a cohort with no identified post cells
            out[int(g)] = {"error": str(ex)[:120]}
    return out


def sa_ols(p):
    import pyfixest as pf
    q = p.copy()
    q["ly"] = np.log1p(q.y)
    q["ev"] = np.where(q.cohort > 0, (q.year - q.cohort).clip(did.EMIN, did.EMAX), -999)
    cols = []
    for g in sorted(q.cohort[q.cohort > 0].unique()):
        for e in range(did.EMIN, did.EMAX + 1):
            m = (q.cohort == g) & (q.ev == e)
            if e != -1 and m.any():
                c = f"d_{g}_{e + 10}"
                q[c] = m.astype(float)
                cols.append((c, g, e))
    m = pf.feols("ly ~ " + " + ".join(c for c, _, _ in cols) + " | work + year", data=q, vcov={"CRV1": "work"})
    b = m.coef()
    V = pd.DataFrame(np.asarray(m._vcov), index=b.index, columns=b.index)
    size = q[q.cohort > 0].groupby("cohort").work.nunique()
    w = pd.Series(0.0, index=b.index)
    for c, g, e in cols:
        if e in (0, 1, 2) and c in w.index:
            w[c] = size[g]
    w /= w.sum()
    est, se = float(w @ b), float(np.sqrt(w @ V @ w))
    base = float(q.loc[(q.cohort > 0) & (q.year < q.cohort), "ly"].mean())        # D2: treated pre-period mean
    return {"coef_event0_2_log1p": round(est, 5), "se": round(se, 5),
            "ci": [round(est - 1.96 * se, 5), round(est + 1.96 * se, 5)], "works": int(q.work.nunique()),
            "treated_pre_mean_log1p": round(base, 5), "relative_to_pre_mean": round(est / base, 3),
            "relative_ci": [round((est - 1.96 * se) / base, 3), round((est + 1.96 * se) / base, 3)]}


def gutenberg(p):
    r = pd.read_parquet(did.DATA / "registrations.parquet")
    links = pd.read_parquet(did.DATA / "links.parquet").merge(r[["entry_id", "reg_year", "renewed", "title", "author"]], on="entry_id")
    links = links[links.reg_year.between(1923, 1930)]
    pg = pd.read_csv(RAW / "pg_catalog.csv", usecols=["Text#", "Type", "Issued", "Title", "Language", "Authors"])
    pg = pg[pg.Type == "Text"]
    pg["t"] = pg.Title.map(lambda s: norm(str(s).split("\n")[0]))
    pg["yr"] = pd.to_datetime(pg.Issued, errors="coerce").dt.year
    idx = pg.groupby("t")
    rows = []
    for x in links.itertuples():
        t = norm(x.title)
        sn = surname(x.author)
        hit = None
        if t in idx.groups and sn:
            c = pg.loc[idx.groups[t]]
            c = c[c.Authors.fillna("").map(norm).str.contains(rf"\b{re.escape(sn)}\b")]
            if len(c):
                hit = int(c.yr.min())
        rows.append({"work": x.work, "reg_year": x.reg_year, "renewed": x.renewed, "pg_year": hit})
    d = pd.DataFrame(rows)
    out = {"linked_works": int(len(d)), "on_gutenberg": int(d.pg_year.notna().sum())}
    ren = d[d.renewed & d.reg_year.between(1923, 1929)].copy()
    ren["exp"] = ren.reg_year + 96
    ren_share = float(((ren.pg_year >= ren.exp) & (ren.pg_year <= ren.exp + 2)).mean())
    nr = d[~d.renewed]
    # never-renewed works over the same calendar windows (expiry-year mix of the renewed works)
    wins = ren.exp.value_counts(normalize=True)
    nr_share = float(sum(wt * ((nr.pg_year >= y) & (nr.pg_year <= y + 2)).mean() for y, wt in wins.items()))
    out.update({"renewed_released_0_2y_after_expiry": round(ren_share, 4), "renewed_n": int(len(ren)),
                "never_renewed_same_windows": round(nr_share, 4), "never_renewed_n": int(len(nr)),
                "by_expiry_year": {int(y): {"n": int(len(g)), "share": round(float(((g.pg_year >= y) & (g.pg_year <= y + 2)).mean()), 4)}
                                   for y, g in ren.groupby("exp")}})
    # D2: overall shares and the within-group timing profile of renewed releases (years since expiry)
    out["ever_on_gutenberg"] = {"renewed_1923_1929": round(float(ren.pg_year.notna().mean()), 4),
                                "never_renewed": round(float(nr.pg_year.notna().mean()), 4)}
    dt = (ren.pg_year - ren.exp).dropna().astype(int)
    out["renewed_release_years_since_expiry"] = {int(k): int(v) for k, v in dt.value_counts().sort_index().items()}
    out["renewed_released_before_expiry"] = int((dt < 0).sum())
    # releases per 1,000 renewed works at each lag, among works whose lag year is observable (catalogue of 2026-10)
    out["renewed_release_rate_per_1000_by_lag"] = {
        k: {"at_risk": int((ren.exp + k <= 2026).sum()),
            "rate": round(1000 * float((ren.pg_year == ren.exp + k).sum()) / max(1, int((ren.exp + k <= 2026).sum())), 2)}
        for k in range(0, 8)}
    nr_rate = float(sum(wt * (nr.pg_year == y).mean() for y, wt in wins.items()))
    out["never_renewed_release_rate_per_1000_per_year"] = round(1000 * nr_rate, 2)
    return out


def hathi():
    r = pd.read_parquet(did.DATA / "registrations.parquet")
    r = r[r.reg_year.between(1923, 1930)].copy()
    r["k"] = r.title.map(lambda s: " ".join(norm(s).split()[:4]))
    r["sn"] = r.author.map(surname)
    keys = set(r.k)
    rows = []
    with gzip.open(RAW / "hathi_full_20261001.txt.gz", "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) < 26:
                continue
            try:
                y = int(f[16])
            except ValueError:
                continue
            if not 1922 <= y <= 1931:
                continue
            k = " ".join(norm(f[11]).split()[:4])
            if k in keys:
                rows.append((k, y, f[2], norm(f[25])))
    h = pd.DataFrame(rows, columns=["k", "year", "rights", "h_author"])
    m = r.merge(h, on="k")
    m = m[(m.year - m.reg_year).abs() <= 1]
    m = m[[bool(sn) and sn in a for sn, a in zip(m.sn, m.h_author)]]
    m["pd"] = m.rights.isin(["pd", "pdus"])
    per = m.groupby(["entry_id", "renewed", "reg_year"]).pd.mean().reset_index()
    out = {"registrations_matched": int(per.entry_id.nunique()), "volumes": int(len(m)),
           "pd_share_renewed": round(float(per[per.renewed].pd.mean()), 4), "pd_share_never_renewed": round(float(per[~per.renewed].pd.mean()), 4),
           "renewed_by_reg_year": {int(y): {"n": int(len(g)), "pd_share": round(float(g.pd.mean()), 4)} for y, g in per[per.renewed].groupby("reg_year")}}
    return out


def main():
    p = did.panel()
    out = {"rr_by_cohort": by_cohort(p), "sun_abraham_ols": sa_ols(p), "gutenberg": gutenberg(p), "hathitrust": hathi()}
    (T / "secondary.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
