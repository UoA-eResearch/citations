# Preregistration: do Supreme Court precedents die before they are overruled?

Lead: `legal-digital-humanities-precedent-erosion-before-overruling`. This plan is committed before any citation has
been counted.

**What was seen before this plan.** The treatment side only (`code/overruled.py`,
`results/tables/overruled_coverage.json`):
- Wikipedia's list of explicitly overruled decisions parses to 132 (overruled, overruling) pairs: 107
  constitutional, 22 statutory, 3 common law.
- All 132 are linked to CourtListener clusters through their U.S. Reports citation.
- 126 overrulings fall in 1960–2024.
- **Coverage.** SCDB flags 174 decisions of 1960–2024 as altering precedent (`precedentAlteration` = 1). 88 of those
  are not on the list, because the list is incomplete and SCDB's flag also covers alterations short of explicit
  overruling. The treated population is therefore the listed explicit overrulings, not every alteration.

**Novelty.** Feldman (SCOTUSblog / Legalytics, June 2026) argues the case qualitatively, from six case studies.
Broughman & Widiss (2017) ran an event study on Shepard's net citations with a 5-year pre-window. No population-wide,
long-pre-window, matched-control study on open lower-court citation data was found.

## 1. Data

- **Citations.** The CourtListener citation map (2026-09-30), keeping citing–cited opinion pairs.
  - Opinions map to clusters through the opinions dump. Clusters give the citing date (date_filed) and map to
    dockets, and dockets to courts.
  - A citation is lower-court if the citing court is not `scotus`.
  - Citations are counted per citing calendar year, per cited Supreme Court cluster, with repeated citations from the
    same citing cluster counted once.
- **Coverage control.** The total of lower-court citations to all Supreme Court clusters in each year enters as the
  denominator of shares (descriptive), and through calendar-year fixed effects in the model.

## 2. Population

- **Treated.** Listed overruled decisions, with the following restrictions:
  - the overruling year is 1960–2024;
  - the overruled decision was decided at least 20 years before it was overruled, so that event years −20 to −11 are
    observed;
  - the decision has at least 50 lower-court citations in calendar years before the overruling year.

  A decision overruled twice (in part, then fully) is treated at its first listed overruling. Pairs whose overruled
  decision links to several clusters use the cluster with the most lower-court citations.
- **Controls.** Supreme Court clusters never listed as overruled, with at least 50 lower-court citations before the
  treated case's overruling year.
  - Each treated case gets up to 10 controls, drawn from clusters decided within ±2 years of it and, where SCDB covers
    both (1946 on), in the same SCDB issue area.
  - Controls are matched by nearest Mahalanobis distance on log(1 + lower-court citations) in each of event years
    −20 to −11, measured on the treated case's calendar.
  - Matching is with replacement across stacks. Standardised mean differences on the matching variables are reported.

## 3. Estimation

- **Stacked PPML.** Each treated case and its controls form a stack.
  - The outcome is yearly lower-court citations for event years −20 to +10.
  - Fixed effects are case × stack and calendar year × stack.
  - Treated × event-year dummies run for −10 to +10, with events −20 to −11 pooled as the reference.
  - Standard errors are clustered by stack.
- **The relative decline at event e** is D(e) = 1 − exp(β_e), where β_e is the treated × event coefficient.
- **The preregistered statistic** is the pre-share, D(−1) ÷ D(+5): the share of the five-years-after decline already
  present the year before overruling.
- **The interval** comes from a stack bootstrap (B = 1,000, seed 20261023), refitting the model each time.

## 4. Hypothesis and decision rule

- **The precondition.** If D(+5)'s 95% interval includes 0 (no detectable post-overruling decline), the pre-share is
  not defined and H1 is **not testable**.
- **H1 (precedents erode before overruling): at least a third of the five-year decline has already happened by the
  year before overruling.**
  - **Supported** if the pre-share is at least 0.33 and its lower bound is above 0.
  - **Refuted** if the upper bound is below 0.33.
  - **Otherwise Inconclusive.**

## 5. Secondary (reported, not confirmatory)

1. **The event path:** D(e) for e from −10 to +10, with the share series.
2. **Excluding citing opinions that also cite the overruling decision.** This addresses whether the post-decline is
   partly citations that discuss the overruling itself.
3. **Federal courts only,** and state courts only.
4. **Constitutional against statutory** overrulings.
5. **Overrulings after 1990.**
6. **Out of sample.** Pre-trends of Chevron (overruled by Loper Bright, 2024) and Humphrey's Executor (overruled by
   Trump v. Slaughter, 2026; not in the 1960–2024 window if its listed year is 2026), against their matched controls.
7. **Robustness of the ratio:** the pooled statistic mean D(−3..−1) ÷ mean D(+3..+5), which is less noisy.

## 6. Limits stated in advance

- **The treated set** is the listed explicit overrulings, about half of SCDB's alterations.
- **CourtListener coverage** changes over time. Calendar-year fixed effects within each stack absorb common shifts,
  but not shifts specific to a court or jurisdiction.
- **Counts are not treatment.** A citation counts whether it follows, distinguishes or criticises the precedent.
- **Matching on the −20 to −11 trajectory** over-controls if erosion starts before year −10.
- **The ratio** is unstable when the post-decline is small, hence the precondition and secondary 7.

## 7. Outputs

- `results/tables/`: `overruled_pairs.csv`, `overruled_coverage.json`, `matching_balance.json`, `primary.json`,
  `event_path.csv`.
- `results/figures/`.
- `deviations.md` records any change before the results it affects.
