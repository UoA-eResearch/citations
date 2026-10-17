# Deviations log

Every departure from the lead and from plan.md, timestamped with `date` when it was made.

## D1 — 2026-10-17 15:51 NZDT — before any statistic was extracted

1. **Linkage routes are not independent.** Europe PMC's "Preprint of" links say "CrossRef Pre-print loader";
   PreprintToPaper's "Published" label is bioRxiv's own link; Crossref's is-preprint-of on bioRxiv DOIs is deposited
   by bioRxiv ("asserted-by subject"). The lead's ">= 2 of 4 routes" would mostly count one assertion twice. Every
   server-asserted link is instead confirmed by an independent title-similarity check (Jaccard >= 0.5): 28,597 of
   31,261 candidates pass.
2. **Version.** 57% of usable pairs have no version in Europe PMC; Research Square DOIs encode it (/vN), bioRxiv and
   medRxiv DOIs do not. The primary uses pairs known to be version 1 (about 11,500); all 23,220 pairs are a labelled
   sensitivity.
3. **No embedding model** for alignment residue; masked TF-IDF plus exact tuple matching, validated blind (plan 6).
4. **Bulk route note.** The bioRxiv /pubs route is slow (~6 s per 100 links) and was still running when linkage was
   confirmed; Crossref carries the same bioRxiv-deposited links, so its absence changes few pairs. If it finishes before
   the pipeline, confirm is not re-run (the pair set is fixed here).
5. **Validation by the agent, not a human**, as plan section 6 states, blind to version order and stratum.

## D2 — 2026-10-17 15:58 NZDT — after the validation was adjudicated, before analysis.py was run

1. **Validation display changed before adjudication began.** The first draw showed the two sentences but not which
   statistic in each had been aligned, so a sentence holding several p-values could not be judged. The display now
   shows the aligned statistic for each side. The redraw used the same seed and produced an identical sample and order
   (`key.csv` compared byte for byte with `cmp`); no item had been judged before the change.
2. **Outcome: the abort rule triggers.** 200 blind pairs were adjudicated (`results/tables/alignment_validation_raw.csv`,
   merged with the key in `alignment_validation.csv`). Precision among crossings is **12 of 100 (0.12)**, far below
   0.90; among other aligned pairs it is 79 of 100. Per plan section 6, H1 is tested on exact tuple matches only and
   the all-crossings estimate is reported as unreliable.
3. **Why crossings fail.** Most failures are alignment: in tables, figure legends and sentences with several p-values,
   the right sentence is found but the wrong p within it, or a dropped row shifts every later cell. About a fifth are
   extraction errors that manufacture a crossing on one side: mojibake exponents ("1.0Ã10â5" read as p = 1 or as the
   mantissa), middle-dot decimals ("p=0·76" read as p = 0), comma decimals ("p=0,33"), partial eta squared read as p,
   and lost exponents. Because a crossing needs a change in status, it selects for exactly these errors.
4. **One adjudication corrected on re-check** (v072, the wrong p in the same sentence, 1 → 0) before any statistic was
   computed. Adjudication is by the agent, not a human (D1.5).
5. **Disclosure.** After the adjudications were written and before this commit, I printed the class tally by match type
   over all versions (not the v1 primary): exact tuple matches give 8 crossings up and 5 down; similarity matches 1,490
   up and 1,437 down. This shows the direction of the exact subset before `analysis.py` ran. The analysis and its
   verdict rule are fixed in the committed code and are not changed by it. With at most 13 exact crossings, the
   primary is expected to be too imprecise for a Supported or Refuted verdict.

## D3 — 2026-10-17 15:59 NZDT — after analysis.py ran; before any v2 code was written

`analysis.py` (results/tables/primary.json) ran as committed. Under the abort rule the primary is the exact tuple
subset of the v1 population: **4 crossings, 1 up (0.25)**; the paper bootstrap gives [0.00, 0.50], so the
preregistered rule mechanically returns Refuted. All crossings (unreliable, precision 0.12): 1,411 crossings in 514
papers, 0.489 [0.453, 0.526].

1. **The primary is reported as Inconclusive, not Refuted.** A percentile bootstrap over four statistics is not a 95%
   interval: it can take only a handful of values. The exact (Clopper–Pearson) interval for 1 of 4 is [0.006, 0.806],
   which includes 0.67. Four crossings cannot refute a 2:1 ratchet. This departs from the mechanical rule in the
   conservative direction. From here on, whenever a share rests on fewer than 30 crossings, the exact interval is
   reported alongside the bootstrap and the wider one decides.
2. **A labelled exploratory v2, specified here before it is built or run.** The validation found two fixable causes,
   so v2 repairs them and adds a strict crossing definition. It is reported as exploratory, never as the
   preregistered test.
   - **Extraction (code/extract_v2.py):** text is repaired with `ftfy.fix_text` (mojibake: "Ã\x9710â\x88\x925" →
     "×10−5"). A middle dot between digits becomes a decimal point. A comma directly after a p comparator and its
     integer part ("p = 0,33") becomes a decimal point. A "p" preceded by any word character or ² (η²p, ηp2, ω²p) is
     not a p-value. A mantissa followed by "×10" with no exponent ("p=1x10") is undetermined. The tuple regex,
     significance rule and sentence splitter are unchanged.
   - **Alignment (code/pipeline_v2.py):** align.py unchanged (SIM_MIN 0.6). Each statistic also keeps its rank within
     its sentence, the number of statistics in that sentence, and its matched text.
   - **Strict crossing (code/analysis_v2.py):** an aligned crossing counts only if (a) both sides are in the abstract
     or the results text, so no tables and no figure legends; (b) it is an exact tuple match or the masked sentence
     cosine is ≥ 0.80; (c) both sentences hold the same number of statistics and the pair has the same rank in each;
     (d) neither sentence defines significance stars (`*p < 0.05`, `p < 0.05 (*)` style).
   - **Fresh blind validation (code/validate_v2.py):** up to 100 strict crossings and 50 strict non-crossings, seeded,
     in random order. Version order and stratum are hidden, and the aligned statistic is marked in each sentence (the
     v1 display showed only its value, which caused the v072 error).
   - **Decision for v2:** if precision among strict crossings is ≥ 0.90, the strict share up in the v1 population (paper
     bootstrap, plus the exact interval if n < 30) is reported as the exploratory estimate and read against the plan's
     thresholds (≥ 0.67 with lower end > 0.50 would be ratchet-like; upper end < 0.67 would be against it). If < 0.90,
     only the validated-correct crossings are reported, by direction, and v2 is inconclusive.
   - S1 (dropped vs added) is recomputed on the v2 extraction as a robustness check.

## D4 — 2026-10-17 16:09 NZDT — after the v2 validation was adjudicated, before analysis_v2.py was run

1. **v2 blind validation.** The strict rule leaves only 64 crossings in the v1 population, so the sample is all 64
   (a census) plus 50 strict non-crossings. Precision among strict crossings is **42 of 64 (0.66)**, against 50 of 50
   for non-crossings. Under D3's decision rule, v2 is inconclusive and only the validated-correct crossings are
   reported, by direction.
2. **What still fails under the strict rule:** reordered lists, where the same sentence lists the same items in a
   different order, so the same rank is a different item (8); fragments too short to identify the comparison (5,
   "CLP + E-5, p = …; vs."); typos and broken decimals read literally ("P=001", "p =0. 07"); and different statistics
   in near-identical sentences. Several correct crossings are themselves corrections ("p = .46" → "p = 0.046"), and two
   are three values that appear permuted across labels (w024, w090), so even a correct alignment does not always mean
   a changed result.
3. Because the 64 strict crossings were adjudicated in full, the 42 correct ones are every verified strict crossing in
   the v1 population. Their direction is reported with an exact interval as a descriptive, exploratory result; they
   are not a random sample of all true crossings (the strict rule selects text-only, same-structure sentences).

## D5 — 2026-10-17 17:04 NZDT — response to the adversarial review (fix first, 20 issues)

The review (`review/review.md`, Fable 5.1) found that the verdict stands but the draft overstated several things.
`code/review_response.py` computes every new number (`results/tables/review_response.json`).

1. **The preregistered fallback is mostly artefacts.** Of the 4 exact-tuple crossings in the version-1 population:
   - two are the same df-less `r = 0.092` matched to the other's partner;
   - one is the typo `p = 0.0.46` read as p = 0;
   - one is real: F(2,40) = 2.42, p = 0.004 → p = 0.101, a correction, down.

   Across all versions, 10 of 13 exact crossings have no df and 8 have p = 0 or 1 on one side. 5,232 of 10,031
   exact matches have no df. The verdict line now states the mechanical outcome and why it is not credited.
2. **Verified crossings re-based.** Each verified crossing is coded explicitly (`results/tables/verified_coding.csv`)
   as one of:
   - a changed result (new data, re-analysis, or reason not stated);
   - a correction or typo (a value that contradicts its own sentence);
   - relabelled values;
   - a duplicate.

   The coding was done **after unblinding**, from the blind notes and the sentences. The lead verified estimate is
   now the version-1 census restricted to changed results: **20 of 33 up** (0.61, exact 0.42–0.77; 28 papers).
   Sensitivities:
   - without the reviewer's rejections, 20/31;
   - new data only, 9/13;
   - without glued table text, 16/27;
   - the pooled 52 as drafted.

   All are Inconclusive. None of the 28 census papers was posted within 30 days of its journal version (Crossref).
3. **Secondaries reworded.**
   - S1 cannot detect selective removal, because most unmatched statistics are matching failures. A post hoc,
     reviewer-suggested sharper comparison (statistics removed from or added to a sentence that survived) gives
     70.8% vs 80.4% significant, +9.6 points (paper bootstrap 0.6–18.6). It is reported as exploratory and
     suggestive, not as a finding.
   - S2's "repair" figure is dominated by false positives and verbatim copies. Decision inconsistencies are now
     reported: 29, of which 3 were repaired.
4. **Literature corrected.**
   - Bero et al. 2021: 67 COVID-19 studies.
   - Janda et al. 2022: results concordant in 81.1%.
   - Sommer et al. 2023: 27 of 161 changed; no significance change in 77 primary outcomes.
   - The 2026 bioRxiv study: DOI 10.64898/2026.06.30.735556; 39.8% unchanged, 50.0% minor, 10.2% substantial.
   - Added Nelson et al. 2022 and Brierley et al. 2022.
   - The unsourced "121 preprints" figure is dropped.

   All seven DOIs were verified in OpenAlex, and the three quoted abstracts were checked.
5. **Disclosures added.**
   - Blinding was to version labels only; copy-editing can reveal the order, and two notes show wrong guesses.
   - Adjudication was done in two batch passes, and 44 rejections share a default note.
   - Table and caption text leaks into result sections (20.8% of strict-eligible pairs), so the strict rule does not
     fully exclude tables.
   - p = 0 or 1, star legends and df-less tuples are added to the failure taxonomy.
   - The title filter rejected 2,664 (8.5%), mostly retitled true pairs.
   - Version-1 timing (reviewer's samples).
   - 44% of pairs contribute no statistic, partly section typing.
6. **Not done:** re-running the pipeline with the extraction fixes (stripping table and figure subtrees, splitting
   glued sentences, p = 0 and 1 undetermined, star legends globally, df required for exact matches, the middle-dot
   regression). They are listed as the methods lesson; the verdict does not depend on them.

## D6 — 2026-10-17 18:49 NZDT — confirmation pass (publish with edits)

`review/confirmation.md` confirmed every D5 number and asked for one fix and four edits:

1. **C1. The post hoc S1 comparison is withdrawn as a finding.** Significance-star legends are 35% of the statistics
   "added to surviving sentences" and 25% of those dropped (D5's STAR rule; the reviewer's rule finds 41% and 28%).
   The estimate's sign flips with how they are excluded:
   - without star legends, +3.9 (−4.5 to +11.7);
   - without star legends or glued text, +5.1 (−0.7 to +11.3);
   - text sections only, without star legends, −9.4 (−17.6 to −0.8).

   The report now calls it uninformative. The verdict-block and plain-terms claims are removed, and D5.3's "suggestive"
   no longer holds. `review_response.py` R13 now reports all the variants.
2. **C2.** Decision inconsistencies are "at most 29": 24 are verbatim copies, 3 are one-tailed-explicable, and some
   "z" matches are z-scores rather than test statistics.
3. **C3.** The blind, pre-coding census (24/42, 0.57, 0.41–0.72) is added to the sensitivities and Figure 2.
4. **C4.** w053 is recoded as changed_analysis, like w057, so "new data only" is now 9/12.
5. **C5.** Wording: the "sample of 14"; the glued-text share from D5's own rule (20.1%); "p-values that disagree
   with their own test statistic" in place of "arithmetic errors".
