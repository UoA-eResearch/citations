# Plausibility gate (G3)

## 1. Headline numbers against expectation

| quantity | value | expected range and source | plausible? | notes |
|---|---|---|---|---|
| significant rate at matched pseudo-triggers (station null p0) | mean 7.0% (all quintiles 6.8-7.0%) | about 5% for a beta >= 2 criterion; clustering raises it (Hardebeck et al. 2025: 3.5-8.5% per test) | yes | |
| observed significant rate after real triggers | 6.6% | equal to p0 if no triggering | yes | 15,042 observed, 15,742 expected |
| proxy recall of ComCat M >= 1 within 30 km | 46% of 7,897 events, nearly flat with magnitude | a strict 3-station P-S proxy misses very near events (S-P < 0.8 s) and sparse-network events | yes, by design | diagnostic of M >= 3 misses in deviations.md |
| local-event pairs per station-week (population baselines) | mean 36.7 per 7 days | a few to hundreds per week in active California networks | yes | 21% of pairs have no local pair in either window |
| estimated vs measured peak velocity | Spearman 0.4692; 71% within one quintile (2,546 of 6,634 station x trigger pairs measured at 40 broadband stations) | moderate agreement expected without site terms | yes | 4,086 requests returned no LHZ data |

## 2. Three units traced end to end (`code/handtrace.py`, seed 20261026; `results/tables/handtrace.json`)

| unit | raw input | intermediate values | output | matches the pipeline? |
|---|---|---|---|---|
| CI.DRE. x us6000r2xq (M7.5, 11,442 km) | raw picks of the station and its 199 neighbours within 50 km | independent P-S pairing, t0, 3-station coincidence, hourly windows | post 0 / base 10 (trace) vs 0 / 10 (table) | yes, exactly |
| NC.JBG. x usp000hrw0 (M7.3, 9,657 km) | raw picks of the station and its 925 neighbours within 50 km | independent P-S pairing, t0, 3-station coincidence, hourly windows | post 0 / base 1 (trace) vs 0 / 1 (table) | yes, exactly |
| NC.KHMB. x usp000dhc1 (M7.1, 11,853 km) | raw picks of the station and its 73 neighbours within 50 km | independent P-S pairing, t0, 3-station coincidence, hourly windows | post 0 / base 1 (trace) vs 0 / 1 (table) | yes, exactly |

The trace omits teleseismic masking (as stated in its note); all three agree exactly.

## 3. Invariants

| invariant | where | holds? |
|---|---|---|
| every pick read is kept or dropped with a reason | `coverage.json` picks_fetch, picks_proxy | yes: 531,327,099 kept of 2,088,914,320 read; 515,102,630 after merging and masking |
| every station x trigger pair is in the population or dropped with a reason | `coverage.json` pairs_primary | yes: 228,963 in the population of 3,276,936 |
| real and pseudo triggers pass identical validity rules | `windows.test` (one function for both) | yes by construction |
| pseudo-trigger seeds are deterministic across processes | `windows.station` (crc32 of the station id, not Python's salted hash) | yes |
| the strain estimate uses only magnitude and distance | `windows.strain` | yes (G1) |
