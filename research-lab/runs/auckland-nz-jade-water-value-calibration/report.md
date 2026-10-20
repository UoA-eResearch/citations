# A $15 band in a $265 market: how wide the Electricity Authority's published water-value runs actually are

*Every one of the 152 weekly JADE runs the Electricity Authority published from 2023 to 2025, scored against the
price the market then settled at Haywards.*

**Verdict: H1 Supported, H2 Refuted — and the headline is larger than either hypothesis.**

- **H1 (the upper tail is far too thin): Supported.** The realised price finished above the run's simulated 90th
  percentile in **59.2% of weeks** (95% CI 46.1% to 73.0%). A calibrated distribution would do that a tenth of
  the time; the hypothesis asked only for 20%, and the interval's lower bound is more than twice that.
- **H2 (three times worse when the lakes are low): Refuted.** Low-storage weeks do fail more often — 90.0% against
  56.0% — but the ratio is **1.61** (95% CI 1.12 to 2.36), and the upper bound sits below the threefold threshold
  the plan set. The effect is real and it is not threefold.

**The finding that matters more than either test: the published distributions are not thin on one side, they are
narrow on both.**

- The realised price finished **outside** the simulated 10th-to-90th-percentile band in **86.8% of weeks** — 59.2%
  above it and 27.6% below it. Almost nothing lands in the middle.
- The median simulated band is **$15.03/MWh wide**, a 90th percentile only **14% above** the 10th. Realised weekly
  prices over the same three years ran from **$25.94 to $290.88**. The band spans **5.7%** of the range prices
  actually took.
- Nominal coverage collapses accordingly: the 50% interval contained the outcome 5.3% of the time, the 80%
  interval 13.2%, the 90% interval 17.1%.
- This is stable, not an artefact of one crisis. Exceedance runs 61.5% in 2023, 63.5% in 2024 and 52.1% in 2025,
  and is essentially flat across forecast horizons (57.2%, 59.2%, 58.6%, 54.6% at stages 1 to 4).

**Why, and what it does not mean.** JADE's published runs vary *one thing*: which of 91 historical inflow
sequences the year follows. Demand, fuel costs, station outages and offer behaviour are held as given. So this
result is best read not as "the model is wrong" but as a measurement of something useful in its own right:
**hydrological uncertainty alone accounts for a band about one-twentieth as wide as the variation prices actually
show.** Everything else — gas, outages, and how generators choose to offer — lives outside these percentiles.
Anyone reading them as a forecast interval for price would be badly misled, and that is worth stating plainly
because the runs are published, open, and used.

## In plain terms

New Zealand's electricity market runs on water. The Electricity Authority publishes a weekly computer run, using a
model built at the University of Auckland, that works out what the water stored in the hydro lakes is worth. Each
run plays the year ahead 91 times over, once for each year of rainfall on record, and reports the range of
electricity prices that come out.

We took all 152 of those published runs from 2023 to 2025 and asked a simple question: when the week they were
forecasting actually arrived, where did the real price land in the range they gave?

Almost never inside it. In 59 weeks out of every 100 the real price finished above everything but the top tenth of
the model's range, and in another 28 it finished below the bottom tenth. The typical published range was about $15
wide. Real prices over those three years ranged over $265.

One week shows it clearly. In mid-August 2024, during the gas shortage, the model's 91 runs produced prices
between $139 and $173. The market settled that week at $449.

This is not really a mistake in the model. The run only changes one thing between its 91 tries: the rainfall.
Everything else that moves prices — gas, broken power stations, how generators choose to bid — stays fixed. So the
honest reading is that rainfall alone explains a band about one-twentieth as wide as prices really move. The
numbers are sound for what they are. They just should not be read as a forecast of what a week will cost.

## What was asked

Since 2023 the Electricity Authority has published weekly runs of JADE as its benchmark for the value of water
held in New Zealand's hydro lakes. JADE is a stochastic dual dynamic programming model of the hydro-thermal
system, developed by the Electric Power Optimization Centre at the University of Auckland and released as open
source. Each weekly run looks a year ahead over 52 weekly stages, under historical inflow sequences, and produces
a distribution of wholesale prices as well as the water values the Authority publishes.

The preregistration (`plan.md`) sets two hypotheses:

- **H1:** does the realised price exceed the simulated 90th percentile in at least 20% of weeks, twice the
  nominal 10%?
- **H2:** is that at least three times more common in weeks that begin with the lakes unusually low?

This is a calibration audit of a published official model. It is not a claim that JADE is the wrong model for the
job the Authority uses it for, and the limitations below say why that distinction matters.

## What was already known

The Authority publishes the runs, chiefly to support trading-conduct monitoring, and an EPOC workshop presentation
describes that publication and notes that JADE superseded the earlier DOASA model. An arXiv paper on capacity
planning uses the JADE New Zealand dataset. No published check of whether the runs' price distributions match the
prices that followed was found, and the Authority does not publish one (searches 2026-10-20).

## How it was done

**Data.** Everything is published by the Electricity Authority on EMI and downloaded from its blob store:

- the **Expected water values** dataset: 152 weekly runs out of 17,991 files and 44.8 GB. Each run's
  `tidy_results.csv` is about 88 MB and prices appear in no smaller file, so each was streamed and filtered in
  flight to the rows the study needs — 13.4 GB read, 104 MB kept;
- each run's **input-freeze timestamp**, from the `Inputs/data_files/<YYYYMMDDHHMM>/` folder name, and its own
  `hours_per_block.csv`;
- **final energy prices**, half-hourly by node, for HAY2201, with BEN2201 and OTA2201 alongside;
- the **Hydrological Modelling Dataset**: per-lake active storage from 1980, and the derived capacity series
  giving each scheme its GWh per million cubic metres.

**The out-of-sample boundary.** Stage 1 of a run is the week its inputs were frozen, and is partly elapsed when
the run is made; stage 2 is the first week wholly after the freeze, and is the week scored. This was verified
rather than assumed: every run's input timestamp falls inside its own stage-1 week, which also confirms that JADE
week *w* of year *Y* begins on 1 January plus 7(*w*-1) days.

**Measures.** For each run and each inflow sequence, the stage-2 block prices at HAY are combined into a weekly
average weighted by that run's own hours per block. The realised figure is the time-weighted average of settled
half-hourly prices at HAY2201 over the same seven days. The study records where the realised price fell within its
own simulated distribution (the probability integral transform) and whether it exceeded the simulated 90th
percentile.

**National storage.** Lake volumes cannot be added across lakes, so each lake's active storage is converted to
energy with its own GWh-per-Mm3 ratio before summing. A run is low-storage if that figure, averaged over its first
week, is below the 20th percentile for the same week of the year in other years.

**Intervals** come from a moving-block bootstrap over runs in calendar order (blocks of four consecutive runs,
2,000 resamples, seed 20261020), because consecutive weekly runs share inputs and market conditions.

## Results

### What was simulated, and what happened (`results/figures/F1_band_vs_actual.png`)

![Simulated band against realised price](results/figures/F1_band_vs_actual.png)

| | |
|---|---|
| weekly runs scored | **152** (52 in 2023, 52 in 2024, 48 in 2025); none excluded |
| median simulated 10th-90th band | **$15.03/MWh** (90th percentile 1.14x the 10th) |
| realised weekly prices, 10th to 90th percentile across weeks | **$25.94 to $290.88** (a spread of $264.94) |
| band as a share of that spread | **5.7%** |
| median simulated median | $107.56/MWh |
| median realised | $132.58/MWh |
| realised outside the simulated band | **86.8% of weeks** |

Two of these rows measure different things and should not be run together. The band is one run's uncertainty
about one week; the realised spread is variation across three years of weeks. A model could in principle be well
calibrated week by week and still show a narrow band, if prices were genuinely predictable a week out. **The
evidence that the band is too narrow is the coverage below, not the ratio** — the nominal 90% interval contains
the outcome 17.1% of the time. The $15-against-$265 comparison is an illustration of magnitude, and the title
should be read as one.

### H1: the upper tail (`results/figures/F3_exceedance.png`)

- **Exceedance rate 59.2%** (95% CI 46.1% to 73.0%), against a nominal 10% and a 20% threshold. **H1 is
  Supported**: the lower bound is more than double the threshold. Minimum detectable effect 18.7 percentage
  points.
- When the price did exceed the 90th percentile, it did so by a median factor of **1.69**, and at most **4.68**.
- **By horizon:** 57.2% (stage 1), 59.2% (stage 2), 58.6% (stage 3), 54.6% (stage 4). The miscalibration is
  present in the very week the inputs were frozen and does not grow with horizon.
- **By year:** 61.5% (2023), 63.5% (2024), 52.1% (2025).

![Exceedance by horizon and storage](results/figures/F3_exceedance.png)

### The other tail, and the shape of the failure (`results/figures/F2_pit.png`)

The realised price fell **below** the simulated 10th percentile in **27.6%** of weeks. The probability integral
transform is U-shaped and almost empty in the middle: of 152 weeks, 90 landed in the top tenth of their own
distribution and 42 in the bottom tenth, leaving 20 for the eight bins between.

| nominal interval | weeks it actually contained |
|---|---|
| 50% | 5.3% |
| 80% | 13.2% |
| 90% | 17.1% |

![Probability integral transform](results/figures/F2_pit.png)

### H2: storage state

| group | runs | exceedance rate |
|---|---|---|
| national energy storage in the bottom fifth for that week of the year | 20 | **90.0%** |
| all other weeks | 84 | **56.0%** |

- **Ratio 1.61** (95% CI 1.12 to 2.36). The interval excludes 1, so low storage genuinely makes things worse, but
  its upper bound is below 3. **H2 is Refuted** by the preregistered rule.
- The split covers the 104 runs in 2023 and 2024, because the hydrological dataset ends 2024-12-31 (D1).
- A sensitivity covering all 152 runs, using JADE's own run-start reservoir sum with the season removed, agrees:
  90.3% against 51.2%, a ratio of **1.76** (95% CI 1.31 to 2.42).

### One week in detail

The run published for week 32 of 2024 forecast the week beginning 12 August 2024, during the gas shortage. Across
all 91 inflow sequences its weekly average price at Haywards ranged from **$139.33 to $173.04**, with a 90th
percentile of **$167.07**. The market settled that week at **$449.36**, with daily averages from $350 to $599 —
**2.69 times** the 90th percentile, and well beyond the highest of the 91 sequences. This week was recomputed by
hand from the raw files, independently of the analysis code, and matches.

## What this does and does not show

- **It shows** that the price percentiles in the Authority's published weekly runs are far narrower than realised
  prices, in both directions, consistently across three years and across forecast horizons; and that the gap
  widens when storage is low, though by less than threefold.
- **It does not show that JADE is a poor scheduling model, or that its water values are wrong.** The runs vary
  only the inflow sequence, holding demand, fuel costs, outages and offer behaviour fixed. A narrow price band is
  the arithmetic consequence of that design, not evidence of an error in it. What the study quantifies is how much
  of realised price variation that design can reach: about a twentieth.
- **It cannot attribute the gap** between simulated and realised prices to particular causes. Gas, outages and
  offer behaviour are all candidates and none is separated here.
- **The storage split is partly out of sample.** The preregistered version covers 2023 and 2024 only; the
  all-years sensitivity uses a different storage measure and agrees, but neither is a substitute for a
  hydrological record that reaches 2025.
- **Prices can be revised.** The latest published monthly files were used, and December 2025 was assembled from
  daily files because the Authority publishes that month's consolidation only as incomplete (D1).
- **One node.** HAY2201 is the reference node for the model's HAY output; Otahuhu and Benmore are recorded in
  `runs.csv` but not scored.
- **No personal or community data**: market prices, model outputs and reservoir levels only.

## Process and deviations

- **Preregistration.** `plan.md` was committed before any simulated price met a realised one, after only the blob
  listing and one file's schema had been examined.
- **Code before outputs.** `fetch.py` and `analysis.py` were committed before the outputs they produced;
  `figures.py` was written after the results.
- **D1** records the 152-run count, the varying number of inflow sequences, the complete-week rule, the December
  2025 assembly, the storage measure and its coverage, and the spread statistics added after the results.
- **Validation** in `primary.json` checks the inflow-sequence distribution, the 168-hour weeks, the half-hourly
  period counts (including the 334- and 338-period daylight-saving weeks) and the realised monthly means, which
  reproduce the market's own history — the August 2024 peak of $465/MWh and the collapse to $29 that November.

## Reproducing it

`code/fetch.py`, then `code/analysis.py`, then `code/figures.py`.

- **Inputs** are cached under `data/`: `runs/<year>_<week>.csv`, `runs/<year>_<week>_hours.csv`, `run_index.csv`,
  `prices/<yyyymm>.csv` and `hmd/`.
- **Results** are in `results/tables/`: `primary.json`, `runs.csv` and `by_stage.csv`.
