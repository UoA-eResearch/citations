You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/movement-nz-ev-policy-discount-vs-ruc/ (read-only except your output in
review/).

**The question.** New Zealand ended the Clean Car Discount on 31 December 2023 (E1) and applied road user charges
to light EVs and plug-in hybrids on 1 April 2024 (E2). How much of the EV registration collapse is each? Non-plug
hybrids lost the rebate but were never moved to road user charges, so they identify E2 only.

- **Data.** NZTA Motor Vehicle Register via ArcGIS aggregation queries; 1,419,410 light-vehicle first
  registrations, 2021-01 to 2026-09.
- **H1.** R = (December 2023 excess) / (January-March 2024 shortfall) against a trend-and-month baseline fitted
  2021-01 to 2023-09. Reported R = 0.09 (CI -0.40 to +1.07), verdict Inconclusive.
- **H2.** Q = |delta_RUC| / |delta_CCD|, delta_RUC a difference-in-differences against hybrids across April 2024.
  Reported +32% (CI -36% to +153%), Q = 0.16 (CI 0.01-0.53), verdict Inconclusive.

**What to read:** plan.md, deviations.md (D1), report.md and report.html; code/ (fetch.py, analysis.py,
figures.py); results/tables/ (primary.json, monthly.csv, placebos.csv); data/registrations.csv and data/raw/.

**Git.** Read-only git is fine. Check that plan.md was committed before the series was built and that code came
before its outputs.

**Environment.** Python:
/mnt/citations/research-lab/runs/auckland-nz-crl-structural-uplift-prereg/venv/bin/python (numpy). Do NOT pip
install. Scripts and outputs under review/reviewer_checks/. You may re-query NZTA's ArcGIS service
(services.arcgis.com/CXBb7LAjgIIdcsPt/.../MVR_Mar26) politely to verify counts; do not fetch nzta.govt.nz, which
blocks scripted requests.

Check at least:

1. **The counts.** Re-query the service independently for a few months and powertrains. Does `data/registrations.csv`
   match? Are the motive-power groupings right (is `PETROL ELECTRIC HYBRID` a non-plug hybrid? should
   `ELECTRIC [PETROL EXTENDED]` be treated?), and does misclassifying them change anything?
2. **Snapshot bias.** The register holds vehicles still registered in September 2026. Quantify the attrition
   gradient (for example by comparing an older MVR service, `MVR_April2021`, with this one for the same months) and
   say whether it can generate the December 2023 spike or the 2026 recovery.
3. **H1.** Is the baseline specification defensible for a series growing this fast? Does a different functional
   form (log-linear vs level, trend break, Poisson) change R materially? Is the preregistered rule (lower bound
   >= 0.5) sensible when R is a ratio of two noisy quantities and the denominator is near zero in some draws? Is
   the "leans against H1" wording in the report fair given an Inconclusive verdict?
4. **The bootstrap.** Residuals are taken around the baseline before 2023-10 and around each analysis window's own
   mean afterwards. Does that understate or overstate uncertainty? Is the three-month block sensible with monthly
   seasonality? Recompute with an alternative scheme.
5. **H2 and the placebos.** Is the hybrid control valid (did hybrids face any other change in 2024)? The 2026
   placebo (+43%) exceeds the real estimate (+32%) - does that mean the design is uninformative, and does the
   report say so clearly enough? Would a longer post window, or market share instead of counts, do better?
6. **The recovery claim.** The report says the fall "did not last", against a preprint describing it as lasting.
   Is that supported, given the preprint measures market share and may cover a shorter window? Is comparing
   January-September 2026 with full-year 2023 a fair comparison as written?
7. **The ute result.** Is the December 2023 trough and January 2024 spike in diesel utilities real in the data, and
   is the causal language around it appropriately hedged?
8. **The report.** Every number against the tables; the plain-terms section; whether two Inconclusive verdicts are
   presented honestly rather than buried under the descriptive findings.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered
findings (severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.
