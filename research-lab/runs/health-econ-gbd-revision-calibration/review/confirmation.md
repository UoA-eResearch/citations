# Confirmation pass: commit 15825ae (review edits, D3)

Reviewer: same independent reviewer as `review.md`, 12 October 2026. Checked against `results/tables/review_checks.csv`,
`none_class_audit.csv`, `exploratory.csv`, `secondary.csv`, `primary.json`, the raw files, the GBD 2023 appendix
text and the GBD 2019 paper. No GBD estimates are reproduced here.

## Recommendation: **publish with edits** (two wording fixes required, one minor)

R1-R6 are all addressed, and every number in the rewritten `report.md`, the tiles and the figure caption matches the
results files. The remaining problems are two sentences that overstate what the new numbers show, both in prominent
places (the verdict bullets, the plain-language summary and the figure caption). They are text-only fixes; one needs
a single extra row in the review-requested table.

## 1. R1-R6 status

| Issue | Status | Where |
|---|---|---|
| R1 `none` class | Addressed. Erratum appended to plan.md (preregistered text untouched), quality.py docstring corrected, class renamed "not assessed in WHO Table 4.1", `none_class_audit.csv` lists all 85 with GBD-VR and WHO-MDB flags, three alternative groupings reported with CIs, limitation rewritten. The 27 (any year) vs 17 (2010-21) counts are both disclosed. Groupings 59/100, 69/100, 59/68 match mine. | report.md "The data", "Review-requested analyses", "Limitations"; deviations.md D3 |
| R2 death weighting | Addressed. Death-weighted C2 overall and by group with two-way bootstrap CIs, gap +20.2 (+2.1 to +37.2), low without China/India, share of misses, per-country medians; added to the figure as grey squares; "It was not" and "the most useful finding" removed; both weightings framed as answers to different questions. One overstatement remains (issue 1 below). | verdict bullet 3, "In plain terms", review table, "Why the death-weighted gap is large", figure |
| R3 H4 fragility | Addressed. Paragraph "The H4 label is fragile"; country-only bootstrap for the gap (−1.8 to +4.1), seeds 1-10 (4.9-5.4, one below 5), B = 20,000 (5.3). | report.md after the verdict table; review table |
| R4 distribution-free check | Addressed. Overlap 88.6% (86.2-90.6) with by-group values and gap; expected C1/C2/overlap at ρ = 0, 0.5, 0.8; "The sharp H3 verdict therefore rests on..." sentence; limitation. | "Two tests, and what they assume"; "What this means"; "Limitations" |
| R5 cell information | Addressed. 26,000 pairs, 91.5% same outcome, 16% sub-1-death cells, C2 83.2% (80.7-85.5) without them, size strata. | "In plain terms", "The data", review table, "Limitations" |
| R6 exploratory labelling | Addressed. "In an exploratory follow-up" prefix; 2.2× stated as log-scale with a correct natural-scale example (−17%/+20% → −33%/+49%; I recomputed: exp(±0.182) and exp(±0.397)). | "In plain terms", X4 |
| S7-S12, M13-M15 | Addressed: tiles say "at least 78% if calibrated"; GBD 2019 quote verified verbatim against PMC7567026 ("...capture uncertainty from stochastic variation in input data, age and sex splitting of data, corrections for alternative case definitions or uninformative cause of death codes, other data manipulations, and model choice, it remains a challenge to fully represent the UIs around estimates, particularly in locations with sparse or absent data"); GBD 2023 appendix §4.1.6 quote verified (PDF p. 40); Other neoplasms quote verified (PDF p. 361); "no substantive changes to the modelling strategy in GBD 2023" for Other intestinal infectious diseases verified (PDF p. 634, repeated p. 635); mechanism paragraph present (one overstatement, issue 2); IHME reply concedes conditional intervals and bias corrections; Dorrington & Bradshaw and Byass cited with verified quotes; secondary caption says 1,000 draws; own-interval counts corrected (21/5 and 13/0); stray ")" fixed; "Other pharynx cancer" footnoted. | throughout |

## 2. Remaining issues

**1. (Required) "Almost entirely China and India" overstates the study's own numbers.** Locations: verdict bullet 3
("That gap is almost entirely large revisions to major causes in China and India"); "In plain terms" ("That is almost
all China and India"); `results/figures/coverage_by_group.txt` and `code/figures.py` caption ("almost entirely because
of large revisions to major causes in China and India"); "What this means" last paragraph ("the picture differs,
because GBD 2023 moved several of China's and India's largest causes..."). The table reports that without China and
India the low group's death-weighted C2 rises from 69.7% to 83.3%, but does not report the gap. I bootstrapped it
with the study's own `review_checks.boot` (same seed): **high − low excluding China and India = +6.7 points (−0.7 to
+13.4)**. Dropping the two countries removes 67% of the +20.2 gap, not almost all of it; they hold 55% of the low
group's death weight and 75% of its weighted misses. Fix: change "almost entirely" / "almost all" to "mostly: about
two-thirds of the gap, and a residual gap of about 7 points (−1 to +13) remains"; add the row "Death-weighted gap,
high − low, excluding China and India: +6.7 (−0.7 to +13.4)" to the review-requested table and to
`review_checks.py`; in the plain-language summary say "Most of that is China and India, where ...".

**2. (Required) The tail sentence ties the high group's heavy tail to 2021, but it is present in both years.**
Location: "Why the cell-weighted gap is near zero", sentences "The heaviest tail of revisions is in well-registered
countries (SD of z 4.2). In the 2021 data year that matches the arrival of new registration data and GBD 2023's
COVID-19 misclassification correction (GBD 2023 appendix §3.8)." By group × year, the SD of z in the high group is
4.23 in 2019 and 4.09 in 2021 (low: 2.70 and 2.38; medium: 2.75 and 2.49), so the extreme standardised revisions in
well-registered countries are not a 2021 phenomenon, and the share of cells beyond |z| > 5 is the same in every
group (3.6-3.8%; by year 3.2-4.5%). "Heaviest tail" also reads as "more frequent large misses", whereas the data show
the same frequency with larger magnitudes, as expected when intervals are narrow. What does differ by year is the C2
share itself (high group 85.5% in 2019 vs 78.7% in 2021, X5), which is what coincides with the new VR data and the
COVID-19 correction. Fix: "The most extreme standardised revisions occur in well-registered countries (SD of z 4.2
against 2.5), in both years, because their intervals are narrow; the share of cells beyond |z| > 5 is the same in
every group (3.6-3.8%). The high group's lower coverage in 2021 (78.7% against 85.5% in 2019; X5) coincides with
the 2020-22 registration data and the COVID-19 misclassification correction that GBD 2023 added (appendix §3.8), but
this study does not show that link."

**3. (Minor) Zavalis et al. sentence.** Location: "Precedents". "found this for global risk-factor burden across
eight GBD rounds" conflates their two analyses: the eight rounds (2010-2023) feed the instability (range-to-mean,
coefficient-of-variation) analysis; the outside-the-earlier-UI finding (70-96% of several dietary-risk estimates)
is GBD 2021 point estimates against GBD 2019 intervals. Suggested: "found the same between recent rounds for global
risk-factor burden (eight rounds for instability; GBD 2021 estimates against GBD 2019 intervals)".

## 3. Numbers checked (report.md and tiles vs results files)

All of the following match after rounding: 26,000 pairs (25,950 eligible in both years), 91.5% same outcome, 16%
sub-1-death (8,364 / 52,219), 83% without them (83.2%, 80.7-85.5, n = 43,855); 17 and 9 `none` countries with GBD
VR / WHO MDB data, 10 moved to high in ALT2 (China 9.6, Bermuda 10.6, Saint Kitts 10.9, Guam 10.9, Taiwan 15.4,
USVI 15.5, Northern Mariana 17.7, San Marino 18.0, American Samoa 18.75, Andorra 19.2, all < 20); E1 floor 77.9 /
88.9 / 95.6 at ρ = 0 / 0.5 / 0.8; C2 99.2% at ρ = 0.5; overlap 88.6 (86.2-90.6), high 88.2, medium 89.1, low 88.7,
gap −0.4 (−3.4 to +2.5), expected overlap 99.3% at ρ = 0; H4 seeds 4.9-5.4 with one below 5, B = 20,000 → 5.3,
country-only −1.8 to +4.1; ALT1 +0.9 (−3.1 to +4.9), ALT2 −0.2 (−4.4 to +3.7), ALT3 +0.2 (−4.2 to +4.6);
death-weighted 76.5 (62.9-90.3), high 89.9 (79.5-95.3), medium 87.4, low 69.7 (52.8-87.9), gap +20.2 (+2.1 to
+37.2), low without China/India 83.3 (74.4-90.4), 75% / 65% / ten of ten, per-country medians 91.4 / 83.1; size
strata 71.7 / 77.3 / 83.0 / 85.5 / 86.1 / 86.1; s21 medians 0.075 / 0.109 / 0.200 (ratio 2.7), revision medians
0.084 / 0.116 / 0.262 (ratio 3.1); SD of z 4.16 / 2.63 / 2.54, |z| > 5 3.8 / 3.8 / 3.6%; Other neoplasms ×4.0 and
98% up, Other intestinal ×2.7 and 76% up; ten lowest-C2 causes 18% of misses, 3.9 / 3.0 / 1.1%; own-interval rows
21 (5) and 13 (0); X4 natural-scale example; tiles ("at least 78% if calibrated", "no cell-weighted quality
gradient"); figure caption numbers (70%). The figure renders correctly with the death-weighted squares and the C1
floor in the legend. `report.html` was regenerated (contains the new strings). Appendix page citations: p. 361
(CoDCorrect quote), p. 634 (Other intestinal, repeated on p. 635), §4.1.6 (PDF p. 40). `deviations.md` D3 and the
plan erratum are accurate; the preregistered plan text is otherwise byte-identical.

New numbers from this pass (not in the results files; add to `review_checks.py` if used): death-weighted gap
excluding China and India +6.7 (−0.7 to +13.4); share of the full gap removed by excluding them 67%; China + India
share of the low group's death weight 55%; SD of z by group × year: high 4.23 / 4.09, medium 2.75 / 2.49, low
2.70 / 2.38 (2019 / 2021); share |z| > 5 by group × year: 3.2 / 4.3, 3.1 / 4.5, 3.6 / 3.6%.
