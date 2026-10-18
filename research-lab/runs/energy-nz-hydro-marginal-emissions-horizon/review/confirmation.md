# Confirmation pass: energy-nz-hydro-marginal-emissions-horizon (commit 4916fbe)

Reviewer: adversarial review agent, 2026-10-18. Checked against the 16 issues in `review/review.md`: report.md and
report.html, deviations.md (D2), code/sensitivity.py and results/tables/sensitivity.json, code/figures.py with the
re-rendered figures and captions, results/tables/tiles.json. One new check was run:
`review/reviewer_checks/confirm_gradient_ci.py` (bootstrap intervals of the horizon differences under all 17
specifications, using the study's own `sensitivity.fit()`; output in `out_confirm_gradient_ci.json`).

## Recommendation: publish with edits

The revision does what the review asked. The preregistered pipeline and numbers are unchanged; the 17-specification
sensitivity analysis is implemented independently and its numbers match mine for every specification both of us ran
(the one exception, half-hour × month fixed effects, is a genuinely different specification; see item 2); the
summary, plain-language section, tiles and figure titles now present only the sign of the gradient and the flat AEF
as findings; the H2 construct limitation, the literal-rule Refuted, the post hoc block rule and the day-mean rescoring
are all disclosed; the H1 instrument mismatch, the per-MWh-moved figure, the sign-reversal share, the gradient
numbers, the energy-balance identity, the quarterly-check caveat, the storage caveat and the minor fixes are in. Every
number I checked in the revised report matches sensitivity.json, mef.json or simulation.json.

Six items remain. The first is a substantive qualifier to the new headline; the rest are wording, one factual
correction in D2, and a figure re-render. None requires new preregistered analysis.

## Status of the 16 issues

| # | Issue | Status |
|---|---|---|
| 1 | MEF levels not robust to lagged-outcome controls | Addressed: 17-row table, ranges in summary and tiles, "What we cannot say". See remaining item 1 for the headline's qualifier. |
| 2 | Window inflow as uncontrolled channel | Addressed: inflow responses, inflow-controlled rows, mechanism moved to "What we cannot say", F1 title changed. |
| 3 | Coal/gas composition artefact | Addressed: two-row composition table, "we draw no fuel conclusion", tiles and plain language fixed. |
| 4 | 7-day fragility (leap-year, hh×month FE, 7-day-mean instrument) | Addressed in the table. D2's description of my hh×month variant is wrong (item 2). |
| 5 | Geothermal placebo | Addressed (channel named, both readings of the rule). The "fires at 2 days" statement uses the wrong intervals (item 3). |
| 6 | Wind control | Addressed. |
| 7 | H2 construct | Addressed (H2 point 1, summary, D2). |
| 8 | H2 disclosures | Addressed (literal rule, timing, day-mean rescoring −2.45 (−4.05 to −0.99), control-set dependence). |
| 9 | ±1 h "a third survives" | Addressed (now "uninformative", with the overlap fact). |
| 10 | Per MWh moved, calendar-day window, sign-reversal share | Addressed. |
| 11 | H1 matched instrument | Addressed (1.52, F 10.8; difference 1.32, 0.66–3.45). Minor provenance point (item 5). |
| 12 | Descriptive gradient numbers | Addressed (0.16, 0.11–0.21; 0.54, 0.38–0.79). |
| 13 | Energy-balance identity | Addressed. |
| 14 | Quarterly check is within-year | Addressed. |
| 15 | Storage level and Wānaka outflow | Addressed. |
| 16 | Minor text/number fixes | Addressed (n, tile 3, implementation note, Tiwai wording, MfE row, geothermal share). |

## Remaining items

**1. "Holds in every specification" is true of the point estimates, not of the intervals.** *Location:* report.md
summary ("What holds in every specification we tried", bullets 1–2); plain-language paragraph "First" ("That held in
every version of the analysis we tried"); tiles.json tile 2 ("always above the 1-hour value"); F1 caption ("holds in
every one"); "What this does and does not show", first bullet. The point estimate of MEF(7 d) − MEF(1 h) is positive in
all 17 specifications (0.12 to 0.64), but its 95% month-block bootstrap interval excludes zero in 15 of 17. The two
exceptions are the specifications that address both review concerns at once:

| Specification | MEF(7 d) − MEF(1 h) | 95% CI | MEF(1 d) − MEF(1 h) | 95% CI |
|---|---|---|---|---|
| no lagged D/E + window inflow | 0.116 | −0.027 to 0.234 | 0.052 | −0.001 to 0.095 |
| 3 days of anomaly history + window inflow | 0.118 | −0.050 to 0.262 | 0.040 | −0.009 to 0.079 |
| (all other 15) | 0.18 to 0.64 | lower bounds 0.12 to 0.46 | 0.06 to 0.24 | lower bounds 0.02 to 0.19 |

*Fix:* in each location, say "the point estimate rises in every specification; the rise is statistically clear in 15
of 17, and not in the two that control for window inflow without lagged outcomes". Tile 2: "point estimate always
above the 1-hour value". Add the difference intervals to `sensitivity.json` (the draws are already computed in
`fit()`; a few lines in `main()`), so the claim is backed by a results file rather than by the reviewer's output.

**2. D2 mischaracterises the reviewer's half-hour × month variant.** *Location:* deviations.md D2 ("Day-type dummies
are kept. The reviewer's version without them gave 1.24 at 7 d with F 9.2"). My variant (`reestimate.py`,
`design(extra_fe=True)`) kept the preregistered half-hour × day-type dummies and *added* half-hour × month dummies;
the study's variant *replaces* half-hour × day-type with half-hour × month plus a day-type main effect. Mine nests the
study's. The correct statement is: with half-hour × month effects added on top of the preregistered fixed effects,
MEF(7 d) is 1.24 with F 9.2 (weakly identified); with them replacing the half-hour × day-type effects, 0.72 with F 43.
*Fix:* reword D2; add the first variant to the table's "Reading" notes or as a row, since it is the more demanding
specification and it pushes the 7-day first stage below the plan's threshold.

**3. The geothermal-placebo sentence uses the re-run's intervals, not the preregistered ones.** *Location:* report.md
"Other checks", Geothermal placebo ("Read as 'excludes zero', it fires at 2 days"; "Intervals are near zero at their
lower ends"). The preregistered placebo output is `mef.json` `geo_ci` (bootstrap seed 20261019): lower bounds 0.0035
at 12 h, 0.0027 at 1 d and 0.0041 at 2 d, so under the "excludes zero" reading the flag fires at 12 h, 1 d and 2 d, as
the pre-review draft said. `sensitivity.json` `geothermal_response` re-draws with seed 20261018 and gets −0.0001,
−0.003 and 0.004; that is seed noise at a boundary, and the report should quote the preregistered file. *Fix:* "Read
as 'excludes zero', it fires at 12 h, 1 d and 2 d in the preregistered bootstrap (lower bounds 0.003–0.004); a re-run
with another seed puts the 12 h and 1 d lower bounds just below zero."

**4. F1 and F2 titles are cut off at the right edge of the rendered PNGs.** *Location:* code/figures.py suptitles
("... (preregistered specification)" renders as "(preregistered specif"; "... (not robust; see text)" renders as
"(not robust; see tex"). *Fix:* shorten the titles (e.g. "Marginal emissions rise with the counting horizon
(preregistered)" and "Where weather-driven demand is met, preregistered controls (not robust)") or reduce the font
size, and re-render.

**5. Two cited numbers have no home in results/tables.** *Location:* report.md H1 section ("MEF(30 d) − MEF(1 h) =
1.32 (0.66–3.45)"; "autocorrelation 0.04 at 7 days") and "Reading the table" ("day-to-day autocorrelation 0.59").
These come from `review/reviewer_checks/out_h1_probe.json` and `out_reestimate2.json`; `sensitivity.json` holds
MEF(30 d) under the 7-day-mean instrument but not the difference interval or the autocorrelations. *Fix:* add them to
`sensitivity.json` (the 1440 and 2 draws are in hand inside `fit()`), or cite the reviewer files explicitly.

**6. Trivial.** (a) Sensitivity table, row "weather history + window inflow": F at 7 d is 56.5, printed as 57 while
the other rows round half-down. (b) report.html still carries "pre-review draft" in the masthead because
`build_report_html.py` keys the status on the existence of this file; rebuild after it lands. (c) `sensitivity.py`
spreads daily inflow over 48 half-hours on DST days of 46 or 50; immaterial.

## What was verified in this pass

- sensitivity.json reproduces my numbers for the nine control-set rows, the window-inflow rows, the no-wind row, the
  calendar-aligned climatology, the 7-day-mean (including 30 d) and next-24-h instruments, the three subsamples, the
  four-control-set composition, the inflow responses (−2.7 / −3.7 / −8.0) and the day-mean H2 rescoring (−8,853 t,
  −2.45, −4.05 to −0.99), to three decimals.
- `sensitivity.py`: the joint partialling of two window controls is done exactly (QR of the residualised W and I);
  the common sample is the preregistered one (n = 173,569); the scheduler re-implementation gives 250,640 MWh
  actually moved, matching mine; the only code change in 4916fbe adds the 12 h and 2 d horizons for the geothermal
  check.
- Summary ranges: 1 h −0.16 to 0.23, 7 d 0.13 to 0.79, 7 d − 1 h 0.12 to 0.64, 1 d − 1 h 0.04 to 0.24, "1.3 to 8
  times the average" (0.129/0.098, 0.794/0.098): all match the table.
- report.html body matches report.md; tiles match tiles.json; captions match figures.py.
- Git: dc75863 (review + sensitivity code, 16:26) precedes sensitivity.json (16:30), figures (16:31) and 4916fbe
  (16:32); mef.py, series.py, simulate.py, checks.py and their outputs are untouched since 15:39.
