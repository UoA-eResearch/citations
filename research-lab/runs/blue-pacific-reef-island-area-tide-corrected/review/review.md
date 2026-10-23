# Review: blue-pacific-reef-island-area-tide-corrected

Reviewer: Fable 5.1 (independent, adversarial), 2026-10-23. Scripts and outputs: `review/reviewer_checks/`
(`checks_core.py` -> `checks_core.out`, sections A-J; `stac_coverage.py`; `fd_rq_seam.py`; `chips.py` -> `chip_*.png`).
Nothing outside `review/` was modified.

## Verdict: fix first

The preregistered H2 verdict (Supported) survives every re-analysis I ran: 2.08%/yr (1.57-2.65) as reported; 0.87
(0.65-1.15) on islets of 5 ha or more; 1.86 (1.36-2.42) with wrong-sign tide slopes zeroed; 2.12 without the gross
filter; 2.05 with a joint area~level+time fit; 2.17 with a quadratic tide response. The process is honest: the plan
preceded the first area file, D1-D5 preceded the first rates run, and D6 changed one constant and is fully disclosed.

But three things the report says about *why* and *where* are wrong, not merely overstated, and one headline sentence
about H1 rests on an unguarded sensor step the study did not notice. They need fixing before publication:

1. the "mechanism" paragraph (overpass-phase drift, r = 0.97, per-atoll drifts of -25 to +33 mm/yr) misreads a
   per-islet scene-sampling artefact and an algebraic identity as physics (Finding 1);
2. at Tarawa and Kiritimati the primary MNDWI-Otsu area does not respond to the gauge at all, so their "corrected"
   rates are not tide-corrected, and the Kiritimati row is manufactured by a wrong-sign slope on 20 images
   (Finding 2);
3. the early epoch is a median of 5 Landsat 7 images (1999-2012) against 20 Landsat 8 images (2013-2015) per islet,
   so "taken at face value, the epochs show no speed-up" is a Landsat 7 vs 8 vs Sentinel-2 comparison, not an epoch
   comparison (Finding 3);
4. no atoll has Sentinel-2 before 2017, and Funafuti and Tarawa have none before late 2019; "2016-2026" and "the
   decade" are wrong for 36 of the 150 islets (Finding 4).

## Findings

### 1. (Major) The H2 "mechanism" is a tautology plus sampling noise; the per-atoll drift numbers are not atoll properties

**Claim** (report.md:14-16, 118-122; plain terms 39-42; h2_diag.py:8-9): the bias "tracks each islet's tide
sensitivity times the drift in water level at image time (r = 0.97)", the drift "runs from about -25 mm/yr (Tarawa)
to +22 mm/yr (Majuro) ... and +33 mm/yr at the two Kiritimati islets", because "satellites pass at a fixed local
time, so they sample the tide at a slowly drifting phase".

**Evidence** (`checks_core.out` B, D):
- r = 0.97 is the definition of the correction, not a test of it. Uncorrected minus corrected = TS(y) - TS(y - beta h),
  which is beta x trend(h) up to Theil-Sen's non-linearity. With OLS in place of Theil-Sen the correlation is exactly
  1.000 (section D). It cannot fail, so it is not evidence for any mechanism.
- The "drift" per atoll is the *median of per-islet* Theil-Sen trends of the level at each islet's own usable scenes
  (h2_diag.py:51, 67). Within one atoll those per-islet trends span roughly +/-100 mm/yr (10th-90th percentiles:
  Funafuti -119 to +102, Tarawa -168 to +62, Kwajalein -40 to +90, Majuro -33 to +63). Every islet at an atoll shares
  the gauge and the overpass times, so this spread is entirely which scenes passed the cloud screen for which islet.
- Computed once per atoll on the union of acquisitions, the level trend at image times is -21 (Funafuti, bootstrap
  -64 to +13), -15 (Kiritimati), -5.5 (Kwajalein), -11 (Majuro), -2.8 (Penrhyn), -12 (Tarawa, -52 to +25) mm/yr. None
  is distinguishable from zero. The report's Majuro +22, Kiritimati +33 and Tarawa -25 are medians of noisy per-islet
  values and do not match (-11, -15, -12).
- Fixed-local-time sampling of a tide aliases to periods of weeks (M2), a year (K1) or a constant (S2); it does not
  produce a decade-long monotonic drift. The daily-mean component on image days trends -7 to +10 mm/yr and the
  tidal-anomaly component -1 to -20 mm/yr (section B), both inside their noise.
- The permutation floor (0.29) shuffles levels and so also destroys beta; it is the floor for "no tide response at
  all". The relevant floor, keeping beta and propagating its standard error against the observed level trend, is
  0.20%/yr (section D), so the conclusion "the bias is not noise in the sense of a flat statistic" holds, but the
  framing is muddled: the bias *is* produced by sampling noise in the levels, which is precisely what the correction
  removes.

**What is true and worth saying instead**: any finite sample of ~75 overpass tide levels has a non-zero trend by
chance (SE 30-60 mm/yr per islet); with |beta| of 35-70% of area per metre that becomes 1-3%/yr in an uncorrected
rate, in a direction that differs from islet to islet and atoll to atoll. That is a stronger practical argument for
per-image correction than a putative orbital drift, and it is what the data show.

**Fix**: rewrite report.md:14-16, 118-122 and the plain-terms paragraph; drop "fixed local time ... drifting
phase", the per-atoll drift column of the table (or replace it with the union-of-acquisitions value and its CI), and
the r = 0.97 claim (or state it as the identity it is). Keep the verdict.

### 2. (Major) At Tarawa and Kiritimati the primary index does not respond to the tide; the "correction" there is noise, and one row is an artefact

**Claim** (report.md:112-113, 122): Tarawa's islets "barely respond to the tide (median +2% per metre)"; Kiritimati
corrected rate -2.30%/yr, bias +2.78.

**Evidence** (`checks_core.out` A, C; `chips.out`; `chip_tarawa_015_low.png`, `chip_tarawa_015_high.png`):
- Lag scan of the pooled within-islet correlation between area and gauge level: Funafuti -0.90, Kwajalein -0.81,
  Majuro -0.73, Penrhyn -0.54, all peaking at lag 0 (the gauges are correctly aligned). Tarawa +0.09, Kiritimati
  +0.00, with no lag between -6 and +6 h giving a correlation beyond -0.17.
- At the same Tarawa islets the *sensitivity* indices do respond with the right sign: MNDWI < 0 area r = -0.37, NDWI
  area r = -0.33. So the failure is Otsu's, not the gauge's or the islets'.
- 12 of 20 Tarawa islets and 1 of 2 Kiritimati islets have a positive fitted slope; 16 of 20 Tarawa slopes are not
  significantly negative. Elsewhere: 1 of 128.
- Imagery: tarawa_015 (21 ha) measures 14.1 ha of Otsu land at -1.10 m and 28.4 ha at +0.39 m. At high water the
  Otsu threshold moves from 0.06 to 0.32 and the mask swallows the bright shallow water over the reef flat around the
  islet (the three-class problem D5 already met at Penrhyn, now in the other direction). Its fitted slope is +62% per
  metre and its "corrected" rate -8.2%/yr.
- kiritimati_001 (36 ha, n = 20, the minimum): r = +0.53, slope +21% per metre, uncorrected rate -1.44, "corrected"
  -6.67%/yr. The Kiritimati row of the table (two islets, mean -2.30, bias +2.78) is this artefact.
- With slopes set to 0 unless significantly negative: Tarawa -1.66%/yr (reported -0.81), Kiritimati +0.47 (reported
  -2.30); H2 1.86 (1.36-2.42); pooled -0.35.

**Fix**: report Tarawa and Kiritimati as atolls where the primary index fails the tide-response check and give their
rates from the MNDWI < 0 or NDWI series (or constrained slopes) with that caveat; delete the Kiritimati row (two
islets, one of them a wrong-sign artefact, is an islet-level number for a named 36 ha island, see also Finding 6);
replace "barely respond to the tide" with the measurement failure it is; add a preregistered-style guard for future
runs: a slope used for correction must be negative beyond 2 SE, otherwise the islet is flagged.

### 3. (Major) The early epoch is an unguarded Landsat 7 -> Landsat 8 step; "no sign of faster loss" is not a face-value epoch comparison

**Claim** (report.md:22-23, 135-138, 144-145, 196-197; plain terms 46-47): without the guard D = +0.15 (-0.52 to
+0.86), "Inconclusive, pointing if anywhere to slower, not faster, loss"; "Taken at face value, the epochs show no
speed-up"; "a median of 25 usable Landsat images per islet over 1999-2015".

**Evidence** (`checks_core.out` F; `f_e1_platform_step.csv`):
- For the 33 H1 islets, E1 usable images are LE07 101 (1999-2003) + 81 (2004-2012) + 4 (2013-15) and LC08 705
  (2013-2015); no LT05 at all. Per islet: median 5 Landsat 7 images over 1999-2012 and 20 Landsat 8 images in
  2013-2015. The "17-year" Theil-Sen slope is therefore mostly (L8 level - L7 level) / ~12 years.
- The E1 Theil-Sen rate correlates 0.67 with each islet's Landsat 8 minus Landsat 7 corrected-area difference. An
  OLS trend with a platform fixed effect averages +0.46%/yr against +0.14 without it (and the Theil-Sen mean is
  -0.48: the series are heavy-tailed enough that OLS and Theil-Sen disagree in sign).
- Landsat residual SD after the tide fit is 19% of OSM area (Sentinel-2: 9%); 70% of the L7 scenes are Tier 2 (no
  ground control, geolocation not guaranteed).
- The plan's guard tests only Landsat 8 against Sentinel-2. Nothing tests Landsat 7 against Landsat 8, and the
  report does not say that E1 is itself a two-sensor series.

**Fix**: state the E1 composition (5 L7 images 1999-2012, 20 L8 images 2013-2015 per islet) wherever E1 rates are
quoted; remove "pointing if anywhere to slower, not faster, loss" and "taken at face value, the epochs show no
speed-up" (or make them explicitly conditional on an untested L7 = L8 assumption); add the L7-vs-L8 step as a
limitation of the design, not only "the early epoch is thin".

### 4. (Moderate) The Sentinel-2 epoch is not 2016-2026 anywhere, and is 6.8 years at Funafuti and Tarawa

**Evidence** (`stac_coverage.out`; `checks_core.out` I): Earth Search has zero Sentinel-2 items (L2A, C1-L2A or L1C)
over Kanton and Kapingamarangi before 2022, over Funafuti and Tarawa before 2019, and over Majuro before 2017. This is
the archive, not a search bug in scenes.py (the Kanton/Kapingamarangi statement in the report is correct). But the
used E2 windows are Kwajalein/Majuro/Penrhyn 2017-01 to 2026-08 (9.6 y), Kiritimati 2018-06 to 2026-05, Funafuti and
Tarawa 2019-10 to 2026-08 (6.8 y; per-islet median span 6.6 y). The report says "every usable Sentinel-2 image from
2016" (line 3), "2016-2026" throughout, "the decade"/"a decade's area trend" (title, lines 24, 39, 49, 120, 198) and
"over 2016-2021" for the guard's Sentinel-2 side, whose spans are 4.65-4.98 years starting 2017.

**Fix**: give the actual window per atoll in the methods and the table; say "2017-2026 (2019-2026 at Funafuti and
Tarawa)" instead of "2016-2026"; drop "decade" where it covers Funafuti and Tarawa.

### 5. (Moderate) The guard: not opportunistic, but its precision is overstated and its construction has three weaknesses

**Evidence** (`checks_core.out` E):
- D6 is not outcome-selecting in effect: every span threshold from 3.0 to 4.5 y and 15 or 20 scenes gives a mean
  Landsat-minus-Sentinel-2 difference of +0.86 to +1.24 with the lower bootstrap bound above 0 (13 to 44 islets).
  At 5.0 y the set is empty. The study's reading (sensors disagree) is right.
- But the bootstrap resamples islets within atolls as if independent. The 13 islets are 6 at Majuro, 6 at Kwajalein
  and 1 at Penrhyn, and islets at an atoll share the same Landsat scenes, dates and tides. Per atoll the mean
  difference is +1.77 (Majuro), +1.19 (Kwajalein), -1.59 (Penrhyn); one islet (majuro_010, S2 rate -4.6) contributes
  +5.4 and without it the mean is +0.9. The effective sample is three atolls, and "six times the tolerance" (report
  line 130) should not be stated with that confidence.
- The windows differ: Landsat 8 includes 2016 (84 scenes), Sentinel-2 starts 2017. Year means of the two sensors'
  corrected areas do not diverge monotonically (differences +3.3, +1.8, +3.0, -2.1, +0.1 for 2017-2021), so a step
  rather than a drift, or window mismatch plus noise, cannot be excluded.
- load_areas (rates.py:46) de-duplicates acquisitions by pixel count and clear share, not by tier, so 313 of 580
  Landsat 8 acquisitions used by the guard islets are kept as Real-Time (RT) processings although a T1 or T2
  processing of the same acquisition exists for most ("RT+T2" 29,732, "RT+T1" 12,020 raw islet-acquisition
  pairs). Tier matters: T2 scenes read +3.7% of area above the islet mean, T1 -1.5%.
- Sentinel-2 at 30 m against 10 m differs by only -0.10%/yr, so the resampling is not the issue.

**Fix**: prefer the final tier when several processings exist (T1 > T2 > RT); restrict the Landsat side to the
Sentinel-2 window; report the guard as "+1.2%/yr over 13 islets at three atolls (2 of 3 atolls positive)" and drop
"six times the tolerance"; keep H1 "not testable".

### 6. (Moderate) kwajalein_078 "possible loss" is a tidal sand cay sampled four times in 2018, and an islet-level loss statement

**Evidence** (`checks_core.out` H; `chip_kwajalein_078_low.png`, `chip_kwajalein_078_high.png`): the feature is a
bright sand cay on a reef flat; "dry" (MNDWI < 0 over 10%) in 95% of lowest-quartile-level scenes and 5% of
highest-quartile scenes among the five borderline Kwajalein features. Its dry share by year is 0.50 (n = 4, 2018
only; there is no 2016-2017 imagery), 0.29, 0.33, 0.80, 0.38, 0.60, 0.40, 0.43, 0.40. The "possible loss" flag
(report.md:167-169) is a tide-phase coin flip on 4 scenes. It is also the one place the report makes a named,
islet-level change statement, which the care note (plan.md:23-26, report.md:210-212) says it will not do.

**Fix**: reword to "one 1.3 ha intertidal sand cay whose detection depends on tide phase; no change can be inferred";
make the possible-loss rule require a minimum number of early scenes and a tide-stratified comparison.

### 7. (Minor) The land screen is outcome-neutral and works; small gaps

**Evidence** (`checks_core.out` H; chips): the dry-land share is cleanly bimodal, with nothing between 0.2 and 0.4 or
between 0.6 and 0.8 except five Kwajalein cays of 1.0-1.7 ha. Removed Penrhyn features: 123 at or below 0.05.
Imagery: penrhyn_126 is a submerged knoll (Otsu "land" is a ring of deeper water around it; the study correctly
measures 0 ha), penrhyn_036 likewise, kwajalein_056 is surf-zone reef flat, penrhyn_099 (lowest kept share, 0.89) is a
real cay. The screen uses the whole record, never a rate. Gaps: (a) the possible-loss rule has no "possible gain"
counterpart (zero cases here, but asymmetric by design); (b) `qa_d5.not_measured_ge_1ha` is `[]` because rates.py:184
tests presence in the area table, which includes rows without any area; three features of 1 ha or more never got an
Otsu area (kanton_000, kiritimati_000, tarawa_000, the main islands, too large for one window), and only Kiritimati's
is mentioned (report.md:156); (c) the screen's borderline outcomes depend on the tide distribution of each cay's
scene sample (3 kept, 2 dropped among the five), which is fine as long as it is said.

### 8. (Minor) Numbers and wording against the tables

Checked and matching: every figure in the H2 table except the drift column's meaning (Finding 1); 2.08 (1.57-2.65);
0.29; 88%; 1.24 (0.46-2.07); 13; D +0.15 (-0.52 to +0.86), mixed +0.97 (-1.55 to +3.49); sensitivities; 150/6; -0.28
(-0.59 to +0.04), median -0.25 (recomputed); 23 engineered -0.58; 79 islets 1-5 ha -0.01; 161,845 and 27,401; 0.6%
and 2.2%; 1.7%; 228/361/133/126; 1.14; DEP 146, r -0.20/-0.15, 8-10%/yr, atoll values; 364 features.
Discrepancies and wording:
- "76 Sentinel-2 images per islet" (line 144): recomputed median 75 (150 islets) and 60 for the 33 H1 islets; "25
  Landsat": 26. Cosmetic.
- h2_diagnostics `by_size` has 76 islets in (1, 5] while h1_h2 has 79 in [1, 5): bin-edge convention; say which.
- "Funafuti's islands look as if they were growing quickly when they were not" (line 40): the corrected rate is
  +0.94%/yr, so they were growing, less quickly.
- "DEP is closer to the corrected rates at Funafuti" (line 178): DEP -1.8 against +1.0 corrected and +4.2 uncorrected;
  the signs disagree, "closer" is a distraction. Same for Tarawa (DEP +2.5 vs -0.8 and -1.8).
- "Sentinel-2 L2A for 2016-2026 (161,845 islet-image records...)" (line 79): the count is after the land screen;
  say so.
- `h1_h2.json` `levels_missing_share` 0.0174 is over retained-islet records; fine, but the text says "1.7% of images".

### 9. Checks that passed (so the reader need not redo them)

- **Git and D6**: plan.md committed 21:48 (598ae71); first (buggy) area file 22:19; D1-D5 committed 22:16-00:53; the
  first rates log at 01:13:26 shows guard 0 islets; the D6 commit (98102c7, 01:13:37) changes only `GUARD_MIN_SPAN`
  plumbing in rates.py and adds deviations text and `h1_h2_run1_before_D6.json`, which differs from the final JSON
  only in the guard block. H1 was Inconclusive with or without D6, as stated.
- **Tide series**: UHSLC fast-delivery and research-quality hourly values are identical (mean 0.0 mm, SD 0.0) over
  2017-2021 at Tarawa, Majuro, Funafuti and Kwajalein, so the RQ->FD seam at 2022-01-01 adds no datum step
  (`fd_rq_seam.out`). Gauge alignment is confirmed by the lag-0 peak at the four responsive atolls.
- **Linearity and the two-step fit**: a joint area~level+time fit changes slopes by a median 0.5% per metre and rates
  by 0.07%/yr; a quadratic level term is significant (p < 0.01) in 25% of islets, changes individual rates by
  0.38%/yr on average, but the pooled rate by -0.03 and H2 by +0.09 (`c_tide_fit_variants.csv`).
- **Gross filter**: without it H2 is 2.12 (1.60-2.67) and the pooled rate -0.31. Not driving anything.
- **Sentinel-2 baseline change (2022-01-25)**: islet-level step +1.35% of area against placebo cuts of -0.42 (2020)
  and -1.24 (2024); within interannual swings. The D4 offset rule cannot be verified from stored outputs, but items
  whose metadata and flag disagree (336 records) read 3.8% lower than same-islet-same-year peers; too few to move a
  rate. The Otsu thresholds do not differ by group.
- **Landsat Collection 1 BQA bits** (measure.py:139-141, 206-209): fill bit 0, cloud bit 4, cloud confidence 5-6,
  shadow confidence 7-8 are correct for Collection 1. TOA conversion without the sun-angle term is correct for
  normalised differences.
- **Cloud rule (D2)**: its only demonstrable effect on rates is the per-islet scene selection that produces the
  level-trend scatter in Finding 1, which the correction removes.
- **Coverage statement**: Kapingamarangi and Kanton have no Sentinel-2 before 2022 in any Earth Search collection
  (archive, not search). Kiritimati's two islets: 3 retained non-engineered features, 2 with enough images; the main
  island is unmeasurable in one window.
- **Care note**: results are by atoll and pooled except the two items in Findings 2 and 6 (a two-islet atoll row and
  a named possible-loss feature).

## Summary of required changes

1. Rewrite the H2 interpretation (Finding 1): drop the orbital-drift mechanism, the r = 0.97 claim and the per-islet-
   median drift column; describe the bias as beta times the chance trend of each islet's sampled levels.
2. Treat Tarawa and Kiritimati as index failures (Finding 2): report them from an index that passes the tide-response
   check, remove the Kiritimati row, and add a slope-sign guard.
3. State the E1 composition and remove the "no sign of faster loss" language (Finding 3).
4. Correct the epoch windows (Finding 4).
5. Re-run the guard with final-tier scenes and matched windows and soften its precision (Finding 5).
6. Reframe kwajalein_078 (Finding 6) and fix the minor items (7-8).

## In plain terms

The study's main number holds up: at these atolls, skipping the tide correction really does change a decade-scale
island-area trend by about 2% a year, and it still does under every alternative way I computed it. What does not hold
up is the story told about it. The "drift" in water level at satellite overpass is not a property of the satellite's
orbit; it is the luck of which cloud-free pictures each island happened to get, and it differs from island to island
on the same atoll. At Tarawa and Kiritimati the island-finding method cannot see the tide at all (it mistakes bright
shallow water for land at high tide), so the "corrected" trends there are not corrected, and one atoll row in the
table is an artefact of that. The claim that the older and newer decades show "no speed-up" rests on an early record
that is really five old Landsat 7 pictures against twenty newer Landsat 8 pictures per island, with no check that
those two satellites agree. And the "decade" is seven years at two of the six atolls. None of this reverses the
headline, but the report should say what the data show and not more.
