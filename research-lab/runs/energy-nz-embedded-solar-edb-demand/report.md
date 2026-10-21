# What rooftop solar has done to New Zealand's electricity networks: invisible in the annual books, visible at summer midday

*Twenty-nine electricity distributors, 2014–2026: their annual information disclosures, the Electricity Authority's
registry of installed solar, and half-hourly metered offtake at every grid exit point, used to measure how much
grid energy distributed solar displaces and whether it touches the winter peak.*

**Verdict: Inconclusive on the three annual tests; Supported on summer-midday grid offtake, with a caveat on size.**
Distributed solar on the 29 networks grew from about 17 MW to 363 MW behind the meter (about 490 MW including solar
farms) over the panel's years. That is too small a share of annual energy for the distributors' annual disclosures to
detect, so the annual tests cannot answer their questions. Half-hourly grid data can: where solar grew, the networks
draw less from the national grid at summer midday.

- **H1 (net grid supply falls by at least 1.0 GWh per MW): Inconclusive.** −2.33 GWh per MW (95% interval −7.06 to
  +5.54). The minimum detectable slope at 80% power is about 8 GWh per MW, against an expected 1.0–1.4.
- **H2 (energy delivered to customers falls by at least 0.3 GWh per MW): Inconclusive.** −0.65 (−17.2 to +8.8);
  minimum detectable slope about 18.
- **H3 (the winter peak moves by less than 0.2 MW per MW): Inconclusive.** +0.53 (−2.24 to +1.91); minimum detectable
  slope about 2.8.
- **H4 (summer-midday grid offtake falls by at least 0.3 MW per MW): Supported.** −0.84 MW per MW (−1.01 to −0.16),
  stable when any one network is left out (−0.90 to −0.72).
  - **The size is overstated.** In a check added after the results (not preregistered), evening and night offtake
    fell with solar too: −0.49 and −0.33 MW per MW, intervals including zero. Networks adding solar fastest also drew
    less from the grid at hours when panels produce nothing.
  - **Netting that out**, midday minus evening offtake falls **−0.35 MW per MW (−0.44 to −0.26)**, and midday minus
    night −0.51 (−0.56 to −0.25). That is within the 0.4–0.6 range expected for average summer-midday output per MW
    installed.

## In plain terms

Rooftop solar is spreading fast in New Zealand. We asked what it has done to the electricity networks that carry
power to homes and businesses. Has it cut how much energy they deliver, and has it lowered the winter evening peak
that drives the cost of building them?

The yearly figures every network publishes cannot tell us. Solar is still only about one or two percent of the
energy they carry, and the yearly totals move around far more than that for other reasons. All three of our tests
on the yearly figures came back "can't tell".

The half-hourly meter readings where each network connects to the national grid tell a clearer story. On summer
afternoons, networks where solar grew draw noticeably less power from the grid. A fair estimate is that each
megawatt of panels cuts summer midday demand on the grid by about a third to half a megawatt, which is about what
panels produce on an average summer afternoon.

Our first estimate was larger than that. Some of the networks that added the most solar also drew less power in the
evening and at night, when panels produce nothing, so part of the first number was not the solar at all. We took that
into account to get the fairer estimate.

## What was asked

New Zealand's distributed solar has roughly doubled every two years since 2013. Ministry and agency modelling
(MBIE's 2025–2026 reports, EECA's study of residential solar and storage) project its effects, but no empirical,
network-level measurement was found. The preregistration (`plan.md`) set four tests, all per MW of installed solar:

- **H1:** net supply from the grid falls by at least 1.0 GWh a year.
- **H2:** energy delivered to customers falls by at least 0.3 GWh a year.
- **H3:** the network's maximum coincident demand moves by less than 0.2 MW either way.
- **H4:** summer-midday offtake at grid exit points falls by at least 0.3 MW.

**Why H1 and H2 differ.** Solar output that a household uses itself never passes the meter, so it lowers the energy
the distributor delivers. Output the household exports is delivered to a neighbour, so it does not lower delivered
energy, but it does lower what the network takes from the national grid. The lead this study came from put "at least
1.0 GWh per MW" on delivered energy; by this accounting that figure belongs to grid supply (H1), and delivered energy
should fall only by the self-consumed share (H2).

## How it was done

**Outcomes.**
- *Annual (H1–H3):* the Commerce Commission's information disclosures, Schedule 9e, for disclosure years
  (April–March) 2015–2025: energy delivered to ICPs; electricity entering the system minus electricity supplied
  from distributed generation (net grid supply); maximum coincident system demand.
- *Summer (H4):* the Electricity Authority's half-hourly metered flows at every grid exit point (Grid_export minus
  Grid_import), December–February, summers 2014/15 to 2025/26.

**Exposure.** The Authority's registry-based count of installed solar by network, monthly:
- *behind the meter* (residential and commercial segments, H2 and H3);
- *all distribution-connected solar*, including the farms in the industrial segment (H1 and H4).

**Model.** Outcome per customer connection (ICP) on solar kW per ICP, so the slope reads in GWh (or MW) per MW;
weighted by ICPs; distributor and year fixed effects; heating degree-days (H4: mean daily maximum temperature). 95%
intervals from a distributor-cluster bootstrap (4,999 resamples). Networks that share grid exit points are merged for
H4, giving 24 units.

## Results

### Installed solar (`results/figures/F1_installed_solar.png`)

![Installed solar](results/figures/F1_installed_solar.png)

| disclosure year | behind the meter, MW | all solar, MW | energy delivered, GWh |
|---|---|---|---|
| 2015 | 17 | 19 | 31,305 |
| 2020 | 102 | 110 | 32,574 |
| 2025 | 363 | 489 | 33,583 |

At an expected 1.2 GWh per MW, the 2025 stock would displace about 0.6 TWh of grid supply, under 2% of the energy
the networks carry, and less than the year-to-year movement in many networks' totals.

### The four tests (`results/figures/F2_slopes.png`)

![The four slopes](results/figures/F2_slopes.png)

| test | estimate | 95% interval | minimum detectable | verdict |
|---|---|---|---|---|
| H1 net grid supply, GWh/MW | −2.33 | −7.06 to +5.54 | 7.95 | Inconclusive |
| H2 energy delivered, GWh/MW | −0.65 | −17.22 to +8.75 | 18.27 | Inconclusive |
| H3 winter peak, MW/MW | +0.53 | −2.24 to +1.91 | 2.81 | Inconclusive |
| H4 summer-midday offtake, MW/MW | **−0.84** | **−1.01 to −0.16** | 0.55 | **Supported** |

**The annual tests could not have succeeded.** Their minimum detectable slopes are five to thirty times the
effects they were designed to find. Every robustness variant agrees (`results/tables/robustness.json`): levels,
unweighted, first differences, without degree-days, without 2021, without network-years whose outcome jumped more
than 15%, and with the disclosures' own ICP counts. All give wide intervals spanning zero.
The implied self-consumption share, about 11%, is equally uninformative.

### Summer midday (`results/figures/F3_change_vs_change.png`)

![Change versus change](results/figures/F3_change_vs_change.png)

| variant | MW per MW | 95% interval |
|---|---|---|
| preregistered (per ICP, weighted) | −0.84 | −1.01 to −0.16 |
| levels, ICPs as a control | −0.50 | −1.07 to −0.15 |
| unweighted | −0.89 | −0.99 to −0.24 |
| first differences | −0.58 | −0.86 to +0.43 |
| leave one unit out (range) | −0.90 to −0.72 | — |
| *placebo:* evening 18:00–21:00 | −0.49 | −0.65 to +0.21 |
| *placebo:* night 02:00–05:00 | −0.33 | −0.54 to +0.24 |
| *exploratory:* midday minus evening | **−0.35** | **−0.44 to −0.26** |
| *exploratory:* midday minus night | −0.51 | −0.56 to −0.25 |

The evening and night rows and the two differences were added after the primary results (D3, D4).

**The placebo did not come back clean.** Evening and night offtake also fell where solar grew, by roughly half to
three-fifths of the midday slope, though neither interval excludes zero. The two units with the largest growth in
solar per ICP, Top Energy and EA Networks, both added solar farms. EA Networks serves a heavily irrigated district, where summer
load can shift for reasons unrelated to solar. The leave-one-out range shows no single
unit drives the estimate.

**Comparing midday with the same network's evening removes whatever moved all hours together.** What remains,
−0.35 MW per MW, has a tight interval and is the study's best estimate of solar's effect on summer-midday grid
demand. Midday minus night gives −0.51. The preregistered −0.84 should be read as an upper end.

## What this does and does not show

- **It shows** that by summer 2025/26 distributed solar measurably reduces what New Zealand's networks take from the
  national grid at midday: on the netted estimate, about a third to a half of installed capacity. That is
  consistent with average summer-midday output.
- **It does not show** whether solar has eroded the distributors' delivered-energy base or left the winter peak
  untouched. The annual disclosures are too coarse to tell, and the tests were Inconclusive, not null results. The
  peak result would be expected on physical grounds, since winter evening peaks fall after dark, but this study
  cannot confirm it.
- **Confounding.** Networks with faster solar uptake differ in other ways: irrigation, industry, electrification,
  growth. The placebo shows this matters for H4's size. The within-network contrast is the main guard, and it is
  exploratory.
- **Exposure.** Installed capacity is the Authority's registry count; the inverter-versus-panel rating and system
  orientation are unknown, so per-MW output figures are approximate.
- **Data corrections**, all made before any estimate:
  - ICP counts are taken from the registry, because four disclosure-derived counts were wrong (D2): Westpower 2024
    implied 91,158 ICPs against about 14,300.
  - Six distributor-years with no distributed-generation figure are left out of H1.
  - The market data's flow directions are named from the grid's side, which the plan had reversed (D1).
- **No personal data.** All inputs are network-level aggregates.

## Process and deviations

- **Preregistration.** `plan.md` was committed before any outcome series was built; the panel and analysis code
  were committed before they were run.
- **Deviations** (`deviations.md`):
  - D1 corrected the grid-exit flow direction and set the H4 specification, before any panel was built.
  - D2 replaced the disclosure-derived ICP counts with registry counts, before any estimate.
  - D3 completed the preregistered robustness set for H4 and added the post hoc placebo.
  - D4 added the exploratory midday-minus-evening contrast after the placebo.

## Reproducing it

`code/fetch.py` (inputs and a hashed manifest), `code/build_panel.py`, `code/analysis.py`, `code/figures.py`.

- **Inputs** are public: the Commerce Commission's disclosure Parquet; the Authority's installed-generation report
  (EMI GUEHMT) and metered grid flows; Open-Meteo historical temperatures.
- **Results** are in `results/tables/`: `panel_annual.csv`, `panel_summer.csv`, `panel_log.json`, `primary.json`
  and `robustness.json`.
