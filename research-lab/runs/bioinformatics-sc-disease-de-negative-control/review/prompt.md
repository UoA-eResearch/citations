You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/bioinformatics-sc-disease-de-negative-control/ (read-only except your
output in review/).

**The question.** How much single-cell disease signal in the CZ CELLxGENE Census survives matched healthy-vs-healthy
negative controls? Does cross-study replication follow donor count rather than cell count?

**Reported:**
- **H1 Supported:** 74% of 799 contrasts are indistinguishable from their matched null on the DE-gene count
  (95% CI 57-84%), 82% on the preregistered π1.
- **H2 Inconclusive:** donors predict replication (β 0.061, 0.021-0.095) but not detectably better than cells.
- **D2:** π1 has 8% power against a synthetic twofold change in 5% of genes, against 87% for the DE-gene count, so
  both are reported and the interpretation leads with the DE-gene count.

**What to read:** plan.md, deviations.md (D1 data route and counts; D2 the statistic), report.md,
results/plausibility.md, code/ (meta.py, fetch_h5ad.py, pb_h5ad.py, draws.py, de.R, power_check.py, analyse.py,
figures.py, fetch_ot.py) and results/tables/ (primary.json, contrasts.csv, pairs.csv, coverage.json,
power_check.json, age_map.csv, draw_fallbacks.csv). Pseudobulk matrices are in data/pb/, DE job directories in
data/jobs/ (counts.f32, donors.csv, draws.csv, stats.csv per contrast).

**Git.** Read-only git is fine. Verify that plan.md preceded any expression value, and that D2 preceded the H1
result (the power check's outputs against primary.json).

**Environment.** Python is venv/bin/python, with -I. Do NOT pip install. R runs only in the `sc-negctl-de:1` Docker
image (`--network none`, `--user $(id -u):$(id -g)`, `-e OPENBLAS_NUM_THREADS=1`). The machine is busy, so keep to
at most 4 processes. Put scripts and outputs under review/reviewer_checks/.

Check at least:

1. **The null construction.** Is matching on sex and age bin, with the plan's fallbacks, adequate? 11.8% of null
   donor slots used a fallback and 5.5% did not match sex, while the exploratory attribution finds sex imbalance is
   the strongest predictor of exceeding the null. Does that undermine the exceedance cases, the indistinguishable
   ones, or both?
2. **The statistic switch (D2).** Is leading with the DE-gene count defensible, given it was a preregistered
   secondary and the choice used only null draws and synthetic injections? Does the π1 result deserve more weight
   than the report gives it? Is the power check's injection (2x in 5% of expressed genes) a fair test?
3. **Sizes.** The exceedance test runs at m per group (median 13 vs 13) while the full-size run uses every donor
   (median 100). Is the report's hedging enough, or does F2 still mislead? Could a size-matched full-size null be
   built in some other way?
4. **The pipeline.** de.R: filterByExpr/TMM/voom/eBayes per draw, sex as covariate when it varies. Is re-filtering
   per draw right? Does the empirical p (1 + #{null >= real})/(B + 1) with BH across contrasts behave as claimed?
5. **H2.** Pair construction across Census collections, the regression's predictors and the two bootstraps. Is the
   null-pair baseline (0.03 vs 0.30) computed on comparable gene sets?
6. **Report.** Check every number against the tables, including the by-disease shares and the Open Targets
   enrichment (9.9% at raw p, none after BH).

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/. Paraphrase rather than quote any source text; the lab never commits quoted source text.

> **Gate checks (METHODS.md G1–G7).** Verify:
> - **G1:** plan.md's leakage audit is real and complete; look for label-correlated fields it missed.
> - **G2:** `results/tables/coverage.json` exists, and no unplanned fallback entered a statistic.
> - **G3:** `results/plausibility.md` traces three units, and the asserted invariants hold.
> - **G4:** every validation metric has an error audit with a judgeable denominator.
> - **G5:** `review/overclaim_check.md` passes and is honest; re-label any sentence you disagree with.
> - **G6:** `results/attribution_ledger.csv` passes `tools/attribution.py check`; spot-check 5 claims against
>   their sources, including the role and conditions.
> - **G7:** validation labels come from two blind labellers, with agreement reported.
>
> Report any gate that is missing or hollow as a finding.

When you finish, reply with a short summary: the verdict and a one-line description of each finding.
