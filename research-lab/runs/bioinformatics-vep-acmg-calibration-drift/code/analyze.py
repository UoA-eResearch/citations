#!/usr/bin/env python
"""H1, H2, H4 and the reproduction gate (plan.md sec 5) on the joined, rare-filtered analysis table.

Outputs (results/tables/): h1_interval_lr.csv (every tool x cohort x interval), h1_verdicts.csv (N_new),
h2_trend.csv (pooled >= +3 / <= -3 intervals by cohort year) and h2_prepost.csv, h4_strata.csv, gate_c2019.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from calib import TOOLS, assign_points, bootstrap_lr, gene_counts, interval_lr, intervals, local_posterior_thresholds, lr_target, verdict  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
PROC, TAB = RUN / "data" / "processed", RUN / "results" / "tables"
NBOOT = 2000


def load():
    df = pd.read_parquet(PROC / "analysis_table.parquet")
    df = df[df.rare & df.label.isin(["P", "B"])].copy()
    for t in TOOLS:
        df[f"pts_{t}"] = assign_points(t, df[t].values)
    return df


def lr_table(d: pd.DataFrame, tool: str, cohort: str, seed=0, extra=None):
    iv = intervals(tool)
    genes, cnt = gene_counts(d, f"pts_{tool}", iv)
    if cnt.shape[0] == 0:
        return []
    tot = cnt.sum(0)
    lr = interval_lr(tot)
    bs = bootstrap_lr(cnt, NBOOT, seed)
    rows = []
    for i, k in enumerate(iv):
        col = bs[:, i]
        lo, hi = np.nanpercentile(col, [5, 95]) if np.isfinite(col).any() else (np.nan, np.nan)
        nP, nB = int(tot[i, 0]), int(tot[i, 1])
        n_min = nB if k > 0 else nP
        rows.append(dict(tool=tool, cohort=cohort, points=k, n_P=nP, n_B=nB, N_P=int(tot[-1, 0]), N_B=int(tot[-1, 1]),
                         n_genes=len(genes), lr=float(lr[i]), lr_lo5=float(lo), lr_hi95=float(hi), target=lr_target(k),
                         frac_inf_boot=float(np.mean(bs[:, i] >= 1e12)), verdict=verdict(k, lr[i], lo, hi, n_min),
                         **(extra or {})))
    return rows


def pooled(d: pd.DataFrame, tool: str):
    """Collapse the intervals to the two strongest pooled ones: points >= +3 -> 3, <= -3 -> -3, else 0."""
    d = d.copy()
    p = d[f"pts_{tool}"].values
    d["pts_pool"] = np.where(np.isnan(p), np.nan, np.where(p >= 3, 3, np.where(p <= -3, -3, 0)))
    return d


def pooled_lr_boot(d, tool, seed=0):
    d = pooled(d, tool)
    genes, cnt = gene_counts(d, "pts_pool", [-3, 3])
    return interval_lr(cnt.sum(0)), bootstrap_lr(cnt, NBOOT, seed), cnt, genes


def main():
    df = load()
    cohorts = {"C2019": df[df.cohort == "C2019"], "N_2020": df[df.cohort == "N_2020"], "N_new": df[df.primary_new]}
    for y in range(2021, 2027):
        cohorts[f"N_{y}"] = df[(df.cohort == f"N_{y}")]
    sizes = [dict(cohort=c, P=int((d.label == "P").sum()), B=int((d.label == "B").sum()), genes=int(d.gene.nunique()))
             for c, d in cohorts.items() if c != "N_new"]
    pd.DataFrame(sizes).to_csv(TAB / "cohort_sizes_rare.csv", index=False)
    # ---- H1 ------------------------------------------------------------------------------------------------------
    rows = []
    for t in TOOLS:
        for c, d in cohorts.items():
            rows += lr_table(d, t, c, seed=hash((t, c)) % 2**32)
    h1 = pd.DataFrame(rows)
    h1.to_csv(TAB / "h1_interval_lr.csv", index=False)
    v = h1[h1.cohort == "N_new"][["tool", "points", "n_P", "n_B", "lr", "lr_lo5", "lr_hi95", "target", "verdict"]]
    v.to_csv(TAB / "h1_verdicts.csv", index=False)
    print("H1 on N_new:\n" + v.round(3).to_string(index=False), flush=True)
    # ---- H2: pooled strongest intervals by year, pre vs post -------------------------------------------------------
    trows = []
    for t in TOOLS:
        for y in ["C2019", "N_2020"] + [f"N_{y}" for y in range(2021, 2027)]:
            d = cohorts[y]
            lr, bs, cnt, _ = pooled_lr_boot(d, t, seed=11)
            tot = cnt.sum(0)
            for i, side in enumerate(("<= -3", ">= +3")):
                b = bs[:, i][np.isfinite(bs[:, i])]
                trows.append(dict(tool=t, cohort=y, side=side, n_P=int(tot[i, 0]), n_B=int(tot[i, 1]), lr=float(lr[i]),
                                  lr_lo5=float(np.percentile(b, 5)) if len(b) else np.nan,
                                  lr_hi95=float(np.percentile(b, 95)) if len(b) else np.nan))
    pd.DataFrame(trows).to_csv(TAB / "h2_trend.csv", index=False)
    windows = {"revel": ([2021, 2022], [2024, 2025, 2026]), "am": ([2021, 2022, 2023], [2025, 2026]),
               "esm1b": ([2021, 2022], [2024, 2025, 2026])}
    prow = []
    for t, (pre, post) in windows.items():
        dpre = df[df.primary_new & df.year.isin(pre)]
        dpost = df[df.primary_new & df.year.isin(post)]
        lpre, bpre, _, _ = pooled_lr_boot(dpre, t, seed=21)
        lpost, bpost, _, _ = pooled_lr_boot(dpost, t, seed=22)
        with np.errstate(divide="ignore", invalid="ignore"):
            lr_ratio = np.log(bpost) - np.log(bpre)
        for i, side in enumerate(("<= -3", ">= +3")):
            r = lr_ratio[:, i][np.isfinite(lr_ratio[:, i])]
            prow.append(dict(tool=t, side=side, pre_years=pre, post_years=post, lr_pre=float(lpre[i]), lr_post=float(lpost[i]),
                             log_ratio=float(np.log(lpost[i]) - np.log(lpre[i])),
                             log_ratio_lo5=float(np.percentile(r, 5)) if len(r) else np.nan,
                             log_ratio_hi95=float(np.percentile(r, 95)) if len(r) else np.nan,
                             frac_boot_finite=float(len(r) / len(lr_ratio))))
    h2 = pd.DataFrame(prow)
    h2.to_csv(TAB / "h2_prepost.csv", index=False)
    print("H2 pre/post:\n" + h2.round(3).to_string(index=False), flush=True)
    # ---- H4: strata on N_new ----------------------------------------------------------------------------------------
    srows = []
    nn = cohorts["N_new"]
    strata = {"stars_1": nn[nn.stars == 1], "stars_2plus": nn[nn.stars >= 2],
              "vcep_gene": nn[nn.vcep_gene], "non_vcep_gene": nn[~nn.vcep_gene]}
    for t in ("revel", "am"):
        for s, d in strata.items():
            srows += lr_table(d, t, "N_new", seed=31, extra={"stratum": s})
    h4 = pd.DataFrame(srows)
    h4.to_csv(TAB / "h4_strata.csv", index=False)
    # ---- reproduction gate on C2019 ----------------------------------------------------------------------------------
    gate = {}
    for t in ("revel", "am"):
        d = cohorts["C2019"].dropna(subset=[t])
        th, _ = local_posterior_thresholds(d[t].values, d.label.values, t, n_boot=1000)
        pub = {**{k: v for k, v in TOOLS[t]["path"].items()}, **{k: v for k, v in TOOLS[t]["ben"].items()}}
        gate[t] = {str(k): dict(rederived=th.get(k), published=pub.get(k)) for k in sorted(pub)}
    json.dump(gate, open(TAB / "gate_c2019.json", "w"), indent=2)
    print("gate:", json.dumps(gate))


if __name__ == "__main__":
    sys.exit(main())
