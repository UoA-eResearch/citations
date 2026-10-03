# Preregistration: do neural point processes beat ETAS only because the ETAS baseline ignores catalog incompleteness?

Lead: `seismology-geophysics-npp-gain-incompleteness-baseline` (research-lab/leads.json). Written 2026-10-04 and
committed to git before any incompleteness-aware ETAS model has been fitted or evaluated.

## What has been seen before writing (disclosure)

**Literature search** (web, 4 Oct 2026). Neither EarthquakeNPP (Stockman et al., TMLR 2026, arXiv 2410.08226 v3) nor
the Fusion model (Xiong et al. 2026, arXiv 2608.18791) compares neural point processes (NPPs) against an
incompleteness-aware ETAS. Both use standard ETAS. No other such comparison was found.

**Published results** (Stockman, Lawson & Werner 2023, repository ss15859/Neural-Point-Process, commit 6b75508). Its
released per-target-event temporal log-likelihoods give the NPP-minus-standard-ETAS gap G per target event (M ≥ 3) at
the lowest input cutoffs:

| Sequence | Input cutoff | Target events | Gap G (nats per target event) |
|---|---|---|---|
| Visso | 1.2 | 988 | +1.016 |
| Norcia | 1.2 | 861 | +1.612 |
| Campotosto | 1.3 | 152 | +1.385 |

**Stockman's ETAS code and protocol.**

- Temporal ETAS conditioned on all events with mw > cutoff.
- Times in hours. Train/test split at hours 1200, 1800 and 3600 after the first event.
- The test evaluation uses only test events plus 19 burn-in events as history.
- β is estimated from test magnitudes.

**The AVN catalog.** Its size, largest events and event counts by cutoff.

**The Fusion repository** (XiongTLu/FusionEarthquake, commit 9a5ed1d). Its released checkpoints ("PWL_joint")
correspond to no released script, so Fusion is not part of the primary analysis.

**Not yet computed:** any incompleteness-aware ETAS fit, and any ETAS evaluation with full history.

Departures go to `deviations.md` with timestamps from `date`.

## 1. Question

At low input cutoffs, Stockman's NPP beats standard ETAS by 1.0–1.6 nats per target event on the 2016–17 Central
Apennines (AVN) sequence. Is that gain mostly explained by the ETAS baseline ignoring short-term catalog
incompleteness, so that it is a handicapped baseline rather than learned structure?

## 2. Configurations (primary)

Three AVN partitions: Visso (cutoff 1.2), Norcia (1.2) and Campotosto (1.3).

- **Target events:** M ≥ 3 in the test period.
- **Target set and split:** exactly as in Stockman's released results, with the same truncation (mw > cutoff), split
  times and burn-in. A configuration is used only if my re-implementation reproduces Stockman's released standard-ETAS
  pointwise log-likelihoods: mean absolute difference below 0.01 nats, using the released parameters and the same
  truncated-history protocol.

## 3. Models

All models are temporal ETAS with Omori kernel f(t) = (p−1) c^(p−1) (t+c)^(−p) and productivity K e^{α(m−m0)}. They
are fitted by maximum likelihood on the training period with input events mw > cutoff, where m0 is the cutoff.

| Model | Description |
|---|---|
| S0 | Stockman's standard ETAS: released parameters, released pointwise LLs, truncated test history. This is the published baseline in G. |
| S1 | S0's released parameters, evaluated with the full observed history (all prior events above the cutoff). |
| S2 | Standard ETAS refitted here (complete-catalog assumption), with β from the training period and full-history evaluation. |
| A | **ETAS-I (rate-dependent detection; Hainzl 2016, 2021).** See below. |
| B | **Time-varying completeness (Helmstetter et al. 2006 form).** See below. |

**Model A (ETAS-I).** An event at (t, m) is detected with probability D = exp(−T_b λ(t) e^{−β(m−m0)}): it is missed
if a larger event occurred within the blind time T_b.

- The observed-event intensity is λ(t) β e^{−β(m−m0)} D. Integrated over magnitude, the observed rate is
  (1/T_b)(1 − e^{−T_b λ(t)}).
- λ(t) is the true rate above m0, triggered by the observed events.
- Free parameters: μ, K, α, c, p and T_b; β is fitted on the training period.

**Model B (time-varying completeness).** D = Φ((m − m_c(t))/σ), with σ = 0.2 fixed.

- m_c(t) = max(m0, max over prior events j with m_j ≥ 4.5 of [m_j − G − H log10((t − t_j)/1 h)]).
- Free parameters: μ, K, α, c, p, G and H.

**Target-event temporal log-likelihood** (models S1, S2, A, B). For each target event i, with j the previous target
event:

log λ₃(t_i) − ∫_{t_j}^{t_i} λ₃ dt

where λ₃ is the model's intensity of observed M ≥ 3 events:

- S models: λ(t) e^{−β(3−m0)}.
- A: (1/T_b)(1 − exp(−T_b λ(t) e^{−β(3−m0)})).
- B: λ(t) ∫_{3}^{∞} β e^{−β(m−m0)} Φ((m − m_c)/σ) dm.

This matches Stockman's definition. LL is the mean over target events.

**Choosing the primary incompleteness-aware model.** Of A and B, the primary is the one with the higher maximised
training log-likelihood per event, chosen on training data only. The other is reported as secondary.

**Validation before use.** The fitting code must recover the parameters of a synthetic catalog simulated from model A
and from model B (known truth: within 2 standard errors or 10%), and must improve on S2 on Stockman's released
synthetic incomplete catalog. If validation fails, the code is fixed using synthetic data only, before any AVN test
evaluation.

## 4. Primary hypothesis and decision rule

For each configuration, the recovery fraction is

R = (LL_inc − LL_S0) / (LL_NPP − LL_S0)

where LL_inc is the primary incompleteness-aware model with full history. LL_S0 and LL_NPP are the released
per-target-event means. The 95% CI for R comes from a block bootstrap over 24-hour blocks of target events, with
2,000 resamples.

| Verdict | Condition |
|---|---|
| Supported | R ≥ 0.75 in at least 2 of 3 configurations |
| Contradicted | the 95% upper bound of R is below 0.75 in at least 2 of 3 configurations |
| Inconclusive | otherwise |

## 5. Secondary analyses (no verdicts)

- **Decomposition of G.** History effect (S1 − S0), refit effect (S2 − S1), incompleteness effect (A or B − S2),
  and the remainder.
- **The non-primary model** (A or B).
- **R as a function of input cutoff (1.2–3.0)** for each sequence, using Stockman's released NPP and ETAS results at
  each cutoff, where they reproduce.
- **Stockman's synthetic incomplete catalog:** the same comparison, where the generating incompleteness is known.
- **Fusion (Xiong et al. 2026).** Only if its released checkpoints can be evaluated with released code. Otherwise its
  published AVN gains over its own ETAS (+0.14, +0.13 and +0.05) are reported for context only.

## 6. Threats (fixed now)

- **Triggering by undetected events** is not modelled explicitly in A or B; the parameters absorb part of it.
- **β leak in S0.** Stockman's S0 uses β from test magnitudes, a small advantage to S0. S2, A and B use training β.
- **Heavy computation.** The test period at cutoff 1.2 has about 148k events. Full-history intensities use exact
  sums. Integrals use exact Omori integrals where available, and adaptive quadrature for A and B.
- **One sequence.** Only one sequence, the AVN, is studied, with three overlapping test periods, so the result may
  not generalise.

## 7. Review and reporting

- An independent reviewer agent checks code and results before any verdict.
- The report opens with "In plain terms".
- The code and fitted parameters are released.
