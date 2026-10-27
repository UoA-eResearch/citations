You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/cheminformatics-drug-discovery-split-calibration/ (read-only except your
output in review/).

**The question.** Which retrospective splitting strategy predicts the error a bioactivity model makes on genuinely
later data? Models are trained on ChEMBL 33 and tested on compounds first measured in 2023+ documents that appear
only in ChEMBL 37. There are 250 targets, 7 splitters and 5 model families.

**Reported:**
- **H1 Supported:** random and scaffold splits understate prospective RMSE: median signed bias −0.37 and −0.27,
  bar ≤ −0.25.
- **H2 Refuted:** document- and author-disjoint splits have median absolute bias 0.17 and 0.22, bar ≤ 0.12, though
  their signed bias is near zero.
- **H3 Refuted:** mean Kendall τ is about 0.35–0.41 for every splitter.

**What to read:** plan.md, report.md and code/:
- fetch.py, build.py, select.py: extraction, targets, prospective sets, delta audit;
- run.py: splitters, models, fits;
- analyse.py, corrector.py, figures.py, plausibility_check.py.

And results/tables/ (selection.json, targets.csv, delta_audit.csv, coverage.json, primary.json, bias_long.csv,
tau_long.csv, corrector.json, plausibility_traces.json). The data are in data/ (train.parquet, prospective.parquet,
fits/*.json; the SQLite files are under data/raw).

**Git.** Read-only git is fine. Verify that plan.md and the analysis code preceded any table read, and that the
target list was committed before any fit completed.

**Environment.** Python is venv/bin/python, with -I. Do NOT pip install. The machine is busy with another job, so
keep CPU low (at most 2 processes, and no retraining of large targets). Put scripts and outputs under
review/reviewer_checks/.

Check at least:

1. **Prospective truth.**
   - Is "new in 37, from a 2023+ document, on a compound absent from 33" leak-free? Consider InChIKey keying (salts,
     stereo, tautomers: could a near-identical compound count as new?) and the document-year field.
   - The delta audit says 43 of 60 new activities are older papers newly curated. Is the 2023+ restriction enough?
2. **Filters and aggregation.** pChEMBL, relation, assay type and confidence; the median per compound; targets
   measured in both releases under a changed curation.
3. **Splitters (run.py).**
   - Do group splits hit about 20% test? Do the 425 dropped repeats bias which targets enter each splitter?
   - Author union-find: normalisation, and the 145 infeasible units.
   - The time splitter uses document years inside 33. Is its "near-zero bias" an artefact of one repeat?
4. **Metrics and inference.**
   - Signed bias as retro mean over repeats minus prospective. Is the target bootstrap right?
   - Is median absolute bias a fair H2 statistic, given prospective-set noise (small sets have noisy RMSE)?
   - Could part of H2's 0.17 be irreducible sampling noise in the prospective RMSE itself? If so, quantify it, for
     example with a bootstrap of the prospective set per target.
5. **H3.** Kendall τ over 5 models with near-tied RMSEs. Is τ ≈ 0.4 just noise among models that perform similarly?
   Is the bar meaningful?
6. **Report.** Check every number against the tables, and that the title, the plain-terms section and the claims
   about prior work are fair.

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
