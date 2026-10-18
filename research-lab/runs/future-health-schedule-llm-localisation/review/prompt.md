You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/future-health-schedule-llm-localisation/ (read-only except your output in
review/).

**The question.** Does a general open LLM (Nemotron 3 Nano Omni, served locally) answer yes/no questions about New
Zealand's Pharmaceutical Schedule worse than matched questions about Australia's PBS (H1)? Does retrieval from the
jurisdiction's own document close that gap (H2)? Does it affirm plausible but absent NZ eligibility criteria at least
20% of the time (H3)?

**Design.** Items generated from the Pharmac Schedule XML (Oct 2026; stability edition Nov 2025) and the PBS API v3
(schedule 4751; stability edition the API's earliest), chemicals matched across countries. Families: (a) listed
tablet/capsule presentations, (b) Special Authority / Authority Required, (d) true vs counterfactual criteria (from
another chemical in the same ATC2 group). Conditions: zero-shot, BM25 top-3 retrieval, retrieval with abstention;
100-item paraphrase check. Chemical-cluster bootstrap for the NZ−AU gap; Wilson intervals for fabrication.
Answer-key checks: round 1 failed a family (D4: one fix), round 2 passed overall but failed the family (a) negatives
bar; D5 made family (a) descriptive, moved H1/H2's verdict to family (b) with the pooled (a)+(b) reported, and added
a hand screen of all 100 NZ counterfactuals (H3 tested on all and on the screened 83; verdict only if both agree).

**What to read:**
- plan.md (preregistration, commit 6bd3e3c), deviations.md (D1–D5 and the D5 addendum);
- report.md and report.html (pre-review draft);
- code/: fetch.py, names.py, generate.py, validate.py, run.py, analysis.py, figures.py;
- results/tables/: key_validation_round1.csv, key_validation_round2.{csv,json}, nz_counterfactual_screen.csv,
  generation_stats.json, primary.json, accuracy.csv; results/figures/;
- data/: items.jsonl, items_v1.jsonl, passages.jsonl, runs.jsonl, validation/ (sheets and samples),
  raw/nz/ (Schedule XML, PDF and its pdftotext rendering), raw/pbs/ (API JSON pages).

**Git.** Read-only git in /mnt/citations is fine. Check from commits and file timestamps that code and deviations were
committed before the outputs they govern: D5, the screen and analysis.py before any model output was used; the run
began after D5. The agent states it did not open runs.jsonl before the analysis; check what you can.

**Environment.**
- Python: venv/bin/python in the run directory (pandas, numpy, rank_bm25, requests, matplotlib). Do NOT pip install.
- Your scripts and outputs go under review/reviewer_checks/, caches under review/reviewer_checks/cache.
- Use at most 8 cores. Do NOT send requests to localhost:8000 (the model server); if you need model answers, use
  data/runs.jsonl. Do not call the PBS API (the key is not stored anywhere in the repo, by design).

Check at least:

1. **Answer keys.** Re-adjudicate a fresh random sample (at least 60 items across families and jurisdictions, not in
   either validation sample) against the PDF text and raw PBS JSON. Is the key-error rate for families (b) and (d)
   credible? Screen at least 40 AU counterfactuals for overlap with the chemical's own criteria.
2. **The NZ counterfactual screen.** Re-screen all 100 independently (or a large sample) without looking at the
   agent's labels first; compare. Is "distinct" applied consistently? How sensitive is H3 to borderline calls?
3. **Generation.** Matching, the stability rule, the SA inheritance logic (NZ), authority = A or S (AU), mixed-item
   exclusion, the 3-per-chemical cap, balance; whether question wording leaks the answer or differs between countries.
4. **Runs.** Prompts, the JSON schema, error handling (5 errors), the paraphrase set, and whether retrieval passages
   are built from the same structured data as the key (circularity) and how often BM25 retrieves the right chemical.
5. **Analysis.** H1 cluster bootstrap (family (b) and pooled), H2's rule, H3 Wilson intervals, the D5 verdict logic,
   response-bias tables, abstention, paraphrase agreement. Recompute the main numbers from runs.jsonl.
6. **D5's legitimacy.** Were D5's consequences fixed before outputs, and are they the natural reading of D4's bar?
   Would the verdicts change under the preregistered pooled analysis or without the screen?
7. **The report.** Every number against the tables; overstated claims; the "In plain terms" section; whether the
   verdict line is right (H1 Inconclusive, H2 Inconclusive, H3 Supported) and whether the headline framing is fair.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in review/reviewer_checks/.
