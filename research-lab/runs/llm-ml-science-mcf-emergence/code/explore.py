#!/usr/bin/env python
"""EXPLORATORY analyses defined after the primary results (deviations.md D4).

E1 within-run synchrony of departures across the six tasks; E2 zero-shot vs five-shot lead time; E3 MCF accuracy above
chance at matched training tokens (~300B) and at the end of the 1B OLMo runs; E4 how often the CF crossover rule fires at
the first checkpoint only because CF accuracy is below chance.
Output: results/tables/explore_synchrony.csv, explore_leadtime.csv, explore_matched_tokens.csv, explore_crossover.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
B = 1e9


def main():
    u = pd.read_csv(TAB / "units.csv")
    w = pd.read_csv(TAB / "checkpoint_metrics.csv")
    # E1
    rows = []
    for run, g in u[u.departure_mcf5.notna()].groupby("run"):
        ck = sorted(w[w.run == run].tokens.unique())
        idx = [ck.index(t) for t in g.departure_mcf5]
        rows.append(dict(run=run, tasks=len(g), first_B=g.departure_mcf5.min() / B, last_B=g.departure_mcf5.max() / B,
                         median_B=g.departure_mcf5.median() / B, spread_checkpoints=max(idx) - min(idx),
                         same_checkpoint=int(pd.Series(idx).value_counts().max())))
    e1 = pd.DataFrame(rows)
    e1.to_csv(TAB / "explore_synchrony.csv", index=False)
    print("E1\n", e1.round(1).to_string(index=False))
    # E2
    d = u[u.departure_mcf5.notna()].copy()
    e2 = pd.DataFrame(dict(run=d.run, task=d.task, lead5=d.departure_mcf5 / d.masscross_mcf5,
                           lead0=d.departure_mcf0 / d.masscross_mcf0))
    e2.to_csv(TAB / "explore_leadtime.csv", index=False)
    print("E2 median lead ratio five-shot %.1f, zero-shot %.1f" % (e2.lead5.median(), e2.lead0.median()))
    # E3
    rows = []
    for run in ("pythia-6.9b", "OLMo-2-1124-7B", "OLMo-7B-0424-hf", "OLMo-2-0425-1B", "OLMo-1B-0724-hf"):
        g = w[w.run == run]
        target = 300 * B if "1B" not in run else g.tokens.max()
        t = g.tokens.values[np.argmin(np.abs(np.log(g.tokens.values) - np.log(target)))]
        h = g[g.tokens == t]
        rows.append(dict(run=run, tokens_B=t / B, mean_excess=float((h.acc_mcf5 - h.chance_mcf5).mean()),
                         max_excess=float((h.acc_mcf5 - h.chance_mcf5).max()), mean_mass=float(h.mass_mcf5.mean())))
    e3 = pd.DataFrame(rows)
    e3.to_csv(TAB / "explore_matched_tokens.csv", index=False)
    print("E3\n", e3.round(3).to_string(index=False))
    # E4
    first = w.sort_values("tokens").groupby(["run", "task"]).head(1)
    cr = u.merge(first[["run", "task", "tokens", "acc_cf", "chance_mcf5"]], on=["run", "task"])
    at_first = cr[cr.crossover == cr.tokens]
    e4 = pd.DataFrame(dict(units=[len(u)], crossover_defined=[int(u.crossover.notna().sum())],
                           crossover_at_first_checkpoint=[len(at_first)],
                           of_which_cf_below_chance=[int((at_first.acc_cf < at_first.chance_mcf5).sum())]))
    e4.to_csv(TAB / "explore_crossover.csv", index=False)
    print("E4\n", e4.to_string(index=False))


if __name__ == "__main__":
    main()
