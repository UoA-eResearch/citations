#!/usr/bin/env python
"""EXPLORATORY robustness checks for H1 (deviations.md D8, prompted by the independent review):
  1. boundary slices: LR in the thin score slice just inside each pathogenic interval's lower bound (where the
     target applies exactly, rather than the interval average);
  2. H1 on the 2021-2022 cohorts only (before the post-2022 gene-mix wave);
  3. H1 on N_new excluding variants that had been confident in C2019 / N_2020 and re-entered after a non-confident
     interlude (1.2%).
Output: results/tables/explore_robustness.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import load, lr_table  # noqa: E402
from calib import TOOLS, bootstrap_lr, gene_counts, interval_lr, lr_target  # noqa: E402

TAB = Path(__file__).resolve().parents[1] / "results" / "tables"
SLICE = {"revel": 0.018, "am": 0.004, "bayesdel": 0.04, "varity_r": 0.015, "esm1b": 1.5}


def boundary_rows(d, tool):
    t = TOOLS[tool]
    rows = []
    for k, b in sorted(t["path"].items()):
        s = d[tool].round(t["dec"])
        w = SLICE.get(tool, 0.02)
        inside = (s >= b) & (s < b + w) if t["hip"] else (s <= b) & (s > b - w)
        dd = d.assign(pts_slice=np.where(d[tool].isna(), np.nan, np.where(inside, 1, 0)))
        genes, cnt = gene_counts(dd, "pts_slice", [1])
        lr = interval_lr(cnt.sum(0))[0]
        bs = bootstrap_lr(cnt, 1000, 9)[:, 0]
        tot = cnt.sum(0)
        rows.append(dict(check="boundary_slice", tool=tool, points=k, slice=f"[{b}, {b + w if t['hip'] else b - w})",
                         n_P=int(tot[0, 0]), n_B=int(tot[0, 1]), lr=float(lr), lr_lo5=float(np.nanpercentile(bs, 5)),
                         lr_hi95=float(np.nanpercentile(bs, 95)), target=lr_target(k)))
    return rows


def main():
    df = load()
    nn = df[df.primary_new]
    rows = []
    for tool in ("revel", "am", "bayesdel", "varity_r"):
        rows += boundary_rows(nn, tool)
    early = df[df.cohort.isin(["N_2021", "N_2022"])]
    reentrant = set(df[df.cohort.isin(["C2019", "N_2020"])].variation_id)
    nn_clean = nn[~nn.variation_id.isin(reentrant)]
    for tool in TOOLS:
        rows += [dict(check="cohort_2021_2022", **r) for r in lr_table(early, tool, "N_2021-22", seed=13)]
        rows += [dict(check="N_new_no_reentrants", **r) for r in lr_table(nn_clean, tool, "N_new_clean", seed=14)]
    out = pd.DataFrame(rows)
    out.to_csv(TAB / "explore_robustness.csv", index=False)
    print(f"re-entrants excluded: {int(nn.variation_id.isin(reentrant).sum())} of {len(nn)}")
    cols = ["check", "tool", "points", "n_P", "n_B", "lr", "lr_lo5", "lr_hi95", "target"]
    print(out[out.check == "boundary_slice"][cols + ["slice"]].round(2).to_string(index=False))
    for c in ("cohort_2021_2022", "N_new_no_reentrants"):
        s = out[out.check == c]
        print(c, s.verdict.value_counts().to_dict())
        print(s[s.tool.isin(["revel", "am"])][cols + ["verdict"]].round(2).to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
