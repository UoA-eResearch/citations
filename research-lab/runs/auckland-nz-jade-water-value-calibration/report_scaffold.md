## What was asked

Since 2023 the Electricity Authority has published weekly runs of JADE as its benchmark for the value of water
held in New Zealand's hydro lakes. JADE is a stochastic dual dynamic programming model of the hydro-thermal
system, developed by the Electric Power Optimization Centre at the University of Auckland and released as open
source. Each weekly run looks a year ahead over 52 weekly stages, under historical inflow sequences, and produces
a distribution of wholesale prices as well as the water values the Authority publishes.

The question here is narrow and empirical, and the preregistration (`plan.md`) states it as two hypotheses:

- **H1:** does the realised price exceed the simulated 90th percentile far more often than a calibrated
  distribution allows -- in at least 20% of weeks, twice the nominal 10%?
- **H2:** is the miscalibration at least three times worse in weeks that begin with the lakes unusually low?

This is a calibration audit of a published official model. It is not a claim that JADE is the wrong model for the
job the Authority uses it for, and the limitations section says why that distinction matters.

## What was already known

The Authority publishes the runs, chiefly to support trading-conduct monitoring, and an EPOC workshop presentation
describes that publication and notes that JADE superseded the earlier DOASA model. A 2023 arXiv paper on capacity
planning uses the JADE New Zealand dataset. No published check of whether the runs' price distributions match the
prices that followed was found, and the Authority does not publish one (searches 2026-10-20).

## How it was done

**Data.** Everything is published by the Electricity Authority on EMI and downloaded from its blob store:

- the **Expected water values** dataset: 152 weekly runs (52 in 2023, 52 in 2024, 48 in 2025) out of 17,991 files
  and 44.8 GB. Each run's `tidy_results.csv` is about 88 MB, and prices appear in no smaller file, so each was
  streamed and filtered in flight to the rows the study needs, keeping about 240 KB per run;
- each run's **input-freeze timestamp**, taken from the `Inputs/data_files/<YYYYMMDDHHMM>/` folder name, and its
  own `hours_per_block.csv`;
- **final energy prices**, half-hourly by node, for HAY2201, with BEN2201 and OTA2201 reported alongside;
- the **Hydrological Modelling Dataset**: per-lake active storage back to the 1980s, and the derived capacity
  series that gives each scheme its GWh per million cubic metres.

**The out-of-sample boundary.** Stage 1 of a run is the week its inputs were frozen, and is therefore partly
elapsed when the run is made; stage 2 is the first week wholly after the freeze. That is the week the study scores.
The convention was verified rather than assumed: every usable run's input timestamp falls inside its own stage-1
week, which also confirms that JADE week *w* of year *Y* begins on 1 January plus 7(*w*-1) days.

**Measures.** For each run and each inflow sequence, the stage-2 block prices at HAY are combined into a weekly
average weighted by that run's own hours per block. The realised figure is the time-weighted average of settled
half-hourly prices at HAY2201 over the same seven days. The study then records where the realised price fell within
its own simulated distribution -- the probability integral transform -- and whether it exceeded the simulated 90th
percentile.

**National storage.** Lake volumes cannot be added across lakes, so each lake's active storage is converted to
energy using its own GWh-per-Mm3 ratio from the derived capacity series before summing. A run is classed as
low-storage if that national figure, averaged over the run's first week, sits below the 20th percentile of the same
week of the year in other years.

**Intervals** come from a moving-block bootstrap over runs in calendar order (blocks of four consecutive runs,
2,000 resamples, seed 20261020), because consecutive weekly runs share inputs and market conditions.

## Reproducing it

`code/fetch.py`, then `code/analysis.py`, then `code/figures.py`.

- **Inputs** are cached under `data/`: `runs/<year>_<week>.csv` (the filtered simulation output),
  `runs/<year>_<week>_hours.csv`, `run_index.csv`, `prices/<yyyymm>.csv` and `hmd/`.
- **Results** are in `results/tables/`: `primary.json`, `runs.csv` and `by_stage.csv`.
