# Rebate or road charge? Separating two 2024 shocks to New Zealand's EV uptake

*1.4 million light-vehicle first registrations, January 2021 to September 2026, from New Zealand's Motor Vehicle
Register, used to tell apart two policy changes three months apart: the end of the Clean Car Discount on
31 December 2023 and the arrival of road user charges for electric vehicles on 1 April 2024.*

**Verdict: Inconclusive on both preregistered tests, with clear descriptive findings behind them.**

- **H1 (the January 2024 collapse was mostly buyers rushing in early): Inconclusive, and the evidence leans
  against it.** Plug-in registrations ran 951 vehicles above baseline in December 2023 but 10,578 below it over
  January–March 2024, a ratio of 0.09 where the hypothesis needed at least 0.5. The interval is wide
  (−0.40 to +1.07), so the preregistered rule returns Inconclusive, but no variant of the estimate reaches 0.5:
  starting the baseline in 2022 gives 0.44, and counting November as well as December gives −0.01.
- **H2 (road user charges did far less than the rebate's removal): Inconclusive, for lack of power.** After
  1 April 2024, plug-in registrations moved **+32%** relative to non-plug hybrids (95% CI −36% to +153%) — the
  wrong sign for a deterrent, and indistinguishable from nothing. The minimum detectable effect is 161%, and a
  placebo at 1 April 2026 gives +43%, larger than the real event.

**What the data show plainly, whatever the formal tests return:**

- **The rebate's end is visible to the naked eye; the road charge is not.** The plug-in share of light
  registrations fell from **27.3% in December 2023 to 2.8% in January 2024**, a 24.5 percentage-point drop in one
  month. Nothing comparable happens at April 2024.
- **The drop was a genuine fall in demand, not a timing artefact.** Pull-forward accounts for about a tenth of it.
- **It did not last.** By mid-2026 the plug-in share is back to 18–22%, above its mid-2023 level (11.2%), and
  January–September 2026 already has 29,402 plug-in registrations against 37,581 in all of 2023. A 2026 preprint
  describes the fall as "lasting"; on data running 2.5 years past the change, it was not.
- **The same policy pushed the other way for utes, and that is visible too.** The high-emission fee ended on the
  same date, and diesel utility registrations collapsed to 988 in December 2023 before rebounding to 4,245 in
  January 2024 — buyers waiting for the fee to lapse, the mirror image of the rebate deadline.

## In plain terms

New Zealand ended its rebate for electric cars on 31 December 2023, and three months later started charging EV
drivers road user charges. EV sales fell off a cliff. Which change did it?

We counted every light vehicle registered in New Zealand from 2021 to September 2026, grouped by what powers it.

The rebate's end is unmistakable. In December 2023, 27 of every 100 vehicles registered could plug in. In January
2024, fewer than 3 could. The road user charge, by contrast, left no mark we can find: after it arrived, EV
registrations actually moved up a little compared with ordinary hybrids, which don't pay it.

Two things complicate the story. Some buyers rushed to register before the rebate ended, but only about a tenth of
the drop is explained that way, so most of it was people simply not buying. And the slump did not last: by 2026 EV
registrations had largely recovered.

There is a neat check on all this. The same law charged a fee on high-emission vehicles, and it ended on the same
day. Diesel ute buyers did the opposite of EV buyers: they waited. Ute registrations fell to a quarter of normal in
December 2023 and then more than quadrupled in January. The same deadline, the opposite incentive, the opposite
behaviour.

We cannot put a confident number on the road charge's effect: there is too much month-to-month noise, and a
placebo test on a year with no policy change produced a bigger swing than the real one.

## What was asked

Two policy changes landed three months apart, and public debate attributes the EV slump to both, plus a change of
government messaging. The study asks two preregistered questions (`plan.md`):

- **H1:** how much of the collapse in early 2024 is buyers who simply registered early, before the rebate ended?
- **H2:** is the incremental effect of road user charges small — under a third of the rebate effect?

**The identification.** Non-plug hybrids lost their rebate at the same moment as plug-in vehicles, but were **not**
moved to road user charges: as of May 2026 the government has legislated intent but set no date. They are
therefore a control for the road-charge shock and not for the rebate shock, which is why the rebate effect is
measured against the group's own fitted baseline instead.

## What was already known

A 2026 Research Square preprint (rs-11080967) estimates the Clean Car Discount's removal by regression
discontinuity in time and reports an immediate, lasting fall of about 24 percentage points in battery-electric
market share. Only its title could be retrieved (D1), so this study compares with the figure reported in secondary
sources rather than claiming priority on that effect. The Ministry of Transport's November 2023 regulatory impact
statement predates both changes. No study separating the two shocks, or quantifying the December 2023
pull-forward, was found (searches 2026-10-20).

## How it was done

**Data.** NZTA's Motor Vehicle Register, through its ArcGIS service, which answers aggregation queries. NZTA's web
site refuses scripted requests, so counts were obtained grouped by month, motive power, import status and vehicle
type — no vehicle-level record was retrieved. The universe is light vehicles (passenger cars, vans and utilities),
1,419,410 first registrations from January 2021 to September 2026.

**Groups.** Plug-in (battery-electric plus plug-in hybrid) is treated; non-plug hybrids are the control; petrol
and diesel are context.

**Measures.**
- A baseline for the treated group: log registrations on a linear trend with calendar-month effects, fitted
  January 2021 to September 2023 and projected forward.
- **H1** compares the December 2023 excess with the January–March 2024 shortfall, both in vehicles.
- **H2** compares the treated group's shortfall against its own baseline (the rebate effect) with a
  difference-in-differences against hybrids across 1 April 2024, excluding April as a transition month.
- Intervals come from a residual block bootstrap (three-month blocks, 2,000 resamples), with residuals taken
  around the baseline before October 2023 and around each analysis window's own mean afterwards, so post-period
  noise is estimated rather than assumed away.

## Results

### The two shocks (`results/figures/F1_registrations.png`)

| month | plug-in registrations | plug-in share of light registrations |
|---|---|---|
| October 2023 | 3,708 | 16.8% |
| November 2023 | 4,604 | 19.5% |
| **December 2023** | **5,976** | **27.3%** |
| **January 2024** | **590** | **2.8%** |
| March 2024 | 954 | 4.7% |
| June 2024 | 928 | 5.5% |
| June 2025 | 2,148 | 11.6% |
| June 2026 | 4,577 | 21.7% |
| September 2026 | 4,574 | 18.3% |

Total light registrations barely moved across the deadline (21,875 in December 2023, 21,201 in January 2024), so
the share collapse is not a volume artefact.

![Registrations by powertrain](results/figures/F1_registrations.png)

### H1: pull-forward explains about a tenth of the collapse (`results/figures/F2_pullforward.png`)

- December 2023 excess: **951 vehicles** above baseline.
- January–March 2024 shortfall: **10,578 vehicles** below baseline.
- **R = 0.09** (95% CI −0.40 to +1.07). The rule needed a lower bound of at least 0.5, so **H1 is Inconclusive**;
  the interval also fails to exclude 0.5, which is why it is not Refuted.
- **Sensitivities both stay below 0.5**: fitting the baseline from 2022 gives R = 0.44; counting November as well
  as December gives R = −0.01, because November 2023 was itself slightly below baseline.
- The treated group sat **81% below baseline** over January–March 2024 (95% CI −91% to −59%).

![Pull-forward](results/figures/F2_pullforward.png)

### H2: no detectable road-user-charge effect (`results/figures/F3_ruc_did.png`)

| comparison | plug-in vs hybrids |
|---|---|
| **1 April 2024 (the real change)** | **+32%** (95% CI −36% to +153%) |
| 1 April 2022 (placebo) | −14% |
| 1 April 2023 (placebo) | −5% |
| 1 April 2025 (placebo) | −4% |
| 1 April 2026 (placebo) | +43% |

- **H2 is Inconclusive**: Q = 0.16 with a 95% interval of 0.01 to 0.53, which straddles the one-third threshold.
- The estimate has the wrong sign for a deterrent and a minimum detectable effect of 161%. A placebo year produced
  a larger swing than the event year, so this design cannot resolve an effect of plausible size at monthly
  frequency.
- By powertrain and import status, relative to hybrids after April 2024: new battery-electric +31%, used
  battery-electric +27%, new plug-in hybrid +4%, used plug-in hybrid −11%.

![Road-user-charge difference-in-differences](results/figures/F3_ruc_did.png)

### The fee side of the same policy

Diesel utility registrations, which paid the high-emission fee until 31 December 2023, ran at about 2,700 a month
through late 2023, fell to **988 in December 2023**, and jumped to **4,245 in January 2024** before settling back
near 2,600–2,700. Buyers deferred across exactly the date EV buyers rushed. This is descriptive, but it is the
clearest available evidence that registration timing responds sharply to these deadlines.

## What this does and does not show

- **It shows** that the end of the Clean Car Discount coincides with an abrupt, very large fall in plug-in
  registrations; that only about a tenth of the fall is explained by early registration; that the fall had largely
  reversed by 2026; and that no road-user-charge effect is visible against a hybrid control.
- **It does not establish the size of the road-user-charge effect.** The test is badly underpowered, and a placebo
  year moved more than the event year. "No detectable effect" is not "no effect".
- **It cannot separate the rebate's end from everything else that changed at the same date**, including the
  high-emission fee's removal, the change of government messaging, and model launches and price cuts. The ute
  result shows the fee mattered for timing, which also shifts the mix of what was registered.
- **The register is a snapshot of vehicles still registered in September 2026.** Vehicles since deregistered are
  missing, and attrition rises with age, tilting earlier months slightly down. The difference-in-differences
  compares powertrains within the same months and is largely unaffected; the H1 baseline is more exposed, which is
  why the alternative estimation window is reported.
- **Counts are first New Zealand registrations**, so for used imports the month is the import's registration, not
  the sale.
- **No personal data.** Counts only, aggregated by the register's own service.

## Process and deviations

- **Preregistration.** `plan.md` was committed before any registration series was built, after only field lists
  and category counts had been examined.
- **Code before outputs.** `fetch.py` and `analysis.py` were committed before the outputs they produced;
  `figures.py` was written after the results.
- **D1** records that the register service runs to September 2026 (not March, as its name suggests), the added
  2026 placebo, and that the prior preprint could not be read in full.

## Reproducing it

`code/fetch.py`, then `code/analysis.py`, then `code/figures.py`.

- **Inputs** are aggregation queries against NZTA's `MVR_Mar26` FeatureServer, cached in `data/raw/<year>.json`
  with the monthly series in `data/registrations.csv`.
- **Results** are in `results/tables/`: `primary.json`, `monthly.csv` and `placebos.csv`.
