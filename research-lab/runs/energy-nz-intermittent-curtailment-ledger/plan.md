# Preregistration: how much New Zealand wind and solar output is curtailed, and why?

Lead: `energy-nz-intermittent-curtailment-ledger` (The Energy Movement). Written 2026-10-21, before any curtailment
series was built and before any output was compared with any forecast.

**Examined beforehand (nothing estimated):**
- The column layout of EMI daily offer files, and which units carry a value in `ForecastOfGenerationPotentialMegawatts`
  on single sample days. The field is empty for every unit on 15 January and 15 July 2019. It is filled for eight
  wind farms on 15 January 2020 (Mahinerangi, Mill Creek, Te Rere Hau, Te Āpiti, Tuku, Tararua, White Hill, West
  Wind), nine from January 2021 (Waipipi), and ten by mid-2022 (Turitea).
- The headers of the Generation_MD and FinalEnergyPrices files.
- Download speed: the EMI Azure blob store serves about 0.5 MB/s per connection and scales with parallel
  connections.

**Novelty** (searches 2026-10-21, web and OpenAlex, including Electricity Authority, Eye on Electricity and
Transpower material). No New Zealand curtailment statistic or estimate was found. The method follows offer-based
curtailment studies elsewhere (MISO economic maximum minus dispatch; potential-minus-output in Germany, with potential
from reanalysis rather than the plant's own forecast).

## 1. What is measured

For each wind or solar unit and half-hour trading period (TP):

- **Potential** *P*: the latest submitted `ForecastOfGenerationPotentialMegawatts` (rows with `IsLatestYesNo = Y`).
- **Output** *G*: metered generation (Generation_MD, kWh per TP, × 2 for average MW), matched to the unit by point of
  connection and fuel.
- **Price**: the final energy price at the unit's node (FinalEnergyPrices, or NodalPricesAndVolumes where the former
  does not reach back).
- **Offer**: the unit's offered tranches (MW, $/MWh) for the TP, and their sum.

**Unconstrained TPs** are those in which nothing in the market should hold the unit below its potential:
- the node price exceeds every price at which the unit offered MW, by at least $1/MWh;
- the node price is at least $1/MWh;
- the unit offered at least its potential.

**Bias correction.** The potential forecast is the plant's own submission and may be biased. Per unit and calendar
quarter, a scale *k* = median(*G*/*P*) is taken over unconstrained TPs with *P* at least 10% of the unit's maximum
offered MW, and *P̂* = *k*·*P*.

**Detection floor.** The gap is *g* = *P̂* − *G* (MW). The floor *f* is the 95th percentile of *g* on that unit-quarter's
unconstrained TPs. A TP is **curtailed** when *g* > *f*. Curtailed energy is the sum of *g* × 0.5 h over curtailed TPs;
available energy is the sum of *P̂* × 0.5 h over all TPs. A unit-quarter with fewer than 200 unconstrained TPs is
pooled with its unit-year.

**Cause** of each curtailed TP (descriptive):
- *offer-limited*: the unit offered less than *P̂*;
- *price-driven*: the node price is at or below the highest price at which the unit offered MW;
- *other*: neither, i.e. the unit offered its potential at prices below the node price and still produced less.

## 2. Data

- **Offers**: EMI daily files, 1 August 2019 to 30 September 2026, streamed from the blob store. Only energy rows for
  units that ever carry a potential forecast are kept, latest submissions only; raw files are discarded after
  filtering.
- **Output**: Generation_MD monthly files, same period; fuel codes identify wind and solar.
- **Prices**: FinalEnergyPrices (monthly) for the same period, at the units' nodes.
- **Weather** (secondary): Open-Meteo ERA5 hourly 100 m wind speed and shortwave radiation at each plant.
- The first full calendar year with potential forecasts, **2020**, is the baseline. The lead proposed 2019, but the
  field is empty for most or all of 2019.

## 3. Hypotheses

Shares are curtailed energy divided by available energy, over all wind and solar units carrying a potential forecast.
Intervals come from a moving-block bootstrap over days (7-day blocks, 2,000 resamples, seed 20261021), with *k* and *f*
re-estimated in each resample.

- **H1 (curtailment has grown to a material level):** the share is below **0.5%** in calendar 2020 and at least
  **2.0%** in the 12 months to 30 June 2026.
  - *Supported* if both point estimates meet their thresholds and the interval for the increase excludes zero.
  - *Refuted* if the 2025/26 interval lies wholly below 2.0%, or the 2020 interval wholly above 0.5%.
  - *Inconclusive* otherwise.
- **H2 (most curtailment is not price-driven):** at least **50%** of curtailed energy in the 12 months to 30 June
  2026 occurs in TPs whose node price exceeds $0.01/MWh.
  - *Supported* if the estimate is at least 50% and its interval lies above 40%.
  - *Refuted* if the interval lies wholly below 50%.
  - *Inconclusive* otherwise.

**Measurability gate.** If, in 2025/26, the median unit's detection floor exceeds 25% of its mean potential, the
report states that curtailment is not reliably measurable from offers alone, whatever H1 and H2 return.

## 4. Secondary and robustness, fixed in advance

- **Validation of output totals**: the matched wind and solar output summed by month against Generation_MD fuel
  totals; units that cannot be matched are listed.
- **Variants**:
  - offered `MaximumOutputMegawatts` instead of the potential forecast;
  - no bias correction (*k* = 1);
  - curtailed energy counted above the floor only (*g* − *f*);
  - floor at the 90th and 99th percentiles;
  - unconstrained TPs requiring a $10/MWh margin;
  - each unit left out in turn;
  - wind only.
- **Regime break**: the share before and after real-time pricing (1 November 2022), reported separately.
- **Weather check**: correlation of *P* with ERA5 wind speed (wind) and radiation (solar) on unconstrained TPs, by
  unit, as a plausibility check on the forecasts.
- **Ledger and projection**: monthly curtailment by unit, island and cause, published as a table. A projection for
  the 12 months to 30 June 2027 is frozen in the report: the 2025/26 share times the ratio of available energy
  projected from units commissioned by 30 September 2026. It is scored after June 2027.

## 5. Threats and care

- **Forecast error is not curtailment.** The bias correction and floor are the study's defence. If they are too
  loose, the share is inflated; too tight, deflated. The variants bracket this, and the measurability gate states when
  the floor swamps the signal.
- **Strategic forecasts.** A plant could submit high potentials. Weather correlation and per-unit leave-outs expose
  outliers.
- **Matching.** Offer units and metered generators are matched by point of connection; shared or renamed points are
  listed.
- **Regime changes.** Real-time pricing (November 2022) and Code changes alter offers mid-sample; they are reported,
  not smoothed.
- **Few solar plants and short histories.** The solar component is reported separately and not over-read.
- Any departure from this plan will be logged in `deviations.md` before the affected result is read.
