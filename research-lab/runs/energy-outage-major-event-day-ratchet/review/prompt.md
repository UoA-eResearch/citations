You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/energy-outage-major-event-day-ratchet/ (read-only except your output in
review/).

**The question.** Does the IEEE 1366 2.5β major-event-day (MED) rule hide the US outage trend it is meant to
normalise? State daily SAIDI from EAGLE-I county 15-minute snapshots (2015–2025), MCC 2022 customers, 25 included
systems (24 states + DC); rules: rolling 2.5β, frozen 2.5β (2015–2019), fixed 99th percentile, 10-year (2025 only),
all events. H1 masking ratio; H2 rolling − frozen MED-excluded trend; H3 Monte Carlo power ratio rolling/oracle.
Validation against EIA-861 (PUDL).

**What to read:** plan.md (950d8c0), deviations.md (D1), report.md and report.html (pre-review draft); code/
(fetch.py, build.py, analysis.py, simulate.py, figures.py); results/tables/ (primary.json,
primary_coverage_sensitivity.json, state_year*.csv, decomposition*.csv, simulation.json); results/figures/;
data/ (daily.csv, county_reporting.csv, build_cache/, raw/ with the EAGLE-I CSVs (11 GB), MCC.csv,
coverage_history.csv, DQI.csv, core_eia861__yearly_reliability.parquet, SHA256SUMS).

**Git.** Read-only git in /mnt/citations is fine. Check that code was committed before the outputs it produced, and
that D1 came before any series was computed.

**Environment.** Python: venv/bin/python in the run directory (pandas, numpy, scipy, pyarrow, matplotlib). Do NOT pip
install. Your scripts and outputs go under review/reviewer_checks/ (caches under review/reviewer_checks/cache). Use at
most 8 cores and avoid holding more than ~20 GB of RAM (read the raw CSVs in chunks or with column subsets). Do not
use localhost:8000.

Check at least:
1. **Daily SAIDI construction.** UTC→local conversion and day boundaries (including DST), the 15-minute assumption
   (are snapshots really every 15 minutes in every year? gaps? duplicates?), the 2023 `sum` column, the MCC
   denominator, zero-filling, year-boundary handling. Re-derive a few state-years independently from the raw CSVs.
2. **Inclusion rule** (coverage history and county-count stability) as preregistered; which states it admits.
3. **Thresholds and indices.** The 2.5β computation (window, non-zero days, logs, ddof), frozen and q99 rules, the
   10-year rule; the annual indices.
4. **Trends and bootstrap.** The panel regression, the state-cluster bootstrap, H1's rule (Inconclusive when the
   all-events interval includes 0) and H2's sign convention against the plan's wording.
5. **Decomposition** (Shapley over orders) and its summary.
6. **Validation.** The EIA side (IEEE-method utilities, customer weighting, with-MED SAIDI), the years, the Spearman.
7. **The Monte Carlo.** The mixture fit (zero days, truncated log-normal body, GPD tail; the ξ cap at 0.9), the
   scenarios as preregistered, detection rule, power ratio bootstrap, false-positive rates. Is scenario B's "leakage"
   result a genuine property of the rolling rule or an artefact (e.g. tail draws starting at u, body/tail definitions)?
8. **The report.** Every number against the tables; whether the headline verdict (Refuted) and the interpretation
   (normal-operations rise vs storm leakage) are supported; the "In plain terms" section.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in review/reviewer_checks/.
