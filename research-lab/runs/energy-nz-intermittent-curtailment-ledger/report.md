# How much New Zealand wind and solar output is curtailed? Measured from the plants' own forecasts, the answer is mostly noise, with a growing price-driven core

*Every offered wind and solar plant in New Zealand, January 2020 to September 2026: each half-hour's
dispatch-time forecast of generation potential, from the plant's own offers, set against its metered output and the
price at its node, to build the country's first curtailment ledger.*

**Verdict: not reliably measurable from offers alone, by the study's own preregistered gate.** In 2025/26 the
median plant's detection floor, the size of gap that forecast error alone produces, is 27% of its mean potential,
above the 25% gate. By their rules, H1 is Refuted and H2 Supported. But both readings are dominated by forecast noise,
which the preregistered measure counts by construction. The clearest real signal is curtailment in half-hours when
the node price was at or below the plant's own offer price. It rose from almost nothing in 2020 to **2.2% of
available wind and solar energy in 2025/26**.

- **H1 (curtailment rose from below 0.5% in 2020 to at least 2.0% in 2025/26): Refuted by its rule.** The measure
  reads 2.27% in 2020 (95% interval 2.13–2.42%) and 5.20% in 2025/26 (4.36–6.32%). The 2020 value is almost entirely
  the noise mass the rule flags by construction (2.22 of the 2.27 percentage points), so the refutation reflects the
  measure's floor rather than real curtailment in 2020.
- **H2 (at least half of 2025/26 curtailment happens when prices exceed $0.01/MWh, i.e. is not price-driven):
  Supported by its rule, but reversed once the noise is removed.** 72.7% (64.1–82.3%) of the measured curtailed
  energy falls in such half-hours, but half of the measured total is the noise mass, which sits in unconstrained
  half-hours by definition. Of the curtailment outside that mass (126 GWh, 3.0% of available energy), 73% occurs when
  the price was at or below the plant's own offer.

## In plain terms

When there is more wind or sun than the grid can use or wants to pay for, wind and solar farms are turned down or
switched off. That is "curtailment". Other countries publish how much of it happens; New Zealand does not. We tried
to measure it.

Every wind and solar farm tells the market, every half-hour, how much it could generate. We compared that with
what each farm actually produced. In principle, the difference is curtailment.

In practice, the farms' forecasts are off by a lot even when nothing is holding them back, and our method counted
some of that forecasting error as curtailment. By the test we set ourselves in advance, we cannot measure
curtailment reliably this way.

One part is clear, though. Sometimes the price at a farm's connection falls to or below the price it asked for.
Then it is turned down because the power is not wanted. That kind of curtailment was almost nil in 2020. In the year
to June 2026 it reached about 2% of everything the wind and solar farms could have produced. It comes in spells,
with big ones in 2022 and in late 2025.

## What was asked

New Zealand's wind and solar build-out is accelerating, and the Electricity Authority is changing how intermittent
generators share reserve costs, but no curtailment statistic exists. The preregistration (`plan.md`) asked two
questions:
- **H1:** did curtailment grow from under 0.5% of available energy in 2020 to at least 2.0% in the 12 months to
  June 2026?
- **H2:** is at least half of it not price-driven, i.e. does it happen when the node price exceeds $0.01/MWh?

It also set a gate: if forecast error swamps the signal, say so whatever H1 and H2 return.

## How it was done

**Data.** All from the Electricity Authority's EMI service:
- daily offer files, about 170 GB, streamed and filtered to wind and solar energy offers;
- half-hourly metered output by generator (Generation_MD);
- final prices by node.

25 points of connection were matched: 15 wind, 10 solar. Mahinerangi wind farm has no matching metered generator,
and Rotohiko is a battery, so both are excluded.

**Measure** (plan section 1).
- **Potential** is the plant's latest dispatch-time forecast.
- **Unconstrained half-hours** are those in which the price exceeded every price the plant offered at by $1 or
  more, and the plant offered at least its potential.
- **Bias correction.** Per plant and quarter, the potential is scaled by the median ratio of output to potential in
  unconstrained half-hours.
- **Curtailed half-hours** are those whose gap (scaled potential minus output) exceeds the plant-quarter's 95th
  percentile of unconstrained gaps; curtailed energy sums those gaps.
- **Intervals** come from a 7-day block bootstrap with the calibration re-estimated in every resample.

## Results

### The measure and its floor (`results/figures/F1_windows.png`)

![By 12-month window](results/figures/F1_windows.png)

| | 2020 | 2025/26 |
|---|---|---|
| available energy (bias-corrected potential) | 2,128 GWh | 4,171 GWh |
| preregistered curtailed share | **2.27%** (2.13–2.42) | **5.20%** (4.36–6.32) |
| … in unconstrained half-hours (noise by construction) | 2.22% | 2.17% |
| … at or below the plant's own offer price (price-driven) | 0.02% | **2.22%** |
| … other flagged half-hours | 0.03% | 0.79% |
| non-price share of curtailed energy (H2) | 99% | 72.7% (64.1–82.3) |

**The noise mass.** The rule flags a half-hour when its gap exceeds the 95th percentile of gaps in unconstrained
half-hours, and it counts unconstrained half-hours too. So it flags about 5% of them by construction: 5.0% in 2020,
4.7% in 2025/26. Their gaps are forecast error. That mass is about 2.2% of available energy in both periods, a floor
under the measure, and it is what makes the 2020 baseline 2.27% rather than near zero.

**Above the floor.** In half-hours where the price was at or below the plant's offer, 18% were flagged in 2025/26,
nearly four times the noise rate, so most of that mass is real. Price-driven curtailment by 12-month window:

| window | price-driven share of available energy | half-hours at or below the offer price |
|---|---|---|
| Jan 2020–Jun 2021 | 0.01% | 0.4% |
| Jul 2021–Jun 2022 | 0.23% | 1.5% |
| Jul 2022–Jun 2023 | 1.10% | 4.2% |
| Jul 2023–Jun 2024 | 0.07% | 0.4% |
| Jul 2024–Jun 2025 | 0.77% | 2.6% |
| Jul 2025–Jun 2026 | **2.22%** | **7.0%** |

![Monthly price-driven curtailment](results/figures/F3_monthly_price_driven.png)

### The gate (`results/figures/F2_gate.png`)

![Detection floor by plant](results/figures/F2_gate.png)

The median plant's floor is 27% of its mean potential in 2025/26 (gate 25%). Wind plants range from 22% to 60%
(median about 27%). Solar plants sit higher, partly because their mean potential includes nights. **The gate fails.**

### Robustness (`results/tables/robustness.json`)

| variant | 2020 | 2025/26 |
|---|---|---|
| preregistered | 2.27% | 5.20% |
| only the gap above the floor counted | 0.84% | 2.72% |
| floor at the 99th percentile | 0.76% | 3.01% |
| floor at the 90th percentile | 3.41% | 6.49% |
| no bias correction | 2.28% | 5.58% |
| unconstrained requires a $10 margin | 2.26% | 5.43% |
| plant-quarters with partial metering dropped (k < 0.5) | 2.27% | 5.19% |
| wind only | 2.27% | 5.11% |
| each plant left out (2025/26 range) | — | 3.80% (without Turitea) to 5.67% (without Harapaki) |

- The offered maximum output, a planned alternative to the potential forecast, is empty for these plants, so that
  variant cannot be run.
- Before and after real-time pricing (November 2022) the measure reads 2.91% and 3.95%.
- The potential forecasts track ERA5 weather at most plants: correlations of 0.44–0.85 with 100 m wind speed or
  solar radiation. Two new solar farms are lower (Dannevirke 0.14, Tauhei 0.07).

**Projection, frozen for scoring after June 2027.** By the preregistered rule (the 2025/26 share scaled by projected
available energy from plants operating by September 2026), the measure would read **5.65%** for the 12 months to
June 2027. Given the floor, the price-driven component is the more useful thing to watch; it is not projected here.

## What this does and does not show

- **It shows** that price-driven curtailment of New Zealand's wind and solar has become material. These are
  half-hours in which the plant's node price fell to or below its own offer, and its output fell short of its
  forecast potential by more than forecast error usually does. They were almost absent in 2020 and reached about
  2.2% of available energy in 2025/26, in spells.
- **It does not provide** a reliable all-cause curtailment statistic. The plants' own potential forecasts err by
  more than a quarter of their mean output at the 95th percentile, and the preregistered measure folds that error
  in. A better measure would compare constrained half-hours with forecast-matched unconstrained ones, or use the
  system operator's dispatch records.
- **It does not show** that most curtailment is network- or security-constrained. Once the noise mass is set aside,
  most identifiable curtailment is price-driven.
- **Caveats.**
  - The price-driven class also contains some noise, at roughly the 5% base rate.
  - "Price at or below the offer" is an economic condition, so this class mixes market-driven spill with
    constraints that drive the local price down.
  - Partial metering at some new plants is absorbed by the bias correction.
  - One day (31 August 2026) is not published.

## Process and deviations

- **Preregistration.** `plan.md` was committed before any series was built. It fixed a 2020 baseline, since the
  potential field is empty before late 2019. The fetch, build and analysis code were committed before their outputs.
- **Deviations** (`deviations.md`):
  - D1, before any series was built: an unpublished day; December 2025 prices assembled from daily files; generation
    column-name case; the two fuel codings that had left out ten newer plants; partial metering, with a variant
    added.
  - D2 records the failed gate and the post hoc decomposition (`code/diagnostics.py`), written after seeing the
    results.

## Reproducing it

`code/fetch.py`, `code/build.py`, `code/analysis.py`, `code/diagnostics.py`, `code/figures.py`.

- **Inputs** are public EMI files from the Azure blob store, plus Open-Meteo ERA5.
- **Results** are in `results/tables/`: `primary.json`, `robustness.json`, `diagnostics.json`, `ledger_monthly.csv`
  (the open ledger by plant and month), `build_log.json` and `output_validation_monthly.csv`.
