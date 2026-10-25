# Independent review: auckland-nz-avf-dvv-hydrological-baseline

Reviewer: Fable (fresh context), 2026-10-25. Scripts and outputs: `review/reviewer_checks/` (`load_cache*.py`,
`model_checks.py`, `ccf_checks.py`, `remeasure.py`, and their `.log` / `.json` / `.csv` / `.parquet`). No study file
outside `review/` was modified. Nothing was re-downloaded; all checks read `data/ccf`, the result tables and
`data/raw/era5_daily.csv`.

## Verdict: fix first

H1 "Refuted" survives every variant I ran (six corrupted pairs removed, constant-only and season-only baselines,
cubic interpolation, KBAZ re-segmented): the median held-out R² stays negative and no pair reaches 0.5. But the
numbers in the verdict block, the title's "noise floor near 0.14%", a G6 literature statement and the dv/v table
itself are not publishable as they stand:

1. six of the 32 scored pairs (all with KBAZ) are measured against a reference that mixes two sensor polarities, and
   52 dead-channel days enter the table as +2.05%; their R² of −22 to −1499 are processing artefacts;
2. the published Brenguier et al. (2008) abstract does say velocity decreases "of the order of 0.05%", so the
   report's G6 "correction" asserts something false;
3. "noise floor 0.14%" is the residual of a model that does worse than a constant; the data's own 30-day wander is
   about 0.08%;
4. linear interpolation on 20 Hz lags makes the stretching multimodal and the dv/v values banded for low-SNR
   pairs (it does not change the verdict, but the published series carry the artefact), and the coherence filter
   admits pairs whose coda SNR is below 1.

Provenance is clean: plan 18fd367 10:38 → correlate.py 0d69233 10:40 → dvv.py / model.py / forcing.py 8c2e926 10:42;
first `data/ccf` files 11:15; `dvv_daily.parquet` 19:59 and `fit.csv` 20:00 the same day. The only later change to
model.py is the `sys.path` line (diff checked). `data/raw/era5_daily.csv` has no gaps (5,387 days), so the
`fillna(0)` / `interpolate()` fallbacks never fired. My re-implementation of the stretching reproduces
`dvv_daily.parquet` exactly (max difference 0.0, `remeasure_summary.csv`), and my refit reproduces every `fit.csv`
held-out R² and τ (`model_checks.log`).

## Findings

### 1. Major (data/processing): KBAZ flipped polarity across a 3.5-year gap and had a dead-channel block; one plan segment holds all of it

- KBAZ has files for 2013-01 to 2014-08-25 and again from 2018-03-21, none in 2015–2017 (`ccf_checks.log`, station
  availability). The FDSN epochs show no gap but change Dip from +90 to −90 on 2014-08-25
  (`results/tables/fdsn_channels.txt`). `dvv.py:25-44` builds segments from the metadata only, so the plan's "gap of
  more than 7 days" never sees the data gap and KBAZ is one segment 2008–2023.
- The 2013–14 and 2018–20 training stacks of AWAZ-KBAZ correlate at **−0.986** at zero lag (ETAZ-KBAZ −0.952;
  `ccf_checks.json: kbaz_polarity`). The reference averages two polarities, and the 2013–14 days are stretched
  against an inverted waveform: 51–92% of AWAZ-KBAZ and ETAZ-KBAZ days in 2013–14 sit at the ±2% grid edge, and
  HBAZ-KBAZ / EPAZ-KBAZ / KBAZ-WTAZ sit at ±1.2% (a half-cycle skip) before snapping to ~0 in 2018
  (`kbaz_by_year.csv`, `scored_pairs_median_dvv_by_year.csv`).
- A second block: 2018-08-22 to 2018-10-31, **520 rows, all ten KBAZ pairs, 52 days each, every one dv/v = +2.05%
  with cc = 0.000** (`dead_channel_check.log`). That is what `dvv.py:118-129` returns when the current stack is
  flat in the window (cc is 0 for every ε, `argmax` takes the first grid point). A zero-valued (dead) channel
  passes the 20 h check and the transient mask (`correlate.py:78,100`: median RMS 0, `0 <= 0`), whitening maps a
  zero spectrum to zero, and the day enters the table. All 312 such rows in scored pairs are in training.
- The model then "explains" the polarity step and the +2% block with cumulative rain (AWAZ-KBAZ training R² 0.93,
  rain coefficient 0.003) and extrapolates it: held-out R² −1499, −220, −163, −150, −68, −22. These six values set
  the bootstrap's lower bound (−0.67) and inflate the residual floor.
- Re-segmenting KBAZ at the gap (`remeasure.py`, two references) drops AWAZ-KBAZ's training R² from 0.93 to 0.24
  (the 0.93 was the flip) but leaves held-out R² at −20 to −184 because the +2.05% block is still in training; the
  2018-08 to 2020 and 2021–23 medians agree to 0.01% once it is out (`remeasure.log`).
- Without the six KBAZ pairs: median held-out R² **−0.064 (−0.17 to −0.003)**, 26 pairs, 19 negative, median 2 SD
  residual **0.096%** (`model_checks.log: NON-KBAZ 26`). Still Refuted, but not the published numbers.
- **Fix.** (a) Segment on data gaps > 7 days (the plan's own wording) and on the dip change; (b) reject a day whose
  coda has zero energy or whose cc at ε = 0 is negative, in `correlate.py` or `dvv.py`; (c) recompute
  `dvv_daily.parquet`, `fit.csv` and every downstream table and figure. If KBAZ cannot be made consistent, drop its
  pairs and make the 26-pair result primary. Record as a post-result D-entry. (A G3 hand trace would have caught
  this: dv/v of 2% is not hydrology.)

### 2. Major (G6, false statement in the verdict block): the 0.05% figure is in the published abstract

- Ledger row A2 marks the lead's 0.05% as "not found", citing a search of the arXiv preprint (0706.1935), whose
  abstract says "less than 0.1%". The **published** Nature Geoscience abstract (doi 10.1038/ngeo104, fetched
  2026-10-25) states that velocity decreases "of the order of 0.05%" preceded the eruptions. The preprint is not the
  cited source.
- `report.md` verdict bullet "The lead's 0.05% target is not supported by that source: the 0.05% figure does not
  appear in its text (G6)" is false, and `deviations.md` (pre-review gate entry) repeats it.
- **Fix.** A2 → "supports", locator "published abstract", conditions "size of the precursory decrease, not the
  measurement precision"; keep A12 (precision better than 0.1%). Rewrite the two verdict bullets: 0.05% is the
  precursor size at Piton de la Fournaise, the paper's daily precision is better than 0.1%, and the comparison must
  use the corrected floor from finding 3. Overclaim rows: **17 Overstated** (false), **16 Partially supported**
  (the paper says "better than 0.1%", and the 0.14% it is compared with is wrong).

### 3. Major (interpretation, title): "noise floor near 0.14%" is the failed model's residual, not the data's floor

- 0.136% is the median 2 SD of residuals from a model whose held-out R² is negative on 25 of 32 pairs, i.e. worse
  than the held-out mean. The 2 SD of the 30-day-smoothed held-out dv/v about its own mean is **0.080%** (32
  pairs) / 0.084% (26 non-KBAZ); a season-only model trained on 2013–2020 leaves 0.076% on the 26
  (`model_checks.log`). The raw 10-day values wander 0.14% (2 SD), which is the measurement noise of a 10-day stack.
- Title, verdict bullet, plain-terms sentences 28 and 30 and the Brenguier comparison all rest on 0.14%. With the
  data's own floor near 0.08%, the comparison with 0.05% precursors and <0.1% precision reads differently and must
  be rewritten, not re-numbered.
- **Fix.** Report the preregistered statistic as "2 SD of the model residual" with the no-model and season-only
  floors beside it; take the 0.14% out of the title; make the plain-terms sentence about the data's wander
  (about 0.08% at 30-day smoothing, 0.14% at 10 days). Overclaim rows 1, 15, 28, 30: **Partially supported** as
  written.

### 4. Medium (measurement): linear interpolation at 20 Hz makes the stretching multimodal and the dv/v values banded

- `dvv.py:125` samples the current stack with `np.interp` on the 0.05 s lag grid. For a coda window centred at
  36–50 s, half a sample of shift is 0.05–0.07% dv/v. Histograms of the 10-day dv/v for ABAZ-MBAZ and MBAZ-WIAZ have
  **no values** in |dv/v| < 0.04% or near ±0.125%, and peaks at ±0.06% and ±0.19%, odd half-samples at the window
  centre (`step_2018_check.log`). On a real ABAZ-MBAZ stack the linear cc(ε) curve has four local maxima within
  0.05 of the best; a cubic spline gives one (`ccf_checks.json: cc_surface`).
- Synthetic stretches (`ccf_checks.json: synthetic`): sign and magnitude are **correct** (injected +0.50% →
  +0.495%, +0.03% → +0.030%, noiseless; the 0.005% error is the fine-grid quantum). With noise at ABAZ-MBAZ's
  measured 10-day-stack SNR (0.56), a true 0 never returns |dv/v| < 0.04% with linear interpolation (0 of 100)
  and does 21% of the time with cubic; the spread is the same (SD 0.16%). No signal is destroyed, but low-SNR
  series are bimodal and their 30-day mean is a duty cycle of band occupation.
- Re-measuring 14 pairs with cubic interpolation (`remeasure_summary.csv`): ABAZ-MBAZ's share of |dv/v| < 0.04%
  goes from 0.001 to 0.19, held-out R² move by ≤ 0.05 on coherent pairs (AWAZ-EPAZ −0.187 → −0.155, EPAZ-HBAZ
  −8.33 → −8.07, HBAZ-WTAZ 0.329 → 0.342). The verdict is insensitive; the published series are not.
- **Fix.** Band-limited interpolation (cubic spline or ×10 upsampling) before stretching; re-run `dvv.py`; D-entry.
  The plan's 0.01% grid was also replaced by a 0.05% coarse grid with 0.005% refinement without a deviation entry.

### 5. Medium (scoring): the coherence filter does not screen out noise-dominated pairs

- The filter uses the mean of the **maximum** cc over 81 + 21 trial stretches of a 20 s window holding about 25
  cycles, which selection inflates. ABAZ-MBAZ passes at 0.53 with a 10-day-stack coda SNR of 0.56; a single day
  correlates at 0.09 with its reference (`ccf_checks.json: spot_days`, `synthetic`); its 30-day held-out dv/v has a
  2 SD of 0.20% against EPAZ-HBAZ's 0.08%. For several scored pairs the causal and acausal coda are uncorrelated
  (HBAZ-WTAZ −0.16, ETAZ-KBAZ 0.05, ABAZ-MBAZ 0.21 over 0–100 s), so the symmetric fold halves the coherent part.
- Consequence: "32 scored pairs", the median R² and the residual floor mix a handful of coherent pairs with many
  noise series.
- **Fix.** Add an SNR or ε = 0 coherence criterion, or report by SNR tercile, and say how many pairs carry the
  result; keep the preregistered 32 alongside.

### 6. Medium (secondary 4 is hollow): "every epoch boundary a break" only truncates the held-out window

- `model.py:81` swaps the segment table, but `fit_pair` (`model.py:56`) keeps the `seg` labels, references and
  constants that `dvv.py` computed under the plan rule. Secondary 4 therefore changes `ho_end` for 34 pairs and
  nothing in training; the identical median (−0.1238) is a coincidence of the median pair.
- **Fix.** Recompute dv/v with every-epoch segments, or reword the row and bullet as "held-out windows truncated at
  the first epoch boundary". (A 90-day step test at the 2018-07-05 network-wide boundary gives |z| > 2 only for
  KBAZ pairs, `step_2018.csv`, so the training-period effect is probably small once finding 1 is fixed.)

### 7. Medium (gates): G3 missing, G2 has no coverage file and one silent fallback is live

- No `results/plausibility.md`. 5,743 dv/v rows (3.0%) sit at the ±2% grid edge; 22% of ETAZ-KBAZ days. An
  expected-range check or one hand trace of a KBAZ day would have stopped the draft. Report it as a missing gate
  even though the study predates METHODS.md.
- No `coverage.json`. The dead-channel path in finding 1 is a silent fallback that entered a statistic (G2's
  definition). `correlate.py:119-122` also turns any exception into a dropped station-day without a reason (the
  `have` array records it, so it is recoverable). Window counts are sound: 0 pair-days with 1–23 windows; valid
  days have 46–47 of 48 windows (the last window always fails the gap test); 207,871 of 276,155 pair-days valid.
- G5 and G6 pass mechanically; rows 16–17 and 1/15/28/30 need the relabelling above. Ledger A5 labels a background
  statement in an imaging paper as "main finding", and that abstract mentions ocean-generated noise, not cultural
  sources (those come from A6). A1, A3, A6 and A12 check out against their abstracts.

### 8. Minor (numbers and consistency in report.md)

- "Median training coherence is 0.51 across 53 pairs": `fit.csv` gives **0.53** (0.5256; also `secondary.json`).
- `results/figures/F1_heldout_r2.png` still carries the pre-G5 title wording ("Rainfall and season do not
  predict…"); `figures.py:48` was not updated with the report title.
- "10-day centred moving stack" is ±5 days inclusive, i.e. 11 days (`dvv.py:111-112`).
- "Deviations: technical only" undersells the grid change (finding 4) and, after this review, the segmentation.
- Plain terms "25 of the 32 pairs… worse than guessing their average": six of the 25 are the KBAZ artefacts;
  recount after the fix.
- The lockdown test compares adjacent 30-day windows on a series smoothed over ±15 days, so the step leaks into
  the "before" window; with a guard the median step is 0.0048% instead of 0.0068%, conclusion unchanged
  (`model_checks.log`). The two pairs beyond 2 SD are AWAZ-EPAZ and AWAZ-MBAZ; the single 2023 pair beyond 2 SD is
  HBAZ-KBAZ (finding 1), and the non-KBAZ median 2023 residual is +0.028%.

## What checked out

- Git order (above). `correlate.py`: 8 Hz anti-alias then ÷5 from 100 Hz (every epoch is 100 Hz), 0.3–5 Hz
  band-pass, per-window whitening with a 0.25–0.35 / 4.5–5.5 Hz cosine taper, 2 s RAM, zero-padded (linear)
  correlation, correct lag re-ordering; transient mask on pre-whitening RMS at 5× the median; ≥ 24 common windows.
- Stacks are plausible noise correlations: apparent group velocities from the envelope peak 0.7–2.0 km/s; coda
  SNR against the last 5 s from 83 (EPAZ-HBAZ) down to 1.6 (AWAZ-KBAZ); asymmetric sides as expected for an
  urban and coastal source field. Spot days: EPAZ-HBAZ 2015-06-15 correlates 0.87 with its reference, AWAZ-ETAZ
  2019-03-10 0.63, HBAZ-WTAZ 2017-11-02 0.53.
- `dvv.py`: window t₁ = max(5, 2d/1.5) to t₁ + 20 s, symmetric fold correct, reference from training days of the
  same segment, stretching sign correct (synthetic), fine grid 0.005%.
- `model.py`: P_τ uses rain strictly before the day (impulse test: P[100] = 0, P[101] = erfc(√τ),
  P[110] = erfc(√(τ/10))), training-mean rain subtracted, one dummy per training segment, held-out restricted to
  segments seen in training, R² about the held-out mean, τ by training R² only, bootstrap with the stated seed
  reproduces the CI exactly.
- Post hoc checks: `posthoc_drift.py` freezes t at its last training value with the same β; `posthoc_kernel.py`
  swaps the kernel and reruns the pipeline unchanged. Both do what the report says. The temperature variant shifts
  the series back L days and selects L with τ on training R² only.
- Verdict logic: the median is negative under every variant tried here, so "Refuted" is fair; the constant-only
  and season-only baselines (−0.42 and −0.34 on 32 pairs; −0.17 and −0.09 on 26) show the failure is not only the
  cumulative kernel or the drift.

## Confirmation pass

Reviewer: Fable (same reviewer), 2026-10-26, on commit 4f87c4f. Checks: `review/reviewer_checks/confirm_checks.log`
(v1 vs D1 per pair, segment starts, drop locations, level offsets). G5 (`--verify`, 36 rows) and G6 (12 claims)
pass. Every report number I checked matches the new tables (median and CI, 26 of 31, training R² 0.17, the four
variants, the three floors, lockdown with and without guard, 2023, τ counts, pair types, coverage counts, EPAZ-HBAZ
−5.3, season-only better on 23 of 31).

### Verdict: publish with edits

Findings 1–8 are resolved in substance. The data-gap rule used to fix finding 1 is blunter than it needs to be and
has side effects the report does not name (item 9); either re-run with a longer gap threshold or state the choice
and its effect in the verdict block. H1 "Refuted" is unaffected either way.

1. **Finding 1 (KBAZ) — resolved.** Segments break on dip changes and data gaps (`segments.csv`: KBAZ 2008–2014-08-25
   and 2018-03-21–2023-11-21); dead-channel days (852) leave references and stacks; negative zero-stretch days (959)
   are dropped; all counted in `coverage.json`. KBAZ pairs now give held-out R² −0.15 to −5.7 instead of −22 to
   −1499, and AWAZ-KBAZ's training R² falls from 0.93 to 0.45, which confirms the old fit was the polarity step.
2. **Finding 2 (Brenguier) — resolved.** A2 is "supports" with the published abstract as locator; the verdict and
   plain-terms sentences now use 0.05% as the precursor size; A5 is background on ocean noise with cultural noise
   under A6; METHODS.md G6 asks for the version of record.
3. **Finding 3 (floors) — resolved.** Residual 0.076%, no-model 0.074% and season-only 0.067% stand side by side,
   and the title now carries the data's month-scale wander (0.07%), not the model residual.
4. **Finding 4 (interpolation) — resolved.** `dvv.py` evaluates the stretched trace with a cubic spline (vectorised
   over the grid); the 0.05%/0.005% grid and the plan's 0.01% are stated. Hand traces agree with the table to one
   fine-grid step.
5. **Finding 5 (scoring) — resolved as a post hoc breakdown.** The zero-stretch coherence of the 11-day stack is
   stored (`cc0`), and the 22 pairs with median cc0 ≥ 0.7 give −0.27, the same as all 31. Adequate.
6. **Finding 6 (secondary 4) — resolved.** `RULE=every_epoch` recomputes references and dv/v
   (`dvv_daily_every_epoch.parquet`, `segments_every_epoch.csv`); the variant is −0.18 (−0.38 to −0.04) on 32 pairs.
7. **Finding 7 (gates) — resolved.** `results/plausibility.md` has expected ranges, three hand-traced pair-days
   (`handtrace.json`) and the invariants; `coverage.json` records every drop with a reason.
8. **Finding 8 (minor) — resolved.** Coherence 0.54, F1 title, 11-day stack, guarded lockdown windows (both
   reported), lockdown and 2023 outlier pairs consistent with the tables.
9. **New problem (medium): the 7-day data-gap rule splits records at routine outages, and the report does not
   separate its effect from the KBAZ fix.** My review suggested "data gaps > 7 days"; that was too blunt. Applied
   literally it yields 16 MKAZ segments, 7 for WIAZ and RVAZ, 5 for ABAZ and AWAZ (`segments.csv`), with these
   effects (`confirm_checks.log`):
   - held-out windows now end at outages, not sensor changes: MBAZ pairs at 2023-06-29 (an 8-day outage) instead
     of 2025-03-11 (910 vs 1,524 days), WIAZ pairs at 2023-01-11, MKAZ pairs at 2021-06-20 (157–168 days, so
     ETAZ-MKAZ is no longer scored);
   - 15 of the 31 scored pairs rest on a held-out segment with under two years of training (AWAZ from 2019-01-28
     after 10- and 17-day outages, RVAZ from 2019-07-02, WIAZ from 2020-06-19, MBAZ-WIAZ 196 training days); their
     median R² is −0.31 against −0.21 for the rest;
   - the AWAZ pairs acquire a level offset from the short segment's constant plus the extrapolated drift: AWAZ-EPAZ
     −0.19 → −15.5 and AWAZ-ETAZ −22.6 → −27.0 with mean held-out residuals of 2.9 and 4.4 held-out SDs; six scored
     pairs are offset-dominated. This is the same failure mode as finding 1 in miniature.
   - The non-KBAZ median moved from −0.06 (v1) to −0.21, and the report attributes the change to "the review
     fixes" without saying which. With held-out 2 SD of 0.03–0.07%, a 0.02% level offset moves a pair's R² by
     about −0.3, so the median's value (not its sign) is fragile to segmentation choices.
   - **Fix (preferred).** Keep the dip rule and the per-day dead-channel and polarity drops, which are what catch
     KBAZ, and raise the data-gap threshold to one that signals reinstallation (90 days or more); report both
     thresholds. **Minimum.** State in the verdict block and in D1 that the 7-day data-gap threshold is a post hoc
     choice, list the held-out windows it truncates and the pairs it unscores, and give the ablation (KBAZ-only
     split vs the full rule). Either way the verdict stands.
10. **Housekeeping (minor).** `results/figures/v1_pre_review/` holds only F1 (D1 says the first-version figures are
    kept there; add F2 or say so); `results/tables/v1_pre_review/dvv_daily.parquet` is untracked in git while D1
    says the v1 outputs are kept (commit it or note that the parquet is local only).
