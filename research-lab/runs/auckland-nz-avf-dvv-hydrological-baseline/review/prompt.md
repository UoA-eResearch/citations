You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/auckland-nz-avf-dvv-hydrological-baseline/ (read-only except your output in
review/).

**The question.** Does a rainfall-diffusion + annual + drift model, trained on 2013–2020, predict held-out (2021+)
ambient-noise dv/v (stretching, 0.5–2 Hz) across 11 Auckland Volcanic Field stations? H1 is a median held-out R² of at
least 0.5.

**Reported:** H1 Refuted.
- Median held-out R² −0.12 (−0.67 to −0.03), with 32 scored pairs.
- Training R² 0.19.
- Noise floor (2 SD of residuals) 0.136%.
- Robust to every-epoch segments, temperature, frozen drift (post hoc) and a draining kernel (post hoc).

**What to read:** plan.md, deviations.md, report.md, code/ (correlate.py, forcing.py, dvv.py, model.py, secondary.py,
posthoc_drift.py, posthoc_kernel.py, figures.py), results/tables/ (pairs.csv, dvv_daily.parquet, fit.csv,
primary.json, secondary*.json, posthoc_*.json) and results/figures/. The daily correlations are in data/ccf/.

**Git.** Read-only git is fine. Verify that the plan preceded correlate.py's output, and that dvv.py and model.py were
committed before dvv_daily.parquet and fit.csv existed.

**Environment.** Python is venv/bin/python, with -I. Do NOT pip install. It is CPU-only. Read correlations from
data/ccf without re-downloading waveforms. Put scripts and outputs under review/reviewer_checks/.

Check at least:

1. **Correlation processing (correlate.py).**
   - Whitening and RAM, the transient mask and the window counts.
   - Is the decimation and filtering right?
   - Do the stacks look like plausible noise correlations (symmetric, coda present)?
   - Spot-check a few pair-days.
2. **dv/v (dvv.py).**
   - The stretching sign convention: dv/v = −ε for cur(t(1+ε)). Is the sign right?
   - The coda window, the reference per segment and the 10-day stack.
   - Coherence values.
   - Could a bug (wrong window, wrong side, wrong sign, reference mixing segments) destroy a real hydrological
     signal? Test with a synthetic stretch.
3. **The model (model.py).**
   - P_τ via convolution: alignment, a lag of at least 1, and the subtracted training-mean rain.
   - Design-matrix rows, segment constants and held-out segment handling.
   - R² about the held-out mean.
   - The scoring filter and the bootstrap.
   - Is "Refuted" fair, or does the extrapolated drift or cumulative kernel mechanically doom held-out R²? The post
     hoc checks address this; are they implemented correctly?
4. **The noise-floor statement.** Is 0.136% (2 SD of 30-day-smoothed residuals) the right summary of detectability?
5. **Secondaries.** The lockdown step, the 2023 residuals, temperature lag selection and the pair-type split.
6. **Report.** Check every number against the tables, and that the plain-terms section, title and care note are fair.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.

**Gate checks (METHODS.md G1–G7; this study predates the gates, so G5 and G6 were run as a pre-review gate).**
Verify:
- **G5:** `review/overclaim_check.md` passes (`python3 -I ../../tools/overclaim_check.py . --verify`) and is honest;
  re-label any sentence you disagree with.
- **G6:** `results/attribution_ledger.csv` passes `python3 -I ../../tools/attribution.py check .`; spot-check 5 claims
  against their sources, including the role and conditions.
- **G1–G4, where they apply:** label-correlated fields or leakage between training and held-out periods; silent
  fallbacks (for example JSON or forcing gaps filled with defaults); plausibility of the headline numbers; validation
  metrics without an error audit.

Report any gate that is missing or hollow as a finding.
