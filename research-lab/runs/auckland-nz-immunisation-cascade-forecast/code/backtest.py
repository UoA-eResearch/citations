"""Rolling-origin backtest (plan section 4) and frozen prospective forecasts (plan section 5).
Reads data/coverage.parquet. Writes results/tables/{backtest_cells.csv, backtest_summary.csv, h1.json,
secondary_*.csv} and results/forecasts_frozen.csv."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
PRIMARY_GROUPS = ["Total", "Maori", "Pacific"]
SECONDARY_GROUPS = ["Asian", "European or Other"]
ORIGIN_FIRST, ORIGIN_LAST = (2012, 2), (2025, 2)
FREEZE_ORIGIN = (2026, 2)
EXCLUDE_TARGETS = [((2020, 3), (2022, 2)), ((2023, 3), (2024, 2))]  # schedule changes; AIR migration
RNG = np.random.default_rng(20261007)


def qi(year, quarter):
    return year * 4 + quarter - 1


def qlabel(i):
    return f"{i // 4}Q{i % 4 + 1}"


def load():
    d = pd.read_parquet(RUN / "data" / "coverage.parquet")
    d["qi"] = [qi(t.year, (t.month - 1) // 3 + 1) for t in pd.to_datetime(d.quarter_end)]
    # Otago + Southland -> Southern where Southern is absent (earliest files); missing if either part is suppressed
    os_ = d[d.district.isin(["Otago", "Southland"])]
    if len(os_):
        s = os_.groupby(["qi", "milestone", "group"]).agg(
            eligible=("eligible", lambda x: x.sum() if len(x) == 2 and x.notna().all() else np.nan),
            immunised=("immunised", lambda x: x.sum() if len(x) == 2 and x.notna().all() else np.nan)).reset_index()
        s["district"] = "Southern"
        have = set(map(tuple, d[d.district == "Southern"][["qi", "milestone", "group"]].values))
        s = s[[(a, b, c) not in have for a, b, c in s[["qi", "milestone", "group"]].values]]
        d = pd.concat([d[~d.district.isin(["Otago", "Southland"])], s], ignore_index=True)
    d = d[(d.eligible > 0) & d.immunised.notna()]
    return {(r.district, r.group, int(r.milestone), int(r.qi)): (float(r.eligible), float(r.immunised)) for r in d.itertuples()}


def cov(P, d, g, m, t):
    v = P.get((d, g, m, t))
    if v is None:
        return None
    n, k = v
    p = min(max(k / n, 0.5 / n), 1 - 0.5 / n)
    return p, n


def logit(p):
    return np.log(p / (1 - p))


def expit(x):
    return 1 / (1 + np.exp(-x))


def m1(P, d, g, q, h):
    m, L = (12, 4) if h >= 3 else (18, 2)
    inp = cov(P, d, g, m, q + h - L)
    if inp is None:
        return None
    deltas = []
    for t in range(q, q - 40, -1):
        a, b = cov(P, d, g, 24, t), cov(P, d, g, m, t - L)
        if a is not None and b is not None:
            deltas.append(logit(a[0]) - logit(b[0]))
        if len(deltas) == 4:
            break
    if len(deltas) < 2:
        return None
    return dict(p=float(expit(logit(inp[0]) + np.mean(deltas))), n_in=inp[1])


def b1(P, d, g, q, h):
    c = cov(P, d, g, 24, q)
    return None if c is None else dict(p=c[0])


def b2(P, d, g, q, h):
    xs, ys = [], []
    for t in range(q, q - 40, -1):
        c = cov(P, d, g, 24, t)
        if c is not None:
            xs.append(t); ys.append(c[0])
        if len(xs) == 8:
            break
    if len(xs) < 5:
        return None
    b, a = np.polyfit(xs, ys, 1)
    return dict(p=float(np.clip(a + b * (q + h), 0, 1)))


def m2_fit(P, cells, q):
    """OLS on logit C24[t] ~ dg intercepts + logit C12[t-4] + logit C6[t-6], targets t in [q-19, q]."""
    rows = []
    for d, g in cells:
        for t in range(q - 19, q + 1):
            a, b, c = cov(P, d, g, 24, t), cov(P, d, g, 12, t - 4), cov(P, d, g, 6, t - 6)
            if a and b and c:
                rows.append((d, g, logit(a[0]), logit(b[0]), logit(c[0])))
    if len(rows) < 30:
        return None
    df = pd.DataFrame(rows, columns=["d", "g", "y", "x12", "x6"])
    keys = sorted(set(zip(df.d, df.g)))
    idx = {k: i for i, k in enumerate(keys)}
    X = np.zeros((len(df), len(keys) + 2))
    X[np.arange(len(df)), [idx[k] for k in zip(df.d, df.g)]] = 1
    X[:, -2], X[:, -1] = df.x12, df.x6
    coef, *_ = np.linalg.lstsq(X, df.y.values, rcond=None)
    return idx, coef


def m2(P, fit, d, g, q):
    if fit is None or (d, g) not in fit[0]:
        return None
    b, c = cov(P, d, g, 12, q), cov(P, d, g, 6, q - 2)
    if not (b and c):
        return None
    idx, coef = fit
    return dict(p=float(expit(coef[idx[(d, g)]] + coef[-2] * logit(b[0]) + coef[-1] * logit(c[0]))))


def dm_test(diff_by_origin, h):
    x = np.asarray(diff_by_origin, float)
    T = len(x)
    xm = x - x.mean()
    lag = h - 1
    gam = [np.sum(xm[k:] * xm[:T - k]) / T for k in range(lag + 1)]
    var = (gam[0] + 2 * sum((1 - k / (lag + 1)) * gam[k] for k in range(1, lag + 1))) / T
    stat = x.mean() / np.sqrt(var)
    return float(stat), float(1 - stats.norm.cdf(stat))


def reduction_ci(cells, base, B=5000, block=4):
    origins = sorted(cells.origin.unique())
    by = {o: cells[cells.origin == o] for o in origins}
    T = len(origins)
    out = np.empty(B)
    for b in range(B):
        starts = RNG.integers(0, T - block + 1, int(np.ceil(T / block)))
        pick = [origins[s + k] for s in starts for k in range(block)][:T]
        sub = pd.concat([by[o] for o in pick])
        out[b] = 1 - sub.ae_M1.mean() / sub[f"ae_{base}"].mean()
    return np.percentile(out, [2.5, 97.5])


def run_backtest(P, districts, groups, horizons):
    rows = []
    q0, q1 = qi(*ORIGIN_FIRST), qi(*ORIGIN_LAST)
    errs = {}  # (group, h) -> list of (target_qi, z)
    for q in range(q0, q1 + 1):
        fit2 = m2_fit(P, [(d, g) for d in districts for g in groups], q)
        for h in horizons:
            for g in groups:
                past = [z for (tq, z) in errs.get((g, h), []) if tq <= q]
                zq = np.percentile(past, [10, 90]) if len(set(tq for tq, _ in errs.get((g, h), []) if tq <= q)) >= 8 else None
                recent = [z for (tq, z) in errs.get((g, h), []) if q - 8 < tq <= q]  # D1 secondary: last 8 target quarters
                zr = np.percentile(recent, [10, 90]) if len(set(tq for tq, _ in errs.get((g, h), []) if q - 8 < tq <= q)) >= 6 else None
                for d in districts:
                    act = cov(P, d, g, 24, q + h)
                    f1 = m1(P, d, g, q, h)
                    if act is None:
                        continue
                    row = dict(origin=q, target=q + h, h=h, district=d, group=g, actual=act[0], n_target=act[1])
                    for name, f in (("M1", f1), ("B1", b1(P, d, g, q, h)), ("B2", b2(P, d, g, q, h)),
                                    ("M2", m2(P, fit2, d, g, q) if h == 4 else None)):
                        row[name] = None if f is None else f["p"]
                    if f1 is not None:
                        s = np.sqrt(f1["n_in"] * f1["p"] * (1 - f1["p"]))
                        z = (logit(act[0]) - logit(f1["p"])) * s
                        errs.setdefault((g, h), []).append((q + h, z))
                        if zq is not None:
                            row["lo80"] = float(expit(logit(f1["p"]) + zq[0] / s)); row["hi80"] = float(expit(logit(f1["p"]) + zq[1] / s))
                        if zr is not None:
                            row["lo80r"] = float(expit(logit(f1["p"]) + zr[0] / s)); row["hi80r"] = float(expit(logit(f1["p"]) + zr[1] / s))
                    rows.append(row)
    df = pd.DataFrame(rows)
    for m in ("M1", "B1", "B2", "M2"):
        df[f"ae_{m}"] = (df[m].astype(float) - df.actual).abs() * 100
    return df, errs


def summarise(df, h, label, extra=None):
    c = df[(df.h == h) & df.M1.notna() & df.B1.notna() & df.B2.notna()]
    if extra is not None:
        c = c[extra(c)]
    out = dict(label=label, h=h, n_cells=len(c), n_origins=c.origin.nunique(), MAE_M1=c.ae_M1.mean(), MAE_B1=c.ae_B1.mean(), MAE_B2=c.ae_B2.mean())
    for b in ("B1", "B2"):
        out[f"reduction_vs_{b}"] = 1 - c.ae_M1.mean() / c[f"ae_{b}"].mean()
        d = c.groupby("origin").apply(lambda x: (x[f"ae_{b}"] - x.ae_M1).mean())
        out[f"DM_stat_{b}"], out[f"DM_p_{b}"] = dm_test(d.values, h)
    if "lo80" in c:
        w = c.dropna(subset=["lo80"])
        out["PI80_coverage"] = float(((w.actual >= w.lo80) & (w.actual <= w.hi80)).mean()) if len(w) else np.nan
    if "lo80r" in c:
        w = c.dropna(subset=["lo80r"])
        out["PI80_recent_coverage_posthoc"] = float(((w.actual >= w.lo80r) & (w.actual <= w.hi80r)).mean()) if len(w) else np.nan
    return out, c


def main():
    P = load()
    districts = sorted({k[0] for k in P if k[0] != "National total"})
    assert len(districts) == 20, districts
    df, errs = run_backtest(P, districts + ["National total"], PRIMARY_GROUPS + SECONDARY_GROUPS, [1, 2, 3, 4])
    df["target_label"] = df.target.map(qlabel)
    df.to_csv(TAB / "backtest_cells.csv", index=False)
    prim = df[(df.district != "National total") & df.group.isin(PRIMARY_GROUPS)]
    # H1
    s, c = summarise(prim, 4, "H1 primary: 20 districts x Total/Maori/Pacific, h=4")
    lo1, hi1 = reduction_ci(c, "B1")
    lo2, hi2 = reduction_ci(c, "B2")
    s.update(reduction_vs_B1_CI=[lo1, hi1], reduction_vs_B2_CI=[lo2, hi2])
    if s["reduction_vs_B1"] >= 0.30 and s["reduction_vs_B2"] >= 0.30 and s["DM_p_B1"] < 0.05 and s["DM_p_B2"] < 0.05:
        verdict = "Supported"
    elif hi1 < 0.30 or hi2 < 0.30:
        verdict = "Refuted"
    else:
        verdict = "Inconclusive"
    s["verdict"] = verdict
    json.dump(s, open(TAB / "h1.json", "w"), indent=1, default=float)
    print(json.dumps(s, indent=1, default=float))
    # secondary
    sec = []
    for h in (1, 2, 3, 4):
        sec.append(summarise(prim, h, f"primary cells, h={h}")[0])
    for g in PRIMARY_GROUPS + SECONDARY_GROUPS:
        sec.append(summarise(df[(df.district != "National total") & (df.group == g)], 4, f"group {g}, h=4")[0])
    sec.append(summarise(df[df.district == "National total"], 4, "national, all groups, h=4")[0])
    excl = lambda c: ~np.any([(c.target >= qi(*a)) & (c.target <= qi(*b)) for a, b in EXCLUDE_TARGETS], axis=0)  # noqa: E731
    sec.append(summarise(prim, 4, "h=4 excluding schedule-change and AIR-migration targets", excl)[0])
    for a, b, lab in [((2013, 1), (2016, 4), "targets 2013-2016"), ((2017, 1), (2019, 4), "targets 2017-2019"),
                      ((2020, 1), (2022, 4), "targets 2020-2022"), ((2023, 1), (2026, 2), "targets 2023-2026")]:
        sec.append(summarise(prim, 4, f"h=4, {lab}", lambda c, a=a, b=b: (c.target >= qi(*a)) & (c.target <= qi(*b)))[0])
    m2c = prim[(prim.h == 4) & prim.M1.notna() & prim.M2.notna()]
    sec.append(dict(label="M2 vs M1, h=4 (common cells)", h=4, n_cells=len(m2c), MAE_M1=m2c.ae_M1.mean(), MAE_M2=m2c.ae_M2.mean()))
    pd.DataFrame(sec).to_csv(TAB / "backtest_summary.csv", index=False)
    print(pd.DataFrame(sec)[["label", "n_cells", "MAE_M1", "MAE_B1", "MAE_B2", "reduction_vs_B1", "reduction_vs_B2", "DM_p_B1", "DM_p_B2", "PI80_coverage"]].round(3).to_string())
    by_d = prim[(prim.h == 4) & prim.M1.notna() & prim.B1.notna() & prim.B2.notna()].groupby(["district", "group"])[["ae_M1", "ae_B1", "ae_B2"]].mean()
    by_d.to_csv(TAB / "secondary_by_district.csv")
    # frozen prospective forecasts (plan section 5): origin 2026Q2, h = 1..4
    q = qi(*FREEZE_ORIGIN)
    fr = []
    for g in PRIMARY_GROUPS + SECONDARY_GROUPS:
        for h in (1, 2, 3, 4):
            past = [z for (tq, z) in errs.get((g, h), []) if tq <= q]
            zq = np.percentile(past, [10, 90])
            rq = [(tq, z) for (tq, z) in errs.get((g, h), []) if q - 8 < tq <= q]
            zr = np.percentile([z for _, z in rq], [10, 90]) if len({tq for tq, _ in rq}) >= 6 else (np.nan, np.nan)  # D2: D1's own minimum
            for d in districts + ["National total"]:
                f = m1(P, d, g, q, h)
                if f is None:
                    continue
                s_ = np.sqrt(f["n_in"] * f["p"] * (1 - f["p"]))
                fr.append(dict(origin=qlabel(q), target=qlabel(q + h), h=h, district=d, group=g, forecast=f["p"],
                               lo80=float(expit(logit(f["p"]) + zq[0] / s_)), hi80=float(expit(logit(f["p"]) + zq[1] / s_)),
                               lo80_recent=float(expit(logit(f["p"]) + zr[0] / s_)), hi80_recent=float(expit(logit(f["p"]) + zr[1] / s_)),
                               last_published_C24=(cov(P, d, g, 24, q) or (np.nan,))[0]))
    out = RUN / "results" / "forecasts_frozen.csv"
    if out.exists():  # D2: never overwrite the frozen, hashed file; a re-run writes alongside it
        out = RUN / "results" / "forecasts_rerun.csv"
    pd.DataFrame(fr).to_csv(out, index=False, float_format="%.5f")
    print(pd.DataFrame(fr)[lambda x: (x.group == "Total") & (x.district == "National total")].round(4).to_string())


if __name__ == "__main__":
    main()
