# Independent review: movement-nz-ev-policy-discount-vs-ruc (draft commit 60012cc)

Reviewer: adversarial reviewer agent, 2026-10-21. Scripts and raw outputs are in `review/reviewer_checks/`
(`verify_counts.py/.out`, `verify_categories.py/.out`, `attrition_snapshots.py/.out`, `reanalysis.py/.out`,
`preprint_excerpts.txt`). All service queries were aggregation queries against `MVR_Mar26`; one older NZTA snapshot
(`MVR_May23`, an ArcGIS Online CSV item) was downloaded once for the attrition check.

## Verdict: **fix first**

The two preregistered verdicts (H1 Inconclusive, H2 Inconclusive) are correct and reproduce exactly, the counts are
right, and the bootstrap is adequate. The report cannot be published as written because several headline and
framing claims are wrong or overstated, and two of them rest on a false scope limitation:

- The prior preprint was retrievable in full (open-access PDF, found in under a minute via OpenAlex). It **does**
  quantify pull-forward (1,206 vehicles in the final eight weeks), its data end in **December 2025**, and it never
  mentions road user charges. The report's novelty claim, its "only its title could be retrieved" statement and its
  rebuttal of the preprint's "lasting" finding all need rewriting (findings 1, 2).
- "Pull-forward accounts for about a tenth" is presented as a plain fact; across defensible baselines the share is a
  tenth to nearly a half, and the preregistered specification is the most aggressive extrapolation (finding 3).
- The H2 difference-in-differences is confounded by rebound from the January 2024 trough, its placebos are not
  "dates with no policy change", and its control group acquires a new product category inside the post window
  (findings 4-6).
- The "light vehicle" universe contains ~37,000 vehicles over 3,500 kg GVM, and the ute figures are truck-inclusive
  (finding 7). Three preregistered analyses were not run (finding 9).

None of this changes an Inconclusive into something else, which is why this is "fix first" rather than "do not
publish": the edits are to text, framing and a few added numbers, not to the design.

## Findings

### 1. Major — the prior preprint was retrievable and contradicts the novelty claim

**Evidence.** `plan.md:13-18`, `deviations.md:18-20`, `report.md:71-75` say the full text "could not be retrieved",
only the title was available, and that the preprint "does not quantify pull-forward"; `report.md:74-75` concludes
"No study ... quantifying the December 2023 pull-forward, was found". OpenAlex (W7213895029) lists the preprint as
open access at `https://www.researchsquare.com/article/rs-11080967/latest.pdf`; `curl` fetched the 39-page PDF
directly (the HTML landing page is JavaScript-rendered and shows only the title, which is presumably what the study's
fetch saw). From the abstract (`reviewer_checks/preprint_excerpts.txt`): "Anticipation bunching analysis documents
1,206 vehicles brought forward in the final eight weeks, equivalent to 3.7 weeks of average demand." Section 4.3 and
Table 5 give the same figure (28.8% above trend). Data: "weekly vehicle registration records from the New Zealand
Motor Vehicle Register, spanning December 2021 to December 2025". A grep for road user / RUC / April 2024 finds
nothing: the preprint does not separate E2 from E1.

**Why it matters.** The study's genuine contribution (separating E2 from E1 using hybrids) survives, but the
pull-forward measurement is not novel, and the preprint's 1,206 excess vehicles is a directly comparable number to
the study's December excess (951 preregistered; 1,400-2,600 under other baselines, see finding 3). A silently
failed fetch produced a false scope limitation that then propagated into the plan, D1 and the report.

**Fix.** Replace the "only its title" statements with what the preprint actually reports (data window, outcome,
pull-forward figure, no RUC treatment). Drop the claim of priority on pull-forward; compare the two pull-forward
estimates instead. Record in deviations.md that the full text was retrieved at review.

### 2. Major — "It did not last" misrepresents both the preprint and the study's own data

**Evidence.** `report.md:25-27` and `:44`: "It did not last ... A 2026 preprint describes the fall as 'lasting'; on
data running 2.5 years past the change, it was not." The preprint's "permanent over 24 months" is a claim about
January 2024 to December 2025. Over exactly that window the study's own series agree with it
(`reanalysis.out`, "Recovery / share claims"): mean plug-in share Jan 2024-Dec 2025 was **6.6%** against 13.4% in
Jan-Nov 2023; 2025 full-year share 7.7%, BEV share 4.3% (2023: 9.9%). The recovery begins in **March 2026**
(plug-in share 9.5% in February, 19.6% in March), outside the preprint's data. Secondary sources attribute the March
2026 jump to a fuel-price spike after Middle East supply disruptions (Kiwibank "chart of the week", found by web
search; not independently verified here), i.e. an exogenous shock, not a reversal of the policy effect.

Also: `report.md:25` says "By mid-2026 the plug-in share is back to 18-22%". The April-September 2026 monthly range is
**13.7-21.7%** (mean 17.5%); August 2026 was 13.7%. And `report.md:26` compares nine months of 2026 (29,402) with
twelve of 2023 (37,581), which is not a like-for-like comparison; Jan-Sep 2023 was 23,293, so Jan-Sep 2026 is 26%
higher, which is the cleaner statement.

**Fix.** Rewrite as: the fall persisted through 2025, consistent with the preprint; from March 2026 plug-in
registrations and share rose back above 2023 levels (Jan-Sep 2026 29,402 vs Jan-Sep 2023 23,293; share 15.9% vs
12.3%), coinciding with a fuel-price shock the preprint could not observe. Correct "18-22%" to "14-22%" or give the
mean. Do not present this as a refutation of the preprint.

### 3. Major — "about a tenth" is stated as fact; defensible baselines give a tenth to nearly a half

**Evidence.** `report.md:24` ("Pull-forward accounts for about a tenth of it"), `:43-44`, `:118`, `:159`, and the F2
title "Pull-forward explains little of the collapse (ratio 0.09)" (`code/figures.py:88`). `reanalysis.out`, "H1: R
under alternative baselines":

| baseline (treated = BEV+PHEV) | E | M | R | predicted Q1 2024 / month |
|---|---|---|---|---|
| log-linear, 2021-01..2023-09 (preregistered) | 951 | 10,578 | **0.09** | 4,291 |
| Poisson, same window | 1,521 | 9,115 | 0.17 | 3,804 |
| level-linear, same window | 2,399 | 7,746 | 0.31 | 3,347 |
| log-linear, 2022-01..2023-09 (prereg sensitivity) | 2,456 | 5,614 | 0.44 | 2,637 |
| level-linear, 2022-01..2023-09 | 2,620 | 5,727 | 0.46 | 2,674 |
| local level anchored on Oct-Nov 2023, fitted month effects, no trend | 1,721 | 7,520 | 0.23 | 3,272 |
| same, with fitted trend | 1,412 | 9,397 | 0.15 | 3,898 |
| new vehicles only, log-linear (plan s5.1) | -664 | 9,929 | -0.07 | 3,886 |
| new vehicles only, level-linear | 1,288 | 6,650 | 0.19 | 2,793 |

The preregistered log-linear fit extrapolates exponential growth and predicts 4,291 plug-ins a month for Q1 2024,
above the October-November 2023 actuals (3,708 and 4,604 averaged 4,156); it is the most aggressive counterfactual
on the table and therefore gives the smallest R. The 2022-window fit does the opposite (predicts 2,637 a month, well
below the Oct-Nov actuals) and gives 0.44. The honest range is roughly 0.1-0.45.

What the report *can* say, and does not: R >= 0.5 requires a flat counterfactual at or below **2,850 vehicles a
month** (break-even in `reanalysis.out`), against 4,156 actually registered in October-November 2023. That is the
substantive reason the evidence "leans against" H1, and it is stronger than the point estimate. The bootstrap
agrees: P(R >= 0.5) is 13% under the study's scheme and 9-16% under the alternatives.

**Fix.** In the summary, plain-terms section, H1 heading and the F2 title, replace "about a tenth" with "between a
tenth and a half depending on the baseline; no baseline reaches half, and a counterfactual low enough to reach half
would sit below the October-November 2023 registrations". Report the alternative-baseline table (or at least the
level and Poisson variants) and the new-vehicles-only result, which the plan promised (s5.1). Keep "leans against"
only if it is justified by the break-even argument, and keep it out of the plain-terms section, where the verdict
should be stated as Inconclusive first.

### 4. Major — the H2 difference-in-differences is confounded by rebound from the January trough

**Evidence.** The pre-window (Jan-Mar 2024) is the immediate aftermath of an 81% shock. Inside it the treated series
runs 590 -> 752 -> 954, a log slope of **+0.24 per month**, while hybrids run 6,122 -> 5,835 -> 6,800 (+0.05 per
month) (`reanalysis.out`, "H2: components"). Parallel trends fail on their face: any partial mean reversion from the
trough (dealers clearing stock, prices adjusting, deferred buyers returning) appears as a positive DiD. Treated rose
35% from pre to post window; hybrids 3%. The +32% is therefore not "the wrong sign for a deterrent" that needs
explaining (`report.md:16, :141`); it is the sign the confound predicts, and it says nothing about the RUC effect's
sign or size. The dose check points the same way: BEVs (full RUC) moved **+33% relative to PHEVs** (half-rate RUC),
the reverse of a deterrent, and BEVs had the deeper January trough. Longer post windows make the DiD larger, not
smaller (+42% to May-Dec 2024, +49% to Mar 2025, +54% to Sep 2025), again consistent with recovery dynamics.

The placebo-in-time distribution (`reanalysis.out`): the identical 3-skip-6 statistic computed at every feasible date
outside Oct 2023-Oct 2024 (n = 38) has mean +0.17, SD **0.38**, and **18 of 38** placebos exceed the real estimate in
absolute value (14 exceed it in the same direction). The statistic mostly measures the relative trend of a fast-growing
series against a slow one, in whichever direction it happens to be running.

**Fix.** State plainly that the design cannot identify delta_RUC because the pre-period is a transient, that the
positive sign is expected under rebound, and that Q is uninterpretable when |delta_RUC| is dominated by that
confound. Report the placebo-in-time distribution alongside the four April placebos. Keep the Inconclusive verdict,
but change the framing from "underpowered" to "underpowered *and* confounded".

### 5. Moderate — the placebos are not "dates with no policy change"

**Evidence.** `report.md:53`, `code/figures.py:123` and the F3 caption describe the placebo years as having "no
policy change". The Clean Car Discount's full scheme (fees on high emitters; rebates extended beyond BEV/PHEV,
including to many hybrids) began on **1 April 2022**, which is the 2022 placebo date itself; the 1 July 2023 rebate
and fee changes sit inside the 2023 post window. The preprint confirms both dates (preprint line 514: "introduction
of the Clean Car Discount (CCD) on 1 April 2022, a rebate reduction on 1 July 2023"). The register shows them:
hybrids 2,273 -> 5,078 and ICE 38,394 -> 8,535 across March/April 2022; plug-ins 4,419 -> 1,616 and hybrids
10,575 -> 4,746 across June/July 2023 (`reanalysis.out`, "policy events inside placebo windows"). The 2026 placebo
(+43%) straddles the March 2026 demand jump noted in finding 2. Only 2025 is clean.

**Fix.** Drop "no policy change"; label the 2022 and 2023 placebos as contaminated by Clean Car Discount phases and
say so in the F3 caption. The point that the design is uninformative is better made with the placebo-in-time
distribution (finding 4).

### 6. Moderate — the hybrid control acquires a new product category inside the post window

**Evidence.** `verify_categories.out`: `DIESEL HYBRID` is 26, 25 and 184 vehicles in 2021-2023, then 4,172 in 2024
and 6,771 in 2025; it is almost entirely new Toyota Hilux (12,318) and Land Cruiser (3,251) 48-volt mild hybrids,
`GOODS VAN/TRUCK/UTILITY`, appearing from February 2024 (62) and running 409-567 a month from May 2024. In the
control these are 14/66/69 in Jan-Mar 2024 and ~450 a month in May-Oct 2024. Excluding them moves the DiD from
+32% to **+41%** (prereg window), i.e. the control's post-period level is propped up by a product launch that has
nothing to do with road user charges, and a mild-hybrid ute is not a substitute for a plug-in car.

**Fix.** Report the DiD with and without `DIESEL HYBRID`, and note the composition change under "Threats". Consider
whether the control should be petrol hybrids only.

### 7. Moderate — the "light vehicle" universe includes ~37,000 heavy vehicles; the ute numbers are truck-inclusive

**Evidence.** `verify_counts.out` (c): the two `VEHICLE_TYPE` values selected (`plan.md:36`, `report.md:81-82`)
contain 37,317 vehicles with `GROSS_VEHICLE_MASS` > 3,500 kg in 2021-2026, 36,295 of them diesel; they are 13.6-20.6%
of the diesel `GOODS VAN/TRUCK/UTILITY` series each year. The "1,419,410 light-vehicle first registrations" figure
(`report.md:82`, `deviations.md:10`) is therefore ~2.6% heavy. The effect on the plug-in and hybrid series is
negligible (337 heavy BEVs, 157 heavy PHEVs, 301 heavy diesel hybrids over six years), so H1/H2 are unaffected, but
the "diesel utility" series (`report.md:29, :152`) is not what it says. Restricted to <= 3,500 kg the trough and
rebound are *sharper*: 2,092 and 2,005 in Oct-Nov 2023, **515** in December, **3,649** in January
(`verify_counts.out` c2). The truck component barely moved, which dilutes the study's series. Consequently the
plain-terms line "fell to a quarter of normal" (`report.md:48`) is wrong on the report's own numbers (988/2,696 =
37%) but right on the light-only numbers (515/2,050 = 25%).

**Fix.** Either add `GROSS_VEHICLE_MASS <= 3500` to the universe (one re-fetch; H1/H2 will move by less than
rounding) or call the universe "passenger cars, vans and goods vehicles" and give the light-only ute numbers. Make
the plain-terms fraction consistent with whichever series is shown. The ute pattern itself is real and repeats at
the other two fee dates (9,793 -> 1,219 across March/April 2022; 6,203 -> 1,541 across June/July 2023), which the
report could use to strengthen the descriptive point.

### 8. Moderate — the share collapse is quoted peak-to-trough with mix effects at both ends

**Evidence.** `report.md:22` ("27.3% in December 2023 to 2.8% in January 2024, a 24.5 percentage-point drop"). The
December denominator is depressed by ICE buyers deferring past the fee's end (ICE 10,337 in November, 5,499 in
December, 14,489 in January), which inflates December's share and deflates January's. The report's own defence
("total light registrations barely moved", `report.md:111`) misses this: the total is stable because the two
deferrals offset. November to February is 19.5% -> 4.1% (BEV share 13.4% -> 2.7%), still an enormous fall but not
24.5 points. The 24.5 pp figure also invites an unwarranted equation with the preprint's 24.1 pp, which is BEV share,
a different outcome.

**Fix.** Give both comparisons and say why they differ; do not juxtapose 24.5 pp with the preprint's 24.1 pp
without saying the outcomes differ.

### 9. Moderate — preregistered analyses not delivered

- `plan.md` s5.1: "H1 is repeated on new vehicles only, where scrappage over this window is minimal" — not in the
  report. Result (finding 3): R = -0.07 (log-linear), 0.02 (Poisson), 0.19 (level).
- `plan.md` s4: "Market share as an alternative outcome to counts" — not reported for H2. In logs the share DiD is
  identical to the count DiD by construction (the total cancels), which the report should say; in percentage points
  it is **-1.7 pp** (treated share 3.9 -> 5.6, hybrid share 31.5 -> 35.0), the opposite sign (`reanalysis.out`).
- `plan.md` s5.5: "The minimum detectable effect for delta_RUC and for R is computed from the bootstrap and reported
  whatever the verdicts" — only the delta_RUC MDE appears (`report.md:16`). The bootstrap SE of R is 0.36
  (`primary.json`), so the MDE for R is about 1.0, i.e. the H1 test could only ever have "Supported" a pull-forward
  that exceeded the entire shortfall; this should be stated, since it explains the Inconclusive.
- `plan.md` s4 "Persistence: the treated-minus-control gap through September 2026" is only narrated.

**Fix.** Add the three missing results; one paragraph each.

### 10. Minor — snapshot attrition (quantified; the report's qualitative statement is right and can now cite numbers)

**Evidence.** `attrition_snapshots.out`: between the May 2023 snapshot (data to 30 April 2023) and the October 2026
load, survivors are 95.1% of 2021 registrations, 95.9% of 2022, 96.2% of Jan-Apr 2023, a gradient of about one point
per registration year. Plug-ins survive at 97-99%, new vehicles ~99%, used imports 89-93%; hybrids 93-96% (the
used-import share). Month-to-month differences are < 1 pp, so attrition cannot generate the December 2023 spike
(+30% on November) or the 2026 recovery (a doubling), and it understates the 2023 plug-in totals by at most ~2%
relative to 2026. April 2023 was complete in the May 2023 snapshot (ratio 0.963, in line with neighbours), which
supports treating September 2026 as complete in a 6 October 2026 load (`MVR_Mar26` editingInfo dataLastEditDate
2026-10-06; September 2026 is the year's largest month at 25,063). The brief's `MVR_April2021` service does not exist
under this org; `MVR_May23` is the oldest NZTA snapshot I could find.

**Fix.** Cite these figures in "What this does and does not show" instead of "slightly down". Note that the register
service is a 6 October 2026 load, which is why a service named `MVR_Mar26` runs to September 2026; and note that D1
item 1 is not a deviation at all, because `plan.md:6-7` already recorded that the snapshot runs through September
2026 and `plan.md` s2 already specified "January 2021 to September 2026".

### 11. Minor — motive-power groupings (checked; two notes)

`PETROL ELECTRIC HYBRID` (11,188 vehicles) is Nissan e-Power (Note, X-Trail, Qashqai, Serena): series hybrids with no
plug, correctly in the control. `ELECTRIC [PETROL EXTENDED]` (495; Leapmotor C10/B10 range-extended EVs in
2025-26, BMW i3 REx earlier) is a plug-in, correctly treated; for road user charges it is a plug-in hybrid (reduced
rate), so it belongs in PHEV rather than BEV, but the counts are too small to matter. `RE-REG` import status is
counted as "new" by `analysis.py:63`; immaterial. No category is ungrouped. The counts themselves match the service
cell for cell in all six months re-queried (`verify_counts.out`: 0 mismatches), and the rebuilt series matches
`monthly.csv` exactly.

### 12. Minor — the bootstrap (adequate; small notes)

The study's scheme reproduces exactly from the seed (R CI [-0.40, 1.07]; delta_RUC CI; Q CI [0.01, 0.53]), and
**no draw is dropped** for M <= 0, so the ratio's denominator is not a problem in this dataset. Alternatives give the
same picture: pre-period-only residuals, leverage-inflated (SD 0.317 -> 0.408 for 13 parameters on 33 months), with
circular blocks of 1, 3, 6 or 12 months give R CIs of [-0.41, 1.10] to [-0.43, 1.22], delta_RUC CIs of roughly
[-30%, +150%] and Q CIs of [0.01, 0.48-0.52]; P(R >= 0.5) is 9-16% throughout. Two quirks worth a sentence in the
report: the December 2023 residual is identically zero under the "window's own mean" construction (a one-month
window), and the pre-period residuals are not leverage-corrected, which the larger post-window residuals (SD 0.43)
happen to offset. Residual autocorrelation is low (lag-1 -0.02, lag-2 0.36), so a three-month block is reasonable.
The last residual can never be drawn (`analysis.py:132` upper bound), which is immaterial.

### 13. Minor — numbers and wording

- `report.md:15, :134`: the lower CI for delta_RUC is exp(-0.4373) - 1 = **-35.4%**, printed as -36%.
- `report.md:9`: "the evidence leans against it" immediately after "Inconclusive" is editorialising unless the
  break-even argument (finding 3) is given; in the plain-terms section the verdict should come first and the
  "tenth" claim should carry its range.
- `report.md:7`: the headline "Inconclusive on both preregistered tests, with clear descriptive findings behind them"
  is honest, and the "whatever the formal tests return" section (`report.md:19`) is where the overstatements live;
  tightening findings 2, 3 and 8 fixes it.
- `report.html` mirrors `report.md` (same numbers and phrases; only differences are its own 2%/8/97% layout values).

## What checked out

- **Counts.** Six months re-queried cell by cell (2023-11, 2023-12, 2024-01, 2024-04, 2026-03, 2026-09): identical
  to `data/registrations.csv`; rebuilt monthly series identical to `results/tables/monthly.csv`; total 1,419,410.
- **Report numbers against the tables.** Every figure in the results tables, the H1/H2 numbers, the share table, the
  annual totals and the ute numbers match `primary.json`/`monthly.csv` (apart from the -36% rounding and the
  "18-22%" range above).
- **Preregistration order.** `plan.md` + `fetch.py` committed 21:26:35 NZDT (5d01d6f); raw JSON written 21:27-21:28;
  `analysis.py` committed 21:30:26 (2693931) before `results/tables` (mtime 21:32); the later change to
  `analysis.py` (f343551) only appended the preregistered sensitivities and the ute series. Data and logs are
  gitignored by lab policy, so the plan-before-data check rests on file mtimes, which are consistent.
- **Verdict mechanics.** Both decision rules applied as preregistered; both Inconclusive; the (E - 0.5M) difference
  test gives the same answer as the ratio rule.
- **Completeness of September 2026** and the snapshot date (finding 10).

## Suggested order of edits

1. Findings 1 and 2 (preprint; "did not last"): rewrite the summary bullets, plain-terms paragraph, "What was already
   known", D1 item 3.
2. Finding 3: replace "a tenth" with the range and the break-even argument; add the alternative-baseline table and the
   new-only H1; fix the F2 title.
3. Findings 4-6: reframe H2 as confounded as well as underpowered; add the placebo-in-time distribution and the
   control-without-diesel-hybrids estimate; relabel the placebos.
4. Findings 7-9, 13: universe/ute numbers, the share comparison, the missing preregistered results, -35%.

## Confirmation pass (revision 9552d6d, 2026-10-21)

**Verdict: publish with edits** — four small text/figure fixes below, none needing a further review round. Every
number in the revised report.md was checked against `reviewer_checks/*.out` or recomputed; all match. Findings 1-13 are
resolved as described in the coordinator's message, with the residuals noted here. report.html mirrors report.md.

### Resolved

1-2 (preprint, "did not last"): the prior-work section, summary bullets and D2 now state the preprint's window
(Dec 2021-Dec 2025), its pull-forward figure (1,206) and its silence on RUC; "did not last" is replaced by "lasted
about two years" with the 6.6% vs 13.4% comparison, the 13.7-21.7% range and the like-for-like 29,402 vs 23,293.
Correct. Not attributing the 2026 recovery is the right call.
3 (H1): the baseline table (0.09-0.46, local-level 0.15-0.23, new-only -0.07 to 0.19) matches `reanalysis.out`;
break-even 2,850 vs 4,156, MDE ~1.0 (2.8 x 0.359), P(R >= 0.5) 9-16% all correct. "Leaning against" now rests on the
break-even, as recommended.
4-6 (H2): slopes +0.24/+0.05, BEV vs PHEV +33%, +42% to +54%, 38 placebos / SD 0.38 / 18 of 38, diesel-hybrid
+41%, share -1.7 pp, lower CI -35%: all correct. The placebo text now names 1 April 2022 and 1 July 2023.
7 (utes): 515 and 3,649 are the light-only (<= 3,500 kg) figures; "a quarter of their October-November level" is now
right (515 / 2,048 = 25%). The new claim at report.md:37 that the pattern recurs at the other fee dates was only
verified on the truck-inclusive series in my first pass; I re-queried the light-only series
(`reviewer_checks/raw/c3_light_ute_other_fee_dates.json`): March/April 2022 **9,049 -> 662**, June/July 2023
**5,488 -> 948**. Confirmed, and sharper than the truck-inclusive numbers.
8 (shares): Nov->Feb 19.5% -> 4.1% is given with the mechanism; the "one in five to one in twenty-five" plain-terms
version is accurate.
9 (omitted preregistered analyses): new-only H1, market-share H2 and the H1 MDE are now reported.
10 (attrition, D1 item 1): figures match `attrition_snapshots.out`; D1 item 1 is recorded as not a deviation.

### Residual issues (fix before publishing)

**C1. The preprint is not restricted to new vehicles, and it includes PHEVs** (report.md:75 "weekly *new*
registrations"; :81-83 "What this study adds: ... first registrations including used imports, and plug-in hybrids
alongside battery-electric vehicles"; D2 item 1 "weekly new registrations"). The preprint's "new registrations" means
newly registered vehicles: it aggregates "by fuel type (BEV, PHEV, HEV, ICEV), import status (new vs. used)"
(preprint line 410), reports new-versus-used heterogeneity (section 5.1, Table 9, Figure 6: used BEV share +0.8 pp,
n.s.; used BEV count -152/week) and PHEV effects (Table 13: PHEV -234.5/week). So two of the three claimed
additions are not additions. What this study genuinely adds: the RUC separation; a combined BEV+PHEV treated group
and monthly first registrations in a passenger-plus-goods universe; data to September 2026. **Fix:** delete "*new*"
(say "weekly first registrations, new and used"), and reword the additions paragraph and D2 item 1 accordingly.

**C2. The figures were not regenerated.** `code/figures.py:88` still titles F2 "Pull-forward explains little of the
collapse (ratio 0.09)", presenting the lower end of the range as the headline, and `code/figures.py:123` /
`results/figures/F3_ruc_did.txt` still say the placebo years are "dates with no policy change", which report.md:146-147
now contradicts (the phrase survives once in report.html via the caption). F1's caption still says "light vehicles".
**Fix:** retitle F2 (e.g. "Pull-forward explains a tenth to under half of the collapse, by baseline"), rewrite the F3
caption ("placebo dates; 2022 and 2023 coincide with Clean Car Discount changes"), rerun `figures.py` and
`build_report_html.py`.

**C3. "A study published in September 2026" (report.md:58) should be "a preprint posted in September 2026, not yet
peer-reviewed".** With that change the plain-terms sentence is fair: the preprint finds a 24.1 pp permanent fall in
BEV share over its window and 1,206 vehicles bunched into the final eight weeks (28.8% above trend) with the static
price effect dominating; this study finds a sharp fall lasting about two years and a December excess of 951-2,620
vehicles that is well under half the shortfall. Same direction, similar magnitudes, same conclusion on the rush's
relative size. Two honest caveats are optional but would strengthen it: the preprint's bunching window is eight weeks
(November-December) while this study's excess is December only (November 2023 sat slightly below the baseline); and
the preprint reports ICEV registrations "unaffected" at the deadline, whereas this study's monthly data show the
sharp ICE deferral across it (the ute result) — a point of disagreement, not confirmation.

**C4. `review/reviewer_checks/` is untracked** (git status `??`), yet report.md:186-187 and D2 cite its scripts as the
post-review analyses. Commit it (about 120 KB including the cached `raw/` JSON; no secrets; `attrition_snapshots.py`
takes the 1.4 GB May-2023 CSV path as an argument and does not need the file in the repo).

### Minor wording

- report.md:3 and :44 still say "light vehicles" while :90 discloses ~37,300 heavier vehicles; say "passenger cars,
  vans and goods vehicles" or add "(including about 37,000 trucks)".
- report.md:131 "above the October-November actuals": above their average (4,156); November alone was 4,604.
- report.md:51-52 "plug-in sales only started climbing back in 2026": 2025 was already 16,946 against 12,101 in 2024
  (share 7.7% vs 6.3% for May-Dec 2024); "stayed low through 2025 and climbed back sharply from March 2026" is more
  exact.
- report.md:55 "more than quadrupled": January was seven times December on the light-only series (3,649 / 515).
- D2 item 7: the April 2021 service was the review brief's suggestion, not the draft's.
