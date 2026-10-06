You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/legal-digital-humanities-federal-register-llm-drafting/ (read-only except your
output). Read plan.md (preregistration, commit 22616bf), deviations.md (D1-D8), report.md (draft), code/ (fetch_meta.py,
fetch_govinfo.py, groups.py, parse.py, pools.py, mle.py, generate.py, validate.py, analysis.py, figures.py,
explore_words.py), results/tables/ and results/figures/, logs/. Data are in data/ (meta/fr_groups.parquet,
paragraphs_raw.parquet, paragraphs_sealed.parquet, pools/, llm_ref/*.jsonl; the sealed 2026 XML and its manifest).
Use the study's venv (./venv/bin/python) and cores 0-3 only (taskset -c 0-3); the other cores run a separate job. You
may run read-only git commands in /mnt/citations (git log/show) to check what was committed when.

Check at least:
1. Was the decision rule applied as preregistered? Recompute the primary DiD and its interval from the code path, and
   check the verdict logic (Supported / Refuted / Inconclusive) and the placebo rule.
2. Sealing and timing: were the 2026 issues untouched until validation and the MDE were committed? Did any estimator or
   design change (D1-D8) follow sight of any 2022+ estimate? Check commit times against the deviation timestamps.
3. The estimator: is the paired reference (D5) and the two-point calibration with propagated uncertainty (D6) correct
   and sound? Is the bootstrap implemented as described (documents resampled within group and period; calibration
   draw i shared across groups)? Any leakage between the human reference, generation, validation and calibration sets?
4. Validation: are V1 and V2 implemented as described, and is the report honest about the V1 coverage shortfall, the
   12% false-positive rate and the gap between the planned (3 pp) and realised precision?
5. Group assignment and filters: is the DOT / other-cabinet / excluded mapping right (spot-check agencies), are
   templated classes and near-duplicates removed as described, and are procedural paragraphs handled as stated?
6. Does every number in report.md match the results files? Recompute the key ones.
7. Interpretation: is the "government-wide rise from mid-2025" and its attribution (LLM use vs. deregulatory/policy
   vocabulary) hedged appropriately? Is the exploratory analysis clearly labelled? Is anything overclaimed?
8. What would a computational social scientist or an expert on LLM-text detection (Liang et al. style estimators)
   object to? Use web search if useful.

Write your review to /mnt/citations/research-lab/runs/legal-digital-humanities-federal-register-llm-drafting/review/review.md
with a recommendation (publish / publish with edits / fix first), numbered issues with locations and concrete fixes,
and a table of recomputed numbers. Reply with the recommendation and the number of issues.
