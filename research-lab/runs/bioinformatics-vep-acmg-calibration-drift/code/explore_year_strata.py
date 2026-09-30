#!/usr/bin/env python
"""EXPLORATORY (not preregistered; deviations.md D6): pooled strongest-interval LRs by cohort year x review stratum,
to locate the post-2022 rise of H2 (single-submitter labs vs multi-submitter / expert-panel classifications, and
VCEP vs other genes). Output: results/tables/explore_year_strata.csv"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import load, pooled_lr_boot  # noqa: E402

TAB = Path(__file__).resolve().parents[1] / "results" / "tables"
df = load()
rows = []
for t in ("revel", "am", "esm1b"):
    for y in ["C2019", "N_2020"] + [f"N_{y}" for y in range(2021, 2027)]:
        d = df[df.cohort == y]
        for s, sub in (("stars_1", d[d.stars == 1]), ("stars_2plus", d[d.stars >= 2]),
                       ("vcep_gene", d[d.vcep_gene]), ("non_vcep_gene", d[~d.vcep_gene])):
            if len(sub) < 50:
                continue
            lr, bs, cnt, _ = pooled_lr_boot(sub, t, seed=7)
            tot = cnt.sum(0)
            b = bs[:, 1][np.isfinite(bs[:, 1])]
            rows.append(dict(tool=t, cohort=y, stratum=s, n_P_ge3=int(tot[1, 0]), n_B_ge3=int(tot[1, 1]),
                             N_P=int(tot[-1, 0]), N_B=int(tot[-1, 1]), lr_ge3=float(lr[1]),
                             lo5=float(np.percentile(b, 5)) if len(b) else np.nan, hi95=float(np.percentile(b, 95)) if len(b) else np.nan,
                             frac_P_in_ge3=float(tot[1, 0] / tot[-1, 0]) if tot[-1, 0] else np.nan))
out = pd.DataFrame(rows)
out.to_csv(TAB / "explore_year_strata.csv", index=False)
print(out[out.tool == "revel"].pivot_table(index="cohort", columns="stratum", values="lr_ge3").round(1).to_string())
print(out[out.tool == "revel"].pivot_table(index="cohort", columns="stratum", values="frac_P_in_ge3").round(3).to_string())
print(out[out.tool == "esm1b"].pivot_table(index="cohort", columns="stratum", values="lr_ge3").round(1).to_string())

# composition of newly classified labels by year x stratum (which class moved?)
rows = []
for y in ["C2019", "N_2020"] + [f"N_{y}" for y in range(2021, 2027)]:
    d = df[(df.cohort == y) & df.revel.notna()]
    for s, sub in (("1-star", d[d.stars == 1]), ("2+star", d[d.stars >= 2])):
        for lab in ("B", "P"):
            g = sub[sub.label == lab]
            rows.append(dict(cohort=y, stratum=s, label=lab, n=len(g), median_revel=float(g.revel.median()),
                             frac_ge3=float((g.pts_revel >= 3).mean()), frac_le_m3=float((g.pts_revel <= -3).mean())))
comp = pd.DataFrame(rows)
comp.to_csv(TAB / "explore_composition.csv", index=False)
print(comp[comp.label == "B"].pivot_table(index="cohort", columns="stratum", values="median_revel").round(3).to_string())
