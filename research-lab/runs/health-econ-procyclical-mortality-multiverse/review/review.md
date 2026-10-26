# Review: health-econ-procyclical-mortality-multiverse

Reviewer: independent adversarial review (Fable), 2026-10-27. Scripts and outputs in `review/reviewer_checks/`
(`check_data.py`, `check_specs.py`, `check_estimator.py`, `sensitivity.py`, with `.out` and `sensitivity.json`).

## Verdict: publish with edits

No reported number is wrong, the estimator is correct, and the provenance holds. The edits are interpretive: the
"measure" story conflates a real difference between the two weakness measures with an ageing confound built into
the study's employment-to-population ratio (finding 1); the H2 mechanism sentence and the F2 figure title make an
absence claim the data cannot support (finding 2); the pooled share should be shown for what it is, the average of
two opposite answers over near-duplicate windows (finding 3). Two silent details need a deviation entry (findings 4,
6), and three literature claims lack ledger support (finding 5). None requires re-estimation.

## What was verified

- **Provenance (git).** plan.md d2bef80 21:47 -> engine 533cdf5 21:54 -> panel + D1 75cc3e9 22:34 -> draft ed2f4fc
  22:39. `code/multiverse.py` is unchanged after 21:54; `build.py` changed only in the panel commit (D1). The run log
  shows a 36 s run. Plan preceded the panel; D1 preceded estimation.
- **NBER parse.** Yearly totals (restatus != 4, state of residence) match the published US totals exactly for 27 of
  29 years (1981 +51, 1982 -72 deaths, 0.004%); NCHS alphabetical codes 1976-2002 and postal codes 2003-04 both map
  correctly (the 1999-2004 CDC match is exact). ager12 -> 11 groups, age-not-stated (0.02-0.05%) kept in totals and
  excluded from age-specific rates. STD2000 sums to 1,000,000 and matches the 11-group 2000 standard. SEER 20-group
  mapping to 11 groups is correct; US totals are 217.6M (1976), 282.2M (2000), 331.6M (2020).
- **Weekly apportionment.** 365/366 days covered for every state-year 2014-2022; 259 in 2023 (unused). The
  occurrence/residence ratio is flat over 2014-2017 in the mean (-0.0009 to -0.0017) with no drift except DC
  (finding 6). NYC is correctly added to NY in both weekly and VSRR files (otherwise calibration factors would be
  far from 1; NY 2023 = 163.5k, consistent with 2022's 174.5k).
- **Splice as hidden driver: no.** Year-by-year cross-state SD of the within-state log change in deaths is 0.014
  (1999), 0.013 (2018), 0.023 (2023) against a median of 0.018; the correlation with the change in unemployment in
  those years (+0.34, -0.17, -0.15) sits inside the range of other years (-0.44 to +0.34). The 2023 quarterly-rate
  figure is 3.4% above the day-scaled weekly figure in 98% of states, a common shift absorbed by year effects.
  Re-running the 1976-2022 window (288 specs, 1,999 draws): 61.1% negative-significant against 59.7% for 1976-2023;
  canonical -0.64% in both.
- **Estimator.** Six specifications (TWFE, FD with quadratic trend and lag and weights, division x year with linear
  trends and lag, TWFE quadratic, FD linear unweighted, an H2 FD spec) rebuilt independently in pandas and fitted
  with pyfixest 0.60 CRV1: all betas agree to 1e-7 and match the spec tables. SE ratios squared equal exactly
  (n - K_nested)/(n - k): pyfixest does not count cluster-nested fixed effects, the study counts every parameter
  (the Stata `regress, cluster` convention; more conservative). The closed-form WCR equals a brute-force restricted
  bootstrap on two real specifications with 999 shared draws (p 0.4474 = 0.4474; p 0.0000 = 0.0000; t to 4 d.p.).
  Lag reparametrisation, FD trend mapping and FD weights are as the plan states.
- **Joint test.** Shared G x 500 draws, restricted residuals per specification, one-sided comparison against the
  two-sided CR1 critical value matching the observed statistic. 0 of 500 null draws reach the observed share, so
  "p < 0.002" is the correct statement.
- **Report numbers.** Every number in the verdict block, the window table, the canonical table, the H2 table and the
  decomposition sentences matches the tables (rounding included). G5 `--verify` and G6 `check` pass.

## Findings

### 1. The "measure" result is partly an ageing confound in the study's employment-to-population ratio (medium)

Evidence (`check_specs.out`, "measure x controls x outcome", long windows):

| measure | controls | crude | log_aadr | log_crude |
|---|---|---|---|---|
| -emp/pop15 | none | 17.6% | 50.0% | 11.1% |
| -emp/pop15 | demog | 65.7% | 52.8% | 59.3% |
| unemployment | none | 92.6% | 88.9% | 90.7% |
| unemployment | demog | 90.7% | 94.4% | 90.7% |

For the unemployment rate, controls and age adjustment do not matter. For -emp/pop15 they decide the result: with
an age-adjusted outcome, or with the demographic shares, 53-66% of long-window specifications are negative and
significant; with a crude or log crude outcome and no controls, 11-18%. The canonical-type coefficient
(1976-2017, log crude) is +0.19% without controls and -0.31% with them; with the age-adjusted outcome -0.03% and
-0.41%. By trend: -emp/pop15 gives 19.5% with no trends against 38-39% with state trends; unemployment 58-67%
throughout. State trend slopes of -emp/pop15 correlate 0.39 with slopes of the 65+ share across states
(`check_data.out`).

The mechanism is in the denominator (build.py:98, 228): LAUS employment is divided by SEER total resident
population 15+, which includes retirees, the institutionalised and the military. A state that ages faster sees
emp/pop15 fall and crude mortality rise with no cyclical content, biasing beta positive in exactly the specifications
without age adjustment or demographic controls. BLS defines the ratio over the civilian non-institutional population
16+. The plan preregistered this construction, so it is not a G1 problem, but the report's reading is: "The
employment-to-population ratio, arguably a cleaner measure of activity, gives it far less support" (report.md:146)
is unsupported and, on this evidence, backwards. The "measure" share of the R2 (11 points) includes the confound.

Note that the measure still matters after the confound is removed (53-66% against 90%+, and the canonical-type
-emp/pop15 estimate is not significant in any variant, p 0.35-0.93), so the headline "with the unemployment rate"
survives.

Fix: (a) add the table above (or the measure x controls cross-tab) to Results; (b) replace report.md:146 with a
sentence saying the E/P result depends on age adjustment or demographic controls, and why; (c) list the denominator
mismatch under "Not shown" / limits; (d) in the verdict bullet "The measure", add "largely in specifications
without age adjustment or demographic controls" or the 53-66% figure; (e) deviations: a post hoc note that the
confound was identified in review.

### 2. H2: an absence claim the precision does not support; figure F2 still carries the pre-G5 wording (medium)

report.md:149-152: after 2010 "the remaining state variation does not track unemployment". The canonical-type
log-drug specification gives +0.04% per point for 2011-2019 (CR1 CI -4.2% to +4.3%) and +1.9% for 2011-2023
(-2.3% to +6.1%); the median CI half-width over all log-drug specifications is 3.9% per point. The 1999-2010
contrast's canonical-type estimate is +5.6% (+2.4% to +8.8%, WCR p 0.004), which lies inside the 2011-2023 interval.
Post-2010 the data cannot distinguish zero from an effect as large as the one they find for 1999-2010. The G5 pass
changed the title from "do not follow the cycle" to "show no reliable cyclical pattern" for this reason but left
this sentence, and `figures.py:117` still writes the F2 suptitle "post-2010 drug deaths do not track the cycle".

Also: the 20 negative-significant H2 specifications are 19 unweighted TWFE/divyear specs, 17 of them with the crude
level rate, and 16 with -emp/pop15 (`check_specs.out`), i.e. a corner of the multiverse, not a countervailing
pattern; worth one sentence so "3.5% negative-significant" is not read as evidence of procyclical overdose deaths.

Fix: reword report.md:151-152 to "the remaining state variation is not detectably related to unemployment: the
intervals, roughly +/-4% per point, include both zero and the 1999-2010 estimate"; add the canonical-type H2
estimates with CIs to the H2 table; regenerate F2 with a matching title (or edit figures.py:117 and re-run).

### 3. The pooled share averages two opposite answers over near-duplicate windows (medium, interpretation)

Long windows (1976-2017/2019/2023, 1,008 specs): 65.8% negative-significant, in the Refuted band. Sub-periods
(1,296 specs): 33.2%, in the Supported band. The three long windows share 42 of their 44-48 years, so the pooled
47.4% triple-counts one sample against three disjoint ones. The report's "the window decides it" is right, but the
verdict block should say plainly that Inconclusive is the mean of a Refuted and a Supported answer, not a
population of individually ambiguous specifications, and that the plan's window list fixes the weighting.

Supporting evidence for the pre-1992 claim (reviewer re-run, not preregistered, 1,999 draws): a 1992-2017 window
gives 22.0% negative-significant (unemployment 31.5%, -emp/pop15 12.5%), 77% negative, 5.1% positive-significant;
canonical -0.06% per point (CI -0.60% to +0.49%, p 0.88). 1992-2019: +0.01%. The 2006-2017 canonical estimate
(-0.57%) and the 1992-2005 one (+0.21%) cancel over 1992-2017. This supports "owe their significance largely to the
pre-1992 years" and can be cited as a reviewer check, labelled post hoc.

Fix: one sentence in the verdict block with the 66% / 33% split and the window-overlap caveat; optionally the
1992-2017 result labelled post hoc.

### 4. G2: FD-with-lag specifications in 1976 windows silently drop 1977 (low)

`multiverse.py:88` builds the FD lag term from u(t-2); for a window starting 1976 that needs 1975 unemployment, and
LAUS begins in 1976 (`check_data.out`: 1975 ur missing for all 51 states). The `ok` mask at `multiverse.py:126`
drops the 1977 rows without a message: n = 2,040 for FD/cumulative against 2,091 for FD/contemp and TWFE/cumulative
in 1976-2017 (`check_specs.out`), and likewise 714 vs 765 (1976-1991), 2,142 vs 2,193, 2,346 vs 2,397. 192
specifications are affected; the plan says only the first year is dropped. Effect on conclusions: none (canonical
1978-2017 is -0.70%, p 0.004). No other NaN drops appear (n is otherwise constant within window x estimator x lag).

Fix: a D3 entry stating the drop and the affected count; a line in "How it was done". Code: assert n against the
expected count or log the dropped rows.

### 5. G6: three literature claims lack a real ledger source (low)

- report.md:150-151 attributes the post-2010 overdose rise "above all" to illicit fentanyl. No ledger row. It is a
  causal literature claim and needs a source (an NCHS data brief on synthetic-opioid deaths, or a review) or
  softening to "largely unrelated to the business cycle".
- "less pollution" (report.md:37) is backed by M4, which cites Ruhm 2000 while its own conditions field says
  pollution is a later literature. That is a hollow row. Add a row for the pollution mechanism (e.g. the
  air-pollution-and-procyclical-mortality paper by Heutel and Ruhm, 2016) or drop the words.
- M6 ("no specification curve with joint inference over this panel was found") rests on the lead's search; fine
  as an absence claim, but the ledger should name the search terms or date.

The ledger tool passes because it checks resolution, roles and fields, not whether the source supports the claim.

### 6. Data construction details to document (low)

- DC's occurrence/residence ratio drifts 2.2% per year over 2014-2017 (median state 0.01%), so DC's calibrated
  2018-2022 deaths may be off by up to ~10% by 2022. DC carries 1/51 weight in unweighted specifications. Note as a
  limit.
- deviations.md D1 says DC's VSRR counts are "11-15%" above NCHS; the overlap years give 15.2%, 11.5%, 12.3%,
  16.1%.
- VSRR calibration: without it, S2 is 2.3% (2011-2019: 4.2%, 2011-2023: 0.3%) against 1.6%; verdict unchanged
  (`sensitivity.json`). Zero drug-death cells: none, so the log(d+1) fallback never ran. Worth one line each.
- `code/download.sh` writes to `/mnt/data/procyclical/raw`, not `data/raw`; its FRED loop is empty; `489q-934x` and
  the FRED series are fetched outside it. The report's reproduction steps say so for FRED and 489q but the path
  mismatch will trip a reader.

### 7. Multiverse definition: short-window trend specifications are mechanically null (low, informational)

228 specifications have k/n > 0.30 (division x year with state linear or quadratic trends in 12-16-year windows;
max 0.41). In 2006-2017 the share negative-significant is 28.5% with no trends, 11.8% with linear and 0.0% with
quadratic trends; cumulative-lag specs 5.1% against 21.8% contemporaneous. A state quadratic over 12 years with one
recession absorbs the cycle by construction. These options are preregistered and symmetric across measures, so
they do not bias the comparison, but the sub-window shares (13%, 1.4%) are partly a power statement. One sentence
in Results. The "canonical choices are among the most favourable" sentence is true within 2006-2017 (no trends
28.5%, unemployment 23.1%, controls 18.5%) but "no trends" is the least favourable trend option overall (43.1% vs
50.9% / 48.3%); add "in that window".

### 8. Wording (low)

- Plain terms: "every combination of the reasonable choices a researcher could make" -> "every combination of a
  fixed set of reasonable choices" (eight dimensions; cause-specific outcomes, alternative clustering and
  heterogeneity-robust estimators are excluded, as the limits say).
- Report "By window and measure" table header "negative, either" is unclear; "negative (either measure)".

## Gate checks

- **G5** passes (38 rows) and is honest for the sections it covers. Its scope is title, standfirst, verdict block
  and plain terms; the unsupported sentences in findings 1 and 2 sit in "What this does and does not show", outside
  the tool's reach. Suggest the lab extend G5 to that section for this report.
- **G6** passes mechanically; finding 5 lists one missing and one hollow row. Spot-checked M1 (Ruhm 2000, QJE,
  1972-1991), M2 (Ruhm 2015, JHE 42, 1976-2010, weakening and countercyclical poisoning), M3 (Brüning and Thuilliez
  2019, Demography, France), M5 (Stevens et al. 2015, AEJ:Policy, nursing-home staffing), M7 (splice table): roles
  and conditions are right.
- **G1.** No leakage-audit section in plan.md (the study predates the gate). I found no outcome-correlated choice:
  every option is preregistered and crossed symmetrically; D1 was logged before estimation; 1976-1991 is Ruhm's own
  window, so its 85% is a replication, not a selected window. The confound in finding 1 is a measurement flaw, not
  hindsight selection.
- **G2.** No `coverage.json`. One silent drop (finding 4). Weekly gaps: none in 2014-2022. Bootstrap: no resamples
  can fail (closed form), and NaN-free designs were confirmed by constant n.
- **G3.** No `plausibility.md`. The report anchors the canonical estimate on Ruhm 2000 (-0.5% per point), and this
  review's NBER-total and pyfixest checks serve as traces. Acceptable for a pre-gate study; note its absence.
- **G4, G7.** Not applicable (no classifier, matcher or labelled validation sample).

## Summary of required edits (publish with edits)

1. Measure x controls/outcome table; replace report.md:146; denominator limitation; qualify the "measure" bullet.
2. Reword report.md:151-152; add H2 canonical-type CIs; regenerate F2's title.
3. State the 66% / 33% split and the window-overlap caveat in the verdict block.
4. D3 for the 1977 drop (192 specs).
5. Ledger rows for fentanyl and pollution, or drop the words.
6. Document the DC drift, the VSRR calibration sensitivity (2.3% vs 1.6%), and fix download.sh's path.
7-8. One-line clarifications.
