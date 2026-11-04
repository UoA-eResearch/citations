# Independent review: astronomy-gaia-sb1-tess-synchronization-boundary

Reviewer: Claude (Fable 5.1), 2026-11-05. Scripts and outputs in `review/reviewer_checks/` (`checks.py` ->
`checks.json`/`checks.log`; `checks2.py` -> `checks2.json`/`checks2.log`; `checks3_nanC.log`). Study files read
only. Numbers below without a file reference come from those outputs.

## Verdict: fix first

H1's *Refuted* survives every correction I could make: even on the most favourable subset and the most lenient rule
(credible signals, P_orb target, no doubling) the cool share is 0.59, below 0.70. But the report's level (a fifth),
its hot-side reading, its central positive claim (a step at the Kraft break), its width figure and its "floor"
argument all need rework, one preregistered secondary was not run and changes the picture, and the classification
rules carry one-directional biases the report does not quantify. These are analyses and a rewrite, not edits.

What holds up: plan.md (df9de0b, 12:22 on Nov 3) precedes the first download (first bulk script 13:01, Gaia table
13:58); the ellipsoidal-before-doubling test was already in classify.py at its first commit (fe71d02, Nov 3 22:37),
a day before classification (stars.parquet, Nov 4 22:06); G6 passes and I verified A1 and A2 against their
abstracts; G5 passes mechanically; my own read of the 30 folded panels matches the lead's 14 clear / 16 incoherent
panel for panel; the G3 traces match g3_traces.json.

## Findings

### 1. The synchronized share is never compared with its chance level (major)

**Evidence.** A permutation null (each detection's P_rot swapped with another detection's, within TESS-magnitude
tercile, weighted as in the primary; `checks.json` section 2) gives a chance share of 0.092 ± 0.007 for the cool
group and 0.054 ± 0.012 for the hot group, against the observed 0.205 and 0.093. Random periods land within 10% of
P_orb about one time in eleven because the P_rot and P_orb distributions overlap. So the hot share is about three
standard deviations above chance, and the logistic's fitted floor of 0.11 (primary.json) is the chance level, not a
synchronized population. The lead's own audit shows the mechanism: of the three panels labelled synchronized in
g4_folded.png, two (3 and 10) are flat noise.

**Why it matters.** The report's floor argument (report.md lines 21-26, 110-114) says spurious periods dilute the
share. They also create synchronized labels at the chance rate, and with roughly 60% of detected-class panels
incoherent (10 of the 16 detected-class panels in the audit), chance accounts for about a quarter of the cool share
and more than half of the hot one.

**Fix.** Report the excess over the permutation null for every group and variant; describe f_hot as a few per cent
above chance; stop reading the logistic floor as a synchronized fraction.

### 2. The "step at the Kraft break" is not separable from the disappearance of spots (major)

**Evidence.** Across 5,500-7,500 K the class mix changes completely (`checks.json` section 8): the detected share of
stars with light curves falls from 0.32 to 0.09, pulsators rise from 0.04 to 0.32 and ellipsoidals from 0.00 to
0.34. The hot detected class is the residue left after those removals, and finding 1 shows it is near chance. On
detections with a credible signal (semi-amplitude above 2 ppt and at least two detecting sectors; `checks2.json`)
the share is 0.43 for cool stars (n = 568) and 0.475 for hot stars (n = 59, so roughly ± 0.13): no step. The
profile likelihood locates the transition where spot-dominated detections give way to a chance-level residue, which
theory puts at the same temperature as the tidal transition, so the study cannot tell the two apart. The plan
anticipated exactly this (plan.md lines 129-130) and then the report presented the step as a positive result
(title; report.md lines 14-16, 36-37, 108-109).

**Fix.** Rewrite the title, verdict bullet 3, the "location matches theory" paragraph and the plain-terms sentence
to say that the synchronized excess over chance vanishes above about 6,300 K, which is also where spot signals
vanish, and that the hot side therefore does not measure synchronization. Re-label G5 rows 1, 11, 12 and 25 as
Partially supported.

### 3. The "inconsistent" rule discards the best-observed stars (major)

**Evidence.** With the detection rule firing in 84.7% of TESS-SPOC sectors (finding 12), one spurious sector makes a
multi-sector star inconsistent. Of the 6,382 inconsistent stars with P_orb < 10 d, 4,233 have a majority cluster
(after the post hoc P/2P harmonisation, at least two sectors agreeing within 10% and more than half of the
detecting sectors; median cluster fraction 0.88, i.e. typically seven of eight sectors agree; `checks.json` section
6). Among cool stars 2,164 have such a cluster, more than the 1,770 cool detections H1 rests on, and 33% of their
cluster periods are within 10% of P_ps (42% of P_orb), against 0.23 in the detected class. The post hoc harmonised
run (posthoc.py lines 48-56) fixes only P/2P flips and still leaves 5,851 stars inconsistent.

**Fix.** Add a labelled post hoc majority-vote rule and report the cool and hot shares under it (combined with the
detected class the cool share is about 0.29 unweighted). State in the limits that the plan's rule preferentially
removes stars with many sectors.

### 4. Preregistered secondary 2 was not run, and it matters (major)

**Evidence.** plan.md lines 86-87 promise a rerun with the possible-beaming and pulsator classes included.
analyse.py lines 132-133 only count ellipsoidals as synchronized; secondary.json has no pulsator or beaming variant.
Cool main-sequence stars at 4,000-6,200 K are not gamma Dor or delta Scuti pulsators, yet 451 cool stars with
P_orb < 10 d carry the pulsator flag, and 47.5% of them have P_rot within 10% of P_ps (`checks.json` section 5;
their median P_orb is 2.7 d against 4.9 d for the detected class). The rule (periods.py lines 100-116: three or more
peaks in 0.3-3 d not within 2% of an integer ratio) flags spot evolution and differential rotation on the
shortest-period, most synchronized binaries. Folding pulsators in moves the unweighted cool share from 0.224 to
0.272 and the hot share from 0.123 to 0.224 (`checks2.json`).

**Fix.** Run secondary 2 as planned and put it in the sensitivity table. Say that the pulsator rule, applied below
the gamma Dor strip, removes synchronized spotted stars.

### 5. Completeness weighting up-weights the detections most likely to be false; the 339 "low-C" drops are
something else (moderate)

**Evidence.** The share by completeness cell is 0.14 at C = 0.6-0.9 (n = 490) and 0.28 at C = 0.9-1 (n = 1,192);
by semi-amplitude it is 0.05 below 1 ppt (n = 680, 38% of cool detections, below the chance level) and 0.38-0.40
above 2 ppt (`checks.json` section 3). The 1/C weights therefore favour the low-amplitude detections that the
audit says are noise, which is why the weighted share (0.205) sits below the unweighted one (0.232). The weighting
assumes every detection is real. The hosts (all 1,792 non-detections) are by construction the quietest light
curves, so C is optimistic for typical stars. Separately, primary.json's 339 detections "dropped for C < 0.1" are
338 detections with no completeness cell at all (142 with semi-amplitude above 2%, 87 with P_rot below 0.3 d; the
NaN fails the `>= 0.1` test at analyse.py line 72) plus one with C < 0.1 (`checks3_nanC.log`). The effect on the
shares is small (cool 0.205 to 0.200, hot 0.093 to 0.104 with them at weight 1), but the description in
primary.json and report.md is wrong and the drop is absent from coverage.json (G2).

**Fix.** Describe the drop correctly and record it in coverage.json; present the unweighted share alongside the
weighted one with the reason; say in the limits that the weights assume real detections.

### 6. The H1 logistic is mis-optimised; the "width about 300 K" is an artefact (moderate)

**Evidence.** Refitting with scaled parameters (`checks.json` section 7) lowers the negative log-likelihood from
1,596.8 to 1,588.3; the midpoint moves to 6,345 K and the width to the lower bound (44 K). A 50 K profile puts the
minimum at 6,350 K (delta-NLL 3.2 at 6,300 K, 4.1 at 6,400 K). In 300 bootstrap refits the midpoint interval is
6,226-6,413 K and the width interval 44-288 K, with 82% of resamples at the bound. So the reported width of 313.7 K
(primary.json; report.md line 15) is the stuck optimiser's start value, and the data only say the transition is
sharper than about 300 K. The weighted likelihood also uses sum(w)/n = 1.28, inflating every delta-NLL. And the
cool bin is not a plateau: the share rises from 0.00-0.10 below 5,200 K (n = 225, at or below chance) to 0.28 at
5,800-6,100 K, which a floor-ceiling logistic cannot express.

**Fix.** Refit with scaled parameters; report T0 about 6,350 K (6,230-6,410) and the width as unresolved below
about 300 K; remove the 300 K figure; note the rise through the cool bin.

### 7. The ACF doubling rule, after the ellipsoidal test, can only move stars out of the synchronized class
(moderate)

**Evidence.** Of 416 doubled detections with P_orb < 10 d, 93 had their undoubled period within 10% of P_ps and all
93 are now labelled sub-synchronous (61 cool). A star at P_orb/2 is removed as ellipsoidal before doubling, so
doubling never moves a star in. The cool share is 0.230 without doubling and 0.295 with the P_orb target and no
doubling (`checks.json` section 4; `checks2.json`). Panel 22 of the audit is such a case (the lead noted it).

**Fix.** Add the no-doubling variant to the sensitivity table and the rule-choices paragraph.

### 8. D1: thin audit trail, and the sensitivity does not test what was excluded (moderate)

**Evidence.** deviations.md was first committed with the report (414c199, 06:11 on Nov 5), eight hours after its own
22:06 stamp; stars.parquet was written at 22:06:53, 74 seconds after periods.py finished (logs/periods.log
22:05:39), so the claim that classify.py had not been run when D1 was decided cannot be checked. The decision
itself is defensible on the 99.5% detection rate. The 6,100 QLP-only stars are fainter (median Tmag 11.82 against
11.32), hotter (36% hot against 29%) and shorter-period (median P_orb 3.73 d against 4.46 d) than the TESS-SPOC
stars, at the same ecliptic latitude (`checks.json` section 9), so the exclusion removes a short-period,
synchronization-prone slice. The promised sensitivity is uninformative: detrended QLP still fires in 97.5% of
sectors (posthoc.json), and adding those sectors makes 16,327 stars inconsistent, so it says nothing about the
6,100 excluded stars.

**Fix.** Characterise the excluded stars in the limits; say the detrending did not rescue QLP.

### 9. Gates: G7 hollow for the audit, an undocumented D2, G3 and plan items missing (moderate)

**Evidence.**
- G7 is declared not applicable (plan.md line 122; report.md line 144), but the 16-of-30 figure in the title and
  verdict is a validation label set by one agent who could see the class labels (g4_check.json). I re-rated the
  panels and agree 30 for 30, but I also saw the labels; that is not the two blind labellers METHODS.md asks for.
- g4_check.py line 1 refers to a D2 that does not exist in deviations.md: replacing the plan's independent TESS
  catalogue with Gaia DR3's own rotation-modulation periods is an undocumented deviation. Those Gaia periods are
  noisy themselves, so the 30% agreement (41 of 135) cannot be read as the TESS error rate, as report.md line 25
  and plausibility.md line 42 do.
- g4_check.json's note on panels 25 and 30 is wrong for panel 25: it is class pulsator, not sub-synchronous, and its
  fold shows two cycles per P_orb, an ellipsoidal variable that the pulsator test caught first (classify.py line
  62 orders pulsator before ellipsoidal).
- G3's promised comparison of cool single-star TESS periods with literature ranges (plan.md line 116) is absent from
  plausibility.md.
- Plan secondary 5 (sub- and super-synchronous shares by Teff and P_orb, including 10-12 d) appears only as
  counts by Teff; the RUWE distribution promised at plan.md line 134 is not reported (41% of the sample has
  RUWE > 1.4).

**Fix.** Add D2; mark G7 as not met for the audit (or run a blind second rater); add the G3 item or say it was
dropped; report secondary 5 and RUWE.

### 10. Report numbers and wording (minor)

- "66% of hot detections are signals at half the orbital period" (report.md line 99): ellipsoidals are 61.6% of the
  hot detected-plus-ellipsoidal set (the 0.663 in secondary.json includes synchronized stars) and 25% of all hot
  stars with a period.
- "A fifth of Gaia's close binaries" (title) and "about a fifth of the cool stars" (plain terms): it is a fifth of
  the 27% of cool stars with light curves that have a usable period; 6.5% of cool stars with light curves are
  labelled synchronized. G5 rows 1 and 26 should be Partially supported.
- The Lurie et al. 79% is among eclipsing binaries with visually confirmed spot modulation (abstract checked); the
  comparable figure here is the credible-signal share (0.43-0.59), not the pipeline share. Add that condition to
  ledger row A2.
- "Climbs towards half among the stars with the best data" is supported (0.46 at four or more sectors, cool).

### 11. H2: the right label, a one-sided diagnosis (minor)

**Evidence.** Inconclusive is correct under plan.md lines 48-50, and the eccentricity-noise diagnosis is right: the
median Gaia e error is 0.04-0.09 and SB1C solutions are essentially absent (0.7% at P < 1 d, zero elsewhere). But
P_circ,50 was estimable post hoc: with e minus twice its error below 0.05 the circular share is 0.78-0.83 below
5 d and 0.28 at 20-30 d; with e below twice its error it falls through one half at 7-10 d (`checks.json` section
11). P_sync,50 stays undefined because the detections are diluted (finding 1), not because of physics; on credible
signals the cool share is 0.43-0.59. The report blames only the circular side (report.md lines 118-119).

**Fix.** Say both halves failed on measurement; report the noise-aware P_circ,50 as post hoc.

### 12. The detection rule is not a selection (minor, for the record)

**Evidence.** FAP < 1e-5 fires in 84.7% of TESS-SPOC sectors (94.6% bright, 74.4% faint), and 32% of detections have
FAP exactly zero (`checks.json` section 1). On red-noise light curves the Baluev FAP admits almost everything, so
the effective criterion is that a light curve exists; the 1,792 no-detection stars are the quietest ones. The plan
fixed the rule in advance, so this is not a deviation, but the report should say it in those terms rather than as
a "white-noise threshold admits many periods".

## Gate summary

- G1: real; no label-correlated field found; the period search never sees the orbit.
- G2: coverage.json present; the 338 grid-miss drops are missing and mislabelled (finding 5).
- G3: three traces match the tables; the single-star comparison is missing (finding 9).
- G4: denominators are judgeable; the catalogue swap is undocumented and the audit is single-rater (finding 9).
- G5: passes mechanically; re-label rows 1, 11, 12, 25, 26 (findings 2 and 10).
- G6: passes (9 claims, titles confirmed); A1 and A2 verified against abstracts; add the condition to A2.
- G7: declared not applicable but applies to the visual audit (finding 9).
