# Review: energy-outage-major-event-day-ratchet (pre-review draft 2b5cb6b)

Reviewer checks and their outputs are in `review/reviewer_checks/` (check1 raw scan, check2 independent re-derivation,
check3/4 blank rows, check5 independent re-implementation of the analysis, check6 simulation variants, check7 EIA
trend comparison and the 2015 zero days). Nothing outside `review/` was modified; nothing was committed by the
reviewer (commit 96c8a7c, made by someone else on 2026-10-20, swept `review/reviewer_checks/` in with another lead's
files; the study files are byte-identical to 2b5cb6b).

## Verdict: fix first

The pipeline is sound and the three preregistered verdicts are correctly derived from it: an independent
re-implementation reproduces every table to machine precision and the bootstrap intervals to resampling noise, the
daily SAIDI re-derives exactly from the raw files, the git timeline is clean, and every number in the report matches
the tables. What is not supported is the report's narrative around the verdicts: (1) the "storm leakage" story that
the headline, the simulation section, the "what it does not show" section and the plain-terms section are built on is
mostly an artefact of how the simulation defines a storm; (2) H2's "Refuted" depends on 2015, a year with visibly
incomplete coverage, sitting in the frozen baseline, and is Inconclusive under every alternative including the
study's own preregistered sensitivity; (3) the "+3.1% a year rise in everyday outage minutes" is not seen in the
utilities' own MED-excluded SAIDI for the same states and years, which the report has in hand but does not compare;
and (4) the closest prior work, flagged by the lab's own scouting critique, is omitted. These need new text and two
small added analyses (the reviewer's versions can be reused), not a re-run of the pipeline.

### Verified and found correct (no action needed)

- **Daily SAIDI construction** (check1, check2). UTC to local conversion, DST days and year boundaries are handled
  correctly: for DC, FL, VT, MI, IA, IL, LA and NV, all 4,018 days each re-derive from raw rows (selected on the raw
  `state` column, own time-zone code) to within 6e-14 of `data/daily.csv`. No exact or within-slot duplicates worth
  mentioning (0 in nine years; 262 rows in 2019 and 242 in 2025, 2e-8 of customer-minutes). Snapshots are on the
  15-minute grid (0–121 off-grid timestamps per year out of ~35,000). The 2023 `sum` column has the same row
  structure and the expected magnitude (4.24e9 customer-snapshots vs 4.97e9 in 2022 and 7.57e9 in 2024). MCC
  denominator and zero-filling match the plan. The data start 2014-12-31 19:00 EST, so local 2015-01-01 is
  complete. 204,918 state-days = 51 systems x 4,018 days.
- **Inclusion rule** (check5): reproduced exactly; the 25 systems and the ten exclusions are as the plan specifies.
- **Thresholds and indices** (check5): 2.5β window Y-5..Y-1, non-zero days, natural logs, sample SD, strict `>`
  for MEDs, frozen, q99 and 10-year rules all as preregistered and reproduced to 1e-13.
- **Trends and bootstrap** (check5): the FE estimator and the state-cluster bootstrap reproduce; H1's Inconclusive
  rule and H2's sign convention (rolling minus frozen; Supported if upper bound < 0) match plan.md §3.
- **Decomposition arithmetic** reproduces (but see finding 8 on labels).
- **Validation statistic** reproduces (0.944); and the proxy is better than the report says: within-state Spearman
  over 2018–2024 has median 0.96 (no state negative), year-on-year log changes correlate 0.95, the EAGLE-I/EIA level
  ratio has median 1.09, and the EIA with-MED all-events trend over 2020–2025 (-3.0%/yr) matches EAGLE-I's (-3.4%).
- **Monte Carlo**: rates reproduce (A: rolling 0.434 vs 0.4385, oracle 0.585 vs 0.594; B: 0.322/0.083/0.024; C at
  nominal); the ratio bootstrap, Wilson intervals and false-positive rates are as preregistered.
- **Git**: plan 950d8c0 (15:48) → code e868d1c (15:55) → D1 4babc1f (21:01) → build cache 21:05–21:21 → tables
  21:23–21:27 → figures/report 2b5cb6b (21:29). `analysis.py` and `simulate.py` are byte-identical to e868d1c.
- **Report vs tables**: every number checked matches; `report.html` carries the same numbers as `report.md`.

## Findings

### 1. Major — the "storm leakage" narrative is mostly an artefact of the simulation's storm definition

**Where:** report.md:7–9 ("Its weakness runs the other way: a rising rolling threshold lets storm growth leak into
the 'normal operations' index"), 25–29, 177–181 ("Scenario B shows the rolling rule's real weakness"), 202–205,
52–54 ("Its real weak spot ran the other way ... storms in disguise"); F4 caption ("so any detection by a normalised
index is leakage", figures.py:112–113); simulate.py:3, 24, 43.

**Evidence** (check6_simulation_variants.json/.log, 2,000 systems per scenario, same seed and mixture):

- In the preregistered design a "storm" is any day above the 95th percentile of non-zero days (`u`). The 2.5β
  threshold sits at median 2.7 x `u` (check5 `tail_vs_threshold`), so **57–66% of simulated storm days fall below the
  rolling threshold** and supply 21–29% of the rolling "normal operations" index in year 6, rising to 39% by year 11
  in scenario B. The real data look the same: 58% of the top-5% days of 2015–2019 are below the 2015–2019 threshold
  and supply 21% of the non-MED index. Under IEEE 1366 these days *are* normal operations; growth in their number is
  a normal-operations deterioration, not leakage.
- Growing only the tail's **scale** (bigger storms, same frequency: the mechanism the report describes, "the rising
  threshold let bigger storm days count as ordinary ones") gives **no leakage at all**: rolling 5.2%, frozen 3.6%,
  mean rolling slope -0.1%/yr. Growing only the **frequency** gives 32% (frozen 14%). The whole B effect is more
  sub-threshold storm days, which every normalised index counts.
- Defining a storm as a day that would be an MED at baseline (tail fitted above each state's own 2015–2019 2.5β
  threshold, median 2.1% of days): scenario B detection is **rolling 7.9%, frozen 4.3%, q99 5.8%, oracle 4.3%**. The
  genuine rolling-rule channel is about 3–4 points above nominal, not "a third of systems". (Under this definition
  scenario A gives rolling 50%, oracle 45%, ratio 1.11 (1.08–1.16): H3 Refuted is robust.)
- The ξ cap does not drive any of this (ξ ≤ 0.5 variant: H3 ratio 0.76, B rolling 32%).

**Fix:** keep the preregistered B result but report the diagnostic (share of simulated storm days below the threshold)
and the MED-scale-storm variant next to it; replace the "weakness runs the other way"/"real weak spot"/"storms in
disguise" framing with: growth in the frequency of sub-MED bad-weather days enters every normalised index, the
rolling one most because its threshold also rises, and that is what the standard counts as normal operations. Rewrite
the F4 caption (detection in B is leakage only for days above the threshold). The "What it does not show" bullet
(202–205) and the frozen/q99 "firmer lower estimate" claim should be reworded accordingly (the frozen index also
counts sub-threshold storm days; its lower trend is a baseline effect, finding 2).

### 2. Major — H2 "Refuted" rests on 2015 being in the frozen baseline; every alternative is Inconclusive

**Where:** report.md:15–19, 139–141, 150–151 ("The threshold rose ... 4.0 ... to 4.9"); plan.md §1(b), §3 H2;
analysis.py:30–31, 111–114.

**Evidence** (check5 `H2_alt_frozen_windows`, `annual_alpha_minus_2017_2019_mean`, `threshold_ratio_medians`,
`trends_2021_2025`; check7; check1):

- Rolling minus frozen MED-excluded trend, 95% cluster-bootstrap intervals: preregistered baseline 2015–2019
  **+0.79 (+0.18, +1.48) Refuted**; frozen on 2017–2019 +0.56 (-0.10, +1.25) Inconclusive; on 2018–2022 +0.64
  (-0.15, +1.52) Inconclusive; on 2016–2019 +0.67 (+0.02, +1.35) marginal; preregistered coverage sensitivity +0.54
  (-0.11, +1.23) Inconclusive (the report's own number); window 2021–2025 +0.45 (-0.22, +1.10) Inconclusive.
- The baseline is not stationary: the median across states of the annual mean of ln(daily SAIDI) on non-zero days,
  relative to 2017–2019, is **2015 -0.26, 2016 -0.06, 2017 -0.12, 2018 +0.11, 2019 +0.04**, then 2022–2025 +0.12 to
  +0.20. The frozen threshold from 2017–2019 is already 5.7% above the 2015–2019 one; the 2020–2024 threshold is
  only 3.7% above the 2017–2019 one. Most of the reported "4.0 to 4.9" rise is the window shedding 2015–2016 and
  taking in 2022–2024, not storms ratcheting the threshold.
- The 2015 shortfall is at least partly coverage, which the county-count rule cannot see: **Nevada has no data at all
  from 1 January to mid-June 2015** (46% of its 2015 days are zero, 100% in January–May) yet passes the rule because
  the same 15 counties report once data start (check7). Nationally, rows per snapshot go 362 (2015) → 609 (2018) →
  698 (2020) and distinct counties 2,498 → 3,072 (check1); ME and OK report 6% and 4% fewer counties in 2015 than
  their 2018–2022 median; collection gaps total 4.4 days in 2015, 2.9 in 2016, 2.5 in 2017, 1.8 in 2018 and under
  half a day after; the per-county gap-weighted/x15 ratio is highest in 2015 (VT 1.16, IA 1.16, LA 1.11; check2).

**Fix:** the preregistered verdict can stand as the preregistered test, but the headline, the H2 bullets and the
threshold section must say that H2 is Refuted only with the 2015–2019 baseline and Inconclusive under the
preregistered coverage sensitivity and under every cleaner baseline; add the alternative-window table; attribute
most of the threshold rise to window composition; disclose the Nevada 2015 gap and the 2015–2017 coverage growth
(finding 5) as the reason the baseline is low. The verdict line should not read as if the ratchet critique were
refuted outright (finding 6).

### 3. Major — the utilities' own MED-excluded SAIDI shows no trend over the same states and years

**Where:** report.md:13 ("rises +3.1% a year"), 43–45 ("everyday outage minutes rose about 2–3% a year under every
rule"), 131, 199, 202–205; validation section 188–193; analysis.py:121–130 (only the with-MED series is used).

**Evidence** (check7.json, 2020–2025, 150 state-years, same 25 states, IEEE-method utilities, customer-weighted):

| series | FE trend %/yr (95% CI) |
|---|---|
| EAGLE-I all events | -3.4 (-9.9, +3.0) |
| EIA-861 SAIDI with MEDs | -3.0 (-9.2, +2.7) |
| EAGLE-I MED-excluded, rolling 2.5β | +3.1 (+1.6, +4.9) |
| EAGLE-I MED-excluded, frozen | +2.3 (+0.8, +3.9) |
| **EIA-861 SAIDI without MEDs** | **-0.05 (-1.1, +1.1)** |

Rolling minus EIA-without-MED: +3.1 points (+1.9, +4.4). The proxy tracks the utilities' all-events series (also
2020–2024: -1.7 (-5.2, +1.3) difference, n.s.), so the gap is in the MED classification: the state-level 2.5β
excludes a smaller and faster-shrinking share of SAIDI than the utilities' own thresholds (MED share of SAIDI by
year, EAGLE-I 77/66/55/61/75/36% vs EIA 78/74/65/69/80/51%). The plan (§6) anticipated that state aggregation changes
which days are MEDs; the report nonetheless presents the +3.1% rise as a finding about everyday reliability.

**Fix:** add the without-MED comparison to the validation section and the results; state plainly that the rise in the
MED-excluded index is a property of the state-level construct and is not seen in utility-reported MED-excluded SAIDI
for the same states and years; reword the plain-terms paragraph (43–45) and the "It shows" bullet (199). This also
strengthens the point that the study is about the rule's behaviour on state aggregates, not about US reliability.

### 4. Moderate — the closest prior work is omitted and the novelty claim is overstated

**Where:** report.md:73–81 ("No study was found that quantifies ... the detection power of alternative rules");
plan.md "Novelty".

**Evidence:** Eto, LaCommare, Sohn & Caswell, "Evaluating the Performance of the IEEE Standard 1366 Method for
Identifying Major Event Days", IEEE Trans. Power Systems 32(2):1327–1333, 2016 (OpenAlex W2476114777, DOI
10.1109/TPWRS.2016.2585978; LBNL-1006405) proposes quantitative metrics for how well the 1366 method isolates major
events from underlying year-to-year trends and tests the DRWG's alternative threshold specifications. The lab's own
scouting critique (`research-lab/scouting/signature-areas-2026-10-16-critique.json`, entry for this lead) said the
lead's lit_against was "materially wrong" about exactly this paper.

**Fix:** cite it in "What was already known"; narrow the novelty claim to what is new here (an open, recomputed daily
panel from EAGLE-I; the frozen-threshold counterfactual; the reclassification accounting; the power comparison across
policies).

### 5. Moderate — the report says the coverage sensitivity addresses 2015–2017 coverage growth; it cannot

**Where:** report.md:209–210 ("Coverage grew in 2015–2017, which the inclusion rule and the coverage sensitivity
address"); analysis.py:95 (`yrs = d.year.clip(2018, 2022)`).

**Evidence:** the coverage history starts in 2018; the sensitivity divides 2015–2017 customer-minutes by the 2018
covered customers, so a 2015 shortfall in covered customers is left in the numerator and untouched in the
denominator. The only guard for 2015–2017 is the county-count rule, which finding 2 shows misses a five-month gap.

**Fix:** correct the sentence; say what the sensitivity does cover (2018–2022 levels) and that 2015–2017 coverage is
addressed only by the county-count rule, with its limits.

### 6. Moderate — the headline verdict and its first sentence overstate what was found

**Where:** report.md:7 ("Verdict: Refuted. The standard rule does not hide the trend in these data"), 12 ("so there
is nothing to mask").

**Evidence:** H1 is Inconclusive by its own rule; the all-events interval (-9.9, +3.0) is consistent with a 10%/yr
decline or a 3%/yr rise, so "nothing to mask" is "no detectable trend to mask". H2 is Refuted only in the primary
specification (finding 2). H3 is the robust Refuted (ratio 0.74 (0.70–0.78); 0.76 with lighter tails; 1.11 with
MED-scale storms). The sentence "does not hide the trend" asserts what H1 could not test.

**Fix:** "Verdict: Refuted (H3; H2 under the preregistered baseline only). H1 Inconclusive: no detectable all-events
trend to mask." Keep the one-word tag if the lab's convention needs one, but the first sentence must carry the
qualification.

### 7. Minor — data-quality facts the report should disclose (none changes a verdict)

**Where:** report.md:93–95 ("Days with no record are zero"), 209–211.

**Evidence** (check1, check3, check4, check2):

- The 2015–2021 year files end at **31 December 00:00 UTC**, so the last ~29–32 local hours of each of those years
  are zero-filled; 2022–2025 are complete (0.3% of a year; a small 2021→2022 step).
- **Blank `customers_out` rows** occur in 2017–2021 and 2025 (nationally 1%, 9%, 6%, 8%, 4%, 6% of rows) and are
  dropped. They behave like the explicit zero rows of 2022–2024 (the neighbouring non-blank value has median 1
  customer, p90 ~30, in both cases), so dropping them is defensible, but they are concentrated: MI 2018 28% of rows,
  IA 2019 17%, WI 2018–2020 12–14%, and in the trend window IL 2025 34%, SC 2025 30%, VT 2025 17%, OK 2025 12%,
  VA 2025 11%. A per-county interpolation bound on what they could hide is under 2% of annual customer-minutes for
  most state-years but 9% for IL 2025, 13% for VT 2025 and 8% for DC 2020.
- National collection gaps: 4.4 days in 2015 (one 24.5-hour gap on 6–7 January), 2.9 in 2016, 2.5 in 2017, 1.8 in
  2018, under half a day after.
- Per-county snapshot gaps longer than 15 minutes are 5–11% of snapshots; the x15 convention is the right one for
  snapshot data (a gap usually means the outage ended), but a gap-weighted alternative runs 1–7% higher in most years
  and 10–16% higher in 2015 for VT, IA and LA.
- The last 5–8 local hours of 2025-12-31 are absent (no 2026 file). Nevada 2015 as in finding 2.

**Fix:** a short data-quality paragraph in "How it was done" listing these; say that "no record" includes these
dataset gaps.

### 8. Minor — the decomposition's "MED growth" is not what plan.md §5 defines

**Where:** analysis.py:65–75; report.md:156–161 ("storm change: median -161 minutes"); plan.md §5.

**Evidence:** the code's `MED_growth` is the residual total - nonMED - reclassification, i.e. the change in the
excluded part net of reclassification; the plan's "MED growth at a fixed (2020) classification" is total - year1 =
median -156 (non-MED growth at the fixed 2020 classification is +18, vs the Shapley +14). The three plan parts do not
sum to the total, which is presumably why the code did this; the report should say which it reports.

**Fix:** label the column "MED change net of reclassification" (or report the plan's version and note that
reclassification is a transfer between the two parts).

### 9. Minor — simulation deviations not recorded; a preregistered output is missing

**Where:** simulate.py:28 (`xi=min(c, 0.9)`), plan.md §4; report.md:182–184; simulation.json
`median_years_to_detect`.

**Evidence:** the ξ cap is not in the plan (14 of 25 states hit it; raw MLE ξ ranges 0.17–2.32);
it was in the code committed before the data, so it is a design choice rather than tuning, and it does not matter
(finding 1), but it belongs in deviations.md. "Years to first detection" (plan §4 outputs) is computed (median 4–5
years) but not reported.

**Fix:** record the cap in deviations.md with the ξ ≤ 0.5 result; add one line on years to detection.

### 10. Minor — D1's "before any series was computed" is loosely true

**Where:** deviations.md D1; 4babc1f.

**Evidence:** the original sequential build.py (e868d1c) would have computed 2015–2022 state-day totals in memory
before failing on the 2023 column; nothing was written or seen, and the D1 change (reading `sum`, caching per year)
does not alter the computation, so no analytic choice was informed. Timeline otherwise clean.

**Fix:** one clause in D1 saying the failed run produced no output that was inspected.

### 11. Minor — small wording inconsistencies

- report.md:29 "about 2.3% a year" vs 204 "about 2.2% a year" for the frozen/q99 indices (2.26 and 2.25).
- report.md:31–32 and 190–193: "ranks states almost exactly" describes a pooled state-year Spearman; add the
  within-state figure (median 0.96; year-on-year changes 0.95), which is the one that matters for trends and is
  stronger support for the proxy than the pooled number.
- report.md:150–151: "the median state rolling threshold went from 4.0 ... to 4.9" should carry the window-composition
  caveat of finding 2.
- F3 title "The rolling threshold rose, so fewer days were excluded" is correct as a description of the counts.
