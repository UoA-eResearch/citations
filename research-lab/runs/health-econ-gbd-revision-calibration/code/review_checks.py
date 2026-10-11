"""Analyses requested by the independent review (review/review.md; deviations.md D3). Exploratory: none changes a
preregistered verdict. Writes results/tables/review_checks.csv and results/tables/none_class_audit.csv.

R1  The `none` class: which of its 85 countries have vital registration in GBD's own garbage-code table or post-2010
    national data in the WHO Mortality Database; the H4 gap under three alternative groupings.
R2  Death-weighted C2 (weights = GBD 2021 deaths), overall and by group, the high - low gap; excluding China and India.
R3  H4 gap with the country-only bootstrap; the upper bound across seeds 1-10 and at B = 20,000.
R4  Distribution-free check: do the two releases' 95% UIs overlap? (>= 90% if both are calibrated, whatever the error
    shape or dependence.)
R5  C2 by GBD 2021 death count; C2 excluding cells with < 1 death; agreement of the two years within country-cause pairs.
S7  E1 at error correlations 0.5 and 0.8.
S9  Share of C2 misses from the ten lowest-C2 causes, Other neoplasms and COVID-19.
S10 Median stated log-SD and median absolute log-revision by group; SD of z and share |z| > 5 by group.
M13 Rows outside their own interval in each raw file (exact comparison and relative excess > 1e-6)."""
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

import analysis as A
import build
import quality

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
SEED = A.SEED


def wmatrices(p, ycol, ecol, wcol, countries, causes):
    ci = {c: i for i, c in enumerate(countries)}
    ki = {k: i for i, k in enumerate(causes)}
    Y = np.zeros((len(countries), len(causes)))
    E = np.zeros_like(Y)
    q = p[p[ecol] & p.location_id.isin(ci) & p.cause_id.isin(ki)]
    w = q[wcol].astype(float).values if wcol else np.ones(len(q))
    np.add.at(Y, (q.location_id.map(ci).values, q.cause_id.map(ki).values), w * q[ycol].astype(float).values)
    np.add.at(E, (q.location_id.map(ci).values, q.cause_id.map(ki).values), w)
    return Y, E


def boot(p, ycol, ecol, groups, wcol=None, b=A.B, seed=SEED, two_way=True):
    """Like analysis.boot_share, with optional cell weights. Returns {group: (estimate, draws)}."""
    causes = np.array(sorted(p.cause_id.unique()))
    mats = {g: wmatrices(p, ycol, ecol, wcol, cs, causes) for g, cs in groups.items()}
    rng = np.random.default_rng(seed)
    draws = {g: np.empty(b) for g in groups}
    for i in range(b):
        bk = rng.multinomial(len(causes), np.full(len(causes), 1 / len(causes))) if two_way else np.ones(len(causes))
        for g, (Y, E) in mats.items():
            a = rng.multinomial(Y.shape[0], np.full(Y.shape[0], 1 / Y.shape[0]))
            den = a @ E @ bk
            draws[g][i] = (a @ Y @ bk) / den if den > 0 else np.nan
    return {g: (float(Y.sum() / E.sum()), draws[g]) for g, (Y, E) in mats.items()}


def gap(r, hi="high", lo="low"):
    d = r[hi][1] - r[lo][1]
    l, u = A.ci(d)
    return r[hi][0] - r[lo][0], l, u


def rec(rows, analysis, group, est, lo=np.nan, hi=np.nan, n=np.nan):
    rows.append(dict(analysis=analysis, group=group, estimate=est, lower95=lo, upper95=hi, n=n))


def who_mdb_years():
    x = pd.read_excel(RUN / "data" / "raw" / "who" / "list_ctry_years_feb2026.xls", sheet_name="avail_mortality", header=None)
    hdr = x.index[x.iloc[:, 0].astype(str).str.strip() == "Country"][0]
    x = x.iloc[hdr + 1:, :7]
    x.columns = ["code", "name", "admin1", "subdiv", "year", "list", "icd"]
    x = x[x.admin1.isna() & x.subdiv.isna() & x.year.notna()]
    x["year"] = x.year.astype(int)
    return x


def main():
    p = A.metrics(pd.read_parquet(RUN / "data" / "panel.parquet"))
    q = pd.read_parquet(RUN / "data" / "quality.parquet")
    rows = []
    g = A.groups_of(q)

    # R1: audit of the `none` class
    gb, _ = quality.garbage_table()
    names = set(q.location_name)
    gb["location_name"] = [quality.match(n, names) for n in gb.gbd_app_name]
    in_gbd_vr = set(gb.location_name.dropna())
    mdb = who_mdb_years()
    mdb["location_name"] = [quality.match(n, names) for n in mdb.name]
    alias_extra = {"Virgin Islands (USA)": "United States Virgin Islands", "Saint Kitts and Nevis": "Saint Kitts and Nevis"}
    mdb.loc[mdb.location_name.isna(), "location_name"] = mdb.loc[mdb.location_name.isna(), "name"].map(alias_extra)
    mdb10 = mdb[mdb.year >= 2010].groupby("location_name").year.nunique()
    none = q[q.who_quality == "none"].copy()
    none["in_gbd_vr_table"] = none.location_name.isin(in_gbd_vr)
    none["who_mdb_years_since_2010"] = none.location_name.map(mdb10).fillna(0).astype(int)
    by_c = pd.read_csv(TAB / "by_country.csv")[["location_id", "C2"]]
    none = none.merge(by_c, on="location_id", how="left")
    none["gbd_vr_since_2010"] = none.garbage_pct_2010_21.notna()
    none[["location_name", "in_gbd_vr_table", "gbd_vr_since_2010", "garbage_pct_2010_21", "who_mdb_years_since_2010", "C2"]].sort_values(
        ["in_gbd_vr_table", "who_mdb_years_since_2010"], ascending=False).to_csv(TAB / "none_class_audit.csv", index=False)
    none["gbd_vr_since_2010"] = none.garbage_pct_2010_21.notna()
    rec(rows, "R1 `none` countries in GBD's VR garbage-code table (any year 1980-2021)", "none", int(none.in_gbd_vr_table.sum()), n=len(none))
    rec(rows, "R1 `none` countries with GBD VR data in 2010-2021", "none", int(none.gbd_vr_since_2010.sum()), n=len(none))
    rec(rows, "R1 `none` countries with WHO MDB national data in >= 1 year since 2010", "none", int((none.who_mdb_years_since_2010 > 0).sum()), n=len(none))
    novr = set(none[~none.gbd_vr_since_2010].location_id)
    vr_none = none[none.gbd_vr_since_2010]
    good = set(vr_none[vr_none.garbage_pct_2010_21 < 20].location_id)
    lowwho = set(q[q.who_quality.isin(["low", "very low"])].location_id)
    high = set(g["high"])
    alts = {
        "ALT1 low = WHO low/very low + `none` without GBD VR data 2010-21": (high, lowwho | novr),
        "ALT2 as ALT1, and `none` with GBD VR and garbage < 20% moved to high": (high | good, lowwho | novr),
        "ALT3 low = `none` without GBD VR data 2010-21 only": (high, novr),
    }
    for name, (h, l) in alts.items():
        r = boot(p, "cov2", "elig2", {"high": np.array(sorted(h)), "low": np.array(sorted(l))})
        e, lo, hi = gap(r)
        rec(rows, f"R1 H4 gap (C2 high - low), {name}", f"high {len(h)} / low {len(l)}", e, lo, hi)

    # R2: death-weighted C2
    r = boot(p, "cov2", "elig2", {"all": np.array(sorted(p.location_id.unique()))} | g, wcol="p21")
    for k, (e, d) in r.items():
        lo, hi = A.ci(d)
        rec(rows, "R2 death-weighted C2", k, e, lo, hi)
    e, lo, hi = gap(r)
    rec(rows, "R2 death-weighted C2 gap, high - low", "high - low", e, lo, hi)
    ci_ids = set(q[q.location_name.isin(["China", "India"])].location_id)
    r2 = boot(p, "cov2", "elig2", {"low": np.array(sorted(set(g["low"]) - ci_ids)), "high": g["high"]}, wcol="p21")
    rec(rows, "R2 death-weighted C2, low group excluding China and India", "low", r2["low"][0], *A.ci(r2["low"][1]))
    rec(rows, "R2 death-weighted C2 gap, high - low, excluding China and India (confirmation pass)", "high - low", *gap(r2))
    w_ci = p[p.elig2 & p.location_id.isin(ci_ids)].p21.sum() / p[p.elig2 & p.location_id.isin(g["low"])].p21.sum()
    rec(rows, "R2 share of the low group's GBD 2021 deaths (eligible cells) in China and India", "low", float(w_ci))
    x = p[p.elig2 & p.location_id.isin(g["low"])].copy()
    x["wmiss"] = x.p21 * (~x.cov2)
    share = x[x.location_id.isin(ci_ids)].wmiss.sum() / x.wmiss.sum()
    top10 = x.groupby(["location_id", "cause_id"]).wmiss.sum().nlargest(10)
    rec(rows, "R2 share of the low group's death-weighted C2 misses from China and India", "low", float(share))
    rec(rows, "R2 share of the low group's death-weighted misses from its 10 largest country-cause pairs", "low",
        float(top10.sum() / x.wmiss.sum()), n=int(sum(1 for (c, _) in top10.index if c in ci_ids)))
    pc = p[p.elig2].groupby("location_id").apply(lambda z: np.average(z.cov2, weights=z.p21) if z.p21.sum() > 0 else np.nan,
                                                  include_groups=False)
    for k in ("high", "low"):
        rec(rows, "R2 median per-country death-weighted C2", k, float(pc.reindex(g[k]).median()))

    # R3: H4 interval sensitivity
    r = boot(p, "cov2", "elig2", g, two_way=False)
    rec(rows, "R3 H4 gap, country-only bootstrap", "high - low", *gap(r))
    ups = []
    for s in range(1, 11):
        ups.append(gap(boot(p, "cov2", "elig2", g, seed=s))[2])
    rec(rows, "R3 H4 upper bound across seeds 1-10: min", "high - low", float(min(ups)))
    rec(rows, "R3 H4 upper bound across seeds 1-10: max", "high - low", float(max(ups)))
    rec(rows, "R3 H4 seeds (of 10) with upper bound < 0.05 (would be Refuted)", "high - low", float(sum(u < 0.05 for u in ups)))
    rec(rows, "R3 H4 gap, B = 20,000", "high - low", *gap(boot(p, "cov2", "elig2", g, b=20000, seed=SEED)))

    # R4: distribution-free overlap
    p["overlap"] = (np.maximum(p.L21, p.L23) <= np.minimum(p.U21, p.U23))
    r = boot(p, "overlap", "elig2", {"all": np.array(sorted(p.location_id.unique()))} | g)
    for k, (e, d) in r.items():
        rec(rows, "R4 UIs overlap (>= 90% if both calibrated)", k, e, *A.ci(d))
    rec(rows, "R4 UIs overlap gap, high - low", "high - low", *gap(r))
    e = p[p.elig2]
    for rho in (0.0, 0.5, 0.8):
        s21 = (np.log(e.U21) - np.log(e.L21)) / (2 * A.Z)
        s23 = (np.log(e.U23) - np.log(e.L23)) / (2 * A.Z)
        sd = np.sqrt(s21 ** 2 + s23 ** 2 - 2 * rho * s21 * s23)
        c2 = (2 * norm.cdf(A.Z * np.sqrt(s21 ** 2 + s23 ** 2) / sd) - 1).mean()
        ov = (2 * norm.cdf(A.Z * (s21 + s23) / sd) - 1).mean()
        e1 = (norm.cdf((np.log(e.U21) - np.log(e.p21)) / sd) - norm.cdf((np.log(e.L21) - np.log(e.p21)) / sd)).mean()
        rec(rows, f"S7/R4 expected if calibrated, error correlation {rho}: C1 (E1)", "all", float(e1))
        rec(rows, f"S7/R4 expected if calibrated, error correlation {rho}: C2", "all", float(c2))
        rec(rows, f"S7/R4 expected if calibrated, error correlation {rho}: overlap", "all", float(ov))

    # R5: size strata and year agreement
    bins = [-np.inf, 1, 10, 100, 1000, 10000, np.inf]
    lab = ["< 1", "1-10", "10-100", "100-1,000", "1,000-10,000", ">= 10,000"]
    e = p[p.elig2].copy()
    e["size"] = pd.cut(e.p21, bins, right=False, labels=lab)
    for k, z in e.groupby("size", observed=True):
        rec(rows, "R5 C2 by GBD 2021 deaths in the cell", k, float(z.cov2.mean()), n=len(z))
    r = boot(p[p.p21 >= 1], "cov2", "elig2", {"all": np.array(sorted(p.location_id.unique()))})
    rec(rows, "R5 C2 excluding cells with < 1 GBD 2021 death", "all", r["all"][0], *A.ci(r["all"][1]), n=int((p.elig2 & (p.p21 >= 1)).sum()))
    w = e.pivot_table(index=["location_id", "cause_id"], columns="year", values="cov2", aggfunc="first").dropna()
    rec(rows, "R5 country-cause pairs eligible in both years", "all", len(w))
    rec(rows, "R5 share of those pairs with the same C2 outcome in both years", "all", float((w[2019] == w[2021]).mean()))

    # S9: concentration of misses
    m = p[p.elig2 & ~p.cov2]
    k = pd.read_csv(TAB / "by_cause.csv").nsmallest(10, "C2")
    rec(rows, "S9 share of C2 misses from the 10 lowest-C2 causes", "all", float(m.cause_id.isin(k.cause_id).mean()), n=len(m))
    for c in ("Other neoplasms", "COVID-19", "Other intestinal infectious diseases"):
        rec(rows, f"S9 share of C2 misses from {c}", "all", float((m.cause_name == c).mean()))
        z = p[p.elig2 & (p.cause_name == c)]
        rec(rows, f"S9 {c}: median log-revision (ln p23 - ln p21)", "all", float(np.median(np.log(z.p23) - np.log(z.p21))), n=len(z))
        rec(rows, f"S9 {c}: share of cells revised upward", "all", float((z.p23 > z.p21).mean()))

    # S10: mechanism
    for kk, cs in ({"all": None} | g).items():
        z = p[p.elig2] if cs is None else p[p.elig2 & p.location_id.isin(cs)]
        s21 = (np.log(z.U21) - np.log(z.L21)) / (2 * A.Z)
        rec(rows, "S10 median stated log-SD s21", kk, float(np.median(s21)))
        rec(rows, "S10 median |ln p23 - ln p21|", kk, float(np.median(np.abs(np.log(z.p23) - np.log(z.p21)))))
        rec(rows, "S10 SD of z", kk, float(np.std(z.z)))
        rec(rows, "S10 share |z| > 5", kk, float((np.abs(z.z) > 5).mean()))
        for y in (2019, 2021):
            rec(rows, f"S10 SD of z, year {y} (confirmation pass)", kk, float(np.std(z[z.year == y].z)))

    # M13: own-interval violations in the raw files
    for key in ("d21", "d23_2019", "d23_2021"):
        d = build.read(key)
        out = (d.val < d.lower) | (d.val > d.upper)
        rel = np.maximum((d.lower - d.val) / d.val.abs().clip(lower=1e-12), (d.val - d.upper) / d.val.abs().clip(lower=1e-12))
        rec(rows, f"M13 rows outside their own interval, {build.FILES[key]}", "exact", int(out.sum()), n=len(d))
        rec(rows, f"M13 rows outside their own interval, {build.FILES[key]}", "relative excess > 1e-6", int((out & (rel > 1e-6)).sum()), n=len(d))

    out = pd.DataFrame(rows)
    out.to_csv(TAB / "review_checks.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.to_string())


if __name__ == "__main__":
    main()
