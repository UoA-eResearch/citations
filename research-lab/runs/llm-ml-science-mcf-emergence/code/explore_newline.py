#!/usr/bin/env python
"""EXPLORATORY E5 (deviations.md D6): OLMo-1B-0724 scored with the letter read after a newline. Applies the preregistered
departure and mass-crossing rules (and the sustained-crossing variant) to its six tasks, side by side with the
preregistered prompt. Output: results/tables/explore_newline_units.csv, explore_newline_trajectory.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
NAME = "OLMo-1B-0724-hf"


def sustained(t, m):
    for i in range(len(m)):
        if (m[i:] > 0.5).all():
            return t[i]
    return np.nan


def main():
    ck = pd.read_csv(RUN / "data" / "checkpoints.csv")
    ck = ck[ck.run == NAME]
    parts = []
    for r in ck.itertuples():
        d = pd.read_parquet(RUN / "results" / "evals_newline" / NAME / f"{r.revision}.parquet")
        d["chance"] = 1 / d.n_options
        g = d.groupby("task").agg(acc=("correct", "mean"), chance=("chance", "mean"), mass=("mass", "mean")).reset_index()
        g["tokens"] = r.tokens
        parts.append(g)
    tr = pd.concat(parts).sort_values(["task", "tokens"])
    tr.to_csv(TAB / "explore_newline_trajectory.csv", index=False)
    u = pd.read_csv(TAB / "units.csv")
    rows = []
    for task, g in tr.groupby("task"):
        t = g.tokens.values
        dep = A.first_persistent(t, g.acc.values > g.chance.values + 0.05)
        mc = A.first_persistent(t, g.mass.values > 0.5)
        pre = u[(u.run == NAME) & (u.task == task)].iloc[0]
        rows.append(dict(task=task, departure_newline_B=dep / 1e9, masscross_newline_B=mc / 1e9,
                         sustained_newline_B=sustained(t, g.mass.values) / 1e9,
                         final_excess_newline=(g.acc.values[-1] - g.chance.values[-1]) * 100,
                         departure_prereg_B=pre.departure_mcf5 / 1e9, final_excess_prereg=(pre.final_acc_mcf5 - pre.final_chance) * 100))
    out = pd.DataFrame(rows)
    out.to_csv(TAB / "explore_newline_units.csv", index=False)
    print(out.round(1).to_string(index=False))
    piv = tr.assign(excess=(tr.acc - tr.chance) * 100).pivot_table(index="tokens", columns="task", values="excess")
    piv.index = (piv.index / 1e9).round(0)
    print(piv.round(1).to_string())


if __name__ == "__main__":
    main()
