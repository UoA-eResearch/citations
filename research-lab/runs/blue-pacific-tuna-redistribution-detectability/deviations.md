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
2. **[Superseded - see D8.3: this file is the adult-only biomass, and the 0.848 below is just the adult fraction.]**
   The bigeye *historical* `bet_Btot` is a different quantity: 0.848 × (adult + young) overall, between
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

## D7 — 2026-10-16 18:45 NZDT — the fixed footprint was not fixed in its early years; refit on covered years

The D6 footprint (cells fished in >= 80% of years) gave a centroid trend of +0.075 deg/yr (+0.019, +0.134),
against +0.65 for the unconstrained density centroid. But its yearly coverage fell as low as 0.17: a "fixed"
cell set is only fixed if its cells are actually fished. Coverage is below 0.8 in 1980-1987 (0.17, 0.29,
0.71, 0.49, 0.58, 0.74, 0.74, 0.72) - the fishery's development years - and in 1998, 2001 and 2002.
Refitted on the 31 years with coverage >= 0.8 (1988-2021): **+0.002 deg/yr (-0.009, +0.013)**.

This refinement was not specified in D6; it was prompted by the coverage figure, and it is labelled post hoc.
It moves the conclusion in the conservative direction: the +0.075 itself came from the under-covered early
years, and within grounds genuinely fished throughout there is no eastward drift at all. The D6 decision rule
said that if the trend vanished on a fixed footprint, the centroid result is fleet expansion; it vanishes.
The footprint is 96.8% inside the EEZs and spans 141.5-159.5 E, so its density share cannot move much and is
reported but not interpreted.

## D8 — 2026-10-16 19:31 NZDT — changes made in response to the adversarial review (fix first, 18 issues)

The Fable 5.1 review of draft 9f05cfc recomputed everything from the raw files and confirmed the commit order,
the EEZ mask, tau, O1 for all 42 years, H1, H2, H3, the per-EEZ numbers and the power figures. It found six
must-fix problems. Each was verified here before it was acted on.

1. **The fixed-footprint headline was unsupported, and I had left out a preregistered result.** On the 86-cell
   footprint, SEAPODYM's own projected 2011-2050 centroid trend is +0.0095 deg/yr (GFDL 0.0066, IPSL 0.0094,
   MIROC 0.0159, MPI 0.0062) against +0.070 domain-wide, and the observed interval (-0.009, +0.013) contains
   it. The check could not tell "no shift" from "the projected shift". The D6 decision rule was mis-specified:
   it never asked what the model would show on that footprint. And the 50% footprint - the sensitivity D6
   itself named - gave +0.137 (+0.077, +0.195), sitting in footprint.json and absent from the report. That is
   selective reporting, and it is corrected. `footprint_grid.py` now reports every threshold x coverage rule,
   each beside the model's projected shift on the same cells. Where the check has power (footprints reaching
   ~185E, model +0.03 to +0.04), observed trends run from -0.010 to +0.137 depending on the rule. "The fish
   have not moved east" and "the fleet moved, not the fish" are withdrawn. What survives: most of the catch
   centroid's +0.55 deg/yr is fleet footprint, and whether skipjack density has shifted east is unresolved.
2. **The preregistered intervals undercover.** The disclosed 0.89 was measured under white noise. Under the
   observed AR(1) autocorrelation (0.56) coverage is about 0.79 (block bootstrap) and 0.76 (HAC). A GLS-AR(1)
   interval gives +0.198 (-0.225, +0.620), which includes tau. The verdict stays Supported by the preregistered
   rule and is reported as borderline - Inconclusive under GLS-AR(1). test_analysis.py now measures coverage
   under AR(1) noise too.
3. **D2.2 misdiagnosed the bigeye historical file.** `bet_Btot_hist_F0` is identical to `bet_Badult_hist_F0`
   (max difference 0): the served historical "total" is adult biomass only. The 0.848 was adult/(adult+young).
   The projection files' wrong variable name is a leftover of `cdo add bet_Byoung bet_Badult` with no `chname`
   step (their history attribute). The adult+young fix was right; the description was wrong, and it was
   headed to SPC.
4. **The H2 density-share "contradiction" was the fleet's footprint.** O2 is a share over fished cells, and the
   fleet fished 25 cells in 1980 and 410 by 1992. From 1990 the observed density-share trend is +0.180 against
   the model's +0.221 (difference -0.041, -0.496 to +0.322); catch and free-school shares agree in sign too.
   The preregistered 1980-2010 numbers stay; the interpretation, and the sentence saying the model "deserves
   less confidence", are withdrawn. None of the observed series is footprint-free.
5. **The detection year is a range, not 2098.** Under catch-share noise models it runs 2050 (post-1990
   residuals, 2010 step removed) to 2117 (autocorrelation 0.75); 2097 with the preregistered noise. A
   fishery-independent index with model-like noise would reach it by about 2035.
6. **The Bell reproduction was mislabelled.** -14.2% is the 2011-2018 baseline; the spliced 2009-2018 gives
   -15.3%. Bell et al.'s own equation (1), a month-by-month ratio over 2011-2020, gives -13.8% (-9.3 to -19.9)
   - so part of the gap was my method, not the files. The residual gap is MPI (-9.3% against -5%).

Also: "one time in six" described a 42-year linear decline; for the decline the projection actually makes,
beginning in 2011, the record to 2021 has 8% power - the false-alarm rate. H3 is called uninformative. The
D4 FIRMS check, promised and not run, is now run: the 1-degree file holds 58% (1980s) to 79% (2010s) of the
5-degree skipjack purse-seine total for the domain - a quarter of the catch missing, time-varying. Outside the
twelve EEZs, skipjack catch in 140-180E fell from 107 to 26 kt/yr after 2010 while catch at 180-200E rose from
17 to 61 kt/yr: the closure's displaced catch went partly into the EEZs and partly to the eastern high seas.
**[Superseded - see D9: the eastern rise came in 2014-19, not at the closure.]**
(The review read this as no change east of 180E, on a narrower window; with 2000-09 against 2010-19, which
includes the 2015 El Nino, it is a large rise.) The PNA proposed closing a further eastern high-seas block
(10N-20S, 170E-150W) around 2010-11; whether and when it took effect I could not confirm, so it is mentioned
only as a possibility. And D7's refinement was not logged with a decision rule before it ran; the draft said
every post-hoc analysis was, which was false for D7.

## D9 — 2026-10-16 19:46 NZDT — the confirmation pass (publish with edits, 6 edits)

The reviewer's confirmation pass on 9ba8dd3 found all six must-fix items addressed and recomputed the new
numbers to match. Six edits, none changing a verdict, each verified here first:

1. **I had over-claimed the closure's displacement.** D8 and the revised report said the 2010 closure's
   displaced catch went partly to the eastern high seas, from decade averages. The years say otherwise:
   outside-EEZ skipjack at 180-200E was 13.6 kt/yr in 2010-2013, no higher than 2000-2009 (16.7). The rise came
   in 2014-2019 (92.5 kt/yr; 173.5 in 2015), correlates 0.76 with Nino 3.4 (2000-2019), and began after CMM 2008-01 lapsed
   in February 2013. At the closure, displaced catch went into the EEZs.
2. **The PNA eastern closure is confirmed**, which I had failed to do: announced 23 April 2010, effective
   1 January 2011, for PNA-licensed purse seiners, 10N-20S x 170E-150W, 4,555,000 km2 (pnatuna.com/node/102).
   It explains why nothing rose east of the dateline at the closure. A June 2014 3IA amendment titled as
   removing the closure exists but could not be opened; noted, not relied on.
3. **The Tuna Atlas rows are raised** (every WCPFC SKJ purse-seine row has processing level "raised"), so the
   1-degree file's ~27% shortfall is raising plus suppression, not suppression. The 1-degree file has no catch
   at 120-130E in any decade (144-578 kt/decade at 5 degrees, domestic fleets); excluding that band it holds
   63/76/78/82% by decade. In the 1980s it holds 68% of the 5-degree catch at 130-160E but 11% at 160-200E, so
   the early-1980s EEZ share rests on a file that barely sees the east that decade.
4. Wording: "agree from 1990" -> "point the same way" (intervals +/-0.4-0.5); "8%, the false-alarm rate" ->
   "about the 5% false-alarm rate"; F1's caption no longer calls the density share free of where the fleet
   fishes; D2.2 and the D8 displacement sentence carry superseded markers in place.
5. **One reviewer claim corrected rather than adopted.** It said that where the footprint check has power,
   none of the rule combinations points west. There are eight such combinations on the wider footprints; four
   exceed the projected rate, and one is -0.010 (west, though indistinguishable from zero). The report gives
   that count.
