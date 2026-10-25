# Deviations from the preregistration

## D1 — 2026-10-23 17:16 NZDT — PPML separation (POST-RESULT: logged after the first primary run was read)

**The problem.** The first run of `did.py primary` returned log RR −1.11 (SE 0.29), which the rule calls Refuted. Its
event-time coefficients show why that number is degenerate:
- events 0 and 1 are +0.45 and +0.73;
- events 2 to 6 are −2.9 to −12.8.

Those later coefficients belong to cohort × event-time cells with zero editions (`results/tables/cell_counts_d1.csv`),
mostly in calendar years 2024–2025, when Open Library has ingested almost nothing (15 editions in 2025 across all
linked works). In PPML a dummy whose cells are all zero is perfectly separated, and its maximum-likelihood estimate
is −∞. pyfixest returned large negative numbers instead of dropping it, and the event 0–2 aggregate averaged them in.

**The fix.** It follows the standard convention (ppmlhdfe):
- a cohort × event dummy whose cells sum to zero is separated, so its observations are dropped and it is not estimated;
- the event-time aggregates and the RR average only the identified cells, with cohort-size weights renormalised.

Every variant uses this. The first-run numbers are kept (`primary_pre_d1.json`, `event_study_pre_d1.csv`) and
reported.

**What it does to the result.** The fix removes cells that pull the estimate down, so it moves the result towards
H1. It is reported as a post-result change, and the report states the preregistered number.

**Linkage validation** (`results/tables/linkage_validation.json`; 300 registrations, labelled blind by a separate
agent):
- precision is 0.81 (renewed 0.78, never renewed 0.84);
- recall is 0.38 (renewed 0.29, never renewed 0.50).

Renewed, more popular books more often have duplicate Open Library work records. These are either dropped by the
uniqueness rule or have their editions split across records, so the outcome is undercounted for treated works. This
is reported as a limitation. The plan has no gate on it.

## D2 — 2026-10-25 13:13 NZDT — fixes after independent review (POST-RESULT)

The Fable review (`review/review.md`, verdict "fix first") found the following. All changes were made after every
result had been seen. The first-version tables are kept in `results/tables/v1_pre_review/`.

1. **Renewal matching (registrations.py).**
   - The renewal TSVs use two schemas (author/title/rdat and auth/titl/dreg); they are now coalesced.
   - The reviewer's diagnosis was partly off: the auth/titl files cover 1950s–60s registrations, so they cannot
     match. The real gap was 1,405 date-matched renewal rows whose title field is empty in the first schema. These now
     fall back to the entry's full text.
   - The title score is now the better of the raw renewal title and the renewal title with the author's name tokens
     removed (renewal entries are often prefixed "SURNAME, GIVEN.").
   - **Effect:** 1,278 registrations move from never renewed to renewed (144 of them linked). Renewed shares are now
     17–20% per year. A spot check of 12 at random found all 12 genuine. Links are unchanged (identical file hash).
2. **Reference-cell separation (did.py).** D1 tested only the estimated dummies. A cohort whose reference cell
   (event −1) has zero editions is unidentified (all its dummies are measured against zero) and is now dropped and
   recorded, iterating with D1's cell rule.
   - This removes cohorts 2022–2024 from the no-print-on-demand variant and cohort 2025 from the lag variant. Those
     produced the earlier "RR 794" and the failing pre-trends.
   - The primary model is unaffected (no zero reference cells).
3. **Sensitivity (post hoc), `did.py sensitivity` → `results/tables/sensitivity.csv`:**
   - leave-one-cohort-out;
   - calendar years limited to ≤ 2023 and ≤ 2022;
   - excluding treated works whose Open Library first-publish year predates registration (reprints; 17 of 65
     datable treated works);
   - each for the preregistered count outcome and two **exploratory** outcomes: any new edition in the year, and
     editions capped at 5 per work-year.
4. **OLS reading.** Coefficients are now expressed relative to the treated pre-period mean of log(1 + editions). The
   two-way-FE OLS (`did.py ols`) is labelled as such, distinct from the Sun–Abraham OLS (`secondary.py`).
5. **Linkage validation (validate_links.py score).**
   - In 16 of 90 linked items the matcher's chosen work was not among the 8 candidates shown to the labeller. Those
     items cannot be judged, and they are excluded from precision.
   - Precision is now 73/74 = 0.99. Recall is labelled as conditional on the candidates shown.
   - Renewal status in the validation table comes from the corrected registrations.
6. **Descriptives and provenance.**
   - Ambiguity-drop shares by renewal status are added to the linkage summary.
   - The Gutenberg release rate per 1,000 works at risk, by years since expiry, is added. Normalised this way, it shows
     no early burst, contrary to the review's raw counts.
   - `did.py cells` now generates the cohort × event cell counts (`cell_counts.csv`).
   - The original `cell_counts_d1.csv` came from an ad hoc command, and the recorded pre-D1 run was a re-run made
     just before D1 was applied. The time of the very first run was not recorded.
7. **An unlogged deviation, now logged.**
   - Plan §1 says blocking is on "author surname plus the first title token"; link.py blocks on the first two
     non-article title tokens and applies the surname at resolution.
   - The first-publish-year date rule rarely binds, because 85.5% of linked works lack a first-publish year.
