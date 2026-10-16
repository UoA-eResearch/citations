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

## D4 — 2026-10-16 18:35 NZDT — the preregistered masking check is blind; recorded before primary.py ran

plan.md §9.1 measured public-domain suppression as "catch recorded where effort is missing" and set a rule:
if that exceeded 10% of in-EEZ catch in any decade, O2 and O2u would be flagged unreliable. `observed.py`
returned exactly 0.0 in every decade. That is not reassurance. In this file the missing-value pattern is
identical across all 26 variables in 100.0000% of the 6,249,600 cell-months from 1980 to 2021: a suppressed
cell loses its catch, its effort and its set counts together, which makes it indistinguishable from a cell
nobody fished. Catch-without-effort cannot occur, so the check could never have fired.

Consequences, decided now, before any primary result has been seen:
- The rule in §9.1 is **unevaluable**, not satisfied. The report will say the masking footprint is unknown
  from this file, not that it is small.
- Following the conservative branch the plan itself specified for the triggered case, the report leads with
  O1, and O2/O2u are presented with their unknown exposure to suppression stated.
- One added check, labelled post hoc: compare the 1° file's annual skipjack purse-seine total inside the
  domain with the FIRMS Global Tuna Atlas 5° total for the same area and gear. Suppression bites far less
  at 5°, so the shortfall bounds what the 1° file is missing. It cannot say where inside the domain the
  missing catch was, so it bounds the size of the problem, not its direction for the EEZ share.

## D5 — 2026-10-16 18:39 NZDT — three exploratory additions after seeing the primary results

Made after primary.py had run. None changes a preregistered verdict; all are labelled exploratory.

1. **Per-EEZ results, at the lab owner's direction.** plan.md §10 restricted reporting to the pooled
   twelve-EEZ share, on the lead's note that EEZ-level results bear on revenue and should wait for SPC/FFA/PNA
   engagement. The lab owner (2026-10-16): "Your concerns around indigenous engagement are very noble - but
   not really feasible for you to do. I don't want people to not benefit from the research you can do just
   because of that." These are public WCPFC fleet catch records gridded by cell; the restriction was a
   political-sensitivity choice, not a data-rights one. Per-EEZ shares are now computed, reported as catch
   shares only - no revenue conversion, and no claim about any state's fishery beyond what the catch shows.
   **Prediction fixed before computing:** if the 2010 jump in the pooled share (+17.0 pp step) is the
   high-seas-pocket closure, it should sit in the EEZs bordering the two closed pockets - FSM, Palau, PNG,
   Solomon Islands, Nauru, Marshall Islands and Kiribati (Gilbert Islands) - and be near zero in those that
   do not border them: Tuvalu, Tokelau, Cook Islands, Kiribati (Phoenix) and Kiribati (Line).
2. **A size-calibrated power analysis.** The preregistered one-sided HAC test detected a "decline" in 14%
   of simulations when none was injected, against a nominal 5%: three Newey-West lags undercorrect residual
   autocorrelation of +0.56. That makes the preregistered MDE (0.325 pp/yr) and detection year (2084)
   optimistic. The calibrated version takes its critical value from the injected-zero simulations, so the
   test has 5% size by construction. The preregistered numbers stay in the report; the calibrated ones are
   reported beside them as the more honest pair.
3. **The zonal centroid.** The lead's method named an ENSO-adjusted trend in the catch centroid's longitude
   as a second estimand; plan.md dropped it. An eastward shift should move the centroid east, independently
   of where EEZ boundaries fall. Computed for observed catch, observed density and SEAPODYM biomass.

## D6 — 2026-10-16 18:43 NZDT — the per-EEZ prediction failed; a fixed-footprint check on the centroid

**The D5 prediction did not hold.** It said the 2010 jump would sit in the seven EEZs bordering the closed
pockets and be near zero in the five that do not. ENSO-adjusted steps summed by group do favour the bordering
EEZs (+12.1 against +5.0 pp), but all of it is Papua New Guinea (+16.6); four of the seven bordering EEZs have
negative steps and all five non-bordering EEZs positive ones. Raw before/after means point the other way:
bordering EEZs 76.5% -> 77.0% of domain catch, non-bordering 4.4% -> 14.2%. And the per-EEZ steps are poorly
identified - with twelve post-2010 years the step and trend terms trade off, so PNG's raw share fell 8.9 points
while its step is +16.6. The report will not attribute the pooled 2010 step to the closure on the strength of
the per-EEZ pattern; it coincides with the closure and with a jump in the EEZ share of fishing days, and that is
all that can be said.

**What the per-EEZ shares show instead** is catch moving from the western EEZs (PNG, FSM) to central and
eastern ones (Kiribati Gilbert, Nauru, Tuvalu, Phoenix), and the ENSO-adjusted centroid moving east at +0.55
(catch) and +0.65 (density) degrees per year. That is the direction SEAPODYM projects - but the purse-seine
fishery itself expanded east over these decades, and a centroid computed over the cells fished in each year
moves east whenever new eastern grounds open, fish or no fish.

**Check, defined before it is run:** recompute the density centroid over a FIXED footprint - only the cells in
the domain fished on at least 5 days in at least 80% of the 42 years (sensitivity: 50%) - so that no cell
enters or leaves. If the eastward trend survives on a fixed footprint, density has shifted east within grounds
fished throughout. If it vanishes, the centroid result is fleet expansion. Either way the report says which.
The same fixed footprint is used for a density share, to see whether the flat O2 result depends on footprint.
