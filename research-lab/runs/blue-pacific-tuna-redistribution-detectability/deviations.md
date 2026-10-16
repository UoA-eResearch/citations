# Deviations log

Every departure from the lead and from plan.md, timestamped with `date` when it was made.

## D1 — 2026-10-16 18:31 NZDT — four departures from the lead, all made before plan.md was committed

1. **Observation window 1980–2021, not 1980–2024.** The only account-free copy of WCPFC's public-domain
   1°×1° purse-seine file (SPC THREDDS, last modified 2024-11-26) runs 1967-12 to 2021-12. WCPFC's own
   downloads need a registration form. The FIRMS Global Tuna Atlas reaches 2024 but only at 5°, too coarse
   to assign catch to EEZs.
2. **Out-of-sample test 2000–2010, not 2010–2024.** SEAPODYM's historical run (ocean-reanalysis forced)
   ends in 2010-12; the projections from 2011 are forced by Earth system models and cannot be compared with
   observations year by year. The lead's split is infeasible on two counts.
3. **Threshold derived from model output, not by hand.** The lead's −0.15 pp/yr was a back-of-envelope
   conversion of the 13% figure. τ = −0.1174 pp/yr is SEAPODYM's own projected rate on exactly the share the
   observations measure (plan §4.3). Computing it required examining model output before the plan; that is
   the hypothesis-generating model, not the outcome, and what it showed is recorded in plan §4 in full.
   It showed that the model's historical run trends the opposite way to its projection, which is why plan
   §1.3 fixes the interpretation of H1 in advance.
4. **Density shares instead of a delta-GLM CPUE standardisation** (plan §5): within-year shares cancel
   fleet-wide creep; the remaining confound, school-type mix, is tested directly by the free-school series.

## D2 — 2026-10-16 18:31 NZDT — two data-integrity problems in the SEAPODYM files on SPC THREDDS

1. The four bigeye projection files named `bet_Btot_<ESM>_F0.nc` name their variable `bet_B_young`. They
   hold total biomass: identical to `bet_Badult` + `bet_Byoung` (correlation 1.0000, ratio 1.0000) and not a
   copy of the `bet_Byoung` file (different hash, ratio 6.7). `code/model_targets.py` reads the variable by
   position, not by name.
2. The bigeye *historical* `bet_Btot` is a different quantity: 0.848 × (adult + young) overall, between
   0.73 and 1.00 by cell. Splicing it to the projections would put a definitional step at 2010/2011 inside
   Bell et al.'s 2009–2018 baseline. Adult + young is used instead. Skipjack and yellowfin hold
   Btot = adult + young to 1.0000 in every cell, in both runs, so the primary skipjack analysis is untouched.
   Both are worth reporting to SPC.

## D3 — 2026-10-16 18:31 NZDT — the warm-pool edge index was redefined before use

The first version anchored its eastward scan at a fixed 140°E and recorded nothing in any month the pool
sat west of it; with a 12-of-12-months rule, 27 of 42 years were lost. That was a definition bug, not a data
gap. The index now anchors on the warm-pool maximum within 130–200°E, interpolates the 29 °C crossing, and
requires at least 9 months with ≥29 °C water. All 42 years are present; El Niño years sit at 190–208°E and
La Niña years at 162–177°E. Also: PSL's single-file ERSST downloaded at ~45 KB/s and its OPeNDAP endpoint
returned 429, so ERSST v5 is read from NCEI's monthly files, whose calendars disagree between years; the
date is taken from each filename. None of this involved the outcome.
