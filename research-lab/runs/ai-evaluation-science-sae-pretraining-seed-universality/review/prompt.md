You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/ai-evaluation-science-sae-pretraining-seed-universality/ (read-only except your
output in review/).

**What to read:**

- plan.md (preregistration, commit 3e34053) and NOTES_pre_plan.md;
- deviations.md (D1-D7);
- report.md (pre-review draft, commit 4928313);
- code/: fetch.py, tokenize_pile.py, pairs.py, match.py, test_match.py, run_train.sh, run_match.sh, check_step0.py,
  analysis.py, figures.py, exploratory.py, lineage_check.py, exploratory_conditional.py, release_arrays.py;
- results/tables/, results/figures/ and logs/.

**Git.** You may run read-only git commands in /mnt/citations, for example to check that each stage's code was committed
before the outcomes it could affect.

**Environment:**

- **Python.** venv/bin/python in the run directory (torch, transformers, sparsify, pandas, numpy).
- **Data.**
  - Models are in data/raw/models/<name>, early checkpoints in data/raw/step0, step1 and step1000.
  - SAEs are in data/sae/<model>/layers.<L>/seed<s>/.
  - The held-out set is data/heldout_tokens.bin (uint16, 2,048-token sequences).
  - The per-pair per-latent arrays are data/match/L<L>/pair_<id>.npz (ids as in results/tables/pairs_L<L>.csv) and
    fired_<model>_s<seed>.npy.
- **Limits.**
  - The GPU (one A100 80GB) is free. You may use it for checks, one process at a time.
  - Keep RAM under about 40 GB.
  - Do not start or stop any Docker container.

Check at least:

1. **Timing and disclosure.**
   - Were the plan, the matching code, the analysis code and the figure code committed before the outcomes they could
     affect?
   - D5-D7 are post hoc. Is anything post hoc presented as confirmatory?
   - Is anything done but not disclosed?
2. **Matching correctness.** Independently re-implement the correlation matching, densely and on a subset of H if
   needed, for at least one within pair and one full-seed pair at each layer, and compare with the stored arrays.
   Check:
   - the hookpoint, against sparsify's `layers.L`, and the dropping of position 0;
   - the SAE encode (b_dec handling), against the installed sparsify source;
   - the assessable-latent rule;
   - the handling of non-assessable candidates;
   - the FVU definition.
3. **The statistic.**
   - Recompute W, X, R, the dyadic bootstrap interval and the verdict from results/tables/pairs_L*.csv, independently
     of analysis.py.
   - Check that no cross-model pair shares an SAE seed.
   - Is the interval honest about what variance it includes and leaves out (the SAE recipe, the held-out text, the
     layers)? Is its narrowness a sign of a problem?
4. **D6, the decoupled variants.**
   - Verify the lineage claims (code/lineage_check.py; results/tables/lineage_*.csv) and EleutherAI/pythia issue #203.
   - Is the relabelling legitimate under plan section 2's contingency rule?
   - Does the report's reading of the decomposition overreach? In particular: "whatever perturbs a run, its SAE
     features end up about equally dissimilar", and the claims about near-replicates.
5. **Interpretation.**
   - Is "Refuted" right by the rule, and stated with the right scope, given that r ≥ 0.9 gives 0.725 (Supported)?
   - Is the claim that "the binding constraint is the SAE, not the language model" supported?
   - Is the conditional-replication result (D7) partly a selection or regression-to-the-mean artefact? For example,
     latents matched across both SAE seeds may simply be better-estimated or more frequent. Is the practical advice
     drawn from it sound?
   - The McCann comparison:
     - Are his claims stated accurately? Use arXiv 2605.24577.
     - Is the Procrustes implementation sound?
     - Is the comparison fair given the differences in setting?
     - Is the dominance of outlier dimensions in the fit a problem?
   - Use web search to check novelty: SAE feature universality across pretraining seeds. Also check the facts stated
     about the cited papers and models.
6. **Numbers.** Does every number in report.md, results/tables/tiles.json and the figures match the results files?
7. **Plain-language summary.** Is "## In plain terms" accurate and not overstated?

Write your review to review/review.md with:

- a recommendation (publish / publish with edits / fix first);
- numbered issues, each with its location and a concrete fix;
- a table of the numbers you recomputed.

Put any scripts you write in review/reviewer_checks/. Reply with the recommendation and the number of issues.
