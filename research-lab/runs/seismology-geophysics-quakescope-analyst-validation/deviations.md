# Deviations from the preregistered plan (plan.md, commit 5bb0f02)

## D1. Implementation clarifications, before any matching (2026-10-11 16:51 NZDT)

All of these were decided while writing the code. No reference pick had been matched to a catalogue pick, and no
recall had been computed.

1. **NCEDC review status.** The plan says "reviewed catalogues" but did not name a filter. The NCEDC catalogue (2019
   probe) mixes final (F) and automatic (A) events about equally. Only events with status F are used.
   - **Join:** the per-year catalogue CSV (`earthquake_catalogs/NCEDC/YYYY.ehpcsv`, NCEDC public S3), joined by event
     ID, supplies status, event type (`eq`) and magnitude.
   - **SCEDC:** its event phase files have no status field and are used as published (event type `eq`).
2. **Distance floor.** `log10(distance)` uses distance floored at 1 km, since NCEDC lists distances down to 0.0 km.
3. **Band covariate: the plan's wording conditions on the outcome.** The plan says "modal read band over its matched
   days". Read literally, that conditions on the outcome. The covariate is instead the modal read band over the
   station's denominator days: loaded days with at least one reference P pick.
4. **The noise hour.** Bytes covering about 08:30-10:30 UTC are read from each day-long miniSEED file, aligned to the
   record length (blockette 1000), then trimmed to 09:00-10:00. Response removal uses a pre-filter of 0.3, 0.5, 0.4·fs
   and 0.45·fs Hz.
5. **Noise stations.** Noise and the other H2 covariates are computed only for stations with at least 30 denominator P
   picks (the H2 set). That set is defined from reference picks and availability, not from matches.
6. **The bootstrap.** Stations drawn more than once get distinct labels, so each copy has its own random effect.
7. **Convergence.** The variational-Bayes convergence flag is recorded for the main fit and as the share of
   bootstrap refits. Here, as in the previous study, it varies from run to run with stable estimates.
8. **Reference tables.** The SCEDC and NCEDC phase formats are parsed as described in `code/parse.py`, with NCEDC's
   Hypoinverse Y2000 implied decimals. The parse filters are those of plan section 3, plus item 1.

The synthetic test (`tests/synthetic_test.py`) recovers a known between-station SD (0.158 against 0.159) and a known
covariate structure (spatial-CV R² 0.62).
