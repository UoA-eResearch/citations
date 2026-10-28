# Independent review: auckland-nz-hirds-out-of-sample-exceedance-audit

Reviewer: Fable (adversarial pre-publication review), 2026-10-29. Scripts and outputs: `review/reviewer_checks/`
(c1–c8 `.py` with matching `.out`; three CSVs). No Auckland Council raw value appears in any of them.

## Verdict: publish with edits

The preregistered verdict (H1 Inconclusive, 6-h 10% AEP O/E 1.49, 258 against 172.9 over 1,729 gauge-years at 201
gauges) reproduces exactly from the stored data (c1, c5), the reader and the boundary splice are sound (c2), the
annual maxima are correct to within the 5-minute grid (c3), the HIRDS depths and the AEP convention are right (c1,
HIRDS v4 PDF), and the chronology in git matches the deviations. Nothing I found changes the verdict. What needs
fixing before publication is the inference's stated precision, a mislabelled secondary (the "fitting-site" split), a
remaining class of impossible values that the D6 screen cannot catch, several overstated sentences, and an incomplete
Auckland explanation. Numbered findings follow; the edits in findings 1–5 and 9 are required, the rest are
recommended.

## Findings

### 1. The 9-block percentile bootstrap understates uncertainty (moderate)

- Evidence (`review/reviewer_checks/c4_inference.out`): with the yearly counts in `results/tables/year_by_year.csv`
  the percentile interval reproduces (0.781–2.346). Alternatives on the same nine blocks: t-interval on the yearly
  O/E 0.58–2.44; log-t 0.52–2.21; cluster-robust ratio t(8) 0.55–2.43; bootstrap-t 0.70–2.77. Simulating nine
  years with Poisson counts and lognormal year effects matched to the observed dispersion (extra-Poisson CV 0.79),
  the percentile bootstrap covers the true ratio 83% of the time, not 95%.
- Consequence: the verdict is Inconclusive either way, but the report's "0.78 to 2.35" and the plain-terms "0.8 to
  2.3" (report.md:12–13, 41–42) present more precision than nine clustered years give. The 1-h and 24-h lower bounds
  of 1.01 and 1.06 (report.md:19–20, 95, 97) would not survive a calibrated interval, so no sentence should lean on
  them excluding 1.0.
- The storm-cluster bootstrap (`code/analyse.py:192–200`) resamples 71 storms with the storm count fixed; adding a
  Poisson storm count widens it from 0.95–2.26 to 0.86–2.33 (SD 0.34 → 0.37; the compound-Poisson SD implied by
  the cluster sizes is 0.385, close to the year-block SD 0.40). As coded it is slightly anticonservative and should
  not be read as independent confirmation of the year-block interval.
- Fix: keep the preregistered interval as the registered one, but add a t-based (or bootstrap-t) interval beside it
  and say that with nine blocks the percentile bootstrap is known to be narrow; qualify the storm bootstrap; make
  sure no text implies the 1-h or 24-h intervals exclude 1.0. Also worth one sentence: under the fitted model the
  preregistered rule would return Supported only 31% of the time, and under the null it would return Refuted 42% of
  the time (c4), so Inconclusive was the likely outcome of this design.

### 2. Impossible values remain after the D6 screen, which is per record (moderate)

- Evidence (`c7_spatial_coherence.out`, `c8_...out` part d): Okoraka at Ngatawhiti Road (Northland), 1 September
  2024: five consecutive 1-minute records of 19.5, 17.0, 16.0, 15.0 and 14.5 mm (82 mm in five minutes), giving
  184.5 mm in 1 h (3.3 times HIRDS's 250-year 1-h depth) and 194.5 mm in 6 h (1.6 times the 250-year depth), all
  coded 0; the nearest included gauges at 11–25 km recorded 17–20 mm in the same 6 hours. This is a logger or
  telemetry dump counted as an exceedance at 1 h, 6 h and the 2% level. The D6 rule (`code/maxima.py:58–68`:
  >50 mm in ≤15 min, >150 mm in ≤60 min) cannot see it because no single record crosses 50 mm.
- Scale: 17 primary gauge-years exceed HIRDS's 250-year 6-h depth (6.9 expected if HIRDS held), 11 at 1 h (3.2
  expected), 32 at 24 h (7.5). Most of the largest are spatially coherent storms (Glengarry and Fishers on 8 March
  2018 agree at 11 km; Gabrielle on 14 February 2023), but Hakaru at Tara on 24 February 2023 (343 mm in 6 h,
  131 mm in 1 h, with 91 mm at the nearest gauge 11 km away) deserves a look.
- Sensitivity (`c8` part c): dropping gauge-years above 1.5× the 250-year depth moves 6-h O/E 1.49 → 1.47 (1 h
  1.52 → 1.48; 24 h 1.91 → 1.89); dropping all above the 250-year depth gives 1.41 / 1.40 / 1.77. The verdict is
  unchanged.
- On D6's thresholds: the spike limits are round numbers above New Zealand's short-duration records, so generic; the
  stuck-sensor rule's floor of 2 mm (`maxima.py:63`) was written with the 5.2 mm buoy in view and is not generic (a
  sensor stuck at 1 mm per 5 minutes would pass; I found no such case). The screen touched 4,520 out-of-sample
  records at 6 of the 201 gauges (`c6_...out`), which coverage.json does not count (see G2 below).
- Fix: report the beyond-250-year counts and the sensitivity above; name Okoraka 2024 as a probable fault and either
  exclude it with a stated multi-record rule (e.g. any 5-minute total above a national-record envelope) or leave it in
  and say so; add the record counts removed by D6 to coverage.json.

### 3. The "fitting site" classification by 100 m is wrong for most gauges; the fitting/non-fitting split is mislabelled (moderate)

- Evidence (`c1_overview.out`): `code/analyse.py:49` calls a gauge a HIRDS fitting site only if a listed HIRDS site
  lies within 100 m. Of the 117 included gauges classed "not among HIRDS's fitting sites", 75 have a same-named
  HIRDS site within 3 km, most at 0.10–0.40 km (Akatarawa at Cemetery 0.11 km, Otutu Bush 0.10 km, Te Rangi
  0.10 km, Ben Nevis 0.1016 km, Tadmor at Mudstone 0.17 km, and so on). Coordinates differ between the council
  servers and HIRDS's list by one to a few hundred metres.
- Leakage consequence: none for H1. Every matched site's listed coverage ends in 2015 or 2016, and HIRDS's own
  report gives 2015 (NHD/councils) and 2016 (CliDB) as the data ends, so no non-Auckland gauge can have fed HIRDS
  after water year 2016/17 whatever the matching. The only ends of 2017 are Auckland Council's 58 sites.
- Reporting consequence: report.md:130–131 and secondary.json's `fitting_sites`/`non_fitting_sites` (84 vs 117,
  1.47 vs 1.51) compare "within 100 m of a listed site" with "not within 100 m", not fitting with non-fitting
  gauges. The report's inference that overlap does not matter is therefore not supported by this split.
- Fix: relabel the rows, or redo the split with name matching plus a 1 km radius, or drop it. State that the HIRDS
  report's data-end dates, not the matching, are what make 2017/18 onward out of sample for the Hilltop councils.

### 4. Overstated sentences; G5 rows to relabel (moderate)

- "HIRDS's own mid-century depths fit the observations" and "The observed rate also matches what HIRDS itself
  projects for the 2030s and 2040s" (report.md:25–27, 37–38; overclaim rows 20 and 27, both marked Supported).
  O/E 1.01 has an interval of 0.51–1.62 (wider under finding 1), and depths 10% higher than historical (+1 SE)
  give 0.94: the data cannot distinguish "matches the 2031–2050 depths" from "matches depths 10% higher for any
  reason". Relabel Partially supported; write "is consistent with". In report.md:160–162, "a warming signal arriving
  ahead of schedule" is a causal gloss the study disclaims at report.md:186; drop "ahead of schedule".
- "Every duration and level points the same way" and "A similar or larger excess appears at 1-hour and 24-hour
  durations" (report.md:17, 36; rows 13 and 25). The durations share the same nine years and the same storms: 181 of
  the 258 6-h exceedances also exceed at 24 h, 79 of 154 at 1 h (`c5_bias_control.out`). Relabel Partially
  supported and add "which share the same storms, so this is not independent confirmation".
- Title and row 1: "exceeded about 1.5 times as often as stated" is a point estimate whose honest interval runs from
  about 0.55 to 2.4. The hedge in the title carries it, but the plain-terms range should use the wider interval.
- Row 32, "HIRDS used Auckland data into 2017, which shortens Auckland's test window": the HIRDS report says early
  2017, i.e. inside water year 2016/17; the shortening is the lab's conservative reading of a calendar-year label
  (finding 5). Relabel Partially supported.

### 5. Auckland: the explanation is incomplete and the G1 shift should be owned as a conservative choice (minor to moderate)

- The site list gives the 58 Auckland Council sites an end of 2017; `code/analyse.py:51` moves their window to
  2018/19. The HIRDS v4 report (section 2.2) says Auckland Council's data extend to early 2017, which is inside
  water year 2016/17, so under plan.md's own definition 2017/18 is already out of sample. D1 chose the conservative
  reading from the listed years alone; that is defensible, but the report presents it as a fact about HIRDS.
- Evidence (`c1_overview.out`, `c6b_traces_auckland.out`, `c8` part a): under the primary rules no Auckland gauge
  qualifies whichever start is used (0 with ≥8 complete years from 2017/18; 2 with ≥7). Auckland loses known time to
  2xx grades in every year (18–44% of records), and in 2018/19 additionally to about 15% of the year coded missing
  or synthetic (long gaps), which is why that year is complete for no gauge even with 2xx kept. Under S3 the start
  matters: the pipeline's per-gauge starts (46 of the 70 Auckland gauges shifted to 2018/19, the rest from 2017/18)
  give the reported 12 gauges, 1.55; starting every Auckland gauge in 2017/18 gives 27 gauges, O/E 2.14
  (0.58–4.04), and with ≥6 years 62 gauges, 2.33 (0.47–4.54) (`c6b_traces_auckland.out`).
- Fix: in report.md:143–147 say that 2021/22–2022/23 grades are the main reason and 2018/19's coded gaps the
  second; state that the 2018/19 start is a conservative reading of a calendar-year label that the HIRDS report
  contradicts; add the 2017/18-start S3 row to the post hoc table, still labelled exploratory.

### 6. A co-located duplicate was missed (minor)

- Tasman `HY_Wangapeka_at_Biggs_Tops` and WestCoast `Wangapeka_Biggs_Top` are 0.26 km apart with a median annual
  maximum ratio of 1.02 (`c8` part b): the same gauge served by two councils, both among the 201. The 100 m rule
  (`code/analyse.py:69`) is too tight given the coordinate offsets in finding 3. Impact is one gauge, eight common
  years and one exceedance; drop one and say so in coverage.json.

### 7. D5 understates what changed between the invalid and corrected runs (minor)

- `git diff 8dd1f0f 4d88f23 -- code/` shows, besides the reader fix: (i) `maxima.py` gained the NaN-as-missing rule
  (D4 at deviations.md:106–107 says maxima.py already did this; it did not until D5; in the first run a NaN would
  have propagated through the cumulative sum and nulled every later maximum of that gauge, though no Auckland gauge
  was in either primary); (ii) the S1 upper-bound ceiling was rewritten for float times; (iii) six Hilltop series
  that came back empty in the first fetch (v0 coverage.json: 6) were recovered by the refetch (final: 0), part of
  198 → 201 gauges. None affects the corrected primary's validity, but "no analytic rule changed" (deviations.md:134)
  should list them.
- Chronology checks out: plan.md 13:10 before inventory/fetch code 13:17 and the first fetch log 13:23; D2 13:40 and
  D3 13:50 before analyse.py 13:55; first full run 15:13 (`logs/analyse.log`, v0 table mtimes 15:13); D5 commit
  15:17; the v0 tables were committed later (16:28, with the corrected results) but their mtimes are intact. The
  report discloses the first run and its numbers (report.md:176–180) adequately.

### 8. "Without January–February 2023" removes two months from the numerator only (minor)

- `code/analyse.py:175` with `maxima.py:126` drops windows ending in January–February 2023 from the 2022/23 maxima
  but keeps the full expected count. Dropping the whole year gives 1.20 (`c1`), against 1.17 reported. Immaterial
  here; say which was done, or use the whole-year version.

### 9. Numbers in the report that do not match the tables (minor; fix)

- report.md:172–173: S3 "gives 1.47" — secondary.json and the report's own table say 1.45; 1.47 is the pre-screen
  value (v1_before_screen).
- report.md:112–113: the 52-exceedance cluster has 47 Hawke's Bay, 4 Northland and 1 Wellington; 48 is the Hawke's
  Bay count for all of February 2023 (54), which plausibility.md:34 states correctly.
- report.md:72–73: "within 0.4% of the exact maximum" is true of the 30-gauge-year sample; across all 1,729 primary
  gauge-years the grid is up to 1.9% below the exact maximum and misses two exceedances (Tahekenui at Glenstrae
  2020/21: exact 95.0 vs depth 94.7 vs grid 94.5; Kapoaiaia at Kahui Hut 2023/24), so the exact count is 260 (O/E
  1.50) (`c3_exact_maxima.out`). Say "within 2%, never above".
- `data/hirds_depths_skipped.csv` and coverage.json label five gauges "coordinates outside New Zealand"; their
  inventory coordinates are missing (NaN), which `code/depths.py:69` lets through to the bounds test. Three of them
  (Taranaki 4248 at Opunake WWTP, Lake Ratapiko, Mangaotea Culvert) have 7–9 complete out-of-sample years and
  could have been placed from the site list. Relabel the reason; optionally recover them.

### 10. Framing of the stated-rate null (minor, recommended)

- Because exceedance probability is convex in the depth, an unbiased depth with the stated standard error (about 10%
  of the 10-year 6-h depth) is expected to be exceeded more than 10% of the time. The study's own sensitivities show
  it: O/E 2.39 at −1 SE and 0.94 at +1 SE average 1.67 against 1.49 at the centre, implying an expected O/E of
  about 1.1 if HIRDS were exactly right with its stated uncertainty. The in-sample control (0.89) absorbs part of
  this, which is a further reason the out-of-sample/in-sample ratio (1.49/0.89 = 1.67) is the cleaner comparison.
  One sentence in "What this does and does not show" would do.

### 11. Selection-rule and control tests (no finding; for the record)

- The inclusion rules use two rainfall-correlated fields (known time and the median wet interval). Tests
  (`c1`, `c5`): the resolution rule never varies within an included gauge (0 of 201), so it selects gauges, not
  years; dense and non-dense gauge-years give 1.52 and 1.48; O/E rises with known time (1.33 / 1.42 / 1.58 for
  known 0.90–0.95 / 0.95–0.99 / ≥0.99), i.e. the completeness bias runs downward as the report says; the 80
  dropped years of included gauges contain 7 partial exceedances (8.75%), so dropping them does not inflate O/E;
  completeness 0.80–0.95 gives 1.44–1.55; a minimum of 5–9 years gives 1.43–1.53. One mild upward nudge: over all
  2,527 complete gauge-years regardless of the 8-year rule O/E is 1.43 (0.79–2.13), and the gauges the rule excludes
  have 1.28. Report the all-gauge-years figure.
- In-sample control: the 113 control gauges overlap the primary in only 70 (control is Wellington-heavy, primary
  Hawke's Bay-heavy). On the 70 shared gauges in-sample O/E is 0.88 and out-of-sample 1.41, so the control holds
  where it matters. By council in sample: Marlborough 0.52 (13 of 25 expected over 250 gauge-years), Northland 1.89
  on 37 gauge-years; water years 2015/16–2016/17, fitted by HIRDS but excluded from both windows, give 1.23.

### 12. Reader, boundary, maxima, depths, AEP (checked; sound)

- Refetch at one connection (`c2_refetch.out`): Northland Waitangi at Ohaeawai 2021/22 (20,207 records, 1,923 mm)
  and West Coast Haast at Roaring Billy 2019/20 (16,888 records, 6,314 mm, 312 same-minute tip pairs, the case the
  v0 reader broke) match the stored series record for record in time, value and code. A single request spanning
  28 June–4 July 2022 at Akatarawa at Cemetery returns the same 472 records and 10.6 mm as the stored splice of
  two yearly windows; Hilltop adds no synthetic records at From or To, so `fetch.py:70`'s drop of the shared
  boundary instant loses nothing and the incremental semantics across 1 July are preserved. g4_raw_check.csv is
  convincing for the same reason.
- No exact-duplicate time stamps in 123 M records; `np.interp` returns the post-tip cumulative at a duplicated
  abscissa anyway (`c3`). The grid maximum never exceeds the exact maximum; the window-end year assignment (a window
  ending exactly at 00:00 on 1 July goes to the new year, `maxima.py:119`) is one bin and immaterial.
- HIRDS depths (`c1`): 6-h 10-year depths 43–283 mm across servers, monotone in ARI and duration, SE/depth median
  9.9%, RCP4.5 and RCP8.5 2031–2050 depths +8.0% and +9.2%; the API's ARI 10 carries AEP 0.100. HIRDS v4 fits a
  GEV to annual maxima (the 1 − e^(−λ) formula in its section 3.1.1 is only for the peaks-over-threshold estimate of
  the index median), so AEP = 1/ARI is right. Hawke's Bay's NZ Map Grid conversion is confirmed by same-named HIRDS
  sites at 0.1–0.4 km.

## Gate checks (METHODS.md G1–G7)

- **G1.** The leakage audit in plan.md section 4 is real: the cut-off comes from the HIRDS report, inclusion uses no
  rainfall values. Two label-correlated fields enter inclusion (known time, median wet interval); tested above,
  their effect is downward or neutral. The 100 m fitting-site matching is wrong but has no leakage consequence
  (finding 3). Pass with finding 3's relabel.
- **G2.** `results/tables/coverage.json` exists, fallback 0, counts reconcile (443 attempted; 201 ok; 5 + 7 + 230
  dropped; 3,831 gauge-years, 2,527 ok). Gaps: plan.md section 5 promised counts of quality-excluded values; none
  are given, and the D6 screen's removals (4,520 records at 6 gauges) are not counted. The "outside New Zealand"
  reason is mislabelled (finding 9). Pass with additions.
- **G3.** `results/plausibility.md` traces three gauge-years; all three reproduce from the stored data (61.0 vs
  58.2 (5.9); 159.6 vs 135.0 (12.0); 38.7 vs 82.0 (7.3)); the storm-cluster and control invariants hold. Pass.
- **G4.** No classifier or labeller; the validation metrics are the grid-versus-exact maxima (30 of 30 within 0.4%,
  all 1,729 within 2% by my recomputation) and the raw refetch (10 of 10, plus my 2 gauge-years and one boundary
  window). Pass, with the wording fix in finding 9.
- **G5.** `review/overclaim_check.md` is filled in honestly but every row is Supported; I relabel rows 13, 20, 25,
  27 and 32 as Partially supported (finding 4) and row 1's plain-terms counterpart (row 30) should carry the wider
  interval.
- **G6.** `tools/attribution.py check --show` passes (9 claims). Titles verified for R4 (Wright et al. 2019, US
  design standards), R5 (Serinaldi and Kilsby 2015, stationarity is undead), R6 (Cyclone Gabrielle as a design
  storm, Earth's Future 2024) and R7 (2023 Auckland landslides, Landslides 2024). R1 and R3 checked against the
  HIRDS v4 PDF text: section 2.2 gives CliDB to 2016, NHD to 2015 and Auckland Council to early 2017; Table 6's 6-hour
  row reads 10.8 in the 10-year column. R2's role is background and the claim is generic. Pass.
- **G7.** Does not apply; no unit was labelled by an agent or person. Confirmed.

## Required edits, in one list

1. Add a t-based or bootstrap-t interval beside the preregistered one, state the 9-block caveat, qualify the storm
   bootstrap, and remove any reliance on the 1-h/24-h lower bounds exceeding 1.0 (finding 1).
2. Report the beyond-250-year counts and the sensitivity; name Okoraka 2024 as a probable fault; count D6's
   removals in coverage.json (finding 2).
3. Relabel or redo the fitting/non-fitting split (finding 3) and drop the duplicate Biggs Top gauge (finding 6).
4. Soften the mid-century and cross-duration sentences and the plain-terms range; relabel G5 rows 13, 20, 25, 27, 32
   (finding 4).
5. Complete the Auckland explanation and add the 2017/18-start S3 row (finding 5).
6. Correct S3 1.47 → 1.45, 48 → 47, "0.4%" → "2%", and the skipped-coordinates reason (finding 9); list the three
   extra changes in D5 (finding 7).
