#!/usr/bin/env python
"""Scoring (plan.md sec 5): WIS against the final vintage, relative WIS with a two-way bootstrap (locations x 4-week
blocks of reference dates within season), panels from wastewater coverage.

Usage: score.py VARIANT [LAG]   -> results/tables/relwis_{variant}_lag{L}.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline import QLEVELS, RAW, load_hosp, locations, season_of  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB, FC = RUN / "results" / "tables", RUN / "results" / "forecasts"
QCOLS = [f"q{x:g}" for x in QLEVELS]
NBOOT = 5000


def truth():
    h = load_hosp()
    f = h[h.as_of == h.as_of.max()]
    return f.set_index(["location", "target_end_date"]).observation


def wis(Q: np.ndarray, y: np.ndarray) -> np.ndarray:
    """FluSight WIS for 23 quantiles: (1 / (K + 1/2)) * (|y - median| / 2 + sum_k alpha_k / 2 * IS_alpha_k), K = 11."""
    K = 11
    med = Q[:, 11]
    tot = 0.5 * np.abs(y - med)
    for k in range(K):
        lo, hi = Q[:, k], Q[:, 22 - k]
        alpha = 2 * QLEVELS[k]
        IS = (hi - lo) + (2 / alpha) * np.maximum(0, lo - y) + (2 / alpha) * np.maximum(0, y - hi)
        tot = tot + alpha / 2 * IS
    return tot / (K + 0.5)


def attach_scores(fc: pd.DataFrame, tr: pd.Series) -> pd.DataFrame:
    fc = fc.copy()
    fc["target_end_date"] = fc.reference_date + pd.to_timedelta(7 * fc.horizon, unit="D")
    fc["y"] = tr.reindex(pd.MultiIndex.from_arrays([fc.location, fc.target_end_date])).values
    fc = fc[np.isfinite(fc.y)]
    Q = fc[QCOLS].values
    fc["wis"] = wis(Q, fc.y.values)
    fc["cov50"] = (fc.y >= fc["q0.25"]) & (fc.y <= fc["q0.75"])
    fc["cov95"] = (fc.y >= fc["q0.025"]) & (fc.y <= fc["q0.975"])
    fc["ae"] = np.abs(fc.y - fc["q0.5"])
    fc["season"] = fc.reference_date.map(season_of)
    return fc


def panels():
    cov = pd.read_csv(TAB / "ww_coverage.csv")
    loc = locations()
    a2l = dict(zip(loc.abbreviation, loc.index))
    cov["location"] = cov.abbr.map(a2l)
    return cov[["season", "location", "coverage"]]


def paired(a: pd.DataFrame, b: pd.DataFrame, keys=("reference_date", "location", "horizon")) -> pd.DataFrame:
    m = a[list(keys) + ["season", "wis"]].merge(b[list(keys) + ["wis"]], on=list(keys), suffixes=("_a", "_b"))
    return m


def rel_wis(m: pd.DataFrame, nboot=NBOOT, seed=0, block=4):
    """Ratio of mean WIS (a / b) with a two-way bootstrap: locations, and 4-week blocks of reference dates within each
    season, resampled independently. Also the geometric mean over locations of location-level ratios."""
    g = m.groupby(["location", "reference_date"])[["wis_a", "wis_b"]].sum()
    L = g.index.get_level_values(0).unique()
    R = np.sort(g.index.get_level_values(1).unique())
    A = g.wis_a.unstack().reindex(index=L, columns=R).fillna(0).values
    B = g.wis_b.unstack().reindex(index=L, columns=R).fillna(0).values
    est = A.sum() / B.sum()
    ls = m.groupby("location")[["wis_a", "wis_b"]].sum()
    ls = ls[(ls.wis_a > 0) & (ls.wis_b > 0)]
    geo = float(np.exp(np.log(ls.wis_a / ls.wis_b).mean()))
    seasons = pd.Series(R).map(lambda r: season_of(pd.Timestamp(r))).values
    blocks = []
    for s in np.unique(seasons):
        idx = np.where(seasons == s)[0]
        blocks.append([idx[i:i + block] for i in range(0, len(idx), block)])
    rng = np.random.default_rng(seed)
    bs, bg = [], []
    for _ in range(nboot):
        wl = np.bincount(rng.integers(0, len(L), len(L)), minlength=len(L)).astype(float)
        wr = np.zeros(len(R))
        for bl in blocks:
            for j in rng.integers(0, len(bl), len(bl)):
                wr[bl[j]] += 1
        a, b = wl @ A @ wr, wl @ B @ wr
        bs.append(a / b)
        la, lb = A @ wr, B @ wr
        ok = (wl > 0) & (la > 0) & (lb > 0)
        bg.append(np.exp(np.average(np.log(la[ok] / lb[ok]), weights=wl[ok])))
    return dict(rel_wis=est, lo=float(np.percentile(bs, 2.5)), hi=float(np.percentile(bs, 97.5)), geo=geo,
                geo_lo=float(np.percentile(bg, 2.5)), geo_hi=float(np.percentile(bg, 97.5)),
                n_tasks=len(m), n_locations=len(L), n_rounds=len(R))


def verdict(r):
    if r["rel_wis"] <= 0.95 and r["hi"] < 1:
        return "supported"
    if r["lo"] > 0.95:
        return "contradicted"
    return "inconclusive"


def score_variant(variant: str, lag: int, tr=None, pan=None):
    tr = truth() if tr is None else tr
    pan = panels() if pan is None else pan
    fc = attach_scores(pd.read_parquet(FC / f"{variant}_lag{lag}.parquet"), tr)
    fc = fc.merge(pan, on=["season", "location"], how="left")
    a, b = fc[fc.model == "ww"], fc[fc.model == "base"]
    rows = []
    for name, sel in (("primary (coverage >= 50%)", lambda d: d.coverage >= 0.5),
                      ("secondary (coverage >= 20%)", lambda d: d.coverage >= 0.2)):
        m = paired(a[sel(a)], b[sel(b)])
        r = rel_wis(m)
        r.update(variant=variant, lag=lag, panel=name, verdict=verdict(r))
        rows.append(r)
    return pd.DataFrame(rows), fc


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "main"
    lag = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    out, _ = score_variant(variant, lag)
    TAB.mkdir(parents=True, exist_ok=True)
    out.to_csv(TAB / f"relwis_{variant}_lag{lag}.csv", index=False)
    print(out[["variant", "lag", "panel", "rel_wis", "lo", "hi", "geo", "geo_lo", "geo_hi", "n_tasks", "n_locations", "verdict"]]
          .round(3).to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
