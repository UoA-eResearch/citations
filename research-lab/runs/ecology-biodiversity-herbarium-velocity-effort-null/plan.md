# Plan (preregistration): do global herbarium-based plant range velocities survive a sampling-noise and collecting-effort null?

Lead: `ecology-biodiversity-herbarium-velocity-effort-null`. Written before any centroid, displacement, per-species
count or per-period count was computed.

**Seen before this plan:**
- Daru, Birkeland & Chala (bioRxiv 10.64898/2025.12.26.696646, December 2025): abstract and full text. Their
  historical baseline uses 16,219,436 herbarium records of 109,242 species in two periods, 1970–2000 (median 1983)
  and 2001–2024 (median 2010).
  - They report 28-year centroid velocities with a median of 5.6 km/yr (95% CI 5.5–5.6).
  - Records are thinned at 5 arcmin and restricted to native regions. No minimum record count is stated, and no
    code is released.
  - Their SDMs are used for future projections; the text describes the historical shifts as computed from the
    herbarium records.
- The GBIF snapshot schema (2026-07-01), and the first three filtered rows of one file, from testing the extractor.
- `code/s3_extract.py` was started at 06:36 on 2026-10-26. It filters only and computes nothing else.

## 0. Question and hypothesis

Centroid displacement is always positive, so finite samples inflate it. Collecting effort also moved between the two
periods. How much of the reported velocity would appear if every species' range had stayed fixed?

- **H1 (primary).** A null that keeps each species' range fixed reproduces at least half of the observed median
  velocity.
  - The null permutes records between periods, preserving per-period counts, and reweights them by each period's
    collecting-effort surface (section 3).
  - Statistic: ratio = (median over species of each species' null median velocity) / (median over species of the
    observed velocity). The 95% CI comes from a species bootstrap (2,000 resamples).
  - **Supported** if the lower bound is at least 0.5.
  - **Refuted** if the upper bound is below 0.5.
  - **Inconclusive** otherwise.

## 1. Data and cleaning

- **Records.** GBIF snapshot 2026-07-01 (AWS Open Data; doi:10.15468/dl.teccpa): phylum Tracheophyta, basis of record
  PRESERVED_SPECIMEN, years 1970–2024, both coordinates present. The species unit is the GBIF `specieskey`.
- **Cleaning,** in order, each rule counted with tools/coverage.py:
  1. Drop records with GBIF issues ZERO_COORDINATE, COORDINATE_INVALID, COORDINATE_OUT_OF_RANGE or
     COUNTRY_COORDINATE_MISMATCH.
  2. Drop records with coordinate uncertainty above 10 km. Missing uncertainty is kept.
  3. Drop records with latitude equal to longitude, or within 0.5° of (0, 0).
  4. Drop records whose establishment means is introduced, naturalised, invasive or managed (case-insensitive),
     and records with occurrence status ABSENT.
  5. **High-density points** (a proxy for CoordinateCleaner's centroid, capital and institution tests): drop any
     exact coordinate pair (rounded to 1e-4°) carrying more than 1,000 distinct species across 1970–2024.
  6. **Sea points:** drop records whose 5-arcmin cell does not intersect Natural Earth 10 m land or minor islands.
  7. Drop records without a species key.
- **Periods:** P1 = 1970–2000, P2 = 2001–2024.
- **Thinning:** unique 5-arcmin cells, (floor(12·lat), floor(12·lon)), per species per period. Each thinned point is
  its cell centre.

## 2. Observed velocities

- **Centroid** per species per period: the normalised spherical mean of the thinned cell-centre unit vectors.
- **Displacement:** the great-circle distance between the P1 and P2 centroids (R = 6,371.0088 km).
- **Velocity** = displacement / 28 years, Daru et al.'s divisor. The two periods' median years differ by 27; the
  ratio statistic is unaffected by the divisor.
- **Bearing:** initial great-circle bearing. **Poleward displacement:** the change in absolute centroid latitude,
  in km.
- **Population (primary):** species with at least 10 thinned cells in each period.
- **Reproduction check,** reported but not part of H1: the median velocity and species count at thresholds of 1, 3,
  5, 10, 20 and 50 cells per period, against Daru et al.'s 5.6 km/yr and 109,242 species.

## 3. Nulls

Each species' pooled records (both periods, after cleaning) are kept with their 5-arcmin cells. A replicate assigns
n1 of them to P1 and n2 to P2, where n1 and n2 are the observed record counts. It then thins per period and computes
the velocity exactly as in section 2. Each null runs 999 replicates per species, seeded by species key.

- **(a) Noise only (secondary):** a uniformly random assignment.
- **(b) Noise plus effort (primary).**
  - Effort E_p(c) is the number of thinned species × 5-arcmin units of all tracheophytes in period p within the
    1° cell c.
  - **Leave-one-species-out:** the focal species' own units are subtracted, so its own shift cannot enter its weights
    (G1).
  - Each record gets the weight w1 = s1 / (s1 + s2), where s_p = E_p(c) / Σ_c E_p(c) is the share of period p's
    effort in its 1° cell.
  - P1's n1 records are drawn without replacement with probability proportional to w1, using exponential keys. The
    rest go to P2.
  - Cells with no effort in either period (after leave-one-out) get w1 = n1 / (n1 + n2).
- **Per species,** store the null median, 5th and 95th percentiles of velocity, and the median poleward displacement.

## 4. Secondary analyses

- **The noise-only ratio** (null a).
- **Exceedance:** the share of species whose observed velocity exceeds their own null 95th percentile (5% expected
  if ranges were fixed).
- **Excess velocity:** the median of (observed − null median) per species, in km/yr.
- **Direction:** the share of species with positive poleward displacement, observed against null.
- **Splits** of the ratio and exceedance:
  - by latitude band of the pooled centroid (|lat| < 23.5°, 23.5–50°, > 50°);
  - by thinned cells per period (10–19, 20–49, ≥ 50, using the smaller period).
- **Robustness of H1's ratio:**
  - thresholds of 20 and 50 cells;
  - 30-arcmin thinning;
  - effort grids of 30 arcmin and 2°;
  - arithmetic-mean centroids;
  - cleaning without rule 5.
- **SDM-centroid variant** (the critic's request), on a random 1,000 species (seed 20261026) from the primary
  population:
  - Fit a MaxEnt-type presence-background model per period, using elapid with default features and WorldClim 2.1
    bioclim at 10 arcmin.
  - Background: 10,000 points sampled in proportion to that period's effort, within 1,000 km of any of the species'
    pooled records.
  - Threshold at the 5th percentile of training suitability. Take the binary range's spherical-mean centroid
    (cell-area weighted).
  - Fit once on the observed records and once on one noise-plus-effort null replicate. Report the median velocity of
    each and their ratio.
  - If elapid cannot be installed or fails, record that as a deviation and drop the variant.

## 5. Leakage audit (G1)

Fields that correlate with the period label, and how the nulls stay blind to them:
- **The focal species' own records in the effort surface** would encode its shift into its weights. They are
  removed by leave-one-species-out effort.
- **Record counts per period** are preserved by design, so a null cannot gain or lose sampling depth.
- **Thinning after assignment:** null replicates are thinned exactly as the observed data are, so duplicate
  specimens cannot behave differently in the null.
- **Dataset and institution identity** (for example, recent digitisation projects) correlate with period. They are
  part of "effort" and are captured only through the 1° effort surface, not used per species.
- No LLM or agent judges any unit, so no order-swap probe is needed.

## 6. Other gates

- **G2:** coverage for every cleaning rule, threshold and null replicate (`results/tables/coverage.json`).
- **G3:** `results/plausibility.md`, with three species traced by hand.
- **G5 and G6** at write-up.
- **G4 and G7 do not apply:** there is no classifier or labelling. The reproduction check compares a summary
  statistic with a published one.

## 7. Limits stated in advance

- **Not Daru et al.'s exact data.** Their names are reconciled to WCVP and restricted to native TDWG regions; this
  study uses GBIF species keys and GBIF's establishment field. The snapshot also includes specimens digitised since
  their download. The observed-versus-null comparison runs on the same records, so it does not depend on matching
  their median.
- **The effort null assumes** that, within a 1° cell, effort is independent of species identity. Targeted
  collecting of particular taxa breaks that.
- **The nulls test for range shift beyond what fixed ranges plus noise and effort would produce.** They do not show
  that any particular species has or has not moved.
- **The SDM variant** uses fixed, simple settings. It is not Daru et al.'s MaxEnt pipeline.
