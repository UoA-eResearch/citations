You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/ecology-biodiversity-globi-temporal-link-holdout/ (read-only except your
output in review/).

**The question.** On GloBI snapshots v0.6 (2023) → v0.11 (2026), does the advantage of structural/taxonomic link
predictors over an effort-only baseline (degree, citations) at least halve on future records compared with a random
holdout? H1: ρ = A_temporal / A_random ≤ 0.5.

**Reported:** H1 Refuted.
- ρ = 1.68 (1.10 to 2.30).
- Taxonomy + structure: 0.991 random and 0.948 temporal, against effort's 0.951 and 0.880.
- Degree-matched temporal: 0.850 against 0.568.

**What to read:** plan.md, deviations.md, report.md, code/ (build.py, model.py, figures.py), results/tables/
(primary.json, per_class.csv) and results/figures/. The data are in data/interim/ (edges_v0.6/v0.11.parquet,
species_v0.6.parquet) and data/raw/ (MD5-verified Zenodo files).

**Git.** Read-only git is fine. Verify that plan.md and the code preceded the edge files and primary.json.

**Environment.** Python is venv/bin/python, with -I. Do NOT pip install. Set OMP_NUM_THREADS=4 and keep CPU moderate.
Put scripts and outputs under review/reviewer_checks/.

Check at least:

1. **Graph construction (build.py).**
   - Type mapping and direction (hasHost, hostOf and the like).
   - Species-name keys, the refuted-pair removal, and the DuckDB read options (quote='', ignore_errors). Are rows
     silently lost?
   - Is the 26–42% "lost" turnover a sign of systematic name re-resolution that manufactures temporal positives?
     Check a sample of positives for synonymy.
2. **Leakage (model.py).**
   - Do features for temporal pairs use only v0.6? Citation counts come from v0.6 species.
   - Does the inner split for supervised training leak evaluation positives?
   - For the random holdout, are the hidden edges excluded from features, including the taxonomic counts and
     species citation counts, which are computed over all of v0.6?
   - The self-link subtraction in taxo().
3. **Negatives.** Uniform negatives exclude edges in either snapshot. Is the degree-matched sampler correct? Is pooling
   by within-class percentile ranks valid?
4. **The statistic and bootstrap.**
   - Choosing the best predictor on the random holdout.
   - Cluster weights by top_namespace for positives, and iid weights for negatives.
   - Are the AUROC with integer weights and ρ's interval computed correctly?
5. **Interpretation.** Is "Refuted" fair, given:
   - new-dataset dominance (72% of positives);
   - name churn;
   - effort already scoring 0.88?

   Could the taxonomic features exploit dataset-level artefacts, such as a new dataset recording many species of one
   genus?
6. **Report.** Check every number against the tables, and that the plain-terms section and title are fair.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.

**Gate checks (METHODS.md G1–G7; this study predates the gates, so G5 and G6 were run as a pre-review gate).**
Verify:
- **G5:** `review/overclaim_check.md` passes (`python3 -I ../../tools/overclaim_check.py . --verify`) and is honest.
- **G6:** `results/attribution_ledger.csv` passes `python3 -I ../../tools/attribution.py check .`; spot-check claims.
- **G1:** label leakage between the v0.6 training graph and the v0.11 positives (for example re-resolved names
  counted as new pairs, or negatives sampled from pairs that later appear).
- **G2–G4, where they apply.**

Report any gate that is missing or hollow as a finding.
