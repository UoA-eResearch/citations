# Preregistration: how much grid energy has New Zealand's rooftop solar displaced, and has it touched the winter peak?

Lead: `energy-nz-embedded-solar-edb-demand` (The Energy Movement). Written 2026-10-21, before any outcome series was
built and before any effect was estimated.

**Examined beforehand (no effect estimated):**
- The Commerce Commission's information-disclosure Parquet (`EDB_ID_Full_2026-06-01.parquet`, sha256 `c8f84407…`) and
  its JSON data dictionary: the list of schedules, sections, categories and units, and the count of rows per measure,
  distributor and year. Schedule 9e(ii) carries the energy and demand measures used below for all 29 distributors in
  disclosure years 2013–2025. No outcome value was summarised.
- The Electricity Authority's "Installed distributed generation trends" report (EMI report GUEHMT), exported as CSV by
  network participant, market segment, size band and fuel type (17 files, `data/raw/ea/SHA256SUMS`). Exposure-only
  summaries were read: national solar capacity at March 2025 is 601 MW, split residential 338, commercial 73 and
  industrial 190 (SME is a cross-cutting classification); the largest single-month steps (24–160 MW) are all in the
  industrial segment and the >10 kW band (solar farms, e.g. Top Energy November 2023, EA Networks November 2024).
- EMI's Network Supply Points table (20 October 2026) and the column layout of one Grid_import file (January 2015).
  The first rows of that file were seen while reading the header; nothing was summarised.

**Novelty** (searches 2026-10-21, web and OpenAlex). Modelling exists — MBIE's 2025–2026 reports on high solar and
battery uptake, EECA's study of the value of residential solar and storage, Rewiring Aotearoa scenarios — but no
empirical, network-level measurement of how much energy New Zealand's distributed solar has displaced, or of its effect
on network peaks, was found.

## 1. The accounting this study rests on

Rooftop solar on a consumer's connection (ICP) has two parts:
- **self-consumed** output never passes the meter, so it lowers the energy the distributor delivers to ICPs;
- **exported** output is metered as distributed-generation supply and delivered to neighbouring ICPs, so it does not
  lower energy delivered at all.

Both parts lower what the network draws from the national grid. So:

| measure (Schedule 9e(ii)) | expected change per MW of solar |
|---|---|
| Total energy delivered to ICPs | −(self-consumed share × yield) |
| Electricity supplied from distributed generation | +(exported share × yield) |
| Net supply from the grid = electricity entering the system − electricity supplied from DG | −yield |

Yield in New Zealand is about 1.05 (Invercargill) to 1.4 GWh per MW a year; installers commonly assume 30–40% of
residential output is self-consumed without a battery, commercial self-consumption is higher. Expected values are
therefore about **−1.0 to −1.4 GWh/MW** on net grid supply and about **−0.35 to −0.7 GWh/MW** on energy delivered.

The lead's hypothesis put "at least 1.0 GWh per MW" on energy delivered to customers. By the accounting above that
number belongs to net grid supply; on energy delivered it would require nearly all output to be self-consumed. H1 tests
the lead's number on the measure where it applies, and H2 tests energy delivered against a self-consumption floor.

## 2. Data

- **Outcomes**: Schedule 9e(ii), network = "All", year-end disclosures, disclosure years (April–March) **2015–2025**,
  29 distributors: total energy delivered to ICPs (GWh); electricity entering the system for supply to consumers'
  connection points (GWh); electricity supplied from distributed generation (GWh); maximum coincident system demand
  (MW). Average ICPs from Schedule 1 (energy delivered ÷ energy delivered per average ICP).
- **Exposure**: Electricity Authority installed solar capacity (MW), month-end, by network participant, mapped to the
  29 distributors (embedded-network participants are excluded; name changes are mapped in `code/build_panel.py`). For a
  disclosure year, the mean of the twelve month-ends April–March.
  - **Behind-the-meter solar** (H2, H3): residential + commercial segments, all sizes.
  - **All distribution-connected solar** (H1, H4): all segments, including solar farms.
- **Non-solar distributed generation capacity** (control in H1): EA all fuels minus solar minus standalone batteries.
- **Weather**: Open-Meteo historical (ERA5) daily mean and maximum temperature at each distributor's load centre(s)
  (listed in `code/weather.py`; multi-region networks average several points). Heating degree-days base 18 °C summed
  April–March; for H4, mean daily maximum temperature December–February.
- **Grid exit points (H4)**: EMI half-hourly Grid_import and Grid_export by point of connection, December–February,
  summers 2014/15 to 2025/26; each POC's network code as recorded in the metered data. Net offtake = import − export,
  summed over a network's POCs.

## 3. Hypotheses

All slopes are per MW of installed solar, estimated in per-ICP form (outcome per average ICP on solar kW per ICP, so the
coefficient is in GWh per MW), weighted by average ICPs, with distributor and year fixed effects and heating
degree-days. Intervals are 95% percentile intervals from a distributor-cluster pairs bootstrap (4,999 resamples, seed
20261021).

- **H1 (grid energy displaced at about the expected yield):** net supply from the grid falls by **at least 1.0 GWh per
  MW** of all distribution-connected solar (control: non-solar DG capacity per ICP). *Supported* if the estimate is
  ≤ −1.0 and the interval excludes zero; *Refuted* if the whole interval lies above −1.0; otherwise *Inconclusive*.
- **H2 (the distributors' delivered-energy base erodes by the self-consumed share):** energy delivered to ICPs falls by
  **at least 0.3 GWh per MW** of behind-the-meter solar (a floor below the expected 0.35–0.7). Same decision rule with
  −0.3.
- **H3 (the peak is untouched):** maximum coincident system demand changes by **less than 0.2 MW per MW** of
  behind-the-meter solar in either direction. *Supported* if the whole interval lies within ±0.2; *Refuted* if the
  estimate lies outside ±0.2 and the interval excludes zero; otherwise *Inconclusive*.
- **H4 (summer midday grid offtake falls):** mean net grid offtake in trading periods 25–30 (12:00–15:00 local time),
  December–February, falls by **at least 0.3 MW per MW** of all distribution-connected solar (summer-midday output per MW
  installed is expected near 0.5). Network-summer panel, summers 2014/15–2025/26, network and summer fixed effects,
  ICPs and mean daily maximum temperature as controls, same bootstrap. Same decision rule with −0.3. Networks whose
  points of connection cannot be separated in the metered data are merged into one unit, recorded before estimation.

## 4. Secondary and robustness, fixed in advance

- **Export share**: the slope of electricity supplied from DG on behind-the-meter solar, and the implied
  self-consumption share, H2 ÷ (H2 + export slope), compared with the 30–40% installer assumption.
- **Specification**: levels (GWh on MW, ICPs as a control); unweighted per-ICP; first differences; dropping heating
  degree-days; residential solar only as the H2/H3 exposure; leave-one-distributor-out (all 29, reported as a range);
  dropping disclosure year 2021 (COVID-19); dropping network-years whose absolute log change in the outcome exceeds 15%
  (industrial closures and openings).
- **Power**: the minimum detectable slope at 80% power from the bootstrap standard error, reported for each hypothesis.
- **Placebo**: H1 and H2 with solar capacity two years ahead added alongside current capacity; its coefficient
  should be near zero (future installations should not move present energy).

## 5. Threats and care

- **Confounding by growth and electrification.** Solar uptake is faster where population, incomes and electrification
  (heat pumps, EVs) grow. Year effects absorb national trends and ICPs absorb connection growth; residual electrification
  correlated with solar biases H1 and H2 towards zero and H3 upwards. Stated with each result.
- **Collinearity with time.** Identification is from differences between networks in the timing of uptake; the
  minimum detectable slope is reported, and an Inconclusive result will be called underpowered only if it is.
- **Measurement.** Disclosure definitions changed over time (the dictionary records versions); distributed-generation
  supply is metered for exports only; ICPs are derived from a disclosed ratio. Network participants and distributors
  are matched by name; any participant that cannot be matched is listed.
- **Solar farms** are excluded from behind-the-meter solar by segment; they are included in H1 and H4, where they
  reduce grid supply like any embedded generation.
- **No personal data**: all inputs are network-level aggregates.
- Any departure from this plan will be logged in `deviations.md` before the affected result is read.
