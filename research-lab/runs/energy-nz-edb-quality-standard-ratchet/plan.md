# Preregistration: does New Zealand's reliability regime normalise storms away, and does the choice of major-event rule change who breaches?

Lead: `energy-nz-edb-quality-standard-ratchet` (Energy signature area). This plan is committed before any interruption
outcome is aggregated. Only the schema, date range and distributor names of the interruption files were read.

## 0. What was seen before this plan, and how it changes the lead

The quality-standard tables of the 2015, 2020 and 2025 default price-quality path (DPP) determinations were
transcribed by double entry (`code/transcribe.py`, `results/tables/transcription_check.json`).
- **Hand entry against an automated parse:** identical in all 50 rows.
- **Against independent sources:**
  - every DPP4 boundary value equals the Commission's own uncapped value;
  - 14 of 16 DPP4 limits equal the uncapped limit clamped to DPP3 × [0.95, 1.05]. The two exceptions are Aurora,
    whose DPP3 limit was varied, and Powerco, by 0.007.

Those published parameters already answer the lead's level question, so it is reported descriptively and is not
tested:
- **Uncapped changes.** The Commission's uncapped DPP4 unplanned SAIDI limits differ from DPP3's by a median of
  about +2%, ranging from −37% (Orion) to +32% (Vector), and +57% for Aurora against its original DPP3 value.
- **Boundary values** fell for 11 of 16 distributors.
- **The ±5% cap** bound for 13 of 15: it held 7 limits down and 6 up.
- **The lead's DPP2 → DPP4 comparison is not like for like.** The DPP2 limit covers 0.5 × planned + unplanned SAIDI
  with a daily 2.5-beta boundary, while DPP3 and DPP4 cover unplanned SAIDI only, with a rolling-24-hour,
  fixed-count boundary of 2.3 major events a year.

The tests below use the interruption-level data. The Commission published that data with its DPP3 and DPP4 models,
and no aggregate of it has been computed.

## 1. Data

- **Interruptions.** One record per interruption: start time, planned/unplanned, SAIDI and SAIFI values, ICP
  minutes.
  - The DPP3 model data (`DPP3 Final - EDB interruptions.xlsx`) covers disclosure years 2009–2019.
  - The DPP4 model data (`dpp4_edb_interruptions_transitional`) covers 2014–2024.
  - The 2025 disclosure (`EDB_ID_10a_interruptions_2025`) covers April 2024 – March 2025.
- **The splice:**
  - The DPP3 file supplies 2009–2013, the DPP4 file 2014–2024, and the 2025 disclosure 2025.
  - The overlap years 2014–2019 are checked first. Annual raw unplanned SAIDI should agree within 5% for at least
    80% of distributor-years. If not, the disagreement is reported, and the trend tests use 2014–2024 from the DPP4
    file only.
  - 2025 is used only if its unplanned, network-caused interruptions can be identified as in the model data. If not,
    the trend window ends in 2024.
- **Distributors.** These are the 16 non-exempt distributors of DPP4.
  - Eastland Network is Firstlight Network.
  - Centralines is combined with Unison if, in the overlap years, the DPP4 file's Unison equals Unison plus
    Centralines in the DPP3 file. Otherwise it is dropped.
- **National SAIDI.** The customer-weighted sum of distributor SAIDI. Each distributor-year's ICP count is the median
  of ICP minutes ÷ SAIDI value over its interruptions.

## 2. Hypotheses and decision rules

Two tests replicate the lab's US study (`runs/energy-outage-major-event-day-ratchet`) with official data, and one is
specific to New Zealand.

The IEEE 1366 2.5-beta rule works on calendar-day unplanned SAIDI (interruptions by start time). Its threshold for
year *t* is exp(α + 2.5β), where α and β are the mean and SD of ln(daily SAIDI) over the non-zero days of years
*t*−5 to *t*−1. A major-event day exceeds the threshold, and is excluded from the major-event-excluded index.

**The trend.** The slope of ln(national index) on disclosure year over 2014–2025, expressed as % a year. The
interval comes from a distributor-cluster bootstrap (B = 2,000, seed 20261023), which recomputes the national index.
A year-pairs bootstrap is reported as a sensitivity.

- **H1 (masking).** The major-event-excluded index under the rolling rule grows at less than half the rate of raw
  unplanned SAIDI. The statistic is the ratio of the two trends.
  - **Inconclusive** if the raw trend's interval includes 0.
  - **Supported** if the ratio's upper bound is below 0.5.
  - **Refuted** if its lower bound is above 0.5.
  - **Otherwise Inconclusive.**
- **H2 (ratchet).** The rolling threshold removes more of the trend than a threshold frozen at 2009–2013. The
  statistic is the excluded-index trend under the frozen threshold minus that under the rolling threshold.
  - **Supported** if the lower bound is above 0.
  - **Refuted** if the upper bound is below 0.
  - **Otherwise Inconclusive.**
- **H3 (the rule decides compliance).** The assessment years are 2021–2025 (April 2020 – March 2025), compared with
  DPP3 limits.
  - **Rule (a)** is the Commission's: rolling-24-hour SAIDI major events against the determination's DPP3 boundary
    value. Half-hours inside a major event are capped at boundary ÷ 48.
  - **Rule (b)** is the IEEE 2.5-beta daily rule. Its boundary comes from the DPP3 reference window (non-zero days
    of 2010–2019), and major-event days are capped at the boundary.
  - Under each rule, the limit is target + 2 SD over the same window and the assessed value is computed the same way.
  - **Supported** if at least two distributors exceed their limit in a different set of years under (a) than under
    (b). **Refuted** if none does. **Otherwise Inconclusive.**
  - Aurora is excluded, because it was on a customised path from April 2021. Powerco is assessed only in 2024–2025,
    after its transition to the DPP.

## 3. Validation gate (before H3 is read)

The Commission's rule is re-implemented in Python (`code/rules.py`). It must reproduce:
- the Commission's uncapped DPP4 boundary value, target and limit within 1% for every distributor, from the DPP4 file
  over 2015–2024;
- the DPP3 determination's boundary values within 1%, from the DPP3 file over 2010–2019.

If it fails, the cause is reported and H3 is not tested until the cause is fixed.

## 4. Secondary and descriptive

- **Annual raw and normalised unplanned SAIDI** by distributor, 2009–2025, under each rule. The share of raw SAIDI
  removed by normalisation in each year.
- **The yearly count of major events** under a frozen threshold, as a measure of storm frequency.
- **The decomposition of each distributor's DPP3 → DPP4 change in uncapped target.** Re-normalising 2015–2024 with
  the DPP3 boundary separates the boundary re-estimation from outcomes at a fixed boundary.
- **The cap in its first year.** In 2025, the first DPP4 assessment year, which distributors exceed the capped limit
  and which the uncapped one.
- **SAIFI** analogues of H1 and H3.
- **Sensitivities:**
  - trend windows ending in 2024;
  - excluding 2023 (Cyclone Gabrielle);
  - excluding Aurora;
  - excluding the "small distributor" rank adjustments (Invercargill, Nelson).

## 5. Limits stated in advance

- There are 16 distributors and 12 trend years. Weather years are shared across distributors, so the cluster
  bootstrap may understate uncertainty, which is why the year bootstrap is reported too.
- The 2022 targeted review changed how successive interruptions are recorded. The DPP4 file is the "transitional"
  series on the earlier basis, and the 2025 disclosure may not be.
- Compliance under DPP3 is assessed against annual limits. The regime's contravention rules are not modelled beyond
  exceedances.
- Limits can rise for reasons other than weather, such as network condition, vegetation and recording practice.

## 6. Outputs

- `results/tables/`: `dpp_limits.csv`, `transcription_check.json`, `panel_annual.csv`, `validation.json`,
  `primary.json`.
- `results/figures/`.
- `deviations.md` records any change before the results it affects.
