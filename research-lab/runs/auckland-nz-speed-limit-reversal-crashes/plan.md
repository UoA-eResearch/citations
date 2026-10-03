# Preregistration: what did reversing New Zealand's speed-limit cuts cost in crashes?

Lead: `auckland-nz-speed-limit-reversal-crashes` (research-lab/leads.json). Written 2026-10-03 and committed to git
before any crash from FY2025/26 or later has been tabulated.

## What has been seen before writing (disclosure)

**Speed limits.** The National Speed Limit Register (NSLR) was snapshotted today: the full layer with polygons plus a
daily attribute-only copy. A snapshot daemon now keeps copies, because the register is rewritten silently.

**Pre-period crashes.** CAS crashes for FY2005/06–FY2024/25 (Jan 2025–Jun 2025 is the last half-year) were downloaded
and used for the design work below. The scout had already tabulated FY2023/24–FY2024/25 injury crashes in zones raised
in Apr–Oct 2025.

**Post-period crashes.** CAS crashes for FY2025/26 onward were downloaded into a sealed file and not tabulated:
`data/sealed/cas_post.json.gz`, SHA-256 `465dc0f4b17c0bafe2f28975e653d7e412c1027333db125d8cc0e4cb084042e8`. The analysis
checks this hash before reading.

**Design numbers.** All numbers below come from pre-period data only: `code/build_units.py`, `code/pre_design.py`
and `results/tables/pre_*.csv`.

## 1. Question

The Land Transport Rule: Setting of Speed Limits 2024 came into force on 30 Oct 2024. It made road controlling
authorities reverse many speed-limit reductions made since 2020, mostly by 1 Jul 2025. Did injury crashes rise on the
roads whose permanent limit went back up, relative to similar roads whose limit did not change?

## 2. Data

- **NZTA Crash Analysis System (CAS).** Open FeatureServer, all police-reported crashes. Points are in NZTM. Each crash
  has `crashYear` and `crashFinancialYear`, which together give half-year resolution:
  - FY "a/b" with crashYear a = July–December of a (half aH2);
  - with crashYear b = January–June of b (half bH1).
- **NSLR, full layer.** Snapshot of 2026-10-03; Permanent category only.
- **OpenStreetMap New Zealand extract** of 2026-10-02 (Geofabrik, md5 6ded30a3…). Public-road classes: motorway,
  trunk, primary, secondary, tertiary (each with links), unclassified, residential, living_street and road. Private and
  `access=no` ways are excluded.

## 3. Units and treatment (fixed by `code/segments.py` and `code/build_units.py`)

- **Segments.** Each OSM way is cut into equal pieces of at most 100 m: 1,184,764 segments, 106,770 km.
- **Limit at each date.** A segment takes the NSLR limit in force at its midpoint on a date: whenEffective ≤ t <
  whenIneffective.
  - If overlapping records disagree, the segment is ambiguous and excluded.
  - Check dates: t22 = 2022-06-01, t0 = 2024-10-29, t1 = 2025-11-01, and the 1st of each month from Nov 2024 to Jul 2026.
- **Classes:**

  | Class | Rule |
  |---|---|
  | Treated | Exactly one raise between t0 and t1, of 10–40 km/h (100→110 excluded). No other value at any monthly check up to 1 Jul 2026. |
  | Expressway | 100→110 in the same window; analysed separately as exploratory. |
  | Control | The same limit at every check date from t0 to 1 Jul 2026. |
  | Excluded | Everything else: lowered, several changes, ambiguous, or not covered at t0 or t1. |

- **Register coverage gaps.** From about May 2026 the public register shows growing gaps: records end without
  replacements. A check date with no record in force therefore counts as unknown, not as a change.
- **Cohort.** The half-year of the raise's whenEffective: 2025H1 for 10,897 treated segments, 2025H2 for 86.
- **Strata** (coarsened exact matching): road controlling authority × v0 × half-year of any reduction between t22 and
  t0 ("none" if no reduction) × class group (highway = motorway/trunk, arterial = primary/secondary, local = the rest).
  - Only strata containing both treated and control segments are used: 96.8% of treated segments, about 828 km.
- **Transition types** (secondary analyses):
  - urban 30/40→50;
  - urban 50→60–80;
  - peri-urban 60/70→70–100;
  - rural 80/90→90–100.

## 4. Primary analysis

**Outcome.** Injury crashes (fatal, serious or minor) snapped to segments by the rule in `code/snap.py`:

- Candidates are segments within 30 m.
- Prefer a candidate whose normalised OSM name equals CAS `crashLocation1`, or which shares its state-highway number.
- Otherwise take the nearest. Crashes more than 30 m from any segment are dropped and counted.

**Window.** 2022H1–2026H1.

- **Pre-period:** 2022H1 up to the half before the cohort's transition half.
- **Transition half:** the half containing whenEffective. It is dropped for that cohort's treated segments.
- **Post-period:** the halves after transition, up to and including 2026H1.
- **Why the window starts in 2022 (pre-period data).** The full-history event study rejects parallel pre-trends
  (joint Wald p = 0.0001). Treated segments ran higher relative to controls in 2018–2021, consistent with earlier
  reductions (2020–2021) that the NSLR history, which starts in 2022, cannot see. Within 2022H1–2024H2 the
  coefficients are -0.26 to +0.17 with no monotone trend (joint p = 0.044; reported as a limitation).
- **Why 2026H2 is excluded.** It is partial and lagged, and the register has gaps.

**Model.** A Poisson regression on the segment × half-year panel:

- **Fixed effects:** segment, and stratum × half-year.
- **Regressor:** one indicator, treated × post.
- **Standard errors:** clustered by corridor. A corridor is road controlling authority + normalised OSM name, or the
  OSM way when the way has no name.
- **Estimation:** pyfixest `fepois`.
- **No forbidden comparisons.** No already-treated segment-half acts as a control for a later cohort, because
  transition halves are dropped and every post half of both cohorts is coded treated.

**Estimand.** RR = exp(β), the injury-crash rate ratio on treated segments after the raise relative to controls.

**SE calibration (pre-period).**

- **Placebo setup.** 200 placebo-in-space draws assign fake treatment to control segments, stratum by stratum, in a
  window with the same shape: 6 pre half-years, a dropped transition half and 2 post halves.
- **Results.**
  - The placebo log-RR SD (0.113) equals the mean clustered SE (0.113); the ratio is 1.00.
  - At |z| > 1.96 the rejection rate is 6.5%.
- **Rule.** The clustered SE is used without inflation.

**Power (pre-period).**

- Treated segments had about 135 injury crashes per half-year in 2023H2–2025H1, so the post-period should hold about
  270.
- The implied SE of log RR is about 0.100.
- Minimum detectable effect at 80% power: RR 1.28 at one-sided α = 0.05, and **RR 1.33 at one-sided α = 0.025**, the
  level used here.
- A true effect of +10%, the size of the hypothesis, is therefore unlikely to be detected in Stage 1.

**Two looks (decision rules).** The test is split across two stages at one-sided α = 0.025 each (Bonferroni), so the
overall rate is at most 0.05.

- **Stage 1 (now):** post = 2025H2 + 2026H1. This is the verdict for this report.
- **Stage 2 (re-run about Oct 2027,** when CAS holds FY2026/27): the identical code with post = 2025H2–2027H1 and the
  window extended to 2027H1.
- **The NSLR snapshots kept from today onward** determine any further limit changes up to 30 Jun 2027. Stage-2
  controls and treated segments must also be stable through that date.

| Verdict (each stage) | Condition |
|---|---|
| Supported | RR ≥ 1.10 and the one-sided 97.5% lower bound > 1.00 |
| Contradicted | the one-sided 97.5% upper bound < 1.10 |
| Inconclusive | otherwise |

## 5. Secondary and robustness analyses (reported, no verdicts)

- **Fatal+serious crashes.** Same model.
- **All crashes, including non-injury.**
- **Effects by transition type and by state highway vs local road.**
- **Auckland only.**
- **Effect by post half.** 2025H2 and 2026H1 separately.
- **Manipulation check.** The share of post-period crashes on treated segments whose CAS `speedLimit` equals the new
  limit v1. The pre-period baseline share recording v0 is 0.71 for treated segments and 0.94 for controls.
- **Snapping tolerance.** 15 m and 50 m; and name-matched snaps only.
- **Full window.** 2017H2 onward, which has known pre-trends.
- **Cohort-specific (ETWFE-style) indicators.**
- **Without the 2025H2 cohort.**
- **Expressway 100→110 segments.** Exploratory.
- **Speed–crash benchmark.** For each transition type, the injury-crash ratio predicted by a power model with
  exponent 2, assuming mean speed rises by a quarter of the posted change. Exploratory only.

## 6. Validity threats (fixed now)

- **Selection.** Which reductions were reversed depended on consultation and on the Rule's criteria. Strata match on
  authority, prior limit, reduction timing and road class, but unobserved differences remain.
- **Reporting lag.** Recent minor-injury crashes are reported late. Treated and control segments are affected
  equally, but recent periods are noisier.
- **Concurrent changes.** Variable school-zone limits (by Jul 2026) are not in the Permanent layer. Traffic volume and
  enforcement changes are not observed.
- **Register quality.** The 29% mismatch between CAS-recorded limits and the NSLR limit on treated segments
  (2023H2–2025H1) shows that recorded limits lag the register. NSLR is the source of truth for treatment.

## 7. Review and reporting

- An independent reviewer agent checks code and results before any verdict is stated.
- The report opens with an "In plain terms" section.
- Departures are logged in `deviations.md` with timestamps from `date`.
- Derived tables are committed. Raw CAS, OSM and NSLR snapshots are kept locally; they are large, so the SHA-256 sums
  are committed instead.
