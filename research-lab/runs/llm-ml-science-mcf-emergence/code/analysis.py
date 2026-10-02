#!/usr/bin/env python
"""Departure and mass-crossing steps per unit (run x task) and the hypothesis tests (plan.md sec 4-5).

Departure: first checkpoint with MCF accuracy > chance + 0.05 that stays above at the next checkpoint.
Mass crossing: first checkpoint with mean letter mass > 0.5 that stays above at the next checkpoint.
Crossover: first checkpoint with MCF accuracy > CF accuracy, persistent in the same way.
A first exceedance at a run's last checkpoint cannot be confirmed by a next checkpoint and does not count.
Five-shot is primary; zero-shot is the secondary indicator. Steps are in training tokens.
Output (results/tables/): checkpoint_metrics.csv, units.csv, hypotheses.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
EV = RUN / "results" / "evals"


def metrics():
    ck = pd.read_csv(RUN / "data" / "checkpoints.csv")
    parts = []
    for r in ck.itertuples():
        f = EV / r.run / f"{r.revision}.parquet"
        if not f.exists():
            continue
        d = pd.read_parquet(f)
        d["chance"] = 1 / d.n_options
        g = d.groupby(["fmt", "task"]).agg(acc=("correct", "mean"), chance=("chance", "mean"), mass=("mass", "mean"),
                                           n=("correct", "size")).reset_index()
        g["group"], g["run"], g["revision"], g["tokens"] = r.group, r.run, r.revision, r.tokens
        parts.append(g)
    m = pd.concat(parts, ignore_index=True)
    w = m.pivot_table(index=["group", "run", "task", "revision", "tokens"], columns="fmt",
                      values=["acc", "mass", "chance"]).reset_index()
    w.columns = ["_".join(c).strip("_") for c in w.columns]
    return m, w.sort_values(["run", "task", "tokens"]).reset_index(drop=True)


def first_persistent(tokens, cond):
    for i in range(len(cond) - 1):
        if cond[i] and cond[i + 1]:
            return tokens[i]
    return np.nan


def units(w):
    rows = []
    for (group, run, task), g in w.groupby(["group", "run", "task"]):
        t = g.tokens.values
        ch = g.chance_mcf5.values
        row = dict(group=group, run=run, task=task, n_ckpt=len(g), first_tokens=t[0], last_tokens=t[-1],
                   final_acc_mcf5=g.acc_mcf5.values[-1], final_chance=ch[-1], final_mass_mcf5=g.mass_mcf5.values[-1],
                   final_acc_cf=g.acc_cf.values[-1])
        for sfx in ("mcf5", "mcf0"):
            row[f"departure_{sfx}"] = first_persistent(t, g[f"acc_{sfx}"].values > ch + 0.05)
            row[f"masscross_{sfx}"] = first_persistent(t, g[f"mass_{sfx}"].values > 0.5)
        row["crossover"] = first_persistent(t, g.acc_mcf5.values > g.acc_cf.values)
        rows.append(row)
    u = pd.DataFrame(rows)
    for sfx in ("mcf5", "mcf0"):
        dep, mc = u[f"departure_{sfx}"], u[f"masscross_{sfx}"]
        u[f"violation_{sfx}"] = dep.notna() & (mc.isna() | (mc > dep))
        u[f"leadratio_{sfx}"] = dep / mc
    return u


def spearman_boot(u, sfx, nboot=2000, seed=0):
    both = u[u[f"departure_{sfx}"].notna() & u[f"masscross_{sfx}"].notna()]
    n_units, n_runs = len(both), both.run.nunique()
    if n_units < 8 or n_runs < 3:
        return dict(n_units=n_units, n_runs=n_runs, rho=np.nan, lo=np.nan, hi=np.nan)
    x, y = np.log(both[f"masscross_{sfx}"].values), np.log(both[f"departure_{sfx}"].values)
    rho = stats.spearmanr(x, y).correlation
    runs = both.run.unique()
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(nboot):
        pick = rng.choice(runs, len(runs))
        b = pd.concat([both[both.run == r] for r in pick])
        if b[f"masscross_{sfx}"].nunique() > 1 and b[f"departure_{sfx}"].nunique() > 1:
            bs.append(stats.spearmanr(np.log(b[f"masscross_{sfx}"]), np.log(b[f"departure_{sfx}"])).correlation)
    lo, hi = np.nanpercentile(bs, [2.5, 97.5])
    return dict(n_units=n_units, n_runs=n_runs, rho=rho, lo=lo, hi=hi)


def main():
    m, w = metrics()
    w.to_csv(TAB / "checkpoint_metrics.csv", index=False)
    u = units(w)
    u.to_csv(TAB / "units.csv", index=False)
    rows = []
    for sfx in ("mcf5", "mcf0"):
        dep = u[u[f"departure_{sfx}"].notna()]
        nv = int(u[f"violation_{sfx}"].sum())
        h1 = "supported" if nv == 0 else ("contradicted" if nv >= 2 and nv >= 0.10 * len(dep) else "inconclusive")
        sp = spearman_boot(u, sfx)
        if np.isnan(sp["rho"]):
            h2 = "not testable"
        elif sp["rho"] >= 0.7 and sp["lo"] > 0:
            h2 = "supported"
        elif sp["hi"] < 0.7:
            h2 = "contradicted"
        else:
            h2 = "inconclusive"
        never = u[u[f"masscross_{sfx}"].isna()]
        rows.append(dict(indicator=sfx, primary=sfx == "mcf5", units=len(u), departing_units=len(dep), violations=nv,
                         H1=h1, **{f"H2_{k}": v for k, v in sp.items()}, H2=h2, never_crossing_units=len(never),
                         never_crossing_but_departing=int(never[f"departure_{sfx}"].notna().sum()),
                         median_leadratio=float(dep[f"leadratio_{sfx}"].median()) if len(dep) else np.nan))
    h = pd.DataFrame(rows)
    h.to_csv(TAB / "hypotheses.csv", index=False)
    print(h.round(3).to_string(index=False))
    print(u.groupby("group")[["departure_mcf5", "masscross_mcf5"]].agg(lambda s: f"{s.notna().sum()}/{len(s)}").to_string())


if __name__ == "__main__":
    main()
