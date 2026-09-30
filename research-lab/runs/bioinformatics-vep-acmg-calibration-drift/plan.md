# Preregistration: do the ClinGen PP3/BP4 score thresholds still hold on variants classified after they were set?

Lead: `bioinformatics-vep-acmg-calibration-drift` (research-lab/leads.json). Written 2026-10-01 ~00:25 NZST and
committed to git before any outcome data were examined. Nothing had been joined between predictor scores and
ClinVar labels at that point. Probes made before writing:

- the ClinVar FTP archive listing;
- one MyVariant.info query (BRAF p.V600E) to confirm field names;
- the header and first row of the ClinGen Evidence Repository export;
- the text of the two calibration papers.

Every later departure goes to `deviations.md` with a timestamp.

## 1. Background and gap

ClinGen's Sequence Variant Interpretation group calibrated missense predictors against ACMG/AMP evidence strengths.
Pejaver et al. 2022 (AJHG) did REVEL, BayesDel, CADD, MutPred2, VEST4 and others; Bergquist et al. 2025 (Genet Med)
added AlphaMissense, ESM1b and VARITY_R.

- **Calibration data.** A December-2019 ClinVar set: missense, ≥1 star, not conflicting, gnomAD AF < 0.01, tools'
  training variants removed; 11,834 variants in 1,914 genes.
- **Method.** Local posterior probability with a prior of 0.0441. Evidence strength follows likelihood-ratio (LR)
  targets on the points scale: LR = c^k for k points, c = 2.406. That gives Supporting 2.406, Moderate 5.79, (+3)
  13.93, Strong 33.5. Benign targets are the reciprocals.
- **Validation.** The only temporal check so far is one year of later data: variants new in the December-2020 release
  (9,114). On it every interval met its target.

Since the recommendations were published (bioRxiv March 2022; AJHG December 2022; Bergquist bioRxiv September 2024,
journal 2025), clinical laboratories have applied these thresholds as PP3/BP4 evidence. Two things follow:

- the thresholds have never been checked on the 2021–2026 classifications;
- later ClinVar labels may partly *reflect* the tools, which inflates any apparent validation. Shang, Badonyi &
  Marsh (bioRxiv 2026.03.27) call this circularity "an increasing concern" that they could not quantify.

## 2. Hypotheses

- **H1, prospective calibration (primary).** For each tool and each published interval, the realised interval LR
  among variants first confidently classified after December 2020 meets that interval's nominal LR target. The
  lead's prior expectation is that some intervals fall short, most likely in single-submitter classifications.
- **H2, feedback over time.** For the highest-evidence intervals, realised LRs among newly classified variants rise
  after the thresholds became available to laboratories. That is the signature of labels increasingly set by the
  tools.
  - Highest-evidence intervals: pathogenic +3 and +4 together ("≥ +3"); benign −3 and −4 together ("≤ −3").
  - Pre/post windows:

    | Tool | Pre-publication cohorts | Post-publication cohorts |
    |---|---|---|
    | REVEL | 2021–2022 | 2024–2026 |
    | AlphaMissense | 2021–2023 | 2025–2026 |
- **H3, direct circularity (ClinGen expert panels, VCEPs).** Among VCEP classifications, the fraction whose P/LP or
  B/LB category depends on the PP3/BP4 points rises over the approval years. Realised LRs computed on
  tool-independent VCEP labels are lower than on all VCEP labels.
- **H4, heterogeneity.** The ratio of realised to nominal LR is lower for 1-star (single-submitter) classifications
  than for ≥2-star (multiple submitters or expert panel), and lower outside VCEP genes than inside.

## 3. Data (all open)

- **ClinVar labels.** `variant_summary` monthly archives, GRCh38 rows, for 2019-12, 2020-12, 2021-12, 2022-12,
  2023-12, 2024-12, 2025-12 and 2026-09 (the latest).
- **Scores and frequencies.** MyVariant.info batch queries, dbNSFP 4.8a: REVEL, BayesDel_noAF, ESM1b, VARITY_R_LOO,
  CADD phred and AlphaMissense. Frequencies are gnomAD v2.1.1 exome AF, with genome AF as fallback.
- **AlphaMissense, primary source.** The official hg38 release (Zenodo 8208688): one score per variant on the
  canonical transcript. dbNSFP is the fallback.
- **Expert-panel criteria.** The ClinGen Evidence Repository export: every VCEP classification with its applied
  criteria codes and approval date, downloaded 2026-10-01.

## 4. Definitions

- **Missense.** A GRCh38 single-nucleotide variant whose ClinVar name carries a single amino-acid substitution
  `p.(Xaa)(n)(Yaa)`, with Xaa ≠ Yaa and neither a stop codon.
- **Confident label.**
  - P = {Pathogenic, Likely pathogenic, Pathogenic/Likely pathogenic};
  - B = {Benign, Likely benign, Benign/Likely benign};
  - review status of ≥1 star (criteria provided, single or multiple submitters without conflicts; expert panel;
    practice guideline).
  - Anything else counts as not confident, including conflicting, VUS, 0-star and other.
- **Rare.** gnomAD v2.1.1 exome AF < 0.01, with genome AF when the exome AF is missing. Variants absent from gnomAD
  count as rare.
- **Calibration-era set C2019.** Rare, confident missense variants at 2019-12. This replicates Pejaver's set except
  for the removal of training variants.
- **Yearly prospective cohorts N_Y.** Confident at snapshot Y and not confident at the previous snapshot, labelled as
  at Y.
  - N_2020 (2019-12 → 2020-12) replicates Pejaver's validation set.
  - N_2021 through N_2025 are the December-to-December steps.
  - N_2026 runs 2025-12 → 2026-09.
- **Primary prospective cohort N_new.** The union of N_2021 to N_2026, each variant labelled at its first confident
  snapshot.
  - Variants whose confident label later flips (P ↔ B) are counted and reported.
  - A sensitivity analysis uses the 2026-09 label.
- **Scores.** Where a tool gives several transcript scores, use the most pathogenic value: the maximum, or the
  minimum for ESM1b. The median is a sensitivity analysis. A variant without a tool's score is excluded for that
  tool only.
- **Thresholds.** The published nine-interval tables are used verbatim: Bergquist 2025 Table 1 for BayesDel, REVEL,
  AlphaMissense, ESM1b and VARITY_R, and Pejaver 2022 for CADD. Intervals a tool never reaches are marked "–".

## 5. Metrics and tests

- **Interval LR.** For interval I, LR_I = (n_P,I / n_P) / (n_B,I / n_B), within a cohort and tool. Uncertainty
  comes from a gene-cluster bootstrap (2,000 resamples of genes), because variants cluster within genes.
  - Target for a pathogenic interval with k points: c^k. For a benign interval: c^−k.
- **H1 verdict per interval.** Pathogenic side (benign side mirrored):
  - **meets:** the one-sided 95% lower bound ≥ target;
  - **falls short:** the one-sided 95% upper bound < target;
  - **inconclusive:** otherwise;
  - **insufficient:** fewer than 10 variants of the minority class in the interval.
- **H1 overall.** The thresholds "hold prospectively" for a tool if no interval of that tool falls short on N_new.
  - Primary tools: REVEL and AlphaMissense.
  - Secondary tools: BayesDel, ESM1b, VARITY_R and CADD.
- **H2.** log(LR_post / LR_pre) for the "≥ +3" and "≤ −3" intervals, with a gene-bootstrap CI.
  - Predicted sign: positive for pathogenic, with the benign LR moving further below 1.
  - Contrast: the same quantity for ESM1b, whose clinical uptake is lower, as an exploratory comparison.
- **H3.** Recount each VCEP classification on the ACMG points scale (Tavtigian 2020): PVS 8, PS 4, PM 2, PP 1,
  BS −4, BP −1, adjusted by `_Strength` suffixes; BA1 is stand-alone benign.
  - Classes from points: P ≥ 10, LP 6–9, VUS 0–5, LB −1 to −6, B ≤ −7.
  - A label is *tool-dependent* if removing the PP3/BP4 points moves it across the VUS boundary.
  - Report the agreement between the recount and the published assertion first. H3 is interpreted only on variants
    whose recount agrees.
  - Report the tool-dependent fraction by approval year, and interval LRs on tool-independent versus all VCEP
    labels.
- **H4.** Ratio of interval LRs between strata (1-star vs ≥2-star; VCEP gene vs not), with a gene-bootstrap CI, on
  N_new.
- **Reproduction gate (sanity check, not an endpoint).** Re-derive thresholds on C2019 with Pejaver's local-posterior
  method: prior 0.0441; a window holding at least 100 labelled variants; 1,000 bootstrap resamples; one-sided 95%
  bound.
  - Pejaver's windows also used a gnomAD set, which is not reproduced here, so agreement is expected only
    approximately.
  - Record the REVEL PP3 Strong threshold (published 0.932) and the BP4 Moderate threshold (published 0.183). If they
    are off by more than 0.1, investigate before interpreting H1.

## 6. Reporting rules

- Every tool × interval × cohort cell is reported, in a table and a figure.
- The headline is H1 for REVEL and AlphaMissense on N_new, then H2 and H3.
- No endpoint is switched after results are seen; anything added later is labelled exploratory in `deviations.md`.
- Independent adversarial review (a subagent) happens before any verdict is stated.

## 7. Known limitations (a priori)

- **REVEL's training set is not public.** Prospective REVEL LRs may be inflated by variants that were in HGMD before
  2016. AlphaMissense and ESM1b are not trained on clinical labels, and VARITY_R_LOO leaves each variant out.
- **ClinVar labels are imperfect and partly tool-derived.** H2 and H3 exist to measure this, not to remove it.
- **Differences from Pejaver's pipeline.** The gnomAD window set and exact training-variant removal cannot be
  reproduced, so C2019 is an approximation of their set.
- **Coverage of the H3 recount.** The points recount ignores VCEP-specific combining rules; it is validated against
  the published assertions before use.
