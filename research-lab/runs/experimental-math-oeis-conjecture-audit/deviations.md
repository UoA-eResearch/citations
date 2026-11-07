# Deviations from plan.md

## D1 — 2026-10-25 03:03 NZDT — parser scope, before any screening

The first parse was inspected for coverage only. No LODA program had been run and no conjecture had been checked
beyond its data.
1. **A trailing period broke recurrence parsing** (for example "Empirical: a(n) = 8*a(n-1) - 13*a(n-2) - 12*a(n-3).").
   This was fixed.
2. **"(conjectured)" and "(empirical)" written after the formula** are now parsed from the text before the keyword.
3. **"Conjectures from …: (Start) … (End)" blocks.** Their member lines, which state the formulas without repeating the
   word, are candidate lines too, flagged `in_block`. The plan names "Barker-style" conjectures, which are mostly
   written this way, and lines that contain the word were already candidates.

Effect on the candidate set: 38,637 lines; 22,774 parsed (15,306 C, 1,002 D, 6,466 G); 21,998 consistent with their
own data; 776 contradicted by their own data (reported separately, as planned).

## Pre-review gate (G5, G6, plus G2 and G4 gaps) — 2026-10-25 22:57 NZDT, after all results (wording, attribution, one descriptive table)

The lab's METHODS.md gates were run before this draft's review. No preregistered result changed.
- **G5 overclaim check** (`review/overclaim_check.md`, passes): the title's "almost always hold" became "almost
  always agree with independent programs beyond the data" (a median of 26 further terms).
- **G6 attribution ledger** (`results/attribution_ledger.csv`, 7 claims, passes): the two Ekhad papers have three
  authors each. The report now cites Ekhad, Sloane and Zeilberger (2016) and Ekhad, Yang and Zeilberger (2017), and
  gives a source for Walnut (Shallit 2022).
- **G2 gap.** 104 conjectures whose predictor failed and 2 with short or mismatched LODA output were dropped from
  screening without mention; the coverage bullet now states them.
- **G4 gap.** "Mostly parsing artefacts" for the 776 self-contradicted lines was unaudited. New
  `code/contradicted_audit.py` (`results/tables/contradicted_audit.json`) finds that 541 (70%) carry an ignored
  condition (385 index restrictions, 167 parity or residue), with e.g.f. and iff statements rare (2 and 4). The text
  was corrected.

## D2 — 2026-11-07 — fixes after the independent review (verdict: fix first)

All of this follows the first review (`review/review.md`) and is post hoc. The first draft's interim files are kept
as `data/interim/*_v1.parquet`.

1. **Data check (finding 1).** `run_rec` now reports how many data terms it actually checked. A conjecture is
   "consistent" only if at least 5 were checked and all agree. Those with none checked are "unchecked" (4,166 C
   lines, typically high-order empirical recurrences on short entries). Those with 1–4 checked are "few checked"
   (833). Neither group is screened. "Agree" now needs at least one term beyond the data. The threshold of 5 is the
   reviewer's suggestion.
2. **Strata (finding 2).** Each entry is marked with whether it has a real b-file (a Git-LFS pointer in
   `oeisdata/files`). LODA programs are checked against up to 1,000 known terms, so where a b-file exists LODA is
   not an independent source. Rates are reported separately for the two strata, and the pooled rate is no longer
   the headline. The ledger's O5 condition is corrected. Agreements whose LODA formula comment states the
   conjecture's own recurrence are counted as tautological (153).
3. **Self-contradicted lines (finding 3).** `contradicted_audit.py` is rewritten. Each contradicted line is put in
   one class: stated range too early, holds from a later index, g.f. offset slip, ignored parity or residue
   condition, or no simple fix. The last class is listed by A-number in `contradicted_no_simple_fix.csv`. The parser
   also no longer treats a vanishing leading polynomial as a contradiction. At a data index it checks the reduced
   relation; beyond the data it stops.
4. **Verdict wording (finding 4).** The preregistered rule gives "Refuted" and the verdict line keeps it, but the
   report says the hypothesis is not supported within this pipeline's coverage, which is not a refutation of the
   claim.
5. **Depth (finding 5).** The plan allowed 2,000 b-file fetches and the confirmation step used 13. New `bdeep.py`
   spends the remaining 1,987 on a seeded random sample (seed 20261107) of the 8,586 entries that have a real
   b-file and at least one consistent, unflagged C/G/D conjecture. Every such conjecture on a sampled entry is run
   against up to 1,000 b-file terms, with no LODA involved. This uses one source (the b-file) and is labelled as
   such.
6. **Editor-flagged lines (finding 6).** Lines tagged [Wrong] or [Incorrect], or in a block so tagged, are flagged
   and parsed with the tag removed (the second A267515 line now parses). They do not count toward H1. That leaves A076217 untagged, but its entry carries a
   later note that the conjectured recurrence fails at powers of 3. Separate follow-up notes are not detected
   automatically, so no confirmed falsification is new.
7. **Parser (findings 7 and 8).** A stated start on an a(n+k) form is shifted with the re-indexing. Closed forms with
   no lag are class P, which the plan lists as "not parsed", and are reported outside the C/G/D population (1,843
   lines). A301424 is annotated in `falsifications.csv`: its "(conjectured)" qualifies the denominator's
   factorisation, not the g.f.
8. **Selection (finding 9).** `selection.csv` gives the share of consistent lines without a LODA program by keyword
   "easy", A-number range, block membership and class.
9. **Reporting (finding 10).**
   - The LODA and predicted values at each disagreement are stored.
   - The b-file label for a later failure is renamed `bfile_fails_later_than_loda` (zero cases).
   - The confirmation step's request count is corrected to 13.
   - A bug that read cached b-files with string keys is fixed. The first run never hit the cache.
   - On D1 timing: the LODA home directory was created about 45 s before the D1 commit, so screening setup had
     begun. The parser scope recorded in D1 was decided at the 02:59 parse, before any LODA program ran on a
     conjecture.
10. **Direct b-file test, results and conduct.** oeis.org answered HTTP 429 at one request per second. The fetcher
    then backed off and retried, and finally paused 5 s between requests; all 1,987 sampled files were fetched. 3 of
    3,114 conjectures (2 entries, A267514 and A210247) are contradicted by their b-file. Both failures are noted in
    later lines of their entries.
