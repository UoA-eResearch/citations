# Plan (preregistration): can first appearances of AMR genes in new bacterial species be forecast better than sampling effort alone predicts?

Lead: `bioinformatics-amr-gene-species-emergence-forecast`. Written before any Pathogen Detection data were
downloaded.

**Seen before this plan:**
- **The lead's text.**
- **The NCBI Pathogen Detection FTP layout:** per organism group, a `latest_snps/Metadata/*.metadata.tsv`.
- **That file's column names** (one header line, E. coli group): collection_date, scientific_name, species_taxid,
  geo_loc_name, bioproject_acc, AMR_genotypes, AMR_genotypes_core, amrfinder_version, refgene_db_version and others.
- No row of data.

## 0. Hypotheses

**Units.**
- A *gene* is an AMRFinderPlus element symbol in `AMR_genotypes_core` (acquired and point-mutation calls). Point
  mutations are excluded, because they are species-specific by construction.
- A *species* is `scientific_name`, reduced to genus plus species.
- A *pair* (gene, species) **emerges** in a period if it is first observed then. Primary rule: in at least two
  isolates from different BioProjects. Isolates are dated by `collection_date`.

**Periods.**
- Training: collected through 2021.
- Validation (model choice only): 2022.
- Test: 2023–2025.

**Candidates.** Every pair (gene, species) not observed through 2022, where:
- the gene was observed in at least one species by 2022; and
- the species had at least 20 isolates by 2022.

**Forecasts.** Each method ranks all candidates by their chance of emerging in 2023–2025.
- **Null (sampling effort):** the chance that a gene carried at its pre-2023 overall frequency would turn up at least
  twice among the species' test-period isolates: 1 − Binomial(≤1; n_s,test, f_g). Here n_s,test is the realised
  number of the species' 2023–2025 isolates, given to the null and to the model alike, and f_g is the gene's share of
  all isolates through 2022.
- **Model:** gradient-boosted trees (scikit-learn HistGradientBoosting) trained on the same task one period earlier.
  Candidates are pairs not seen through 2019, labels are emergence in 2020–2022, and hyperparameters are chosen on
  that split's 2022 slice. Features:
  - effort: log n_s for the forecast period, log n_s before it, and the null's own probability;
  - co-occurrence: the gene's number of host species, the species' number of genes, the gene's frequency, and its
    frequency growth over the last three years;
  - taxonomy: whether the gene is already in the species' genus and in its family, with counts (NCBI taxonomy);
  - genes the species already carries that co-occur with this gene elsewhere (a Jaccard-style score);
  - protein embedding: the cosine similarity of the gene's ESM-2 (650M) mean embedding to the nearest gene the species
    already carries.

**Primary metric:** precision@100, the share of the top 100 ranked candidates that emerge in 2023–2025.

- **H1:** the model's precision@100 is at least twice the null's, and the 95% interval of the ratio excludes 1.
  - The interval comes from a bootstrap over genes: candidate pairs are resampled by gene, 2,000 times, seed
    20261028.
  - **Supported** if ratio ≥ 2 and the lower bound > 1. **Refuted** if the upper bound < 2. Otherwise
    **Inconclusive**.
- **H2:** the protein-embedding feature adds signal beyond co-occurrence and taxonomy. The model without it (same
  training) has lower average precision (AUPRC) on the test candidates, by a paired gene-bootstrap 95% interval that
  excludes 0.
  - **Supported** if the interval of AUPRC(full) − AUPRC(without embedding) lies above 0. **Refuted** if it lies
    below 0, or within ±0.005 of it. Otherwise **Inconclusive**.

## 1. Data

- **Metadata.** `latest_snps/Metadata/*.metadata.tsv` for every bacterial organism group on the Pathogen Detection
  FTP. Each file's PDG version is recorded, and all are downloaded in one session.
- **Genotypes.** `AMR_genotypes_core` symbols, with the AMRFinderPlus and reference-database versions recorded. Point
  mutations (symbols with an underscore and an amino-acid change, AMRFinderPlus's POINT convention) are dropped.
- **Gene products.** Protein sequences for the symbols, from the AMRFinderPlus Reference Gene Catalog (version fixed
  at download). Embeddings: ESM-2 t33 650M, mean over residues, computed once.
- **Taxonomy.** NCBI taxdump (fixed date) gives genus and family for each species_taxid.
- **Isolates.**
  - Kept if collection_date parses to a year from 1990 to 2025.
  - Clinical and non-clinical isolates are pooled.
  - Isolates whose scientific_name is not resolved to species are dropped and counted (G2).

## 2. Secondary analyses (reported, not confirmatory)

- **Outcome variants:** at least one isolate instead of two BioProjects; at least three.
- **Gene × country** first appearances, the same comparison.
- **Precision@k** for k = 50, 500; AUPRC; recall of the null and model at matched list sizes.
- **Ablations:** without taxonomy, without co-occurrence, effort alone (a model that sees only the effort features).
- **Literature check.** The model's top 20 test-period hits, checked against Europe PMC for prior reports before
  2023. A hit already reported before 2023 counts as foreseeable from the literature.
- **Calibration:** the predicted against the observed share of emerging pairs, by decile.

## 3. Leakage audit (G1)

- No 2023–2025 record enters training or model choice.
- The test-period effort n_s,test is a declared input to both the null and the model, not a leak. The question is
  what beyond effort is predictable.
- Genes and species introduced after 2022 cannot be candidates.
- The reference catalog and AMRFinderPlus version are fixed. Calls are NCBI's uniform reanalysis, so a catalog
  update cannot create a "new" pair in only one period.
- Duplicate submissions of the same isolate (same biosample) are counted once.
- No LLM or agent labels any unit, except the literature check, which is descriptive and done by keyword search.

## 4. Other gates

- **G2:** `results/tables/coverage.json`, covering:
  - isolates read and kept, and why the rest drop;
  - genes with a protein sequence;
  - species resolved;
  - candidate pairs.
- **G3:** `results/plausibility.md`: the base rate of emergence; three emerging pairs traced to their first isolates;
  the null's calibration.
- **G4:** a check of 30 random first-observation dates and BioProjects, recomputed from the raw metadata by an
  independent script.
- **G5 and G6:** at write-up.
- **G7:** does not apply.

## 5. Limits stated in advance

- **Observation is not emergence.** A first observation in the database is when a pair was first sequenced and
  submitted, which mixes biology with surveillance. The effort null addresses this only in part.
- **Pathogen Detection covers chosen pathogens** (mainly foodborne and clinical), so species outside it are absent.
- **The model differs from the lead's.** It is gradient-boosted trees over engineered features, not a temporal graph
  neural network, chosen for auditability on CPU. A negative result is about these features, not every model.
- **Collection dates are partly missing or coarse** (year only). Year resolution is used throughout.
