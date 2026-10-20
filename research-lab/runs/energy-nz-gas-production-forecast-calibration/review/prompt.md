You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/energy-nz-gas-production-forecast-calibration/ (read-only except your
output in review/).

**The question.** Are the field-level gas production profiles that operators report to MBIE systematically
optimistic, and are the probabilistic reserve categories calibrated?

- **Forecasts.** Six vintages (as at 1 January 2019–2024) of MBIE's petroleum reserves workbook, recovered from
  Internet Archive raw copies because MBIE's site blocks scripted downloads.
- **Outcomes.** MBIE field-level gross and net production (1974–2023) and the national net series (to 2025).
- **Measure.** e = ln((F + 0.05)/(A + 0.05)); median by horizon with a field-cluster bootstrap.
- **Hypotheses.** H1 over-forecasting ≥ +5% at one year and ≥ +15% at three; H2 2P ultimate-recoverable revisions
  downward more than half the time; H3 1P revised down more than 10% of the time.
- **Reported verdicts.** H1 Supported, H2 Inconclusive, H3 Supported.

**What to read:**
- plan.md (preregistration) and deviations.md (D1);
- report.md and report.html (pre-review draft);
- code/: fetch.py, parse.py, analysis.py, figures.py;
- results/tables/: primary.json, by_horizon.csv, pairs.csv, national_pairs.csv, revisions.csv, vintages.csv;
- results/figures/;
- data/: raw/MANIFEST.json and the workbooks under raw/reserves, raw/gas, raw/mbie_other, raw/gic; the tidy
  profiles.csv, reserves.csv, realised.csv, national.csv, gic_annual.csv.

**Git.** Read-only git in /mnt/citations is fine. Check that plan.md was committed before any forecast was paired
with an outcome, that each code file was committed before its outputs, and what the post-hoc fixes changed (the
duplicate 2021 vintage; the identification of the national series as net).

**Environment.**
- Python: /mnt/citations/research-lab/runs/auckland-nz-crl-structural-uplift-prereg/venv/bin/python has openpyxl
  and numpy. Do NOT pip install.
- Your scripts and outputs go under review/reviewer_checks/, caches under review/reviewer_checks/cache.
- Use at most 8 cores. Be polite to web.archive.org: it rate-limits, and everything needed is already on disk.

Check at least:

1. **Parsing.** Re-extract at least three vintages independently from the workbooks: the vintage year, the gas
   block of the production-profile sheet (the LPG block follows it in the same sheet and must not be read as gas),
   and the ultimate-recoverable and remaining-reserve columns in PJ. Do the totals match the workbooks' own Total
   rows? Is any field dropped or double-counted?
2. **The realised series.** Is the claim that MBIE's energy-overview "Indigenous Production → Natural gas" line is
   the **net** series correct, and does it really match the field-level net sums and the published 102 PJ for 2025?
   Does using gross instead change any verdict?
3. **Pairing and the field map.** Is the map from workbook field names to MBIE's published fields defensible from
   names alone? What does the "Others" residual do to the median, and is the sensitivity excluding it honest? Does
   the union rule (a field that produced without being forecast) actually add the pairs it claims (6 of 258)?
4. **The statistics.** Recompute the medians, the field-cluster bootstrap and the decision rules. Is a
   field-cluster bootstrap defensible when all fields share a common year shock, and when only two vintages
   contribute at three years? Is the MDE calculation (2.8 × SE) right? Would clustering by target year or by
   vintage change the verdict?
5. **The reserve tests.** Is using ultimate recoverable (rather than remaining reserves plus production) the right
   way to test calibration? Is the 1% tolerance material? Does the 1P result survive restricting to fields with
   meaningful volumes? Is the H3 reading ("not a conservative floor") fair, given that 1P can fall when a
   development plan changes?
6. **Horizon definition.** The vintage "as at 1 January Y" is published mid-year, so h = 0 is part-observed and
   h = 1 may be partly known too. Does that undermine the h = 1 result?
7. **The missing vintages.** The 2025 and 2026 releases are not in the archive. Is the report honest about that,
   and does their absence plausibly bias the result in either direction?
8. **The report.** Every number against the tables; overstated claims; whether "the schedule is optimistic, not the
   volumes" is supported by H2 being Inconclusive rather than Refuted; the "In plain terms" section.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered
findings (severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.
