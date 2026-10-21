# Deviations from the preregistration

## D1 — 2026-10-22 04:32 NZDT — after the limb-1 results: the placebo cutoffs fail; post hoc checks

The preregistered RD gives a usable-share jump of +2.8 pp (−6.3 to +10.5) at 1 June 2023, so H1 is Inconclusive by
its rule. Placeholders rose by 9.0 pp (1.7 to 18.7) and absent fields fell by 11.9 pp (−16.0 to −8.5). But the
placebo cutoffs give jumps larger than the threshold in both directions: +17.3 pp at 1 June 2021 and −15.7 pp at 1
June 2022. The pooled daily series is dominated by shifts in who submits, most visibly pandemic-era SARS-CoV-2
surveillance, so a jump at any date mostly measures composition. Two checks, written after seeing this
(`code/analysis_rd_posthoc.py`):

1. the preregistered RD with SARS-CoV-2 samples (taxonomy 2697049) excluded, at the real and placebo cutoffs;
2. a within-submitter comparison: for organisations submitting in both windows, the change in their own shares,
   weighted by their samples, with an organisation-cluster bootstrap, at the real and placebo cutoffs.

H1's verdict stays the preregistered estimate's. The checks describe how far that estimate can be trusted.

## D2 — 2026-10-22 09:34 NZDT — gold-set labels (before any record was labelled)

The gold set was drawn as planned: 500 records, 250 with a linked publication, all of whose texts were retrieved. A
first look at six records showed that many untagged samples are laboratory organisms: mice, a medaka strain, grafted
tomato plants, a mouse-brain atlas. For these a country of collection is legitimately inapplicable. The plan's
"not determinable" label is therefore recorded in two kinds:
- **inapplicable**: laboratory stock, model organism raised in a lab, cell line, synthetic or engineered material;
- **not stated**: a country could exist, but the evidence does not give it.

Scoring is unchanged: both count as "not determinable", so a prediction on either counts as wrong. The split is
reported, because it shows how much of the missing metadata is legitimately missing.

**Pass 1** labels every record in sheet order and writes `data/gold/pass1_labels.csv` (sheet id, label, basis).
**Pass 2** follows at least five hours later, from `pass2.md` (its own order and ids), without reading pass 1's
labels. The arms are not run until both passes are complete.
