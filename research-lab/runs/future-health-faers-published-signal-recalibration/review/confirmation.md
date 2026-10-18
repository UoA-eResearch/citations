## Confirmation (commit c3516ec, deviation D4)

Checked with `review/reviewer_checks/confirm_d4.py` (eligibility, exclusion and mapping logic; independent re-run of
H1, the joint paper+control bootstrap, the FAERS-only variant and H2 from `data/recomputed.csv`; SQL spot checks of
two `faersonly` cells), plus a reading of the code diff d62a942..c3516ec, the new `primary.json`,
`null_sensitivity.json`, the D4 logs, `report.md`, `report.html` and F3.

### Final verdict: publish with edits

The four "fix first" items are addressed correctly, and every number in the rewritten report matches the tables. The
remaining edits are wording.

### What I verified

- **Exclusions.** None of the 26 known-wrong signals is in the new capped set (0 of 26). `REVIEW_EXCLUDE_PAPERS` /
  `REVIEW_EXCLUDE_SIGNALS` remove 22 extracted ROR rows from 5 papers before mapping; the remaining four known-wrong
  signals (CD, TAC x2, T-DM1) fall to the new rules. Eligible 443, capped 370, papers 132, all 370 recomputed (`status`
  ok). Composition against the reviewed 406: 328 common, 78 dropped (15 found wrong, 18 conjugate rule, 7 abbreviation
  rule, 38 lost the redraw), 42 new.
- **Mapping rules.** `abbreviation()` (shorter than 4 characters, or all capitals/digits/hyphens after stripping
  parentheses) and the conjugate rule (`CONJ` in the paper's string but not in the mapped ingredient) do what D4 says.
  They are conservative: the abbreviation rule also drops CsA (3, correctly mapped to cyclosporine) and "BARICITINIB"
  (1, a drug name in capitals); the conjugate rule drops every sacituzumab govitecan (19 rows) and enfortumab vedotin
  (1) signal, whose mapping to the bare antibody was a correct exposure because neither antibody exists unconjugated.
  Fourteen correctly mapped signals of the reviewed 406 were lost this way. Brentuximab vedotin, polatuzumab vedotin,
  gemtuzumab/inotuzumab ozogamicin and belantamab mafodotin are kept, as they should be. This is a cost of a simple
  rule, not an error, but D4 ("this removes the trastuzumab conjugates") understates it.
- **FAERS-only variant.** `faers_only()` truncates the window start to 2012Q4 and uses the pipeline's deduplicated
  window, so only F-prefixed cases enter; 365 computable, 5 windows end before 2012Q4. For the 119 windows that already
  start at or after 2012Q4 the variant equals the primary (a identical, 119/119); for the 246 earlier windows
  faersonly_a <= primary_a (246/246). My own SQL reproduces two cells exactly (lisinopril–angioedema a = 5,285,
  N = 14,375,662; hydroxychloroquine–pemphigus a = 83, N = 13,688,579). Survival 70.1% (json 0.7014) against 70.7% for
  the same 365 signals under the primary; the boundary is immaterial, as my finding 6 predicted.
- **Null-propagated interval.** `analysis.py` resamples papers and the 190 controls jointly, refits the MLE null in
  each of 2,000 draws, reruns BH inside the draw and counts zero-cell signals as non-survivors. My independent
  implementation (1,000 draws, another seed) gives 0.557–0.817 against the pipeline's 0.571–0.820; the paper-only
  bootstrap 0.648–0.771 against 0.644–0.770. Both agree to seed noise. Under the plan's thresholds the propagated
  interval is Inconclusive, as the report now says.
- **Numbers in report.md against the tables** (all match): 262/370 = 71%, 64–77%, 57–82%; SD null 61% (54–68%);
  uncalibrated 86% (82–91%); 73/69/69%; FAERS-only 70% of 365; "all drugs" label 317, 72% (65–79%); centre-zero 46%
  (36–56%) and the full 4x4 grid; threshold 3.34 / 3.38 / five survivors with a < 3; H2 1.07 (1.01–1.16) on 359;
  57 and 44 beyond 2x (101), 141 (39%) within 0.8–1.25; bands 26/50/81/93%; years 62/66/77%; 17 and 72 of 132 papers;
  108 non-survivors = 11 zero cells + 16 ROR <= 1 + 6 with a < 3 + 12 with lo <= 1 + 63 lost to calibration; 34 pre-2004
  windows; 142 of 332 controls with a = 0; control median ROR 0.38 and fitted centre 0.43; secondary coefficients
  (−0.96, −0.52 per year p = 0.017; −0.63 per log case on 69); pipeline check unchanged (same ten signals, median
  1.00, 8 of 10 within 15%). `report.html` carries the same verdict and figures; F3 shows the two new rows.
- **The verdict and plain-terms text.** "Inconclusive" with the preregistered test stated beside it; "survive" defined
  as recomputed ROR above about 3.35; the controls described as chosen in claims/EHR research; my fresh-sample
  precision (0.90, 0.74–1.00) and label accuracy (0.76) cited; my event-matched nulls and the MedDRA-drift count
  labelled as computed on the pre-review 406; the a = 0 exclusion, combination products, the pre-2004 windows and the
  self-adjudication of round 2 stated. Finding-10 corrections are in.

### Remaining required edits (wording only)

1. **Process section.** "The negative-control mapping and the primary pipeline's code were committed before the
   outputs they produced" is no longer true of D4: `eligible.py`, `recompute.py`, `analysis.py` and `figures.py` were
   edited 19:08–19:16, their outputs written 19:15–19:31, and code and outputs committed together in c3516ec (19:32).
   Add one clause: "D4's code and outputs were committed together after review."
2. **D4 and the eligibility bullet.** State what the two rules removed besides the wrong signals: all sacituzumab
   govitecan and enfortumab vedotin signals (correct exposures, excluded conservatively), CsA and "BARICITINIB";
   14 correctly mapped signals of the reviewed 406 in total. Deviations.md should say "removes the conjugates whose
   RxNorm ingredient is the bare antibody, including sacituzumab govitecan and enfortumab vedotin", not only "the
   trastuzumab conjugates".
3. **Deviations D4** cites "the 39 windows starting before 2004Q1"; after the redraw it is 34 (the report has 34).
   Write "39 before D4, 34 after".
4. **Limitations.** "19 of 313 rejected events would pass with a fuller map" was counted on the pre-review set; the
   non-PT rejections now number 303. Add "(pre-review count)".
5. Optional: one sentence on the redraw's composition (78 of the reviewed 406 dropped, of which 38 only because the
   cap was redrawn; 42 new), so a reader can see that the 26 removals moved more signals than 26.

Nothing else is required. The tag Inconclusive is the right one.
