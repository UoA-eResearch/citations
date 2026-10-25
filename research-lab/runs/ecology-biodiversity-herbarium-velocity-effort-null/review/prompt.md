You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/ecology-biodiversity-herbarium-velocity-effort-null/ (read-only except your
output in review/).

**The question.** Daru, Birkeland & Chala (bioRxiv 10.64898/2025.12.26.696646) report that herbarium centroids of
109,242 plant species moved at a median of 5.6 km/yr between 1970–2000 and 2001–2024. How much of that would a null
reproduce if every range stayed fixed? The null reassigns each species' records between periods at their observed
counts, weighted by each period's collecting effort. H1: the null reproduces at least half of the observed median.

**Reported:**
- **H1 Supported.** Observed median 6.9 km/yr (69,596 species, at least 10 thinned 5-arcmin cells per period).
  Noise-plus-effort null 4.6; ratio 0.667 (0.661–0.673).
- Noise-only null: ratio 0.41.
- 36% of species exceed their null's 95th percentile; 53.6% move poleward against 50.8% under the null.
- Robustness ratios 0.64–0.71.
- SDM-centroid variant (1,000 species): ratio 0.74 (0.68–0.82).
- **Pre-result deviations:**
  - D1: Pareto order sampling replaced the planned exponential-key sampler, which reproduced only 66% of a
    synthetic effort shift;
  - D2: cleaning was rewritten after G2 caught a silent 1% record loss.

**What to read:**
- plan.md, deviations.md, report.md, results/plausibility.md and results/attribution_ledger.csv.
- results/tables/: primary.json, clean_summary.json, coverage.json, reproduction.csv, observed_*.parquet,
  nulls_*.parquet, sdm_variant.*, handtrace.json.
- code/: s3_extract.py, clean.py, velocity.py, analyse.py, sdm_variant.py, figures.py, handtrace.py, test_velocity.py
  and test_effort.py.
- **Data:** data/gbif_s3/ (raw extract, 736 MB), data/clean.parquet, data/clean_no_r5.parquet and data/ref/ (Natural
  Earth, WorldClim).

**Git.** Read-only git is fine. Verify that the plan, D1, the null and analysis code, and D2 all precede the first
velocity output (observed_primary.parquet, 09:15 on 2026-10-26).

**Environment.** Use venv/bin/python with -I. Do NOT pip install. The machine is shared (vLLM on the GPU; other jobs),
so use at most 8 workers. `code/velocity.py primary 8` re-runs the primary in about 25 minutes. The functions in
velocity.py (shift, nulls, weights) can be imported and run for single species.

Check at least:

1. **Cleaning.** The rules, the dense-point proxy (more than 1,000 species at one coordinate pair; 86 points), the
   sea-cell test and the 3.0M records without a species key. Is the D2 fix right, and do the counts reconcile?
2. **Thinning and centroids.** Cell assignment and the dateline join; the spherical mean and the 28-year divisor; the
   arithmetic variant. Do the hand traces really check independently?
3. **The nulls** (velocity.nulls, velocity.weights). This matters most.
   - Does reassigning records, then re-thinning, model a fixed range correctly?
   - Is Pareto order sampling with odds s1/s2 the right effort weighting? Do the inclusion probabilities match
     n1·s1/(n1·s1 + n2·s2)?
   - Leave-one-species-out effort, the edge cases (s1 or s2 = 0), and the 1° effort grid.
   - Could the null absorb real movement, for example collectors following expanding species, or be biased the other
     way?
   - Do test_velocity.py and test_effort.py show what D1 says?
4. **The statistic.** The ratio of medians, as opposed to the median of ratios; the species bootstrap; the
   exceedance interpretation (36% against 5%); the poleward excess. Is "Supported" right, and is the 0.5 bar
   meaningful?
5. **Reproduction.** Our 6.9 km/yr and Daru et al.'s 5.6, with different names, no native-range filter and a newer
   snapshot. Does any difference threaten the observed-versus-null comparison?
6. **SDM variant.** It uses one null replicate per species against the observed fit. Check the background and
   threshold choices, and whether the conclusion "modelling ranges does not remove the effect" is fair.
7. **Report.** Check every number against the tables. Check that the title, plain terms and the claims about Daru et
   al. (ledger A1, A2, A10) are fair to the preprint.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.

**Gate checks (METHODS.md G1–G7).** Verify:
- **G1:** plan.md's leakage audit is real and complete (leave-one-species-out effort); look for period-correlated
  fields it missed.
- **G2:** `results/tables/coverage.json` exists, and no unplanned fallback entered a statistic (effort θ = 1
  defaults are counted).
- **G3:** `results/plausibility.md` traces three units, and the asserted invariants hold.
- **G4:** does not apply (no classifier or labelling); confirm.
- **G5:** `review/overclaim_check.md` passes and is honest; re-label any sentence you disagree with.
- **G6:** `results/attribution_ledger.csv` passes `python3 -I ../../tools/attribution.py check . --show`; spot-check
  5 claims against their sources, including the role and conditions.
- **G7:** does not apply (no labels); confirm.

Report any gate that is missing or hollow as a finding.
