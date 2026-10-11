# Independent review: GBD revision calibration (health-econ-gbd-revision-calibration)

Reviewer: independent adversarial review, 12 October 2026. Worked only from the run directory, the raw files in
`data/raw/`, read-only git commands, and my own recomputations (study venv). No raw GBD rows or GBD estimates are
reproduced below; every number is a share, count, difference or ratio.

## Recommendation: **publish with edits** (edits R1-R6 are required, not optional)

The preregistered pipeline is sound and I reproduce it: the 55,896-cell panel rebuilt from the raw zips matches
`data/panel.parquet` exactly, the four verdicts follow the preregistered rules, every number in `report.md` and
`tiles.json` matches the results files, the plan and analysis code were committed (6b7a3e2, 00:07:45) before the
earliest result file (00:08:05), and the only code change after that is the one-line D1 fix. The headline verdict
(Inconclusive) stands.

What must change is the interpretation layer. (i) The "no gradient by data quality" message is a property of the
equal-cell weighting: weighting cells by deaths, C2 is 90% in high-quality countries and 70% in the low group (gap
+20 points, bootstrap CI +2 to +37), driven by large revisions to major causes in China and India, both of which the
study classes as "no vital registration". (ii) The `low` group's `none` class (85 countries) is wrongly described: it
contains Taiwan, China, India, Bermuda, Guam, San Marino and other places that do have death registration, and at
least eight of them have post-2010 data in the WHO Mortality Database; absence from WHO Table 4.1 mostly reflects
WHO's Section 3.1 exclusion of small states and non-member territories. (iii) The H4 label (Inconclusive rather
than Refuted) sits inside bootstrap Monte Carlo noise and flips under the country-only bootstrap and under two
defensible reclassifications. (iv) A distribution-free version of H3 (do the two 95% UIs overlap? floor 90% under
calibration with no shape or dependence assumption) gives 88.6% with a CI that reaches 90.7%, so the strength of H3
depends on the log-normal / non-negative-correlation assumptions, which the report should say. None of these
changes a preregistered verdict; all of them change what a reader should take away.

## 1. What I verified (by prompt item)

**1. Panel.** Rebuilt independently from the six zips: inner join on (location_id, cause_id, year) gives 55,896 rows
= 204 × 137 × 2 with no missing values; all six estimate columns and both population columns agree with
`panel.parquet` to 0.0. The 137 shared IDs are exactly the intersection of the 139 level-3 IDs in the GBD 2021 file
and the 140 in the GBD 2023 2019-year file (541 and 1056 only in 2021; 716, 940, 1161 only in 2023). The level-3
list extracted from the GBD 2023 all-cause 2021-year file is identical to the 2019-year file's (140), so no fatal
level-3 cause is missing on the GBD 2023 side. The hierarchy JSONs have no duplicate IDs (377 and 380 unique nodes,
each visited once), so the `walk()` level assignment is unambiguous; the six extra depth-1 nodes are the tool's
"Total cancers / hepatitis / NAFLD" aggregates and are childless, so nothing is misclassified. Cause names are
identical across releases for all 137 IDs; only the Taiwan location name differs (irrelevant, join is on ID).
Non-comparable content despite a shared ID: besides Other neoplasms (median log-ratio +1.39, i.e. ×4.0, 98% of
cells revised up, C2 8%), Other intestinal infectious diseases (+1.01, ×2.7, 76% up, C2 29%), Chagas (+0.31),
Other neurological disorders (+0.22, C2 35%) and Motor neuron disease (+0.22, C2 49%) show systematic shifts
(|median z| > 1). See R-issue 9.

**2. C2 argument.** Correct as stated: with ln p_r = ln θ + e_r, e_r ~ N(0, s_r²) and Corr(e21, e23) = ρ ≥ 0,
Var(e23 − e21) ≤ s21² + s23², so P(|z| ≤ 1.96) ≥ 0.95. Expected C2 under calibration is 0.950 at ρ = 0, 0.992 at
ρ = 0.5, 0.999 at ρ = 0.8 (computed on the actual s's). Mean-of-draws: confirmed by the GBD 2023 appendix
(§4.1.6: "The mean of the draws is used as the final estimate ... a 95% UI is created from the 0·025 and 0·975
quantiles"). Empirically the point estimate sits at median position 0.535 (IQR 0.507-0.579) of its own log-interval
in GBD 2021 and 0.534 in GBD 2023, i.e. mildly above the log-midpoint, as a mean of right-skewed draws would. The
bias this adds to z is (σ23² − σ21²)/2, a difference that largely cancels; X6 (asymmetric half-widths) confirms it is
immaterial. Small counts: C2 is 71.7% for cells with < 1 GBD 2021 death (16% of eligible cells), 77.3% for 1-10,
83.0% for 10-100, 85.5% for 100-1,000 and 86.1% for ≥ 1,000, so small cells pull C2 down but the ≥ 1,000 stratum is
still 9 points short of 95%. Eligibility: 91 cells are C1-eligible but not C2-eligible (60 Measles, 26 Conflict, 5
Malaria: GBD 2023 fixed counts or L23 = 0); their C1 is 15%, so dropping them flatters C2 by < 0.1 point. E1 is
correctly derived but is a floor, not an expectation: 77.9% at ρ = 0, 88.9% at ρ = 0.5, 95.6% at ρ = 0.8. Alternative
formulations: see R4 (distribution-free overlap: 88.6%) and R2 (death-weighted: 76.5%).

**3. Recomputation.** My own two-way pigeonhole bootstrap (independent code, integer resampling rather than
multinomial, same B and seed) reproduces every point estimate exactly and every interval to within Monte Carlo
noise (table in §3). The study's implementation is correct: `bk` (cause multiplicities) is drawn once per replicate
and shared across groups, country multiplicities are drawn within group, cells are weighted by the product, and
both years of a country-cause cell receive the same weight. Decision rules and the headline rule were applied as
preregistered (H1 upper 68.8 < 95 → Supported; H2 high upper 71.8 ≤ 90 → Refuted; H3 upper 84.0 < 95 → Supported;
H4 lower −2.8 < 0 and upper 5.2 ≥ 5 → Inconclusive; headline Inconclusive).

**4. Quality groups.** WHO Table 4.1: pdfplumber on pages 9-14 yields 119 class rows and the study's filter drops
none (I listed every non-header row the filter would discard: there are none). Class thresholds match Table 8.1
(p. 31). Name matching: all 119 matched; "Cyprusf" is a footnote marker correctly aliased. Garbage table: I rendered
appendix page 76 and compared the parse for Albania (1987-89, 1992-2010), Algeria (2005-06), Australia (1980-2018),
China (1991-2002, 2004-17), India and Andorra value by value; all agree with the figure, and China's 2010-21 mean
(9.6%) reproduces. 145 countries parsed, 130 with 2010-21 data, no duplicate country-years. The `none` class is the
problem: see R1.

**5. Timeline and disclosure.** `git log`: plan + build/quality/analysis/synthetic-test committed 6b7a3e2 at
00:07:45 NZDT; results committed f672f50 at 00:15:45. File mtimes: panel 00:07:53, quality 00:07:58, synthetic
tests 00:08:01, crashed first analysis 00:08:05, primary.json 00:08:28, secondary 00:08:30, mixed model/by-tables
00:09:08, tiles 00:13:56, exploratory 00:15:13. `git diff 6b7a3e2 f672f50 -- code/analysis.py` is exactly the
one-line D1 fix; `plan.md` is byte-identical across the commits; `logs/primary_run1.json` equals `primary.json`.
D1 and D2 are accurate. Presentation code (figures.py, build_report_html.py, tiles) was added post hoc but changes
no analysis. Exploratory results are labelled in the Results section but leak unlabelled into the plain-language
summary (R6).

**6. Numbers.** Every figure in `report.md` (verdict table, secondary table, diagnostics, X1-X6, "In plain terms",
"What this means") and all four tiles match `primary.json`, `secondary.csv`, `exploratory.csv` and
`mixed_model.json` after rounding. The by-cause claim (Other neoplasms C2 8%, 7 of 137 causes ≥ 95%, median 84%)
matches `by_cause.csv`.

**7. Interpretation.** See R2-R4, S7-S12.

**8. Data use.** `by_country.csv` holds counts of eligible cells, C1, C2 and public-document covariates (WHO class,
usability midpoint, GBD garbage share); `by_cause.csv` holds counts, C1, C2 and median |z|; `secondary.csv`,
`exploratory.csv`, `primary.json`, `mixed_model.json` and the figures hold shares, differences and ratios only.
`data/` and `logs/` are git-ignored (`.gitignore:135-136`), nothing under them is tracked, and `report.html`
contains no estimate columns. Compliant.

## 2. Issues

### Required before publication

**R1. The `none` class (85 countries) is misdescribed and includes countries with good death registration.**
Location: `plan.md` §4 ("Countries missing from the table have no vital-registration data in the WHO Mortality
Database"), `code/quality.py` docstring, `report.md` "The data" bullet ("85 have no data in the WHO Mortality
Database"). WHO Table 4.1 footnote b says only countries "included in this analysis (see Section 3.1)" are listed,
and Section 3.1 (p. 6) restricts GHE to 183 Member States with population > 90,000 plus Puerto Rico, Taiwan and
Palestine, explicitly excluding Andorra, Cook Islands, Dominica, Marshall Islands, Monaco, Nauru, Niue, Palau, Saint
Kitts and Nevis, San Marino and Tuvalu; non-member territories (Bermuda, Greenland, Guam, American Samoa, Northern
Mariana Islands, US Virgin Islands, Tokelau) are never in scope. Cross-checking the WHO MDB availability list
(`list_ctry_years_feb2026.xls`, national rows, years ≥ 2010) shows San Marino (14 years), Saint Kitts and Nevis
(13), Bermuda (12), Dominica (12), Andorra (10), Cook Islands (3), Papua New Guinea (3) and Botswana (1), plus the
US Virgin Islands under a different name, all have MDB data yet are classed `none`. Taiwan does not report to the
WHO MDB but has complete, well-coded registration (GBD garbage share 15%, per-country C2 91%, higher than the USA's
89%). Of the 85, 17 appear in GBD's own VR garbage-code table (China 9.6%, Bermuda, Saint Kitts, Guam, Taiwan, USVI,
Northern Mariana Islands, San Marino, American Samoa, Andorra, Dominica, Monaco, Cook Islands, Greenland, Palestine,
India 44%, Palau); 68 have no VR in either source. Fix: correct the sentence in plan (as an erratum note), code and
report; name the 17; add to the secondary table the three reclassifications I ran (all cell-weighted, two-way
bootstrap): low = WHO low/very low + 68 no-VR (n = 100): gap +0.9 [−3.3, +5.0]; additionally moving the WHO-none
countries with GBD VR and garbage < 20% to high (n = 69/100): gap −0.3 [−4.5, +3.9]; low = the 68 no-VR only: gap
+0.2 [−4.1, +4.7]. The substantive conclusion (no gradient detectable) survives; two of the three would be
"Refuted" under the preregistered rule.

**R2. The H4 message is a property of equal-cell weighting; death-weighted, the gradient is large.** Location:
`report.md` "What this means" ("Data quality does not explain the shortfall. We expected the opposite, so this may be
the most useful finding"), "In plain terms" ("It was not."). Weighting each cell by its GBD 2021 death count, C2 is
76.5% overall, 89.9% in high, 87.4% in medium and 69.7% in low; the high − low gap is +20.2 points with a
country × cause bootstrap CI of +2.4 to +36.6. This is driven by China and India: 65% of the low group's
death-weighted misses come from ten China/India pairs (stroke, COPD, ischaemic heart disease, COVID-19, diabetes,
oesophageal cancer, road injuries, lower respiratory infections); excluding China and India the low group rises to
83.3%, and the median per-country death-weighted C2 is 91% in high vs 83% in low. Both weightings are legitimate
answers to different questions (is the typical country-cause interval calibrated? vs. are the intervals around
the deaths that matter calibrated?). The report must present the death-weighted result as an alternative
formulation, state that the equal-cell null and the death-weighted gradient coexist, and drop "the most useful
finding" and "It was not." in favour of "we found no gradient when every country-cause counts equally; weighting by
deaths, the data-poor group looks markedly worse, almost entirely because of China and India". Add the analysis to
`exploratory.py` so it is reproducible.

**R3. The H4 label is within Monte Carlo and specification noise, and the report does not say so.** Location:
`report.md` verdict table and opening paragraph ("misses the preregistered 5-point refutation threshold by 0.2").
With the preregistered seed the upper bound is 5.22; my implementation with the same seed gives 5.06; ten other
seeds give 4.98-5.47, two of ten below 5.0 (Refuted); B = 20,000 gives 5.16. The country-only bootstrap, which the
plan lists as the sensitivity check for the interval method but which the report shows only for the overall shares,
gives a gap CI of −1.7 to +4.4 (Refuted). The reclassifications in R1 give upper bounds of 5.0, 3.9 and 4.7. Fix:
add the country-only bootstrap row for the H4 difference to the secondary table; add one sentence after the verdict
table: "The Inconclusive/Refuted boundary lies within bootstrap resampling noise (upper bound 4.98-5.47 across
seeds) and the country-only bootstrap and alternative groupings put it below 5; the substantive reading is that a
gradient of 5 points or more is excluded only at the margin and a gradient near zero is most consistent with the
data."

**R4. Add the distribution-free check and state what the C2 assumptions buy.** Location: `report.md` "Two tests",
"Limitations" (C2 assumptions). If both releases' 95% UIs are calibrated, the truth lies in both with probability ≥
0.90 whatever the error shape or dependence, so the two UIs must overlap at least 90% of the time (equivalently
|ln p23 − ln p21| ≤ h21 + h23 with the facing half-widths). Observed: 88.6% [86.4, 90.7] overall; high 88.2%,
medium 89.1%, low 88.7%; high − low −0.5 [−3.4, +2.5]. The point estimate is below the floor but the CI reaches
it. Under the preregistered assumptions (log-normal, ρ ≥ 0) the expected overlap would be ≥ 99%, so 88.6% is still
strong evidence; but the report currently reads as if H3 were assumption-light. Fix: report the overlap statistic
in the secondary table and say: "A version of the test that needs no distributional or dependence assumption (do
the two intervals overlap? at least 90% if both are calibrated) gives 88.6% (86.4-90.7): below the floor, but not
decisively. The sharper C2 verdict rests on the log-normal and non-negative-correlation assumptions, under which
calibrated intervals would overlap at least 99% of the time."

**R5. Disclose the information content of the 52,000 cells.** Location: `report.md` "In plain terms" ("about
52,000 comparisons"), "The data". 16% of C2-eligible cells (8,364) have fewer than one estimated death in GBD 2021
(fractional deaths, e.g. a rare tropical disease in a small high-income country) and have the lowest C2 (71.7%);
excluding them C2 is 83.2% (n = 43,855), excluding < 10 deaths 84.7%. The two years are near-duplicates: 26,269
country-cause pairs, 91.5% with the same C2 outcome in both years, P(miss in 2021 | miss in 2019) = 84%. The
bootstrap already clusters on country × cause, so the intervals are right, but "52,000 comparisons" overstates
the evidence. Fix: say "about 52,000 cells (26,000 country-cause pairs over two years; 16% of cells have fewer than
one estimated death, and the result holds without them: 83%)".

**R6. Exploratory results appear unlabelled in the summary, and "2.2×" is a log-scale factor.** Location:
`report.md` "In plain terms" ("Most revisions were of about the expected size. The problem is a minority of large
jumps"; "both rounds' ranges would have had to be about twice as wide (2.2×)"), tile 4 note. Both sentences come
from X4 (post hoc, D2). The 2.18 factor scales the combined log-SD; on the natural scale a ±20% interval becomes
−33%/+49% and a ×0.5-×2 interval becomes ×0.22-×4.5, which is not "twice as wide". Fix: prefix "In an exploratory
check," and write "the log-scale spread would need to be about 2.2 times larger (for a ±20% interval, roughly
−33% to +49%)".

### Recommended

**S7. E1 and the tiles.** `tiles.json` tile 1 says "about 78% expected if calibrated"; the report body correctly
says "and independent". E1 is the minimum compatible with calibration (77.9% at ρ = 0; 88.9% at ρ = 0.5; 95.6% at
ρ = 0.8). Change the tile to "at least 78% if calibrated" and add the ρ examples to the E1 diagnostic, which makes
the C1 shortfall look larger, not smaller.

**S8. Cite IHME's own description of the UIs rather than paraphrasing.** `report.md` "IHME's likely reply" says
"GBD describes its intervals as reflecting uncertainty from data, data processing and model choice" without a
source. Usable sources: GBD 2019 diseases-and-injuries paper (Lancet 2020; PMC7567026): UIs capture "stochastic
variation in input data, age and sex splitting of data, corrections for alternative case definitions or uninformed
cause of death codes, other data manipulations, and model choice", and "It remains a challenge to fully represent
the UIs around estimates, particularly in locations with sparse or absent data"; GBD 2023 CoD appendix §4.1.6
(p. 38): "The validity of the UI can be checked via its coverage of the out-of-sample data; ideally, the 95% UI
would capture 95% of these data. Higher coverage suggests that the UIs are too large, and lower coverage suggests
overfitting", and the reduction to 250 draws "from 500 in GBD 2021" (the GBD 2021 appendix itself says 1,000 for
the CODEm ensemble; cite both). The out-of-sample coverage criterion is IHME's own calibration standard and is the
strongest peg for the report's framing; note that it targets held-out data points, not the next round's estimates.
Also cite GBD 2023 appendix §3.8 (83/67/38 country-years of 2020/21/22 VR data; COVID-19 misclassification
correction) and the "additional 312 country-years of new VR data" sentence, which are the basis for the X5 narrative.

**S9. Other intestinal infectious diseases deserves the same treatment as Other neoplasms.** C2 29%, median
revision ×2.7 upward in 76% of cells, second-lowest cause, yet the GBD 2023 appendix section for this cause states
"We have made no substantive changes to the modelling strategy in GBD 2023" (custom binomial model). That is a
revision of a factor of 2.7 with an unchanged model, i.e. data, redistribution or envelope changes the intervals did
not anticipate; it cuts against the "method changes explain the misses" reading and should be said. Extend the
"Same ID, different content" limitation to list the five systematic-shift causes (§1 item 1). Note also that the ten
worst causes account for only 21% of C2 misses (Other neoplasms 3.9%, COVID-19 1.1%), which supports "broad, not
driven by a few causes".

**S10. State the mechanism behind the H4 null.** In this panel the stated log-SD is 2.7× larger in the low group
(median s21 0.200 vs 0.075 in high; 0.109 medium) and the revisions are 3.1× larger (median |ln p23 − ln p21| 0.262
vs 0.084), so uncertainty and revisions scale together. This directly answers Byass et al. (PLOS Med 2013), who
found GBD 2010 intervals "not appreciably wider" in data-sparse regions. Also report that the tail is heavier in
well-registered countries (SD of z 4.2 in high vs 2.5 in low; share |z| > 5 is 3.6-3.8% in every group), which is
the quantitative counterpart of X5's narrative about new VR data and the COVID-19 correction in 2021.

**S11. Make the reply to "rounds are not comparable" concede what it should.** GBD papers say each round
"supersede[s]" the previous one and the UIs are conditional on the current data and model; revisions from bug fixes
(Other neoplasms), new data and recoding are bias corrections that no conditional interval claims to cover. The
report's strongest ground is the one it already states, the user's revision risk, plus IHME's own out-of-sample
coverage criterion (S8). The sentence "In data-rich countries, revisions come from recoding, redistribution of
garbage codes, new years of data and cause-model changes" is plausible but not shown; hedge it ("are likely to").
A demographer would add: all-age both-sex counts mix age-structure and population revisions (the rate secondary
answers the population part only), and WHO's class describes what WHO received, not GBD's inputs (China's DSP and
India's SRS/MCCD are major GBD sources).

**S12. Prior work.** Add Dorrington and Bradshaw, Bull WHO 2016 ("The most recent estimates from IHME and WHO lie
outside the respective 95% uncertainty intervals about their previous estimates", maternal mortality) as the
earliest cross-round interval check, and Byass et al. 2013 (S10). Zavalis, Pezzullo and Ioannidis (JAMA Health Forum
2026; PMC12988449) is correctly characterised: eight GBD iterations, 66 risk factors, global only, 70-96% of GBD 2021
estimates for several dietary risks outside GBD 2019 UIs, no country, cause-of-death or data-quality analysis. The
novelty claim (country × cause, calibration framing, data-quality gradient) holds.

### Minor

**M13. Plan disclosure counts.** `plan.md` says 6 rows outside their own interval in "the GBD 2023 file" and 5 in
GBD 2021. Exact comparison gives 13 in GBD 2023 (7 in the 2019-year file, 6 in the 2021-year file, all Conflict and
terrorism, all rounding of fixed counts, relative excess < 1e-6) and 21 in GBD 2021 (14 COVID-19, 4 Eating
disorders, 3 Conflict), of which 5 exceed 1e-6 relative. State the tolerance used.

**M14. B for secondary analyses.** `analysis.row()` uses b = 1,000; plan §6 says B = 2,000 (§7 is silent). Say so
in the secondary table caption.

**M15. Cosmetics.** `deviations.md` line 6 has a stray ")" ("Plan committed 2026-10-12 00:07 NZDT)"). The X2 count
of 13 "Other ..." causes includes "Other pharynx cancer", which is a site group rather than a residual; harmless but
worth a footnote.

## 3. Recomputed numbers

Shares in %, differences in percentage points. "Study" = `results/tables/`; "Review" = my independent code
(`/tmp/.../scratchpad/recompute.py`, not part of the run). Bootstrap: two-way country × cause, B = 2,000, seed
20261012 unless stated.

| Quantity | Study | Review |
|---|---|---|
| Panel cells / C1-eligible / C2-eligible | 55,896 / 52,310 / 52,219 | 55,896 / 52,310 / 52,219 (rebuilt from zips; all values identical) |
| Shared level-3 IDs | 137 | 137 (139 ∩ 140; cause names identical across releases) |
| C1 overall (H1) | 65.92 [62.84, 68.84] | 65.92 [62.96, 68.79] |
| C1 high / medium / low | 67.36 / 67.38 / 64.86 | 67.36 [63.0, 71.8] / 67.38 / 64.86 [61.2, 68.2] |
| C1 high − low | +2.50 [−2.71, +7.57] | +2.50 [−2.52, +7.58] |
| C2 overall (H3) | 81.40 [78.72, 83.95] | 81.40 [78.80, 83.99] |
| C2 high / medium / low | 82.08 / 82.31 / 80.85 | 82.08 [78.4, 85.6] / 82.31 / 80.85 [77.6, 83.8] |
| H4 gap, preregistered seed | +1.23 [−2.76, +5.22] | +1.23 [−2.70, +5.06] |
| H4 gap, B = 20,000 (seed 123) | — | +1.23 [−2.75, +5.16] |
| H4 upper bound over seeds 1-10 | — | 4.98-5.47; 2 of 10 < 5.0 |
| H4 gap, country-only bootstrap | not reported | +1.23 [−1.68, +4.36] |
| E1 (ρ = 0) / C1 on same cells | 77.93 / 66.01 | 77.93 / 66.01; E1 at ρ = 0.5: 88.9; ρ = 0.8: 95.6 |
| Expected C2 if calibrated, ρ = 0 / 0.5 / 0.8 | ≥ 95 | 95.0 / 99.2 / 99.9 |
| Reversed naive coverage (p21 inside UI23) | — | 70.6 |
| Distribution-free: UIs overlap (floor 90) | — | 88.59 [86.35, 90.68]; high 88.2, medium 89.1, low 88.7; gap −0.5 [−3.4, +2.5] |
| Point-estimate position in own log-UI, median | — | 0.535 (GBD 2021), 0.534 (GBD 2023); 80% of cells > 0.5 |
| C2 by GBD 2021 deaths: < 1 / 1-10 / 10-100 / 100-1,000 / 1,000-10,000 / ≥ 10,000 | — | 71.7 / 77.3 / 83.0 / 85.5 / 86.1 / 86.1 (n = 8,364 / 8,669 / 12,994 / 13,869 / 6,577 / 1,746) |
| C2 excluding < 1 death / < 10 deaths | — / 85.6 (high) 83.8 (low) | 83.2 / 84.7 overall |
| Death-weighted C2: all; high / medium / low | — | 76.5; 89.9 / 87.4 / 69.7; gap +20.2 [+2.4, +36.6]; low excl. China+India 83.3 |
| Reclassified H4 gap: ALT1 / ALT2 / ALT3 (R1) | — | +0.9 [−3.3, +5.0] / −0.3 [−4.5, +3.9] / +0.2 [−4.1, +4.7] |
| Median stated log-SD s21: high / medium / low | — | 0.075 / 0.109 / 0.200 (s23: 0.078 / 0.107 / 0.228) |
| Median absolute log-revision: high / medium / low | — | 0.084 / 0.116 / 0.262 |
| SD of z: all; high / medium / low | 3.10 | 3.10; 4.16 / 2.63 / 2.54 |
| Share of C2 misses from 10 worst causes / Other neoplasms / COVID-19 | — | 21.4 / 3.9 / 1.1 |
| Country-cause pairs; same C2 outcome both years | — | 26,269; 91.5% |
| WHO Table 4.1 rows parsed / dropped by filter | 119 / — | 119 / 0 |
| `none` countries with GBD VR data / with WHO-MDB data ≥ 2010 | 0 implied | 17 / ≥ 8 |
| Garbage parse spot checks (6 countries, 150 country-years vs page image) | — | all agree; China 2010-21 mean 9.6% reproduces |
| Rows outside own UI: GBD 2021 / GBD 2023 | 5 / 6 | 21 (5 material) / 13 (0 material) |
| Verdicts H1 / H2 / H3 / H4 / headline | S / R / S / I / Inconclusive | same, by the preregistered rules |

## 4. Sources consulted outside the run directory

- GBD 2019 diseases and injuries, Lancet 2020, https://pmc.ncbi.nlm.nih.gov/articles/PMC7567026/ (UI definition;
  "supersede" sentence).
- GBD 2021 causes of death, Lancet 2024, https://pmc.ncbi.nlm.nih.gov/articles/PMC11126520 (1,000-draw UIs;
  "supersede all previous GBD cause-of-death publications").
- GBD 2023 causes of death appendix 1 (local copy): §4.1.6 p. 38 (mean of draws; out-of-sample coverage criterion;
  250 vs 500 draws); §3.8 p. 25 (COVID-19 misclassification correction); p. 361 (Other neoplasms CoDCorrect error,
  quote verified verbatim); "no substantive changes" for Other intestinal infectious diseases.
- WHO GHE 2021 methods (local copy): §3.1 p. 6 (183 Member States > 90,000; 11 excluded; Puerto Rico, Taiwan,
  Palestine added); §4.2 p. 7; Table 4.1 pp. 9-14 and footnote b; Table 8.1 p. 31.
- Zavalis, Pezzullo, Ioannidis, JAMA Health Forum 2026, https://pmc.ncbi.nlm.nih.gov/articles/PMC12988449/ and
  medRxiv 10.1101/2025.11.14.25340145.
- Byass et al., Reflections on the GBD 2010 estimates, PLOS Med 2013, https://pmc.ncbi.nlm.nih.gov/articles/PMC3699446
- Dorrington and Bradshaw, Acknowledging uncertainty about maternal mortality estimates, Bull WHO 2016,
  https://pmc.ncbi.nlm.nih.gov/articles/PMC4750434/
