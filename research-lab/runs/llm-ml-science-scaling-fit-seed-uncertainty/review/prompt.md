You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/llm-ml-science-scaling-fit-seed-uncertainty/ (read-only except your output
in review/).

**The question.** How much does training-seed variation (PolyPythias, 10 seeds × 5 sizes 14M–410M, 8 checkpoints
each) move a Chinchilla scaling-law extrapolation to Pythia-2.8B? Does averaging 3 seeds per size halve the spread?

**Reported:**
- **H1 Inconclusive:** W₁ = 0.123 nats (0.038–0.160) against the bar of 0.05.
- **H2 Inconclusive:** shrinkage 0.16 (−0.10 to 0.81).
- **Post hoc:** two 410M runs with late loss jumps drive the width; excluding them gives W₁ 0.051. Nearly all fits
  overshoot the actual 2.8B loss by about 0.07.

**What to read:** plan.md, deviations.md (D1 bf16 → fp32 before any fit; D2), report.md, code/ (evaluate.py, fit.py,
spike_check.py, posthoc.py, figures.py) and results/tables/ (losses.csv, losses_bf16.csv, primary.json,
ladders_single.csv, posthoc.json, spike_check.csv, eval_noise.json).

**Git.** Read-only git is fine. Verify that the plan preceded the evaluations, D1 the fits, and that post hoc files
came after primary.json.

**Environment.** Python is venv/bin/python, with -I. Do NOT pip install. Keep CPU to at most 8 processes, with
OMP_NUM_THREADS=1 per process. Do NOT use the GPU (shared server). Put scripts under review/reviewer_checks/.

Check at least:

1. **Evaluation.** Is the token/sequence construction right (the first token unscored, 2,048-token sequences)? Is
   fp32 adequate? Spot-check a few losses.csv values for internal consistency, such as monotonicity at 70M–160M and
   the 1B/1.4B fp16–fp32 agreement. Is evaluating 2.8B in fp16 a material problem for secondary 1?
2. **Fits.**
   - Is the Huber-on-log-L objective with log-sum-exp correctly implemented, with the analytic gradient, the 64-start
     grid and best-start selection?
   - Do fits converge? Look for boundary or degenerate parameters (β near 1, E).
   - Is N the non-embedding count, and D = step × 2,097,152?
3. **Ladders and width.**
   - Single-seed draws (one seed per size, all checkpoints), n-seed averaging, and the percentile-width definition.
   - Is the seed bootstrap (duplicated seeds mapped to pseudo-seeds) valid? Do its wide intervals reflect only 10
     seeds per size?
4. **Interpretation.**
   - Are "Inconclusive" verdicts fair?
   - Is the "two unstable runs" story supported? Check spike_check.csv, and whether 14M/31M late rises also matter.
   - Is the post hoc 0.051 legitimately computed? Its ladders are a subset of the same draws.
   - Is the overshoot claim robust to the fp16 target and to evaluation noise (SD 0.047)?
5. **Report.** Check every number against the tables. Are the plain-terms section and the title fair? Is the claim
   that dropping unstable runs is the effective fix properly hedged?

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.
