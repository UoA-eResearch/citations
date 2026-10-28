You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/bioinformatics-amr-gene-species-emergence-forecast/ (read-only except your
output in review/).

**The question.** Can first appearances of AMR genes in new bacterial species be forecast prospectively, better
than a sampling-effort null, on the NCBI Pathogen Detection corpus?

**Reported:**
- **H1 Refuted.** The preregistered model's precision@100 is 0.00 against the null's 0.08 (ratio CI 0.00–1.27).
- **H2 Refuted.** ESM-2 embeddings subtract average precision (−0.005, −0.013 to +0.001), and removing the feature
  lifts precision@100 from 0.00 to 0.18.
- **But** under the preregistered first-appearance variant both models score 0.00 against the null's 0.10, so the
  no-embedding repair does not survive. 705 of 847 primary-rule "emergences" were already observed once before 2023.
- Diagnosis: the embedding is near-saturated (median nearest-neighbour cosine 0.971) and its top tail picks
  barely-sequenced species (top-100 median 24 horizon isolates against 414 for real emergences).

**What to read:** plan.md; deviations.md (D1 catalog-growth restriction, D2 hyperparameters and post hoc);
report.md; results/plausibility.md; code/ (list_groups, build, taxonomy, proteins, embed, candidates, analyse,
posthoc, variant_any, coverage_report); results/tables/ (primary, secondary, posthoc, variant_any, coverage,
build, proteins, task_*, top100*.csv). Data under data/ (not in git): isolates.parquet, pairs.parquet,
task_*.parquet, gene_embeddings.parquet, raw/ and raw_ref/.

**Git.** Read-only git is fine. Verify plan.md preceded the first download, and that analyse.py was committed
before the candidate tables existed.

**Environment.** Python is venv/bin/python, with -I (note: -I drops the script's own directory from sys.path, so
local imports need the path inserted). Do NOT pip install. At most 4 processes. analyse.py takes several hours,
mostly in the ablations; you need not rerun it. Put scripts and outputs under review/reviewer_checks/.

Check at least:

1. **The outcome definition.** Is the two-BioProject rule defensible as "emergence" when 83% of its positives were
   already observed once? Is the first-appearance variant handled honestly, and does it deserve to be the primary?
2. **The null.** Is 1 − Binomial(≤1; n, f) the right effort baseline? Is giving both the null and the model the
   realised horizon count fair, or does it hand the null the answer? Would a stronger or weaker null change H1?
3. **The candidate set.** The ≥20-isolate species rule, the "gene established somewhere" rule, and the catalog
   restriction (D1). Does D1 do analytic work it should not?
4. **The model.** Features, leakage across the 2019/2022 cutoffs, hyperparameter selection by gene-grouped CV,
   and whether precision@100 on 472,779 candidates with 847 positives is a stable statistic at all.
5. **The embedding diagnosis.** Is "the embedding breaks the model" established, or could it be an artefact of one
   ablation and a saturated score distribution? Check the top-100 characterisation.
6. **Inference.** Gene-resampled bootstrap with undefined draws (210 of 2,000 for H1); is the interval honest?
7. **Report.** Check every number against the tables, and the plain-terms section.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered
findings (severity, evidence with file:line or your check's output, the fix). Paraphrase rather than quote any
source text; the lab never commits quoted source text.

> **Gate checks (METHODS.md G1–G7).** Verify:
> - **G1:** plan.md's leakage audit is real and complete; look for label-correlated fields it missed.
> - **G2:** `results/tables/coverage.json` exists, and no unplanned fallback entered a statistic.
> - **G3:** `results/plausibility.md` traces three units, and the asserted invariants hold.
> - **G4:** every validation metric has an error audit with a judgeable denominator.
> - **G5:** `review/overclaim_check.md` passes and is honest; re-label any sentence you disagree with.
> - **G6:** `results/attribution_ledger.csv` passes `tools/attribution.py check`; spot-check the claims against
>   their sources, including the role and conditions. Three DOIs in this lab resolved to the wrong paper this week,
>   so check titles, not just resolution.
> - **G7:** validation labels come from two blind labellers (does not apply here; confirm).
>
> Report any gate that is missing or hollow as a finding.

When you finish, reply with a short summary: the verdict and a one-line description of each finding.
