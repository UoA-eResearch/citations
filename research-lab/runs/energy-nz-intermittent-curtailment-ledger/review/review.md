# Independent review: energy-nz-intermittent-curtailment-ledger

Reviewer: Claude (Fable 5.1), 2026-10-22. Brief: `review/prompt.md`. Scripts and outputs: `review/reviewer_checks/`
(`check1` offer timing on sampled days, `check2` panel classes/gate/matched floor/windows/ledger, `check3` re-fetched
raw EMI day against the study's filter, `check4` bootstrap relabelling, `check5` projection, `check6` lead times over
all 2,617 days, `check7` concentration and definition dependence, `check8` solar floors). Python run with `-I`; one
raw EMI offers file (2025-10-15, 206 MB) re-fetched into `reviewer_checks/raw_emi/`. Nothing outside `review/` was
modified.

## Verdict: fix first

The preregistered pipeline is implemented as the plan says and its numbers reproduce (gate 27.1%, H1 Refuted and H2
Supported by rule, every figure in the report's tables matches `results/tables/`). The git order is clean: `plan.md`
(3bc4894, 20:34) precedes the fetcher (20:35) and the panel/analysis code (20:39); D1 (00:50-00:56) precedes
`build_log.json` and all curtailment figures; D2 was committed with the first results (01:41) before
`diagnostics.json` (01:43). The fetch filter is exact: the re-fetched raw file for 2025-10-15 has 1,264,430 rows and
5,520 latest energy rows with a potential at the study's POCs, equal to the fetch log and the study's filtered file
(check3). The noise-mass argument is right, and a potential-matched floor (my check2 d) leaves the post hoc
price-driven number almost unchanged (2.17% against 2.22%).

What cannot stand is the headline. "A growing price-driven core reaching 2.2%" and "reverses H2's reading" rest on
(i) a post hoc redefinition of price-driven under which the majority flips (73% of non-noise curtailment under the
report's "price at or below the plant's own offer", 47% under the plan's own $0.01 line), (ii) two plants, Turitea
and Kaiwera Downs, which supply 86% of the series and which are precisely the two plants that offer above $0.01, one
of them having moved its offer from $0.01 to $0.02 in the 2025/26 year, so that the growth is confounded with
where the merit order now puts dispatch-down, and (iii) a "dispatch-time potential" that is in fact a week-old
forecast for every solar plant and, since 2025, an intra-period revision for half the wind fleet. The frozen
projection also counts four commissioned plants as zero. These need fixing in the text, the tables and the projection
before publication; the computations behind the preregistered verdicts do not.

## Findings

### 1. Major: the headline's "price-driven" class is post hoc, flips the H2 reading only under its own definition, and cannot separate market spill from network constraint

Evidence (check7 output; `code/diagnostics.py:24-27`; `code/analysis.py:67`):

- H2 was preregistered as "price exceeds $0.01/MWh" (`plan.md` section 3, `analysis.py:67`). The report's post hoc
  class is "price at or below the plant's highest offer price" (`diagnostics.py:27`). Of the 126.3 GWh of 2025/26
  curtailment outside the unconstrained (noise) class, the share at price <= $0.01 is **47%**; at or below the
  plant's own offer **73%**; at price < $1/MWh **95%**; at price < $5 **99%**. The "reversal" of H2 therefore holds
  under the report's definition and not under the plan's; the plan's line sits on a knife-edge between plants
  offering $0.01 and plants offering $0.02 or $1.60 (finding 2). The report presents only the 73% figure.
- The 33.1 GWh "other" class is not "other": 31.2 GWh of it is in half-hours with price below $1/MWh (check2 c), i.e.
  the same near-zero-price surplus half-hours, at plants whose $0.01 offer happened to sit just below the price. The
  raw spot check shows what lives there: Turitea on 2025-10-15 TP30 had potential 196 MW, offer 221 MW at $0.02,
  output 103 MW and a node price of $0.04 (check3 tail); it was being held 93 MW below potential at a price above its
  offer, and the rule files that under "other".
- "Price at or below the plant's own offer" is the condition "the plant was marginal or dispatched down", which a
  constrained-off plant also satisfies because its nodal price falls to its offer. The report's caveat says so, but
  the summary, the title and the plain-terms paragraph ("turned down because the power is not wanted") do not.

Fix: report the non-noise split under both definitions (and the < $1 line) in the results table; replace
"price-driven" with "dispatched down (price at or below own offer)" and drop "reverses H2's reading" from the
summary, keeping it as a definition-dependent observation in the discussion; rewrite the plain-terms sentence so it
does not attribute cause.

### 2. Major: the 2.2% series is two plants, and its growth is confounded with those plants' offer prices

Evidence (check7 output; `results/tables/ledger_monthly.csv`):

- 2025/26 post hoc price-driven energy by plant: Turitea LTN2201 53.7 GWh, Kaiwera Downs GOR0331 25.4 GWh, next
  Waipipi 6.5 GWh; the two plants are 86% of 92.4 GWh. Fleet share with Turitea left out 1.15%, with Kaiwera Downs
  out 1.67%, with both out **0.41%**. Three months (Oct 2025, Dec 2025, Jan 2026) hold 79% of the year's total.
- These are the two plants whose highest offer price is above $0.01: Kaiwera Downs $1.60 since FY2025; Turitea
  $0.01 in every year to FY2025 and **$0.02 in 96% of FY2026 half-hours**. Its price-driven energy went from 3.9 GWh
  (FY2025) to 53.7 GWh (FY2026); Kaiwera Downs from 7.2 to 25.4 GWh. When all wind offers $0.01, SPD spreads
  dispatch-down across plants and the per-plant gap stays under each plant's detection floor; once one plant offers
  $0.02 it takes the whole of the dispatch-down first, and its gap clears the floor. The measure therefore detects
  concentrated dispatch-down and not thinly spread dispatch-down, so part of the 0.77% to 2.22% rise can be a change
  in who is marginal rather than in how much is spilled. The report's leave-one-out covers only the preregistered
  measure (3.80% without Turitea) and says nothing about the price-driven series.
- The report's "In half-hours where the price was at or below the plant's offer, 18% were flagged" is a fleet
  average dominated by the same two plants (Kaiwera Downs 21.5% of its half-hours at or below its offer, Turitea 8.7%).

Fix: add a per-plant table and the leave-one-out for the price-driven series; state the offer-price change at
Turitea and the $1.60 offers at Kaiwera Downs; say in the summary and plain terms that the 2.2% is dominated by two
plants and that the measure cannot see dispatch-down spread evenly over $0.01 plants.

### 3. Major: the potential is not a dispatch-time forecast for a large part of the panel, and the report's description of it and of the solar floors is wrong

Evidence (check1 and check6 outputs; `lead_times.parquet`; `report.md` "Potential is the plant's latest
dispatch-time forecast", "Solar plants sit higher, partly because their mean potential includes nights"):

- Lead of the highest-SubmissionOrder potential before the trading period starts, all days, all units: FY2020-FY2025
  median 8 minutes with 0% submitted after the start; **FY2026 median 1.9 minutes with 47% submitted after the period
  had started** (Meridian and Mercury wind units at -11.6 minutes, Tararua units at -1.2 minutes). Turitea and
  Kaiwera Downs, the two plants of finding 2, are the only large wind plants whose potential remained a pre-period
  submission (about +2 minutes) in FY2026. The 2020 and 2025/26 series are thus compared across a change in what
  the potential is.
- Solar plants' potentials are submitted days ahead and not refreshed: median lead 3,900-8,700 minutes at KOE1101,
  WAI0331, ASB0661 (FY2025), EDG0331; 47-69% of their half-hours use a potential more than a day old. Their floors
  are high for that reason, not mainly because of nights: on daytime half-hours alone the floor is still 42-45% of
  mean potential at ASB0661, EDG0331, KOE1101 and WAI0331 (check8), far above the 25% gate.
- A share of wind half-hours also carry stale potentials (over 2 hours old: 6-19% in FY2020-FY2025, 27% in FY2026;
  WWD1103 on 2024-04-15 used a week-old value all day).

Fix: report the lead-time distribution (reviewer's `lead_times.parquet` can be regenerated with check6); describe
the potential as "the last potential on file for the period", not a dispatch-time forecast; either restrict the
measure to potentials submitted within a fixed window before the period (and say what that removes) or carry the
timing regime as a stated limitation of the 2020 versus 2025/26 comparison; correct the solar sentence in the report
and in `F2_gate.txt`.

### 4. Moderate: the frozen projection is not the plan's quantity

Evidence (check5 output; `code/analysis.py:184-205`; `plan.md` section 4):

- Four plants commissioned by 30 September 2026 enter with **zero** projected available energy because their
  metered output is zero or near zero in the panel (k = 0 makes P_hat = 0): Clandeboye TMK0331 (solar; this review
  first misnamed it Tauhei, corrected in the confirmation pass: Tauhei is WHU1101, which is metered), Kaiwaikawe
  MPE1101 (wind), Kōwhai Park ISL0661 and Pāmu Rā ki Whitianga KPU0661. Kaiwera Downs 2 KIW2201 is
  annualised from six months (April to September 2026) that include its commissioning ramp. The projected available
  energy (4,534 GWh) is therefore not "available energy projected from units commissioned by 30 September 2026".
- The projected share (5.65%) is the noise-dominated measure; the report says as much, but the plan's rule is still
  applied to a quantity the report itself calls unmeasurable, and the price-driven component is not projected.

The rule is reproducible, so the number is scoreable, but when it is scored in July 2027 those four plants will have
metering and the denominator will differ from the projection by design. Fix: project available energy for unmetered
plants from their offered potential (k = 1) or their nameplate and a stated capacity factor, state the exclusions in
the report, and either project the price-driven component under the same rule or say explicitly that only the
preregistered measure is frozen.

### 5. Moderate: the report's statement that `MaximumOutputMegawatts` is empty is false, and the variant never could run

Evidence (`code/build.py:31-33` keeps the column in the filtered offers; `build.py:63-66` does not carry it into
the panel; `code/analysis.py:146` tests `"MaximumOutputMegawatts" in d`, which is always False; check1 column
`maxout_filled`; check3 raw rows): the field is populated in 2020 and from October 2025 (Turitea 222 MW, Tararua
35 MW, Mahinerangi 36 MW on 2025-10-15) and empty in FY2022 to January 2025. It is a capacity figure, so the
planned variant would be uninformative, but the report says "is empty for these plants, so that variant cannot be
run", which is not what happened. Fix: say that the column is a nameplate value, populated only in some years, and
that the variant was not run for that reason.

### 6. Moderate: 163,282 panel rows (9%) are dropped silently for missing metered output, and only two of the nine cases are disclosed

Evidence (check2 a; `code/analysis.py:31`; `results/tables/build_log.json` `rows_missing_output`): besides
Mahinerangi (121,584 rows) and Rotohiko (18,212), the drop removes Lauriston solar at ASB0661 for 12,386 half-hours
(16 October 2024 to 30 June 2025; Generation_MD lists only Highbank hydro at that POC then), KOE1101 for October to
December 2023, GOR0331 for August 2023, WIL0331 for October to December 2019, TMK0331 for June to August 2026 and
small gaps at DVK0111 and WVY1101. The plan promised that "units that cannot be matched are listed". Fix: list these
in `build_log.json` and the report, and check whether Lauriston's output before July 2025 was metered under another
fuel or generator code.

### 7. Minor: the block bootstrap relabels resampled days to the original calendar positions, so each resample's calibration quarters mix days from different seasons

Evidence (`code/analysis.py:93-96`: `assign(date=pd.Timestamp(days[i]))` then quarter and year recomputed from the
new date; check4): in a 2025/26 resample, 84% of rows are calibrated in a quarter other than their own. The
point estimate uses true quarters, the intervals a different estimator. With 150 resamples each, the study's
relabelling gives 2020 [2.10, 2.40]% and 2025/26 [4.45, 6.07]%; keeping each day's true quarter gives [2.09, 2.40]%
and [4.34, 5.91]%, so the effect is small and no verdict changes. Fix: keep each resampled day's own quarter and
year labels, or state the relabelling.

### 8. Minor: calibration pooling departs from the plan in two small ways

Evidence (`code/analysis.py:44-57`): k pools to the plant-year when fewer than 200 "big" unconstrained half-hours
(potential at least 10% of capacity) exist, while the plan's rule is 200 unconstrained half-hours; and when the
plant-year is also thin, k is set to 1 and f stays NaN, so the plant-quarter can never be flagged but its full
potential counts in available energy (KPU0661 in 2025/26, gate NaN). Also the gate takes the row-weighted median of
four quarterly floors, which is a reasonable reading of "the median unit's detection floor" but should be stated.
Fix: say so in the report; the effect on the headline numbers is negligible (check2 e: gate 0.271 under every
variant tried, 0.269 wind only).

### 9. Minor: windows and baseline

The first 12-month window is 18 months (January 2020 to June 2021, `diagnostics.py:52`); the report labels it, but
the calendar-2020 price-driven share (0.017%, check2 g) is the like-for-like baseline and should replace it in the
window table. The 2020 flag rate of 5.0% and 2025/26 of 4.7% in unconstrained half-hours, and the 2.2% noise mass
in both periods, are confirmed; the 2020 baseline of 2.27% is an artefact of the rule and H1's refutation is a
property of the measure, as the report says. Leading with the gate is what the plan prescribes and is fair.

### 10. Confirmations (no action)

- Potential-decile-matched floor (within plant-quarter, 95th percentile of unconstrained gaps in the same decile of
  P_hat, check2 d): noise mass falls from 2.17% to 1.61%, "other" from 0.79% to 0.58%, price-driven from 2.22% to
  2.17% with a matched-floor flag rate of 18.6%. The heteroscedasticity threat does not undo the dispatch-down
  signal. Worth adding to the robustness table.
- Matching: every wind and solar POC in Generation_MD has offers (`generation_pocs_without_offers` empty), monthly
  matched output equals the fuel total, and the output/potential ratios in `build_log.json` are 0.98-1.03 for the
  established wind plants. Mahinerangi's exclusion is right (no wind generator at HWB0331; its output is inside the
  Waipori hydro metering). Rotohiko is a battery. Both fuel codings are read (`build.py:27`).
- Stale potentials: on 2022-01-15 a Tararua unit's latest rows span two submissions, the earlier carrying a stale
  6.8 MW against the later 17.8 MW; taking the highest SubmissionOrder is right, and the zero-MW stale tranches do
  not affect `offered`.
- Spells: the ledger's largest price-driven months are January 2026 (30.0 GWh), October 2025 (22.8), December 2025
  (20.1), September 2022 (15.4) and September 2024 (10.5), so "spells, with big ones in 2022 and late 2025" is
  supported. The report makes no hydrology claim.
- H1 and H2 rule logic (`analysis.py:116-124`) matches the plan; every number in the report's tables matches
  `primary.json`, `robustness.json` and `diagnostics.json` (checked individually).
- December 2025 prices assembled from daily files have the same rows per day as November (11,664).

## Summary of required edits before publication

1. Headline, summary, title and plain terms: present the non-noise split under the plan's $0.01 line and the post
   hoc own-offer line; rename the class; remove "reverses H2's reading" as a conclusion; attribute the 2.2% to two
   plants and to the merit-order position that their offer prices give them.
2. Add per-plant and leave-one-out tables for the price-driven series and the offer-price history of Turitea and
   Kaiwera Downs.
3. Report the lead-time distribution of the potential; correct "dispatch-time" and the solar "nights" sentence.
4. Re-freeze the projection with the four unmetered plants included by a stated rule.
5. Correct the `MaximumOutputMegawatts` sentence; list the dropped plant-periods.

## Confirmation pass

Reviewer: Claude (Fable 5.1), 2026-10-22, on commits 2c2a8b1 and f603d05. Check: `reviewer_checks/check9_confirmation.py`
(.out). `code/sensitivity_post_review.py` is tracked in git; `results/tables/sensitivity_post_review.json` is its
output; D3 is logged in `deviations.md` with dollar amounts restored.

**Verdict: publish with edits** (two wording fixes, one of them a plant name; no number changes).

Verified against `sensitivity_post_review.json`: non-noise split 46.9% / 73.1% / 94.9% (report gives the complements
53% / 27% / 5%); dispatched-down series by window and "without the two largest" (0.011/0.004, 0.233/0.064,
1.102/0.892, 0.070/0.030, 0.766/0.454, 2.215/0.412%), top-two names per window, Turitea 53.72 and Kaiwera Downs
25.44 GWh (86%); offer prices (Turitea $0.01 to $0.02 in FY2026, Kaiwera Downs $1.60 from FY2025); FY2026 wind
lead times (median -1.2 to -11.6 min, 76.2-89.1% after the start; Turitea 7%, Kaiwera Downs 0.1%, Waipipi 0.7%);
solar median leads 1.74-6.39 days; MaximumOutputMegawatts populated share by FY (1.0, 0.346, 0, 0, 0, 0.358, 1.0);
dropped rows by plant and month; projection variant 5.925% beside the rule's 5.65%; bootstrap and pooling notes;
calendar-2020 dispatched-down 0.02%. Title, verdict line, plain terms, F2 and F3 captions and report.html match. Edits
1-5 of the original review are implemented.

Remaining edits:

1. **Plant name in the projection paragraph.** The four unmetered plants are Clandeboye (TMK0331), Kaiwaikawe,
   Kōwhai Park and Pāmu Rā; the report says "Tauhei". Tauhei is WHU1101 (Generation_MD `tauhei_solar_farm`, NSP
   table "Tauhei Solar Farm"), is metered (k = 1.0) and is already in the projection (annualised from five months).
   The report's own dropped-rows list has TMK0331 as Clandeboye. The misnaming originated in this review's finding 4,
   now corrected above.
2. **The summary's comparison.** "Without them the rest of the fleet shows 0.4% in 2025/26, below the 0.9% of
   2022/23": the 0.9% is 2022/23 without *that* window's two largest (Waipipi, Te Āpiti), not without Turitea and
   Kaiwera Downs. Say "the fleet without its two largest contributors showed 0.9% in 2022/23", as the table does.
3. **Optional, supports the text.** The claim that post-period potentials "can absorb a turn-down and hide it" is
   stated without evidence in the report. check9 gives some: among half-hours at or below the plant's own offer, the
   flag rate fell from FY2025 to FY2026 at every wind farm that moved to post-period submission (White Hill 0.36 to
   0.06, Tararua 3 0.20 to 0.03, Harapaki 0.24 to 0.12, Te Āpiti 0.13 to 0.04, West Wind 0.20 to 0.09) and rose at
   the two pre-period plants (Turitea 0.29 to 0.71, Kaiwera Downs 0.47 to 0.55); but it also fell at Waipipi (0.50
   to 0.28), which still submits beforehand, so the mechanism is plausible, not shown. Cite the table, or keep the
   hedge ("can").
4. **Optional.** "The only plants that offer above $0.01/MWh" holds at the median; Kaiwera Downs stage 2 (KIW2201)
   offers above $0.01 in about 14% of its half-hours.
