# Review: auckland-nz-jade-water-value-calibration (draft at commit 96c8a7c)

Independent adversarial review, 2026-10-21. Environment as briefed: the numpy venv at
`energy-nz-hydro-marginal-emissions-horizon/venv`, nothing installed. Scripts, their outputs and the small
evidence files are under `review/reviewer_checks/`; two full `tidy_results.csv` files (2024 week 32, 2023 week 20),
one monthly and two daily price files were re-downloaded from the EMI blob store to `/tmp/jade_review_downloads/`
(checksums in `reviewer_checks/evidence/downloads_SHA256SUMS.txt`). The study directory was not modified.

## Verdict: fix first

The arithmetic is right and the pipeline is clean. Every number I re-derived from raw files matches to the cent, the
filtered cache is identical to the full files on the rows it keeps, the week alignment is verified to the day, and
H1 survives every treatment of dependence I tried (lower bound 41-47% against a 20% threshold). None of that is in
doubt.

The report cannot go out as written, for five reasons, all in the text and the intervals rather than the primary
numbers:

1. The headline interpretation — "hydrological uncertainty alone accounts for a band about one-twentieth as wide as
   the variation prices actually show" — is not what was measured. The published runs price the scored week as a
   risk-neutral least-cost dispatch at a flat long-run fuel-price assumption that differs from the current week's
   own input (in August 2024, gas at $13.20/GJ for the scored week against $28.31 for the freeze week). The band is
   narrow because JADE's price is a short-run marginal cost bounded by thermal costs and $530+ shedding tranches,
   not because hydrology matters little; it stays $15-60 wide even 52 weeks out. (Finding 1)
2. The title, verdict bullets and plain-terms section call the across-week 10th-90th percentile spread "the range
   prices actually took" / "ranged over $265". The realised weekly range is $0.36 to $796.87. (Finding 2)
3. H2 "Refuted" is a ceiling effect. With the other-weeks rate at 56%, the largest ratio arithmetically possible is
   1.79; the threefold threshold could not have been met once H1 held. The report presents the refutation as a
   finding about storage and says "the effect is real" on an interval whose lower bound falls to 1.01-1.06 under
   longer blocks, resting on two consecutive clusters of weeks, one of them the 2024 gas shortage. (Finding 3)
4. The block-4 bootstrap understates dependence: the exceedance indicator has lag-1 autocorrelation 0.66 and changes
   value 24 times in 152 weeks (iid would give ~73). Effective sample size is about 19. The H1 interval should be
   roughly 41-79%, not 46-73%. The verdict is unaffected. (Finding 4)
5. Three deviations from `plan.md` are not recorded in D1, and the all-years storage sensitivity sums reservoir
   volumes in Mm3 across lakes — the operation D1 item 5 says is invalid — and flags a different quantity from the
   preregistered one. (Finding 6)

Required edits are listed at the end. With them made, H1 Supported stands; H2 should be reported as "Refuted by the
preregistered rule, which the base rate made unattainable", with the quintile trend that the split hides.

## What was verified and holds

| check | result | script |
|---|---|---|
| Git order | `plan.md` 21:54:47, `fetch.py` 21:56:34, `analysis.py` 22:03:15 and 22:06:37, first data file written 21:59:36, results 22:45:11, committed 22:47:36. The results commit also added the post-hoc spread block to `analysis.py` (declared, D1 item 6) and the December daily-file fallback to `fetch.py` (D1 item 4); neither touches H1 or H2. | (git, mtimes) |
| Cache fidelity | Full `tidy_results.csv` for 2024 week 32 and 2023 week 20 filtered by the same rule give 6,825 and 6,750 rows, identical to `data/runs/*.csv`. | `rederive.py` |
| Price cache | HAY2201 rows for August 2024 and July 2025 (1,488 each) and the December 2025 daily files for the 1st and 15th are identical to the cache. | `rederive.py` |
| Hand-checked week | 2024 week 32, stage 2 = 12-18 Aug 2024: 91 sequences, min $139.33, p10 $151.58, p50 $160.99, p90 $167.07, max $173.04; realised $449.36 over 336 half-hours, daily means $350.20-$598.98; ratio 2.690. All as reported. | `rederive.py` |
| Two more runs | 2023 week 20 (stage 2 = 21-27 May 2023): p10/p50/p90 $96.47/$105.09/$107.37, realised $28.92, PIT 0. 2025 week 30 (30 Jul-5 Aug 2025): $126.51/$138.68/$146.07, realised $129.48, PIT 0.220. Both match `runs.csv`. | `rederive.py` |
| Realised averages | Recomputed for all 152 stage-2 weeks from the cache: max difference 0.00. | `realised_average.py` |
| Week alignment | Input stamps fall 1-3 days after the JADE week start (2023: Mon-Wed, offsets 1-3; 2024: Tue-Wed, 1-2; 2025: Thu, 1), so the Authority runs the model one to three days into its own week 1. The run's `hours_per_block.csv` carries 169 h in week 14, 167 h in week 39 (or 40 in 2012) and 192/216 h in week 52, which only a 1-January-based week gives; the 50- and 46-period days in the settled data fall inside exactly those weeks. One `Inputs/data_files/<stamp>` folder and one `tidy_results.csv` per run (152 of 152). | (inline), `realised_average.py`, listing |
| Stages 1 and 3 | 57.2% and 58.6% as reported; the stage-1 bands for both re-downloaded runs match `runs.csv`. | `by_stage.csv`, `rederive.py` |
| Block weighting | A weekly mean of half-hours is invariant to block boundaries, so the hours weighting cannot bias the comparison. Under the standard JADE block definition (weekday 07:30-09:30 and 17:30-19:30 peak, 09:30-17:30 and 19:30-23:30 shoulder) the block hour counts reproduce the run's `hours_per_block.csv` in 149 of 152 weeks (the three week-52 weeks differ), and a block-matched average gives the same 59.2%. Per-block exceedance: peak 57.2%, shoulder 61.8%, off-peak 59.2% — broad-based, not spike-driven. | `realised_average.py` |
| DST and week 52 | 334/338-period weeks pair with 167/169 JADE hours correctly. Week-52 stage-2 weeks are 8 or 9 days in JADE but 7 in the realised average; using the full 8/9 days changes no verdict (2023_51: $164.83 vs $153.14 against p90 $83.79). | `realised_average.py` |
| Robustness of the realised measure | Weekly median of half-hours 57.9%, 5-95% trimmed mean 56.6%. Demand weighting cannot be done without load data; it would raise the realised average (peak prices are higher) and so could only raise the exceedance. | `realised_average.py` |
| Percentile method and ties | Exceedance, lower tail and 80% coverage are identical under all eight numpy methods; 90% coverage 17.1-18.4%. Every run has tied weekly prices (median 80 distinct of 91; 2024_07 has 17); the mid-rank PIT handles them. No run has p90 = p10. | `percentile_fairness.py` |
| Node mapping | JADE's NI/HAY and SI/HAY medians are 1.013 and 0.957; the market's OTA/HAY and BEN/HAY are 1.072 and 0.971, so JADE's three-node structure resembles the real one and HAY is a demand node (`demand.csv`, ~380 MW peak). Scoring JADE NI against OTA2201 gives 62.5%, JADE SI against BEN2201 57.9%, JADE HAY against OTA/BEN 62.5%/56.6%. The result is not a mapping artefact. | `node_mapping.py` |
| Storage percentile | Reproduced for all 104 runs to 0.00. National capacity from the derived series sums to 4,351 GWh, consistent with the known system; the 2024 trough is 1,138 GWh. | `storage_split.py`, `hmd_check.py` |
| Report vs tables | Every number in `report.md` matches `primary.json`/`runs.csv`/`by_stage.csv`; `report.html` carries the same numbers (the only HTML-only decimals are CSS sizes). | (inline) |

## Findings

### 1. Major — what is compared is a risk-neutral marginal-cost benchmark at a long-run fuel price, and the report attributes its narrowness to hydrology

**The mapping is fine; the interpretation is not.** JADE's `prices` are the duals of the nodal energy balance in a
cost-minimising dispatch (documentation §1: thermal plants enter at "short-run marginal cost", demand is a fixed
parameter D_i(b,t); `reviewer_checks/evidence/JADE_documentation_outputs.txt`). The Authority's run file has no
`Risk lambda`/`Risk beta` entries, and the documentation states the defaults are "0 = risk neutral" and "1 = risk
neutral" (`evidence/run_2024_week32.csv`, `evidence/JADE_documentation_risk_settings.txt`). The Authority's own 2022
EPOC slides describe the runs as "Assumption laden: Risk neutrality, single scenario re: demand forecast, fuel
prices", produced because the "Market monitoring team require water values to support their efforts in monitoring
trading conduct" (`evidence/EA_EPOC2022_BishopNguyen_slides_text.txt`). So the quantity scored is: the price a
risk-neutral least-cost planner would set, given this week's storage and one of 91 inflow histories. A market price
differs from it by risk premia in water valuation, offers above cost, actual fuel prices, demand and outages. The
exceedance rate therefore measures the gap between market prices and a competitive-cost benchmark under inflow
uncertainty. That is a legitimate and interesting quantity — it is close to what the Authority uses the runs to look
at — but it is not "calibration" in the forecast sense, and the report's gloss on it is wrong in two specific ways.

**(a) The scored week is priced at a long-run fuel assumption, not at "fuel costs held as given".** The
`thermal_fuel_costs.csv` in each run carries weekly values up to the freeze week and then a flat forward assumption
from the stage-2 week on (`evidence/thermal_fuel_costs_excerpt_*.csv`):

| run | gas $/GJ, freeze week (stage 1) | gas $/GJ, scored week (stage 2) onward | CO2 $/t, stage 1 → 2 |
|---|---|---|---|
| 2023 week 20 | 6.97 | 9.47 | 64.97 → 77.76 |
| 2024 week 32 | 28.31 (rising 25.6-28.3 over weeks 28-32) | 13.20 | 51.65 → 64.13 |
| 2024 week 40 | 19.31 | 16.28 | 58.75 → 63.37 |
| 2025 week 30 | 14.02 | 14.02 | 59.16 → 59.16 |

In August 2024 the scored week was priced with gas at less than half the run's own current value, while spot gas in
the market was far above both. With gas at $13.20 the run's thermal stack (`evidence/thermal_stations_2024_week32.csv`)
runs from about $128/MWh (Huntly e3p: 7.4 GJ/MWh × 13.2 + 5.2 + 7.4 × 0.054 × 64.13) to about $184/MWh (peakers at
10.5 GJ/MWh), and the next price level is the first shedding tranche at $530 (`evidence/lost_load_2024_week32.csv`).
The stage-2 envelope that week was $139-173: the model's price was pinned to the thermal stack. The market's $449
is above every thermal cost in the model and below the first shedding tranche; JADE cannot produce it under any inflow sequence without shedding load. The stage-1 to
stage-2 step in the simulated median is negative in 73% of 2024 runs (median −$10.49) and positive in 2023 (median
+$3.63), tracking the fuel step. `report.md:29` ("Demand, fuel costs, station outages and offer behaviour are held
as given") and `report.md:54` ("stays fixed") should say that fuel costs for the scored week are a long-run
assumption that can differ materially from the freeze week's own input, and the verdict should name risk neutrality
(the plan's §5 threat 1 promised this "in the verdict itself"; it is not there).

**(b) "Hydrological uncertainty alone accounts for a band about one-twentieth as wide" (`report.md:31`, `:55`) is
not what was measured.** Hydrology is the dominant driver of New Zealand prices — through risk-averse water
valuation and offers, exactly the channels JADE's risk-neutral cost dispatch does not model. What is narrow is
JADE's pricing of hydrology, not hydrology's effect on prices. The point is sharpened by the longer horizons the
study did not fetch (`fetch.py:35` keeps stages 0-4 only): from the full file, the 2024 week 32 band is $15.49 wide at
stage 2, $42.09 at stage 8, $26.18 at stage 26 and $58.49 at stage 52 (p90/p10 = 1.50); for 2023 week 20 it is $10.91
at stage 2 and $15.40 at stage 52 (`rederive.out`). Even with a full year of inflow uncertainty the band is a fifth of
the realised across-week spread at most. The narrowness is a property of cost-based price formation at fixed fuel
prices, not of a one-week horizon and not of hydrology. The honest sentence is something like: "the spread of a
risk-neutral least-cost dispatch price across 91 inflow years, at a fixed long-run fuel price, is about a twentieth of
the spread of market prices across three years; everything the market adds on top of inflow-driven cost — risk
premia, offers above cost, the actual gas price — is outside it."

**Fix.** Rewrite `report.md:28-34` and `:53-56` on these lines; add risk neutrality and the forward fuel assumption to
the verdict block; quote the Authority's own description of the runs' purpose; say in "What this does and does not
show" that the gap is the quantity the Authority's monitoring looks at, so a large gap is not a defect of the runs.
Consider replacing "calibration audit" (`report.md:72`) with "a comparison of the published cost-based price bands
with settled prices".

### 2. Major — the title and summary call a 10th-90th percentile spread "the range"

`report.md:21` ("Realised weekly prices over the same three years ran from $25.94 to $290.88"), `:21-22` ("the range
prices actually took") and `:48` ("Real prices over those three years ranged over $265") describe
`spread.realised_p10_to_p90_across_weeks`. The realised weekly averages ran from **$0.36 (week of 24 Dec 2025) to
$796.87 (week of 5 Aug 2024)** (`percentile_fairness.out`). The table row at `report.md:123` labels it correctly;
the title, the verdict bullets and the plain-terms section do not. The title's "$265 market" has no defensible
reading as stated.

The comparison itself is between a within-run band and an across-week spread, which the report concedes at
`report.md:129-134` and then leads with everywhere else. Fairer statistics (`percentile_fairness.out`) tell a
slightly weaker but still stark story, and should replace or accompany the 5.7%:

- band against the spread of the model's own errors (realised minus simulated median, p10 −$76 to p90 +$155, spread
  $231): **6.5%**;
- band against realised week-to-week change at the same horizon (p10 −$55 to p90 +$54, spread $110): **13.7%**;
- by year, band against that year's across-week spread: **13.5% (2023), 4.6% (2024), 5.4% (2025)** — the pooled 5.7%
  is pulled down by the regime shift between years, so "stable, not an artefact of one crisis" (`report.md:25`) is
  true of the exceedance rate but not of the ratio in the title;
- the band's half-width would have to be **6.9× wider for 50% coverage and 20.9× wider for 80%**.

A cleaner headline statistic is available and immune to percentile quibbles: the realised price fell **outside the
entire 80-91-member envelope in 71.1% of weeks** (above the maximum sequence in 55.3%, below the minimum in 15.8%).

**Fix.** Correct the three sentences; retitle or define "$265" as the 10th-90th percentile spread of weekly prices
across 2023-2025; give the by-year ratios and at least one error-based ratio; consider the envelope statistic.

### 3. Major — H2 "Refuted" is a ceiling effect, and "the effect is real" rests on two clusters

The ratio statistic is rate_low / rate_high with rate_low ≤ 1. With rate_high = 0.560, the largest attainable ratio is
**1/0.560 = 1.79**, below the threefold threshold (`bootstrap_sensitivity.out`). Once H1 came in at 59%, H2 could not
be Supported under any pattern of storage. The report says "The effect is real and it is not threefold"
(`report.md:13`) and applies the rule without noting that the rule had become uninformative. The plan set the
threshold expecting an "other weeks" rate near the nominal 10-20%; it should say so.

The 20 low-storage runs are two consecutive blocks: **2023_50-2024_03 (6 runs, 6/6 exceed)** and **2024_22-2024_35 (14
runs, 12/14)**, the second coinciding with the 2024 gas shortage. Block-4 resampling treats these as roughly five
independent pieces. With longer blocks the ratio interval's lower bound is 1.06 (L=8), 1.08 (L=13), 1.01 (L=26) and
1.11 (stationary, mean 8-26); the upper bound reaches 2.72. "The interval excludes 1, so low storage genuinely makes
things worse" (`report.md:169`) is too strong for a two-episode comparison confounded with a fuel shock; "consistent
with" is the most it supports. The drop rule (`analysis.py:348`) is immaterial: 9 of 4,000 resamples at L=4.

The preregistered split also hides the actual pattern. Exceedance by storage-percentile quintile (`storage_split.out`):
**18/20, 17/20, 16/18, 12/28, 1/16**. The relation is a strong monotone trend with the only clean break at the top
quintile, and the "other weeks" group averages together quintiles with 85-90% exceedance and one with 6%. In 2024 the
not-low weeks 10-21 exceeded 12/12 and the post-crisis weeks 36-52 exceeded 0/17; storage state and price regime are
the same thing in a hydro system, which is the mechanism, but it means the split cannot separate "low storage" from
"2024".

**Fix.** Report H2 as "Refuted by the preregistered rule; the rule could not have been met given the 56% base rate";
replace "the effect is real" with the quintile table and the cluster description; give the longer-block interval;
say the low-storage group is two episodes, one of them the gas shortage.

### 4. Moderate — the block-4 bootstrap understates dependence; the H1 verdict survives

Exceedance indicator autocorrelation at lags 1-8: 0.66, 0.59, 0.51, 0.44, 0.32, 0.30, 0.22, 0.16; 24 value changes
in 152 weeks against ~73 for an independent series; Bartlett variance inflation ≈ 7.9, effective n ≈ 19
(`bootstrap_sensitivity.out`). H1 95% intervals: iid 51-67%; L=4 47-73% (as reported); L=8 43-77%; L=13 42-79%; L=26
44-84%; stationary bootstrap with mean block 8/13/26: 42-76%, 41-78%, 41-79%; Wilson on n≈19: 38-78%. Every lower
bound clears 20%; the report's "more than twice that" (`report.md:10`) holds only just (41.4% vs 40%) under the
longer blocks. The MDE (18.7 points, `report.md:139`) is from the same under-dispersed draws and is roughly 1.4×
too small.

**Fix.** Report an interval from blocks of 13 or a stationary bootstrap alongside the preregistered one, state the
effective sample size, and drop or qualify "more than twice". The plan's "blocks of 4" was a preregistered choice, so
keep it as primary but say it was too short.

### 5. Moderate — bias is not separated from spread, though the plan promised it

`plan.md:78` lists "the median simulated price against the realised price, which separates bias from spread";
`report.md` gives only the two medians of medians ($107.56 vs $132.58). The realised price exceeds the simulated
median in 93 of 152 weeks (61%); the median ratio realised/p50 is **1.32**; the PIT mean is 0.635
(`percentile_fairness.out`). The failure is a 30% upward level bias plus a band far too narrow, and the two should
be stated separately because they have different explanations (the first is offers and risk premia above cost; the
second is the fixed-fuel cost-based price formation of Finding 1). A persistence baseline is also informative for the
"not a forecast" message: the last completed week before the freeze has median absolute error $32 against $65 for
the JADE median, and the JADE median is closer in only 34% of weeks (`realised_average.out`).

### 6. Moderate — three undisclosed deviations from the plan, and a sensitivity that is a different quantity

- `plan.md:77` promises BEN2201 and OTA2201 "reported alongside"; `report.md:200` says they are "recorded in
  `runs.csv` but not scored". Not in D1. (My numbers are in the verification table above.)
- `plan.md:80` promises the minimum detectable effect "for the exceedance rate and the ratio"; only the rate's is
  reported (`primary.json` H2 has none). Not in D1.
- `deviations.md:21-29` and `report.md:172` describe the all-years sensitivity as "JADE's own run-start reservoir sum
  with the season removed" and say it "agrees". `analysis.py:62-63,77` sums `reslevel` at stage 0 across lakes; the
  JADE documentation gives reservoir state "in Mm3" and the values match the HMD's active storage in Mm3 (Pukaki
  535.0 vs 539.5, Taupo 146.8 vs 143.9, Manapouri+Te Anau 413.4 vs 406.4 on 2024-08-06; `hmd_check.out`). That is
  the sum of volumes across lakes which D1 item 5 (`deviations.md:21`) says "cannot be added", and it weights Hawea
  (0.26 GWh/Mm3) four times as heavily as Tekapo (1.15 GWh/Mm3) relative to energy. The flag is also "bottom fifth of
  residuals from a two-harmonic fit to three years" (`analysis.py:203-214`), which by construction flags 20% of runs
  and compares each week with 2023-2025 only, not with the 44-year history the preregistered measure uses. It
  "agrees" because its 31 flags contain all 20 primary flags plus 2023_46-49 and seven weeks of March-May 2025
  (`storage_split.out`); that is overlap, not independent confirmation. JADE's `total_storage` (an energy series;
  documentation: "StoredEnergy ... total energy in MWh") was fetched and unused, and the HMD specific energies could
  have been applied to the JADE levels. Summing volumes rather than energies happens to change the primary low set by
  only two runs (2023_36 in, 2024_01 out), so the practical effect is small; the description is what is wrong.

**Fix.** Record all three in D1; describe the sensitivity as a different measure (volume-based, three-year relative);
either recompute it with energy weights or drop "agrees" for "flags a superset".

### 7. Minor — numbers and wording

- "91" is used as a fixed count at `report.md:28,40,50,53,178`, in both figure captions and the F1 legend; D1 item 2
  records 80-91 and `primary.json` shows 91 in 101 runs only. Say "up to 91" or "80-91".
- Five end-of-year runs have simulated p10 = 0 (2024_51, 2024_52, 2025_50, 2025_51, 2025_52; 2025_51 has 71% of
  sequences at exactly $0 and p50 = 0). F1's band is drawn to the axis floor there on a log scale. Worth a sentence:
  the model does produce zero prices when spilling, and the market did too ($0.36 that week).
- The week-52 stage-2 weeks are 8/9 days in JADE against 7 in the realised average (three runs, no verdict change);
  mention it in validation.
- The TPO (Taupo) scheme energy capacity differs between the 2023 and 2024 derived-capacity files (485 vs 587 GWh,
  ratio 0.567 vs 0.686); `analysis.py:155` takes whichever file sorts last. Say which file the ratios come from.
- `report.md:143` "does not grow with horizon" is true over stages 1-4 only; the fetch stopped at stage 4.
- `report.md:50-51` and `:178-180` ("daily averages from $350 to $599", "2.69 times") verified.

## Required edits before publication

1. Rewrite the headline interpretation (`report.md:28-34`, `:53-56`, and the verdict line) per Finding 1: risk
   neutrality, the long-run forward fuel assumption with the August 2024 example, and the correct attribution of the
   narrow band to cost-based price formation rather than to hydrology. Quote the Authority's stated purpose.
2. Correct "ran from / ranged over / the range prices actually took" (`report.md:21-22`, `:48`); retitle or define the
   $265; add the by-year and error-based ratios (Finding 2).
3. Restate H2 with the ceiling, the two clusters and the quintile table; soften "the effect is real" (Finding 3).
4. Add a longer-block or stationary-bootstrap interval for H1 and the effective sample size; qualify "more than twice"
   and the MDE (Finding 4).
5. Add a bias paragraph (Finding 5).
6. Record the three deviations in D1 and re-describe the storage sensitivity (Finding 6).
7. Fix the "91" wording and the minor items (Finding 7).

## Scripts and evidence (`review/reviewer_checks/`)

- `bootstrap_sensitivity.py` / `.out` — autocorrelation, effective n, H1 and H2 intervals under iid, moving blocks
  4-52 and the stationary bootstrap; the ratio ceiling; low-storage clusters; the drop rule.
- `percentile_fairness.py` / `.out` — percentile methods, ties, envelope exceedance, PIT, realised range, error-based
  and week-to-week comparisons, coverage multipliers, by-year ratios.
- `node_mapping.py` / `.out` — JADE NI/HAY/SI against OTA/HAY/BEN; zero-price runs; discreteness of the simulated
  distributions.
- `realised_average.py` / `.out` — realised averages recomputed; DST weeks; week-52 length; median/trimmed/block-matched
  alternatives; per-block exceedance; persistence baseline.
- `rederive.py` / `.out` — cache fidelity against two re-downloaded full files; three runs re-derived; longer-horizon
  bands; price-cache fidelity against re-downloaded monthly and daily files.
- `hmd_check.py` / `.out` — specific energies, capacity totals, lake series, JADE `reslevel` units against the HMD.
- `storage_split.py` / `.out` — storage percentile reproduced; volume-sum and deseasonalised alternatives; the
  2024 confound; exceedance by storage quintile.
- `evidence/` — the Authority's run configuration for 2024 week 32 (`run.csv`, `rundata.json`, `lost_load.csv`,
  `thermal_stations.csv`), fuel-cost excerpts for four runs, the JADE documentation's risk-setting and output pages,
  the text of the Authority's 2022 EPOC slides, the full blob listing (17,991 names) and SHA-256 sums of the
  re-downloaded files.

## Confirmation pass (commit 262f85e, 2026-10-21)

Checked: `report.md` (rewritten), `report.html`, `deviations.md` D2, `code/figures.py` and the regenerated F1/F2
captions and F1 legend. `git diff 96c8a7c 262f85e -- results/tables code/analysis.py code/fetch.py data` is empty, so
no pipeline code or result table changed. Every number quoted from my checks appears in both report formats with the
same value (`1.79`, `18 of 20`, `1 of 16`, `$0.36`, `$796.87`, `71.1%`, `$13.20`, `$28.31`, `61.2%`, the 41-79% interval,
the effective sample of 19); the only decimals present in the HTML and not the Markdown are CSS sizes. The F1 PNG now
carries "80-91 inflow years" in its legend.

| finding | status | where |
|---|---|---|
| 1. Risk-neutral, long-run-fuel benchmark misread as "hydrology alone" | **Resolved.** Verdict names the not-a-forecaster point and the reason; risk neutrality (no risk parameters, JADE default), the flat forward fuel assumption with the week-32/33 figures, the $128-184 stack and the $530 tranche, the Authority's 2022 wording, and an explicit withdrawal of the earlier reading are all present. | `report.md:6-8, 22-37, 58-64, 227-234`; D2 item 1 |
| 2. 10th-90th spread called "the range" | **Resolved.** Full range $0.36-$796.87 stated; $265 explained as a pooled percentile spread and called the least fair comparison; the three yardsticks and the 71.1% envelope statistic added. | `report.md:39-43, 139-149` |
| 3. H2 ceiling, two spells, quintiles | **Resolved.** 1/0.56 = 1.79 ceiling in the verdict and H2 section; "the effect is real" gone; two spells with their counts; quintile table; confound stated in the limitations. | `report.md:15-20, 196-211, 235` |
| 4. Bootstrap dependence | **Resolved.** ACF 0.66, effective n ≈ 19, 41-79% under longer blocks, "only just" twice the threshold, MDE understated by ~1.4. | `report.md:10-14, 153-159` |
| 5. Bias separated from spread | **Resolved.** 61.2% above the median, median ratio 1.32, PIT asymmetry, persistence baseline with its caveat. | `report.md:137, 172-179`; F2 caption |
| 6. Undeclared deviations; volume-sum sensitivity | **Resolved.** All three recorded in D2 item 6; the sensitivity withdrawn as corroboration with the Mm³ problem and the superset explanation; BEN/OTA shown as review-derived, not study-scored. The ratio MDE remains uncomputed, now declared; given the ceiling it is moot. | D2 item 6; `report.md:236-237` |
| 7. "91" and minor items | **Resolved.** "80 to 91" / "about 90" in text, table, legend and captions; the remaining minor items listed in D2 item 7. | `report.md:24, 49, 55, 133`; D2 item 7 |

### New or remaining problems in the revision

Two wording errors should be fixed before publication; the rest are optional.

1. **Fix: "exceedance falls monotonically by storage quintile" (`report.md:18`).** The quintile rates are 90.0%, 85.0%,
   88.9%, 42.9%, 6.3% — the third quintile is higher than the second. Say "sits at 85-90% in the bottom three fifths
   and falls to 43% and 6% in the top two". (My own review called it a "monotone trend"; that was loose and I withdraw
   the word.)
2. **Fix: attribution to the Authority (`report.md:63-64`).** "The Authority says plainly that these runs ... exist to
   work out how to use water, not to forecast prices." The 2022 slides state the purpose ("a steady state water release
   policy in presence of uncertain inflows") and the assumptions; they do not say the runs are not price forecasts.
   That is the study's inference and should be worded as such, e.g. "The Authority describes the runs as built on
   simplifying assumptions to work out how to use water; it does not present them as price forecasts, and our check
   confirms they should not be read as one."
3. Optional: "the gas price input follows the observed series up to that week" (`report.md:29`) — the source of the
   weekly pre-freeze series is not documented in the run; "a weekly series" is all that can be claimed.
4. Optional: "assumed gas at less than half what it actually cost" (`report.md:60`) — verified only against the run's
   own week-32 input ($28.31); "less than half its own figure for the week before" is the supportable form.
5. Optional: "Storage matters strongly" (`report.md:18`) reads causally; the confound is stated at `:235`, but
   "exceedance is strongly associated with storage" would match it.
6. Optional: the F1 caption's "in a fuel shortage sits far below the price of fuel" generalises from the one shortage
   in the window; "in the 2024 shortage sat far below" is exact.
7. Optional: D1 item 5 (`deviations.md:29`) still reads "it agrees with the primary split". D2 supersedes it, but a
   bracketed pointer "(superseded: see D2 item 6)" would stop a reader who finishes at D1.

### Fit to publish

Yes, once items 1 and 2 are corrected; each is a one-line edit. The primary results are unchanged and were verified
in the first pass; the revised interpretation is consistent with the Authority's run files and its own description of
the runs; H1 Supported and H2 "Refuted by a rule that could not be met" are stated with their limits.
