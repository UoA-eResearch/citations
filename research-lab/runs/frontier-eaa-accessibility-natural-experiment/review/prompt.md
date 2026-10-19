You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/frontier-eaa-accessibility-natural-experiment/ (read-only except your output
in review/).

**The question.** Did the European Accessibility Act (applying from 2025-06-28) reduce automatically detectable
accessibility failures on EU homepages in the consumer sectors it covers, relative to uncovered sites?
- **Data.** Archived homepages (Wayback, quarterly targets 2024-01 to 2026-04) of a seeded half-sample of Tranco sites
  on 14 EU ccTLDs, .co.uk, and a placebo (.com.au, .co.nz, .ca).
- **Outcome.** log(1 + violation nodes per 1,000 elements), from a frozen 19-rule axe subset under jsdom, with no
  scripts run.
- **Sector.** Assigned by marker rules from the earliest snapshot.
- **Model.** Two-way fixed-effects DiD.
- **Hypotheses.**
  - H1: EU relative change ≤ −15% with the upper bound < 0.
  - H2: the placebo stays within ±5%.
  - H3: overlay substitution.

**What to read:**
- plan.md, and deviations.md (D1–D7);
- report.md and report.html (the pre-review draft, commit 0c44d7a);
- code/: frame.py, cdx_v2.py, fetch.py, sector.py, validate_sector.py, metrics.py, axe_run.js, did.py, figures.py;
- results/tables/: primary.json, sector_validation*.csv, the frame samples;
- results/figures/;
- data/: frame/, cdx/ (eligible.jsonl), html/ (gzipped snapshots), sector.csv, metrics.jsonl, and validation/.

**Git.** Read-only git is fine. Check that each deviation came before what it governs (D1–D5 before any page fetch,
D6–D7 before any metric was analysed), and that the code came before its outputs.

**Environment.**
- venv/bin/python in the run directory. Do NOT pip install.
- Node is /mnt/research-lab-tools/node-v20.18.0-linux-x64/bin/node.
- Scripts and outputs go under review/reviewer_checks/, and caches under review/reviewer_checks/cache.
- Use at most 8 cores.
- Do NOT fetch from web.archive.org or Common Crawl. Everything needed is on disk.
- Do not use localhost:8000.

Check at least:
1. **Snapshots.** Snapshot selection and eligibility (≥ 2 of 4 pre, ≥ 2 of 3 post), the gzip/sha256 store, and whether
   any failed fetch was recorded as absence.
2. **Measurement.** The axe subset and jsdom settings. Re-run axe on a sample of 50 snapshots and compare with
   metrics.jsonl. Check the < 50-element drop and how often it differs by group and period, the 79 timeouts (D7),
   and Wayback replay artefacts (id_, toolbar injection) that could differ by period.
3. **Sector rules.** Marker leakage, such as a cookie banner or footer containing "cart". Re-adjudicate a fresh blind
   sample of at least 40 sites. Also: was the D6 subagent adjudication genuinely blind, and does the 0.87/0.88
   precision hold?
4. **The DiD.** The panel construction, fixed effects, clustering, period exclusions and decision rules. Recompute H1,
   H2, S1 and the event study independently. Check pre-trends, and sensitivity to dropping the transition quarter,
   to winsorising, and to the outcome transform.
5. **Composition.** Whether in-scope and out-of-scope sites differ in archive coverage or snapshot drops after the Act
   (selection into measurement).
6. **H3.** Whether "not testable" with one adopter is the right reading.
7. **The report.** Every number against the tables, overstated causal language, the minimum detectable effects, and
   "In plain terms".

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in review/reviewer_checks/.
