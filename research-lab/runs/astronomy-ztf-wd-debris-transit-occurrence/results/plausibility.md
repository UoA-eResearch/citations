# Plausibility (G3)

- **Hand traces** (`code/handtrace.py`, `results/tables/handtrace.json`). Three stars were re-fetched from IRSA and
  their short-dip statistics recomputed with plain loops. The pipeline's epochs, faint and bright counts, excess and
  faint nights match exactly for all three:
  - WD 1145+017 (known; 743 epochs, excess 28);
  - the candidate with the largest excess (2,487 epochs, excess 134);
  - a random eligible star (1,104 epochs, excess −6).
- **Invariants.**
  - Eligible stars all have ≥ 100 good epochs.
  - Every flagged star meets its rule's thresholds.
  - Injected stars were unflagged before injection.
  - The completeness sum never exceeds the eligible count (72,748 ≤ 109,074).
  - The 18 known systems in the sample match by position within 1.5 arcsec, except WD 1054−226 (4.9 arcsec, a J2000
    paper position against Gaia epoch 2016 for a 36 pc star).
- **Positive controls:** 15 of 18 recovered, with injection recovery of 50–66% by class, which is consistent.

## G4 and the calendar test (after the review)

- **g/r coincidence** (the plan's G4 mitigation). 94% of the long-dip candidates' low bins with at least 3 g and 3
  r epochs are low in both bands (more than 2.5% each). The check barely separates real dimming from
  calibration-like trends.
- **Calendar clustering** (`results/tables/posthoc_review.json`). 454 of 769 long-dip candidates have a low bin in
  the same ten 30-day windows, 140 of them in June 2020 (MJD 59010–59040). In those windows, 2,000 random unflagged
  stars are also faint (median 0.1–0.7%, against −0.02% overall). Most long-dip flags follow survey-wide trends.
- **The rules were re-run on g and r only** (D2); the hand traces above used all filters as first run and match the
  pipeline as run then.
