# Independent review: QuakeScope station-level validation (draft report, commit d497663)

Reviewer: independent adversarial review, 12 October 2026. Scope: plan.md (5bb0f02), deviations.md D1-D4, report.md,
code/, tests/, results/, logs/, the raw phase files and catalogue partitions on disk, and the git history. Everything
below was recomputed with the study's venv (`OMP_NUM_THREADS=2`); the VB main fit, the committed synthetic tests and
the H2 cross-validation were rerun from scratch. Nothing outside `review/` was modified.

## Recommendation: fix first

The preregistration, timing and disclosure are clean, the parsing and matching are correct, and every number in the
report that I could trace to a results file reproduces (table at the end). Two things nevertheless have to be fixed
before the verdict is published, and several claims need editing:

1. The denominator contains station-days that QuakeScope marked `loaded` but on which it produced **zero picks**
   (6.7% of all loaded station-days). Recall there is 0 by construction. These days create the extreme low tail of
   the station distribution that the report interprets as "weak stations", and they are the main thing the
   H1 margin rests on: a VB refit of the same model without those days gives SD_p = 0.095 (sigma_u 1.087, typical recall 93.6%), below the preregistered 0.10. H1 is therefore "Supported" only under the literal `loaded` denominator, and the plan's own rationale for excluding unread days ("a miss there is not a picker failure") applies to days on which the catalogue has no output at all.
2. The D4 claim that the AGHQ cross-check "recovered a known station SD of 1.074 as 1.073" is not reproduced by the
   committed test (`tests/aghq_test.py` gives sample SD 1.060, ML 1.006-1.011). The implementation is right; the claim
   is wrong and must be corrected.

The verdict for H2 (Refuted) is robust to everything I tried. The verdict for H1 (Supported, narrowly) is not robust to
the denominator fix in point 1 and should be reported with that sensitivity, with a revised narrative about the weak
stations.

## Issues

### Major

**1. `loaded` station-days with zero QuakeScope picks are in the denominator and drive the weak-station tail.**
Location: `code/match.py` `availability()` and plan section 3; report sections "The denominator", "H1", "Where the
weak stations are", `results/tables/station_reliability.csv`, Figure 1.

- QuakeScope's availability table has an `npks` column. Among `loaded` station-days of CI, NC and BK, 6.7% have
  `npks = 0` and 17.8% have fewer than 5 picks (`data/raw/availability/*.parquet`, loaded rows grouped by station-day).
- 6,383 of the 509,596 H1 picks (1.25%) fall on loaded station-days with zero picks; their recall is 0.000. Pooled
  recall excluding them is 92.2% instead of 91.0%. Recall rises monotonically with the day's pick count: 65% on days
  with 1-2 picks, 82% on 3-5, 87% on 6-10, 89% on 11-20, 91% on 21-50, 94-96% above 50. Relative to each station's
  median daily count, days with less than 10% of the usual picks have 57% recall, 10-25% have 76%.
- The worst stations in the released table are largely this artefact: BK.BABI (84% of its picks on zero-pick days,
  raw recall 0.12, 0.78 without those days), NC.KTJ (68%, 0.28 to 0.86), BK.BARR (49%, 0.48 to 0.93), CI.WLH2 (47%,
  0.53 to 0.997), NC.HLO (37%, 0.46 to 0.74), CI.BTC (27%, 0.65 to 0.89), BK.RUSS (26%, 0.59 to 0.79). 40 stations
  have more than 10% of their picks on such days. Spearman(u, share of zero-pick days) = -0.23 among the 949 H2
  stations. The raw-recall SD across the 949 stations falls from 0.115 to 0.103 when these days are dropped.
- The clearest case is CI on 2017-01-01 (an Imperial Valley swarm day, 2,191 reference picks, recall 35%): stations
  WMD, COK2, CLI2 and GLA are `loaded` with `npks = 0` and have no pick in the partition at all, while neighbours
  (IMP, COA, YUH2) have 700-940 picks. The whole CI partition has 17,856 picks that day against 44,000-57,000 on the
  following days. 2015-07-09 (734 picks) and 2012-09-01/02 (353) are the next largest. This is also why recall on the
  first day of a month is 84% against 91% mid-month; it is not a partition-edge effect (partitions are by month of
  `peak`; no leakage, checked on five partitions).
- The QuakeScope site says the western catalogue "is being re-read from 2026-10-08 to add station-days a reader
  defect skipped". Zero-pick loaded days are very plausibly that defect. The report mentions the re-read but does not
  connect it to the denominator.
- Effect on H1: a VB refit on the 503,204 picks that remain (1,025 stations; same code, same model, `analysis.fit`) gives intercept 2.916, M 0.648, log10 d -1.032, sigma_u 1.087, typical recall at the reference event 93.6%, and SD_p = 0.0953 (point estimate; I did not run the 200-refit bootstrap, which takes about 4 h with 13 workers). The logit-scale spread is unchanged; the probability-scale SD falls because the ceiling rises. Under this denominator the preregistered rule cannot return "Supported"; whether it returns "Inconclusive" or "Refuted" depends on the bootstrap upper bound, which must be computed. The tail moves as well: 10th percentile 79% (report: 76%), 5th 70% (66%), 11.2% of stations below 80% (14.0%), 29.8% below 90% (35.1%); 12 stations leave the bottom decile; the new station effects correlate 0.94 with the originals. H2 on the same effects: R^2 0.357 (0.284-0.419), linear 0.359, so H2 stays Refuted.
- Effect on the interpretation: the report's "one station in ten finds fewer than 76%", the 5th percentile of 66%, the
  left tail of Figure 1 and the map all include stations whose low recall is a processing or data failure, not a
  sensor or site property. H2 cannot be expected to predict processing failures from station attributes, so part of
  the "unexplained" variation is this too.

Fix: keep the preregistered denominator as the primary (the plan said `loaded`), but add a post-hoc sensitivity
analysis that excludes loaded station-days with `npks = 0` (and, as a second variant, days with fewer than 10% of the
station's median count): pooled recall, SD_p with its bootstrap, the tail quantiles, and the station table. Add a
`zero_pick_day_share` column to `station_reliability.csv` and flag stations above 25%. Rewrite "Where the weak stations
are" and the plain-terms summary so that the extreme tail is attributed to days without catalogue output, and link
it to the announced re-read. State the H1 verdict under both denominators.

**2. The AGHQ synthetic-test claim in D4 is not reproduced.** Location: `deviations.md` D4 item 2 and addendum
("a known station SD of 1.074 (sample) was recovered as 1.073"; "The synthetic test gives the same answer as before");
report section "An independent maximum-likelihood fit" ("recovers a known station SD on synthetic data").

Running the committed `tests/aghq_test.py` (seed 5, default S = 400) gives sample SD 1.060, recovered 1.006 (Laplace)
and 1.011 (15 nodes). S = 300: 1.055 recovered as 1.027; S = 200: 1.058 as 1.001. There is no S for which the
printed sample SD is 1.074. On the same S = 400 data the study's own VB fit gives 1.019, and a brute-force
`scipy.integrate.quad` profile of the marginal likelihood also has its minimum near sigma = 1.0. So the AGHQ code is
correct (I checked the adaptive rule, the Laplace special case, the normalisation and the mode finding; VB, AGHQ and
brute-force agree), but what it shows is that both estimators sit 3-5% below the realised SD in this design, not
that the truth is "recovered". Fix: rerun the test, report the actual numbers, and describe the cross-check as "ML
and VB agree with each other (1.067 vs 1.078 on the real data)". Note the direction: if anything, sigma_u is
underestimated, which favours H1.

### Should be edited before publication

**3. The H1 margin is thinner than the text says, and the report omits the numbers that show it.** Location: report
"H1" and "Limitations".
- The preregistered estimand is computed by Monte Carlo with 10^5 draws. The exact value (Gauss-Hermite quadrature of
  the same integrand) is 0.1045; other MC seeds give 0.1040-0.1046. The report's 0.1049 carries +0.0004 of MC noise.
- 19% of the 200 bootstrap draws fall below 0.10 (bootstrap SD 0.0052; draws 0.093-0.119).
- The preregistered rule was applied correctly (`analysis.h1`), and "Supported" is the rule's answer. The "narrowly"
  framing is fair, but the report should print the quadrature value, the share of draws below 0.10, and the
  sensitivity in issue 1. "Whether the variation clears 0.10 specifically is not settled by these data" is the right
  sentence; it should be in the verdict line, not only in the body.

**4. Sensitivity of SD_p to the logit-normal assumption is in the opposite direction from the one implied.**
Location: report "Limitations". The empirical SD of posterior-mean recall across the 949 stations is 0.115 (0.114 over
all 1,026; 0.098 over stations with >= 100 picks), above the model's 0.105, because the station effects have a long
low tail (skew -0.49 on the logit scale; 1st percentile -2.78 against -2.4 for a normal of the same SD). The
logit-normal summary is therefore conservative for the threshold test. But see issue 1: the tail that makes the
nonparametric number larger is partly the zero-pick artefact. Report both numbers, after the denominator fix.

**5. "Location predicts nothing out of cell ... not a regional pattern" is overstated.** Location: report "What the
attributes do capture" and "For the QuakeScope team". The spatially grouped CV tests transfer across 1-degree cells
only. Within cells there is a modest local correlation: the mean effect of a station's 5 nearest neighbours
(median 14 km) correlates r = 0.33 with its own effect (r = 0.26 for the nearest, 0.34 for 10); a plain 5-fold CV on
latitude and longitude alone gives R^2 = 0.07, and adding location to the four attributes under plain CV gives 0.39
against 0.33 without. The map and the report's own regional shares show the same clustering. Fix: "no pattern at the
100-km scale that transfers between cells; local correlation is modest (r about 0.3)". Drop "not a regional pattern".

**6. The regional shares are irreproducible.** Location: report "Some areas have more than their share" (18% Los
Angeles basin, 13% Long Valley, 14% Bay Area, 9% elsewhere). No box coordinates appear in the report, `checks.py`,
`figures.py` or any results file. With guessed boxes (33.6-34.4N/118.7-117.6W; 37.4-38.2N/122.7-121.7W;
37.4-37.9N/119.2-118.6W) I get 18%, 13%, 17% and 9%. Fix: put the boxes in `checks.py misc` and in the text, or
drop the sentence.

**7. The false-pick proxy section needs stronger caveats and would be accepted by a seismologist only as a flag.**
Location: report "Exploratory: a false-pick proxy", verdict bullet 4, "In plain terms", "For the QuakeScope team".
- "Noise detections. The likely majority." is asserted without evidence. A quick diagnostic supports it partly and
  should be added: in three sampled months (2019-06, 2015-09, 2023-03) isolated unreferenced picks have a clear
  diurnal cycle, 1.2-1.3x the uniform rate at 07-15 h local time and 0.75-0.85x at night, while referenced picks and
  non-isolated unreferenced picks are flat (daytime share 55-58% against 45-49%). That is the signature of cultural
  noise, not of small earthquakes (which are detected more at night). It does not quantify the share.
- The 0.9% versus 62% "validation" is only a sensitivity check. Referenced picks come from M >= 1.5 events recorded
  at many stations, so they cannot be isolated by construction; the comparison says nothing about whether isolated
  unreferenced picks are noise or small events. Say so.
- Neighbours that lacked data: 85% of isolated unreferenced picks have all five neighbours loaded that day and 0.3%
  have two or fewer (same three months). State this directly instead of bounding it with the 0.9% figure, which only
  covers M >= 1.5 events.
- Events below M 1.5 are "unreferenced" by construction, and they are the great majority of catalogued events in both
  regions; the text should say that "unreferenced" means "no M >= 1.5 analyst pick within 100 km", not "no earthquake".
- Only CI, NC and BK stations are candidate neighbours. In the Geysers (BG), the strong-motion networks (CE, NP) and
  the Plate Boundary Observatory (PB) are excluded. BK's isolated share is 77-82% against 59-60% for CI and NC,
  consistent with sparser neighbours.
- The 59% depends strongly on the 0.5 threshold: isolated unreferenced picks have median confidence 0.65 (quartiles
  0.56-0.79) against 0.94 for referenced picks. Report the share at 0.7 and 0.9 as well.
- "about 0.4 P picks per second": the sampled partitions hold 38.9 million P picks of any confidence over about
  78.9 million seconds, i.e. 0.49 per second. Fine as "about 0.5".
- A useful scale for readers: 9.4 isolated confident picks per loaded station-day against 0.86 analyst-picked
  M >= 1.5 arrivals per station-day.

**8. Reference heterogeneity is a threat to H1's interpretation that the report underplays.** Location: report "H1"
and "Secondary analyses". Recall depends strongly on the analyst's weight and onset: SCEDC 97.7% at weight 1.0, 94.2%
at 0.8, 89.0% at 0.5, 78.2% at 0.2; NCEDC 94.3% at 1.0, 92.6% at 0.75, 86.4% at 0.5, 69.9% at 0.25; impulsive 94.7%
against emergent 86.2%. The model adjusts for magnitude and distance but not for these, and the share of low-weight,
emergent picks differs between stations and between the two data centres. On impulsive picks alone SD_p is 0.086,
below the H1 threshold. The report should say plainly that H1 does not hold on the impulsive subset and that part of
the between-station variation is in what analysts chose to pick at a station. A secondary fit with weight (or onset)
as a covariate would separate the two; it costs one VB fit.

**9. PhaseNet's `original` weights were trained on NCEDC analyst picks.** Location: report "The data" ("trained on
Northern California data") and "What this does not show". Zhu and Beroza trained on "more than seven million
waveform samples extracted from over thirty years" of NCEDC analyst-labelled arrivals, so the NC and BK reference
picks from 2010 to about 2017 overlap the training distribution and possibly the training events themselves. The data
show no sign that this inflates recall (NCEDC 89.9% for 2010-2017 against 89.4% for 2018-2024; SCEDC 93.2% against
92.2%), which the report can and should state, together with the caveat.

**10. Related work is missing from the novelty statement.** Location: plan "Novelty check" and report. Two prior
validations of PhaseNet against analyst picks should be cited as the nearest work: Münchmeyer et al. (2022, JGR Solid
Earth, "Which picker fits my data?"), a multi-dataset benchmark against analyst picks including PhaseNet; and the 2025
ESS Open Archive preprint "Performance of the deep-learning phase picker PhaseNet on magnitude 3+ earthquakes in
Southern California" (PhaseNet against SCSN analyst picks; not retrievable in full from here, 403). Neither is an
archive-wide, station-level validation of QuakeScope, so the novelty claim stands. The QuakeScope page lists its own
sequence benchmarks (Ridgecrest, San Simeon, Monte Cristo, Mendocino 2024, Monroe WA; Kaikoura, Norcia, Thessaly;
OBS), consistent with the plan's description. One possible discrepancy: the plan says the 2025 archive was "mostly
`jma_wc`", while the QuakeScope page describes the 2025 incumbent weight set as `instance`; check and correct (the
2025 archive is not used, so this is cosmetic).

**11. The one-word verdict tag.** Location: report first line. "Refuted" for a study whose first hypothesis is
Supported, whose headline descriptive result is favourable to the catalogue (91% recall, near-analyst timing), and
whose plan set no headline rule, will be read as "the catalogue failed". The parenthetical is right; the tag should be
"Mixed" (or "Refuted (H2)"), and the lead's compound hypothesis should be quoted so the reader sees which half failed.

### Minor

**12. "broadband HH stations (n = 287)" counts band code H, which includes 9 HN accelerometer stations.** HH alone is
278 stations, median 95.2%. Fix the label or the number.

**13. The noise covariate contains physically implausible values.** 33 stations have log10 RMS velocity above -6
(more than 1 um/s in 1-10 Hz at 01:00-02:00 local; CI.SHE -4.16 is 69 um/s, CI.TPC -4.43, NC.KTJ -4.80) and 32 are
below -8.7 (below the low-noise model; NC.LEL -9.37). These are response, metadata or dead-channel problems, not site
noise; NC.KTJ is also a zero-pick station (issue 1). 495 of 949 stations have fewer than the full 180 windows and 14
have fewer than 60. The plan's FDSN dataselect fallback was not implemented (21 "no data" stations). None of this
changes H2 (trees are rank-based and the linear model agrees), but the Limitations should say that part of the
noise-recall association is "broken station" detection, and the released table should carry the window count.

**14. S recall denominator.** "Pooled S recall 88.8% (196,118 S picks)" uses all loaded S picks; the SD_p row uses the
>= 10-pick stations (195,079). Label which.

**15. Reference-pick counts.** `parse.py` keeps 574,142 P picks; 9 are dropped in `match.py` because their arrival
time falls in the following, unsampled month (12 picks of both phases; 783,837 to 783,825). Harmless; say so or drop
them in parse.

**16. Duplicate rows in the catalogue partitions.** 0.6-5.7% of (tid, phase, peak) rows are exact duplicates
(re-reads with different run ids). Harmless for one-to-one matching; the proxy removes them. Mention it.

**17. Misses decompose as follows (useful for the report).** Of the 45,866 unmatched H1 picks: 13.9% are on
zero-pick station-days (issue 1); 15.2% have a QuakeScope P pick 0.5-1.0 s away (80% of those late), which is the
tail that the 1.0 s tolerance recovers (91.0% to 92.3%); 6.4% are 1-3 s away; 56% have no P pick within 300 s. The
nearest-pick histogram has no peaks at integer seconds or constant offsets, so there is no time-zone, clock or format
artefact. The 20 picks I verified by hand against the raw phase files and the partitions were all parsed correctly
(SCEDC origin + travel time; NCEDC minute + implied-decimal seconds, event ID at columns 137-146, magnitude at
148-150, weight codes, distances, location codes such as `02` joined across location codes); the misses were genuine
or just outside the tolerance (-0.517 s and -0.520 s in two cases).

**18. NCEDC status A events.** 18% of M >= 1.5 events in the sampled NCEDC months (405 of 2,285 in a one-in-six
sample of months) have status A and are excluded by D1. State the share; it is a reasonable choice but it removes
unreviewed, often recent, events.

**19. `checks.AGHQ.modes` proceeds silently if Newton has not converged after 400 clipped steps.** Record a flag.
Also, `deviations.md` D4 says `fit_vb` is "not bit-for-bit reproducible"; a fresh unseeded refit reproduced sigma_u to
1e-8 and SD_p to 1e-8, so this is overcautious (fine to keep).

**20. The report's `Reproduce` block omits `code/fetch.py months` and `fetch.py catalogues`.** Minor.

**21. `tests/synthetic_test.py` writes into the real results directory.** It calls `A.h1(d, B=8, workers=8)` with
`A.TAB` left pointing at `results/tables/`, so running the committed test overwrites `results/tables/h1_bootstrap_draws.csv`
with 8 synthetic draws (`tests/smoke_main.py` redirects `A.TAB` to a scratch directory; `synthetic_test.py` does not). I
ran the test during this review and restored the file from git (`git restore`; content verified identical to the
committed version, 201 rows, first draw 0.10599). Fix: redirect `A.TAB` in the test as the smoke test does, or have
`h1` take an output path.

## What was checked and holds

- **Timing and disclosure.** plan 5bb0f02 (16:40 NZDT, 11 Oct) before code ac2ad99 (16:51); D2 parse fix f9b9820
  (17:40); `reference_picks.parquet` 17:44; `covariates.parquet` 19:15; `matched.parquet` 19:38; first analysis run
  crashed 00:59 (12 Oct) in the H2 linear check with nothing printed (`logs/analysis_run1_crashed.log` holds only
  HGB binning warnings from the -inf covariate and the traceback; `primary.json` was written only after H2 in that
  version); D3 commit 01:02; rerun finished 05:27; D4 checks 05:33-05:58; report 06:00. `match.py` and
  `analysis.py` were unchanged between ac2ad99 and the matching run except for the D3 edits, which are code-only.
  Nothing post hoc is presented as confirmatory; D4 items are labelled.
- **Parsing.** Verified column positions against the raw Hypoinverse Y2000 files (NCEDC's variant has the ID at
  137-146 and the preferred magnitude at 148-150; header magnitude equals the catalogue magnitude for all 12,828
  events checked; all events join to the catalogue). SCEDC headers all have 10 fields, phase lines 13; weights 1.0,
  0.8, 0.5, 0.2, 0.0; onsets i, e, '.'. Station lines beginning with digits (CE, NP strong-motion stations) are
  correctly not taken as headers because of the length test. Times are UTC throughout (timing residual median
  +0.022 s). De-duplication leaves no duplicates on (source, event, net, sta, phase).
- **Matching.** `greedy_match` is correct (closest-first, one-to-one; the synthetic test's three cases pass).
  Partitions contain only picks of their month. The availability join is per station-day across location codes; the
  modal read band equals the analyst's modal band for 97.8% of stations.
- **H1.** The VB fit reproduces exactly; the bootstrap percentiles reproduce from `h1_bootstrap_draws.csv`
  (200 draws, no NaN, distinct labels); the VB flag explanation (BFGS precision-loss stop at gradient norm 1e-4,
  identical ELBO over three seeds) is right; the AGHQ implementation is right and VB and ML posterior/conditional SDs
  agree (ratio 1.002).
- **H2.** CV R^2 and its bootstrap reproduce exactly; the categorical mask is `[True, True, False, False]` with int8
  codes and NaN for missing; HGB is deterministic here (seeds 1-3 identical); the reliability correction
  R^2/(1 - noise share) is the right correction under uniform shrinkage (derived); the linear model agrees (0.288).
  Refuted is the right reading under every variant tried (plain KFold 0.33; with location 0.39; ML target 0.29).
- **Synthetic test (D1).** Reproduced: true SD_p 0.1592, estimated 0.1576; H2 R^2 0.618.
- **Facts about QuakeScope.** 4.3 billion picks, re-read from 2026-10-08, 2025 DocumentDB retired 2026-10-12
  (issue #59) all confirmed from the QuakeScope site and GitHub.

## Recomputed numbers

| Quantity | Report | Recomputed | Status |
|---|---:|---:|---|
| Reference P picks / stations / events | 574,133 / 1,373 / 23,316 | 574,133 / 1,373 / 23,316 | ok |
| Loaded share, listed share | 88.8%, 99.6% | 88.79%, 99.55% | ok |
| Denominator picks / stations / events | 509,760 / 1,058 / 23,038 | same | ok |
| H1 set (>= 10) picks / stations; H2 stations | 509,596 / 1,026; 949 | same | ok |
| By source: SCEDC / NCEDC (NC, BK) | 230,292 / 279,468 (239,858, 39,610) | same | ok |
| Median M (10-90), median distance (10-90), impulsive | 1.94 (1.57-2.75), 50 (16-88), 56% | 1.94 (1.57-2.75), 49.9 (15.6-87.6), 55.9% | ok |
| Pooled P recall 0.2 / 0.5 / 1.0 s | 86.4 / 91.0 / 92.3% | 86.36 / 91.00 / 92.34% | ok |
| Pooled S recall (n) | 88.8% (196,118) | 88.80% (196,118) | ok (see 14) |
| SCEDC / NCEDC recall | 92.6 / 89.7% | 92.58 / 89.70% | ok |
| Timing median (MAD); within 0.1 s | +0.022 (0.022); 85.9% | +0.022 (0.022); 85.9% | ok |
| Timing by band HH / EH / HN | +0.03 / +0.02 / +0.023 | same (timing_by_band.csv) | ok |
| Recall by year; <= 10 km; 60-100 km | 88-93%; 91.9%; 90.8% | 88.0-92.6%; 91.9%; 90.8% | ok |
| SD_p, 95% CI | 0.105 (0.096-0.114) | 0.10489 (0.09555-0.11432); quadrature 0.1045; 19% of draws < 0.10 | ok, see 3 |
| sigma_u; intercept, M, log10 d | 1.08; 2.64, 0.58, -0.88 | 1.0780; 2.635, 0.582, -0.878 (fresh refit identical) | ok |
| Typical recall; median; 10th; 5th; < 80%; < 90% | 92.4; 92.7; 76; 66; 14%; 35% | 92.44; 92.67; 76.05; 66.15; 14.0%; 35.1% | ok |
| SD_p at other events | 0.088 / 0.121 / 0.123 / 0.149 | same (misc.json) | ok |
| Secondary SD_p 0.2 s / 1.0 s / S / impulsive | 0.107 / 0.106 / 0.176 / 0.086 | 0.1069 / 0.1063 / 0.1758 / 0.0856 | ok |
| Busiest month share | 6.2% (2020-06) | 6.25% | ok |
| Weak stations: n; EH of them; EH of all | 95; 78; 476 | 95; 78; 476 | ok |
| CI EH median (n); CI HH median (n); NC EH median (n) | 79% (83); 95% (287); 91% (393) | 78.8% (83); 95.2% (278 HH; 287 = HH+HN); 91.3% (393) | see 12 |
| Regional shares LA / Long Valley / Bay / elsewhere | 18 / 13 / 14 / 9% | 18 / 13 / 17 / 9% with guessed boxes | see 6 |
| H2 R^2 (CI); linear; + secondary | 0.29 (0.22-0.36); 0.29 (0.22-0.35); 0.32 (0.25-0.39) | 0.2912 (0.2154-0.3554); 0.2876; 0.3216 | ok |
| Noise share; corrected R^2 | 6%; 0.31 | 6.17%; 0.3103 | ok |
| Exploratory R^2 rows | as table | all match h2_exploratory.csv | ok |
| Band / noise tercile / missing means; Spearman | -0.39, +0.38; -0.54, +0.38; -0.67; -0.36 | same (h2_descriptive.json) | ok |
| 908 H instruments; 923 at 100 Hz | | 908; 923 | ok |
| VB refits: iterations, gradient norms, sigma_u, SD_p; L-BFGS-B | 700-790; 6e-5 to 4e-4; 1.0780; 0.10489; 36, 0.1051 | 698-788; 6.4e-5 to 3.6e-4; same; same | ok |
| AGHQ 1 / 15 nodes | 1.065, 0.1041; 1.067, 0.1044 | same | ok |
| Level alignment; Spearman(u, raw) | 1,026/1,026; 0.98 | true; 0.979 | ok |
| Preregistered proxy | 7,485 / 9,391,601; 0.013 per day | same | ok |
| NN proxy: isolated-unreferenced; share; per day; median; 90th; Spearman | 5.57 M; 59%; 9.4; 3.6; 23; +0.28 | 5,573,810; 59.3%; 9.36; 3.56; 23.2; 0.281 | ok |
| Isolated given referenced / unreferenced | 0.9% / 62% | 0.93% / 62.3% | ok, see 7 |
| Median neighbour distance | 18 km | 18.2 km (all), 17.5 (H2 stations) | ok |
| "about 0.4 P picks per second" | 0.4 | 0.49 (38.9 M picks / 78.9 M s) | approx. |
| Missing noise: 25 (22 + 3) | | 21 no data + 1 no response + 3 zero RMS | ok |
| D1 synthetic test | 0.158 vs 0.159; R^2 0.62 | 0.1576 vs 0.1592; 0.618 | ok |
| D4 AGHQ synthetic test | 1.074 recovered as 1.073 | 1.060 recovered as 1.006 (K=1) / 1.011 (K=15); S=300: 1.055 to 1.027; S=200: 1.058 to 1.001 | **not reproduced** |
| Zero-pick loaded station-days (new) | not reported | 6.7% of loaded station-days; 6,383 picks (1.25%) at recall 0; pooled recall 92.2% without them | see 1 |
| SD_p without zero-pick days (new) | not reported | 0.0953 (sigma_u 1.087; typical recall 93.6%; no bootstrap); H2 R^2 0.357 (0.28-0.42) on the same effects | see 1 |
| Tiles, figure captions, figures | | match primary.json and tables | ok |
| QuakeScope facts: 4.3 billion; re-read 2026-10-08; 2025 DB retired 2026-10-12 | | confirmed (Seismica abstract, seisscoped.org, issue #59) | ok |

Sources used for the web checks: Seismica article page for Ni et al. 2025 (doi 10.26443/seismica.v4i2.1738), the
arXiv abstract of Zhu and Beroza (1803.03211), https://seisscoped.org/QuakeScope/, GitHub SeisSCOPED/QuakeScope
issue #59 and pull request #56, and the search listings for Münchmeyer et al. 2022 (arXiv 2110.13671) and the ESS
Open Archive preprint (doi 10.22541/essoar.176054487.79491512).
