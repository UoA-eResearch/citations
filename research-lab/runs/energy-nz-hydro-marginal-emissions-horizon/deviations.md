# Deviations from plan.md

Timestamps are Pacific/Auckland, from `date`.

## D1 — 2026-10-18 15:29 NZDT — ledger calibration source and stated ledger assumptions (before any emissions series was computed)

**Calibration source.** MBIE's quarterly electricity-emissions tables sit behind bot protection that refuses scripted
download, and so does the MBIE PDF. The ledger is therefore calibrated **annually**:
- **target:** the Ministry for the Environment's annual grid-average CO2 factor for purchased electricity (kg CO2 per
  kWh generated, 2015–2024, from `emission_factors_2026_v2_long.csv`, the CO2 component);
- **method:** one scale factor per year on fossil emissions, so that ledger CO2 over total metered generation equals
  that factor;
- **check:** MfE's quarterly factors (2023–2024) are compared with the ledger, not used to fit it.

**Ledger assumptions** (`code/series.py`), fixed before any series was built:
- **Fuel factors.** Natural gas 54.14 kg CO2/GJ (MfE). Sub-bituminous coal 1.991 kg CO2/kg (MfE) at 21.5 GJ/t,
  which gives 92.6 kg/GJ. Diesel 2.660 kg CO2/L (MfE) at 38.4 MJ/L, which gives 69.3 kg/GJ.
- **Heat rates (GJ/MWh):**

  | Unit | Heat rate |
  |---|---|
  | Huntly Rankine (`huntly_1_4`, coal) | 10.3 |
  | Huntly e3p (CCGT) | 7.2 |
  | Huntly P40 (OCGT) | 9.6 |
  | Ōtāhuhu B (CCGT) | 7.0 |
  | Southdown | 8.0 |
  | Stratford (TCC CCGT plus peakers, metered together) | 8.0 |
  | McKee | 9.5 |
  | Junction Road | 9.5 |
  | Te Rapa, Kapuni, Whareroa (gas cogeneration, electricity share) | 6.0 |
  | Whirinaki (diesel) | 11.0 |

- **Zero-emission units in the ledger:**
  - Glenbrook (waste-heat cogeneration; its emissions belong to steelmaking);
  - Kinleith (wood, biogenic).
- **Geothermal.** A flat 0.10 t CO2/MWh. This is the order of the inventory's geothermal fugitive emissions divided by
  geothermal generation.
- **Sensitivities:**
  - geothermal factor 0.05 and 0.15 t/MWh;
  - a Huntly Rankine fuel split of 70% coal / 30% gas by energy, instead of all coal.

The MEF hypotheses compare thermal responses across horizons, times of day and storage states, so a uniform scale
error cancels in their signs and in the H2 ratio. The fuel split and the geothermal factor are bracketed by the
sensitivities.

**Inflow series** (fixed at the same time). The plan's "tributary inflows, summed" is implemented as the HMD natural
inflow to each controlled lake, converted to energy:

  m³/s × 86,400 / 10⁶ × the lake's specific energy (GWh per Mm³, from the HMD capacity series).

- **Lakes:** Taupō, Waikaremoana, Tekapo, Pukaki, Ōhau, Hāwea, Wānaka, Manapōuri and Te Anau.
- **Why:** unweighted sums of m³/s across rivers with very different downstream heads would not measure the
  energy arriving.
- **Population weights for temperature** (approximate 2023 populations, millions): Auckland 1.70, Hamilton 0.18,
  Wellington (city, Hutt, Porirua) 0.42, Christchurch 0.39, Dunedin 0.13.

## D2 — 2026-10-18 16:31 NZDT — after the independent review (fix first): sensitivity analyses and disclosures; the preregistered pipeline and its results are unchanged

**New: `code/sensitivity.py`** (exploratory, not preregistered) and `results/tables/sensitivity.json`. On the same
common sample, they re-estimate MEF at 1 h, 1 d and 7 d under:
- **seven control sets:**
  - no lagged D/E;
  - D lags only;
  - E lags only;
  - added lagged coal, gas and hydro;
  - three days of anomaly history instead of lagged outcomes;
  - each of the main sets with natural inflow summed over the window;
  - no wind-window control;
- **half-hour × month fixed effects.** Day-type dummies are kept. The reviewer's version without them gave 1.24 at
  7 d with F 9.2; this one gives 0.72 with F 43.
- **a calendar-aligned climatology.** The preregistered code caps day-of-year at 365, which shifts leap years by one
  day after 29 February.
- **three alternative instruments:** the next-7-day mean anomaly, including the 30-day horizon; the next-24-h mean;
  the calendar-day mean.
- **three subsamples:** dropping 2021 and 2024; 2015–2019; 2020–2024.

**Also reported:**
- the coal/gas/hydro composition under four control sets;
- the response of window inflow to instrumented demand;
- H2 rescored with block MEFs from the calendar-day-mean instrument.

My code reproduces the reviewer's numbers for every specification both of us ran.

**Disclosures:**
- **The block-level weak-instrument rule was set after the results were seen.** The rule in `code/simulate.py`
  (H2 is Inconclusive if a block carrying moved load has first-stage F < 10) was written after `mef.json` showed the
  night block's F of 4.2. The plan's rule is horizon-level. Under the plan's literal rule, the capture ratio of 18
  (0.83–127) would make H2 **Refuted**. The report keeps Inconclusive and states both.
- **H2's "time-of-day MEF" is the 1-day MEF of windows starting in a block,** not the marginal factor of load placed
  in that block. The construct, as preregistered, cannot answer H2 even with a strong instrument.
- **The single half-hour instrument cannot identify 14- or 30-day windows by construction.** Its autocorrelation is
  0.04 at 7 days, so the plan's instrument was mismatched to the H1 horizon.
- **The storage level is not the Electricity Authority's "controlled storage".** HMD active-storage ranges for Te
  Anau, Manapōuri, Wānaka and Wakatipu are about twice the schemes' active capacity. Each offset is constant, so the
  anomaly used for H3 and the standardised control are unaffected. Wānaka's inflow is HMD's natural *outflow* series.
