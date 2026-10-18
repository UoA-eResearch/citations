"""Thresholds, indices, trends, decomposition and validation (plan sections 1-3, 5). Reads data/daily.csv,
data/county_reporting.csv, data/raw/coverage_history.csv and the PUDL EIA-861 reliability table.
Writes results/tables/primary.json, results/tables/state_year.csv and results/tables/decomposition.csv."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
YEARS = list(range(2020, 2026))
B, SEED = 2000, 20261018


def threshold(x):
    """IEEE 1366 2.5 beta threshold from daily SAIDI values (zero days excluded from the log statistics)."""
    v = np.log(x[x > 0])
    return float(np.exp(v.mean() + 2.5 * v.std(ddof=1))) if len(v) > 1 else np.inf


def indices(d):
    """Per state and year (2020-2025): all-events, and MED-excluded under rolling, frozen, 10-year and quantile rules."""
    rows = []
    for st, g in d.groupby("st"):
        s = g.set_index("date").saidi
        yr = g.set_index("date").year
        base = s[(yr >= 2015) & (yr <= 2019)]
        t_frozen = threshold(base.values)
        q99 = float(np.quantile(base.values, 0.99))
        for Y in YEARS:
            cur = s[yr == Y].values
            t_roll = threshold(s[(yr >= Y - 5) & (yr <= Y - 1)].values)
            t_10 = threshold(s[(yr >= Y - 10) & (yr <= Y - 1)].values) if Y - 10 >= 2015 else np.nan
            r = dict(st=st, year=Y, all=cur.sum(), t_roll=t_roll, t_frozen=t_frozen, t_q99=q99,
                     noMED_roll=cur[cur <= t_roll].sum(), noMED_frozen=cur[cur <= t_frozen].sum(), noMED_q99=cur[cur <= q99].sum(),
                     n_MED_roll=int((cur > t_roll).sum()), n_MED_frozen=int((cur > t_frozen).sum()))
            r["noMED_10y"] = cur[cur <= t_10].sum() if np.isfinite(t_10) else np.nan
            rows.append(r)
    return pd.DataFrame(rows)


def trend(df, col):
    """Pooled log-linear trend (% per year) with state fixed effects: ln(index + 1) on year, within states."""
    y = np.log(df[col].values + 1.0)
    x = df.year.values.astype(float)
    g = df.st.values
    ym = pd.Series(y).groupby(g).transform("mean").values; xm = pd.Series(x).groupby(g).transform("mean").values
    b = ((x - xm) @ (y - ym)) / ((x - xm) @ (x - xm))
    return 100 * (np.exp(b) - 1)


def boot(df, f, rng):
    sts = df.st.unique(); grp = {s: x for s, x in df.groupby("st")}
    vals = []
    for _ in range(B):
        pick = rng.choice(sts, len(sts))
        x = pd.concat([grp[s].assign(st=f"{s}_{k}") for k, s in enumerate(pick)])
        vals.append(f(x))
    return [float(np.nanpercentile(vals, 2.5)), float(np.nanpercentile(vals, 97.5))]


def decompose(d, st):
    """Shapley split of the 2020->2025 change in all-events SAIDI: non-MED growth, reclassification, MED growth."""
    g = d[d.st == st]; s = g.set_index("date").saidi; yr = g.set_index("date").year
    a20, a25 = s[yr == 2020].values, s[yr == 2025].values
    t20 = threshold(s[(yr >= 2015) & (yr <= 2019)].values); t25 = threshold(s[(yr >= 2020) & (yr <= 2024)].values)
    N = lambda a, t: a[a <= t].sum()
    year1 = N(a25, t20) - N(a20, t20); thr1 = N(a25, t25) - N(a25, t20)       # year first, then threshold
    thr2 = N(a20, t25) - N(a20, t20); year2 = N(a25, t25) - N(a20, t25)       # threshold first, then year
    tot = a25.sum() - a20.sum()
    non = (year1 + year2) / 2; rec = (thr1 + thr2) / 2
    return dict(st=st, total=tot, nonMED_growth=non, reclassification=rec, MED_growth=tot - non - rec, t2020=t20, t2025=t25)


def main(cov_sensitivity=False):
    d = pd.read_csv(RUN / "data" / "daily.csv")
    d["year"] = d.date.str[:4].astype(int)
    cov = pd.read_csv(RUN / "data" / "raw" / "coverage_history.csv")
    cov["year"] = 2000 + cov.year.str.split("/").str[-1].astype(int)
    ok_cov = cov.groupby("state").max_pct_covered.min()
    ok_cov = set(ok_cov[ok_cov >= 0.80].index)
    cr = pd.read_csv(RUN / "data" / "county_reporting.csv")
    med = cr[cr.year.between(2018, 2022)].groupby("st").n_counties.median()
    cr["dev"] = (cr.n_counties / cr.st.map(med) - 1).abs()
    stable = cr.groupby("st").agg(maxdev=("dev", "max"), years=("year", "nunique"))
    stable = set(stable[(stable.maxdev <= 0.15) & (stable.years == 11)].index)
    incl = sorted(ok_cov & stable & set(d.st))
    out = dict(states_coverage_ok=sorted(ok_cov & set(d.st)), states_stable=sorted(stable), included=incl, n_included=len(incl))
    d = d[d.st.isin(incl)].copy()
    if cov_sensitivity:   # normalise by covered customers (coverage history; nearest year outside 2018-2022)
        cc = cov.set_index(["state", "year"]).max_covered
        yrs = d.year.clip(2018, 2022)
        d["saidi"] = d.cmi / [cc.get((s, y), np.nan) for s, y in zip(d.st, yrs)]
    idx = indices(d)
    rng = np.random.default_rng(SEED)
    res = {}
    for col in ("all", "noMED_roll", "noMED_frozen", "noMED_q99"):
        res[col] = dict(trend_pct=trend(idx, col), ci=boot(idx, lambda x, c=col: trend(x, c), rng))
    out["trends"] = res
    ratio = lambda x: trend(x, "noMED_roll") / trend(x, "all")
    r_ci = boot(idx, ratio, rng)
    h1 = dict(ratio=ratio(idx), ci=r_ci)
    if res["all"]["ci"][0] <= 0 <= res["all"]["ci"][1]:
        h1["verdict"] = "Inconclusive (no all-events trend to mask)"
    else:
        h1["verdict"] = "Supported" if r_ci[1] < 0.5 else "Refuted" if r_ci[0] >= 0.5 else "Inconclusive"
    out["H1"] = h1
    diff = lambda x: trend(x, "noMED_roll") - trend(x, "noMED_frozen")
    d_ci = boot(idx, diff, rng)
    out["H2"] = dict(diff_pct_points=diff(idx), ci=d_ci,
                     verdict="Supported" if d_ci[1] < 0 else "Refuted" if d_ci[0] > 0 else "Inconclusive")
    out["MED_counts"] = idx.groupby("year")[["n_MED_roll", "n_MED_frozen"]].mean().round(2).to_dict()
    out["threshold_drift"] = idx.groupby("year")[["t_roll"]].median().round(3).to_dict()
    out["noMED_10y_2025_vs_roll"] = dict(ten=float(idx[idx.year == 2025].noMED_10y.sum()), roll=float(idx[idx.year == 2025].noMED_roll.sum()))
    dec = pd.DataFrame([decompose(d, s) for s in incl])
    out["decomposition_median"] = dec[["total", "nonMED_growth", "reclassification", "MED_growth"]].median().to_dict()
    out["decomposition_sum"] = dec[["total", "nonMED_growth", "reclassification", "MED_growth"]].sum().to_dict()
    # validation against EIA-861 (IEEE-method utilities, customer-weighted SAIDI with MEDs, by state-year)
    e = pd.read_parquet(RUN / "data" / "raw" / "core_eia861__yearly_reliability.parquet")
    e["year"] = pd.to_datetime(e.report_date).dt.year
    e = e[(e.standard == "ieee_standard") & e.customers.gt(0) & e.saidi_w_major_event_days_minutes.notna()]
    ew = e.groupby(["state", "year"]).apply(lambda x: np.average(x.saidi_w_major_event_days_minutes, weights=x.customers), include_groups=False)
    ea = d.groupby(["st", "year"]).saidi.sum()
    j = pd.concat([ea.rename("eaglei"), ew.rename("eia")], axis=1, join="inner").reset_index()
    j = j[j.year.between(2018, 2024)]
    rho = stats.spearmanr(j.eaglei, j.eia).statistic
    out["validation"] = dict(n_state_years=int(len(j)), spearman=float(rho), validated=bool(rho >= 0.6))
    suffix = "_coverage_sensitivity" if cov_sensitivity else ""
    idx.to_csv(T / f"state_year{suffix}.csv", index=False)
    dec.to_csv(T / f"decomposition{suffix}.csv", index=False)
    json.dump(out, open(T / f"primary{suffix}.json", "w"), indent=1, default=float)
    print(json.dumps({k: out[k] for k in ("n_included", "trends", "H1", "H2", "validation")}, indent=1, default=float))


if __name__ == "__main__":
    main(cov_sensitivity=len(sys.argv) > 1 and sys.argv[1] == "coverage")
