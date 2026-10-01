# Deviations log: meta-analytic prior shrinkage deep dive

Every departure from `plan.md`, with a timestamp (NZDT) taken from `date`. Newest last.

### D0. Preregistration (2026-10-01 22:04:40)
`plan.md` committed as 3c47ad0, before any first-level model was fitted or any group map computed.

### D1. How the empirical-Bayes likelihood is maximised (2026-10-01 22:23)
The plan names a joint L-BFGS-B fit over α, β and log τ². `code/eb.py` profiles the likelihood instead:

- For a fixed τ², (α, β) is the closed-form weighted least-squares solution. If β < 0, β is set to 0 and α becomes the
  weighted mean.
- log τ² is then found by a bounded one-dimensional search.

This maximises the same marginal likelihood under the same constraint (β ≥ 0), so the estimator is unchanged. The
profiled version is exact in (α, β) and avoids poor starting values.

**Synthetic validation** (`code/validate_eb.py`, `results/tables/validation_eb.csv`, run before any real data). All four
checks pass:

- S against itself gives G = 1.
- With a good prior, EB-Q beats S and EB-0: mean r 0.795 against 0.723 and 0.715 (G = 1.67).
- With an independent prior, EB-W is within 0.001 of EB-0.

One note for interpretation: in this synthetic setting the flat-prior shrinkage EB-0 is slightly *worse* than S (G =
0.95). Voxel-specific shrinkage toward a constant can reduce spatial correlation.

### D2. First-level runs (logged 2026-10-02 05:57:07)
**Download speed.** OpenNeuro's S3 bucket delivered about 130 KB/s per connection to this machine, with throughput
scaling with the number of connections. Two runners of `code/run_first_levels.sh` shared the manifest, 72 jobs each,
with an atomic lock per subject. Each BOLD file was deleted after its model was fitted. The runs took 22:23–05:56,
about 270 GB in total.

**One operational slip, no effect on results.** Row 0 (PIOP1 working memory, sub-0001) was started twice: once as a
manual test and once by the first runner. Both copies were killed and the row was refitted once, later, from a fresh
download.

**Outcome.** 1,695 of 1,698 models were fitted. The three failures are PIOP2 stop-signal subjects with no successful
stop trials (sub-0166, sub-0176, sub-0181). For them the preregistered contrast "succesful_stop − go" is undefined
(there is no successful-stop regressor), not a failed fit; they are excluded under the plan's first-level rule. The
event-file check before the runs had already identified them.

### D3. Primary results and two exploratory analyses defined after seeing them (logged 2026-10-02 06:08:12)
**Primary results** (`results/tables/hypotheses.csv`, `gains.csv`, `draws_*.parquet`):

- **H1 contradicted.** EB-Q is *worse* than the standard mean map in all six domains. G at n = 15 runs from below 0.67
  (the grid floor) to 0.81; for four domains EB-Q at n = 15 is below S at n = 10.
- **H2 contradicted.** The mismatched prior lowers r by 0.04–0.13 in every domain. In five of six domains it raises the
  false-positive rate by 1.5–3.4 times.
- **H3 not supported.** The matched prior beats the flat prior in 4 of 6 domains: emotion, conflict, faces and
  anticipation. It does not in working memory or stop-signal.
- **Prior quality** (spatial r between the NeuroQuery map and the full-sample map): 0.14–0.50, and −0.26 for stop-signal.
  For stop-signal, β is constrained to 0, so EB-Q equals EB-0.

**Checks that the result is not a bug:**

- In one working-memory draw by hand, τ² = 6.7e-3 against a median s²_v of 1.4e-3. Shrinkage weights w_v run from 0.46
  to 0.96 (5th–95th percentile), so the code does what the model says.
- Mechanism: across voxels, |effect| and between-subject SD correlate at 0.67 (full sample, working memory). Voxels with
  the largest effects therefore have the largest s²_v and are shrunk most. That reorders the map and lowers its spatial
  correlation. The synthetic validation (D1) had homogeneous noise, so it could not show this.

**Two exploratory analyses, defined now, after the primary results** (`code/explore.py`):

- **E1, homoscedastic EB.** The same model with s²_v replaced by its mean over voxels. The weight w is then uniform, so
  flat-prior shrinkage leaves spatial correlation unchanged, and any gain or loss comes from mixing in the prior map.
- **E2, oracle ceiling.** At each draw, the best uniform mix λ·b + (1 − λ)·m (both z-scored), with λ chosen using the
  ground truth. This is an upper bound on what any uniform use of this prior map could achieve; it is not a usable
  method.

Both are reported as G at n = 15 against the same S curve, on the same draws (same seeds).

### D4. Independent review and the changes it led to (logged 2026-10-02 06:35:52)
**Review.** An independent reviewer agent (Fable 5.1) recommended *publish with edits*.

- It replicated the n = 15 draws exactly and confirmed the estimator, the profiling (D1) and the ground-truth
  construction.
- τ² never reached its search bounds.
- It confirmed every verdict and every number in the draft, except one rounding (PIOP2 working-memory prior r is 0.21,
  not 0.22).

**Its two major points, both now checked on all 500 n = 15 draws** (`code/review_checks.py`):

1. **The false-positive inflation comes from the shrinkage machinery, not from the mismatched map**
   (`results/tables/review_fpr.csv`).
   - Relative to S, flat shrinkage alone (EB-0, no map) raises the rate 3.38, 1.48, 1.00, 2.24, 0.60 and 3.10 times
     (working memory, emotion, conflict, faces, anticipation, stop-signal).
   - The *matched* prior is highest everywhere: 3.42, 1.80, 1.20, 2.48, 1.28, 3.10.
   - The mismatched content adds extra false positives only in conflict (1.74 against 1.00). Its correlation cost
     relative to EB-0 is −0.006 to 0.
   - H2 stays contradicted under the preregistered rule, but the report now attributes the harm to voxel-specific
     shrinkage and overconfident posterior z.
   - Only four domains (working memory, conflict, faces, stop-signal) meet the false-positive harm criterion (lower bound
     > 1.5). Emotion (1.49 [1.43, 1.54]) and anticipation are flagged by the correlation criterion alone.
2. **The preregistered metrics measure spatial pattern; magnitude accuracy differs in the weak-signal domains.**
   - Pearson r and top-k Dice ignore rescaling of the map. Mean squared error against the same ground truth
     (`results/tables/review_mse_mechanism.csv`), as an EB-Q / S ratio: working memory 1.42, emotion 1.08, conflict
     0.31, faces 1.63, anticipation 0.33, stop-signal 0.96.
   - Shrinkage therefore cuts the error in effect *size* by about 70% where the signal is weak, while still blurring the
     pattern.
   - The H1 and H3 verdicts concern the pattern (the preregistered metric) and are unchanged. The report's
     recommendations are now limited to pattern recovery.

**Mechanism check** (suggested by the reviewer). EB-0 was refitted with s²_v randomly permuted across voxels. This keeps
the same distribution of weights but breaks their link to effect size. It removes 59–93% of EB-0's correlation loss
(working memory 0.037 → 0.007, emotion 0.116 → 0.018, faces 0.130 → 0.009, stop-signal 0.037 → 0.016). The
effect–variance link is the main cause.

**Data facts the review asked to record** (`results/tables/review_tr.csv`, `review_low_coverage.csv`):

- **Repetition time.** The faces task is multiband: TR 0.75 s and 330 volumes. All other tasks have TR 2.0 s (the plan
  quoted 2.0 s from one header). The code reads each run's header, so the model settings applied as intended.
- **Mask defects.** Three PIOP2 subjects were excluded for coverage that is essentially zero, not partial: stop-signal
  sub-0020 (0.0004), working memory sub-0101 (0.0024) and emotion sub-0226 (0.0001). Their brain mask does not overlap
  the template grid, a file or registration defect. Emotion sub-0176 was excluded at 0.42. The other low-coverage
  exclusions are at 0.87–0.90.
- **Confounds and smoothing.** The confounds also include any `non_steady_state_outlier` columns, as planned. Smoothing
  (6 mm) is applied at native resolution before resampling to the 4 mm grid; the plan did not specify the order.

**Other edits:**

- The oracle (E2) is described as the best *non-negative* uniform mix. For stop-signal (prior r −0.26) a negative weight
  would raise the ceiling from r 0.829 to 0.834.
- G values at the grid floor are written as "below 0.67". In `gains.csv`, rows with n0 = 10 show G = 1 with flag "<";
  they are not evaluable, because the floor equals n0.
- The F2 legend no longer covers data.

**Data release.** The plan said per-subject contrast maps would be committed. Even as float16 they total 88 MB, too large
for this repository, which serves GitHub Pages. Instead `results/maps/` holds each contrast's full-sample mean and
between-subject SD maps. The per-subject maps can be regenerated from the open data with `code/first_level.py`.
