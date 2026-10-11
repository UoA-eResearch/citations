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

## D2. SCEDC header variants; local events only (2026-10-11 17:40 NZDT)

The first run of `parse.py` stopped on SCEDC phase-file headers that the format probe had not shown. It stopped
before any matching. Of 54,286 SCEDC files:

| Header | Files | Handling |
|---|---|---|
| Normal | 53,922 | Parsed |
| Placeholder (event ID 0, date 1970-01-01) | 363 | Skipped; no event |
| Missing geographic-type field | 1 | Origin time found by pattern; type left empty, so the event is excluded below |

**The geographic-type field** is `l` (local), `r` (regional) or `t` (teleseism). The plan specifies local
earthquakes, so SCEDC events are kept only with type `eq` and geographic type `l`. Teleseisms would mostly fail
the 100 km filter anyway; regional events located outside the network are dropped.

## D3 - 2026-10-12 01:02 NZDT - analysis crash in H2 (-inf noise covariate); H1 results lost; rerun

The first full analysis run (started 11 October 19:38, about 5 h 20 min) crashed in `h2()`, in the secondary
linear-regression check: `ValueError: Input X contains infinity`. No result had been printed or saved, because
`primary.json` was written only after H2, so no outcome was seen.

**Cause.** Three stations (BK.BABI, BK.QRDG, NC.MDPB) have a median 60-s RMS of exactly zero over their noise hours,
a flat or dead trace, so log10 gave -inf. The primary gradient-boosting model had accepted -inf silently and would
have treated these stations as extremely quiet.

**Changes (code only; no rule changed).**

1. Non-finite `log_noise` is set to missing in `analysis.main()`. Plan section 4 says stations without a usable
   noise hour get a missing value, and a zero-RMS trace is not usable. 22 other stations were already missing
   (21 with no data, 1 with no response).
2. `h1()` writes its bootstrap draws (`results/tables/h1_bootstrap_draws.csv`) and `primary.json` as soon as H1
   is done, and logs progress every 10 refits. The refits use `imap_unordered`. Each refit still uses seed
   20261011 + 1 + b, so results do not depend on order.
3. 13 bootstrap workers instead of 8; the machine is otherwise idle.
4. `tests/smoke_main.py` (new) runs `main()` end to end on synthetic data, with a -inf and a NaN noise value
   planted, in a scratch directory. It passes.

The analysis is rerun from the same matched and covariate files; parse, covariates and match are not rerun.

## D4 - 2026-10-12 05:33 NZDT - post-outcome diagnostics (after the primary results were seen)

The rerun finished (log `logs/analysis.log`). The H1 and H2 verdicts follow the preregistered rules unchanged. Every VB
fit, the main fit and all 200 bootstrap refits, carried statsmodels' "VB fitting did not converge" flag (D1 item 7
anticipated a varying flag; a share of 0 was not anticipated). `fit_vb` also draws its starting values from fresh
entropy unless given a seed, so the main estimate is not bit-for-bit reproducible.

These diagnostics were added after the outcome was seen (`code/checks.py`, `code/run_checks.sh`,
`tests/aghq_test.py`). They are labelled post-outcome in the report and change no verdict:

1. **VB refits with fixed starting seeds** (1, 2, 3; BFGS as in the primary fit) and one with L-BFGS-B. They record
   the optimiser's message, iterations and gradient norm.
2. **An independent maximum-likelihood fit** of the same model by adaptive Gauss-Hermite quadrature (1 and 15 nodes,
   as in lme4's `glmer` nAGQ), from two starting points. Tested on synthetic data first: a known station SD of
   1.074 (sample) was recovered as 1.073.
3. **Checks of bookkeeping.** The station order of the VB effects against the model's level names; the busiest month's
   share (the plan's conditional subset); SD_p at other reference events.
4. **The plan's exploratory false-pick proxy** (section 6), which `analysis.py` had not implemented.
   - Definitions fixed here: catalogue P picks with confidence >= 0.5, with no reference pick of either phase at the
     station within 1 s, and no catalogue P pick at another CI, NC or BK station within 10 s.
   - Rate per loaded station-day in the sampled months.
5. **H2 exploratory.** Single-covariate and location-only cross-validated R², and H2 with the ML station effects
   as the target.

**D4 addendum (2026-10-12 05:56 NZDT).**

- **The AGHQ fit was restarted.** The first attempt (one process; tolerances xatol 1e-6, fatol 1e-4) had printed
  nothing after 19 minutes and was stopped. In a second attempt, the fits started from the VB estimate wandered to
  absurd values: the warm-started Newton iteration for the station modes diverged after large simplex moves. The
  Newton steps are now clipped to ±1, with a restart from zero if they have not converged. The four fits (1 and 15
  nodes; VB and zero starts) run in parallel with tolerances xatol 1e-4 and fatol 1e-3 (`code/run_aghq.sh`). The
  synthetic test gives the same answer as before.
- **A post-hoc variant of the false-pick proxy** (`checks.py falsepick_nn`). The preregistered isolation test was met
  by chance: there are about 0.4 P picks per second across CI, NC and BK, so almost every pick has another station's
  pick within 10 s. The variant calls a pick isolated if none of the station's 5 nearest catalogue stations has a P
  pick within 10 s.
  - **Validated on picks an analyst confirmed:** 0.9% of referenced picks with confidence ≥ 0.5 are flagged, against
    62% of unreferenced ones.
  - Both the preregistered and the variant results are reported, labelled exploratory.
- **Figures** (`code/figures.py`) recompute the H2 out-of-fold predictions. They reproduce R² exactly (asserted).
