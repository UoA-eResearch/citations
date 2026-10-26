# Plan (preregistration): how much single-cell disease signal survives matched healthy-vs-healthy nulls?

Lead: `bioinformatics-sc-disease-de-negative-control`. Written before any expression value was read.

**Seen before this plan:**
- **Census metadata only** (CZ CELLxGENE Census LTS 2025-11-08, `code/meta.py`): cell counts by dataset, donor,
  disease, tissue, cell type, assay, suspension, sex, development stage and primary flag. From these, the counts of
  feasible contrasts below.
- **Abstracts:**
  - Squair et al. 2021 (Nature Communications, doi:10.1038/s41467-021-25960-2): pseudobulk methods control false
    discoveries that cell-level tests do not.
  - Nakatsuka et al. 2025 (Nature Communications, doi:10.1038/s41467-025-62579-z): disease DEGs from single
    neurodegeneration and COVID-19 datasets replicate poorly across datasets; a rank-based meta-analysis helps.
  - Dann et al. 2023 (Nature Genetics, doi:10.1038/s41588-023-01523-7): matched controls reduce false discoveries
    of disease cell states.
- None builds matched healthy-vs-healthy negative-control contrasts across an atlas. No expression matrix, no DE
  result and no gene list from these data has been seen.

## 0. Hypotheses

**Unit: a contrast.** A contrast is one (dataset, tissue_general, cell type, disease) combination, comparing the
disease donors with the dataset's normal donors in that tissue and cell type.

**Signal statistic: π1** (the estimated share of genes with any differential expression) = 1 − π0. π0 is Storey's
estimate at λ = 0.5 from the pipeline's p-values (section 4), truncated to [0, 1].

**Matched comparison.**
- m = min(n_disease, ⌊n_normal / 2⌋) donors per group.
- **Real:** R = 25 subsamples of m disease vs m normal donors; T_real is the median π1 over them.
- **Null:** B = 500 draws of two disjoint sets of m normal donors from the same dataset, tissue and cell type.
  - The pseudo-disease set is matched to a real subsample's disease group on sex and age bin; the pseudo-control set
    to its normal group (section 3).
  - Null draws cycle through the 25 real subsamples' compositions (draw b uses subsample b mod 25).
- **Empirical p:** p = (1 + #{b : π1_b ≥ T_real}) / (B + 1). BH across all primary contrasts.
- **A contrast is distinguishable** from its null if BH q < 0.05, and **indistinguishable** otherwise.

- **H1 (the lead's claim).** More than half of the primary contrasts are indistinguishable from their matched
  healthy-vs-healthy null. S1 is the share indistinguishable; its 95% interval comes from a cluster bootstrap over
  datasets (2,000 resamples, seed 20261027).
  - Supported if the interval's lower bound is > 0.50.
  - Refuted if its upper bound is < 0.50.
  - Inconclusive otherwise.
- **H2 (replication follows donors, not cells).** A pair is two primary-or-replication contrasts (section 2) for the
  same disease, tissue_general and cell type, from datasets in different Census collections.
  - **Replication** is the Spearman correlation of the two full-size contrasts' moderated t statistics over the genes
    tested in both.
  - **Regression:** ρ on three standardised predictors and an indicator:
    - log2 of the smaller donor count, d (the minimum over the four groups in the two contrasts);
    - log2 of the smaller median cells per donor, c (the minimum over the two contrasts);
    - the larger absolute sex imbalance (|share male, disease − share male, normal|);
    - whether the two assays are the same.
  - Intervals come from a cluster bootstrap over disease × tissue_general × cell type groups (2,000 resamples).
  - **Supported** if β_d's interval lies above 0, and the paired difference β_d − β_c has an interval above 0.
  - **Refuted** if β_c ≥ β_d with the difference's interval below 0, or β_d's interval lies below 0.
  - **Inconclusive** otherwise.
  - **Known limit:** the pairs span few diseases (about 10 at the replication thresholds in the metadata). The
    disease-cluster bootstrap is reported as a sensitivity.

## 1. Data

- **CZ CELLxGENE Census LTS 2025-11-08**, Homo sapiens, `X["raw"]` integer counts, through `cellxgene_census` 1.18.0
  and `tiledbsoma` 2.3.0.
  - Cells with `is_primary_data` True only.
  - Census genes as distributed (all features).
- **Donors.** A donor is (dataset_id, donor_id).
  - Donors carrying more than one disease label in a dataset are excluded from that dataset (253 of 14,107 in the
    metadata), which also removes tumour-plus-adjacent-normal designs.
  - Sex comes from `sex`. Age in years is parsed from `development_stage` by a deterministic rule; every distinct
    string and its parsed value is listed in `results/tables/age_map.csv` (G4).
- **Pseudobulk:** the sum of raw counts per (dataset, tissue_general, cell type, donor), with at least 10 cells.
- **Open Targets Platform** (latest release at download, recorded) overall direct association scores, for the
  enrichment secondary. Census MONDO terms are matched to Open Targets disease IDs exactly. Composite labels (with
  "||") are skipped for enrichment.

## 2. Contrasts

- **Primary:** n_disease ≥ 8 and n_normal ≥ 16 eligible donors. In the metadata: 869 contrasts, 33 datasets, 47
  disease labels. All are used.
- **Replication contrasts (H2 only):** n_disease ≥ 4 and n_normal ≥ 4. A contrast is kept only if it has a partner
  from another collection. In the metadata: 359 pairs, 112 groups.
- Disease labels are used as Census gives them, including composite labels. Cell types are the Census Cell Ontology
  terms, without roll-up.

## 3. Draws and matching

- **Age bins:** < 40, 40–59, 60–74, ≥ 75, unknown.
- **Real subsamples:** m disease donors uniformly from the disease group; m normal donors uniformly from the normal
  group.
- **Null draws:**
  - The pseudo-disease set P is drawn from the normal donors to reproduce the disease subsample's counts by
    (sex, age bin).
  - The pseudo-control set Q is drawn from the remaining normal donors to reproduce the normal subsample's counts.
  - When a stratum is short, the draw fills from the same sex in the nearest age bin, then from any donor. Every
    fallback is counted (G2).
- **Seeds:** NumPy default_rng([20261027, contrast index, draw index]).

## 4. DE pipeline (identical for real, null and full-size contrasts)

Bioconductor 3.22 in Docker (`bioconductor/bioconductor_docker:RELEASE_3_22`; edgeR and limma as shipped):
- `filterByExpr(group)`, TMM `calcNormFactors`, `voom`, `lmFit` and `eBayes` (default robust = FALSE);
- design ~ group + sex. Sex is dropped when it is constant across the contrast's donors.

The coefficient is group. P-values go to π1; the moderated t goes to replication. Fits that error are counted and
excluded (G2). A contrast with more than 10% failed null fits is reported as not evaluable.

## 5. Secondary analyses

- **The same exceedance test with other statistics:**
  - the number of genes at BH FDR < 0.05;
  - the mean |logFC| of the 100 genes with the smallest p;
  - **Disease-gene enrichment:** the mean Open Targets overall direct score of the 100 smallest-p genes, against
    the same statistic on null draws. This is for contrasts with a matched single disease ID.
- **Attribution (exploratory):** the standardised excess (T_real − null median) / null IQR, regressed on log2 m,
  log2 median cells per donor, sex and age-bin imbalance, assay and suspension type.
- **Equal weight per disease:** S1 with each disease label weighted equally, since COVID-19 contributes many
  contrasts.
- **Replication over a null baseline:** where both datasets of a pair have null draws, the Spearman correlation
  between null signatures of the two datasets (shared confounding), against the real ρ.
- **Full-size contrasts:** π1 and the number of DE genes at full n, as a practitioner would run them.

## 6. Leakage audit (G1)

- Contrasts, thresholds, m, R, B, the statistic, the pipeline and the bands are fixed here, from metadata counts
  only.
- Null draws use only normal donors from the same dataset, tissue and cell type, and never see disease labels except
  to copy composition.
- Nothing is tuned on any result. The pipeline has no free parameters beyond edgeR/limma defaults.
- Open Targets scores are an external reference built independently of these datasets. Some Open Targets evidence
  may come from the same studies (expression-atlas evidence), and this is stated as a limit.
- No LLM or agent labels any unit.

## 7. Other gates

- **G2:** `results/tables/coverage.json`, covering:
  - cells streamed per dataset against the metadata count;
  - donors kept or dropped, with reasons;
  - pseudobulk groups;
  - contrasts evaluable;
  - fits failed;
  - matching fallbacks.
- **G3:** `results/plausibility.md`:
  - a positive control: male vs female normal donors in the largest primary dataset, through the same exceedance
    test, which must be distinguishable;
  - a synthetic power check: a twofold change injected into 5% of genes in one pseudo-group of a null draw, which must
    exceed the null;
  - three contrasts traced by hand from cell counts to π1.
- **G4:** the age-string map (every distinct string) and the donor-exclusion list.
- **G5 and G6:** at write-up.
- **G7:** does not apply (no human labels).

## 8. Limits stated in advance

- **Exceeding the null is necessary, not sufficient, for disease biology.** Disease donors processed in their own
  batch would exceed a null drawn from normal donors. A within-dataset null cannot remove that confound.
- **Matching on sex and age bin only.** Other donor covariates (ancestry, BMI, post-mortem interval, sampling site)
  are not matched.
- **Census annotations as given.** Cell-type labels differ in granularity across datasets, and composite disease
  labels are kept.
- **H2 is observational** and spans few diseases.
- **Out of scope:** the bulk recount3 cross-check proposed in the lead is not run; it is out of this study's scope.
