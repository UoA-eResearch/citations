"""WIS under each truth, pairwise orderings, relative WIS, H1/H2 and bootstrap (plan sections 0 and 2).

  score.py test   WIS against a hand computation
  score.py run    -> results/tables/primary.json, pairs.csv, relative_wis.csv
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
INT, TAB = RUN / "data" / "interim", RUN / "results" / "tables"
TAB.mkdir(parents=True, exist_ok=True)
QS = np.array([0.01, 0.025] + [round(0.05 * k, 3) for k in range(1, 20)] + [0.975, 0.99])
B, SEED, MIN_PAIR, MIN_COV = 500, 20261025, 100, 0.8
ALPHAS = [0.02, 0.05] + [round(0.1 * k, 1) for k in range(1, 10)]          # 11 central intervals


def wis(qv, y):
    """qv: array (..., 23) of quantile values at QS; y: array (...). Interval form (Bracher et al. 2021)."""
    qd = {round(q, 3): i for i, q in enumerate(QS)}
    m = qv[..., qd[0.5]]
    tot = 0.5 * np.abs(y - m)
    for a in ALPHAS:
        lo, hi = qv[..., qd[round(a / 2, 3)]], qv[..., qd[round(1 - a / 2, 3)]]
        isc = (hi - lo) + (2 / a) * np.clip(lo - y, 0, None) + (2 / a) * np.clip(y - hi, 0, None)
        tot = tot + (a / 2) * isc
    return tot / (len(ALPHAS) + 0.5)


def test():
    qv = np.array([np.arange(23, dtype=float)])
    y = np.array([11.0])                       # the median is index 11 -> 11.0
    w = wis(qv, y)
    # each interval k contributes (a/2)*(hi-lo); hi-lo = 2*(11-i_lo)
    qd = {round(q, 3): i for i, q in enumerate(QS)}
    manual = sum((a / 2) * (qd[round(1 - a / 2, 3)] - qd[round(a / 2, 3)]) for a in ALPHAS) / 11.5
    assert abs(w[0] - manual) < 1e-12, (w, manual)
    w2 = wis(qv, np.array([30.0]))
    assert w2[0] > w[0]
    # independent check: WIS = sum over the 23 quantiles of pinball loss (1{y<q} - tau)(q - y), divided by K + 1/2
    rng = np.random.default_rng(1)
    for _ in range(200):
        q = np.sort(rng.normal(50, 20, 23)); yy = rng.normal(50, 30)
        pin = sum(((yy < qi) - t) * (qi - yy) for qi, t in zip(q, QS)) / 11.5
        assert abs(wis(q[None, :], np.array([yy]))[0] - pin) < 1e-9
    print("wis test pass", round(float(w[0]), 4), round(float(w2[0]), 4))


def is_excluded(m):
    s = m.lower()
    return "ensemble" in s or "baseline" in s


def matrices(F, T):
    """Per season x horizon: models, cells (ref_date, location), WIS matrices under first and final truth."""
    W = F.pivot_table(index=["season", "model", "ref_date", "location", "horizon", "target_end_date"], columns="q", values="value")
    W = W.dropna()
    W = W[[c for c in QS if c in W.columns]]
    idx = W.index.to_frame(index=False)
    tt = T.set_index(["location", "target_end_date"])
    j = idx.merge(T[["location", "target_end_date", "first_value", "final_value"]], on=["location", "target_end_date"], how="left")
    ok = j.first_value.notna() & j.final_value.notna()
    qv = np.sort(W.to_numpy()[ok.to_numpy()], axis=1)          # enforce monotone quantiles
    j = j[ok].reset_index(drop=True)
    j["wis_first"] = wis(qv, j.first_value.to_numpy())
    j["wis_final"] = wis(qv, j.final_value.to_numpy())
    out = {}
    for (s, h), g in j.groupby(["season", "horizon"]):
        cells = g[["ref_date", "location"]].drop_duplicates().sort_values(["ref_date", "location"]).reset_index(drop=True)
        cells["c"] = np.arange(len(cells))
        g = g.merge(cells, on=["ref_date", "location"])
        models = sorted(g.model.unique())
        mi = {m: i for i, m in enumerate(models)}
        X1 = np.full((len(models), len(cells)), np.nan)
        X2 = np.full((len(models), len(cells)), np.nan)
        X1[g.model.map(mi), g.c] = g.wis_first
        X2[g.model.map(mi), g.c] = g.wis_final
        out[(s, h)] = {"models": models, "cells": cells, "first": X1, "final": X2}
    return out, j


def pairwise(X, w):
    """Weighted pairwise mean WIS on common sets: returns (means[i,j] of model i on common set with j, counts)."""
    M = ~np.isnan(X)
    X0 = np.where(M, X, 0.0)
    S = (X0 * w) @ M.T.astype(float)
    N = (M * w).astype(float) @ M.T.astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        return S / N, N


def analyse(mat, w_fn):
    rev, tot, best = 0, 0, {}
    per = {}
    for key, d in mat.items():
        w = w_fn(key, d)
        m1, n = pairwise(d["first"], w)
        m2, _ = pairwise(d["final"], w)
        cnt = pairwise(np.where(np.isnan(d["first"]), np.nan, 1.0), np.ones_like(w))[1]   # unweighted common counts
        iu = np.triu_indices(len(d["models"]), 1)
        ok = cnt[iu] >= MIN_PAIR
        a1 = np.sign(m1[iu] - m1.T[iu])
        a2 = np.sign(m2[iu] - m2.T[iu])
        valid = ok & (a1 != 0) & (a2 != 0) & np.isfinite(a1) & np.isfinite(a2)
        r = int((a1[valid] != a2[valid]).sum())
        rev += r
        tot += int(valid.sum())
        per[key] = (r, int(valid.sum()))
        # relative WIS among well-covered models
        cov = (~np.isnan(d["first"])).mean(1)
        sel = np.where(cov >= MIN_COV)[0]
        if len(sel) >= 2:
            res = {}
            for lab, mm in (("first", m1), ("final", m2)):
                ratio = mm[np.ix_(sel, sel)] / mm[np.ix_(sel, sel)].T
                np.fill_diagonal(ratio, 1.0)
                theta = np.exp(np.nanmean(np.log(ratio), axis=1))
                cand = [(theta[k], d["models"][i]) for k, i in enumerate(sel) if not is_excluded(d["models"][i])]
                res[lab] = min(cand)[1] if cand else None
                res[f"theta_{lab}"] = {d["models"][i]: float(theta[k]) for k, i in enumerate(sel)}
            best[key] = res
    return rev, tot, per, best


def run():
    F = pd.read_parquet(INT / "forecasts.parquet")
    T = pd.read_parquet(INT / "truth.parquet")
    T = T[(T.hub == "old") | (T.hub == "new")]
    # the old hub's truth serves 2022-23, the new hub's 2023-24 onward
    F_old, F_new = F[F.hub == "old"], F[F.hub == "new"]
    mat_o, j_o = matrices(F_old, T[T.hub == "old"])
    mat_n, j_n = matrices(F_new, T[T.hub == "new"])
    mat = {**mat_o, **mat_n}
    J = pd.concat([j_o, j_n])
    rev, tot, per, best = analyse(mat, lambda k, d: np.ones(len(d["cells"])))
    share = rev / tot if tot else None
    changed = [k for k, v in best.items() if v.get("first") != v.get("final")]
    # bootstrap over reference dates within season
    rng = np.random.default_rng(SEED)
    seasons = sorted({k[0] for k in mat})
    dates = {s: sorted({d for k, v in mat.items() if k[0] == s for d in v["cells"].ref_date}) for s in seasons}
    bshare, bchanged = [], {k: 0 for k in best}
    for b in range(B):
        draw = {s: pd.Series(rng.choice(len(dates[s]), len(dates[s]))).value_counts() for s in seasons}
        dw = {s: pd.Series(draw[s].values, index=[dates[s][i] for i in draw[s].index]) for s in seasons}

        def wfn(k, d):
            return d["cells"].ref_date.map(dw[k[0]]).fillna(0).to_numpy(float)
        r_, t_, _, best_ = analyse(mat, wfn)
        bshare.append(r_ / t_ if t_ else np.nan)
        for k, v in best_.items():
            if k in bchanged and v.get("first") != v.get("final"):
                bchanged[k] += 1
    lo, hi = np.nanpercentile(bshare, [2.5, 97.5])
    h1 = "Supported" if lo >= 0.20 else "Refuted" if hi < 0.20 else "Inconclusive"
    robust = [k for k in changed if bchanged.get(k, 0) / B >= 0.5]
    h2 = "Supported" if robust else "Refuted" if not changed else "Inconclusive"
    out = {"pairs_compared": tot, "reversals": rev, "reversal_share": round(share, 4), "reversal_share_ci": [round(float(lo), 4), round(float(hi), 4)],
           "H1": h1, "per_season_horizon": {f"{k[0]} h{int(k[1])}": {"reversals": v[0], "pairs": v[1]} for k, v in per.items()},
           "best_changed": [f"{k[0]} h{int(k[1])}" for k in changed], "best_changed_bootstrap_share": {f"{k[0]} h{int(k[1])}": round(bchanged[k] / B, 3) for k in bchanged},
           "best": {f"{k[0]} h{int(k[1])}": {"first": v.get("first"), "final": v.get("final")} for k, v in best.items()}, "H2": h2}
    # secondary: revision size, rank agreement
    Tt = T.copy()
    Tt["season"] = Tt.target_end_date.map(lambda d: f"{d.year if d.month >= 8 else d.year - 1}-{str((d.year if d.month >= 8 else d.year - 1) + 1)[2:]}")
    Tt = Tt[Tt.final_value > 0]
    Tt["rev_pct"] = (Tt.first_value - Tt.final_value) / Tt.final_value * 100
    out["revision"] = {s: {"median_abs_pct": round(float(g.rev_pct.abs().median()), 2), "share_over_10pct": round(float((g.rev_pct.abs() > 10).mean()), 4),
                           "median_signed_pct": round(float(g.rev_pct.median()), 2), "n": int(len(g))}
                       for s, g in Tt.groupby("season") if s in ("2022-23", "2023-24", "2024-25")}
    from scipy.stats import spearmanr
    out["rank_agreement"] = {}
    for k, v in best.items():
        a, b2 = v["theta_first"], v["theta_final"]
        common = sorted(set(a) & set(b2))
        if len(common) >= 4:
            out["rank_agreement"][f"{k[0]} h{int(k[1])}"] = round(float(spearmanr([a[m] for m in common], [b2[m] for m in common])[0]), 4)
    out["mean_wis"] = {"first": round(float(J.wis_first.mean()), 3), "final": round(float(J.wis_final.mean()), 3), "forecasts": int(len(J))}
    rw = [{"season_h": f"{k[0]} h{int(k[1])}", "model": m, "rel_wis_first": v["theta_first"][m], "rel_wis_final": v["theta_final"].get(m)}
          for k, v in best.items() for m in v["theta_first"]]
    pd.DataFrame(rw).to_csv(TAB / "relative_wis.csv", index=False)
    (TAB / "primary.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps({k: out[k] for k in ("pairs_compared", "reversals", "reversal_share", "reversal_share_ci", "H1", "best_changed", "best_changed_bootstrap_share", "H2", "revision", "rank_agreement", "mean_wis")}, indent=1, default=str))


if __name__ == "__main__":
    {"test": test, "run": run}[sys.argv[1]]()
