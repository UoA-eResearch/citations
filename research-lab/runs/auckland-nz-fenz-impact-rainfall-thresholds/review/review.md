# Independent review: `auckland-nz-fenz-impact-rainfall-thresholds`

Reviewer: Fable 5.1, 2026-11-03. Scripts and outputs: `review/reviewer_checks/` (`check_data.py` → `data.json`;
`check_dups.py` → `dups.json`; `check_models.py` → `models.json`, `models_days.csv`; `check_dedup.py` → `dedup.json`;
`check_trace.py` → `trace.json`). All numbers below are aggregate counts or model outputs; no FENZ or council record
text is reproduced.

## Verdict: **fix first**

The preregistered rule is applied correctly and its three conditions hold on the data as built, and the report is
candid that the margin rests on one storm. Two things stop it being published as it stands:

1. **The panel is not one unit per place.** 53 gazetteer points carry two panel units each (the same place coded
   under two FENZ councils), so 11% of suburb-days are counted twice with identical rain, and 11 of the 64 held-out
   flood suburb-days have a twin row that is a certain non-event with the same rain. D2 says this was fixed; the
   lab's own tables show it was not (finding 1). The fix is mechanical and the result is likely to survive it (see
   `dedup.json`, finding 1), but the published unit counts, coverage and every statistic come from the wrong panel.
2. **The result does not distinguish "rarity" from "depth plus a place's climatology".** Giving the depth model the
   gauge's HIRDS index log M as a plain additive covariate reproduces the rarity model's gain to the fourth decimal
   (S 1.074 vs 1.073; held-out difference between the two −0.6×10⁻⁷, 95% interval −1.0 to +1.1×10⁻⁵). H1 as
   preregistered is met, but the title and the "what this shows" section claim more than that (finding 2).

After a rebuild with one unit per place, one re-run of `analyse.py`, and the D+M comparison reported as a
reviewer-prompted post hoc, this is publishable with the wording changes in findings 2, 7 and 9.

## What was verified and holds

- **Git.** `plan.md` committed 16:41:14 (454cb34); the first build outputs and `analyse.py` committed 16:52:28
  (0ec50f3); `analyse.py` and `panel.py` are byte-identical to that commit at HEAD. The stopped first run: `logs/analyse.log`
  last written 17:10:16, `v0_unseen_flawed_geocoding/primary.json` mtime 17:04, its directory 17:11, sha256
  edd777ce0bc1a276… identical for the working file and the blob in 2afc389. D2's account is accurate. The only code
  change since 0ec50f3 is `rain_daily.py`'s call signature for the HIRDS D7 screen (D3).
- **Time base.** FENZ times are civil time: across eight files, zero timestamps fall in the nonexistent spring-forward
  hour and 103 fall in the repeated autumn hour (those 103 are the "unparsed or DST gap" drops in `fenz_rows.json`).
  The 2024/25 file parses day-first: all 92,017 rows parse, all fall in FY2024/25, and 55,528 have a day field above 12.
  The gauge series are NZST (Auckland explicitly, `fetch_auckland.py`; Hilltop by default), so the conversion is right.
- **Rain assignment.** Nearest usable gauge within 10 km, 30-hour known fraction ≥ 0.9, resolution ≤ 15 min, 2xx kept:
  as planned. The water-year maximum of the daily 6-h series equals the HIRDS lead's S3 annual maximum exactly in all
  3,543 gauge-years I compared (the lab says 3,509; its check is not in the repo, see G3). The G4 window audit's 30 of
  30 exact matches hold.
- **Geocoding accuracy for known places.** 28 well-known towns and suburbs in the panel all lie within 1.4 km of my
  reference coordinates (`data.json: spot_check`).
- **Models and inference.** The spline, deviation coding (unseen region = 0 = average), standardisation from training
  rows, the S inequality, the storm-day bootstrap and the verdict function all do what the plan says. My refit
  reproduces `primary.json` (LL_D 0.0011547, LL_R 0.0011172, D_LL 3.75×10⁻⁵). The bootstrap interval is stable across
  seeds (lower bound 0.9–1.0×10⁻⁵; 0.0–0.2% of resamples ≤ 0).
- **Report numbers.** Every number in the title, standfirst, verdict block, results tables and plain-terms section
  matches `primary.json`, `secondary.json`, `posthoc.json`, `onset.csv`, `coverage.json` and `fenz_rows.json`, with the
  exceptions in findings 7 and 9.
- **G6.** `attribution.py check` passes; the four DOIs resolve to the papers the claims name (Hurford et al. on
  extreme-rainfall alerts vs surface-water flooding in England and Wales; Spekkers et al. on insurance claims in the
  Netherlands; Stone et al. on Cyclone Gabrielle as a design storm for northeastern NZ; Brook and Nicoll on the
  January–February 2023 Auckland storms), with roles and conditions correctly recorded.

## Findings

### 1. The panel double-counts 53 places (major; fix before publishing)

**Evidence.** `dups.json`: 954 panel units sit on 900 distinct gazetteer points; 107 units share a point with another
unit (53 points, two units each). Those twins account for 292,890 of 2,653,907 suburb-days (11.0%): 144,984 point-days
appear twice, with identical rain (`dedup.json: identical_rain`). 83 flood suburb-days are on twinned points (72
training, 11 of the 64 held-out), and in all 83 the twin unit records no callout, so the model sees the same rain
labelled both 1 and 0. The pairs are mostly council-boundary places coded under two councils (Auckland | Waikato 17,
Manawatu-Wanganui | Wellington 7, Auckland | Northland 5, Nelson | Tasman 4) plus five pairs under the same council
(spelling variants the normaliser does not merge). The lab's own tables show it: `fenz_rows.json` counts 3,629
(suburb, TLA) pairs while `geocode.json` keys 3,700 units, and 69 (suburb, TLA) pairs occur under two or more
councils. `build_fenz.py:70-79` keys a place by normalised name plus council; the council fill rule only applies to
blank councils, so a place with two non-blank councils stays split. D2's "one unit per place" and `plausibility.md`'s
"joins neither duplicate nor drop units" are therefore not true.

**Effect on the result.** `dedup.json`: merging each twin pair into the unit with more training exposures (callouts
summed per place-day, activity recomputed) gives 900 units, 2,506,001 suburb-days (316,853 held out), the same 765
training and 64 held-out floods, and the primary comparison survives: D_LL 3.9×10⁻⁵ (0.45 to 8.4×10⁻⁵), S 1.071, both
conditions met (LORO not rerun: 18 fits). So the fix should not change the verdict, but every count and statistic in
the report comes from the wrong panel, and the preregistered rule has to be applied to the right one.

**Fix.** Key a place by its gazetteer point (or by normalised name + TLA with the modal council), sum callouts per
place-day, recompute activity, rerun `panel.py`, `analyse.py`, `posthoc.py`, `g4_check.py`, `figures.py`; correct the
unit counts throughout (954 → about 900 places); record it as D4.

### 2. "Rarity" is not shown to beat "depth plus the place's climatology" (major; wording and a post hoc to add)

**Evidence.** `models.json`. Rarity divides depth by a per-gauge constant M. Add log M as a plain additive covariate to
the depth model (D+M, one extra column) and the held-out log-loss is 0.00111665, against the rarity model's 0.00111721:
D+M is a hair better. Skill over the no-rain baseline: D+M 5.526×10⁻⁴, R 5.520×10⁻⁴; S(D+M over D) = 1.074 against
the reported S(R over D) = 1.073. The held-out difference R − (D+M) is −0.6×10⁻⁷ with storm-day bootstrap interval
−1.0×10⁻⁵ to +1.1×10⁻⁵ (54% of resamples ≤ 0). Adding log M to the rarity model changes nothing (R+M − R = 1.7×10⁻⁷).
This is expected from the design: the boundary knot sits at the 99.9% training quantile (74.5 mm; rarity 1.35) and the
spline is linear beyond it, where 252 of 765 training flood days (depth) and 301 of 765 (rarity) lie, so in the storm
range the rarity model *is* the depth model plus β·log M per gauge. Region effects and suburb activity do not absorb
this: M ranges 27–137 mm within the panel.

**What it means.** The preregistered H1 (r = d/M beats d) is met. The evidence does not show that the index-flood
ratio is the operative scale, only that a gauge's typical annual maximum carries information about callout propensity
that the depth model lacks. The title ("track how rare the rain is for a place") and "What this does and does not
show" read as the former.

**Fix.** Report D+M as a reviewer-prompted post hoc in the results table and in "What this does and does not show":
rarity and depth-plus-log-M are indistinguishable on these data; the gain is from the place's climatology, and the
ratio is one way to encode it. Re-label overclaim row 1 Partially supported until the title says so (for example
"... slightly better than its depth alone").

### 3. Flood days are lost to gauge availability three times as often as ordinary days (medium; a limit to state)

**Evidence.** `data.json: flood_suburb_days_in_panel_suburbs`. Among panel suburbs, 1,006 suburb-days have a flood
callout in FY2017/18–2024/25; 177 (17.6%) are dropped because no gauge within 10 km was usable that day, against 5.7%
of all suburb-days (159,979 of 2,813,886). The losses concentrate in the wet years (72 in 2021/22, 49 in 2022/23) and
on the biggest day: on 27 January 2023, 20 of 76 Auckland flood suburb-days (26%) are lost. Storms knock gauges out
and trip the physical screens, so the panel under-represents the most extreme days. It affects both models alike and
does not bias the comparison, but the report's coverage statement ("no usable gauge that day: 159,979") hides that the
missingness is informative.

**Fix.** State the 17.6% vs 5.7% in Limits, and the 27 January figure beside the storm-day table.

### 4. The optimiser stops at scipy's default tolerance (medium; latent, conclusions robust)

**Evidence.** `models.json: fits`. `analyse.fit` uses L-BFGS-B with default `gtol` 1e-5 on a mean log-loss of order
10⁻³, so the base model "converges" after 8 iterations and D and R after 26, with maximum gradient 7×10⁻⁶. Continuing
to `ftol` 1e-15 / `gtol` 1e-10 lowers the training loss by 0.8–2.6×10⁻⁶ and raises every model's held-out loss (base
1.6692 → 1.6757×10⁻³, D 1.1547 → 1.1570×10⁻³, R 1.1172 → 1.1185×10⁻³): the early stop is an unplanned regulariser.
The comparison survives: D_LL 3.84×10⁻⁵ and S 1.074 at the tight tolerance. `r.success`, `nit` and the gradient are
not recorded anywhere.

**Fix.** Optimise the summed (not mean) loss or set tolerances to the problem's scale; write `success`, `nit` and the
gradient norm into `primary.json`; mention the regularising stop in Limits.

### 5. The G4 geocoding audit cannot see wrong matches inside neighbouring councils (medium; gate partly hollow)

**Evidence.** `g4_geocode.json` reports 0 distant mismatches of 954, but the criterion (the gauge's council equals the
record's council or a neighbour) passes any wrong point in an adjacent region. `data.json: geocode_box` finds 15 panel
units outside a generous bounding box of their FENZ region; most are region mis-coding by FENZ with a correct point
(for example Inangahua under Canterbury, Paraparaumu under Manawatu-Wanganui), but at least two are wrong points
accepted because the neighbour rule allowed them: a Northland-coded record placed at Auckland's Ōtara and a
Bay of Plenty-coded record placed at Napier's Maraenui. 20 units have a FENZ region that differs from their TLA's
modal region (52,936 rows, 0 floods), so the region effect they receive is the wrong one. The spot check of 28
well-known places found no error, so the error rate is low, but G4 asks for an error audit with a judgeable
denominator and this metric has none.

**Fix.** Audit a random 50 of the 954 units against the TLA polygon or a second gazetteer field (TLA is in the
gazetteer), report the error count with its denominator, and fill region from the TLA's modal council rather than
from the record.

### 6. The spline spends its freedom on drizzle (minor; design note)

**Evidence.** `data.json: knots`. Interior knots sit at the quartiles of all positive training rain: 1.0, 3.0 and
8.2 mm for depth, 0.018, 0.058 and 0.167 for rarity; the boundary knot is at 74.5 mm / 1.35, beyond which 33–39% of
training flood days and 8–12 of the 64 held-out ones lie on a linear extrapolation. The onset threshold (10 mm, 0.20)
and the storm-day predictions come from a curve with no bend in the range that matters. Both models share this, so it
does not bias H1, and it is what makes finding 2 exact in the tail.

**Fix.** None required for this verdict; note it. A future version should place knots on the distribution of wet days
(say days above 5 mm) or at fixed depths.

### 7. Wording and numbers that do not match the tables (minor)

- **"24 of them in the Nelson–Tasman floods of 25–30 June 2025"** (verdict block, plain terms, overclaim row 13).
  `data.json`: the 24 held-out floods on those six days are Tasman 13, Marlborough 8, Auckland 2, Nelson 1. The post hoc
  removes all 24. Say "22 in the top-of-the-South-Island floods of 25–30 June 2025 (Tasman, Marlborough, Nelson), plus
  2 elsewhere on those days".
- **"tested once on FY2024/25"** (standfirst, overclaim row 5). The held-out year was scored on three panels: the
  stopped v0 run (opened after the result), the D2 panel, and the D3 panel. Say "scored once per panel build; the
  rule's outcome was the same on all three".
- **"Across all years, flood callouts become ten times more likely ..."** (plain terms, overclaim row 27). The onset is
  a training-years fit (FY2017/18–2023/24) and is common to all regions by construction. Say "In the model fitted to
  2017–2024".
- **"8–9 mm (Bay of Plenty, Hawke's Bay, Marlborough, Wellington)".** 0.20 × the suburb-median M6 gives 7.9, 7.9, 7.5
  and 8.2 mm (gauge-median: 7.6, 8.6, 8.4, 8.6). Say "about 8 mm". Northland and the West Coast (12.8, 12.1) are right.
- **`plausibility.md`** still carries pre-D3 numbers: Auckland rarity model 35% (posthoc.json 36%), "3.4% of the depth
  model's log-loss, or 7.6% of its skill" (now 3.2% and 7.3%).
- **`overclaim_check.md`** rows 1, 20 and 21 cite pre-D3 backings (D_LL 3.92×10⁻⁵, V2 S 0.953, AEP 1.053, IDW 1.075).
  The labels stand; the backings should be refreshed.

### 8. Five gauges leave the assignment without a coverage entry (minor; G2)

**Evidence.** `data.json: gauges`. `rain_daily.parquet` holds 443 gauges; 438 have coordinates and a HIRDS 6-h index
depth, and `panel.py:35` drops the other five silently before the distance search. They are not in `coverage.json`.

**Fix.** Add a `gauges` stage to coverage.json (443 attempted, 5 dropped: no HIRDS depth or location).

### 9. "Supported" is honest, with the above caveats (judgement)

The rule is met and the report leads with the fragility. My decomposition (`models.json: decomposition`) sharpens
it: the whole held-out margin comes from the 64 flood suburb-days (+4.1×10⁻⁵), the 335,475 dry suburb-days pull the
other way (−0.4×10⁻⁵); 65% of the margin is from 26–28 June 2025 and a further 17% from 19–20 April 2025; removing
any single day leaves D_LL ≥ 2.6×10⁻⁵, so the interval excludes zero under every leave-one-day-out, and the
bootstrap is seed-stable. Counting the West Coast (no held-out flood) is per the plan's ≥ 20 all-years rule, which it
meets at exactly 20, and the report discloses it. The LORO is where rarity's advantage is most meaningful (a
transferred depth curve has no way to know a region is wet), and the report could say so. The verdict word can stay
once finding 2 is in the text; "Supported (fragile)" would be more accurate in the lead's verdict_tag.

### 10. Onset thresholds (adequate)

The plan asked for region-specific thresholds; with one shared rain curve and additive region effects they are
common by construction, and the report says so plainly. Adequate. The cheap version of what the plan meant is a
region × rain-slope interaction or per-region fits; worth one line as future work, not a condition of publication.

## Gate checks

- **G1 (leakage).** Real and mostly complete: the test year is used only for scoring; knots, standardisation and
  activity come from training rows; gauge assignment and geocoding never see outcomes. Two gaps: the LORO eligibility
  count (≥ 20 floods) includes test-year floods (harmless here), and the standfirst's "tested once" understates three
  scorings (finding 7). D3 is a post-result data change motivated by the HIRDS review, not by this result, and is
  documented with before-and-after numbers; acceptable.
- **G2 (coverage).** `coverage.json` exists and reconciles with `fenz_rows.json`, `geocode.json` and
  `panel_coverage.json`. No silent fallback enters a statistic (no NaN in activity, d6, M6 or ante72; no duplicate
  keys). Missing: the five-gauge drop (finding 8) and the duplicate-unit inflation (finding 1).
- **G3 (plausibility).** Partly hollow. The three "traces" are region-day aggregates, not raw-to-output traces of
  units; the water-year-maximum invariant is asserted without code in the repo (I confirmed it independently,
  3,543 gauge-years exact); the "joins neither duplicate nor drop units" invariant is false (finding 1); two numbers
  are stale (finding 7). My own unit traces (`trace.json`) pass: for an Auckland suburb-day with a flood callout
  (4 March 2025: 1 flood exposure, d6 14.8 mm = raw recomputation, rarity 0.34, fitted p 0.09% D / 0.11% R), a Tasman
  suburb-day on 27 June 2025 (6 flood exposures, d6 78.4 mm = raw, rarity 1.57, p 29% D / 38% R) and a dry West Coast
  suburb-day (22 September 2024: no exposure, d6 25.8 mm = raw, rarity 0.23, p 0.023% D / 0.013% R), the FENZ counts,
  panel rain, raw recomputation and model predictions agree; the three storm-day rows of `posthoc.json` are
  reproduced from a fresh fit (Auckland 33%/36%, Hawke's Bay 8%/10%, Nelson–Tasman 3%/4%) and move by at most 0.3
  points at the tight tolerance.
- **G4 (error audit).** The window audit is sound. The geocoding audit has no judgeable denominator (finding 5).
- **G5 (overclaim).** The tool passes; labels are honest for the data as built. I re-label row 1 Partially supported
  (finding 2), row 13 and row 27 Partially supported (finding 7), and row 2's "954 suburbs" Partially supported
  (finding 1). Rows 1, 20, 21 have stale backings.
- **G6 (attribution).** Passes; five claims spot-checked (F1, F2, F4, F5 by title through OpenAlex; F3 from the HIRDS
  v4 method, which does use the median annual maximum as its index), roles and conditions correct.
- **G7.** Does not apply: no unit is labelled by a person or an agent; geocoding is deterministic. Confirmed.

## Checks the brief asked for, in one line each

- Outcome construction: civil-time conversion verified by the DST-hour test; day-first 2024/25 verified; suburb-day
  aggregation correct; "Flood" is a defensible primary (nationally 3,483 Flood rows vs 4,602 cyclone-coded; on 13–14
  February 2023 in Hawke's Bay, 155 exposures: 21 Flood, 41 cyclone-coded of which only 6 carry a water or flood action,
  93 untyped), and the V1/V2 variants that widen it are reported and inconclusive. The Flood code is a narrow subset
  of flood work (933 of the 4,840 weather-flood water-removal exposures are coded Flood), which the report should say
  beside the V1 row.
- Geocoding: normalisation fine; the council filter does not bias entry (it removes 17 single-candidate wrong-region
  names and leaves multi-candidate names to the TLA centroid) but cannot catch neighbour-region errors (finding 5);
  spot check passed.
- Rain assignment: as planned; informative missingness (finding 3); five silent gauge drops (finding 8).
- Models: knots chosen separately and fairly, but the comparison is not fair to "depth with climatology" (finding 2);
  convergence (finding 4).
- Inference: bootstrap and S condition correct; LORO West Coast disclosed; "Supported" honest with caveats
  (finding 9).
- Onset thresholds: adequate (finding 10).
- Report: numbers match except finding 7.
