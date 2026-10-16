# Preregistration — How long do island supply lines stay broken after a cyclone?

*Port-call recovery after Category 3+ cyclones from eight years of open daily AIS-derived data, an
import-concentration test, and a frozen forecast for the 2026–27 South Pacific season.*

Committed before any recovery time was computed. Examined beforehand, deliberately, because none involves the
outcome: the port database, overall port activity levels (a data-quality step the lead's own plan allowed),
the cyclone-port event table (built from cyclone tracks and port coordinates alone), and a pure simulation of
what the method can detect. What they showed is in §4, and it changed the hypotheses (§1.2).

## 1. The question

When a severe cyclone passes close to a port, how long do ship calls take to return to normal — and are small
island ports, which often carry a whole country's imports, slower to recover?

### 1.1 Hypotheses as preregistered here

Recovery time is the number of days after closest approach until the port's daily calls are back inside their
expected range (§5). It is modelled in two parts: whether a disruption is detected at all, and, if so, how long
recovery takes.

**H1 (primary).** A port's share of national maritime imports predicts recovery beyond what port size,
traffic level, cyclone category and distance already explain. Adding it to both parts improves the two-part
AIC by **≥ 10**: Supported if ΔAIC ≥ 10; Refuted if ΔAIC < 2; Inconclusive between. Its sign is reported, not
presumed (§1.3).

**H2 (secondary).** Ports in small island developing states recover more slowly than other ports hit by
comparable cyclones: the size-, traffic- and storm-adjusted time ratio is **≥ 2**. Supported if its 95%
interval lies above 1 and the point estimate is ≥ 2; Refuted if the interval's upper end is below 2;
Inconclusive otherwise.

**Pacific (descriptive).** Recovery times at Pacific island ports, reported as a case series with what the
method could and could not have detected at each port's traffic level.

**Forecast (prospective).** A forecast for every active Pacific island port, frozen and committed before
1 November 2026, scored after the 2026–27 season (§7).

### 1.2 How these differ from the lead, and why

The lead proposed: the median Pacific-island recovery time is ≥ 14 days and ≥ 2× that of matched non-island
ports, and import concentration beats port size (ΔAIC ≥ 10). Counting events before any outcome showed the first
claim cannot be tested:

- The primary arm (Cat 3+ within 150 km) holds 32 Pacific events. Most are at ports too quiet for a disruption
  to register (§4.2). With ≥ 0.5 calls a day and ≥ 90 days of follow-up, **5 remain: 5 ports, 3 storms** — and
  three of the five are Cyclone Harold in April 2020, when COVID had already shut Pacific borders and depressed
  shipping worldwide.
- A median over five clustered events cannot carry "≥ 14 days and ≥ 2× a comparison". It is reported as a case
  series instead.
- The lead's underlying claim is about small island ports, which are not only Pacific. Across all UN small
  island developing states there are **18 events, 14 ports, 9 storms, 10 states** (13 Caribbean, 5 Pacific). H2
  tests the island claim there. It remains underpowered (§8), and says so.
- The import-concentration test, which the critic named the lead's genuinely new contribution, has 94 events and
  42 storms, and becomes the primary.
- "Non-island" in the lead is ill-defined (Japan, the Philippines and Taiwan are islands). The comparison is
  small island developing states against all other ports.

All four are logged in deviations.md D1.

### 1.3 The sign of H1 is genuinely open

A port that carries most of its country's imports has no alternative if damaged — an argument for slower
recovery. But ships bound for it also cannot divert elsewhere, so they wait offshore and return as soon as it
reopens — an argument for faster recovery of its call count, while a minor port's traffic may divert to a
neighbour and come back slowly. H1 tests whether import share predicts recovery at all; the report gives its
direction in each part and does not treat either sign as confirmation of anything else.

## 2. What is already known

| Work | What it establishes | What it leaves open |
| --- | --- | --- |
| Verschuur, Koks & Hall (2020), *Transp. Res. D* 85:102393 | AIS-observed recovery: 141 disruptions, 74 ports, 27 disasters; median 6 days, p95 22.2 days, +2 days per 1 m surge | Small islands; import concentration; any prospective test |
| CyPort (arXiv:2509.22656) | 1,927 port–cyclone interactions at 145 US ports, 2015–2023 | Outside the US |
| US DOT, *Prediction of port recovery time after a severe storm* | AIS vessel counts, Gulf of Mexico | Outside the Gulf |
| ADB working paper (2025) | One Philippine typhoon, Bayesian structural time series | Generalisation |
| IMF WP 26/99 (May 2026) | Nowcasts country-level trade from PortWatch incl. some SIDS | Port-level recovery after cyclones |

The scouting critic and a fresh search (2026-10-16) found no PortWatch-based estimate of recovery at Pacific
island ports, no test of import concentration as a predictor, and no frozen seasonal forecast.

## 3. Data (all open, no accounts)

| Source | Use | Vintage |
| --- | --- | --- |
| IMF PortWatch daily port activity (ArcGIS Hub CSV), 2,065 ports, 2019-01-01 to 2026-07-24 | daily calls | 649,027,881 B, sha256 7ee7fde8…, 2026-10-16T10:12Z |
| IMF PortWatch ports database | size, location, share of national maritime imports | 510,188 B, sha256 a3a9380f…, 2026-10-16T07:33Z |
| IBTrACS v04r01 since 1980 | cyclone tracks and categories, to 2026-10-15 | 145,059,983 B, sha256 00f30d31…, 2026-10-16T10:52Z |

Full hashes and URLs: `data/raw/VINTAGE.txt`. PortWatch revises its history; this vintage is what is analysed.

## 4. What was known before any outcome

### 4.1 Events (`code/events.py`, tracks and coordinates only)

| arm | events | Pacific events | Pacific ports | Pacific storms | other events |
| --- | --- | --- | --- | --- | --- |
| **Cat 3+ within 150 km (primary)** | 213 | 32 | 23 | 9 | 181 |
| Cat 1+ within 150 km | 881 | 51 | 24 | 20 | 830 |
| Cat 3+ within 100 km | 134 | 17 | 13 | 7 | 117 |
| Cat 3+ within 250 km | 400 | 42 | 24 | 9 | 358 |

Category is IBTrACS's USA_SSHS (JTWC/NHC), or USA_WIND converted where missing. Tracks are interpolated hourly,
unwrapping longitude across 180° (Fiji, Tonga, Samoa, Tuvalu).

### 4.2 Most Pacific island ports are too quiet to show a disruption

Of 62 Pacific island ports, 12 average ≥ 0.5 calls a day, 5 average ≥ 1, and one (Port Moresby) ≥ 2. Apia
averages 0.53 with no calls on 56% of days. Detectability (§4.3) therefore decides which ports this study can
speak to.

### 4.3 What the method can detect (`code/detectability.py`, simulation only)

Simulated ports with a known closure of L days (zero calls), run through exactly the algorithm in §5, 120
replicates per cell, two dispersion levels (α = 0.25 and 1). Share of closures detected:

| mean calls/day | 2 days | 4 | 7 | 10 | 14 | 21 | 28 | shortest caught 80% of the time | false alarms (no closure) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.25 | 0.09 | 0.08 | 0.18 | 0.22 | 0.38 | 0.54 | 0.88 | 28 days | 0.08–0.15 |
| 0.5 | 0.13 | 0.22 | 0.30 | 0.55 | 0.85 | 1.00 | 1.00 | 14–21 days | 0.08–0.10 |
| 1 | 0.12 | 0.24 | 0.78 | 1.00 | 1.00 | 1.00 | 1.00 | 10 days | 0.04–0.07 |
| 2 | 0.18 | 0.64 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 7 days | 0.02–0.05 |
| 4 | 0.18 | 0.88 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 4–7 days | 0.05–0.06 |
| 8 | 0.31 | 0.94 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 4–7 days | 0.03–0.06 |

(α = 0.25 shown; α = 1 is similar but slower at the low end — full grid in results/tables/detectability.json.)

Three consequences, fixed now:

- At the ≥ 0.5 calls-a-day threshold, closures shorter than about two weeks are mostly invisible. A Pacific port
  reported as "no detectable disruption" means "no disruption long enough to see at this traffic", and the
  report will give each port's detection threshold beside its result.
- When a real closure is caught, the reported recovery time matches its true length to within about a day from
  0.5 calls a day upward. Recovery times are not biased by the method where they are measured.
- False alarms run at 3–10% (above the nominal 5% only at the quietest ports), and a false alarm carries a
  spurious recovery time of about 10–16 days. Part B of the model therefore contains some noise events; the
  traffic control in both parts and the storm-clustered errors are the protection, and the report says so.

## 5. Design

**Events.** A (port, storm) pair whose hourly-interpolated track passes within 150 km of the port at Category 3+
(primary arm), closest approach from 2019-01-01. Ports need ≥ 0.5 calls a day over 2019–2026. An event needs ≥ 270
days of history before it and 120 days plus one window after it (127–155 days, §5 below); events without them are
excluded and counted.

**Counterfactual.** A negative-binomial GLM fitted to the port's calls over [d0−730, d0−15]: day of week, two
annual harmonics, a linear trend, and — the primary specification — an offset of the log summed calls at
reference ports (every port with ≥ 0.5 calls a day 1,000–4,000 km away that is not itself within 250 km of a
Cat 1+ storm in [d0−30, d0+120]). The offset models the port's *share* of regional traffic, so a shock that hits
all shipping at once, such as COVID's collapse in early 2020, cancels rather than reading as storm damage. An
estimated coefficient on the index was tried first and failed this test: fitted to pre-event years with no
shared shocks, it came out near zero (`test_recovery.py`). Sensitivity: the port's own history only.

**Window length scales with traffic.** Every smoothing window holds about ten expected calls: k = max(7,
⌈10 / mean daily calls⌉) days, made odd, capped at 35 — 7 days at busy ports, 11 at one call a day, 21 at half a
call. A fixed 7-day window failed in simulation: at 0.5 calls a day it missed even a 28-day closure every time,
because zero-call weeks happen by chance and a statistic floored at zero cannot fall below a threshold of zero.
Quiet ports therefore get coarser time resolution, which is the honest cost of seeing them at all.

**Recovery time.** Simulate 2000 paths from the counterfactual over [d0−k, d0+120+k]; take centred k-day means.
*Disrupted* if the deepest dip of the observed centred mean relative to the counterfactual mean over days
0–max(14, k) falls below the 5th percentile of the same statistic across the simulated paths — a single
familywise test, because "below a pointwise 5% band on any of 15 days" gave 23% false alarms in testing.
*Recovery time*: the first day after the deepest dip from which the observed centred mean stays at or above the
pointwise 5% band for a full window (k days); censored at 120. Not disrupted → 0, reported as "no detectable
disruption". Sensitivity T10: back within 10% of the counterfactual mean for a full window, the threshold the
lead named.

**Two-part model** (`code/analysis.py`). Part A, logistic for "disrupted"; part B, Weibull AFT for recovery days
among disrupted events, censored at 120. Base covariates in both: log port size (PortWatch vessel count), log mean
daily calls (a detectability control), category, closest-approach distance. Standard errors clustered by storm.
Two-part AIC = AIC(A) + AIC(B).

## 6. Estimands and decision rules

| | estimand | rule |
| --- | --- | --- |
| **H1** | ΔAIC from adding import share to both parts, primary arm | Supported ≥ 10; Refuted < 2; else Inconclusive |
| H2 | time ratio exp(b_SIDS) in part B | Supported if interval > 1 and point ≥ 2; Refuted if upper < 2; else Inconclusive |
| Pacific | per-event recovery and disruption, with detectability at each port's traffic | descriptive |

Adding import share to both parts adds two parameters, so ΔAIC ≥ 10 means a likelihood-ratio statistic ≥ 14 on
2 df (p ≈ 0.001). With events clustered in storms, AIC is overconfident; the report gives the clustered Wald
tests for the share coefficients beside it.

## 7. The frozen forecast

`code/forecast.py` fits the two-part model with base covariates + import share + the small-island indicator on
the primary arm, writes every coefficient to `results/tables/forecast_model.json` and a forecast for each of the
12 active Pacific island ports at Category 3/4/5 and 25/75/125 km to `forecast_table.csv`, and prints their
sha256. **Both files and their hashes are committed before 2026-11-01.** `code/score_forecast.py`, committed
with this plan, scores them once PortWatch covers 30 April 2027 + 135 days (about mid-September 2027; the lead's
July 2027 leaves too little follow-up): Brier score for "disrupted" against the historical share disrupted, and
mean absolute log error of recovery time against the historical median. With fewer than 3 events the score is
reported and not interpreted.

## 8. Power

H2 has nine small-island storm clusters. A rough calculation, before any outcome: if log recovery time has a
standard deviation near 1 and the effective samples are about 9 and 33 storms, the standard error of the log time
ratio is about √(1/9 + 1/33) ≈ 0.38, so 80% power needs a ratio of about exp(2.8 × 0.38) ≈ **2.9**. H2 is
therefore well powered only for an effect larger than the one it tests; a ratio of 2 will most likely come out
Inconclusive, and the report will say that is a power result. H1 uses all 94 events and 42 storms.

## 9. Sensitivities (reported; none changes a verdict)

Arms: Cat 1+ within 150 km; Cat 3+ within 100 and 250 km. Recovery definition T10. Own-history counterfactual.
Excluding events in March–June 2020 (COVID onset).

## 10. Threats to validity

1. **Detectability.** At low traffic a short closure is invisible (§4.3); the traffic control in both parts and
   the case-series framing for the Pacific address this, and do not remove it.
2. **COVID.** Harold (April 2020) coincides with the pandemic's shipping collapse; the reference offset addresses
   it, and the exclusion sensitivity tests whether it matters.
3. **Port calls are not cargo.** A port can reopen to calls before cargo handling recovers, or keep calls while
   handling is impaired.
4. **AIS attribution** is weaker at anchorage-based and lagoon ports.
5. **PortWatch revisions.** The vintage is sealed; the 2027 scoring re-pull will be compared with it.
6. **The small-island set** follows the UN list, which includes some non-island states (Belize, Guyana, Suriname,
   Guinea-Bissau); this is stated, not altered.
7. **Selection of storms by category** uses agency estimates that vary by basin.

## 11. Scope and framing

Results are port-level ship-call counts from public data. Per-port results are reported as data, not assembled
into a country resilience ranking; the report states what each estimate rests on, including how quiet the port is.

## 12. Process commitments

- Code is committed before the outcomes it produces. `recovery.py`, `analysis.py`, `forecast.py` and
  `score_forecast.py` are committed with this plan and have not been run on outcomes.
- Departures go in deviations.md, timestamped with `date`.
- An independent adversarial review (Fable 5.1) runs on the pre-review draft.
- Released: the event table, per-event recovery times, all code. PortWatch and IBTrACS are public and not
  redistributed.
