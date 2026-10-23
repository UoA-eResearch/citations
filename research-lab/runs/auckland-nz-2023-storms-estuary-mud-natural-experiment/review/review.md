# Review: auckland-nz-2023-storms-estuary-mud-natural-experiment

Reviewer: Fable 5.1 (independent, adversarial), 2026-10-23. Scope: review/prompt.md. Everything below was checked
against the study's files; supporting scripts and their outputs are in `review/reviewer_checks/` (`check_*.py`,
`check_*.out`). No study file outside `review/` was modified. CPU use was kept to 2 BLAS threads per script.

## Verdict: publish with edits

The computation is sound and the preregistered verdicts (H1 and H2 Inconclusive) stand under every check I ran. The
wild cluster restricted bootstrap is implemented correctly (an independent re-implementation reproduces the p-values
and intervals), the panel is right, the terciles were built from exposure alone, the Sentinel-2 offset rule decided
correctly on real scenes, and the git record supports the stated ordering. No number needs recomputing.

What must change is the text. The report's title, plain-terms section and "what this shows" section repeatedly treat
the exposure as a measure of "land the storms stripped", while the study's own evidence (and mine, below) shows it
ranks sites by proximity to market-garden and forestry clearance, with slip country near the bottom of the scale.
H1 and H2 therefore never tested the storm question, and sentences such as "the extra mud did not follow the stripped
land" and "the storms left no large, lasting, exposure-graded mud signal" are not licensed. Second, H2 is in effect a
two-site test (effective clusters 1.3 of 13); the report's remark that the CR2 interval "would read as Refuted" should
go, because CR2 is not credible there. Third, several descriptive claims overreach ("not unusual", "almost
everywhere", "mostly Coromandel"). The required edits are listed at the end.

## What was verified (no action needed)

- **Git and timing.** plan.md and sites.csv in e8e09f6 (00:57:45; sites.csv mtime 00:57:38; `sites.py` reads no
  value column). D1 fccecb8 00:59, addendum b764397 01:21, D2 f15c72e 01:32, all before exposure.csv (mtime 09:21:46,
  committed d2411cf 09:22:00, unchanged since). D3 files 09:22:53-09:23:06 (4ec2bac), while the first analysis run was
  in progress; the D4 edit to analysis.py is at 09:35:41 and is only the not-estimable clause (`git diff b764397
  fb30a30 -- code/analysis.py`); primary.json final mtime 09:47:08. exposure.csv and sites.csv are byte-identical to
  their frozen commits.
- **Inference** (`check_inference.out`). Webb six-point weights, null imposed via the restricted fit, CR1 t
  statistics, bisection on the imposed null: all as described. An independent implementation with a new seed gives
  H1 p(0) = 0.281 (study 0.2813) and a grid CI of [-2.5, +5.5] (study -2.33 to +5.67); H2 p(0) = 0.368 (0.3647),
  grid CI [-3.0, +3.0] per IQR (study -3.06 to +3.20). The study code is deterministic (re-run reproduces 0.2813 and
  0.3647 exactly). CR2 and CV3 (jackknife) intervals computed independently match the report's CR2 numbers.
  "Dropping the Airport site gives -0.18 (CR2 +/-0.75)" reproduces (-0.179, +/-0.74).
- **Panel** (`check_panel.out`). 712 rows, 56 sites, 2010-2024, no site-year with two rows, no NaN values, no rows
  outside 2010-2024 at these sites. Every 2023 and 2024 row is dated October or November. `design()` is full rank
  (H1: n 473, k 53, rank 53; H2: n 712, k 72, rank 72). `terciles()` reproduces the frozen `tercile` column from
  `E_route_5` alone; counts 18/19/19. D4's not-estimable rule is correct (metals: 0 top-tercile rows in 2023).
- **Sentinel-2 offset rule** (`check_s2_offset.out`). On a pre-window (S2B_60HTE_20221219) and a post-window
  (S2B_60HTE_20230319) scene over west Auckland, the STAC metadata says offset -0.1 (baseline 05.09) but the COG
  DN over dense vegetation is ~440-515 in the red (reflectance 0.044-0.052, physically right) and subtracting the
  offset would give NDVI > 1. The data are already offset-free; `s2.py` decided `offset_already_removed = True` in
  both, correctly. Vegetation NDVI as computed: p10/50/90 = 0.53/0.77/0.86.
- **Sea mask and routing** (`check_exposure.out`). The "<= 0 m" rule added 1,170 km2, almost all harbour water at
  the LiDAR hydro-flattened level (Kaipara 562 km2 and Waitemata/Gulf 289 km2 at -1.14 m). C(2) within C(5) within
  C(10) for every site; no sea or no-data cell inside any C(5); no contributing land touches the domain edge; no
  contour-DEM fill in any C(R). C(5) extends 6-14 km inland (p95 distance 4.6-12.5 km), as the outlet-radius design
  intends.
- **Report numbers.** Every figure I could trace matches the tables: H1 and 2024 estimates and intervals, placebo
  range, event-study values, leave-one-harbour-out ranges, drop-year-only result, exposure-definition estimates, H2
  numbers, regional table (56-site block), tercile breakdown, slips results, macrofauna, metals, scene and block
  counts, median land area, valid share, Spearman correlations, patch shares.

## Findings

### 1. The exposure does not measure storm damage; the report's conclusions are written as if it does — High (wording and framing; no recomputation)

**Evidence.**
- `check_exposure.out` section 5: newly bare share of valid land within 5 km of known 2023 slip clusters is 0.116%
  (Muriwai), 0.112% (Piha/Karekare), 0.070% (Birkenhead), 0.023% (Titirangi), against 3.31% at the Pukekohe market
  gardens, 1.06% in Woodhill forest, 0.55% at Clevedon and 0.29% at Riverhead/Kumeu. The twelve largest patches
  (36-79 ha each) are all at Pukekohe/Bombay, Karaka, Glenbrook and the South Head/Woodhill forests.
- The tercile cut points are 0.100% and 0.147% (exposure_summary.json). The top tercile is the Whitford embayment
  (Mangemangeroa, Turanga, Waikopua: nine sites whose C(5) sets share 78% of their cells), Orewa, Okura, two Manukau
  sites beside the Karaka/Pukekohe belt and two Kaipara sites (`check_misc.out` (d)). None of the west-coast or
  isthmus slip country has a monitoring site. The gradient the terciles encode is proximity to cropping and
  forestry, and the report's own F1 shows the top-tercile sites sitting in near-white (little newly bare) country.
- Order of magnitude: the newly bare layer is 3,412 ha. Even if every rainfall-triggered slip in the region were
  detected at 10 m, the storm's slip area (thousands of slips, most a few hundred square metres) would be a few per
  cent of that total. The D3 slip-sized exposure (14% of area) is a better proxy but is still mostly not slips, and
  its terciles agree with the primary in only 9 of 19 top and 12 of 18 bottom sites.
- The planned validation (plan section 2.6) against the council's pilot was not possible, so the exposure was never
  checked against any slip inventory.

**Why it matters.** The report says the right things in places ("The exposure measure is the weakest link",
"harvest dominates"), but the headline and the conclusions do not follow through: the title's second clause ("not
more so where the storms stripped more land"), "the extra mud did not follow the stripped land", "No large,
exposure-graded mud signal", "There is no dose-response under any exposure definition", and "It does show that the
storms left no large, lasting, exposure-graded mud signal at the monitoring sites". None of these is a finding about
storm exposure. What the study shows is that mud change in 2023 was not graded by a satellite bare-land measure that
tracks harvest.

**Fix.** Retitle (for example: "Auckland's estuaries were muddier at most sites in the spring after the 2023 storms;
a satellite bare-land exposure, which turned out to map harvest rather than slips, found no gradient"). In "What this
does and does not show", lead with: the preregistered exposure failed descriptive validation as a storm-damage
measure, so H1 and H2 are tests of a harvest-clearance gradient and the storm question remains untested. Rewrite the
three plain-terms sentences quoted above accordingly. Add to "Not shown": that the storms' slips did or did not
grade estuary mud. State in Limits that no slip inventory validated the exposure, and name the open 2023 North Island
landslide inventories (GNS Science) as the route to a real exposure if the lead is revisited.

### 2. H2 is a two-site test; neither interval is reliable; drop the "would read as Refuted" sentence — High (wording)

**Evidence** (`check_inference.out` sections C-E).
- After partialling out site and year effects, 86.7% of the identifying variation in E x 2023 sits in the Manukau
  cluster: Auckland Airport 59%, Clarks Beach 28%. The Carter-Schnepel-Steigerwald effective number of clusters is
  G* = 1.3 of 13 (H1: 7.6 of 11). Range/IQR of the exposure is 21.
- The code is right; the tenfold gap between the wild (-3.06, +3.20) and CR2 (-0.57, +0.15) intervals is real and
  is exactly what G* near 1 produces: the restricted wild bootstrap is very conservative when one cluster carries the
  treatment variation, while CR2 (and CV3, +/-0.5) are anti-conservative. Dropping both Manukau sites widens CR2 to
  +/-2.75 and the wild interval to [-4.75, +4.25], confirming that the apparent precision of CR2 came from two sites.
- Verdict dependence: H1 is Inconclusive under wild, CR2 and CV3 alike. H2 would be "Refuted" under CR2 only, and CR2
  is not a credible interval here.
- Exploratory (reviewer-side): rank and log transforms of exposure also give nothing (+0.52 and +0.03 pp per IQR,
  wild p 0.80 and 0.98), so the null is not an artefact of the two outliers either.

**Fix.** In the H2 results, replace "Why the two intervals differ" with the G* figure and the statement that the H2
interval is uninformative rather than Inconclusive-but-estimated; delete or qualify "It would read as Refuted" in the
summary bullets (CR2 with G* = 1.3 cannot support Refuted); change "There is no dose-response under any exposure
definition" to "no dose-response is detectable, and the dose-response test had almost no identifying variation".

### 3. "The 2023 difference is not unusual" / "within the normal year-to-year wobble" contradicts the study's own numbers — Moderate (wording)

**Evidence** (`check_panel.out` section 9). The 2023 top-minus-bottom value (+1.96) is the largest in the 15-year
event-study series and 2.9 SD of the 2010-2021 values (mean -0.10, SD 0.71); all seven placebos are smaller. What is
true is that 2022, before the storms, was nearly as large: +1.45 in the event study and +1.61 by the same
fixed-effects placebo estimator on pre-2023 data (the preregistered placebo window 2015-2021 excludes 2012 and 2022,
the two years with the largest swings). There is no linear differential pre-trend (0.02 pp per year). So the 2023
gap exceeds the pre-storm gap by about 0.3-0.5 pp, and the cluster-bootstrap p against zero is 0.28.

**Fix.** Replace "not unusual" and "within the normal year-to-year wobble" with the accurate statement: largest in
the series, but only ~0.3-0.5 pp above the pre-storm 2022 gap, and not distinguishable from zero with 11 harbour
clusters. Report the 2022 fixed-effects placebo (+1.61) next to the 2015-2021 placebos.

### 4. The post-hoc pulse: "almost everywhere" overstates it, the Waikato line is wrong, and the regional JSON carries two Auckland 2024 numbers — Moderate

**Evidence** (`check_panel.out` sections 5-8, `check_month.out`, `check_misc.out`).
- The composition checks the prompt asked for all pass, and the report should say so because they strengthen its
  reading: sites sampled in 2021-22 (n = 45) rose +4.58 in 2023 against +2.98 for the 11 sites returning after a
  3-4 year gap; the 2024 fade holds within the same 42 sites (+4.67 in 2023, +1.10 in 2024); with a
  leave-that-year-out baseline 2023 is still the largest year (+4.26; next 2011 at +1.84); the value format changed in
  2020, not 2023 (six-decimal values from 2020 on), so there is no sign of a 2023 reporting change; the 15 November
  samples in 2023 are the Waitemata Central and Upper sites that are always sampled in November. The sampling date
  codes in 2023 are only "2023-10-01" and "2023-11-01" (month precision).
- But the pulse is concentrated, not region-wide: by harbour, Waiwera +15.6, Waitemata Upper +10.9, Kaipara South
  +9.4, Mangemangeroa +8.5, Waikopua +5.7, Okura +4.3, against Puhoi -1.2, Orewa -1.0, Mahurangi +0.7, Whangateau
  +1.4, Manukau +1.5, Turanga +1.7, Waitemata Central +2.6 (16 sites). The site median is +2.6 against the mean
  +4.26. A harbour-cluster bootstrap gives 2.3 to 7.0 (the report's site bootstrap, 2.26-6.30, treats sites within a
  harbour as independent).
- "Waikato, mostly Coromandel and storm-hit ... +5.4 (6 sites)": the six Waikato sites with five pre-years are Firth
  of Thames (2), Whaingaroa/Raglan (2, west coast) and Tairua (2); none is in Coromandel Harbour, and the +5.4 is one
  site (Kuranui Bay +24.6; the median of the six is about +1.6).
- regional_2023.json gives Auckland dev_2024 = 1.10 (the 56 sites) in the `auckland` block and 2.26 in the
  `regions` block (51 sites, including 9 Manukau and other sites with no 2023 survey, which average +7.6). The
  report quotes 1.10 without saying the two blocks use different site sets.

**Fix.** Title and plain terms: "almost everywhere" and "almost across the board" to "at most sites, strongly in
about half the harbours"; add the harbour breakdown and the harbour-cluster interval; cite the composition and
format checks as evidence against a sampling or reporting artefact (they are the best support the pulse has);
correct the Waikato sentence; note the two Auckland site sets in the regional table or drop the `regions.Auckland`
row.

### 5. The plain-terms section contradicts the "not ruled out" statement — Moderate (wording)

"An effect of the preregistered size (4 pp) is not ruled out. The H1 upper bound is +5.7 pp" is correct (the wild
p-curve gives p = 0.21 at beta = 4). But the plain-terms section ends "It does show that the storms left no large,
lasting, exposure-graded mud signal", where "large" is undefined and, read as 4 pp, false. Together with Finding 1,
replace with: "An exposure-graded effect of the size we set out to find (4 points) cannot be ruled out; one above
about 6 points can, but only for an exposure that mostly measured harvest."

### 6. "Dropping year-only rows" is in fact "dropping the 11 biennially sampled Waitemata Central sites" — Low

`check_month.out`: all 55 rows dated 1 January belong to 11 Waitemata Central sites sampled every second year
(2010-2020); their only other row is 2023. Dropping the year-only rows leaves them a single row each, which the site
effect absorbs, so the sensitivity (+1.45, -3.21 to +5.81) removes those sites, seven of which are in the bottom
tercile. Their pre-period season is unknown, so their baselines may not be spring baselines. Say this in the report
(it also explains why the estimate falls: without them the bottom tercile's 2023 rise is +1.95 instead of +1.39).

### 7. Effective sample is far smaller than "19 sites per tercile" — Low (design statement, power)

`check_exposure.out` section 4: within-harbour Jaccard overlap of C(5) is 1.00 (Mangemangeroa, Waiwera), 0.98
(Waikopua), 0.96 (Puhoi), 0.94 (Orewa), 0.92 (Okura); the exposures of co-located sites are identical to three
decimals. The top tercile holds about seven distinct exposure values; H1's effective cluster count is 7.6 of 11. The
plan's power statement (about 50% at 4 pp) assumed 19 independent sites per tercile and therefore overstates power.
State the effective units and say power was below 50%.

### 8. F3's title asserts the conclusion — Low

"No dose-response: 2023 mud change against storm exposure" (figures.py line 118) asserts what a +/-3 pp per IQR
interval cannot support, and "storm exposure" is the Finding 1 problem again. Retitle "2023 mud change against the
bare-land exposure". The F3 caption's +3.19 against the report's +3.20 is rounding of 3.195; harmless.

### 9. Macrofauna wording — Low

The LAWA workbook's Site list sheet labels the indicator "Macrofauna - benthic health score". The report's "by its
range an AMBI-type disturbance score" (values 0.34-5.97) is a reasonable inference; quote the file's label alongside
it so the inference is visible as one.

### 10. Sea mask: rivers and two lakes are "sea", harmlessly — Low (documentation)

`check_exposure.out` section 1: the Sentinel-2 water rule, applied to anything connected to the open sea, classes the
lower Waikato River and, through it, Lakes Waikare (33 km2) and Whangape (8 km2) as sea, contrary to D1's "lakes and
inland ponds are not sea"; the "<= 0 m" rule also takes in the drained Aka Aka/Waiuku lowlands (27 km2 at -0.6 m).
All are more than 20 km from any site and touch no C(10). Record the caveat in D1 or seamask_log; no effect on
results. (For the record: 49 of 56 site cells are themselves "sea", as expected for intertidal sites at -1.3 to
+1.2 m; outlets, not site cells, define C(R).)

## Required edits before publication

1. Title, plain terms and "What this does and does not show" rewritten per Findings 1 and 5: the exposure maps
   harvest, so H1/H2 did not test storm exposure; drop "did not follow the stripped land" and "left no large,
   lasting, exposure-graded mud signal".
2. H2: add G* = 1.3 of 13 and the two-site share of identifying variation; delete or qualify "would read as
   Refuted"; soften "no dose-response under any exposure definition" (Finding 2).
3. Replace "not unusual" / "within the normal year-to-year wobble"; report the 2022 FE placebo +1.61 (Finding 3).
4. Pulse: "almost everywhere" to "at most sites, strongly in about half the harbours"; add harbour breakdown,
   harbour-cluster interval (2.3-7.0) and the composition and format checks; fix the Waikato sentence; note the two
   Auckland site sets in the regional table (Finding 4).
5. Say what the drop-year-only sensitivity removes (Finding 6); state effective exposure units and lower power
   (Finding 7); retitle F3 (Finding 8).

Optional: cite `review/reviewer_checks/` outputs for the added numbers rather than re-running anything.

## Files

- `review/reviewer_checks/check_panel.py` / `.out`: panel, rank, terciles, composition, pulse, precision, event study.
- `review/reviewer_checks/check_inference.py` / `.out`: independent wild bootstrap, CR2/CV3, leverage, G*, drops,
  rank/log exposure.
- `review/reviewer_checks/check_exposure.py` / `.out`: sea mask components, C(R) nesting and extent, within-harbour
  overlap, patch sizes and locations, hotspot densities.
- `review/reviewer_checks/check_s2_offset.py` / `.out`: offset rule against live Earth Search scenes.
- `review/reviewer_checks/check_misc.py` / `.out`: Waikato site set, regional JSON inconsistency, 2024 composition,
  tercile-by-harbour.
- `review/reviewer_checks/check_month.py` / `.out`: 2023 rises by sampling month; year-only-date sites.
