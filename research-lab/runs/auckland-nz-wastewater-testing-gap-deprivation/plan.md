# Preregistration: are COVID-19 cases under-counted more in deprived areas, measured against wastewater?

Lead: `auckland-nz-wastewater-testing-gap-deprivation` (research-lab/leads.json). Written 2026-10-03 and committed to
git before any analysis of the case–wastewater relationship.

## What has been seen before writing (disclosure)

- **Data structure only.** The ESR/PHF Science repository (commit 9891318, 24 Sep 2026): file structure, column
  definitions, and how many weeks each site has both reported cases and a detected wastewater result, which decides
  eligibility. No case-to-RNA ratio has been computed, plotted or tabulated, by anyone.
- **The catchment mapping and covariates** (`code/catchments.py`, `results/tables/catchments.csv`). These use only boundaries,
  populations, deprivation and age, with no outcome data:
  - 112 of 134 sites match an Urban Rural 2023 area by name, and 80 pass the ±25% population check;
  - 57 of those have at least 30 eligible weeks.
- The lead critic recorded that the scout made no prior look at outcomes.

Every later departure goes to `deviations.md` with a timestamp from `date`.

## 1. Question

Wastewater measures infection in everyone connected to the sewer, whether or not they get tested. Reported cases
count only people who tested and reported. If testing or reporting is harder in deprived areas, deprived catchments
will show fewer reported cases per unit of wastewater signal. Does this "ascertainment" fall as catchment
deprivation rises, and did the gap widen once mandatory isolation ended?

## 2. Data

- **Cases and wastewater.** ESR-NZ/covid_in_wastewater `data_historic/` (Jun 2021–Jun 2024):
  - `cases_site.csv`: `case_7d_avg`, the mean new reported cases per day in the catchment, by week ending Sunday;
  - `ww_site.csv`: `copies_per_day_per_person`, flow- and population-normalised, weekly mean;
  - `sites.csv`: population, sampler type and region.
- **NZDep2023 by SA1.** University of Otago file via the Internet Archive mirror. It provides the NZDep2023 score and
  the 2023 usually-resident population.
- **Boundaries.** Stats NZ SA1 2023 and Urban Rural 2023 boundaries from the StatsNZGeospatial open ArcGIS service
  (CC BY 4.0).
- **Age.** Census 2023 age counts by SA1, used for the share aged 65+. They come from Eagle Technology's SA1 layer of
  Stats NZ data, which agrees with the Otago file's population and NZDep scores for 99.7% of SA1s.

## 3. Sample and variables (fixed now)

**Catchments.** A site's catchment is the set of SA1s whose representative point lies in the Urban Rural 2023 area
with the same name as the site (accents and case ignored).

- It is accepted if the summed SA1 population is within ±25% of the site's population in ESR's file.
- Multi-plant metros (Auckland, Wellington, Dunedin, Nelson, Hutt Valley and others) have no exact match and are
  excluded from the primary analysis.

**Analysis period.** Weeks ending 6 Mar 2022 to 30 Jun 2024.

**Eligible site-weeks.** Both values present, and `copies_per_day_per_person` > 0. A zero is a non-detect, below the
limit of detection, and is dropped.

**Eligible sites.** Accepted catchments with at least 30 eligible weeks: 57 sites (38 autosampler, 19 grab, 15
regions).

**Outcome (ascertainment index).**

AI = log((7 × case_7d_avg + 0.5) / population × 100,000) − log(copies_per_day_per_person)

- The population is ESR's. The 0.5 handles weeks with zero cases.
- This differs from the lead, which used raw case counts. Cases are counted per person here because the wastewater
  signal is already per person.

**Deprivation.** The population-weighted mean NZDep2023 score of the catchment's SA1s, z-scored across the 57
sites, so 1 unit = 1 SD.

**Covariates:**

- sampler type: Autosampler (including "Auto/grab") or Grab;
- log ESR population;
- share aged 65+ (z-scored);
- region, as fixed effects. Regions with fewer than 3 eligible sites are pooled into one "small regions" category.

## 4. Hypotheses and primary model

**Primary model.** OLS on site-weeks:

AI ~ week fixed effects + zDep + sampler + log population + z65 + region

- Standard errors are clustered by site.
- The deprivation effect is reported as a ratio, exp(β_zDep): the multiplicative change in reported cases per unit of
  wastewater signal per 1 SD of deprivation.

**H1 (deprivation gap).**

| Verdict | Condition on the ratio per 1 SD of deprivation |
|---|---|
| Supported | ≤ 0.85, with its 95% CI excluding 1 |
| Contradicted | 95% CI lower bound > 0.85 |
| Inconclusive | otherwise |

**H2 (gap widened after isolation ended).** The same model adds zDep × post, where post = weeks ending on or after 20
Aug 2023, the first full week after mandatory isolation ended on 15 Aug 2023. The model also includes post × each
covariate.

| Verdict | Condition on the interaction (log scale) |
|---|---|
| Supported | < 0, with its 95% CI excluding 0 |
| Contradicted | 95% CI lower bound > 0 |
| Inconclusive | otherwise |

## 5. Secondary and sensitivity analyses (no verdicts)

- **Model variants:**
  - a linear mixed model with a random site intercept;
  - a negative-binomial model of weekly case counts with offset log(copies × population) and the same fixed effects.
- **Subsets:**
  - autosampler sites only;
  - leave-one-region-out (range of estimates).
- **Lag.** Wastewater lagged by one week relative to cases.
- **Variant eras,** using the dominant-lineage periods from ESR's national variant data where available. Otherwise
  calendar halves.
- **Population check.** A tighter population rule (±15%).
- **Exploratory: 2024–2026.** Ascertainment over 2024–2026 at the sites still sampled in `data/`, plotted against
  deprivation, descriptive only.

## 6. Threats (fixed now)

- **Ecological inference.** The result describes areas, not individuals.
- **Catchment approximation.** Urban-area boundaries stand in for sewersheds, which are council property and not
  public. The population check limits gross errors, but fringe SA1s may be misassigned.
- **Population mismatch.** Cases are counted where people live; wastewater reflects where people are, including
  commuters and tourists.
- **Shedding.** Viral shedding varies with age, variant and vaccination. The 65+ covariate and week fixed effects
  only partly absorb this.
- **Sample choice.** Metros are excluded, so the sample is towns and small cities. Generalising to Auckland's own
  catchments is not direct.

## 7. Framing and review

- The analysis uses only area-level deprivation. Any result is framed as a gap in health-system testing and reporting
  access, never as a property of communities.
- Findings are to be shared with Iwi-Māori Partnership Boards (e.g. Tāmaki Makaurau) and Pacific health partners
  before wider release, which the lab owner arranges.
- An independent reviewer agent checks code and results before any verdict. The report opens with "In plain terms".
