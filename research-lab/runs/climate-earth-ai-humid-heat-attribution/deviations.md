# Deviations log: AI humid-heat attribution deep dive

Every departure from `plan.md`, with a timestamp (NZDT) taken from `date`. Newest last.

### D1. Preregistration (2026-10-01 11:29:14)
`plan.md` committed as 4691f29, before any event was selected or any forecast run.

### D2. Events selected by the rule; implementation notes (2026-10-01 11:37:56)
`code/select_events.py` computed ERA5 2 m wet-bulb temperature at 06, 12 and 18 UTC for May-September 2023-2025 in
the three boxes. Six events were selected (`results/tables/events.csv`):

| Region | Date | Peak TW |
|---|---|---|
| Persian Gulf | 2024-06-22 | 33.8 degC |
| Persian Gulf | 2025-08-07 | 33.2 degC |
| South Asia | 2024-05-23 | 32.9 degC |
| South Asia | 2023-05-21 | 31.8 degC |
| US Gulf coast | 2023-08-12 | 30.2 degC |
| US Gulf coast | 2024-07-02 | 29.3 degC |

- Both Persian Gulf peaks lie over the sea (26 N, 51 E), as the plan allows (land and sea points). The area-mean
  metric uses land points only.
- Implementation details not specified in the plan:
  - anemoi-inference 0.4.9 and anemoi-models 0.3.1, the versions pinned by ECMWF's notebook; newer versions cannot
    load the checkpoint.
  - torch 2.4.0 with flash-attn 2.6.3, which the checkpoint requires.
  - ERA5 soil fields are named `swvl1/2` and `stl1/2` in the checkpoint.
  - Counterfactual A caps specific humidity so that relative humidity does not exceed max(1, its original value), and
    keeps any original dewpoint excess over temperature. With this, a zero-delta counterfactual reproduces the factual
    state exactly (validation V3).

### D3. Forecasts, nondeterminism check, and results (2026-10-01 14:25:29)
**GPU windows** (plan §7). The shared vLLM server was stopped twice and restarted each time by a trap in
`code/gpu_window.sh` / `code/gpu_noise.sh`:

| Window | Stopped | Restart begun | Serving again |
|---|---|---|---|
| Forecasts | 12:22:51 | 13:35:48 | 13:37:59 |
| Noise check | 13:54:47 | 13:57:13 | 13:59:14 |

The final check of `/v1/models` returned HTTP 200 at 14:24.

**Forecasts.** 234 completed (6 events x 3 leads x 13), plus the V3 run. About 1.6 s per 6-hour step.

**V3 failed at the forecast level, and was then quantified.**
- The zero-delta counterfactual reproduced the factual initial state exactly (max abs difference 0.0).
- Its forecast differed slightly (max abs 2.15, in surface pressure in Pa), because AIFS on this GPU (flash-attention,
  reduced precision) is not bit-reproducible.
- Not in the plan: the factual lead-2 forecast was repeated twice per event (`code/noise_check.py`,
  `results/tables/noise_check.csv`). Run-to-run range of event-peak TW is at most 0.020 degC (area-mean 0.004 degC).
  Max abs differences are 2t 0.06 K, 2d 0.22 K and sp 4 Pa. This is negligible against the attributable signals of
  about 1 degC.

**Results** (`results/tables/hypotheses.csv`, `attribution.csv`, `per_forecast.csv`):
- **H1:** R = 1.21 [1.06, 1.38]; contradicted (upper bound < 1.5).
  - Area-mean TW: 1.40 [1.05, 1.76].
  - The static ratio, with no forecast, is 4.37 [4.00, 4.79].
- **H2:** forecast / static ΔTW_B at lead 2 is 0.99 [0.63, 1.68]; inconclusive.
- **H3** (mean ΔTW_A / ΔTW_B, degC):

  | Lead (days) | 2 | 4 | 6 |
  |---|---|---|---|
  | ΔTW_A | 1.06 | 1.05 | 1.07 |
  | ΔTW_B | 1.11 | 1.31 | 1.41 |

  Static: 0.26 and 1.12.
- **V1:** the factual forecasts underestimate event-peak TW at lead 2 by 1.75 degC on average (all six negative). Two
  of six events exceed 2 degC, so the study is not labelled as limited by skill (the rule needed more than half).
  Area-mean errors are small (-0.3 degC on average).
- **V2:** factual minus counterfactual (B) global-mean 2 m temperature at the end of the forecast is 0.995 of the
  imposed value: the model keeps the signal.

**Mechanism** (exploratory, `results/tables/mechanism_2t_2d.csv`).
- In world A, specific humidity and 2 m dewpoint were unchanged at the start. By the event day, forecast land 2 m
  dewpoint is 1.3-1.5 K below the factual run, about as much as 2 m temperature (1.1-1.3 K): AIFS removes the moisture
  within two days.
- In world B the dewpoint drop (2.1-2.4 K) slightly exceeds the temperature drop (1.7-1.9 K).

### D4. Independent review and linearity control (logged 2026-10-01 14:54:27)
A separate reviewer agent (Fable 5.1) returned FIX FIRST.

**What it reproduced.** attribution.csv, H1 1.209 [1.055, 1.378], the wet-bulb solver, event selection, valid times,
counterfactual signs, hydrostatic z500 (-35 m against -38 m expected), and CMIP6 regridding.

**Main objection.** The forecast change does not track the imposed signal member by member:
- corr(forecast dB, static dB) = 0.01;
- members whose local surface signal is negative (CESM2-WACCM and AWI-CM-1-1-MR, May South Asia, aerosol-dominated)
  still give +0.5 to +2.6 degC.

It asked whether the ~1 degC drop is a perturbation artefact.

**Linearity control, not in the plan** (`code/control_scale.py`, `results/tables/control_linearity.csv`).
- Design: signals scaled by -1 (warming added) and 0.5, for E1 and E5, lead 2, all six models, A and B: 48 forecasts.
- Third GPU window: vLLM stopped 14:41:54, restart begun 14:50:59, serving again 14:52:50.
- Mean event-peak TW change, F minus CF, degC:

  | World | x1 | x0.5 | x-1 |
  |---|---|---|---|
  | A | +1.25 | +0.65 | -1.12 |
  | B | +1.52 | +0.83 | -1.49 |

- The response flips sign and scales with the signal. It is a real, roughly linear response, with a small even
  (perturbation) component of 0.02-0.07 degC.
- Because it does not track the local surface signal, AIFS responds mainly to the column-wide signal (all models cool
  the free troposphere by 1.5-2.3 K), not the local surface change.

**Other checks** (`code/review_checks.py`, `results/tables/review_checks.csv`):
- **World A is partly saturated at the start.** Share of above-ground points at RH >= 0.999, factual vs A:
  - 925 hPa: 1% vs 17%;
  - 850 hPa: 1% vs 11-13%;
  - E3 region at 2 m: 0% vs 7.7%.

  Part of A's "self-correction" is the model shedding this moisture.
- **R by lead** (peak): 1.05 [0.85, 1.22] at 2 days, 1.25 [1.07, 1.49] at 4, 1.32 [1.01, 1.66] at 6.
- **R by lead** (area-mean): 1.39 [1.01, 1.73], 1.29 [0.86, 1.74] and 1.55 [1.30, 1.84].
- **Verdict qualification.** The pooled preregistered H1 verdict (contradicted) holds, but the lead-6 peak result is
  inconclusive, and the area-mean result over all leads (1.40 [1.05, 1.76]) is inconclusive under the same rule.
- **Leave-one-event-out R:** 1.16-1.27 (1.17 without E3).
- **Model-cluster bootstrap:** [1.19, 1.23].
- **Per-member forecast/static dB at lead 2:** median 0.80 [IQR 0.55, 1.25]; 4 of 36 negative.
- **E3 (2024-05-23, 22.3 N 76.7 E) is likely an ERA5 inland-water artefact** at the Indira Sagar reservoir: 2 m
  dewpoint 29.4 degC against a neighbour mean of 21.7. The preregistered rule selected it. It is kept and flagged.
- **Static R of 4.37 is the thermodynamic expectation.** dTW/dT is 0.21 at fixed vapour pressure and 0.93 at fixed
  RH. It is reported as a reference, not a finding. The static change uses surface signals only; the forecast responds
  to the whole column.
- **Mechanism by event** (land, F - CF): in A, the dewpoint drop ranges from 0.8 to 2.3 K against a temperature drop of
  0.8-1.4 K, varying by event; in B, dewpoint mostly falls more than temperature (over-drying). The mechanism code is
  now in `code/review_checks.py`; the earlier inline computation is superseded.
- **Global mean weighting.** "Global mean" weights by cos(latitude) on the reduced Gaussian grid, so it is
  tropics-weighted. The V2 ratio is unaffected.
