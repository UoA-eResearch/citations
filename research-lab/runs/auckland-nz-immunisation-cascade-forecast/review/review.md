# Independent review: NZ immunisation cohort-cascade forecast (pre-publication draft)

Reviewer: independent adversarial review (Claude, Fable 5.1), 7 October 2026, following `review/prompt.md`.
Scope: `plan.md` (691a47e), `deviations.md` (D1), `report.md` / `report.html` (6c62829), `code/` (fetch, parse,
backtest, score, figures), `results/`, `data/`. Read-only except this file. All computation on cores 0-3 with the
study venv.

## Recommendation: **fix first** (text, deviations log and scoring-script hardening; no recomputation of H1; frozen file unchanged)

Every number in `report.md` reproduces from the results files, the results files reproduce byte-for-byte from the
committed code and raw data, the parse is correct across all three layout eras, there is no look-ahead, and the
preregistered decision rule was applied as written. **H1 = Refuted stands.** The frozen forecasts match the hash in
`deviations.md` in both commits and in the working tree, and `score.py` does what the plan says.

The report must not be published as written, for three reasons that are about interpretation and the deviations log,
not about the arithmetic:

1. The central explanation of the post-2020 failure is wrong on the facts. The report says the October 2020 schedule
   change meant "the '12-month' milestone began counting different vaccines". The data say the opposite: the 12-month
   series barely moved, while the 18-month and 24-month milestones (the target and the short-horizon input) were
   redefined. (Issue 1.)
2. The plain-language headline "A quarter or two ahead, it works" is not true for the cells H2 will be scored on.
   For district Totals at a 1-quarter horizon, the cascade has had no advantage over persistence since 2020. (Issue 2.)
3. D1's justification compares the new interval's coverage on half the 2023-26 cells (none from 2024, the worst year)
   with the preregistered interval's coverage on all of them. On the same cells the gap is 65->76% and 64->72%, not
   ~60->72-76%. The frozen h=1 "recent" interval also breaks D1's own minimum (5 target quarters, not >= 6). (Issue 3.)

Fixing these touches `report.md`, `tiles.json`, `deviations.md` and (optionally) `score.py`. It does not touch
`results/forecasts_frozen.csv`, so the preregistered prospective test is unaffected.

## Recomputed numbers

All recomputed independently from `results/tables/backtest_cells.csv` and `results/forecasts_frozen.csv` with my own
code, and the whole pipeline re-run from the raw files in a scratch directory (`parse.py` -> `backtest.py`): the
regenerated `coverage.parquet`, `h1.json`, `backtest_summary.csv`, `backtest_cells.csv`, `secondary_by_district.csv` and
`forecasts_frozen.csv` are **byte-identical** to the committed files (frozen sha256
e19d0d63c19ed56e34629a9c0f93953c5e8c2beba7517ed09688bc62b0d547df, as recorded).

| Quantity (report location) | Report | Recomputed | Match |
|---|---|---|---|
| H1 cells / origins | 2,471 / 50 | 2,471 / 50 | yes |
| MAE M1 / B1 / B2, h=4 (pp) | 4.19 / 4.00 / 4.80 | 4.186 / 3.999 / 4.799 | yes |
| Reduction vs B1 (95% block-bootstrap CI) | −4.7% (−20.4, +13.4) | −4.68% (−20.4, +13.4); my own seed: (−21.4, +14.0) | yes |
| Reduction vs B2 (95% CI) | +12.8% (+4.6, +22.6) | +12.76% (+4.6, +22.6); my seed: (+4.4, +22.9) | yes |
| DM one-sided p vs B1 / B2 (NW lag 3) | 0.76 / 0.0009 | 0.757 / 0.00094 (t49 reference: 0.756 / 0.0016; lag 8: 0.74 / 0.003) | yes |
| Verdict under plan rule | Refuted (upper CI vs B1 < 30%) | Refuted | yes |
| Preregistered 80% PI coverage, h=4 primary | 61% | 61.3% (on 1,904 of 2,471 cells; first 8 origins have no interval) | yes, but note the denominator |
| Period table h=4 (M1/B1/B2, reduction) | 2.06/2.48/3.03 17%; 2.22/2.85/3.19 22%; 5.83/5.83/6.34 0%; 8.07/5.70/7.79 −42% | identical | yes |
| Excluding schedule-change + AIR targets | 5% worse than persistence | −5.0% (n = 1,961, 40 origins) | yes |
| Horizon table h=1 / h=2 | 2.30/2.88/2.94 20%,22%; 2.43/3.28/3.55 26%,32%; PI 77%, 76% | 2.296/2.878/2.941 20.2%, 21.9%; 2.430/3.276/3.553 25.8%, 31.6%; PI 77.4%, 75.8% | yes |
| h=3 vs persistence | "no better" | −8.9% (p = 0.88) | yes |
| Group table h=4 | 3.18/2.97; 4.83/4.76; 4.94/4.58 | identical | yes |
| M2 common cells | 2,351 cells; M2 3.78, M1 4.11, B1 3.92; 3.5% | 2,351 (M1 & M2 & B1); 3.781, 4.107, 3.919; 3.53% | yes, but these numbers are in no results file (Issue 12) |
| National h=4 | M1 3.20 vs B1 2.38; PI 26% | 3.196 / 2.383; 25.6% | yes |
| Frozen national Total 2026Q3 / Q4 | 85.4 (84.9-86.0) / 85.3 (84.8-86.0) | 85.41 (84.91-86.02) / 85.34 (84.79-86.00) | yes |
| Frozen national Māori / Pacific / Asian / Eur-or-Other | 73.4, 86.2, 96.4, 86.9; 73.4, 86.8, 96.0, 86.4 | identical | yes |
| Last published national C24 | 83.7% | 83.74% | yes |
| Districts >= 95% / >= 90% in 2026Q4 | none / Capital & Coast, Auckland | none / 90.9, 90.6 | yes |
| Lowest district 2026Q4 | Northland 69.3% | 69.31% | yes |
| Frozen rows | 279 | 279 (Totals 21 per horizon; Pacific only 7-10; Asian 5-10) | yes |
| District Totals h=1-2: MAE overall / 2023-26 | 1.7-1.9 / about 3 | 1.73, 1.86 / 3.18, 3.16 | yes |
| District Totals h=1-2: PI coverage overall / 2023-26 | 73-76% / about 60% (D1: 59-62%) | 75.4%, 73.5% / 62.2%, 59.0% | yes |
| Recent-window PI, 2023-26 "would have covered" | 72-76% | 76.2% (n = 80 of 180), 72.0% (n = 100 of 200) | numbers yes; comparison not like-for-like (Issue 3) |
| Headline check Jan-Mar 2026 6-month | 66.6% / Māori 48.5% | 66.56% / 48.49% | yes |
| District sum / national, 24m Total | within 1.5% | 0.9965-1.000 | yes |
| Quarters / missing | 66; 2009Q3, 2022Q2, 2023Q2 | 66; same three | yes |
| `report.html` vs `report.md` | | numbers identical (only the commit hash is dropped) | yes |

## Issues

Locations are `file:line` in the working tree at 6c62829.

### Must fix before publication

**1. The schedule-change mechanism is misattributed.** `report.md:90-92` ("So the '12-month' milestone began counting
different vaccines, and its relationship to 24-month coverage changed") and `report.md:168-170` ("The 12-month milestone
in particular changed meaning in October 2020").

National coverage by milestone, quarter-on-quarter change in pp:

| Quarter | 12 m | 18 m | 24 m |
|---|---|---|---|
| 2020Q3 | −0.3 | −0.9 | −1.1 |
| 2020Q4 | −0.5 | **−6.6** | −0.7 |
| 2021Q1 | −0.5 | **−4.4** | −1.5 |
| 2021Q2 | −1.1 | −0.1 | **−2.6** |
| 2021Q3 | −0.5 | +2.2 | **−2.0** |

Under Health NZ's definition ("completed all of their age-appropriate immunisations by the time they turned the
milestone age"), the 1 October 2020 change created a new 12-month event (MMR1, PCV booster) and moved MMR2 from 4 years
to 15 months. That adds vaccines to the **18-month** milestone (children must now have the 12-month event) and the
**24-month** milestone (MMR2 now due at 15 months). The 12-month milestone still measures the 6-week, 3-month and
5-month events, with one fewer PCV dose after the July 2020 3+1 -> 2+1 change. So the target was redefined, not the
h=3-4 input; the h=1-2 input (18 months) was also redefined. This is consistent with the signed errors: 2020-22 h=4
errors are negative (actual − M1 = −2.5 pp on average; persistence −4.2 pp), as a harder target would produce.
The 12-to-24 cohort gap (C24[t] − C12[t−4], national) widened from −2.5 pp in 2018-19 to −7 to −9 pp in 2021-22.

Fix: rewrite both passages. Say that the Oct 2020 change redefined the 24-month target (and the 18-month input), that
the 12-month input was essentially unchanged, and that a cohort-linked model must be re-anchored when the *target*
definition changes. The exclusion-window label in `plan.md:142-143` is fine as written.

**2. "A quarter or two ahead, it works" is overstated for the cells H2 scores.** `report.md:25-26`, tile 3 in
`results/tables/tiles.json`, `report.md:105-112`.

The 20-32% figures are 2012-2026 averages over Total + Māori + Pacific. For **district Totals** (the H2 primary cells),
by target period:

| Totals | h=1: M1 / B1 / reduction | h=2: M1 / B1 / reduction |
|---|---|---|
| 2013-19 | 1.15 / 1.68 / +31% | 1.19 / 1.72 / +31% |
| 2020-22 | 2.16 / 2.16 / **+0.3%** | 2.43 / 2.80 / +13% |
| 2023-26 | 3.18 / 3.20 / **+0.7%** | 3.16 / 3.87 / +18% |
| 2025Q1-2026Q2 | 3.39 / 3.36 / **−0.9%** | 3.61 / 4.24 / +15% |

For all primary cells in 2023-26 the h=1 gain over persistence is +9.5% (h=2: +25%). The gain at h=1 has gone where it
matters for H2. The H2 MAE criterion (<= 2.5 pp) is below every recent-period Totals MAE (3.2-3.6 pp), so the backtest
predicts H2 is more likely to be Refuted than Supported on error alone.

Fix: in "In plain terms" say "A quarter or two ahead it has worked over the whole record, but since 2020 the
one-quarter forecast for district totals has been no better than the latest published value, and the two-quarter
forecast about 15% better". Put the period split in the secondary horizon table. Change the tile to the period-specific
figures or label it "2012-2026 average".

**3. D1's justification is not like-for-like, and the frozen h=1 recent interval violates D1's own rule.**
`deviations.md:14-16`, `report.md:157-159`, `code/backtest.py:254` (frozen `zr` has no minimum-count guard;
the backtest version at line 164 does).

- The recent-window interval needs >= 6 of the last 8 target quarters. Because 2022Q2 and 2023Q2 have no file, it
  existed in 2023-26 for only 80 of 180 (h=1) and 100 of 200 (h=2) district-Total cells, and for **no 2024 target**
  (2024Q1-2024Q4 are exactly the AIR-migration year with the largest errors). On the cells where both intervals exist,
  the preregistered interval covered 65.0% (h=1) and 64.0% (h=2); the recent one 76.2% and 72.0%. The honest statement
  is "65->76% and 64->72% on the half of cells where it could be computed, none of them from 2024", not "60% -> 72-76%".
- At the freeze origin (2026Q2) the h=1 recent window has only **5** target quarters (2024Q3-2025Q3), the h=2 window 6,
  because `ORIGIN_LAST = 2025Q2` stops the backtest four quarters before the data end for every horizon. D1 says "with
  at least 6". The frozen `lo80_recent`/`hi80_recent` for h=1 therefore should not exist under D1's rule.
- The same `ORIGIN_LAST` choice means the preregistered h=1 interval ignores the three most recent available errors
  (targets 2025Q4-2026Q2) and the h=2 interval the two most recent. The plan fixed the origin range for H1; it did not
  need to apply it to the h=1-3 interval calibration.

Fix: amend D1 with the like-for-like numbers and the 5-quarter fact; state that the h=1 recent interval is reported
but does not meet D1's minimum (do not alter the frozen file); record that the h=1-2 interval calibration stops at
origin 2025Q2 as a limitation. Add the guard in `backtest.py` for any future run and log it.

**4. The report states the three mechanisms as facts in Results and hedges only in Caveats.** `report.md:80`
("The cascade worked until the 2020 schedule change and failed after it"), `report.md:90-96`, versus `report.md:165-167`.
Issue 1 shows one of the three is wrong as stated. Fix: carry "consistent with" into the Results bullets, and add the
AIR denominator mechanism (Issue 8), which is the best-supported of the three.

### Should fix

**5. The prediction intervals are mis-specified by cell size, and the report should say so because it determines how
H2 will fail.** `report.md:105-113`, `report.md:126-127` (acknowledged for the national total only), `report.md:154-156`.

Standardising by sqrt(n p(1−p)) assumes the error is sampling noise. It is mostly systematic, so pooled z-quantiles
give intervals that are too wide for small cells and too narrow for large ones:

| Preregistered 80% PI, coverage by target-cell size tertile | small | mid | large | national |
|---|---|---|---|---|
| District Totals, h=1-2 (median n 181 / 548 / 1,457) | 84.7% | 71.9% | **66.9%** | 37% |
| Primary cells, h=4 (median n 67 / 210 / 669) | 75.3% | 59.7% | **49.0%** | 26% |

The frozen national interval (84.9-86.0, 1.1 pp wide) is implausible against a 2023-26 national h=1-2 MAE of 1.1 pp.
The seven largest districts (Auckland, Counties Manukau, Waitematā, Canterbury, Waikato, Capital and Coast, Southern)
are where the H2 interval criterion will most likely fail. Fix: a sentence in "Frozen forecasts" and in "Caveats";
have `score.py` also report coverage by size tertile (secondary, not a change to the verdict rule); note for future
work that a pp- or logit-scale error model per district would be the natural replacement.

**6. Undocumented implementation choice in the interval pool.** `code/backtest.py:211` passes
`districts + ["National total"]` to `run_backtest`, so the national row's z-values enter each group's pooled
percentiles. `plan.md:108-109` says "pooled across districts for that group". Effect (my re-run with districts only):
district h=4 coverage 61.3% -> 59.2%, mean width 12.2 -> 10.6 pp; h=1 77.4% -> 76.3%; frozen Total z10/z90 at h=1
(−1.71, 2.13) -> (−1.63, 1.94). The frozen intervals depend on it. Fix: log as an implementation detail in
`deviations.md` (not a change to the frozen file).

**7. The 30% bar was unattainable for Pacific cells and marginal overall; the report should say so.** `plan.md:135`
("a substantive bar, not a statistical one"), `report.md:60-63`, `report.md:114-122`.

Binomial noise floor for |p̂ − p| at the target cell alone (the input adds about as much again):

| Period | MAE B1 | 30% cut needs | noise floor (all / Pacific) |
|---|---|---|---|
| 2013-16 | 2.48 | 1.74 | 1.60 / 2.30 |
| 2017-19 | 2.85 | 2.00 | 1.84 / 2.57 |

Pacific district cells have median n = 57 (40% of them suppressed); a perfect model could not have met the bar there,
and overall the bar sat about at the floor even before 2020. The 17-22% pre-2020 reduction was therefore close to the
achievable maximum, which the report does not say. Also, the eligible-weighted reduction vs persistence is **−16%**
(unweighted −4.7%): the cascade fails most where the children are. Fix: add both facts to Results/Caveats; the
verdict is unchanged because the preregistered rule is on the unweighted point estimate.

**8. The AIR mechanism is real and specific; the report mentions it in passing.** `report.md:93-94`. Health NZ's
coverage page states: "From 2024, immunisation coverage is measured using data from the AIR. The AIR captures a greater
number of eligible tamariki compared to the NIR, which means a drop in coverage is expected." In the data, the same
cohort's 24-month denominator divided by its 12-month denominator a year earlier is 1.043 and 1.026 for targets
2024Q3-2024Q4 (input under NIR, target under AIR), against 0.98-1.01 otherwise; the 12-to-24 gap reached −12.5 pp in
2024Q3 then closed to ~0 by 2025Q2. Fix: state the denominator mechanism and cite the Health NZ note (AIR went live
4 December 2023); it also explains why the four-cohort δ̂ took a year to re-anchor.

**9. Secondary suppression is understated.** `report.md:173-174` ("Pacific and Asian cells are often suppressed in
smaller districts"). Health NZ's files say: "Cell counts less than 10 are not shown. In addition, secondary suppression
has been applied, which means that other cells (including those with counts over 10) may also be suppressed." Verified:
Waitematā Pacific 24-month (n ≈ 240) is n/s in 2024Q3 and 2024Q4; Southern Māori 24-month (n ≈ 160) is n/s in the same
quarters. The parser handles this correctly (never back-calculates; the % column is ignored even where it is printed
beside n/s counts), but cell entry into the Māori/Pacific evaluations is not random, frozen Pacific forecasts exist for
only 7-10 districts, and H2's secondary scoring will be on an irregular subset. Fix: reword and say which rule applies.

**10. The h=1 forecast is a nowcast, not a quarter-ahead forecast.** `report.md:25-26, 129-132`. Health NZ publishes
Q1 (Jul-Sep) in December, Q2 in March, Q3 in June, Q4 in September. The "h=1" forecast for Jul-Sep 2026, frozen on
7 October 2026, was made a week after the target quarter ended; its value is a ~2-month lead on publication, not a
3-month-ahead forecast of behaviour. Fix: one sentence in "Frozen forecasts".

**11. H2 is a weak test and the report should say how weak.** `plan.md:165-168`, `report.md:146-152`. Forty cells from
two releases, with errors correlated across districts within a release. For a perfectly calibrated 80% interval the
coverage SD is 6.3 pp if cells were independent and larger when correlated, so "70-90%" can fail by chance and pass
by chance. Combined with Issue 2 (recent Totals MAE 3.2-3.6 pp vs the 2.5 pp bar), the report should state the
expected outcome rather than only "reason for caution".

**12. Several reported numbers exist in no results file.** The M2 comparison on 2,351 cells (3.78 / 4.11 / 3.92, 3.5%)
differs from the `backtest_summary.csv` row (2,377 cells, 4.113 / 3.778, no B1); the district-Totals h=1-2 figures
(1.7-1.9, ~3, 73-76%, ~60%, 72-76%) and the "26% national coverage" at h=4 are computed ad hoc. Fix: add rows to
`backtest_summary.csv` (or a `secondary_totals_h12.csv`) so every number in the report is traceable, and say "on the
2,351 cells with M1, M2 and persistence".

**13. Data-description overstatements.** `report.md:34-35` "Every quarterly coverage file ... was collected": three
quarters are missing; I found no 3-month 2022Q2 or 2023Q2 capture in the Wayback index under the Te Whatu Ora paths
(the health.govt.nz index was offline), so say "every file that could be recovered". `report.md:38` "12 current files"
vs `plan.md:13` "24 current files": say the 12 annual files were downloaded but not used. `report.md:42-43` "the
remainder being children with no district": now verifiable, Health NZ's key says "National Total = Northern + Te Manawa
Taki + Te Waipounamu + Central + UNKNOWN", so cite it. `report.md:76`: the 61% coverage is on 1,904 of 2,471 cells.

### Minor

**14. Te Mana Raraunga framing.** `results/figures/districts_2026q4.png` orders districts by forecast coverage, which is
a league table, against `report.md:184-185` ("not as a ranking of communities"). `report.md:29` gives the Māori figure
without the service-reach framing used elsewhere. Fix: order the figure alphabetically or by region; add "how far
services are reaching Māori children" to the plain-terms sentence. Naming Northland as lowest is acceptable if framed
as service reach.

**15. Provenance is sound but compressed; say so.** Commit chain: plan 08:43:08 -> backtest code 08:44:13 -> results +
D1 08:46:12 -> score.py 08:46:45 -> report 08:49:06 NZDT, all pushed to origin/main. File mtimes agree (`backtest.py`
edited 08:45:27 for D1, run 08:45:27-08:45:55; a first, unlogged run fits between 08:44:13 and 08:45:27 and its
numbers reproduce from the final run). The diff of `backtest.py` between e1a51b0 and eb53bc6 is confined to the D1
lines. `parse.py` and `plan.md` are unchanged since 691a47e. Commits prove the order of commits, not of computation;
the parse (08:41) preceded the plan, which the plan discloses. Fix: state in the report that the chain ran in six
minutes so a reader can weigh it.

**16. `score.py` hardening before the first release.** (a) It depends on re-running `parse.py` on a new Health NZ file;
a layout change would force a code edit that `plan.md:160-161` forbids. Decide now that parse-only edits for new
layouts are allowed, must be logged, and must leave the historical rows unchanged; record the current
`data/coverage.parquet` sha256 (prefix 2192604074615726c) in `deviations.md` so that can be checked. (b) Record
`n_cells` and fail loudly if it is not 40 once both releases are in (district renaming would silently shrink the set).
(c) The hash regex takes the first 64-hex string in `deviations.md`; keep D1's hash first or anchor the regex to D1.
(d) Health NZ changed its suppression threshold in one quarter ("6 instead of 10"); irrelevant to Totals, relevant to
the secondary groups.

**17. B2 works on the coverage scale** (`code/backtest.py:95-96`, polyfit on p, clipped) although `plan.md:78` says
"All models work on the logit scale". The B2 paragraph in the plan (clip to [0, 1]) implies the coverage scale, so the
implementation follows the specific text; note the ambiguity in the report's baseline description.

**18. Sub-period DM statistics in `backtest_summary.csv` are unreliable** (e.g. 37.3 for 2017-19 vs B2 on 12 origins
with a lag-3 HAC variance). The report does not quote them; keep it that way or add a note to the CSV.

**19. Cohort alignment.** n24[q+4] / n12[q] nationally is 0.98-1.02 for most of the record and 0.98-1.04 in 2021-24;
n24[q+2] / n18[q] has SD 0.01. Alignment is good enough for the method; the 2021-24 swings (COVID, AIR) are part of
Issue 8 and worth one sentence.

## Answers to the brief

1. **Parsing.** Correct. Independent re-parse is identical. 27/27 spot-checks of raw cells match across the 2009
   `.xls` (DHB Area / NZE + Other triples), the 2015 and 2018 archive sheets, the 2020Q3 long layout with district in
   column 0 and milestone in column 1, the 2021-23 layouts with forward-filled milestone labels, a Region column and the
   "Nothern" typo (skipped, never treated as a district), and the 2024-26 current files. NZE + Other -> European or
   Other sums match and are missing when either part is n/s. Otago + Southland -> Southern applies to the four
   2009-2010 quarters only and is missing if either part is suppressed. Quarter ends derive from the file-name start
   date (archive) or end month / fiscal quarter (current) and are all correct. Suppressed cells are never
   back-calculated, even where Health NZ prints a % beside n/s counts. Group sums equal Totals in 5,013 of 5,013
   complete cells; district sums are 99.65-100% of national. Sums of four quarterlies agree with the unused annual
   files to within ~1% (different extraction dates), except where quarterly cells are secondarily suppressed (Issue 9).
   No unmapped district strings in any archive file.
2. **Implementation.** M1, B1, B2, M2, the logit clipping, the four-cohort δ̂ with a minimum of two, the DM test
   (Bartlett/Newey-West, lag h−1, one-sided normal), the moving-block bootstrap (block 4, 5,000 draws) and the decision
   rule match `plan.md`. No look-ahead: inputs are at or before the origin and interval z-values are filtered on target
   <= origin. Deviations from the plan's wording: national total in the interval pool (Issue 6) and B2 on the coverage
   scale (Issue 17). H1 numbers recomputed exactly (table above).
3. **Timing.** Plan and backtest code committed before results; the only post-result code change is D1, logged. D1 is
   justified in direction but its evidence is overstated and its own rule is broken in the frozen file (Issue 3). H2 is
   scored on the preregistered interval in both the plan and `score.py`. Frozen forecasts committed and hashed on
   7 October 2026, before the Q1 2026/27 release (due December 2026); hash verified in eb53bc6, HEAD and on disk.
   `score.py` implements the plan's rule; hardening suggested (Issue 16).
4. **Interpretation.** The catch-up explanation is well supported (12-to-24 gap −12.5 pp in 2024Q3 to ~0 by 2025Q2;
   h=4 errors +5.8 pp and 76% positive in 2023-26). The AIR explanation is supported and should be made specific
   (Issue 8). The schedule-change explanation is misattributed to the 12-month milestone (Issue 1). The Results section
   states mechanisms as facts (Issue 4). The frozen forecasts are described accurately. The H2 cautions are present but
   understate what the backtest implies (Issues 2, 5, 11). Te Mana Raraunga framing is respected in the text; the
   district figure is a ranking (Issue 14).
5. **Numbers.** Every number in `report.md` matches the results files or recomputes from `backtest_cells.csv`;
   `report.html` carries the same numbers. Several are not in any table (Issue 12).
6. **Expert objections.** The target's definition changed in 2020 and the register in 2023-24 (Issues 1, 8); the
   30% bar sat at the binomial noise floor for small cells (Issue 7); intervals are mis-specified by size (Issue 5);
   secondary suppression makes the Māori/Pacific panels irregular (Issue 9); h=1 is a nowcast (Issue 10); H2 has little
   power (Issue 11). The 8-month milestone is not used and the switch of the official target from 8 to 24 months is not
   relevant to the computation. Cohort alignment is adequate (Issue 19).

## Checks performed

Read every file named in the brief; `git log/show/diff` on all five commits and `origin/main`; file mtimes; byte
comparison of the committed frozen file's hash in both commits; full pipeline re-run in a scratch directory and byte
comparison of all outputs; independent reimplementation of MAE, reductions, DM (also t-reference and HAC lags 4 and
8) and block bootstrap (own seed); re-run of `run_backtest` with and without the national total in the interval pool;
raw-cell spot checks in eight files spanning all layouts; scan of all archive first/second columns for unmapped
district names; group-sum, district-sum and cohort-denominator checks; annual-file cross-check for five years;
suppression verification against raw rows and the files' key text; Health NZ coverage page (definitions, AIR note,
publication calendar); Wayback CDX queries for the missing quarters; web sources on the October 2020 schedule change
and the AIR go-live (4 December 2023).
