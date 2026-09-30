# Preregistration: does the moisture assumption change AI-forecast attribution of humid heat?

Lead: `climate-earth-ai-humid-heat-attribution` (research-lab/leads.json). Written 2026-10-01 and committed to git before
any event was selected, any initial condition was built, or any forecast was run.

Probes made before writing:

- **Literature search** (§1).
- **ARCO-ERA5** (Google public bucket): confirmed that every field AIFS needs is present; timed one field read.
- **CMIP6 on the Pangeo public bucket:** listed models with the needed monthly fields (31 have `ta`, `hus`, `tas`,
  `huss` and `ts` in historical and SSP2-4.5, r1i1p1f1).
- **AIFS Single v1.0** (ECMWF, Hugging Face, CC BY 4.0): downloaded the checkpoint and read its variable list. It
  forecasts 2 m dewpoint (`2d`), unlike Pangu-Weather and GraphCast.
- **A memory probe** on a synthetic state ran out of memory with the shared vLLM server resident. Forecasts will run
  with vLLM stopped and then restarted, as the user has authorised.

No ERA5 value for any candidate event has been examined. Every later departure goes to `deviations.md` with a timestamp
taken from `date`.

## 1. Background and gap

- **Forecast-based attribution.** Heatwaves can be re-forecast from initial conditions with the climate-change signal
  removed, in physics models (Leach et al. 2021, 2024) and in AI weather models (Jiménez-Esteve et al. 2025, Earth's
  Future; FourCastNet-v2, Pangu-Weather, NeuralGCM).
- **Humid heat is the harder case.** Wet-bulb temperature (TW) sets the limit of human heat tolerance (Raymond et al.
  2020; Vecellio et al. 2022). A counterfactual for humid heat must remove moisture as well as heat, and how to do so
  is contested:
  - hold specific humidity fixed (temperature-only);
  - hold relative humidity fixed (Clausius–Clapeyron scaling).
- **The gap.** Statistical rapid attribution of humid heat exists (ERL 2026, ERA5 and CMIP6). No AI-forecast
  attribution of wet-bulb extremes, and no test of how the moisture treatment changes it, was found.
- **Why AIFS.** Most AI weather models lack a surface humidity variable, so surface TW cannot be computed from them.
  AIFS Single v1.0 forecasts 2 m dewpoint.

## 2. Events (selected by rule, from ERA5 only)

- **Regions** (boxes, land and sea points):
  - South Asia: 22–32°N, 68–88°E;
  - Persian Gulf: 23–31°N, 47–57°E;
  - US Gulf coast: 27–33°N, 97–81°W.
- **Window.** May–September of 2023, 2024 and 2025.
- **Metric.** The daily event TW is the regional maximum of 2 m TW at 06, 12 and 18 UTC. TW comes from ERA5 `2t`,
  `2d` and `sp`, by the psychrometric equation (§4).
- **Selection.** Per region, the two days with the highest daily event TW that fall in different years: 6 events.

## 3. Forecasts

- **Model.** AIFS Single v1.0 through anemoi-inference 0.4.9, 6-hourly steps, on an NVIDIA A100 80 GB.
- **Initial conditions.** ERA5 from ARCO-ERA5 at 00 UTC on event day − L, for L ∈ {2, 4, 6} days, plus 18 UTC the
  day before. They are regridded from 0.25° to N320 with earthkit-regrid, and geopotential height is converted to
  geopotential as in ECMWF's example notebook.
- **Worlds**, per event and lead:
  - **F (factual):** unmodified ERA5.
  - **A (temperature only):** subtract the warming signal ΔT from `t` at all 13 levels, `2t`, `skt`, `stl1` and `stl2`.
    Specific humidity and `2d` are unchanged, capped at saturation.
  - **B (constant relative humidity):** as A, but specific humidity at every level is rescaled so that relative
    humidity is unchanged. `2d` is recomputed to keep 2 m relative humidity, and `tcw` is rescaled by the column
    change in q.
  - In A and B, geopotential at every level is recomputed hydrostatically from the virtual-temperature change, with
    surface pressure and mean-sea-level pressure unchanged.
- **Warming signal ΔT.** Per CMIP6 model: the event month's monthly climatology for 2014–2033 (historical 2014 plus
  SSP2-4.5 2015–2033) minus 1850–1900 (historical), r1i1p1f1.
  - `ta` at the 13 AIFS levels; `tas` for `2t` and soil temperatures; `ts` for `skt`.
  - Interpolated bilinearly to the N320 points.
  - Six models: the first six alphabetically among those with all five variables in both experiments.
  - Each model gives one counterfactual member.
- **Size.** 6 events × 3 leads × (1 factual + 6 A + 6 B) = 234 forecasts, each run to the end of the event day.

## 4. Quantities

- **Wet-bulb temperature.** 2 m TW from `2t`, `2d` and `sp`, by solving the psychrometric equation with Bolton (1980)
  saturation vapour pressure (Newton iteration, tolerance 1e-4 K).
- **Event-peak TW.** The regional maximum of TW at 06, 12 and 18 UTC on the event day.
- **Area-mean TW** (secondary). The land-point regional mean of the event-day maximum TW.
- **Attributable change.** ΔTW_A = TW_F − TW_A and ΔTW_B = TW_F − TW_B, per member.
- **Static change.** The same deltas applied offline to ERA5 fields at the event time, with no forecast.

## 5. Hypotheses and tests

- **H1 (primary, from the lead).** Moisture scaling raises the attributable change: R = mean ΔTW_B / mean ΔTW_A ≥ 1.5,
  pooled over events, leads and members.
  - 95% interval: a two-level bootstrap, events then members within event, 5,000 draws.
  - Supported if R ≥ 1.5 and lower bound > 1. Contradicted if upper bound < 1.5. Otherwise inconclusive.
- **H2.** The AI forecast carries the imposed thermodynamic signal: the dynamic/static ratio D = ΔTW_B(forecast) /
  ΔTW_B(static), at lead 2 days.
  - Consistent if the 95% interval lies within [0.75, 1.25]; damped if the upper bound < 0.75; amplified if the lower
    bound > 1.25. Otherwise inconclusive.
- **H3** (descriptive). ΔTW_B and ΔTW_A as functions of lead, 2 to 6 days.

## 6. Validation

- **V1, factual skill.** The error of the factual forecast's event-peak TW against ERA5, per lead. If the lead-2 absolute
  error exceeds 2 °C in more than half of the events, the attribution is reported as limited by forecast skill.
- **V2, drift check.** The global-mean 2 m temperature difference F − B at the end of each forecast, against the imposed
  global-mean ΔT: this shows whether the model retains or erases the perturbation.
- **V3, consistency check.** With zero deltas, the counterfactual pipeline must reproduce the factual forecast exactly.

## 7. Reporting

- An independent reviewer agent checks code, deviations and the draft before any verdict is stated.
- The report opens with an "In plain terms" section.
- ERA5, CMIP6 and AIFS are open. Only derived tables and figures are committed.
- The vLLM server is stopped only for the forecast batch and restarted immediately after. The restart is verified
  and logged.
