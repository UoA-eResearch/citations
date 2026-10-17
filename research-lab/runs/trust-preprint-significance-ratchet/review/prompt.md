You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/trust-preprint-significance-ratchet/ (read-only except your output in review/).

The question: when a preprint becomes a journal article, do reported p-values that cross 0.05 between versions move
into significance more often than out (a "ratchet")? Europe PMC preprint full texts are linked to their PMC
open-access published versions (23,220 pairs; 11,508 known version-1). p-values and statcheck tuples are extracted and
aligned between versions, and the direction of crossings is estimated.

**What to read:**

- plan.md (preregistration, commit 8f19a76, before any statistic was extracted);
- deviations.md (D1-D4):
  - D2: the blind validation result, 0.12 precision among crossings, which triggered the abort rule;
  - D3: the primary reported as Inconclusive instead of the mechanical Refuted, and the exploratory v2 specified
    before it was built;
  - D4: the v2 validation, a census of 64 strict crossings;
- report.md and report.html (pre-review draft, commit 7ec85ab);
- code/: parse_jats.py, link.py, fetch_published.py, extract.py (+ test_extract.py), align.py (+ test_align.py),
  pipeline.py, validate_alignment.py, analysis.py, extract_v2.py (+ test_extract_v2.py), pipeline_v2.py,
  validate_v2.py, analysis_v2.py, supplementary.py, figures.py;
- results/tables/:
  - alignment_validation*.csv (the adjudications with keys merged);
  - primary.json, exploratory_v2.json, supplementary.json, verified_crossings.csv;
  - pairs_candidates.jsonl;
- data/ (large, on HDD via symlink):
  - data/aligned/ and data/aligned_v2/ (statistics.jsonl.gz, pairs.jsonl);
  - data/validation/: sample.jsonl and key.csv (v1), sample_v2.jsonl and key_v2.csv (v2). The samples are what the
    adjudicator saw, with the key hidden;
  - data/parsed/, data/raw/published/.

**Git.** Read-only git in /mnt/citations is fine. Sequence:

1. 402e424: pipeline code, tested on crafted text.
2. 8f19a76: plan.
3. ff11a38: validation adjudicated, D2, before analysis.
4. f312ed2: primary result and D3 v2 specification.
5. 9bb9139: v2 code.
6. fa48104: v2 validation, D4.
7. 7ec85ab: draft.

Check from file timestamps and commits that the adjudications were recorded before analysis.py and analysis_v2.py ran,
and that v2 was specified before any v2 output existed. Note D2.5: the agent printed an all-versions class tally
(exact matches 8 up / 5 down) after adjudicating and before committing.

**Environment:** venv/bin/python in the run directory (pandas, numpy, scipy, sklearn, lxml, ftfy). Do NOT pip install
into it; make your own venv under review/reviewer_checks/ if needed. Put any caches under review/reviewer_checks/cache
(gitignored).

Check at least:

1. **Adjudication quality.** The agent adjudicated its own validation samples, blind to version order and stratum.
   Re-adjudicate independently:
   - at least 60 of the v1 sample (all 12 crossings judged correct, plus a random 48);
   - all 64 v2 strict crossings.

   Report your agreement (and kappa), and whether disagreements bias the direction among verified crossings. Is the
   criterion consistent? For example, "same comparison with changed data" counts as correct, but a typo read
   literally counts as incorrect. Are w024/w090 (values that look permuted across labels) and w053/w057 handled
   reasonably?
2. **The primary and D3.** Recompute the 4 exact-tuple crossings in the version-1 population and check they are real.
   Is reporting Inconclusive instead of the preregistered rule's mechanical Refuted justified, or is it a post hoc
   escape? Should the report lead with the mechanical verdict? Is there any reading of the plan under which the
   all-crossings estimate (0.489, CI 0.453-0.526) should carry a verdict?
3. **Exploratory v2.** Was it specified before it was built and run (D3 text vs code vs timestamps)? Are the strict
   criteria reasonable, or do they select crossings in a way that could bias direction? For example, legends and
   tables are excluded, and these may hold different kinds of results. Does the extraction repair change any v1
   result it should not? Run the tests.
4. **Verified-crossing estimates.** Recompute 24/42 and 31/52, the exact intervals and the paper bootstrap. Is the
   dedup across v1 and v2 right? Is pooling a random v1 sample (from all versions) with a v2 census (version-1 only)
   defensible? Are the "kinds" (data changed, re-analysis, correction) derived reasonably from notes that were written
   blind to direction?
5. **Secondaries.**
   - S1: recompute dropped vs added and the paper bootstrap. Is the comparison meaningful when dropped/added are
     inflated by alignment failures?
   - S2: check consistent() and recompute_p() for errors, e.g. one-tailed tests, chi-square df, r df, rounding
     tolerance at p < 0.01. Is "inconsistencies persist" supported?
   - S3: is it described appropriately?
6. **Pipeline correctness.** Spot-check extract.py and align.py on real text: section assignment, the boilerplate
   filter, version_of(), and whether the one-to-one greedy matching or the rank tie-breaker creates systematic
   misalignment. Check significance(), including "p < 0.1" and "p > 0.01" as undetermined, and p = 0.05 exactly.
7. **Linkage and population.** Is title-Jaccard confirmation adequate? Does "version 1" really mean the full text
   predates peer review? Research Square /vN DOIs; Europe PMC version fields. Could some "preprints" be author
   manuscripts posted after acceptance?
8. **Novelty and literature.** Web-search for version-matched studies of p-value or significance changes between
   preprints and publications (2020-2026), and check the cited works in the report (Sci Rep 2023; Bero et al. 2021;
   JAMA Netw Open 2022; bioRxiv 2026.06.30.735556; Nuijten & Wicherts 2024) exist and say what the report claims.
9. **Numbers.** Does every number in report.md and the figure captions match the results files?
10. **Plain-language summary and headline.** Accurate and not overstated? In particular: "Crossings are rare ... under
    2 per 1,000", "no sign of non-significant results being quietly dropped", "internal arithmetic errors in preprints
    were rarely fixed", and the methods lesson.

Write your review to review/review.md with:

- a recommendation (publish / publish with edits / fix first);
- numbered issues, each with its location and a concrete fix;
- a table of the numbers you recomputed;
- your re-adjudication table (id, your judgement, the agent's, note), kept under review/reviewer_checks/.
