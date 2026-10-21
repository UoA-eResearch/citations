# Preregistration: did the 2023 INSDC rule put countries of origin on sequence samples, and can the missing ones be recovered?

Lead: `ancestral-dsi-origin-recoverability` (Ancestral Futures). Written 2026-10-22, before the BioSample archive was
parsed and before any outcome was computed.

**Examined beforehand (nothing computed):** the INSDC and DDBJ announcements of the spatiotemporal metadata rule (May
2023) and its sequence-side extension (December 2024). These announcements matter for the design: where a country
cannot be given, the rule asks for one of the INSDC missing-value terms ("missing", "not collected", "not
applicable", "restricted access", "missing: lab stock", "missing: third party data" and the like) instead of a
blank. The NCBI BioSample dump's size and date (19 October 2026, 4.95 GB compressed).

**Novelty** (searches 2026-10-22, web and OpenAlex). The CBD's DSI traceability study reports that 16% of GenBank
entries carry a country of origin and that 44% of checked untagged entries state it in the linked publication; a 2026
Scientific Data paper notes variability across databases. No record-level test of the 2023 rule on the full
BioSample archive, separation of placeholders from absence, or precision-validated recovery at archive scale was
found.

**Care.** Samples whose organism is *Homo sapiens*, or that are human-derived (human metagenome taxa; packages or
organism names marked human), are removed at the first filter, so no human genomic data, Indigenous or otherwise, is
analysed. The study measures metadata. It makes no claim about any country's or community's entitlement under the
CBD, the Nagoya Protocol or the Cali Fund.

## 1. Classification of the country field

The BioSample attribute `geo_loc_name` (formerly `country`); where both appear, `geo_loc_name` wins. The text before
the first colon is the country part. Each sample is classified:

- **usable**: the country part resolves to a country or territory in the INSDC country list (exact,
  case-insensitive, with a fixed list of common variants such as "United States"/"USA");
- **placeholder**: the whole value matches the placeholder lexicon. This is the INSDC missing-value terms with
  their qualifiers, plus "unknown", "na", "n/a", "none", "null", "-", "?", "not determined", "not known",
  "not available", "unspecified" and "other", case-insensitive, punctuation-normalised;
- **malformed**: present but neither of the above;
- **absent**: no country attribute.

## 2. Limb 1: the discontinuity

- **Population.** Non-human BioSamples (per the care filter), keyed by `submission_date`.
- **Cutoff.** 1 June 2023, when the rule took effect. Window: 24 months either side (1 June 2021 to 31 May 2025).
  The month before and after the cutoff is a donut, excluded.
- **Estimate.** The jump in the usable share at the cutoff, from a local-linear regression in time on daily shares
  (sample-weighted, triangular kernel over the window, separate slopes either side).
- **Intervals.** A cluster bootstrap over submitting organisations (BioSample `Owner` name), 1,000 resamples,
  seed 20261022. Submissions arrive in batches, so samples are not independent.

**H1 (the rule did little for usable countries):** the jump in the usable share is **under 10 percentage points**.
- *Supported* if the interval's upper bound is below 10 pp.
- *Refuted* if its lower bound is at or above 10 pp.
- *Inconclusive* otherwise.

**Secondary for limb 1:**
- the same jump for placeholder, malformed and absent shares (does the rule produce placeholders rather than
  countries?);
- the second cutoff, 1 January 2025 (sequence-side extension), and placebo cutoffs on 1 June 2021 and 1 June 2022,
  each with the same specification;
- package fixed effects;
- bandwidths of 12 and 36 months;
- no donut;
- shares by year for the CBD/Nagoya/income decomposition below.

## 3. Limb 2: recovery

- **The gold set.** 500 untagged samples (placeholder, malformed or absent), submitted from 1 June 2023 to 31 May
  2025. Drawn by stratified random sampling, seed 20261022: half from samples whose BioProject links a publication
  and half from the rest, with proportional allocation by package within each half.
- **Gold label.** The country where the sample was collected, determined from the linked publication (methods,
  sampling site), the BioProject title and description, and the sample's own attributes, in that order of
  authority. The submitter's institution is **not** evidence of origin. A sample whose origin cannot be determined is
  labelled "not determinable".
- **Adjudication.** The lab has no human adjudicators. Labels come from two passes by the study's AI agent, made
  hours apart, with the records reshuffled and without access to the first pass or to any arm's output. Agreement
  (Cohen's κ) is reported before any arm is scored. Disagreements are settled by a third pass under a fixed rule: an
  explicit sampling-site statement outranks everything else, and otherwise "not determinable". This is a real
  limitation and is stated with the results.
- **Split.** The gold set is split at random into **200 tuning** and **300 test** records.

**Recovery arms**, each emitting a country or "none", and a confidence:
1. **Gazetteer**: country and place names (GeoNames, population ≥ 15,000, plus country names and demonyms) found in
   the evidence text, weighted by source (publication methods > BioProject description > sample attributes);
   submitter affiliation excluded.
2. **Weakly supervised classifier**: logistic regression on TF-IDF features of the same evidence text, trained on
   tagged (usable) samples from the same period and their countries.
3. **Open-weight LLM**: the model served locally (Nemotron 3 Nano Omni), asked to name the collection country
   from the evidence or answer "unknown", with a fixed prompt. Its confidence is its stated probability.

Each arm's confidence threshold is chosen on the tuning split as the lowest that gives at least 90% precision there.

**H2 (most missing origins can be recovered automatically):** on the test split, at least one arm recovers a correct
country for **at least 40%** of the 300 records at **at least 90% precision**. Precision counts a prediction on a
"not determinable" record as wrong.
- *Supported* if the best arm's recovery is at least 40% and its precision at least 90%, with the Wilson lower
  bound of precision at least 85%.
- *Refuted* if no arm's recovery upper bound reaches 40% at its tuned threshold.
- *Inconclusive* otherwise.

**Secondary for limb 2:**
- **Asymmetric error**: the share of each arm's errors that name the submitter's country when the gold country
  differs, which is the error that would move origin away from provider countries;
- the archive-wide recoverable volume, projected with the gold set's sampling uncertainty;
- per-arm calibration.

## 4. Decomposition

Both limbs are broken down by the resolved country's CBD Party and Nagoya Party status and World Bank income
group, using the gold country for limb 2 and the usable country for limb 1. This shows where the traceability
deficit falls. The decomposition is descriptive.

## 5. Threats and care

- **Country is sometimes legitimately inapplicable** (synthetic constructs, lab stocks, model organisms, cell
  lines). The rule's own missing-value terms cover these. Results are also reported with those terms removed from
  the denominator.
- **Submission date is not collection date**, and batches arrive at once; hence the clustered intervals and the
  donut.
- **Mirror agreement.** A random 10,000 accessions are cross-checked against the ENA portal.
- **AI adjudication** is not human expert adjudication (§3).
- Any departure from this plan will be logged in `deviations.md` before the affected result is read.
