# Review: auckland-nz-kauri-dieback-multitemporal-lidar

Reviewer: independent adversarial review (Fable), 2026-10-23. Scripts and their JSON/log outputs are in
`review/reviewer_checks/` (aggregate statistics only; no tree coordinates are written). Rasters were read as windows.

## Verdict: **fix first**

The pipeline is honest and reproducible (features recompute exactly, positive controls pass, numbers match), but the
headline statistic is biased and the interpretation built on it is wrong in two places and overstated in a third:

- The pooled out-of-fold AUC used for H1/H2 has a null of **0.36**, not 0.5, on the 2014–15 labels. "0.51 = chance",
  "could not tell them apart at all" and "every variant at or below chance" are false; the observed value sits ~0.15
  above the estimator's null, and a one-feature test gives 0.58 against a place-effect null of 0.53.
- The 2021 "faint signal" is not distinguishable from a place effect (p ≈ 0.1–0.2 under a within-block label shuffle).
  If anything, it is the 2014–15 set that carries a weak tree-level signal.
- The 2014–15 design measures the same 15 m neighbourhood for positives and negatives (median nearest-neighbour
  1.4 m; 92% of positives have a healthy record within 15 m), so "Refuted" is a verdict on this label geometry, not on
  repeat LiDAR, and the report's generalisation to "open LiDAR at this resolution" is unsupported.

H1 "Refuted" probably survives on the preregistered rule (even the univariate upper bound, 0.65, is below 0.70), but
the AUCs, the H2 gain, the summary, the plain-terms section and the 2021 paragraph must be recomputed and rewritten
before publication.

## Findings

### 1. MAJOR — The AUC estimator is biased for clustered, rare positives; "chance level" is wrong

**Evidence.** `model.py:37-54` pools out-of-fold predictions across block folds and averages them over repeats;
`model.py:57-69` bootstraps that pooled vector. With 320 positives in 73 of 242 blocks, the number of positives in a
test fold ranges 18–110 and training prevalence 2.8–4.2% (`pooled_vs_perfold_auc.json`). The logistic intercept
therefore shifts fold to fold, and pooling ranks whole folds against each other: the fold whose training set lost the
most positives scores all of its (positive-rich) test trees low. A within-block label shuffle, which keeps every
block's positive count and destroys any tree-level signal, gives:

| 2014–15 labels, change model | study estimator (pooled) | mean per-fold AUC |
|---|---|---|
| observed | 0.508 | 0.557 |
| within-block shuffle null (60 perms, mean, 5–95%) | **0.360** (0.31–0.41) | 0.474 (0.43–0.52) |
| p (null ≥ observed) | < 0.017 | < 0.017 |

Per-fold means: static 0.573, static + change 0.600 (pooled: 0.545, 0.593), so the H2 gain is 0.027 per-fold vs
0.048 pooled. A one-feature logistic on ΔP95 alone under the same CV scores 0.485 pooled while the raw univariate
AUC of −ΔP95 (no fitting; sign fixed by the hypothesis) is **0.576** (block bootstrap 0.47–0.65) against a
within-block shuffle null of 0.534 (q95 0.551; p < 0.002, 500 perms) (`cv_variants.json`, `model_checks.json`).
Coefficients are stable in sign (ΔP95 and Δcover15 negative in 100% of 25 fits), so this is the estimator, not
sign-flipping. Positive controls pass (synthetic label from ΔP95 → 0.78; survey membership from static → 0.98), so
the machinery works when the signal is large; the bias matters precisely in the weak-signal regime the study is in.

**Consequence.** report.md:11-13 ("Every variant stays at or below chance"), :31-33 ("The scans could not tell them
apart at all"), :105-107 ("Neither the change features nor the static ones separate them") and the F1 title are not
supported. The H1 thresholds (plan.md:61-64) presuppose a 0.5 null. The H1 verdict likely remains Refuted (the
univariate upper bound is 0.65 < 0.70), but the stated AUCs and all of H2 are artefacts of the estimator.

**Fix.** Report the mean per-fold (or per-repeat, fold-averaged) AUC with a block bootstrap, and report the
within-block shuffle null next to every AUC; state H1 relative to the preregistered thresholds *and* to that null;
recompute H2 from per-fold AUCs; replace "chance" language with the measured null. Record this in deviations.md as a
post-hoc change of estimator forced by a flaw in the preregistered one.

### 2. MAJOR — The 2021 "faint signal" is not separable from a place effect; the 2014/2021 asymmetry is an artefact

**Evidence.** 2021 healthy trees sit farther from tracks (median 177 m vs 127–137 m), higher (167 m vs 139–149 m),
on steeper and more slip-masked ground than symptomatic ones (`labels_check.json`); place predicts status (static
AUC 0.59) and place predicts canopy rise. Within-block shuffle nulls for 2021 (`pooled_vs_perfold_auc.json`,
`cv_variants.json`): change model observed 0.549 / 0.557 (pooled / per-fold) vs null 0.531 / 0.542, p = 0.17 (60
perms; 0.08 with 100 perms); univariate −ΔP95 0.572 vs null 0.556, p = 0.05. The within-block mean difference in
ΔP95 (symptomatic − healthy) is −0.10 m (−0.21 to +0.02), including zero (`model_checks.json`). The gain interval
0.002–0.041 (report.md:17, :82) is a block bootstrap of pooled predictions; it is not a test against this null. By
contrast the 2014–15 set gives a within-block difference of −0.13 m (−0.27 to −0.02) and a univariate AUC with
p < 0.002 against its place null. The two label sets show the same faint ~0.1 m shortfall; the report's dichotomy
("no prognostic signal" vs "faint, time-aligned signal") comes from the estimator bias in Finding 1 plus the
different clustering of the two surveys.

**Consequence.** report.md:16-19, :33 ("sick trees' canopies grew a little less"), :113-114 ("That is evidence
that LiDAR registers dieback in aggregate") and the F2 title ("symptomatic trees rose slightly less") overstate.

**Fix.** Downgrade to "a 0.1 m shortfall in both label sets that is not reliably distinguishable from where the
trees stand"; report the within-block differences and shuffle p-values for both surveys; remove "evidence that LiDAR
registers dieback".

### 3. MAJOR — Positives and negatives in the 2014–15 survey are co-located at the scale of the feature

**Evidence** (`labels_check.json`, `isolation_check.json`). Among 2014–15 records the median nearest-neighbour
distance is 1.41 m (58% < 2 m, 85% < 5 m, 96% < 15 m). 31% of positives have a healthy record within 2 m, 61% within
5 m, 92% within 15 m; a positive's 15 m circle holds a median 13 survey records of which a median 25% are
symptomatic, and 61% of positives sit in circles that are mostly healthy records. 64 of 319 positive 2 m cells also
hold a negative. The ΔP95 of a positive correlates 0.81 with that of its nearest negative (median 3.4 m away; 12%
identical). One third of negatives have a status 2–4 record within 15 m (status 2 "ill thrift", 1,013 records, is
excluded from the labels but not from the neighbourhoods: 3,613 negatives have one within 15 m). The 2021 survey is
the opposite (median NN 49 m; 5% of positives have a healthy record within 15 m), which is why only it can be read as
a per-tree test. Exploratory: positives with no healthy record within 5 m vs negatives with no status 2–4 record
within 15 m give univariate AUC 0.61 (0.46–0.73; n = 118 / 6,090); positives that are the majority of their circle
0.64 (0.48–0.74; n = 54).

**Consequence.** A near-chance AUC was close to guaranteed by the label geometry, independent of what LiDAR can see.
The plan's "position error" caveat (plan.md:82-83) does not cover this: it is label density, not GPS error. The
generalisations at report.md:38-39 ("Open LiDAR at this resolution does not give a cheap early-warning map") and
:105-107 ("a cheap LiDAR screen calibrated on these labels would not work" is fine; the wider claim is not) go beyond
the test. The title's "Not at trees graded from the track" should say why.

**Fix.** State the co-location numbers in "What this does and does not show"; restrict the conclusion to "15 m
neighbourhood features cannot be tested with a survey that grades every stem along a track"; report the clean-subset
AUCs as exploratory with their wide intervals; name the ill-thrift contamination of the negative neighbourhoods.

### 4. MODERATE — The "2 m merge" is a grid-cell dedupe, not the plan's rule, and 9,069 is not a tree count

**Evidence.** `features.py:94-95` keys records by `round(x/2), round(y/2)` and drops later records in the same cell
with the same status; plan.md:27 says "records within 2 m of each other". Only 16% of 2014–15 records are exactly
coincident. A true within-2 m merge (connected components of pairs < 2 m apart, same status) gives 6,871 / 222 / 77
for statuses 1 / 3 / 4, not 9,069 / 234 / 86 (`labels_check.json`). 56 exact locations carry conflicting statuses
(14 with status 1 and 3, 3 with 1 and 4); these survive as a positive and a negative with identical features. The
survey evidently records stems at 0–3 m spacing, so whether these are duplicates or distinct stems is unknown.
Effect on AUC is small (near-neighbours share features anyway), but report.md:3-4, :56-57 present a tree count, and
the implementation change is not in deviations.md.

**Fix.** Call it a 2 m grid-cell dedupe; give the true-within-2 m count alongside; report the conflicting
same-location statuses; add the implementation deviation.

### 5. MODERATE — "Dropped because under half of their circle had valid LiDAR" is wrong; the slip mask is partly a slope mask

**Evidence.** Every one of the 12,247 rows has `valid_r15 = 1.0`; no tree has a raster-edge or water gap in any
radius (`recompute_features.json`: `trees_with_partial_circle = 0`). The 30 (2014–15) and 57 (2021) dropped trees
had more than half their circle masked by |ΔDEM| > 1 m (`features.py:151, 157`). Across random windows the masked
share averages 7% (q95 33%); it correlates with slope (Spearman 0.37 at 2014–15 trees), and in 2021 healthy trees
carry more of it (12% with > 25% masked vs 5–8% for symptomatic) (`labels_check.json`, `stable_windows.json`). The
no-mask variant gives the same 2014–15 AUC, so this does not change the verdict, but report.md:58 misdescribes the
exclusion and the mask removes steep ground under canopy as well as slips.

**Fix.** Correct the sentence; say what the mask removes and that 2021 drop-outs are 3% of trees.

### 6. MODERATE — The +1.25 m rise is not a datum artefact, but it is height-dependent and definition-dependent

**Evidence** (`stable_windows.json`, 1,279 random 128 × 128 windows; `linz_meta.json`). Datum and alignment are
fine: per-window median ΔDEM is +0.05 m (IQR +0.01 to +0.10); ΔCHM on E1-bare cells is +0.01 m; no DSM cell is
below its DEM in either epoch; all four mosaics share one grid and the source tiles are integer-aligned in EPSG:2193,
so the nearest-neighbour mosaicking introduces no shift. (The 2024 DEMs were reprocessed in Jan 2026, after the
DSMs; the bare-ground check shows no resulting offset.) But the rise in window P95 climbs monotonically with E1
canopy height: −0.03 m (0–5 m), +0.80 (5–10), +1.49 (10–15), +1.71 (15–20), +2.20 (20–25), +2.59 (25–30),
+2.99 m (> 30 m); Spearman 0.53. Uniform growth does not do that; a point-density / first-return difference between
the surveys does. The "stable" figure depends on the definition: study definition (E1 P95 > 15 m, ≥ 50 m from
records) 1.39 m median in my windows; any canopy 1.06 m; P95 > 25 m 1.88 m. Because 2014–15 trees stand under
~15 m canopy and 2021 trees under ~23 m, the 2.2 m vs 1.6 m figures (report.md:18-19, :94-97) carry this artefact.
Within each survey symptomatic and healthy trees have similar E1 P95 (14.7 / 14.9; 23.0 / 22.3), so it does not
drive the group contrast, but ΔP95 is correlated with E1 P95 (Spearman 0.34 in 2014–15), which adds noise to the
change features.

**Fix.** Report the class table; do not call the P95 > 15 m sample "stable"; say the between-survey difference is
height-dependent and therefore not a constant that cancels.

### 7. MINOR — Provenance

`git diff fb7799e e8a1bff -- code/features.py`: +15/−2 lines, the Overpass retry/cache only; `model.py` unchanged;
`figures.py` first appears with the results. Data files are untracked, so mosaic timing rests on mtimes (10:07–10:16,
after the plan commit at 10:03:08; trees.csv 10:29, primary.json 10:32, after fb7799e at 10:04:42). Acceptable;
report.md:48-49 should say the feature code was edited once after the commit, for the retry.

### 8. MINOR — Bootstrap over fixed predictions ignores refit variability

Per-repeat change AUCs are 0.507, 0.482, 0.500, 0.482, 0.576 (`model_checks.json`), a spread as wide as the
reported interval; the block bootstrap of the averaged predictions does not include it. The paired gain bootstrap
is implemented correctly (`model.py:84`; unpaired would be −0.05 to +0.14).

### 9. Verified, nothing to fix

- `circle_stats` reproduces exactly from an independent windowed implementation for 1,020 trees including all 320
  positives: indexing, CHM clipping, ≥ 50% rule, slip mask (max |diff| 0.0; `recompute_features.json`).
- trees.csv and trees_xy.parquet rows align by OBJECTID; `frame()` join is sound.
- Every number in report.md matches primary.json; descriptors (5 m / 130–180 m from track; ~15 m / ~23 m canopy)
  match the data.
- Care note holds: tracked outputs carry OBJECTID only; `data/trees_xy.parquet` is untracked; figures are aggregate.
  Review outputs are aggregate.
- H2 "Inconclusive" follows the preregistered rule on the reported numbers (gain 0.048 < 0.05; CI spans 0), but see
  Finding 1 for recomputation.

## What the corrected report should say, in one paragraph

With 15 m neighbourhood features and a survey that grades every stem along the track, symptomatic and healthy
trees share the same measurement; the preregistered AUC bar of 0.70 was not reached (per-fold AUC ≈ 0.56, univariate
0.58, upper bound 0.65), so H1 is Refuted for this design. Both label sets show the same ~0.1 m shortfall in canopy
rise around symptomatic trees; in 2014–15 it survives a within-block shuffle, in 2021 it does not. The two LiDAR
surveys differ by a height-dependent 1–3 m, which is growth plus a processing difference and is not a constant.
Nothing here says what crown-level repeat LiDAR could do.
