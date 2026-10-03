# Deviations log: activity-cliff noise-ceiling deep dive

Every departure from `plan.md`, with a timestamp (NZDT) taken from `date`. Newest last.

### D0. Preregistration (2026-10-03 00:15:52)
`plan.md` committed as 3f882c3, before any ChEMBL activity data were downloaded and before any model was trained.

### D1. Downloads and validation (logged 2026-10-03 01:25:48)
**ChEMBL download.** ChEMBL 37 was downloaded with 64 parallel HTTP range requests (`code/fetch_chembl.sh`); EBI
served about 40–90 KB/s per connection. Fourteen parts failed on the first pass and were re-fetched. The assembled file
matches EBI's published SHA-256 (33c20374…).

**Cliff validation passed.** MoleculeACE's cliff definition was reimplemented in `code/cliffs.py`, with the same
fingerprints, generic-graph scaffold and Levenshtein similarity. It reproduces the published `cliff_mol` in all 30
datasets, with at least 99.8% agreement and most at 100%.

**Empirical-Bayes calibration passed** (`code/validate_eb.py`). On 20,000 synthetic pairs, 78.8% of pairs with
confidence 0.7–0.9 are true cliffs, and every confidence decile is calibrated.

**Matching.** 99.7% of benchmark molecules match ChEMBL by full InChIKey, 0.2% by connectivity, and 0.1% not at all.

### D2. Re-reported values are not independent replicates (logged 2026-10-03 01:25:48)
**What the preregistered noise model gave.** σ = 0.000 for Ki and 0.016 for EC50, with held-out 90% coverage of 67% and
60%. That fails the preregistered check (85–95%).

**Cause.** Of the inter-document replicate pairs in the 30 targets, 67.1% (Ki) and 49.6% (EC50) have identical
pChEMBL values, to 2 decimals. Across all ChEMBL targets the figure is 68.9%. With noise of about 0.5 log units,
chance agreement at this resolution would be under 1%, so these are values re-reported in later documents (curated
sets, follow-up papers), not independent measurements.

- The median difference is therefore exactly 0, and so is a MAD-based σ.
- The plan's fallback (Student-t with the same scale) cannot repair a zero scale.

**Change, made before any hypothesis result.** H1 and H2 had not been computed meaningfully: with σ = 0, every
confidence was 1 or undefined.

- **Replicate pairs.** For each compound, document values identical to 2 decimals are collapsed. A pair is drawn only
  from distinct values; compounds with a single distinct value give no pair. The same applies to the intra-document arm.
  The all-target arm drops identical pairs.
- **Replicate counts.** n_i counts distinct values, not records, because a copied value does not reduce uncertainty.
  The same applies to n_all.
- **Post-2021 survival.** Only post-2021 values that differ from every earlier value of that compound count as new
  evidence.
- **Unchanged.** σ = 1.4826 × MAD / √2, the held-out coverage check, and the rule that the t-model becomes primary if
  coverage falls outside 85–95%.

Non-duplicate pairs give robust σ ≈ 0.46 for both types, and plain SD/√2 of 0.59–0.68. That is consistent with Landrum
& Riniker (2024) and suggests heavy tails; the coverage check decides between the Gaussian and t-models.

### D3. Noise model after D2: the t-model is primary by the plan's rule; consequences (logged 2026-10-03 02:30:38)
**Noise model** (`results/tables/noise_model.csv`, non-duplicate inter-document pairs):

| Type | σ | Pairs | Gaussian 90% coverage | t (4 df) 90% coverage |
|---|---|---|---|---|
| Ki | 0.503 | 2,155 | 80.1% | 87.7% |
| EC50 | 0.367 | 365 | 69.4% | 79.2% |

Gaussian coverage is outside 85–95%, so the t-model (4 df, scale σ) is primary, as plan §3 prescribes. EC50 is below
85% even under the t-model: real replicate differences have heavier tails still.

**What the data allow.** 46,650 of about 48,700 benchmark molecules have one distinct pre-2022 value, so s_i ≈ σ.

- Among all 127,827 similar pairs, the observed differences have SD 0.91, against a mean pair-noise SD of 0.67.
- Under heavy-tailed noise the deconvolution attributes most large differences to noise: prior mass beyond 1 log unit
  is 5.4%, and no cliff pair reaches confidence 0.9 (maximum 0.74, 99th percentile 0.47).
- Under Gaussian noise the prior mass beyond 1 log unit is 15%, and 17.8% of cliff pairs reach confidence 0.9.
- **Cliff confidence is therefore weakly identified from single-measurement data.** It depends on the assumed noise
  tail. Both models are reported; the t-model is primary per the plan.

**Consequences.**

- **H2 under the primary model is not testable.** No target has a high-confidence cliff molecule, and the plan
  excludes such targets. `analysis.py` now reports "not testable" in that case, not "inconclusive". The Gaussian arm
  (`--variant normal`) is reported as the main sensitivity analysis for H2.
- **The null must match.** `null.py` now draws t (4 df) noise for the primary run, matching the primary noise model.
  A Gaussian-noise null is run as a sensitivity arm.
- **Post-2021 survival is uninformative.** Only 1 cliff pair has new, non-copied post-2021 values for both molecules.

### D4. Results, and a delay (logged 2026-10-03 18:03:17)
**Delay.** The sensitivity arms and both nulls finished at 03:43, and stage 2 at 04:08. A wait loop whose pattern
matched its own command line kept running, so the results went unread until about 17:55. Nothing was changed in
between.

**Primary results** (`results/tables/hypotheses_*.csv`):

- **H1 supported.** Cliff pairs with confidence ≤ 0.8:

  | Arm | Share |
  |---|---|
  | Primary (t) | 100% [100, 100] |
  | Gaussian | 74.8% [69.6, 79.0] |
  | σ by potency tertile | 71.4% |
  | σ from all targets | 99.1% |
  | per-target prior | 99.0% |
  | n_i = 1, n_i = all entries, intra-document σ | 100% |

- **H2.** Not testable under the primary model (no high-confidence cliffs).
  - In the Gaussian arm it is **contradicted**, in the opposite direction to the prediction. The restricted gap is 0.441
    against 0.136 for all cliffs, so shrinkage = −2.25 [−3.34, −1.59] (29 targets).
  - In the σ-by-tertile arm: −1.22 [−2.23, −0.24].
  - High-confidence cliffs are those with the most extreme observed differences, and models err on them most.
- **H3 supported.** The noise-only world reproduces 171% [137, 229] of the observed gap with t noise, and 115%
  [91, 152] with Gaussian noise.
  - Null gaps: 0.244 (t) and 0.164 (Gaussian), against an observed 0.142.
  - Observed gaps by model: RF 0.138, SVR 0.151, GBM 0.129, kNN 0.152.
- **Label-shuffle control passed.** With cliff labels permuted among test molecules, the mean gap is −0.002, against
  0.142 real (`control_shuffle.csv`).
- **Secondary.** MoleculeACE-style gap (RMSE on cliff molecules minus RMSE on all test molecules): 0.091. Post-2021
  survival is not evaluable (1 pair).

### D5. Independent review (fix first) and the checks it led to (logged 2026-10-03 20:33:50)
**Review.** An independent reviewer agent (Fable 5.1) recommended *fix first*. The pipeline and nearly every number were
verified. Its central points, each now reproduced with committed code (`code/review_checks.py`, `code/null_v2.py`):

1. **The H2 "reversal" is a selection effect, not evidence that real cliffs are hard.** The noise-only worlds were run
   again with the real data's H2 rule applied to their own cliffs: confidence ≥ 0.9 under the real Gaussian prior and
   the real pair noise (`null_v2.csv`). They show the same enlarged restricted gap:

   | World | Restricted gap |
   |---|---|
   | Gaussian | 0.420 |
   | t | 0.558 |
   | document effect, σ_w = 0.3 | 0.345 |
   | document effect, σ_w = 0.2 | 0.338 |
   | **real data (Gaussian arm)** | **0.441** |

   High-confidence cliffs are those with the most extreme observed differences, the strongest regression-to-the-mean
   selection. The draft's claim that "the cliffs that clearly are real are genuinely hard" is withdrawn.
2. **The t-model is mis-specified for benchmark pairs, and H1 = 100% under it is structural.**
   - Under t (4 df) noise, cliff confidence cannot exceed about 0.74 for any observed difference.
   - Noise alone under the t-model predicts more extreme differences than exist (`review_model_check.csv`):

     | Threshold | Observed | Expected from noise, t | Expected from noise, Gaussian |
     |---|---|---|---|
     | \|d\| > 3 | 824 | 1,287 | 2.4 |
     | \|d\| > 4 | 85 | 420 | 0 |

   - The t-model fits the replicate differences (its variance matches theirs) but does not transfer to benchmark pairs.
   - The report now gives the Gaussian-arm results equal prominence: 74.8% [69.6, 79.0] with confidence ≤ 0.8 and 17.8%
     with confidence ≥ 0.9. The Gaussian confidences are now saved (`cliff_pairs_conf_normal.parquet`).
3. **Many cliff pairs share a source document** (`review_shared_docs.csv`).
   - 69% of cliff pairs and 79% of similar pairs have both molecules in a common pre-2022 ChEMBL document, and 90% of
     cliff-pair molecules have exactly one document. Lab-to-lab offsets cancel within such pairs, so the inter-document
     σ overstates their noise.
   - The intra-document arm does not address this. Its σ is 0.881 (Ki) and 0.660 (EC50), *larger* than inter-document,
     because distinct within-document values come from different assays.
   - Sensitivity (Gaussian; shared-document pairs given σ_w = 0.3): 77.1% of cliffs with confidence ≤ 0.8 and 15.8% with
     confidence ≥ 0.9 (`review_shared_doc_sensitivity.csv`). H1 is robust to this.
4. **Null calibration** (`null_v2.csv` against `null_v2_real_reference.csv`, 5 draws per target and world):

   | World | Pair-difference SD | Cliff test molecules | kNN non-cliff RMSE | Full gap |
   |---|---|---|---|---|
   | Real | 0.87 | 126 | 0.689 | 0.142 |
   | Gaussian | 0.805 | 135 | 0.515 | 0.163 |
   | t | 1.033 | 166 | 0.639 | 0.235 |
   | Document effect σ_w 0.3 | 0.665 | 87 | 0.431 | 0.148 |
   | Document effect σ_w 0.2 | 0.597 | 67 | 0.389 | 0.137 |

   - The Gaussian world is the best calibrated. The t world is over-dispersed: it produces 31% more cliffs than real.
   - Every world reproduces about 100% or more of the observed gap, including document-effect worlds with fewer cliffs
     than reality. H3 stands; the headline is now "about 100–115% at realistic noise", with 171% from the over-dispersed
     t world.
   - The noise-only worlds are easier to predict than reality (non-cliff RMSE 0.39–0.64 against 0.69).
5. **The label-shuffle control** permutes labels over fixed predictions, so it is a sanity check of the gap statistic,
   not of the null machinery. The wording is corrected.
6. **Re-reporting and arm details.**
   - The Ki identical-value fraction depends on the random pair drawn (67–71%); the report now says "about two-thirds".
   - About 17% of the remaining "distinct" pairs differ by under 0.05: near-copies after rounding or unit conversion.
     These bias σ slightly *down*.
   - σ from all ChEMBL targets: 0.325 (Ki) and 0.409 (EC50).
   - The σ-by-tertile H2 uses 13 targets, with 17 excluded.
   - The restricted gap compares high-confidence cliff molecules with all other test molecules, including
     non-high-confidence cliffs.
7. **Methods notes.**
   - A MAD-consistent t (4 df) scale would be 0.911σ; the preregistered "same scale" was kept.
   - `validate_eb.py` tests only Gaussian noise.
   - MoleculeACE's own curation (Dixon outliers, high-SD drop) makes the benchmark somewhat cleaner than raw ChEMBL
     replicates.

**Confirmation pass** (same reviewer, after the rewrite): *publish with edits*. Issues 1–8 are resolved or partly
resolved, and every new aggregate was recomputed and matches. Edits applied:

- The σ-by-tertile arm uses t noise and is labelled as such.
- The §4.2 table states which null run each column comes from.
- The restricted-gap range is 0.32–0.56 once the real H2 exclusion rule is applied in the null worlds; only the
  document-effect σ_w 0.2 world changes, from 0.338 to 0.324.
- Two wording fixes in plain terms and §4.1.
