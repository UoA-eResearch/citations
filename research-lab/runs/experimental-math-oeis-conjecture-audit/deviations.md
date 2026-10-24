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
