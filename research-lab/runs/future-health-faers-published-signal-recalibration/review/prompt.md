You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/future-health-faers-published-signal-recalibration/ (read-only except your
output in review/).

**The question.** Do drug–event safety signals published from the FDA Adverse Event Reporting System (FAERS) in
2023–2025 survive an independent recomputation from public FAERS under one fixed protocol, calibrated against an
empirical null from negative-control pairs?

**Design.**
- Europe PMC search (2023–2025) → 1,830 abstracts → LLM extraction (local Nemotron 3 Nano, JSON schema; v2 after the
  round-1 check failed, D2) → eligible signals (ROR with CI, lower bound > 1, single RxNorm ingredient, a MedDRA PT
  after a fixed US→UK spelling map, a stated window, FAERS database, not an interaction) → at most 5 per paper.
- Recomputation: FDA quarterly ASCII files 2004Q1–2026Q2 in DuckDB (`data/faers.duckdb`), latest version per case,
  primary-suspect role, report-level 2×2 over the paper's own window. Variants: all suspect roles, no dedup, full window.
- Null: OHDSI negative-control pairs mapped to PTs (`code/negative_controls.py`), computed 2004Q1–2025Q4; MLE
  (Schuemie) and sample-SD fits; calibrated p, BH-FDR across eligible signals.
- **H1:** fewer than 60% survive (recomputed ROR > 1 and calibrated q < 0.05); paper-cluster bootstrap.
- **H2:** median published/recomputed ROR ≥ 1.25.

**What to read:**
- plan.md (preregistration), deviations.md (D1, D2, D2 outcome, D3);
- report.md and report.html (pre-review draft, commit d62a942);
- code/: fetch_epmc.py, extract_signals.py, validation_adjudication.py, validate_round2.py, rxnorm.py, eligible.py,
  fetch_faers.py, faers_db.py, negative_controls.py, recompute.py, validate_pipeline.py, analysis.py,
  null_sensitivity.py, figures.py;
- results/tables/ (primary.json, signals_results.csv, pipeline_check.csv, null_sensitivity.json,
  extraction_validation*.json/csv), results/asrun/ (the pre-D3 results), results/figures/;
- data/: signals_all.csv, signals_eligible.csv, signals_eligible_asrun.csv, recomputed.csv, recomputed_asrun.csv,
  negative_controls.csv, negative_controls_computed.csv, extract/signals_raw_v2.jsonl, raw/epmc/records.jsonl,
  faers.duckdb (open it read_only=True; it is 2.2 GB).

**Git.** Read-only git in /mnt/citations is fine. Check from commits and timestamps that code was committed before the
outputs it produced, that D2 came before any signal was recomputed, and how D3 relates to the first results.

**Environment.**
- Python: venv/bin/python in the run directory (pandas, numpy, scipy, statsmodels, duckdb, matplotlib). Do NOT pip
  install into it.
- Your scripts and outputs go under review/reviewer_checks/, caches under review/reviewer_checks/cache. Do not copy
  abstract sentences into committed files; cache/ is gitignored.
- Use at most 8 cores. Do not use the local vLLM server (localhost:8000); it is busy with another study.

Check at least:

1. **Extraction validity.** Re-adjudicate a fresh sample of at least 30 eligible signals against the abstracts
   (records.jsonl): drug, event, estimate, CI, window, FAERS, comparison. Is the 0.96 precision credible?
2. **Eligibility and D3.** Is the cap-after-PT ordering what the plan says? Is the spelling-map fix correct? What does
   D3 change, and could it have been chosen because of the results? Compare as-run with corrected.
3. **Recomputation.** Independently recompute at least 15 signals from the DuckDB tables with your own SQL (window,
   dedup, role, drug matching including brand names, PT match). Check the drug-matching regex for false positives
   (substring matches, combination products, salts) and false negatives (prod_ai coverage before 2014Q3).
4. **Deduplication across the 2012 legacy/FAERS boundary** and windows starting before 2004Q1.
5. **The null.** Recompute the MLE fit. The null is centred far below zero (exp(μ) ≈ 0.43). Is that an artefact of
   the PT mapping, of the controls' outcomes being rarely reported, or of the protocol? Is it appropriate to calibrate
   positive published signals against it? How sensitive is H1 to the centre (null_sensitivity.py is exploratory)?
6. **H1/H2 computation.** Calibrated p, BH across the right set, NaN handling (zero cells), the cluster bootstrap,
   the ratio for H2 (published estimate over recomputed primary ROR).
7. **Secondary models** and the variants, as reported.
8. **The report.** Every number in report.md against the tables; overstated claims; whether "In plain terms" is
   accurate; whether the limitations (one protocol, notoriety bias, what "survive" means) are stated plainly.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in review/reviewer_checks/.
