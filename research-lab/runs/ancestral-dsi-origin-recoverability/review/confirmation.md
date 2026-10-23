# Confirmation pass: `ancestral-dsi-origin-recoverability`

Reviewer: Fable, 2026-10-23. Confirming the fixes in commit `b0149e2` (logged as D10) against the ten findings of
`review/review.md`. I did not redo the review. Checks: `reviewer_checks/confirm_tables.py` / `.out` (post-D10 tables
plus an independent recomputation from `limb2_rows.csv`) and `reviewer_checks/confirm_asym.py`-equivalent output
`confirm_asym.out`. Record text and publication text are not reproduced in this directory.

## Verdict: **publish** — all ten findings are addressed, the new numbers reproduce independently, and both
## preregistered verdicts stand (H1 Inconclusive, H2 Refuted). One labelling fix and two stale cross-references
## are worth clearing first; none changes a number or a verdict.

## Finding by finding

- **F1 — fixed.** The title now reads "left the usable-country share unresolved"; the H1 bullet calls the
  placeholder/blank shift "a trend visible across the rule, not an effect the design can attribute to it"
  (`report.md:13-17`), with the placebo sd of 5.5 points and "9 of 55" beside it; `report.md:133-141` reports all
  three placebo sds (10.2 / 5.5 / 8.1), the p ≈ 0.16 calibration and the yearly trend; "What this does and does not
  show" is retitled "Neither change can be attributed to the rule" (`report.md:232-236`); the plain-terms section
  says "a gradual trend we cannot pin on the rule" (`report.md:47-49`); and the mirror section now draws the
  37%-of-placeholders point as "another reason not to treat the placeholder shift as a measured effect"
  (`report.md:226-228`). Every placebo figure matches `reviewer_checks/rd_replicate.json` (sd 10.222 / 5.534 / 8.128;
  9 and 11 of 55). The F1 caption remains descriptive, which is correct.
- **F2/F4 — fixed.** `code/score.py:134-140` carries `D10_NOT_STATED` with the nine records and a reason each, and
  `final_labels()` applies it under `APPLY_D10` (`score.py:156-159`), leaving the sealed label files untouched —
  the right mechanism. Diffing `limb2_rows.csv` against `limb2_rows_pre_d10.csv` shows exactly nine changed labels —
  R240, R241, R242, R243, R244, R475, R477 (F2) and R054, R461 (F4) — all now "not stated". All four prompted figures
  reproduce from my own recomputation: **ceiling 19/300 = 6.33%** (CI 4.1–9.7); **all three arms threshold `None`,
  0 test calls, 0% recovery, upper bound 1.3%**; **projection 60.7 / 31.6 / 7.7%** (127,068 samples, 81,462–172,674);
  **D7: 147 natural records, ceiling 19.05% (13.5–26.2%), LLM 23 correct of 35 calls**. The five `*_pre_d10` tables
  are present and hold the old values (37 countries, classifier 1.7%, 24 determinable). The report says what changed,
  in four places: the correction bullet (`:36-38`), "Final labels after D10" (`:155`), "Labels as first adjudicated"
  (`:165-166`), "Before D10 the classifier reached 90% on two tuning calls … One of those two tuning calls was R475"
  (`:187-188`), and "Before D10 this was 9.2%" (`:170`). Downstream tables are consistent: all three arms are `null`
  in `decomposition_limb2.json` and `projection_recoverable_test` is 0.0 throughout.
- **F3 — fixed.** `report.md:30-31` reads "laboratory or cultivated material … for which no collection origin
  applies or none is recorded", and `report.md:159-161` adds the counts: 234 of the 350 are *Mus musculus*, 21 are
  field, agricultural or genebank material, "so the category is not a clean biological partition". The plain-terms
  wording at `:52-54` matches.
- **F5 — fixed.** `report.md:245-247` now gives 3 of 250 publication-linked records (1.2%) with a stated sampling
  country against the CBD's 44%. I recomputed the publication-linked stratum independently: 3 of 250 (R001, R129,
  R234). The stratum table at `:157` agrees (92% / 7% / 1%).
- **F6 — fixed.** "Six in ten" at `report.md:52`, and the plain-terms section now closes with "Held to the 90%
  accuracy the plan required, no method made any calls" (`:56-57`).
- **F7 — fixed.** `report.md:171-174` gives both variants (2,190 under the ENA attribute, a further 4,445 under
  `geo_location`), notes two of the 28 gold countries are of this kind, and says that part of the share is "recorded
  under another field name rather than recoverable by mining"; the headline bullet carries the short form at `:33-34`
  and the discussion at `:240-241`. D10 §3 logs the corrected 6,635 / 0.18%.
- **F8 — fixed.** `report.md:194-196` reports both discarded answers by record id, including that R401 is a test
  record, and that raw answers were not retained so recall is slightly understated.
- **F9 — fixed.** `report.md:142-143` states that H1's rule is one-sided ("a large decrease would also read
  'Supported'") and that the raw usable share fell 85.3% → 79.4%; the headline bullet repeats the raw fall at
  `:18-19`.
- **F10 — fixed.** `report.md:258-259` carries the frame-mismatch sentence with the magnitude ("well under a point").

## New issues

1. **Low-medium — the asymmetric-error block switched row basis without saying so.** `report.md:200-203` gives
   75% for the LLM (6 of 8; 41–93%), 60% for the classifier (52–67%) and 38% for the gazetteer (25–52%). These are
   correct, but they are the `test_at_threshold` rows, i.e. the **test split**, whereas the pre-D10 report quoted the
   all-497-record rows (60 / 57 / 33%). Both rows exist in `limb2_secondary.json` and I reproduced all six
   (`confirm_asym.out`); the all-records values are now 64.7% (11 of 17), 57.7% and 34.2%. Since no arm has a tuned
   threshold after D10, `asymmetric()` counts every prediction, so a row named "test_at_threshold" is in fact an
   any-confidence row — the quirk D7 flagged for two arms now applies to all three. Fix: say "on the test split, at
   any confidence" in the report line, and widen D7's note, which still reads "for an arm with no tuned threshold
   (gazetteer, LLM)" (`deviations.md`, D7 §2).
2. **Low — two stale cross-references to the superseded ceiling.** D7's own text still opens "Only 24 of the 300 test
   records turned out to have a determinable country" (`deviations.md:102`). As dated history that is accurate, but a
   reader meets it with no pointer to D10; one clause ("19 after D10") would close it. Separately, the lab's
   `REVIEW_QUEUE.md:50` summary line still carries the pre-D10 headline figures (24/300, 9% findable) alongside the
   note that fixes landed in b0149e2 — a process file, not the report, and the coordinator's to adjust.
3. **Housekeeping I did in my own review files (no finding changed).** Per this pass's instruction to keep record and
   publication text out of `review/`, I redacted the four places where my first-pass `review.md` quoted sample
   attributes or paper sentences verbatim (F2's strain identifiers and collector name, F3's two origin statements,
   F4's facility and grow-out quotes) and replaced them with descriptions; every record id, count, verdict and fix
   is unchanged. I made the same redaction in three check artefacts that echoed attribute values
   (`leakage_check.py`/`.out`, `pass1_limit_check.py`/`.out`, `attr_variant_scan.py`/`.json`) and re-ran each, so a
   re-run stays clean; all counts are unchanged, and a sweep of `review/` for record or publication strings is now
   empty. `leakage_check.py` prints attribute **keys** only and reports the
   600-char-cap records as a yes/no on whether the tail ends inside a geographic attribute; on re-running it, the
   institution-attribute counts are unchanged (108 of 500), but because the script reads the current
   `limb2_rows.csv`, its error counts now reflect the D10 labels (classifier 6/10 of institution-attribute errors
   name the owner country vs 156/271 elsewhere, against 4/8 vs 156/271 before D10); F3's conclusion — no measurable
   inflation — is unaffected, and `review.md` now cites both. Finally I repointed `review.md`'s three references to
   the evidence dumps that were moved to `data/review_evidence/`.
4. **Nil — no pre-D10 value survives anywhere it should not.** I grepped the run's markdown, code and figure captions
   for every superseded figure (24/300, 8%, 1.7%, 9.2%, 152,600, 37 countries, USA 12, 77%, 73%, 67.9%, 0.42/0.43,
   "seven in ten", "one in eleven", "turned blanks", "clearly change"): the only hits outside `review/` are the four
   deliberate "before D10" comparisons in `report.md` and item 2 above. Both figure captions were regenerated
   (F2 "after D10 no arm reaches 90%", F3 "19% … after D10"), and the PNGs (13:10:44) postdate the tables (13:08–13:09).
   Every other number I re-checked in the revised report ties to the post-D10 tables: the 28 countries and their
   7/6/2/2 + 11 breakdown, CBD 64/21/14%, submitter-country 7 of 10, labels 350/119/28 and both strata, any-confidence
   4.0/4.7/5.3% with 16 of 28 and 16 of 19, Brier 0.75/0.44/0.50, D7's 66% and 82%, the projection and its interval,
   and "one in thirteen" for 7.7%.
