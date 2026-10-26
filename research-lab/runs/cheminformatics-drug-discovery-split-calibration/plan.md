# Plan (preregistration): which retrospective data split predicts prospective bioactivity performance?

Lead: `cheminformatics-drug-discovery-split-calibration`. Written before any ChEMBL table was read: the release
tarballs were downloading.

**Seen before this plan:**
- Abstracts: "Clever Hans in Chemistry" (arXiv 2512.20924), which proposes author-disjoint splits without validating
  them against future data; and Almendra & Falcão 2026 (JCIM, doi:10.1021/acs.jcim.6c02796).
  - Almendra & Falcão: on 14 ChEMBL classification datasets, chronological (publication-year) validation shows a
    large generalisation gap that random and structure-filtered validation do not reproduce.
  - They test no document- or author-disjoint splitter, no regression, no model ranking, and no truth taken from
    later releases. Part (a) below is therefore partly confirmatory.
- ChEMBL 33 and 37 file sizes and checksums. No ChEMBL table has been opened.

## 0. Hypotheses

**Unit:** a target.

**Retrospective estimate:** a model's RMSE (pChEMBL units) on held-out data inside ChEMBL 33, under a given splitter.

**Prospective truth:** the RMSE of the same model, trained on all of the target's ChEMBL 33 data, on the target's
prospective set (section 2).

**Signed bias** = retrospective estimate − prospective truth. Negative means the split understated the error.

**Primary model:** ECFP4 + random forest. All five model families are reported.

**Intervals:** bootstrap over targets (2,000 resamples, seed 20261026).

- **H1 (random and scaffold splits understate prospective error).** For each of the random and Bemis–Murcko scaffold
  splitters:
  - Supported if the median signed bias is ≤ −0.25 and its 95% upper bound is < 0.
  - Refuted if its 95% lower bound is > −0.25.
  - Inconclusive otherwise.
  - H1 is Supported if both splitters are, Refuted if both are, and Inconclusive otherwise.
- **H2 (provenance-disjoint splits are nearly unbiased).** For each of the document-disjoint and author-disjoint
  splitters:
  - Supported if the 95% upper bound of the median absolute bias is ≤ 0.12.
  - Refuted if its 95% lower bound is > 0.12.
  - Inconclusive otherwise.
  - Reported per splitter. H2 is Supported if both are, Refuted if both are, and Inconclusive otherwise.
- **H3 (the split changes which model you pick).** τ is the per-target Kendall τ between the retrospective and the
  prospective ranking of the 5 model families, averaged over targets.
  - Supported if mean τ under scaffold is ≤ 0.6, mean τ under document-disjoint is ≥ 0.8, and the paired difference
    (document − scaffold) has a 95% lower bound > 0.
  - Refuted if that difference's 95% upper bound is ≤ 0, or the document-disjoint mean τ has a 95% upper bound < 0.8.
  - Inconclusive otherwise.

## 1. Data

- **ChEMBL 33** (2023-06-09) is the frozen training universe. **ChEMBL 37** (2026-05-29) supplies prospective truth.
  Both are SQLite and checksum-verified.
- **Activities used in both releases:**
  - pChEMBL value present;
  - standard_relation '=';
  - assay type B (binding);
  - assay confidence score 9 (single protein, direct);
  - target type SINGLE PROTEIN;
  - data_validity_comment null;
  - potential_duplicate 0.
- **Keys:**
  - compound: standard InChIKey (compound_structures);
  - target: target ChEMBL ID;
  - activity: activity_id;
  - document: doc_id and its year and authors.
- **Aggregation:** the median pChEMBL per (target, compound) within each set.

## 2. Prospective sets

- **New activities:** activity_ids in ChEMBL 37 (passing the filters) that are absent from ChEMBL 33.
- **Primary (strict, temporal):**
  - new activities from documents with year ≥ 2023;
  - on compounds whose InChIKey is absent from ChEMBL 33 entirely;
  - aggregated per compound.
  - Restricting to 2023+ documents excludes backfilled older papers, which are not future chemistry.
- **Sensitivities:**
  - lenient: compounds present in ChEMBL 33 but unmeasured on that target there;
  - all-delta: new activities from documents of any year.
- **Delta audit** (G3/G4; `tools/error_audit.py`): 60 new activities sampled with seed 20261026, classified by
  inspecting their document records (no outcome used) as:
  - a publication of 2023 or later;
  - an older publication newly curated;
  - a re-deposited or corrected record;
  - other.

## 3. Targets

- **Inclusion:** at least 100 aggregated compounds in ChEMBL 33, and at least 50 compounds in the primary prospective
  set.
- **More than 250 qualifying:** a random 250 are used (seed 20261026).
- **Fewer than 60 qualifying:** the primary prospective set becomes the lenient definition (still 2023+ documents),
  declared here.
- The target list and counts are recorded before any model is trained.

## 4. Splitters (inside ChEMBL 33 only; test fraction about 20% of compounds)

1. **Random:** 5 repeats.
2. **Bemis–Murcko scaffold:** compounds grouped by scaffold; 5 group-shuffle repeats.
3. **Cluster (dissimilarity):** Butina clustering of ECFP4 at Tanimoto distance 0.65, clusters held out; 5 repeats.
4. **Document-disjoint:** each compound assigned to the earliest document measuring it on the target; documents held
   out; 5 repeats.
5. **Author-disjoint:**
   - documents linked when they share an author (normalised surname plus first initial, from docs.authors);
   - connected components held out; 5 repeats;
   - if the largest component holds more than 80% of compounds, the splitter is infeasible for that target, and this
     is counted.
6. **Assay-disjoint:** compounds assigned to the assay of their first measurement; assays held out; 5 repeats.
7. **Time split within release 33:** the latest 20% of compounds by document year (ties broken by doc_id) as test.
   Deterministic, 1 repeat.

Group splits draw groups until the test set holds 15–25% of compounds. If no draw does so in 200 tries, the repeat
is dropped and counted.

## 5. Models (fixed hyperparameters, no tuning; seed 20261026)

- **RF:** ECFP4 (2,048 bits, radius 2) + random forest regressor, 500 trees.
- **LightGBM:** on RDKit 2D descriptors, 500 trees, learning rate 0.05.
- **SVR:** with a precomputed Tanimoto kernel on ECFP4, C = 1.
- **kNN:** Tanimoto-weighted mean of the 5 nearest training compounds on ECFP4.
- **MLP:** multilayer perceptron on ECFP4, hidden layer of 512, early stopping, at most 200 epochs.

Metrics: RMSE (primary); Spearman ρ; ROC AUC with actives at pChEMBL ≥ 6.5, where both classes are present.

## 6. Secondary analyses

- Bias for all 7 splitters × 5 models, for RMSE, Spearman and AUC.
- The share of targets where each splitter's resampling interval covers the truth.
- **Stratification** of results by the prospective set's median nearest-neighbour Tanimoto similarity to the
  training set.
- **Bias corrector:**
  - predicts prospective RMSE from retrospective RMSE plus computable descriptors: the train–test nearest-neighbour
    similarity distribution, activity-cliff density, document and assay entropy, label variance and size;
  - gradient boosting, evaluated by 5-fold cross-validation over targets;
  - reports the median absolute error against a 0.10 log-unit bar, and feature importance.
- **Sensitivities:** the lenient and all-delta prospective sets.

## 7. Leakage audit (G1)

- **Prospective compounds** (strict) are absent from ChEMBL 33. Splitters and models see only ChEMBL 33.
- **Target selection** uses counts only, never performance.
- **Hyperparameters** are fixed in advance; nothing is tuned on prospective data.
- **Labels:** training labels are ChEMBL 33 values as distributed, which is what a practitioner had. Prospective
  labels come only from new ChEMBL 37 activities.
- **Document metadata** (authors, years, assays) defines splits only within ChEMBL 33.
- **Temporal backfill:** the primary set is restricted to 2023+ documents, and the delta audit measures backfill.
- No LLM or agent judges any unit. Author normalisation is a deterministic string rule.

## 8. Other gates

- **G2:** coverage at every step (`results/tables/coverage.json`): activities by filter, compounds, targets, split
  repeats, model fits.
- **G3:** `results/plausibility.md`, with three targets traced by hand.
- **G4:** the delta audit (section 2).
- **G5 and G6:** at write-up.
- **G7 does not apply:** there are no human labels.

## 9. Limits stated in advance

- **The prospective sets are not random.** New measurements follow the series chemists pursued, so they can be easier
  or harder than random future chemistry. Results are stratified by similarity.
- **Author disambiguation** from ChEMBL's author strings is crude. Document-disjoint is the main provenance split.
- **Fixed hyperparameters and five model families.** Rankings among tuned models may differ.
- **Binding assays only**, with the 2023+ document restriction.
