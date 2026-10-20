# Does the major-event-day rule hide the US outage trend it is meant to normalise?

*Daily outage minutes per customer for 24 US states and DC, 2015–2025, built from the EAGLE-I county outage snapshots and
classified under the IEEE 1366 "2.5β" major-event-day rule and three alternatives, plus a Monte Carlo of how well
each rule detects a real trend.*

**Verdict: Refuted on detection power (H3); the ratchet test (H2) is Refuted only with 2015 in the baseline; H1 is
Inconclusive, because there is no detectable all-events trend to mask.** In simulation the standard rule keeps about
three-quarters of a perfect rule's power to detect deteriorating normal operations, and that holds under every variant
tried. The claim that its rising threshold strips trend out is not supported here, but it is refuted only under the
preregistered baseline, and that baseline includes 2015, the year with the thinnest data.

- **H1 (the rule masks an all-events trend): Inconclusive.**
  - All-events SAIDI shows no detectable trend over 2020–2025: −3.4% a year (95% CI −9.9 to +3.0). That interval is
    consistent with a 10%-a-year fall or a 3%-a-year rise, so "nothing to mask" means nothing *detectable* to mask.
  - The MED-excluded index under the standard rolling rule rises **+3.1% a year (+1.6 to +4.8)**.
  - **The utilities' own MED-excluded SAIDI for the same 25 states shows no such rise** (post-review analysis):
    −0.05% a year (−1.1 to +1.1), against +3.1 for this index — a gap of +3.1 points (+1.9 to +4.4). The all-events
    series agree with each other (−3.4 here, −3.0 in the utilities' data). So the rise belongs to the state-level
    construct and its classification of major events, not to US routine reliability.
- **H2 (the rolling threshold removes more trend than a frozen one): Refuted, under the preregistered baseline only.**
  - With the frozen threshold set on 2015–2019, the rolling index rises 0.79 points a year *faster* (+0.18 to +1.48).
  - **Under every cleaner baseline the result is Inconclusive** (post-review analysis): frozen on 2017–2019, +0.56
    (−0.10 to +1.25); on 2018–2022, +0.64 (−0.15 to +1.52); and under the study's own preregistered coverage
    sensitivity, +0.54 (−0.11 to +1.23). None is negative, so the rolling rule never removes *more* trend.
  - 2015 is the problem. Its typical daily outage level sits 0.26 log points below 2017–2019, and Nevada has no data
    at all from January to mid-June 2015, though it passes the county-count inclusion rule.
- **H3 (the rolling rule has at most half an oracle's detection power): Refuted, robustly.**
  - In 2,000 simulated systems where normal-operations severity grows 3% a year, the rolling rule detects the trend
    in 44% and an oracle that knows the storm days in 59%: a ratio of 0.74 (0.70–0.78).
  - The frozen threshold detects 36%, a fixed 99th-percentile rule 25%, and all events 8%.
  - The ratio stays above 0.5 under lighter-tailed storms (0.76) and with storms defined at major-event scale (1.11).

**Validation.** The EAGLE-I index tracks the utilities' own reported SAIDI closely: within each state over 2018–2024
the median Spearman correlation is 0.96, no state is negative, and year-on-year changes correlate at 0.95. Pooled
across 175 state-years, the correlation is 0.94.

## In plain terms

Power companies report how many minutes their customers are without power each year. Before comparing years,
regulators usually remove "major event days", the worst storm days, using a standard statistical rule. Critics worry
the rule's cut-off creeps upwards as storms get worse, which could hide a real decline in everyday reliability.

We rebuilt daily outage minutes for 24 US states and DC from a public federal dataset covering 2015 to 2025, then
applied the standard rule and three alternatives.

Including storms, there was no clear trend over 2020–2025: storms swing too much from year to year to see one.

The standard rule's cut-off did not throw away more of a trend than a fixed cut-off would have. But that result
depends on including 2015 in the starting years, and the 2015 data are patchy; leave it out and the test cannot tell
either way.

With storm days removed, our measure of everyday outages rose about 3% a year. The power companies' own figures for
the same states and years show no rise at all. So that increase comes from how a state-wide measure sorts storm days
from ordinary ones, not from worsening everyday reliability.

We also simulated thousands of made-up power systems. When everyday reliability really did get worse, the standard
rule caught it about three-quarters as often as a perfect rule would, more often than the alternatives we tested.

These are state totals built from outage maps, not individual utilities' official figures.

## What was asked

IEEE Standard 1366 separates "major event days" (MEDs) from normal operations. Each year's threshold is
exp(α + 2.5β), where α and β are the mean and standard deviation of the log of non-zero daily SAIDI over the previous
five years. Regulators judge reliability on the MED-excluded index. If storms are getting worse, the threshold rises
with them, and a critique raised at a 2025 CPUC technical session is that this can hide deteriorating performance.

The study asks three preregistered questions (`plan.md`, 950d8c0):

- **H1 (masking).** Does the MED-excluded index under the rolling rule grow at less than half the rate of the
  all-events index?
- **H2 (ratchet).** Does the rolling threshold remove more of the trend than a threshold frozen at 2015–2019?
- **H3 (detection power).** In simulation, does the rolling rule detect a 3%-a-year deterioration in normal
  operations at most half as often as an oracle that knows which days are storms?

## What was already known

The closest prior work is **Eto, LaCommare, Sohn and Caswell (2016)**, "Evaluating the Performance of the IEEE
Standard 1366 Method for Identifying Major Event Days" (*IEEE Transactions on Power Systems* 32(2):1327–1333,
doi:10.1109/TPWRS.2016.2585978). It proposes quantitative metrics for how well the method isolates major events from
the underlying year-to-year trend, applies them to a large sample of utility-reported data, and tests the alternative
specifications the IEEE Distribution Reliability Working Group had considered. It finds that none is uniformly better
than the standard method: each lowers year-to-year variability for some utilities and raises it, sometimes sharply,
for others. The original novelty search missed it; the lab's own scouting critique had flagged it.

Other known critiques of the 2.5β method concern zero-SAIDI days (IEEE 2013), log-normal tail misfit (IEEE 2011), and
the CPUC session's warning that rising thresholds can hide localised problems.

What this study adds is narrower: an open daily panel recomputed from EAGLE-I rather than utility reports; a
frozen-threshold counterfactual for the specific ratchet critique; an accounting of how much the moving threshold
reclassifies; and a detection-power comparison across rules under known simulated trends.

## How it was done

**Data.**
- **Outages.** The EAGLE-I outage dataset (Oak Ridge National Laboratory; figshare 24237376 v4, CC BY 4.0) gives
  customers out by county in 15-minute snapshots, from utilities' public outage maps.
  - 2015–2025, 11 GB, verified against the repository's MD5 sums.
  - The 2023 file names its customers-out column `sum` (D1).
- **Customers.** The dataset's modelled customer counts per county (MCC 2022).
- **Validation.** EIA-861 reliability data (via PUDL), with and without major events.

**Daily SAIDI** (`code/build.py`). For each state and local day in the state's predominant time zone: the sum over
its counties and snapshots of customers out × 15 minutes, divided by the state's MCC customers. Days with no record are
zero. This gives 204,918 state-days.

**Data quality**, from the review (none changes a verdict):
- the 2015–2021 year files end at 31 December 00:00 UTC, so each of those years' last 29–32 local hours are
  zero-filled; 2022–2025 are complete, and the last 5–8 local hours of 31 December 2025 are absent;
- rows with a blank customers-out field (1–9% of rows nationally in 2017–2021 and 2025) are dropped. They behave like
  the explicit zero rows of later years, but they are concentrated — 34% of rows for Illinois in 2025, 28% for
  Michigan in 2018 — and could hide up to 9% of Illinois's 2025 outage minutes and 13% of Vermont's;
- national collection gaps total 4.4 days in 2015, 2.9 in 2016, 2.5 in 2017 and 1.8 in 2018, then under half a day;
- Nevada has no records from 1 January to mid-June 2015.

**Inclusion.** A state is included if both hold:
- its customer coverage is at least 80% in every year of the dataset's coverage history (2018–2022);
- in every year 2015–2025, the number of its counties reporting any outage is within ±15% of its 2018–2022 median.

24 states and DC qualify: 25 systems, called states below. Excluded:
- AZ, CA, CO, CT, ID and MO, on reporting-county stability;
- AR, IN, KY and MS, on coverage.

The county-count rule is the only guard on 2015–2017 coverage; it cannot see a state that is silent for months but
reports from the same counties once it starts, which is what happened in Nevada in 2015.

**Rules compared** (`code/analysis.py`), for 2020–2025:
- (a) rolling 2.5β, the standard;
- (b) 2.5β frozen at 2015–2019;
- (c) a 10-year window, for 2025 only;
- (d) a fixed 2015–2019 99th percentile;
- (e) no normalisation (all events).

**Trends.** A panel regression of ln(annual index + 1 minute) on year with state fixed effects. Intervals come from a
state-cluster bootstrap (2,000 resamples).

**The Monte Carlo** (`code/simulate.py`):
- **Calibration.** Each simulated system is calibrated to a randomly drawn included state's 2015–2019 days: zero days,
  a log-normal body, and a generalised Pareto tail above the 95th percentile, its shape capped at 0.9 (D2).
- **Scenarios.** 2,000 systems × 11 years each:
  - A: normal operations +3% a year;
  - B: storm frequency and size +5% a year;
  - C: no trend.
- **Detection.** A one-sided p < 0.05 for a positive log-linear trend over the final six years.

## Results

### The trends (`results/tables/primary.json`, `results/figures/F1_indices.png`, `F2_trends.png`)

| index | trend 2020–2025, % per year | coverage sensitivity |
|---|---|---|
| all events | −3.4 (−9.9 to +3.0) | −3.8 (−10.2 to +2.6) |
| **MED-excluded, rolling 2.5β (the standard)** | **+3.1 (+1.6 to +4.8)** | +2.6 (+1.0 to +4.3) |
| MED-excluded, frozen 2.5β | +2.3 (+0.7 to +4.0) | +2.0 (+0.6 to +3.8) |
| MED-excluded, fixed 99th percentile | +2.2 (+0.8 to +3.9) | +2.0 (+0.6 to +3.6) |
| *utilities' EIA-861 SAIDI, with major events* | −3.0 (−9.2 to +2.7) | |
| *utilities' EIA-861 SAIDI, without major events* | **−0.05 (−1.1 to +1.1)** | |

The two EIA rows are a post-review analysis over the same 25 states and 150 state-years
(`review/reviewer_checks/check7.json`).

- **H1 is Inconclusive** by its preregistered rule: the all-events interval includes zero.
  - The "masking ratio" (rolling trend over all-events trend) is meaningless when its denominator is near zero:
    −0.89 (−9.8 to +9.5).
  - All-events SAIDI is dominated by a few storm years (2020 and 2024), so it carries no detectable trend in six years.
- **The MED-excluded rise is a property of the state-level construct.** The EAGLE-I proxy tracks the utilities'
  all-events series (−3.4 against −3.0), so the divergence is in which days count as major events. The state-level
  2.5β excludes a smaller, and faster-shrinking, share of SAIDI than the utilities' own thresholds — 77, 66, 55, 61,
  75 and 36% of SAIDI in 2020–2025, against 78, 74, 64, 69, 80 and 51% in the utilities' data. The plan (§6)
  anticipated that aggregating to states changes which days are MEDs; this is the size of that effect.
- **H2 is Refuted under the preregistered baseline, and Inconclusive otherwise:**

  | frozen baseline | rolling minus frozen, points a year | verdict |
  |---|---|---|
  | **2015–2019 (preregistered)** | **+0.79 (+0.18 to +1.48)** | **Refuted** |
  | 2016–2019 | +0.67 (+0.02 to +1.35) | Refuted, marginally |
  | 2017–2019 | +0.56 (−0.10 to +1.25) | Inconclusive |
  | 2018–2022 | +0.64 (−0.15 to +1.52) | Inconclusive |
  | 2015–2019, coverage sensitivity (preregistered) | +0.54 (−0.11 to +1.23) | Inconclusive |

  The alternative windows are a post-review analysis (`review/reviewer_checks/check5_analysis_replication.json`). In
  no specification does the rolling rule remove *more* trend than the frozen one.
- **The 10-year window** (rule (c), 2025 only) gives a total MED-excluded 2025 index within 1% of the rolling rule's.

![Pooled annual indices](results/figures/F1_indices.png)

![Trends under each rule](results/figures/F2_trends.png)

### The threshold and the excluded days (`results/figures/F3_thresholds.png`)

- **The threshold rose,** from a median 4.0 minutes per customer-day in 2020 to 4.9 in 2025. Most of that rise is the
  five-year window dropping 2015–2016 and taking in 2022–2024, not storms ratcheting it upward: the baseline itself was
  not stationary. Relative to 2017–2019, the median state's typical daily level was −0.26 log points in 2015, −0.06 in
  2016 and −0.12 in 2017, then +0.12 to +0.20 in 2022–2025. A threshold fitted on 2017–2019 is already 5.7% above one
  fitted on 2015–2019, while the 2020–2024 threshold is only 3.7% above the 2017–2019 one.
- **Fewer days were excluded.** The rolling rule excluded fewer days than the frozen rule in every year after 2020:
  - 2023: 8.8 vs 10.2 MEDs per state;
  - 2024: 11.7 vs 13.1;
  - 2025: 7.0 vs 8.5.
- **Decomposition.** Per state, the 2020-to-2025 change in all-events SAIDI is split into three parts:
  - normal-operations growth: median +14 minutes, positive in 20 of 25 states;
  - reclassification as the threshold moves: median +5 minutes;
  - change in the excluded (major-event) part, net of reclassification: median −161 minutes, since 2020 was a heavy
    storm year. This is the residual of the other two, not plan §5's "major-event growth at a fixed 2020
    classification", which is −156; reclassification is a transfer between the two parts.

  Reclassification adds to the normal-operations index rather than subtracting from it.

![Thresholds and major event days](results/figures/F3_thresholds.png)

### Detection power (H3; `results/tables/simulation.json`, `results/figures/F4_power.png`)

| rule | A: normal ops +3%/yr | B: storms +5%/yr | C: no trend |
|---|---|---|---|
| oracle (knows storm days) | 59% | 3% | 4% |
| **rolling 2.5β** | **44%** | **33%** | 5% |
| frozen 2.5β | 36% | 9% | 5% |
| fixed 99th percentile | 25% | 15% | 5% |
| all events | 8% | 16% | 4% |

- **H3 is Refuted.** The rolling rule's power ratio to the oracle is 0.74 (0.70–0.78), far above 0.5. All rules hold
  their nominal 5% false-positive rate under C. Among systems where the trend is detected under A, every normalised
  rule takes a median of five years to first detect it (all events, four).
- **What scenario B measures.** The simulation's "storm" is any day above the 95th percentile of non-zero days. The
  2.5β threshold sits at a median 2.7 times that level, so most simulated storm days — 57–66% — fall *below* the
  threshold, and under IEEE 1366 they are normal operations. The real data look the same: 58% of the top-5% days of
  2015–2019 are below that period's threshold and supply 21% of the MED-excluded index. Scenario B therefore mostly
  grows the number of bad-weather days that every normalised index counts, and the rolling index most, because its
  threshold rises too. Post-review variants (`review/reviewer_checks/check6_simulation_variants.json`) separate the
  mechanisms:
  - growing only storm *size*, at the same frequency: rolling 5%, frozen 4% — no effect beyond nominal;
  - growing only storm *frequency*: rolling 32%, frozen 14%;
  - defining storms as days that would be major events at baseline: rolling 8%, frozen 4%, oracle 4%.

  So the genuine effect of the rising threshold is about 3–4 points above nominal. More sub-threshold bad-weather days
  enter every normalised index, which is how the standard defines normal operations.
- **The tails are heavy.** For 14 of the 25 states, the fitted Pareto tail shape reached the code's cap of 0.9.
  Infinite-variance tails make all-events trends nearly undetectable, matching the 8% power of the all-events index
  under A. The cap does not drive the results: with the shape capped at 0.5, the H3 ratio is 0.76.

![Detection in simulated systems](results/figures/F4_power.png)

### Validation (`primary.json`)

The EIA side is utility SAIDI with major events, customer-weighted within each state, for utilities using the IEEE
method.
- Pooled across 175 state-years (2018–2024), its Spearman correlation with the EAGLE-I all-events index is 0.94 (0.96
  under the coverage sensitivity), well above the preregistered 0.6 bar.
- The stronger test for trends is within states: median Spearman 0.96, none negative, and year-on-year changes in
  the two series correlate at 0.95. The median EAGLE-I level is 1.09 times the utilities'.
- The proxy validates for all-events SAIDI. It does not reproduce the utilities' MED-excluded trend, for the reason
  given under the trends.

## What this does and does not show

- **It shows:**
  - in these 25 states, the standard rolling rule did not remove more of the 2020–2025 trend than a frozen threshold
    would have, though only under the preregistered 2015–2019 baseline;
  - in simulation, the rolling rule keeps about three-quarters of an oracle's power to detect deteriorating normal
    operations, more than the alternatives tested, under every variant tried.
- **It does not show that routine reliability is worsening.** Every MED-excluded index built here rises 2–3% a year,
  but the utilities' own MED-excluded SAIDI for the same states and years is flat. The rise belongs to the
  state-level construct.
- **It does not show that the ratchet critique is wrong in general.** H2's refutation depends on 2015 in the
  baseline, and 2015 has the weakest coverage in the dataset.
- **States are not utilities.** Real thresholds are set per utility on its own daily SAIDI. State aggregation smooths
  days, lowers β and changes which days count as MEDs. The conclusions are about the rule's behaviour on state
  aggregates, not any utility's reported figures.
- **The data are outage maps.** EAGLE-I captures what utilities publish. The coverage sensitivity rescales by covered
  customers only for 2018–2022, the years the coverage history spans; 2015–2017 coverage growth is addressed only by
  the county-count rule, with the limits shown by Nevada. Customers out are snapshots, so outages shorter than 15
  minutes are partly missed.
- **Six annual points** per state; inference is pooled.
- **The NZ external check** named in the lead was descoped in the plan: New Zealand publishes annual, not daily, data.

## Process and deviations

- **Preregistration.** The plan (950d8c0) was committed before any outage series was built. The build, analysis and
  simulation code (e868d1c) was committed before the data finished downloading.
- **D1:** download integrity and the 2023 column name. The first, failed build would have computed 2015–2022 totals in
  memory before stopping at the 2023 column; nothing was written or inspected, and the fix does not change the
  computation.
- **D2 (after independent review):** the Pareto shape cap, which was in the code committed before the data but not in
  the plan; and the post-review analyses and rewording described above. The figure code (`code/figures.py`) was
  written after the results.
- **Review.** An independent adversarial review (`review/review.md`) reproduced every table to machine precision,
  re-derived daily SAIDI exactly from the raw files for eight states, and confirmed the three verdicts as computed.
  It found the narrative unsupported in four places, all corrected here: the storm-leakage reading of scenario B; H2's
  dependence on 2015; the missing comparison with the utilities' MED-excluded SAIDI; and the omitted prior work.

## Reproducing it

`code/fetch.py`, `code/build.py`, `code/analysis.py`, `code/analysis.py coverage`, `code/simulate.py`,
`code/figures.py`. The post-review analyses are `review/reviewer_checks/check5_analysis_replication.py`,
`check6_simulation_variants.py` and `check7_eia_trend_and_2015_zeros.py`.

- **Raw files** are in `data/raw/`, with checksums in `data/raw/SHA256SUMS`.
- **Results** are in `results/tables/`: `primary.json`, `primary_coverage_sensitivity.json`, `state_year.csv`,
  `decomposition.csv` and `simulation.json`.
