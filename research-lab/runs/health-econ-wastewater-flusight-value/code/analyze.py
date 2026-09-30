#!/usr/bin/env python
"""Hypotheses H3-H4 and the descriptive analyses (plan.md sec 2, 5, 7) on the primary forecasts (main, lag 10).

- H3: slope of the log state-season WIS ratio (with / without wastewater) on wastewater coverage, over all state-seasons
  with wastewater features; two-way bootstrap (states x 4-week date blocks).
- H4: equal-weight quantile average of FluSight-ensemble with the with-wastewater model vs with the base model.
- Descriptive: relative WIS by horizon, season and epidemic phase; S5 (holiday weeks excluded); 50%/95% coverage;
  both models and the averages against FluSight-baseline and FluSight-ensemble.
Output: results/tables/{h3,h4,by_group,comparators,coverage_intervals}.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline import QLEVELS, RAW  # noqa: E402
from score import FC, QCOLS, TAB, attach_scores, paired, panels, rel_wis, truth, verdict  # noqa: E402


def load_hub(model: str) -> pd.DataFrame:
    rows = []
    for f in sorted((RAW / "hub" / model).glob("*.csv")):
        d = pd.read_csv(f, dtype={"location": str, "output_type_id": str})
        d = d[(d.target == "wk inc flu hosp") & (d.output_type == "quantile") & (d.location != "US") & d.horizon.isin([0, 1, 2, 3])]
        d["q"] = d.output_type_id.astype(float).round(3)
        rows.append(d)
    d = pd.concat(rows, ignore_index=True)
    d["location"] = d.location.str.zfill(2)
    w = d.pivot_table(index=["reference_date", "location", "horizon"], columns="q", values="value", aggfunc="first")
    w = w.reindex(columns=np.round(QLEVELS, 3))
    w.columns = QCOLS
    w = w.dropna().reset_index()
    w["reference_date"] = pd.to_datetime(w.reference_date)
    w[QCOLS] = np.sort(w[QCOLS].values, axis=1)
    w["model"] = model
    return w


def average(a: pd.DataFrame, b: pd.DataFrame, name: str) -> pd.DataFrame:
    k = ["reference_date", "location", "horizon"]
    m = a[k + QCOLS].merge(b[k + QCOLS], on=k, suffixes=("_a", "_b"))
    out = m[k].copy()
    for c in QCOLS:
        out[c] = (m[c + "_a"] + m[c + "_b"]) / 2
    out["model"] = name
    return out


def h3(sc: pd.DataFrame, nboot=5000, seed=1):
    """State-season log WIS ratio vs coverage over state-seasons with wastewater features in >= half of their tasks."""
    a, b = sc[sc.model == "ww"], sc[sc.model == "base"]
    m = paired(a, b).merge(sc[sc.model == "ww"][["reference_date", "location", "horizon", "coverage", "has_ww"]],
                           on=["reference_date", "location", "horizon"])
    keep = m.groupby(["location", "season"]).has_ww.transform("mean") >= 0.5
    m = m[keep]
    g = m.groupby(["location", "season", "reference_date"])[["wis_a", "wis_b"]].sum()
    cov = m.groupby(["location", "season"]).coverage.first()
    A = g.wis_a.unstack().fillna(0)
    B = g.wis_b.unstack().reindex(index=A.index, columns=A.columns).fillna(0)
    ss = A.index                                                    # (location, season)
    x = cov.reindex(ss).values
    slope = float(np.polyfit(x, np.log(A.sum(1) / B.sum(1)).values, 1)[0])
    dates = pd.DatetimeIndex(A.columns)
    dseason = np.array([f"{r.year}-{str(r.year + 1)[2:]}" if r.month >= 8 else f"{r.year - 1}-{str(r.year)[2:]}" for r in dates])
    blocks = [[np.where(dseason == s)[0][i:i + 4] for i in range(0, int((dseason == s).sum()), 4)] for s in np.unique(dseason)]
    locs = ss.get_level_values(0).unique()
    lidx = pd.Index(locs).get_indexer(ss.get_level_values(0))
    Av, Bv = A.values, B.values
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(nboot):
        wr = np.zeros(len(dates))
        for bl in blocks:
            for j in rng.integers(0, len(bl), len(bl)):
                wr[bl[j]] += 1
        wl = np.bincount(rng.integers(0, len(locs), len(locs)), minlength=len(locs))[lidx].astype(float)
        a, b = Av @ wr, Bv @ wr
        ok = (wl > 0) & (a > 0) & (b > 0)
        if ok.sum() < 5:
            continue
        bs.append(np.polyfit(x[ok], np.log(a[ok] / b[ok]), 1, w=np.sqrt(wl[ok]))[0])
    lo, hi = float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
    v = "supported" if hi < 0 else ("contradicted" if lo > 0 else "inconclusive")
    return dict(slope_per_unit_coverage=slope, lo=lo, hi=hi, n_state_seasons=len(ss), verdict=v)


def main():
    tr = truth()
    pan = panels()
    sc = attach_scores(pd.read_parquet(FC / "main_lag10.parquet"), tr).merge(pan, on=["season", "location"], how="left")
    prim = sc[sc.coverage >= 0.5]
    ww, base = prim[prim.model == "ww"], prim[prim.model == "base"]

    # H3
    r3 = h3(sc)
    pd.DataFrame([r3]).to_csv(TAB / "h3.csv", index=False)
    print("H3", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r3.items()})

    # comparators and H4
    ens, bl = load_hub("FluSight-ensemble"), load_hub("FluSight-baseline")
    fc = pd.read_parquet(FC / "main_lag10.parquet")
    ours = {m: fc[fc.model == m][["reference_date", "location", "horizon"] + QCOLS].assign(model=m) for m in ("ww", "base")}
    avg_ww, avg_base = average(ens, ours["ww"], "ens+ww"), average(ens, ours["base"], "ens+base")
    models = {"ww": ours["ww"], "base": ours["base"], "FluSight-ensemble": ens, "FluSight-baseline": bl,
              "ens+ww": avg_ww, "ens+base": avg_base}
    scored = {k: attach_scores(v, tr).merge(pan, on=["season", "location"], how="left") for k, v in models.items()}
    rows = []
    for panel, sel in (("primary", lambda d: d.coverage >= 0.5), ("secondary", lambda d: d.coverage >= 0.2),
                       ("all locations", lambda d: d.coverage >= 0)):
        for a, b in (("ens+ww", "ens+base"), ("ww", "FluSight-baseline"), ("base", "FluSight-baseline"),
                     ("ww", "FluSight-ensemble"), ("base", "FluSight-ensemble"), ("ens+ww", "FluSight-ensemble"),
                     ("ens+base", "FluSight-ensemble"),
                     ("FluSight-ensemble", "FluSight-baseline")):
            m = paired(scored[a][sel(scored[a])], scored[b][sel(scored[b])])
            r = rel_wis(m, nboot=2000)
            r.update(panel=panel, model=a, reference=b, verdict=verdict(r) if (a, b) == ("ens+ww", "ens+base") else "")
            rows.append(r)
    comp = pd.DataFrame(rows)
    comp.to_csv(TAB / "comparators.csv", index=False)
    comp[(comp.model == "ens+ww") & (comp.reference == "ens+base")].to_csv(TAB / "h4.csv", index=False)
    print(comp[["panel", "model", "reference", "rel_wis", "lo", "hi", "n_tasks", "verdict"]].round(3).to_string(index=False))

    # descriptive by group (primary panel)
    m = paired(ww, base).merge(ww[["reference_date", "location", "horizon", "y"]], on=["reference_date", "location", "horizon"])
    prev = tr.rename("y_prev").reset_index()
    prev["target_end_date"] = prev.target_end_date + pd.Timedelta(weeks=1)
    m["target_end_date"] = m.reference_date + pd.to_timedelta(7 * m.horizon, unit="D")
    m = m.merge(prev, on=["location", "target_end_date"], how="left")
    m["phase"] = np.where(m.y > m.y_prev, "rising", "falling or flat")
    md = m.reference_date.dt.strftime("%m-%d")
    m["holiday"] = (md >= "12-20") | (md <= "01-10")
    rows = []
    groups = [("horizon", h) for h in range(4)] + [("season", s) for s in sorted(m.season.unique())] + \
             [("phase", p) for p in ("rising", "falling or flat")] + [("S5: excluding holiday weeks", "yes")]
    for gname, gval in groups:
        mm = m[~m.holiday] if gname.startswith("S5") else m[m[gname] == gval]
        r = rel_wis(mm, nboot=2000)
        r.update(group=gname, value=str(gval))
        rows.append(r)
    byg = pd.DataFrame(rows)
    byg.to_csv(TAB / "by_group.csv", index=False)
    print(byg[["group", "value", "rel_wis", "lo", "hi", "geo", "n_tasks"]].round(3).to_string(index=False))

    # interval coverage and absolute scores
    rows = []
    for k in ("ww", "base", "FluSight-ensemble", "FluSight-baseline"):
        d = scored[k]
        d = d[d.coverage >= 0.5]
        rows.append(dict(model=k, n=len(d), mean_wis=d.wis.mean(), mae=d.ae.mean(), cov50=d.cov50.mean(), cov95=d.cov95.mean()))
    ci = pd.DataFrame(rows)
    ci.to_csv(TAB / "coverage_intervals.csv", index=False)
    print(ci.round(3).to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
