Confirmation pass. You reviewed /mnt/citations/research-lab/runs/energy-nz-edb-quality-standard-ratchet/ ("fix first").
The agent's fixes are logged as D3 in deviations.md, and report.md was rewritten. Verify each of your findings 1–10,
finding by finding; do not redo the review.

- **Finding 1 (ICP weights).** Check panel.py's guard and results/tables/icp_flags.json (5 flagged, interpolated).
  Re-run your 01 check against the new panel_annual.csv, and confirm the new H1/H2 numbers in primary.json and the
  report: now 2014–2025, raw −4.1%/yr.
- **Finding 2 (2025).**
  - Check panel_checks.json (All rows; 26 of 28 within 5%; usable).
  - Check the Horizon alias and the Top Energy 2025 exclusion (panel.py build; analysis.py MISSING and H3 years),
    the MainPower filter, and NaN-aware national weighting.
  - Did including 2025 introduce any error?
- **Findings 3–10.**
  - D2/D3 text on the ±5% cap, and the Stata comparison in validation.json.
  - H3 variants (exclude, inert IEEE, margins, the 1.3–25× range).
  - The decomposition orderings and Shapley (decomposition.csv, primary.json).
  - The −1% median, the DPP3 contravention wording, the Table E3 citation, the sign-blind H1 handling, the title,
    and the small items.

Also check every number in the new report against the tables, and flag anything new the fixes introduced.

Write review/confirmation.md: a verdict (publish / publish with edits / fix first), then numbered new issues only.
Modify nothing else. Keep CPU moderate, no GPU, no pip installs.
