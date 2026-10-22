# Preregistration: what does Public Domain Day unlock? Renewal-based staggered DiD for US books of 1923–1930

Lead: `legal-digital-humanities-public-domain-day-renewal-did`. Written 2026-10-23, before any Open Library edition
was linked or counted.

**Examined beforehand (nothing estimated):**
- The NYPL renewal TSVs: 445,386 rows, 443,667 with an original registration number.
- The NYPL registration XML for 1923–1930: one volume per year, 8,899–14,521 A-class (book) entries per year.
- The count of A-class registrations whose number appears among renewal original-registration numbers: 1,821–2,543 a
  year for 1923–1927, 3,273 for 1928, and about 5,550 for each of 1929 and 1930.
- The Open Library dump URLs and sizes (2026-09-30 dump).
- No edition, work or Gutenberg record has been linked or counted.

**Novelty** (2026-10-23 searches: web, OpenAlex, NBER and AEA):
- **Prior work is cross-sectional:**
  - Reimers (AEJ: Microeconomics) compares editions of bestsellers published before and after 1923.
  - Heald counts Amazon editions by decade.
- **Not found:** an event study of the annual expiries since Public Domain Day 2019 that uses renewal status to form
  the control group.

## 1. Units, treatment and controls

- **Books.** A-class registrations in the Catalog of Copyright Entries, Part 1, for 1923–1930. Title, author and
  registration date come from the NYPL XML.
- **Renewed (treated).** A registration whose number matches a renewal's original registration number, where:
  - the renewal's original date is within one year of the registration date;
  - the titles match (token-set similarity at least 60).

  A renewed book entered the US public domain on 1 January of (registration year + 96): 1923 → 2019, …, 1930 → 2026.
- **Never renewed (controls).** Same-vintage registrations with no renewal. They have been in the public domain since
  the 1950s.
- **Linking to Open Library works:**
  - **Blocking:** normalised author surname plus the first title token.
  - **Match rule:** title token-set similarity at least 90, and the author surname present in the work's author names
    (from the authors dump; else the edition's "by" statement).
  - **Date check:** the work's first publish year is missing or no later than registration year + 1.
  - **Uniqueness:** a registration with two equally good work matches is dropped.
  - **Validation:** 300 registrations, stratified by renewal status, are labelled by the study's AI agent from the
    records alone. Match precision and recall are reported.
- **Outcome.** New editions per work per calendar year: Open Library editions linked to the work, by the year of their
  publish date, for 2008–2025. 2026 is partial in the dump and is excluded.

## 2. Estimation

- **Model.** Poisson pseudo-maximum likelihood with work and calendar-year fixed effects. Cohort × event-time
  interactions are saturated in the Sun–Abraham form. Treated cohorts are 1923–1929 (public domain 2019–2025).
- **Controls.** Never-renewed works of 1923–1930, plus renewed 1930 works, which are not yet treated anywhere in the
  outcome window.
- **Event times** run from −8 to +6 and are binned at the ends. The reference is event time −1.
- **Inference.** Standard errors clustered by work.
- **Primary estimand.** The cohort-size-weighted average of the event-time 0, +1 and +2 coefficients, reported as a rate
  ratio, RR = exp(average).
  - **H1 (expiry raises new editions by at least 50%).**
    - **Supported** if RR ≥ 1.5 and its 95% interval excludes 1.
    - **Refuted** if the interval's upper bound is below 1.2.
    - **Inconclusive** otherwise.
  - **The pre-trend condition.** The event-time −5 to −2 coefficients must be jointly insignificant (Wald p > 0.1). If
    they are not, H1 is reported as Inconclusive (pre-trend), whatever RR is.

## 3. Secondary analyses (reported, not confirmatory)

1. **Event-study path** by event time, and RR by cohort.
2. **Sun–Abraham OLS on log(1 + editions),** as a functional-form check.
3. **Excluding print-on-demand.** Editions whose publisher matches a fixed list are dropped: CreateSpace, Independently
   Published, Lulu, Kessinger, Forgotten Books, Hansebooks, Alpha Editions, Creative Media Partners, Legare Street,
   Wentworth, Gale ECCO, General Books, Nabu.
4. **Ingestion lag.** Only editions whose Open Library record was created at least 12 months after the start of their
   publish year.
5. **Placebo expiry.** Every treated cohort's expiry is shifted 3 years earlier, using pre-expiry years only.
6. **Project Gutenberg.** The share of linked works released on Gutenberg (title and author match) within 0–2 years of
   the expiry, for renewed works against same-vintage never-renewed works over the same calendar years.
7. **HathiTrust full view.** The share of matched volumes with rights code `pd` for renewed works, by years since expiry.

## 4. Limits stated in advance

- Linkage errors attenuate effects; the validation sample sizes the risk.
- Open Library's coverage of new editions depends on its ISBN feeds, and recent years may be under-ingested. The
  1928–1929 cohorts have short post-periods.
- Renewal is not random. Renewed books were the ones worth renewing, which is why the design compares changes in the
  same works over time.
- Edition counts measure supply in the catalogue, not readership.

## 5. Outputs

- `results/tables/`: `registrations.parquet` (registration, renewal flag, linked work), `linkage_validation.csv`,
  `panel` summary, `primary.json`, `event_study.csv`.
- `results/figures/`.
- `deviations.md` records changes before the results they affect.
