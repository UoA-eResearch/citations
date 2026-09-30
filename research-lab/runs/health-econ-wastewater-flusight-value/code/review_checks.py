#!/usr/bin/env python
"""Checks requested by the independent review (deviations.md D4), on the primary forecasts (main, lag 10):
share of primary tasks without wastewater features; paired win share by horizon; mean WIS difference by season;
location-only and time-only bootstrap intervals beside the two-way one; state-season bootstrap of the lead-lag peak.
Output: results/tables/review_checks.csv, results/tables/leadlag_bootstrap.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline as P  # noqa: E402
from score import FC, TAB, attach_scores, paired, panels, truth  # noqa: E402


def one_way(m, which, nboot=5000, seed=0):
    g = m.groupby(["location", "reference_date"])[["wis_a", "wis_b"]].sum()
    A, B = g.wis_a.unstack().fillna(0).values, g.wis_b.unstack().fillna(0).values
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(nboot):
        if which == "location":
            i = rng.integers(0, A.shape[0], A.shape[0])
            bs.append(A[i].sum() / B[i].sum())
        else:
            dates = pd.DatetimeIndex(g.wis_a.unstack().columns)
            season = np.array([P.season_of(d) for d in dates])
            wr = np.zeros(len(dates))
            for s in np.unique(season):
                idx = np.where(season == s)[0]
                bl = [idx[k:k + 4] for k in range(0, len(idx), 4)]
                for j in rng.integers(0, len(bl), len(bl)):
                    wr[bl[j]] += 1
            bs.append((A @ wr).sum() / (B @ wr).sum())
    return np.percentile(bs, [2.5, 97.5])


def main():
    tr, pan = truth(), panels()
    sc = attach_scores(pd.read_parquet(FC / "main_lag10.parquet"), tr).merge(pan, on=["season", "location"], how="left")
    prim = sc[sc.coverage >= 0.5]
    ww, base = prim[prim.model == "ww"], prim[prim.model == "base"]
    rows = [dict(check="primary tasks without wastewater features (base forecast used)", value=f"{(~ww.has_ww).sum()} of {len(ww)} ({(~ww.has_ww).mean():.1%})")]
    nof = ww[~ww.has_ww].assign(abbr=lambda d: d.location.map(P.locations().abbreviation))
    rows.append(dict(check="  by state-season", value="; ".join(f"{a} {s}: {n}" for (a, s), n in nof.groupby(["abbr", "season"]).size().items())))
    m = paired(ww, base)
    rows.append(dict(check="paired tasks where the wastewater model has lower WIS", value=f"{(m.wis_a < m.wis_b).mean():.1%} (ties {(m.wis_a == m.wis_b).mean():.1%})"))
    for h in range(4):
        mh = m[m.horizon == h]
        rows.append(dict(check=f"  horizon {h}", value=f"{(mh.wis_a < mh.wis_b).mean():.1%}"))
    for s, ms in m.groupby("season"):
        rows.append(dict(check=f"mean WIS difference (with - without), {s}", value=f"{(ms.wis_a - ms.wis_b).mean():+.2f} (mean WIS without {ms.wis_b.mean():.1f})"))
    for which in ("location", "time"):
        lo, hi = one_way(m, which)
        rows.append(dict(check=f"relative WIS, {which}-only bootstrap", value=f"{m.wis_a.sum() / m.wis_b.sum():.3f} [{lo:.3f}, {hi:.3f}]"))
    share = m.groupby("location").wis_b.sum() / m.wis_b.sum()
    rows.append(dict(check="largest location share of base-model WIS", value=f"{P.locations().abbreviation[share.idxmax()]} {share.max():.1%}"))
    out = pd.DataFrame(rows)
    out.to_csv(TAB / "review_checks.csv", index=False)
    print(out.to_string(index=False))

    # lead-lag bootstrap over state-seasons
    h = P.load_hosp()
    loc = P.locations()
    Y = P.yweek(h[h.as_of == h.as_of.max()], loc.population)
    samples, meta = P.ww_series()
    S = P.state_signal(P.ww_windows(samples, -3), meta, pd.Timestamp("2026-09-30"))
    S = S.loc[:, S.columns.isin(Y.columns)]
    units = []
    for _, r in pan[pan.coverage >= 0.5].iterrows():
        if r.location not in S.index:
            continue
        y0 = int(r.season[:4])
        wk = [c for c in S.columns if pd.Timestamp(f"{y0}-10-01") <= c <= pd.Timestamp(f"{y0 + 1}-05-31")]
        s = S.loc[r.location, wk].values
        per = {}
        for lead in range(-3, 5):
            yy = Y.loc[r.location].reindex([c + pd.Timedelta(weeks=lead) for c in wk]).values
            ds, dy = np.diff(s), np.diff(yy)
            ok = np.isfinite(ds) & np.isfinite(dy)
            per[lead] = (ds[ok], dy[ok])
        units.append(per)
    rng = np.random.default_rng(5)
    peaks, d02, d01 = [], [], []
    for _ in range(2000):
        pick = rng.integers(0, len(units), len(units))
        cor = {}
        for lead in range(-3, 5):
            x = np.concatenate([units[i][lead][0] for i in pick])
            y = np.concatenate([units[i][lead][1] for i in pick])
            cor[lead] = np.corrcoef(x, y)[0, 1]
        peaks.append(max(cor, key=cor.get))
        d02.append(cor[0] - cor[2])
        d01.append(cor[0] - cor[1])
    pk = pd.Series(peaks).value_counts(normalize=True).sort_index()
    lb = pd.DataFrame(dict(quantity=[f"peak at lead {k}" for k in pk.index] + ["corr(0) - corr(2)", "corr(0) - corr(1)"],
                           value=[f"{v:.1%}" for v in pk.values] +
                                 [f"{np.mean(d02):.3f} [{np.percentile(d02, 2.5):.3f}, {np.percentile(d02, 97.5):.3f}]",
                                  f"{np.mean(d01):.3f} [{np.percentile(d01, 2.5):.3f}, {np.percentile(d01, 97.5):.3f}]"]))
    lb.to_csv(TAB / "leadlag_bootstrap.csv", index=False)
    print(lb.to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
