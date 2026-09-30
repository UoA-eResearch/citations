#!/usr/bin/env python
"""EXPLORATORY (deviations.md D9): H2's pooled >= +3 LR by cohort year, with and without variants whose confident
label rests on a single submission from the laboratory that dominates the post-2022 benign wave (Ambry Genetics,
60% of 2023-2026 single-submitter benign submissions). Output: results/tables/explore_without_bulk.csv"""
import gzip
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import load, pooled_lr_boot  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
df = load()
with gzip.open(RUN / "data" / "raw" / "clinvar" / "submission_summary_2026-09-28.txt.gz", "rt") as fh:
    for line in fh:
        if line.startswith("#VariationID\t"):
            header = line.lstrip("#").rstrip("\n").split("\t")
            break
    sub = pd.read_csv(fh, sep="\t", names=header, dtype=str, usecols=["VariationID", "Submitter"])
sub["VariationID"] = pd.to_numeric(sub.VariationID, errors="coerce")
nsub = sub.groupby("VariationID").Submitter.agg(["nunique", "first"])
bulk = set(nsub[(nsub["nunique"] == 1) & (nsub["first"] == "Ambry Genetics")].index)
rows = []
for y in ["C2019", "N_2020"] + [f"N_{y}" for y in range(2021, 2027)]:
    d = df[df.cohort == y]
    for name, sel in (("all", d), ("without_single_lab_bulk", d[~d.variation_id.isin(bulk)])):
        for t in ("revel", "am", "esm1b"):
            lr, bs, cnt, _ = pooled_lr_boot(sel, t, seed=17)
            b = bs[:, 1][np.isfinite(bs[:, 1])]
            rows.append(dict(cohort=y, subset=name, tool=t, n=len(sel), lr_ge3=float(lr[1]),
                             lo5=float(np.percentile(b, 5)), hi95=float(np.percentile(b, 95))))
out = pd.DataFrame(rows)
out.to_csv(TAB / "explore_without_bulk.csv", index=False)
print(f"variants whose only submitter is Ambry Genetics: {len(bulk):,}")
print(out.pivot_table(index="cohort", columns=["tool", "subset"], values="lr_ge3").round(1).to_string())

# per-interval H1 verdicts without the single-lab bulk, on N_new and on the most recent cohorts (2024-2026)
from analyze import lr_table  # noqa: E402
from calib import TOOLS  # noqa: E402
rows = []
nn = df[df.primary_new & ~df.variation_id.isin(bulk)]
recent = nn[nn.year.isin([2024, 2025, 2026])]
for t in TOOLS:
    rows += [dict(subset="N_new_without_bulk", **r) for r in lr_table(nn, t, "N_new_wo", seed=23)]
    rows += [dict(subset="2024_2026_without_bulk", **r) for r in lr_table(recent, t, "2024-26_wo", seed=24)]
h = pd.DataFrame(rows)
h.to_csv(TAB / "explore_without_bulk_h1.csv", index=False)
for s in ("N_new_without_bulk", "2024_2026_without_bulk"):
    x = h[h.subset == s]
    print(s, x.verdict.value_counts().to_dict())
    print(x[x.verdict.isin(["falls short", "inconclusive"]) | x.tool.isin(["revel", "am"]) & (x.points > 0)]
          [["tool", "points", "n_P", "n_B", "lr", "lr_lo5", "lr_hi95", "target", "verdict"]].round(2).to_string(index=False))
