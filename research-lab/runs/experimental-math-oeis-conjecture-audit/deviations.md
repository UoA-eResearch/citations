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
