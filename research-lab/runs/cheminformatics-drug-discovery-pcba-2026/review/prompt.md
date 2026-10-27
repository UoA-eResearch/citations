You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/cheminformatics-drug-discovery-pcba-2026/ (read-only except your output in
review/).

**The question.** Does a leakage-audited benchmark built from recent PubChem confirmatory screens change what
virtual-screening methods look like, relative to LIT-PCBA?

**Reported:**
- **H1 Inconclusive:** Q = 0.43 but the interval is (−1.47, 3.38). The report leans instead on the within-benchmark
  contrast: the memorization baseline's median EF1% falls 11.4 → 4.8 → 2.4 (PCBA-2026) and 27.8 → 8.3 → 3.5 (LIT)
  as the split goes random → analog-disjoint 0.6 → 0.4.
- **H2 Supported:** on 0 of 56 target-embedding pairs does ChemBERTa or MoLFormer beat ECFP4 + RF.
- **H3 Supported:** mean τ 0.20 (0.085–0.295) against the 0.4 bar, but the split-half noise ceiling is 0.29.
- Leakage audit: 89% of LIT evaluation compounds and 62% of PCBA-2026's have a training neighbour above Tanimoto
  0.4.

**What to read:** plan.md, deviations.md (D1 archives and APIs; D2 hit rates, the EF ceiling and a BEDROC bug;
D3 the size cap), report.md, results/plausibility.md, code/ (fetch.py, build.py, subsample.py, folds.py, embed.py,
run.py, analyse.py, figures.py, fix_n.py is not part of this run) and results/tables/ (primary.json, metrics.csv,
pairs_h2.csv, tau_h3.csv, folds_new.csv, folds_lit.csv, coverage.json, subsample_check.json, targets_new.csv).
Data: data/new_sub.parquet, data/lit_sub.parquet, data/folds_*/, data/scores_*/.

**Git.** Read-only git is fine. Verify that plan.md preceded any activity outcome, and that D2 and D3 preceded any
fitted score (the scores_* directories against the deviations' timestamps).

**Environment.** Python is venv/bin/python, with -I. Do NOT pip install. The machine is busy; keep to at most 4
processes and do not refit the whole panel. Put scripts and outputs under review/reviewer_checks/.

Check at least:

1. **The benchmark.** Is "confirmatory, single target, 2021+" a defensible population when the result is 28 targets
   from two depositors (NCATS, Tox21), 7 of them counterscreens with hit rates above 20%? Does the one-assay-per-gene
   rule bias anything? Are the outcome and deduplication rules right?
2. **The analog audit.** Is removing evaluation compounds within Tanimoto 0.4 of training the right operation, or
   does it over-debias (it removes 60% of PCBA-2026 and 88% of LIT)? Does it bias *which* actives survive? Is the
   0.6/random sensitivity enough?
3. **The size cap (D3).** Proportional subsampling with a 150-active floor. Does it preserve EF1% as claimed? The
   check covers three targets; spot-check another.
4. **H1.** Is Q with a ratio-of-medians bootstrap salvageable, or should the report say plainly that the
   preregistered statistic cannot answer the question at 15 LIT targets? Is leaning on the within-benchmark
   contrast legitimate, given it is the preregistered split sensitivity?
5. **H2.** Mean-pooled frozen embeddings with a linear head is one way to use a foundation model, and arguably a
   weak one. Is the claim properly scoped? Check the paired bootstrap.
6. **H3 and the noise ceiling.** Is the split-half ceiling computed comparably to the cross-benchmark τ (same
   evaluation sets, same metric)? Does it undercut the verdict?
7. **Report.** Check every number against the tables, and the plain-terms section.

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
>   their sources, including the role and conditions. Two DOIs in this lab resolved to the wrong paper this week,
>   so check titles, not just resolution.
> - **G7:** validation labels come from two blind labellers, with agreement reported.
>
> Report any gate that is missing or hollow as a finding.

When you finish, reply with a short summary: the verdict and a one-line description of each finding.
