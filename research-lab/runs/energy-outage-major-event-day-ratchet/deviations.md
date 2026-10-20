# Deviations from plan.md

Timestamps are Pacific/Auckland, from `date`.

## D1 — 2026-10-18 21:01 NZDT — data format and download checks (before any daily series or index was computed)

- **Integrity.** All 14 downloaded figshare files (EAGLE-I article 24237376, version 4) match the repository's sizes
  and MD5 sums. The 2014 outage file and the two R scripts were not downloaded, because the plan's indices start from
  2015 data.
- **The 2023 file names its outage column `sum`, not `customers_out`.** Its rows have the same layout and
  magnitudes as the 2022 and 2024 files (county, 15-minute snapshot, customers out), so `code/build.py` reads that
  column as customers out. The 2024 file adds a `total_customers` column, which is not used: the plan's denominator is
  MCC 2022.
- **The first build run failed on 2023 because of this.** `build.py` now processes four years in parallel and caches
  each year's state-day totals, without changing what it computes.

## D2 — 2026-10-21 12:02 NZDT — after independent review

An independent adversarial review (`review/review.md`) reproduced every table to machine precision and confirmed the
three verdicts as computed. Nothing in the pipeline was re-run or changed. The changes are to the report's reading
of the results, plus three analyses the review added; each review number used was checked against the reviewer's
outputs before use.

1. **The Pareto shape cap.** `simulate.py` caps the fitted tail shape at 0.9 (14 of 25 states reach it). The cap was
   in the code committed before the data (e868d1c) but was never stated in `plan.md`. It does not drive the results:
   capped at 0.5 instead, the H3 ratio is 0.76 (`review/reviewer_checks/check6_simulation_variants.json`).
2. **Scenario B reread.** The simulation's "storm" is any day above the 95th percentile of non-zero days, but the 2.5β
   threshold sits at a median 2.7 times that level, so 57–66% of simulated storm days are normal operations under the
   standard. Growing only storm size gives no effect; growing only frequency gives all of it; with storms defined at
   major-event scale the rolling rule detects 8% against an oracle's 4%. The "storm leakage" framing is withdrawn from
   the headline, the simulation section, the plain-terms section and the F4 caption.
3. **H2's dependence on 2015.** The rolling-minus-frozen difference is Inconclusive with the frozen baseline set on
   2017–2019 or 2018–2022, and under the preregistered coverage sensitivity. The preregistered verdict stands as the
   preregistered test, but the headline now says it holds only with 2015 in the baseline. Most of the reported rise in
   the threshold is attributed to the window's composition.
4. **Comparison with utility-reported MED-excluded SAIDI** (`review/reviewer_checks/check7.json`): flat, −0.05% a
   year, against +3.1 for this index. The rise is now presented as a property of the state-level construct.
5. **Prior work.** Eto, LaCommare, Sohn and Caswell (2016) is added, verified against OpenAlex, and the novelty claim
   narrowed.
6. **Smaller corrections:** the coverage sensitivity's reach (2018–2022 only); data-quality disclosures; the
   decomposition's "storm change" relabelled as the residual it is; years to first detection reported (median five);
   the within-state validation statistic added; the D1 wording made exact.

The review files the reviewer wrote under `review/reviewer_checks/` first entered the repository in commit 96c8a7c,
which was a commit for a different study that swept them in by mistake.
