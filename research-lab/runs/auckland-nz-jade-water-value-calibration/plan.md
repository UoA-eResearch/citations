# Preregistration: is the Electricity Authority's published water-value model calibrated against what the market then did?

Lead: `auckland-nz-jade-water-value-calibration` (The Energy Movement / Auckland-NZ). Written 2026-10-20, before
any simulated price was compared with any realised price.

**Examined beforehand (no comparison made):** the blob listing of the EMI "Expected water values" dataset (17,991
files, 44.8 GB; 152 weekly runs, 52 in 2023, 52 in 2024, 48 in 2025) and the schema of one `tidy_results.csv`
(2025 Week 20, 88 MB). That file has columns `simulation, stage, year, week, type, name, demand, node, value`
with 91 simulations, stages 0–52, `type` including `prices`, `mwv`, `reslevel`, `total_storage` and `spills`, and
prices reported for nodes HAY, NI and SI in PEAK, SHOULDER and OFFPEAK blocks (42,588 price rows = 91 × 52 × 9).
Stage 1 is the run's own week (Week 20 → 2025 week 20) and stage 2 the following week. Each run also carries its
inputs under `Inputs/data_files/<YYYYMMDDHHMM>/`, which dates the input freeze. No realised price was loaded.

**Novelty** (searches 2026-10-20). The Electricity Authority publishes these weekly JADE runs on EMI, chiefly to
support trading-conduct monitoring, and JADE itself (EPOC, University of Auckland) is open source. An EPOC
workshop presentation describes the publication; an arXiv paper uses the JADE New Zealand dataset for capacity
planning. No published audit of how well the runs' simulated price distributions match what the market then did
was found, and the Authority does not publish one.

## 1. What is being tested

JADE is a stochastic dual dynamic programming model of the New Zealand hydro-thermal system. Each weekly run
simulates forward over 52 weekly stages under 91 historical inflow sequences, producing a distribution of weekly
block prices at HAY, NI and SI. The Authority uses the resulting marginal water values as a benchmark.

The question is narrow and empirical: **when the realised price is compared with the distribution that run
produced, does it fall where the distribution says it should?** This is a calibration audit of a published
official model, not a claim that JADE is wrong for its own purpose (see §5).

**Definitions.**
- **The run's forecast week** is stage 2: stage 1 is the week in which the inputs were frozen and is therefore
  partly elapsed when the run is made, while stage 2 is the first week wholly after the freeze. The freeze
  timestamp from the `Inputs/data_files/<timestamp>/` folder name is recorded for every run and the assumption is
  checked: a run is excluded if its input timestamp is not inside its stage-1 week.
- **Simulated weekly price** for simulation s: the time-weighted average over demand blocks of the stage-2 block
  prices, weighted by that run's own `hours_per_block.csv`.
- **Realised weekly price**: the time-weighted average of EMI final energy prices at HAY2201 over the same seven
  days, using the trading periods actually settled.
- **JADE weeks** map to calendar dates by the convention in the run's own inputs; week 1 begins 1 January. The
  mapping is validated by checking that each run's input timestamp falls inside its stage-1 week before any
  comparison is made.

## 2. Hypotheses

- **H1 (the upper tail is too thin).** Across all usable runs, the realised stage-2 price at HAY2201 exceeds the
  90th percentile of that run's 91 simulated prices in at least 20% of runs, twice the nominal 10%.
  - **Supported** if the 95% lower bound of the exceedance rate is at least 0.20; **Refuted** if its upper bound
    is below 0.20; **Inconclusive** otherwise.
- **H2 (it is worst when storage is low).** Among runs whose national hydro storage at the run start is below its
  historical 20th percentile for that week of the year, the exceedance rate is at least three times the rate among
  the other runs.
  - **Supported** if the 95% lower bound of the ratio is at least 3; **Refuted** if its upper bound is below 3;
    **Inconclusive** otherwise. If either group has fewer than 10 runs, H2 is not scored.

Intervals come from a moving-block bootstrap over runs in calendar order (blocks of 4 consecutive runs, 2,000
resamples, seed 20261020), because consecutive weekly runs share inputs and market conditions.

## 3. Data

- **EMI "Expected water values"**, all weekly runs 2023–2025: `tidy_results.csv` per run, streamed and filtered
  to `prices` and storage rows at stages 0–4 so that only a few megabytes per run are kept; plus each run's
  `hours_per_block.csv` and its input-freeze timestamp.
- **EMI final energy prices**, half-hourly by node, monthly files, for HAY2201 (primary) and BEN2201 and OTA2201
  (reported alongside).
- **EMI Hydrological Modelling Dataset** for national storage and its historical distribution by week of year.

## 4. Analysis

- **Primary:** the stage-2 exceedance rate at HAY2201, with the bootstrap interval, and the same split by storage
  state.
- **Reported alongside:**
  - the probability integral transform: where in its own simulated distribution each realised price fell, as a
    histogram, which shows miscalibration in both tails at once;
  - coverage of the nominal 50%, 80% and 90% central intervals;
  - the lower tail (realised below the simulated 10th percentile);
  - stages 1, 3 and 4, to show how calibration decays with horizon;
  - BEN2201 and OTA2201;
  - the median simulated price against the realised price, which separates bias from spread;
  - the same tests by year, since 2024 included a gas-driven price episode.
- **Minimum detectable effect** for the exceedance rate and the ratio is computed from the bootstrap and reported
  whatever the verdicts.

## 5. Threats and care

1. **JADE is not a price forecaster.** It is a risk-neutral scheduling model run on historical inflow sequences
   with fixed demand and announced outages, published to support water-value benchmarking. Miscalibration against
   realised prices may reflect deliberate simplifications rather than error. The report will say this in the
   verdict itself, not only in the limitations.
2. **The inflow ensemble is historical.** Ninety-one sequences cannot represent fuel-price shocks, outages or
   strategic offering, so the upper tail may be thin by construction. That is the point of measuring it, but it is
   not evidence of a modelling mistake.
3. **Node choice.** HAY2201 is the reference node for the model's HAY output; Otahuhu is reported because it is
   Auckland's reference node.
4. **Week alignment** is the main mechanical risk and is validated before any comparison, as in §1.
5. **Revisions.** Final energy prices can be revised; the latest published monthly file is used and the retrieval
   date recorded.
6. **No personal or community data**: market prices, model outputs and reservoir levels only.
