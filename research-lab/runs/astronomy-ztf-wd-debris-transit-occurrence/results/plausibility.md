# Plausibility (G3)

- **Hand traces** (`code/handtrace.py`, `results/tables/handtrace.json`; D3). Four stars were re-fetched from IRSA,
  kept to g and r as the pipeline is since D2, and their rule statistics recomputed with plain loops: two chosen and
  two random. The pipeline's epochs, faint and bright counts, excess, faint nights and long-rule low bins match
  exactly for all four:
  - chosen: WD 1145+017 (known; 665 epochs, excess 28, no low bins);
  - chosen: the candidate with the largest excess (1,383 epochs, excess 135, 15 low bins);
  - random: an eligible star (899 epochs, excess −20, no low bins);
  - random: a long-only candidate (851 epochs, excess −30, 2 low bins, 5.0% and 9.4% deep at 5.8 and 9.3 standard
    errors).
  The first traces (all filters, three stars, before D2) are kept as `handtrace_v1_allfilters.json`. The failed-query
  count (13) is now read from the fetch logs.
- **Invariants.**
  - Eligible stars all have ≥ 100 good epochs.
  - Every flagged star meets its rule's thresholds.
  - Injected stars were unflagged before injection.
  - The completeness sum never exceeds the eligible count (71,572 ≤ 108,493).
  - The 18 known systems in the sample match by position within 1.5 arcsec, except WD 1054−226 (4.9 arcsec, a J2000
    paper position against Gaia epoch 2016 for a 36 pc star).
- **Positive controls:** 15 of 18 recovered, with injection recovery of 50–66% by class, which is consistent.

## G4 and the calendar test (after the review; `results/tables/posthoc_review.json`, `posthoc_d3.json`)

- **g/r coincidence** (the plan's G4 mitigation). As preregistered (dip epochs coincide in g and r within a night),
  23 of 26 testable random flags pass, 81% of all testable flags and all 14 testable known systems. At the bin level,
  94% of the long-dip candidates' low bins with at least 3 g and 3 r epochs are more than 2.5% low in both bands, and
  71% at least 5% low in both. Under every reading the check barely separates real dimming from calibration-like
  trends.
- **Calendar clustering.** 454 of 769 long-dip candidates have a low bin in the same ten 30-day windows, 140 of them
  in June 2020 (MJD 59010–59040). In those windows, 2,000 random unflagged stars are also faint (median 0.1–0.7%,
  against −0.02% overall). Re-drawing each candidate's low bins among its own well-sampled bins gives 215 (196–238)
  in those windows by coverage alone: the ten windows hold 10.9% of quiet stars' usable bins but 39% of candidates'
  low bins. Many long-dip flags follow survey-wide trends.
