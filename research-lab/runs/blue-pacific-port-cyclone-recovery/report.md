# How long do island supply lines stay broken after a cyclone?

*Ship calls after Category 3+ cyclones at 2,065 ports over eight years of open AIS-derived data: an
import-concentration test, a small-island comparison, and a forecast for the 2026–27 South Pacific season frozen
before it begins.*

**Verdict: Inconclusive, and the direction runs against the lead.** The primary hypothesis was that a port's share
of national imports predicts recovery beyond size and storm. It came out at ΔAIC 2.3 against a bar of 10, just
above the line for Refuted. Its direction is the reverse of the lead's story: ports that carry more of their
country's imports were *less* often detectably disrupted. That association weakens and loses significance once
detectability is properly controlled. The small-island comparison could not be estimated. Only 1 of 17
measurable events at small-island ports showed any detectable disruption, about the method's false-alarm rate, so
there was nothing to time. At the five Pacific events with enough traffic to measure, a complete two-week closure
would almost certainly have been seen; none was. The other 27 Pacific events fall at ports too quiet for any
method based on ship calls to see a disruption shorter than about a month. Where disruptions were detected (other
ports), the median recovery time is 6 days, the same as the main earlier AIS study.

## In plain terms

When a severe cyclone passes near a port, how long until ships come back? And are small island ports, which often
handle most of a country's imports, slower to recover? We used a public daily record of ship visits to 2,065 ports
from 2019 to 2026, and matched it with every cyclone track.

Most Pacific island ports turned out to be too quiet to answer the question. Fifty of 62 get fewer than one ship
every two days. At that rate, a port can be shut for two weeks and the record looks much like an ordinary lull.
We worked out exactly how long a closure each port could reveal before looking at any result.

At the small-island ports busy enough to measure (17 cases, mostly in the Caribbean, five in the Pacific), we
almost never saw a disruption. If a port had been fully shut for two weeks, we would very likely have noticed.
That does not mean the storms did no harm. Ship visits are not cargo, the hardest-hit ports were usually the
quiet ones, and a reduced service can look normal in this record. It does mean that long, complete port closures
were not what happened at the main island harbours we could see.

At the busier ports elsewhere, a detected disruption typically lasted about six days, matching earlier work.

Before the season opens on 1 November 2026, we have locked in a forecast for 12 Pacific ports. We will score it
once the season's data are complete, in about September 2027.

## What was asked

The lead (scouted 2026-10-16 from the University of Auckland's Blue Pacific Horizons signature research area)
claimed three things. Pacific island ports take a median of at least 14 days to recover after a Category 3+
cyclone. That is at least twice as long as matched non-island ports. And a port's share of national imports
predicts recovery better than its size (ΔAIC ≥ 10). It proposed IMF PortWatch daily port calls and IBTrACS cyclone
tracks, with a frozen forecast for the 2026–27 season.

Counting events before computing any outcome showed the first claim had no usable sample (§ How it was done), so
plan.md restated the hypotheses before any recovery time existed:

- **H1 (primary):** adding import share to both parts of a two-part model improves AIC by ≥ 10. Supported if
  ΔAIC ≥ 10, Refuted if < 2, Inconclusive between. The sign is reported, not presumed.
- **H2 (secondary):** small island developing states (UN list) recover at least 2× more slowly, adjusted
  (Weibull time ratio). Supported if the interval is above 1 and the point estimate is ≥ 2; Refuted if the upper
  end is < 2.
- **Pacific:** a descriptive case series, with what the method could have detected at each port.
- **Forecast:** frozen before 1 November 2026, scored after the season.

## What was already known

| Work | What it establishes | What it leaves open |
| --- | --- | --- |
| Verschuur, Koks & Hall (2020), *Transp. Res. D* 85:102393 | AIS-observed recovery after natural disasters: 141 disruptions, 74 ports; median 6 days, p95 22 days | small islands; import concentration |
| CyPort (arXiv:2509.22656) | 1,927 port–cyclone interactions at 145 US ports | outside the US |
| US DOT, *Prediction of port recovery time after a severe storm* | AIS vessel counts, Gulf of Mexico | outside the Gulf |
| IMF WP 26/99 (2026) | PortWatch nowcasts of country trade, incl. some SIDS | port-level recovery after cyclones |

No earlier PortWatch-based estimate for Pacific island ports, test of import concentration, or frozen seasonal
forecast was found (search 2026-10-16).

## How it was done

**Data.** IMF PortWatch daily port calls, 2019-01-01 to 2026-07-24 (2,065 ports, 5.7 M rows). The PortWatch ports
database (size; share of national maritime imports, a model-based PortWatch estimate). IBTrACS v04r01 tracks to
2026-10-15. All retrieved 2026-10-16; hashes are in `data/raw/VINTAGE.txt`.

**Events.** A port–storm pair where the hourly-interpolated track passes within 150 km at Category 3+ (the primary
arm), with closest approach from 2019. The arm holds 213 events. 85 of them (34 storms) are at ports averaging
≥ 0.5 calls a day, with ≥ 270 days of history before and the follow-up the method needs after. The rest are
114 at quieter ports, 8 with too little follow-up and 6 with too little history.

**What counts as a disruption.** For each event, a negative-binomial model of the port's daily calls over the
two years before, with weekday, seasonal and trend terms. It enters the port's *share* of traffic at reference
ports 1,000–4,000 km away, so a shock to all shipping (COVID's collapse in early 2020) cancels rather than
reading as storm damage. 2,000 simulated paths give the range of normal. An event is *disrupted* if the
deepest dip in the first two weeks falls below the 5th percentile of the same statistic in the simulated paths.
*Recovery time* is the first day after the dip from which calls stay within the normal range for a full window.
The smoothing window scales with traffic, about ten expected calls: 7 days at busy ports, 21 at half a call a day.

**What the method can see, worked out first.** Synthetic ports with known closures, run through the identical
algorithm (F1). At ≥ 2 calls a day, a complete closure of a week is caught every time. At one call a day, 78% of
the time. At half a call, 30%, and a two-week closure 85%. False alarms run at 3–10%. When a closure is caught,
the recovery time matches its true length to about a day.

![Detection probability against closure length by port traffic](results/figures/F1_detectability.png)

**Model.** Part A: a logistic model for disrupted or not. Part B: a Weibull accelerated-failure-time model for
recovery days among disrupted events, censored at 120. Both use log port size, log mean daily calls (the
detectability control), category and distance. Part A intervals are clustered by storm. Part B intervals use a
storm-cluster bootstrap (1,000 draws).

**Changed from the lead before any outcome (deviations D1).** 50 of 62 Pacific island ports average under 0.5
calls a day. Of 32 Pacific events in the primary arm, 5 were measurable, from 3 storms, three of them Cyclone
Harold at the onset of COVID. So the Pacific became a case series. The island comparison widened to all small
island developing states. Import concentration, with 85 events and 34 storms, became the primary. "Non-island"
became "not a small island developing state", since Japan, the Philippines and Taiwan are islands.

**Caught by the method's own tests before any real event (D2, D3).** A pointwise 15-day rule gave 23% false
alarms; it became one familywise test. An estimated COVID adjustment absorbed nothing; it became an offset. A
fixed 7-day window could not see even a 28-day closure at half a call a day; it now scales with traffic. And the
simulation itself silently scored invalid runs as undetected; fixed, and now an error.

## Results

### H1: Inconclusive, close to Refuted, and the sign is the reverse of the lead's story

| specification | events (storms) | ΔAIC | part A: odds of disruption per +10 pp import share | verdict |
| --- | --- | --- | --- | --- |
| **primary: Cat 3+ ≤ 150 km** | 85 (34) | **2.33** | **0.78 (0.61–0.98)** | **Inconclusive** |
| Cat 1+ ≤ 150 km | 435 (100) | 9.52 | 0.84 (0.73–0.97) | Inconclusive |
| Cat 3+ ≤ 100 km | 53 (24) | 3.40 | 0.67 (0.40–1.12) | Inconclusive |
| Cat 3+ ≤ 250 km | 189 (50) | 9.08 | 0.78 (0.65–0.92) | Inconclusive |
| recovery = back within 10% (T10) | 85 (34) | 2.18 | as primary | Inconclusive |
| own-history counterfactual | 85 (34) | 1.54 | 0.79 (0.63–0.99) | (below the Refuted line) |
| excluding Mar–Jun 2020 | 81 (32) | 1.46 | 0.79 (0.63–0.99) | (below the Refuted line) |

All the gain is in part A, whether a disruption is detected at all (ΔAIC +4.2). Adding import share to part B makes
the fit worse (−1.8). Its time ratio, 1.66, has a bootstrap interval of 0.17 to 670: these data say nothing about
whether import share changes recovery *length*.

In part A the direction is consistent across every specification. Ports carrying more of their country's imports
were less often detectably disrupted. That fits one of the two mechanisms plan.md set out in advance: ships bound
for a country's only port cannot divert, so they wait and return. But it is also what leftover detectability
would produce, which the post-hoc checks below address.

### H2: Inconclusive, because there was almost nothing to time

| | events | storms | detectably disrupted | median recovery if disrupted |
| --- | --- | --- | --- | --- |
| small island developing states | 17 | 8 | **1** (Kingston, Melissa 2025: 2 days) | — |
| other ports | 68 | 27 | 27 (40%) | **6 days** (p90: 34) |
| Pacific island ports (subset of the first row) | 5 | 3 | 0 | — |

With one disrupted small-island event, part B cannot estimate a small-island time ratio. The preregistered guard
(D4) makes H2 Inconclusive rather than report a number fitted to one event. Part A has an odds ratio for
small-island ports of 0.09 (0.01–1.43, p = 0.09). In the Cat 1+ arm, where 5 of 53 small-island events were
disrupted, the adjusted time ratio is 0.80 (0.15–3.89). That is also Inconclusive, but its point estimate is
nowhere near 2.

![Recovery days against port traffic for every measurable event](results/figures/F2_events.png)

**External check.** The median recovery among detected disruptions at other ports, 6 days, is the median Verschuur
et al. (2020) found from AIS at 74 ports. The two studies differ in method, period and port set.

### Post hoc: is "less often disrupted" just "harder to see"? (D7)

Part A controls for detectability with a straight line in log traffic. But the simulation shows detectability is
a steep threshold. Small-island events have less power to show a week-long closure: on average 0.66, against 0.86
elsewhere. For a two-week closure the gap almost closes: 0.95 against 0.98. Three checks, written and committed
after the results were seen and before they ran:

- **Simulated power as the control.** Each event gets its simulated power to detect a 7-day closure in place of log
  traffic. The import-share odds ratio moves to 0.85 (0.66–1.10, p = 0.21). The small-island ratio stays 0.09
  (0.00–1.79).
- **High-power events only** (≥ 80% power for a 7-day closure; 56 events, 28 storms). Import share: 0.79
  (0.58–1.09). Small-island ports: 1 of 6 disrupted, against 42% elsewhere.

![Odds ratios of a detectable disruption for import share and small-island ports](results/figures/F3_odds_ratios.png)

The direction survives, but neither association is distinguishable from zero once detectability is handled
properly. Part of the preregistered import-share signal was very likely detectability. What survives every check
is the simplest fact: at the small-island ports where a two-week complete closure would have been seen about 95%
of the time, one disruption was seen in 17 events, and it lasted two days.

### The Pacific case series

| port | storm | traffic (calls/day) | shortest closure caught 80% of the time | power for 14 days | dip (observed ÷ expected) | threshold | disrupted |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Lautoka, Fiji | Harold, Apr 2020 (Cat 4, 111 km) | 0.99 | 10 days | 1.00 | 0.93 | 0.24 | no |
| Suva, Fiji | Harold, Apr 2020 (Cat 4, 103 km) | 1.02 | 10 days | 1.00 | 0.88 | 0.24 | no |
| Nuku'alofa, Tonga | Harold, Apr 2020 (Cat 4, 115 km) | 0.54 | 14 days | 0.87 | 0.64 | 0.36 | no |
| Nouméa, New Caledonia | Niran, Mar 2021 (Cat 3, 50 km) | 1.44 | 7 days | 1.00 | 0.38 | 0.30 | no (close) |
| Apra Harbor, Guam | Mawar, May 2023 (Cat 4, 37 km) | 0.87 | 10 days | 0.97 | 0.78 | 0.36 | no |

The other 27 Pacific events in the primary arm could not be analysed. 26 are at ports below 0.5 calls a day,
including Luganville under Harold's eye, Savusavu under Yasa, and every Saipan, Tinian and Rota event. The
remaining one is Apra Harbor under Bavi in July 2026, with too little follow-up yet. At those ports, even a
month-long closure is uncertain to show in ship calls. Nouméa under Niran came closest: calls fell to 38% of
expected against a threshold of 30%.

### The frozen forecast for 2026–27

The forecast model has base covariates, import share and the small-island indicator in part A. Part B drops the
indicator, because one disrupted event cannot estimate it (D5). It was fitted once and frozen on 2026-10-17:

    forecast_model.json  0cbaa6e125ad071f05641a2c3ad58f096c4ad993bbef50220ed77ff6e43b8d25
    forecast_table.csv   26e6c7aa3693f2734372e5ca153d38c0daa8ee85b5d3fd19d0c7e73e635f45c3

For a Category 4 cyclone passing 75 km away:

| port | chance of a detectable disruption | median recovery if disrupted (days) |
| --- | --- | --- |
| Port Moresby, Papua New Guinea | 0.15 | 17 |
| Lae, Papua New Guinea | 0.15 | 16 |
| Rabaul, Papua New Guinea | 0.10 | 14 |
| Kimbe, Papua New Guinea | 0.09 | 14 |
| Nouméa, New Caledonia | 0.08 | 19 |
| Lautoka, Fiji | 0.08 | 18 |
| Suva, Fiji | 0.08 | 18 |
| Papeete, French Polynesia | 0.04 | 23 |
| Apra Harbor, Guam | 0.03 | 23 |
| Honiara, Solomon Islands | 0.03 | 22 |
| Nuku'alofa, Tonga | 0.03 | 23 |
| Apia, Samoa | 0.02 | 23 |

The full table covers Category 3, 4 and 5 at 25, 75 and 125 km. Chances of disruption run from 0.003 to 0.56.
Medians are a Weibull extrapolation; at the quietest ports and strongest storms they exceed the 120-day horizon.
`code/score_forecast.py` was committed with the plan. It scores the forecast against the historical benchmarks
(share disrupted 0.33; median recovery 5.5 days) once PortWatch covers 30 April 2027 plus 135 days, about
September 2027. With fewer than three qualifying events, the score will be reported and not interpreted.

## What this does and does not show

**It shows** that at the small-island ports busy enough to measure, complete closures of two weeks or more after
Category 3+ cyclones were not what happened, 2019–2026. The method's power for such a closure was about 0.95, and
16 of 17 events showed no disruption at all. It also shows that the question the lead asked cannot be answered
from ship calls for most Pacific ports, and how quiet a port must be before the answer runs out (F1).

**It does not show** that small island ports are resilient. Five reasons:

1. **Port calls are not cargo.** A port can receive ships while cranes, warehouses or roads are down.
2. **The hardest-hit ports are mostly the quiet ones.** 49 of 68 small-island events in the primary arm were at
   ports too quiet to analyse. The ports that were measurable are the main national harbours, typically the
   best protected and first to be reopened.
3. **The record misses the worst case in the window.** PortWatch starts in January 2019. So Hurricane Dorian's
   devastation of Freeport, Bahamas (September 2019) has too little prior history for the counterfactual and is
   excluded.
4. **Partial disruption is harder to see than closure.** The simulation used complete closures. Halved traffic
   for a month is less detectable.
5. **Disruptions starting more than two weeks after the storm** (supply-chain knock-ons) are outside the test
   window.

The import-concentration result is weaker than its preregistered p-value suggests. AIC with 34 storm clusters is
overconfident, and the post-hoc power control halves the signal. The direction (less often disrupted, not slower)
is worth testing with cargo or berth data, not AIS calls.

## Process and deviations

Seven logged deviations (`deviations.md`):

- D1: hypotheses restated before any outcome.
- D2, D3: method flaws caught by tests.
- D4: `analysis.py` crashed on first run, because lifelines' AFT fitter has no cluster option. Only descriptive
  tables were produced. The fix (storm bootstrap) and new tests were committed before the rerun.
- D5: the forecast's part B drops the small-island indicator.
- D6: forecast hashes.
- D7: post-hoc detectability checks.

Code was committed before the outcomes it produced. The plan is at d12c3f0, the analysis fix at 3c194e6, and the
results and frozen forecast at 0c928af.

## Reproducing it

    bash code/download.sh                    # PortWatch + IBTrACS; compare data/raw/VINTAGE.txt
    venv/bin/python code/events.py           # cyclone-port events from tracks and coordinates only
    venv/bin/python code/test_recovery.py    # 9 synthetic checks of the recovery algorithm
    venv/bin/python code/detectability.py    # F1 grid (28 cores, ~10 min)
    venv/bin/python code/recovery.py         # every event's counterfactual, disruption and recovery (~30 min)
    venv/bin/python code/test_analysis.py    # 6 synthetic checks of the models
    venv/bin/python code/analysis.py         # H1, H2, arms, sensitivities -> results/tables/primary.json
    venv/bin/python code/supplementary.py    # post-hoc checks, Pacific case series
    venv/bin/python code/figures.py

Released: `results/tables/recovery_events.csv` (every event, its status, disruption and recovery time),
`events_all.csv`, `detectability.json`, `primary.json`, `supplementary.json`, `pacific_case_series.csv`, and the
frozen forecast. PortWatch and IBTrACS are public and not redistributed.
