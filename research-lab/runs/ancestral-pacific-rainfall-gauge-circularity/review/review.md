# Review: ancestral-pacific-rainfall-gauge-circularity (draft at commit 0a73d80)

Reviewer: independent adversarial review, 2026-10-21. Scripts and captured outputs are under `review/reviewer_checks/`
(scripts `01`–`15`, outputs in `reviewer_checks/cache/NN_output.txt` and the CSVs there). Environment: the run's
`venv/bin/python`, nothing installed, one paced network stream for a single six-cell spot-check and one directory
listing.

## Verdict: fix first

The two preregistered verdicts reproduce and are robust: an independent re-implementation of the pipeline (gauge QC,
pentads, labels, shift rule, skill, bootstrap) gives H1 ratio 0.104 (−0.153, 0.349) against the study's 0.103
(−0.154, 0.349) and ΔKGE at independent gauges +0.034 (+0.008, +0.059) against +0.034 (+0.007, +0.059); the H1 upper
bound stays in 0.335–0.375 over 20 other bootstrap seeds, and the within-station contrast (49 stations with both
strata) shows the same gap, so the 10× difference is not a station-selection, regime or period artefact.

But the report cannot go out as written, because a third of the "independent" evidence and the released benchmark
rest on grid cells where CHIRPS and CHIRP carry no rainfall estimate at all (Palau, Johnston, Canton, Chuuk,
Lukunoch, Woleai: product means of 0.001–1 mm per pentad against gauge means of 9–57 mm), which the report presents
as evidence about blending and labels as usable in `benchmark_stations.csv`; the descriptive shares that frame the
story ("22–28% of gauge-months independent", "CHIRPS ingests about a third of Pacific gauges") are computed on
non-reporting station-months and with a 5 km rule that the input lists' coordinate rounding defeats; two
preregistered outputs are missing; the label-resolution caveat is applied to H1 but not to H2, where it cuts the
other way; and one gauge record in the release is 10× too large for 24 years. None of these flips a verdict (the
corrected primary numbers are R = 0.115 (−0.19, 0.39), ΔKGE = +0.046 (+0.016, +0.073)), but the numbers, the
country table, two figures, the benchmark release and the plain-terms summary all change.

## What checked out

- **Timeline (git).** Plan 8502f43 (07:00 Oct 18) → gauge/label/analysis code e80260a (08:24) → D1 e0b29b9 (15:07)
  → secondary code c002349 (15:14) → D1 addendum 7f96f84 (15:42) → figures code 036be82 (16:33) → dtype fix 054bc37
  (05:41 Oct 19, analysis.py only) → results and report 0a73d80 (05:52). D1 precedes any skill computation; both
  post-hoc fixes are as described (the masked-station fix changes a count only, since the station it catches was
  already skipped by `j.chirps.isna().all()`, analysis.py:171).
- **Gauge QC.** Re-parsed three `.dly` files independently (flag column, −9999, run filter): series identical to
  `gauge_daily.csv.gz` (check 09 A). 14 stations lose 170 days to the identical-run filter. Trace days are kept as 0.
- **Pentads and timing.** Own implementation of the CHIRPS six-per-month calendar matches the study's pentads to
  0.000 mm; the day-shift rule (Spearman against CHIRP only, applied to both) reproduces 67/53/2 (check 09 B, D).
- **Labels.** Header is `latitude,longitude,...`, so the column order in labels.py:26 is right. Own haversine without
  the Pacific prefilter, 10 stations × 540 months: max difference 1 m, zero stratum disagreements (check 09 C). All
  540 lists are present and non-empty; 148 × 540 label rows.
- **Extraction.** 3,240 pentads × 148 stations for both products, no duplicate (pentad, station) rows across the part
  files, every error pentad (69 CHIRP, 276 CHIRPS, all HTTP 403 or read failures) later read `ok`, no negative values
  (check 03). Pixel indexing: `rasterio.index()` agrees with a hand floor formula on the (−180, 50) 0.05° origin for
  all 148 stations (check 01), and a six-cell window read from the server at pentad 2010.03.2 (direct-reader era for
  CHIRP) matches the extract exactly (check 13). The CHIRPS COG uses a wider land mask than the 2015-vintage grid of
  the plan's pre-check; the 13 stations it unmasks carry realistic values (e.g. Kapingamarangi CHIRP 34.5 mm/pentad
  against a 45.8 mm gauge), so "147 of 148" is right but needs the explanation.
- **Skill, bootstrap, verdict rules.** RMSE, KGE (r, β, γ as in Gupta 2009), the 30-pentad stratum rule, the
  100-pentad inclusion, station means, station-block bootstrap (2,000, seed 20261018) and the H1/H2 decision rules
  all match plan §1 and reproduce (804 station-strata rows matched; summary numbers above). The β/γ/r decomposition
  claimed for the KGE gain (0.026, 0.031, 0.015) is correct (check 04).
- **Secondary pair.** Reproduced: ratio 0.720 (0.492, 1.001), ΔKGE +0.108 (+0.056, +0.161), 102/28 stations
  (check 09 G). 7,305 days complete for both products; GPCC labels 148 × 240.
- **Report numbers.** Every number in report.md traces to `primary.json`, `station_skill.csv` or
  `benchmark_stations.csv` (221,730 pentads, 37,938 independent, country counts, shifts, CIs). report.html carries
  the same numbers (check 08). Figures match the tables.

## Findings

### 1. (Major) A third of the "independent" pentads come from cells where neither product has an estimate

Evidence (checks 11, 13, 12; `cache/station_product_means.csv`):

- 12 stations have a CHIRP series averaging under 2 mm/pentad or under 20% of the gauge: all six Palau stations
  (CHIRP 0.065 mm/pentad against a 52 mm gauge at Koror, β = 0.001), Johnston Island (0.001 vs 9.3), Canton Island
  (0.011), Lukunoch (0.59 vs 49), Chuuk WSO AP (0.95 vs 49), Woleai (2.5 vs 42) and Koumac (see finding 5). The
  server confirms it: CHIRPS pentad 2010.03.2 is 0.002 mm at Koror and 0–1.4 mm across every Palau land cell, with
  ocean nodata around them; the plan's own 2015 pre-check grid gives 0.02 at Koror. These are product defects (no
  climatology), not extraction errors.
- They supply 10 of the 65 independent station-strata (five Palau, Johnston, Lukunoch, Chuuk, Woleai, Koumac) and
  12,136 of 37,221 independent pentads (33%), plus 4 of 100 supported station-strata.
- At such a cell the gain is 0 by construction (both RMSEs equal the RMS of the gauge: Palau gains 0.0000–0.0001)
  and ΔKGE is whatever the γ term does to two near-zero series (Palau −0.04 to −0.10). Neither says anything about
  blending.
- The plan's masked category ("CHIRPS has no estimate there at all", §3) was implemented as "every CHIRPS value
  empty" (analysis.py:147); the COG fills these cells with near-zero values instead of nodata, so the test misses
  them.
- The report then builds on them: "Independent pentads are concentrated in a few places ... Fiji (20,275) and Palau
  (8,306)"; `benchmark_stations.csv` releases Palau with 8,306 usable independent pentads and Chuuk with 3,029
  supported ones; F1 and F2 plot them.

Effect of dropping the 12 stations from both strata (check 12, same seed and bootstrap): primary gain supported
0.105 (0.069, 0.137), independent 0.012 (−0.018, 0.037), R = 0.115 (−0.188, 0.393), H1 Supported; ΔKGE +0.046
(+0.016, +0.073), H2 Refuted. Sensitivity variants likewise keep their verdicts. Within-station (45 stations):
supported 0.126, independent 0.017, paired difference +0.110 (+0.069, +0.156).

Fix: add a no-estimate test (product mean below, say, 10% of the gauge mean or below 2 mm/pentad, or an explicit
CHPclim check) to the masked category; rerun analysis and figures; report these stations as "CHIRPS has no estimate"
(it is a finding in its own right that CHIRPS cannot be evaluated at Palau, Johnston, Canton or the Chuuk-lagoon
atolls); correct the country table and the Palau sentence; flag them in the benchmark release.

### 2. (Major) The descriptive shares use non-reporting station-months and a 5 km rule that list rounding defeats

Evidence (analysis.py:197–198, figures.py:77–80; check 09 F; check 02; check 10):

- F3 and `ingested_share_by_decade` average over all 148 × 540 station-months, including months in which the gauge
  reported nothing (a station closed in 1998 contributes "not ingested" rows through 2025). On reporting
  station-months the independent share is 18–22% by decade (17.1% of usable pentads), not "22–28%"; the supported
  share is 65–75%.
- "Ingested" is nearest input ≤ 5 km, but 6.7% of the Pacific rows in the lists are rounded to 0.1° (up to ~7.8 km
  off). Nadi's nearest list entry, "NANDI AERO", is 7.37 km away every month; Nausori's is 7.33 km. Both are the
  ingested stations and both count as not ingested. On reporting station-months the ≤ 5 km share is 37–46%, the
  ≤ 10 km share 58–70%; the share of reporting gauges ingested in at least half their months is 39–51% (5 km) or
  59–70% (10 km).
- Report lines affected: "about 62–68% of gauge-months are supported ... only 22–28% are independent"; "In any
  decade, CHIRPS ingests 32–41% of the Pacific gauges themselves"; the F3 y-axis "share of gauge-months"; and in
  plain terms "In any decade, CHIRPS uses about a third of Pacific gauges". The fair statement is roughly half to
  two-thirds, which strengthens the circularity point rather than weakening it.

Fix: compute shares on reporting station-months (or usable pentads), use ≤ 10 km or name matching for "ingested",
relabel F3, and rewrite the three sentences.

### 3. (Moderate) Preregistered outputs are missing from the report

- Plan §5.1: "The co-located case (within 5 km) is reported separately." It was computed (variant `colocated_5km`:
  67 stations, gain 0.097, ΔKGE 0.118) and not reported.
- Plan §4: "which countries cannot be evaluated with open data at all" and "per country, usable station-pentads and
  how many are independent". `by_country` is in primary.json but the report names three countries. 26 of 148
  stations fail inclusion, among them every station of Niue and Tokelau; Nauru, Samoa, Wallis & Futuna and Pitcairn
  have no GHCN-Daily station at all. After finding 1, Palau joins the list of countries that cannot be evaluated.
- Plan §4: the masked-stations-excluded sensitivity is not reported (trivial, one station, but say so).
- The report says "122 GHCN-Daily stations" throughout; 121 contribute CHIRPS skill (FMC00914251 is masked).

Fix: one table (country, stations, usable pentads, independent pentads, no-estimate stations, verdict on
evaluability) and one line on the co-located case.

### 4. (Moderate) The label-resolution caveat is applied to H1 only; it bears on H2 and the "Refuted" wording

Evidence: the CHC diagnostics directory holds only `monthly/` lists (check 07), so CHIRPS's pentad-stage GTS inputs
are invisible to the label. The report says this "would bias the independent gain upwards, against H1" (correct) but
does not say that the same hidden inputs make CHIRPS look better at "independent" gauges, i.e. push H2 towards
Refuted. The independent stratum is dominated by WMO/GTS-type gauges (GHCN ids with W/M: 28 of 55 stations and 87%
of independent pentads once no-estimate cells are removed), whose ΔKGE is +0.060 against +0.031 at COOP/national
gauges (difference +0.03, 95% −0.03 to +0.08; check 15). Not significant, but it is exactly the signature a
pentad-stage leak would leave, and H2's lower bound (+0.016 corrected) is small.

Fix: state the H2 direction of the caveat; report the WMO/COOP split; word H2 as "not supported: CHIRPS is
marginally better on KGE at labelled-independent gauges, a margin that undetected pentad-stage inputs could produce".

### 5. (Moderate) The gauge QC misses a unit error: Koumac 1980–2003 is 10× too large

Evidence (check 14): NC000091577 has 73 daily values ≥ 500 mm (max 1,732 mm), annual totals of 7,000–16,000 mm in
1980–2003 against CHIRP's 880 mm/yr and a plausible 500–1,500 mm/yr from 2004 on. Dividing by ten gives a normal
Koumac. The blank-flag and identical-run checks cannot catch this. It contributes 2,209 supported pentads with
β = 0.14 and is released unflagged. One station in 100 does not move the means, but the release is the stated
purpose of the study.

Fix: add a plausibility screen (daily maximum, annual total against product or climatology), flag or exclude, and
note it in the benchmark.

### 6. (Minor) "Tenfold" overstates what the interval supports

The ratio is 0.10 with a 95% interval of −0.15 to 0.35. "Overstates its advantage ... about tenfold" (report, plain
terms, abstract) is a point estimate whose interval runs from "at least threefold" to "no gain at all". Say "by a
factor of at least three (point estimate ten)".

### 7. (Minor) Heterogeneity worth one paragraph; the within-station result answers the selection objection

- The supported gain is a mix: FM +0.17, FP +0.13, RM +0.15, but Guam −0.09 and CNMI −0.17 (19 ingested stations at
  which CHIRPS is worse than CHIRP, one at −0.9). Without Guam and CNMI the supported gain is 0.151. The report does
  not mention this.
- Stations only in the independent stratum (16) have mean gain −0.006; stations only in the supported stratum (51)
  have 0.086. The contrast survives within station: 49 stations with both strata give supported 0.117, independent
  0.016, paired difference +0.101 (+0.063, +0.142), 88% with the supported gain larger; mean year of the two strata
  2004.6 vs 2005.2 (so not a period effect); median gauge rainfall 37 vs 35 mm/pentad in the two strata (so not a
  regime effect, though gain rises with wetness in both, Spearman 0.23 and 0.37). Check 09 E.
- CHIRPS is not inert at independent cells: it differs from CHIRP by 38% relative RMS there (46% at supported cells;
  check 05), with a median 323 km to the nearest listed input. The blend moves pentads substantially without
  reducing RMSE, which is the fairer description of "neutral".

Fix: report the within-station contrast (it is the answer to "different stations"), the Guam/CNMI anomaly, and the
38% figure.

### 8. (Minor) Partial pentads at record edges

`gauge_pentads()` (analysis.py:32–33) tests completeness against the days present in the record, not the calendar
length, so a record that starts or ends mid-pentad yields one "complete" partial pentad (e.g. FJM00091680 2025.08.5).
3 of 24,993 pentads across five stations checked (check 09 B); negligible. Fix with a calendar-length test.

### 9. (Minor) Wording and presentation

- "The plan's pre-check grid masked 14 stations as ocean. The CHIRPS pentad files used here have values at 147 of the
  148": explain that the COGs use a wider land mask than the 2015-vintage grid, and that the same mask carries
  near-zero cells (finding 1).
- `ingested_share_by_decade` and F3 are "station-months", not "gauges" or "gauge-months"; label them so.
- The D1 reader check (0 of 1,776 mismatches) has no log in `logs/`; keep its output next time. My six-cell
  spot-check is consistent with it.
- The secondary pair's "independent" cells are still adjusted (PERSIANN-CDR follows GPCP, which is satellite-based
  over gauge-free cells), which is why its "independent" gain is 7.7%; the report calls the pair suggestive only,
  which is right, but one sentence on why would help.

## What I did not do

- I did not re-run `check_chirp_reader.py` (network); the direct reader is instead covered by the paced six-cell
  spot-check at a direct-reader-era pentad.
- I did not test the assumption that the served CHIRP pentads are the exact pre-blend input of the served CHIRPS
  v2.0 COGs (plan §1: "the two differ only by the station blending"); nothing here contradicts it, but it is an
  assumption, and the 38% RMS difference at cells 300 km from any listed input should be stated as a property of the
  pair rather than explained away.
