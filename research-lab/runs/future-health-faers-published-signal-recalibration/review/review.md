# Review: future-health-faers-published-signal-recalibration (pre-review draft d62a942)

Independent adversarial review, 2026-10-18. Everything below was checked against the files in the run directory and
the git history; supporting scripts and their outputs are in `review/reviewer_checks/` (abstract text only under the
gitignored `review/reviewer_checks/cache/`). Scripts: `check_boundary_and_pt_drift.py`, `check_drug_terms.py`,
`check_d3_and_null.py`, `check_coverage_and_spelling.py`, `draw_fresh_sample.py`, `write_adjudication.py`,
`recompute_independent.py`, `pseudo_null.py`.

## Verdict: fix first

The pipeline is honestly built and documented, the git order holds for the primary pipeline (code before outputs; D2
before any recomputation; D3 declared with the as-run results kept), and every number in `report.md` reconciles with
`results/tables/`. My own SQL reproduces the recomputed 2x2 counts (21 of 22 signals identical, the other off by one
report), and my refit of the null reproduces mu = -0.849, sigma = 0.962 exactly.

But the report cannot be published as it stands, for four reasons:

1. About 6% of the 406 analysed signals are demonstrably not what they claim to be (wrong database, wrong drug, or a
   combination/factor estimate attributed to a single drug), and the error modes that D2 was declared to have fixed are
   all still present in the analysed set. On a fresh random sample of 70 eligible signals my precision is 0.90, not
   0.96, and the `comparison` label is right for 76%, not 97%.
2. The H1 verdict "Refuted" rests on a 65% lower bound from an interval that ignores the null's own sampling
   uncertainty. Propagating it gives 59-82%, which is Inconclusive under the plan's thresholds. Under every
   defensible alternative null I tried, the survival share is 32-61%. The preregistered test was passed, but the
   plan's stated assumption that the two null fits bracket the bias failed, and the report's headline should say so
   first, not after the verdict.
3. A preregistered sensitivity analysis (FAERS-only, plan section 3) was never run, and the plan's promise to report
   the pre-2004 windows is not kept in the report.
4. Drug mapping through RxNav's approximate match silently substituted the wrong ingredient for abbreviations
   ("CD" = carbidopa recomputed as pyrimethamine; "TAC" = tacrolimus recomputed as triamcinolone) and conflated the
   trastuzumab antibody-drug conjugates with trastuzumab (seven signals recomputed with the parent antibody's exposure).

None of these is likely to flip the direction of H1 or H2 (removing the known-wrong signals raises survival from 71.2%
to 71.9%; H2 is stable at 1.08), so the fixes are mechanical: correct or drop the wrong signals, fix the mapping, rerun,
restate the validation numbers with intervals, add the missing sensitivity, and rewrite the headline and "In plain
terms". I recommend the verdict tag be **Inconclusive** rather than Refuted, for the reasons in finding 4; if the lab
keeps Refuted as the letter of the preregistration, the first sentence must carry the fragility.

---

## Findings

### 1. Extraction validity: precision is 0.90 on a fresh sample, and the D2 failure modes persist (Major)

**Check.** `draw_fresh_sample.py` drew 20 eligible papers (seed 20261101) from the 96 papers in neither validation
round; they carry 70 eligible signals. I read each abstract against every extracted signal (recall included).
Adjudications are in `fresh_sample_adjudication.csv` (`write_adjudication.py` prints the summary).

**Result (random sample, 70 signals, 20 papers).**
- Extraction precision 63/70 = **0.90** (paper-cluster bootstrap 95% CI 0.74-1.00). The study reports 0.96 (68/71).
  The two are compatible statistically, but the errors are the ones v2 claimed to have fixed:
  - paper 37240654: all five eligible statin signals are **daptomycin + statin combination** estimates (an interaction
    analysis) attributed to the statin alone (prompt v2: "never one component of it");
  - paper 40552159: two of five eligible irinotecan signals (fatigue, hyperammonaemia) are **JADER-specific** estimates
    labelled FAERS.
- Mapping errors on top of extraction: 2/70 (paper 39840315, "TAC" recomputed as triamcinolone; finding 2).
  Extraction and mapping both right: 61/70 = 0.87.
- `comparison` label right for 53/70 = **0.76** (study: 0.97). 17 of the 56 signals labelled "all drugs" are
  comparator- or subgroup-restricted analyses (39840315: paediatric nephrotic-syndrome reports; 37154187: COVID-19
  reports; 39135789: children under 8; 39472591: within HNSCC-treatment reports; plus 40115262 and 39842538 outside
  the random sample). The all-drugs-only sensitivity (n = 354) is therefore contaminated and its 0.97 label accuracy
  is not credible.
- Recall: no single-ingredient PT-level ROR was missed in the 20 abstracts.

**Targeted screen** (`abstract_screen.csv`; not random). Grepping the 142 eligible abstracts for other-database
wording flagged 9 papers (24 signals); reading them found 10 wrong: 40567936 (a **JADER** study throughout, five
signals labelled FAERS), 38936945 (JADER, two signals; this paper was already flagged as JADER in round 1 and v2
still gets it wrong), 40552159 (two, above), 36697083 (an adjusted ROR for dose per body weight within olaparib users,
not a drug-event disproportionality; also a round-1 error type that persists). The combination-wording screen (18
papers, 53 signals) found no misattribution beyond 37240654.

**Known-wrong analysed signals, all samples: 26 of 406 (6.4%) in 13 papers** (15 extraction, 11 mapping; list in
`fresh_sample_adjudication.csv`). Survival among the 15 extraction-wrong signals is 53%; removing all 26 moves H1 from
71.2% to about 72%. The errors do not threaten the direction of H1 but they contradict two claims in the report
("precision 0.96", "comparison label right for 103/106") and deviations.md's reading that D2 fixed the database and
component-attribution errors.

**Note on independence.** Round 2 was adjudicated by the agent that wrote the v2 prompt. Its adjudication is lenient
in a visible way: 39840315-style subgroup analyses were accepted as "all drugs".

**Fix.** Drop or correct the 26 known-wrong signals; re-screen every eligible paper whose abstract names another
database or a combination/regimen (the screen is cheap); report precision with a paper-cluster interval and say that
errors cluster by paper (7 of my 7 extraction errors sit in 2 papers); either re-adjudicate the `comparison` label on
a fresh sample or withdraw the all-drugs-only sensitivity and the 0.97 claim.

### 2. Drug mapping: approximate RxNav matches and ADC conflation put the wrong exposure in the 2x2 (Major)

**Evidence.** `rxnorm.ingredients()` falls back to `approximateTerm` with score >= 60, and takes `related.json?tty=IN`
of whatever rxcui comes back. From `data/rxnav_cache.json` (`check_drug_terms.py`, and the cache dump in my session):
- "CD" (carbidopa in paper 40115262) resolved to rxcui 9010 → **pyrimethamine**; recomputed a = 2, ROR 1.56, published 13.81.
- "TAC" (tacrolimus in paper 39840315) resolved to rxcui 10759/10762 → **triamcinolone**; two signals (kidney fibrosis
  a = 0; diabetic ketoacidosis ROR 0.27, published 46.5).
- "trastuzumab deruxtecan", "trastuzumab emtansine" and "T-DM1" resolve to INs whose `tty=IN` relation is plain
  **trastuzumab** (rxcui 1371041 → trastuzumab). The match terms then include HERCEPTIN and every trastuzumab brand, so
  seven ADC signals in five papers (38100054, 40166653, 40620108, 40770257, 40888754, 41398841) are recomputed with the
  exposure "any trastuzumab product": in paper 40620108 the T-DXd (published 31.3), T-DM1 (6.27) and trastuzumab (4.02)
  ILD signals all receive the identical recomputed ROR 10.68 (`signals_results.csv`, rows for ingredient trastuzumab).
  Rule 3 of the plan ("one active ingredient") is not met in substance.
- The eligibility step adds the paper's own drug string as a match term; "ide-cel", "cilta-cel", "CsA", "Xywav" were
  mapped correctly, but nothing in the code prevents a wrong approximate match from passing.

**Not found.** No temp-table name collisions from the 40-character truncation (321 names, 0 shared by different term
sets). No generic-word brand names among the signals' terms that would plausibly match unrelated drugnames (the
word-boundary regex protects substrings; `drug_terms_used.csv`). Drugname-only matching before 2014Q3 catches 96% of
the PS reports that prod_ai catches for the frequent ingredients (amiodarone 69%, irinotecan 92%, the rest >= 95%;
`drugname_coverage_2012Q4_2016Q2.csv`), so the pre-2014Q3 false-negative rate is modest.

**Fix.** Reject approximate matches for strings shorter than five characters or all-capitals abbreviations; have the
extractor expand abbreviations from the abstract (both papers define them in the Methods sentence); use the IN/PIN of
the exact string for conjugates rather than the parent antibody, or exclude ADCs whose mapping collapses to the parent.
Re-run the 10 affected signals.

### 3. Eligibility and D3: the correction is legitimate and did not help the hypothesis (OK, with two small notes)

**Check** (`check_d3_and_null.py`). D3 moves the PT rule before the cap, as plan section 2 orders. The as-run pass had
659 capped signals of which 279 were later rejected as non-PT (denominator 380); corrected: 495 eligible, 406 capped.
Overlap: 338 (paper, k) pairs in both; 68 new; 43 as-run signals no longer drawn (deviations.md says "69 new": 68 new
plus one whose PT changed under the spelling fix, so it was recomputed; fine). Survival: 72.8% among the common
signals, 63.2% among the new, 67.4% among the dropped (as-run q). D3 lowered the point estimate (72.4% → 71.2%) and
left both verdicts unchanged; it cannot have been chosen to help refute H1, and the as-run results are kept. The
reused rows are bit-identical (337/337).

**Spelling map.** The `(?<!o)` fix is correct. The map is otherwise incomplete in a quantifiable way
(`check_coverage_and_spelling.py`): of the 313 "event not a FAERS PT" rejections, 14 would pass with a fuller map
(hyperprolactinaemia 6, gynaecomastia 5, hypophosphataemia 2, hyperaesthesia 1) and 5 more by stripping
parentheses/hyphens (headache(s) 3, angle-closure glaucoma 2). `color`→`colour` and `fetal`→`foetal` fire on
non-medical phrases ("fetal complications"), and the entry `(r"neutropeni", "neutropeni")` is a no-op. The report's
"e.g." should give the count: 19 of 313, no detectable direction of bias. Minor.

**Timing note.** `data/signals_eligible.csv` was written at 18:11:45, twenty seconds before the D3 commit (18:12:05).
The code content is the committed content, so this is immaterial, but see finding 10 on the report's wording.

### 4. H1 inference: the "Refuted" verdict is not robust to the null's own uncertainty, and "survive" means ROR > 3.35 (Major)

**Checks** (`check_d3_and_null.py`).
- Independent recomputation of the pipeline's numbers: 289/406 survive; paper-cluster bootstrap 0.655-0.769 (report
  0.653-0.768). BH re-run inside each bootstrap resample: 0.638-0.768. H2 median 1.079, n = 392. All reproduce.
- **Null uncertainty propagated.** Resampling the 190 controls with the papers and refitting the null in each resample
  gives **0.593-0.816**. The profile-likelihood 95% CI for mu alone is -1.01 to -0.69; at mu = -0.69 with the fitted
  sigma, survival is about 67%. The plan's decision rule compares a bootstrap bound with 0.60; it specifies a paper
  bootstrap and is silent on the null, so the pipeline followed the plan. But the interval it reports is the wrong
  width for the claim it supports, and under the plan's own thresholds the propagated interval is Inconclusive.
- **What the calibrated test actually is.** Because sigma (0.96) dwarfs every signal's se, the calibrated p is almost a
  deterministic function of log ROR: the smallest surviving recomputed ROR is 3.34 and the largest non-surviving ROR
  with a >= 3 is 3.39. "Survive" therefore means "recomputed primary-suspect ROR above about 3.35 (and q < 0.05)". The
  5 survivors with a = 1 or 2 are a consequence. At mu = 0 the threshold would be about 7. The report should say this
  in the Results and in "In plain terms"; "allowed for the background noise" does not convey an effect-size threshold.
- NaN handling is right: all 14 zero-cell signals have a = 0 (one also c = 0), so counting them as non-survivors is
  correct; BH runs over the 392 finite p-values rather than "all eligible signals" as the plan says. State it.
- Cluster bootstrap and H2 ratio: implemented as written; H2 is not sensitive to anything I changed.

**Fix.** Report the null-propagated interval next to the preregistered one; lead the verdict section with the
threshold interpretation; retag the lead Inconclusive (or keep Refuted with the first sentence stating that the
preregistered interval excludes the null's uncertainty and that the bracketing assumption of plan section 7 failed).

### 5. The null: reproduced, not a mapping artefact, but a single global centre is a crude summary and the 43% zero-cell exclusion biases it (Major)

**Reproduction.** MLE mu = -0.8489, sigma = 0.9621 (report: -0.8489, 0.9621); sample mean -0.921, SD 1.124, median
log ROR -0.973 (exp 0.378). 14 controls uncalibrated-positive, 91 uncalibrated-negative (hi < 1): the controls are not
noisy around zero, they sit below it.

**Why it is centred below zero** (`check_d3_and_null.py`, `pseudo_null.py`).
- Not the PT mapping: the mapping table is reasonable, and the centre is broad, not driven by a few PTs
  (leave-one-PT-out mu range -0.91 to -0.79; leave-one-drug-out -0.91 to -0.76).
- Not mainly the chronic-indication outcomes: my split into acute-type PTs (pancreatitis acute, GI haemorrhage, CVA,
  bronchitis, ...; n = 106) and chronic/indication-type PTs (n = 84) gives mu = -0.73 and -1.01. Both are far below 0.
- It is a property of the primary-suspect ROR for unrelated pairs. Drug explains more of the variance than PT
  (one-way R² 0.55 by drug, 0.39 by PT; two-way 0.84). Drugs with many PS reports sit lower (Spearman of log b with the
  drug's mean log ROR -0.45, p < 1e-4) and events with a large background count sit lower (log c, -0.48, p = 1e-4).
  A drug named as primary suspect carries the events it is suspected of; an unrelated event appears in its PS reports
  only incidentally, so the null odds are below 1 and depend on how concentrated the event is in other drugs.
- **The a >= 1 restriction is a bias.** 142 of 332 designated pairs (43%) have a = 0 and are dropped (plan section 4).
  These are the most negative pairs; dropping them pulls mu toward zero. The report should state that the fitted centre
  is, if anything, too high for the designated set, and that the plan's rule was a choice (Schuemie's method can carry
  a = 0 pairs through the likelihood).

**Is it appropriate to calibrate the published signals against it?** Partly. The protocol is the same for controls
and signals, so the centre is the right correction for "an unrelated pair under this protocol" on average. But the
by-event heterogeneity is enormous and the designated controls' outcomes are not the published signals' outcomes.
Exploratory check (`pseudo_null.py`, contaminated by true associations and indication-as-event pairs, so read the
trimmed and median figures): pairing the 119 control drugs with the 231 published-signal PTs gives 12,236 pairs with
a >= 1, MLE centre -0.16 (sigma 1.24), median -0.24, centre after trimming the top decile -0.42 (sigma 0.93); 22% of
pairs are uncalibrated-positive, which shows the contamination. Per event (218 PTs with >= 5 pairs) the median centre
ranges from -2.5 (injection site pain, COVID-19, plasma cell myeloma, disease progression, myelosuppression, death) to
above +2 for rare PTs where a >= 1 selection dominates; 92 of 218 (42%) are above zero. H1 under these alternatives:
32% (pooled MLE), 61% (trimmed), 38% (event-specific centres with pooled sigma). The same cross-product restricted to
the OHDSI outcome PTs (2,084 pairs, not only the 332 designated) gives -0.16 / -0.43 trimmed, i.e. the designated
pairs are much more negative than the cross-product of the same drugs and outcomes.

**Conclusion.** The study's own sensitivity table (71% → 45% at centre 0) understates the problem: every defensible
alternative null I can construct puts survival between 32% and 61%, and the designated-pair null is the most lenient
of them. The plan's section 7 premise ("the two null fits bracket this") failed, as the report admits. That is the
basis for recommending Inconclusive in finding 4. The plain-terms phrase "pairs that are known to be unrelated" should
read "pairs chosen as unrelated in insurance-claims and electronic-record research".

### 6. Deduplication across the 2012 boundary and pre-2004 windows: immaterial for the RORs, but a preregistered analysis is missing (Moderate)

**Check** (`check_boundary_and_pt_drift.py`, `recompute_independent.py`). The pipeline prefixes caseid with L/F, so
the same case number is never deduplicated across 2012Q3/2012Q4. 82,342 case numbers appear in both legacy and FAERS
(2.7% of 3.09 M legacy cases; 23% of legacy cases whose last legacy version is 2012Q3, 9.5% for 2012Q2;
`boundary_overlap_by_quarter.csv`). Treating them as one case changes the window total by about 0.5% and the
recomputed RORs of my 22 signals by at most 7% (lanreotide 15.7 → 16.3, tenofovir 38.1 → 40.8, ipilimumab 951 → 934;
`recompute_independent.csv`). No survival status would change among them.

**Missing.** Plan section 3 promises "a FAERS-only sensitivity analysis" for the boundary; `grep` finds none in the
code, tables or report. Plan D2 promised to report how many windows start before 2004Q1; `primary.json` has 39, the
report does not mention it (the string comparison on quarters handles them correctly, recomputing from 2004Q1). Both
should be added, however small.

### 7. MedDRA version drift undercounts a and c for 48 signals; not stated (Moderate)

**Check** (`pt_version_drift.csv`). FAERS quarterly files are coded in the MedDRA version current at release and
never recoded. For 47 of 406 signals the PT does not appear in any quarter before the window starts, and for 2 it
disappears before the window ends. Examples: ACUTE KIDNEY INJURY first appears 2013Q1 (RENAL FAILURE ACUTE until
2020Q3); ANGIOEDEMA 2007Q1 (ANGIONEUROTIC OEDEMA before); MYELOSUPPRESSION 2020Q3; SEIZURE 2013Q1 (CONVULSION
before); DRUG ADMINISTRATION ERROR retired 2020Q3 (PRODUCT ADMINISTRATION ERROR from 2018Q2); PNEUMOCYSTIS JIROVECII
PNEUMONIA 2013Q1. Papers that recode to a current MedDRA version will count reports the recomputation misses
(methotrexate–myelosuppression 1997-2019 recomputes as a = c = 0; ruxolitinib–myelosuppression 2014-2024 as ROR 0.92
against a published 4.7). Survival among the affected 48 is 73% versus 71%, so there is no net bias, but it is a
protocol limitation that explains part of the ratio spread and belongs in the limitations.

### 8. Recomputation protocol: reproduced; the combination-product choice should be stated (Moderate)

**Check** (`recompute_independent.py`, my own SQL for 22 signals spanning legacy-era and prod_ai-era windows, brand-
heavy drugs, ADCs, the pipeline-check outliers and the tiny-a survivors). `a` identical to the pipeline for 21/22
(lisinopril–angioedema 6,848 vs 6,847: a dedup tie), `b` within a handful of reports (my grouping differs slightly),
RORs identical to two decimals. The pipeline-check outliers hold under my SQL too: hydroxychloroquine–pemphigus a = 84
PS versus 1,545 published (the paper counted any role; the pemphigus cluster lists hydroxychloroquine as co-suspect),
teprotumumab–eyelid retraction a = 0 in 2023 with only 4 such reports in FAERS that year.

**Combination products.** The word-bounded regex on prod_ai matches "EMTRICITABINE\TENOFOVIR ..." as tenofovir
exposure. That is a defensible reading of "one active ingredient", but it is a protocol choice with material effect
for some ingredients: excluding products whose prod_ai contains a backslash moves tenofovir–vitamin D deficiency from
a = 1,144 to 373 (ROR 38 → 33), levonorgestrel–meningioma 215 → 161 (18.2 → 13.7), oxybate–nephrolithiasis 796 → 681,
lisinopril–angioedema 6,847 → 6,458. Survival does not change for these, but the choice should be written into the
protocol description, since many papers exclude combination products.

**Other variants.** "Full window" ends at the quarter before `firstPublicationDate`, which for a few papers is earlier
than the paper's own window end; harmless but worth a sentence. No-dedup and all-suspect variants are as described.

### 9. Secondary models and variants: as reported (OK)

The logistic models reproduce (`primary.json`); the year coefficient's direction is read correctly; the case-count
model's n = 72 is right. One of the 72 published case counts is a total event count rather than the drug-event count
(paper 39472591, n = 40 "cases of hypertension" overall); it does not reach the pipeline-check top 10.

### 10. The report: numbers reconcile; several sentences overstate (Minor, but several)

Every quantitative statement I checked matches the tables (289/406; 65-77%; 63% 56-69%; 87%; 74/70/69%; 354 and 72%;
1.08 1.04-1.16 on 392; 119 beyond 2x; 151 within 0.8-1.25; 69 and 50; 29/48/82/92% by published-ROR band; 67/67/76% by
year; 18 and 76 papers; 14 zero cells, 16 ROR <= 1, 5 with a < 3, 13 with lo <= 1, 69 lost to calibration; 190 of 332
controls; 14 uncalibrated-positive controls; pipeline-check median 1.00 with 8 of 10 within 15%; 24.8 M report
versions; grid values). Corrections:

- "a median control ROR of about 0.43": 0.43 is exp(mu_MLE); the median control ROR is 0.38. Say "the fitted centre".
- "The negative-control mapping and all pipeline code were committed before the outputs they produced": true for the
  primary pipeline, not for `null_sensitivity.py` (written 18:17, output 18:21), the 18:22 revision of `figures.py`, or
  `build_report_html.py`, all committed with their outputs at 18:24 (d62a942); and the D3 eligibility output precedes
  the D3 commit by 20 s. Rewrite as "the primary pipeline's code".
- "Precision 0.96 ... so a small share of the 406 may be mis-extracted": give the fresh-sample figure and the 26 known
  wrong (finding 1), and say the D2 error types persist.
- "The `comparison` label is right for 103/106": withdraw or re-check (finding 1).
- "Survive" is never defined as the effect-size threshold it is (finding 4).
- "In plain terms": "pairs that are known to be unrelated" (finding 5); "About 7 in 10 flags held up" should be
  followed immediately by what held up means (recomputed ROR above about 3.3) and by the 32-61% range under other
  nulls, not only the centre-zero figure; the one-protocol, notoriety-bias and not-incidence limitations are stated
  plainly and well.
- Deviations D3: "69 are new" is 68 new plus one re-keyed by the spelling fix; a clause suffices.
- The plan's pre-check count (2,228) and the run's hit count (2,265) differ; a footnote.

### 11. Process (OK)

Plan committed 08:35 before any extraction; code for RxNorm/eligibility/recompute/analysis committed 08:46, extraction
v1 finished 10:27; DuckDB built 14:07; D2 declared 15:02 with the round-2 sample file written at 15:02:14, eight
seconds before the commit and before any v2 output; D2 outcome 15:27; negative controls computed 15:49; as-run signals
17:51; D3 committed 18:12 with as-run results kept; corrected analysis 18:19. The extraction validation was
self-adjudicated (finding 1). The vLLM server was not used by this review.

## What I would need to see before publication

1. The 26 known-wrong signals removed or corrected, the mapping fixed (finding 2), the pipeline rerun from
   `eligible.py`, and the validation section rewritten with my fresh-sample numbers beside the study's, each with a
   paper-cluster interval.
2. The `comparison` label re-adjudicated or the all-drugs-only sensitivity withdrawn.
3. The null-propagated H1 interval and the ROR-threshold reading of "survive" in the Results; the verdict reworded
   (Inconclusive recommended) and the "In plain terms" paragraph revised accordingly.
4. The FAERS-only sensitivity, the pre-2004 window count, the a >= 1 exclusion, MedDRA drift and the combination-product
   choice added to methods/limitations.
5. The wording corrections in finding 10.
