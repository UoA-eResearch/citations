# Review: energy-nz-edb-quality-standard-ratchet

Reviewer: Fable 5.1 (independent, adversarial). Date: 2026-10-25. Scripts, logs and JSON outputs are in
`review/reviewer_checks/` (`01_weights_and_trend.py`, `02_h3_robustness.py`, `03_decomposition_descriptives_2025.py`,
each with a `.log` and `.json`; `dpp3_reasons.txt` is a pdftotext of the Commission's DPP3 reasons paper from
`data/raw/comcom/`). Nothing outside `review/` was modified.

## Verdict: fix first

The re-implementation of the Commission's rule is sound and better validated than the report says: it reproduces the
Stata model's uncapped DPP3 limits to 0.05% for all 17 distributors and the Commission's own published DPP3-period
exceedance record exactly. But two data-handling errors sit under the headline numbers. (1) The ICP weights carry a
corrupt value that gives Alpine Energy 99.5% of the 2017 national weight, so every H1/H2 number, the national index,
F1 and the SAIFI H1 verdict (which flips to Refuted) must be recomputed. (2) The exclusion of 2025 (D1) rests on a
check that summed sub-network rows together with the "All" row of the disclosure table; redone correctly, 2025 passes
the plan's own usability rule, so either the preregistered windows (2014–2025, 2021–2025) are used or a new deviation
with the true reason is recorded. Several report statements are also wrong or overstated (the IEEE/Commission boundary
ratio range, the "two-of-three-year" rule, the uniqueness of the +104/+11 decomposition, the section 0 median). H3's
verdict (Supported) is robust to every variant I tried; the named set of three distributors is not.

## What checks out

- **Git order.** `plan.md` (f854abf, 16:59) precedes `panel_checks.json`/`validation.json` (b9d611d, 17:05) and
  `panel_annual.csv`/`primary.json` (125642c, 17:07); `plan.md` is unchanged since. D1 (17:01) precedes `build`.
- **rules.py against the Commission's code.** Rolling totals (`cumsum` lag 48), rank-n boundary with ranks 726/329
  (Stata) and 734/328 (R), major-event membership as "any 24-h window containing the half-hour" (R
  `frollapply(max, align="left")`; Stata `cum[_n+48-I] - cum[_n-I]`), cap at boundary/48, target = mean annual,
  SD = SD(daily) × √365.25: all match. The strictness mirrors each model (Stata `>=`, R `>`).
- **The gate is not matching for the wrong reason.** 16/16 DPP4 boundary values exact, targets within 0.03%, limits
  within 0.6% (R's UTC-date day sums); 17/17 DPP3 boundary values within 0.15% of the determination. My check 3 adds:
  rules.py DPP3 limits equal the Stata `Unplanned parameters.dta` uncapped limits to ≤0.05% for all 17.
- **Assessment mode** (not validated by the study): my check 2 compares rule (a) with the Commission's DPP4 reasons,
  Attachment E, Table E3 (assessed values 2021–2024 from compliance statements): 51 of 57 cells within 1%, and the
  set of non-compliant years under the determination's limits is reproduced exactly (Firstlight 2023–24, The Lines
  Company 2023, Top Energy 2023, Vector 2023).
- **Panel.** Day-first fix and the disclosure-year assert: 0 of 176,158 (DPP3) and 0 of 220,880 (DPP4) start times
  fall outside their disclosure year. Overlap 2014–2019 identical in 96/96. Centralines: the DPP4 Unison series equals
  Unison alone, so dropping it follows the plan. The model file equals disclosed Class C ("All" network rows) within
  1% in 163 of 176 distributor-years 2014–2024 (max 10%, Horizon 2014).
- **Report arithmetic** against `primary.json`, `decomposition.csv`, `transcription_check.json`: every number I
  checked matches the tables as they stand (they will change with finding 1). Section 0's cap count (13 of 15, 7 down,
  6 up), range (−37%/+32%) and "boundary values fell for 11 of 16" are right.

## Findings

### 1. Major. The ICP weights are corrupt for two distributor-years and the national index is wrong in 2017

- **Evidence.** `results/tables/panel_annual.csv`: Alpine Energy 2017 `icps` = 327,876,213 (10,309 × its median of
  31,804; the DPP4 file's ICP-minutes column for Alpine 2017 sums to 1.1 × 10¹⁰ against 1.1 × 10⁷ in 2016); The Lines
  Company 2020 = 2,019 (0.08 × median); Alpine 2020 missing (all ICP minutes zero). `code/panel.py:140-142` computes the
  proxy with no plausibility guard; `code/analysis.py:49-61` weights the national index with it. Alpine's share of the
  2017 national weight is 0.995 (check 1), so the 2017 "national" raw index (100.24) is Alpine's own 99.82; corrected,
  2017 is 182.96 (raw) and 127.16 (rolling-excluded) instead of 99.96. The dip at 2017 in `F1_national.png` is an
  artefact.
- **Effect** (check 1, anomalies interpolated within distributor; fixed-median weights give the same): raw trend
  −1.79%/yr (−5.63 to +2.50) not −0.73 (−5.26 to +3.37); rolling-excluded −0.06 (−2.26 to +2.12) not +0.37;
  frozen-excluded +0.09 not +0.46; H2 difference +0.155 pp (−0.014 to +0.388) not +0.10 (−0.10 to +0.38); no-2023 raw
  −5.99 (−9.63 to −2.27); no-Aurora raw −1.96. **SAIFI H1 flips from Inconclusive to Refuted** under the plan's rule:
  raw −1.91%/yr (−3.67 to −0.69), ratio 1.07 (0.85 to 1.31). H1 and H2 for SAIDI remain Inconclusive.
- **Fix.** Validate the proxy against disclosed ICP counts (it matches disclosed year-end ICPs within 1% for 14 of
  15 distributors in 2009–2012, so the method is fine; the data are not) or cross-check with a second proxy
  (`Number of ICPs impacted ÷ SAIFI value`, available in the DPP4 file but not kept by `panel.py:54-55`); add a
  within-distributor plausibility guard; regenerate `panel_annual.csv`, `primary.json`, F1, the H1/H2 table, the
  sensitivities, the SAIFI line and the verdict block; record a deviation.

### 2. Major. D1's exclusion of 2025 rests on a double-counting error; by the plan's rule 2025 is usable

- **Evidence.** `code/panel.py:103-105` sums disclosed Class C SAIDI over all rows of each distributor, but the
  disclosure table carries sub-network rows and an "All" row (Aurora: Dunedin, Queenstown, Central Otago, All;
  Vector: Northern, Southern, All; etc.). The study's Class C totals are inflated by 4.96× (Aurora), 4.04×
  (Firstlight), 3.11× (Vector), 3.08× (Unison), 3.00× (Powerco), 2.46× (OtagoNet) (check 3). D1's "Top Energy, Vector,
  Firstlight and Unison differ by 68–130%, likely because other interruption classes are included" is therefore wrong
  for three of the four. Redone with `network == "All"` for the 16 non-exempt distributors: 14 of 16 within 5%
  (Top Energy +130% is real, its 2025 10a(i) unplanned total equals the sum of all unplanned classes, i.e. it includes
  Transpower-caused interruptions it cannot separate; Nelson has zero Class C and no unplanned rows). The plan's rule
  (`plan.md:40-42`; ≥ 12 and ≥ 80%) returns **usable**.
- **Consequences.** The preregistered windows are 2014–2025 (H1/H2) and 2021–2025 (H3; 2025 is a DPP3 assessment
  year). Two latent bugs would bite on inclusion: `panel.py:124,136` keeps 2025 rows by model-file name, and the
  disclosure names Horizon "Horizon Networks", so Horizon's 2025 would be silently dropped; and Top Energy's 2025
  cannot be isolated to network-caused interruptions.
- **Fix.** Correct the check and either (a) include 2025 (map names; handle Top Energy 2025 explicitly; test the
  2022-review recording-basis concern of `plan.md:115-116`, e.g. by comparing 2025 against 2024 on interruption counts
  and durations) and re-run everything, or (b) record a new deviation that states the real reasons (recording basis,
  Top Energy) and rewrite D1. The current D1 text cannot stand.

### 3. Moderate. The 9-of-17 DPP3 limit mismatch (D2) is fully explained by the Commission's own ±5% cap, which the study had in hand

- **Evidence.** DPP3 reasons paper (`data/raw/comcom/dpp3_reasons.pdf`, Attachment J, J67–J69, Table J1): the DPP3
  target was limited to a ±5% change from a consistently normalised DPP2 target, and the limit is the adjusted target
  + 2 SD. Reconstruction (check 3): Stata target × (1 + J1 adjustment) + 2 × Stata SD equals the determination's limit
  to ≤ 0.02% for all 17 (e.g. Vector 103.39 × 0.8635 + 15.55 = 104.83; Centralines 49.53 × 1.2684 + 20.78 = 83.61).
  `deviations.md:30-33` and `report.md:163-164` present this as an unexplained residual ("include something beyond
  target + 2 SD"; "not fully reproduced").
- **Why it matters.** (a) The ±5% inter-period cap is not a DPP4 novelty (`report.md:42-43`, plain terms, implies the
  "last reset"); it has bounded limits since 2020, which strengthens the "no ratchet" reading and belongs in section 0
  and the title's support. (b) H3's "recomputed limits" strip this feature of the actual regime; Vector's "differs"
  exists only because the recomputed limit (118.95) exceeds the capped one (104.83).
- **Fix.** State the mechanism in D2 and the report; cite Table J1; move the determination-limit H3 result to equal
  prominence (finding 4).

### 4. Moderate. H3: the verdict is robust, the named set is not, and rule (b) is inert for three small distributors

- **Evidence** (check 2). Variants: assessment with `>=`, reference with `>`, unrounded recomputed boundary, IEEE
  threshold on 5 years (2015–2019, the IEEE 1366 convention), ddof = 0: all give the same three. Excluding major-event
  days instead of capping (the H1/H2 convention) gives four (Invercargill, Firstlight, OtagoNet, The Lines Company;
  Vector drops out). The determination's limits give two. Margins: Firstlight 2022 is at 0.982 of the Commission-rule
  limit; Vector 2023 at 0.998. Degeneracy: Electricity Invercargill, Nelson and Network Tasman have **0** reference
  days above the IEEE threshold in 2010–2019, and the rule removes 0.0% of their reference SAIDI; Invercargill's daily
  threshold (55.9) equals its annual IEEE limit (55.9), Nelson's (213) is 1.9× its limit. For them rule (b) is "raw
  SAIDI against raw mean + 2 SD", and Invercargill's "difference" is of that kind.
- **Wrong number.** `report.md:25` "The IEEE boundaries are 1.5 to 13 times the Commission's": the range is 1.28×
  (Powerco) to 24.6× (Nelson).
- **Overstatement.** "The rule decides compliance" and "changes compliance for a fifth of distributors"
  (`report.md:18,157-159`, plain terms line 47–48): one of three is an inert-rule artefact, one is a 0.2% margin that
  the actual regime's cap reverses, and the robust core is Firstlight 2022 (and, depending on cap-vs-exclude, OtagoNet
  and The Lines Company instead of Vector).
- **Fix.** Correct the ratio; report the days-over-threshold diagnostic and name the three inert cases; give the
  determination-limit result (2 of 15) equal prominence or make the headline "2–4 of 15 depending on conventions,
  Supported under all"; soften "decides" to "can change".

### 5. Moderate. The boundary/outcome decomposition is order-dependent and reported as if unique

- **Evidence** (check 3). Study order (boundary evaluated on 2015–2024 outcomes): boundary +11.2, outcomes +104.0 of
  +115.3. Boundary first (evaluated on 2010–2019 outcomes): boundary −4.9, outcomes +120.1. Shapley average: boundary
  +3.2. Per distributor, Aurora's boundary part is 11.3 or 5.8, Horizon's outcome part −2.3 or +1.3.
- **Fix.** The conclusion ("mostly outcomes") survives, indeed strengthens; but `report.md:23,29-30,119-120` and the
  F2 caption should give both orderings or the Shapley split, and `analysis.py:181-183` should be documented as one
  of two conventions.

### 6. Moderate. Section 0's "median about +2%" depends on counting Aurora against a limit the plan says was varied away

- **Evidence** (check 3, from `transcription_check.json`). Median uncapped DPP4/DPP3 limit change: +2.4% over 16
  distributors including Aurora's +57%; **−1.0% over the 15 without Aurora**. `plan.md:17-19` and `report.md:27` list
  Aurora separately in the range but include it in the median.
- **Fix.** Report the 15-distributor median (−1%) with Aurora separately, as the range already does.

### 7. Minor. The report misdescribes DPP3's contravention rule and under-uses the Commission's published record

- **Evidence.** `report.md:161-162` says "two-of-three-year contravention rules ... are not modelled". DPP3 clause 9.8
  (`dpp3_determination.txt:1537-1548`) is an annual assessment: the assessed value "must not exceed the unplanned
  SAIDI limit" for the assessment period; two-of-three was DPP2. DPP4 Attachment E Table E3 lists DPP3 non-compliant
  years per distributor; the study's rule (a) with determination limits reproduces it exactly (check 2), yet
  `report.md:145-146` cites only Top Energy. The six cells off by more than 1% (Orion 2022 −19%, The Lines Company 2022
  +3.7% and 2023 +2.8%, Top 2024 +3.4%, Invercargill 2023 +1.4%) reflect compliance-statement data differing from the
  transitional file; none is near a limit.
- **Fix.** Correct the rule description (exceedance is a contravention under DPP3, subject to enforcement discretion
  and the extreme-event standard); cite the Table E3 reproduction as the assessment-mode validation.

### 8. Minor. H1's decision rule is sign-blind, and the fix for the no-2023 case must now also cover SAIFI

- **Evidence.** `plan.md:63-68`, `analysis.py:102-110`: with a falling raw trend the ratio test returns "Supported"
  (no 2023, ratio 0.06) or "Refuted" (SAIFI with corrected weights, ratio 1.07, 0.85–1.31). `report.md:105-108`
  handles the first honestly; the second will appear after finding 1 is fixed.
- **Fix.** State once that H1's rule is informative only when raw rises; report SAIFI as "no masking of a falling
  trend" rather than a bare "Refuted", consistently with the no-2023 treatment. Print the ratio interval (cluster
  −4.0 to +5.2 after correction) in the table so readers see what 11 years can and cannot show.

### 9. Minor. Title and "no trend to absorb" claim more than the test can

- **Evidence.** The corrected raw-trend interval (−5.6 to +2.5%/yr; year bootstrap wider) admits +2.5%/yr, about
  +28% over the window. "There was no national trend" (`report.md:1,11,150-151`; plain terms 39–41) is absence of
  evidence. The decomposition (boundary part between −5 and +11 of +115) and the ±5% cap (in force since 2020) are the
  actual support for "limits are not ratcheting via the storm threshold".
- **Fix.** Retitle around what is shown, e.g. "No sign that New Zealand's outage limits ratchet with storms: the 2025
  reset's target rises came from ordinary-day outages, not a moving storm threshold, and a ±5% cap has bound limits
  since 2020; the major-event rule can change who breaches". In plain terms, "no steady rise" → "no detectable rise".

### 10. Minor. Small items

- H3 mixes `strict=False` for the reference window (`analysis.py:130`) and `strict=True` for assessment
  (`analysis.py:132`); it mirrors the Stata/R models and is immaterial (check 2), but say so.
- `report.md:100` "0.06–1.6 days per distributor per year" is right; after finding 1 the 2017 value of the
  excluded index (127, not 100) should be re-read before claiming the series is "flat" (it still is, within
  98–134).
- `report.md:12` "100–277 in other years" remains true after correction (2021 = 99.5; 2017 becomes 183).
- `validation.json` compares DPP3 limits only to the determination; add the Stata `Unplanned parameters.dta`
  comparison (≤ 0.05%) to the gate so the limit check passes on its proper reference.

## Checks run

- `01_weights_and_trend.py`: anomaly scan of `panel_annual.csv`; national index and the study's `h12()` under study,
  interpolated and fixed-median weights (primary, no 2023, no Aurora, SAIFI).
- `02_h3_robustness.py`: eight H3 variants; margins; IEEE degeneracy diagnostics; comparison with DPP4 Attachment E
  Table E3.
- `03_decomposition_descriptives_2025.py`: both decomposition orderings and Shapley; section 0 descriptives; 2025
  usability with "All" rows; model file vs Class C by year; DPP3 limits vs Stata and Table J1.
