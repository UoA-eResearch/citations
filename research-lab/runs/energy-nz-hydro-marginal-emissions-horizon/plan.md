# Preregistration: does carbon-aware load shifting cut emissions in New Zealand's hydro-dominated grid?

Lead: `energy-nz-hydro-marginal-emissions-horizon` (Energy / Sustainability). Written 2026-10-18, before any
generation, demand or emissions series was downloaded.

**Examined beforehand (no estimate computed):**
- one month of EMI `Generation_MD` (July 2024): its format (kWh per trading period, by unit, with fuel codes) and the
  list of thermal and geothermal units;
- the EMI dataset listings: `Grid_export`, `Grid_export_to_Tiwai`, `HVDC_Flows`, and the Hydrological Modelling
  Dataset (storage and flows to 2024-12-31);
- one Open-Meteo archive response, for format.

**Novelty** (search 2026-10-18). No published horizon-resolved marginal emissions factor (MEF) for New Zealand was
found. The closest work:
- marginal-generator shares from the Electricity Authority (hydro or thermal is marginal about 95% of the time);
- a 2026 *Energies* paper on state-dependent merit-order price effects;
- WattTime's explainer that reservoir hydro moves emissions in time;
- hydrothermal marginal-CO2 modelling for Chile (Applied Energy 2017).

## 1. Question and hypotheses

Carbon-aware schedulers move flexible load to hours when the grid's **average** emissions factor (AEF) is low. In a
grid where reservoir hydro balances most short-run changes in demand, an extra MWh in one hour may be met by water
that would otherwise have been used later. Its emissions then arrive days or weeks later, when thermal plant makes up
the water. The emissions that a load shift really changes therefore depend on the **horizon** over which they are
counted.

**Estimand.** MEF(h) is the change in national electricity-generation CO2 over the window [t, t+h] per MWh of extra
demand in that window, for demand moved by weather (§4).

**Hypotheses:**
- **H1 (horizon gradient).** MEF rises with horizon: MEF(30 d) − MEF(1 h) > 0.
  - Supported: the 95% lower bound of the difference is > 0.
  - Refuted: the upper bound is < 0.
  - Inconclusive otherwise.
- **H2 (intraday shifting captures little).** A 20 MW deferrable load, scheduled each day into the lowest-AEF hours
  within a 24-hour window, achieves less than half the saving the AEF signal claims, when the saving is scored with
  time-of-day MEFs at the 1-day horizon (§5). The measure is the capture ratio.
  - Supported: the upper bound is < 0.5.
  - Refuted: the lower bound is ≥ 0.5.
  - Inconclusive otherwise.
- **H3 (storage state).** MEF(1 d) is higher when national hydro storage is in its lowest tercile (relative to the
  day-of-year mean) than in its highest tercile.
  - Supported: the lower bound of the difference is > 0.
  - Refuted: the upper bound is < 0.
  - Inconclusive otherwise.

## 2. Data (all open), 2015-01-01 to 2024-12-31

The window ends where the Hydrological Modelling Dataset's storage series ends.

- **EMI Generation_MD.** Half-hourly metered generation by unit, in kWh per trading period (TP), with fuel codes:
  - thermal: coal (Huntly Rankine units), gas, diesel;
  - also geothermal, hydro, wind, solar and wood.
- **EMI metered data:**
  - `Grid_export`, total grid offtake. The demand measure is total grid generation; 2024 grid export is a check on it;
  - `Grid_export_to_Tiwai`;
  - `HVDC_Flows`.
- **EMI Hydrological Modelling Dataset** (to 2024-12-31):
  - daily controlled storage of the main reservoirs, summed to national storage in GWh with the dataset's specific
    yields;
  - tributary inflows, summed to national daily inflow.
- **Temperature.** Open-Meteo historical archive (ERA5-based), hourly 2 m temperature at Auckland, Hamilton,
  Wellington, Christchurch and Dunedin, weighted by 2023 urban-area population.
- **Emissions calibration.**
  - MBIE's quarterly electricity-generation emissions by fuel (New Zealand Energy Quarterly data tables);
  - MfE fuel emission factors;
  - published unit heat rates (MBIE/EA thermal assumptions);
  - geothermal field factors (MfE).

## 3. The emissions ledger (`code/ledger.py`)

1. **Unit emissions.** E_u,t = heat rate_u × fuel factor_u × G_u,t.
   - The Huntly Rankine units burn coal and gas but are coded "coal". Their factor is a blend, set each quarter so
     the ledger's coal and gas totals reproduce MBIE's fuel split.
2. **Calibration.** Each quarter, one scale factor per fuel brings the ledger's total to MBIE's quarterly
   electricity-generation emissions for that fuel. The uncalibrated scale factors are reported; they should be near 1.
3. **AEF.** AEF_t = E_t / D_t, where E_t is total emissions and D_t is total grid generation in TP t. This is the
   signal a carbon-aware scheduler would consume.

## 4. Estimation (`code/mef.py`)

**Instrument.** The weather-driven demand shock z_t is the population-weighted heating-degree anomaly:
- heating degrees are max(0, 16 °C − T);
- the anomaly is taken against the TP-by-day-of-year climatology of 2015–2024, smoothed with a 15-day window.

Cold anomalies raise demand. They do not dispatch thermal plant except through demand, once the controls below are
included.

**Horizon-h cumulative regression, 2SLS:**

Σ_{j=0}^{h−1} E_{t+j} = α + MEF(h) · Σ_{j=0}^{h−1} D_{t+j} + controls + ε,

with Σ D instrumented by z_t.

- **Horizons** h (in TPs): 1, 2, 4, 8, 24, 48, 96, 336, 672, 1440. That is 0.5 h, 1 h, 2 h, 4 h, 12 h, 1 d,
  2 d, 7 d, 14 d and 30 d.
- **Controls:**
  - z_{t−1…t−48} (the previous day's anomalies, as 4 six-hour means);
  - lagged D, E and storage;
  - the previous 7 days' inflow;
  - the previous day's HVDC transfer and Tiwai offtake;
  - **cumulative wind generation over the same window.** Wind is weather-driven and is not caused by demand
    (curtailment is negligible), so it is held fixed. This blocks the cold-and-windy channel.
  - fixed effects: TP × day type (weekday, Saturday, Sunday/holiday), month-of-year, and year.

**Inference.**
- Controls are partialled out once on the full sample (Frisch–Waugh–Lovell).
- A calendar-month block bootstrap (999 resamples, seed 20261018) then gives intervals for each MEF(h), the H1
  difference, and the H2/H3 quantities.
- First-stage F statistics are reported per horizon. If the first-stage F is below 10 at a horizon, MEF at that
  horizon is reported as weakly identified, and a hypothesis that uses it is Inconclusive.

**Time-of-day MEFs (for H2).** The instrumented demand is interacted with four 6-hour blocks of the window's start
time (00–06, 06–12, 12–18, 18–24), each with its own block-specific heating-degree instrument. This is done at
h = 48 TPs (1 day).

**State dependence (H3).** The same h = 48 regression, split by the storage tercile of day t−1. Storage is relative
to the day-of-year mean, with terciles over 2015–2024.

**Secondary estimator.** OLS of the cumulative E on the cumulative residual demand innovation (D minus its
temperature-and-calendar prediction), as in the lead. It is reported beside the 2SLS.

## 5. The scheduling simulation (`code/simulate.py`)

**The load.**
- 20 MW runs for 4 h each day. Its default window is 10:00–14:00.
- A 24-hour-window scheduler moves it each day to the 8 consecutive TPs of lowest AEF.
- Variants: a 1-hour window (shift within ±1 h of the default) and a 7-day window (move the week's 28 load-hours to
  the week's lowest-AEF TPs).

**Scoring.**
- **Claimed saving:** Σ (AEF_default − AEF_scheduled) × MWh moved.
- **Realised saving:** Σ (MEF_block(default) − MEF_block(scheduled)) × MWh moved, using the time-of-day MEFs at 1 day.
  For the 7-day variant it uses MEF(7 d) by block if identified.

**Outputs.**
- the capture ratio = realised / claimed, with bootstrap intervals over the MEF draws;
- the share of days on which the realised saving has the opposite sign from the claimed one.

## 6. Checks and descriptives

- **Energy balance.** At short horizons, the responses of hydro + thermal + geothermal generation to instrumented
  demand should sum to about 1 per MWh of demand.
- **Placebo outcome.** The geothermal generation response should be about 0 at every horizon. If its interval
  excludes ±0.05 MWh/MWh, the instrument is flagged.
- **Ledger reconciliation.** The uncalibrated/calibrated ratio by quarter and fuel.
- **Tiwai (descriptive only).** Smelter demand-response episodes are identified from `Grid_export_to_Tiwai` as drops
  of at least 100 MW sustained for at least 7 days. Thermal generation and AEF around them are shown, with the
  dry-year confounding stated. They are called in dry spells by design, so they cannot be read causally.
- **Descoped from the lead:**
  - the Australian NEM placebo: the unit-level SCADA archive is hundreds of GB, and the internal geothermal placebo
    is used instead;
  - the Tiwai event study as an identification strategy: confounded by design, so it is descriptive.

## 7. Threats and care

1. **Exclusion.** Cold weather may also change inflows (snow) and wind. Wind is controlled over the window, and
   inflows by lag. Snow storage over 30 days cannot be fully controlled. This is stated, and the 30-day MEF is read
   with it.
2. **Strategic water management.** Hydro operators respond to expected future demand. A weather shock that persists
   is partly anticipated. The estimand counts the system's actual response to weather-driven demand, including that
   anticipation, which is the response a scheduler's extra load would also meet.
3. **Ledger accuracy.** Unit heat rates vary with load. Quarterly calibration fixes totals, not within-quarter
   variation. The MEF depends on the thermal response, which is dominated by the Huntly units, whose factors are
   calibrated.
4. **Units of analysis.** These are plants and system totals. No person or community is studied.
