You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/energy-nz-edb-quality-standard-ratchet/ (read-only except your output in
review/).

**The question.** Do New Zealand's default price-quality path resets ratchet distributors' unplanned SAIDI limits
upward with storms, and does the major-event rule matter?

**Data.** The data are the Commerce Commission's own interruption-level records, published with its DPP3 and DPP4
models:
- `data/raw/comcom/dpp3_zip`, the DPP3 bundle, with Stata code;
- `data/raw/comcom/dpp4_zip`, the DPP4 bundle, with R code;
- the limits and boundary values of the 2015, 2020 and 2025 determinations, transcribed by double entry
  (`transcription/`, `code/transcribe.py`).

**Reported:**
- H1 Inconclusive: no national trend, raw −0.7% a year (−5.3 to +3.4).
- H2 Inconclusive: frozen minus rolling +0.10 pp (−0.10 to +0.38).
- H3 Supported: the Commission's rule against the IEEE daily 2.5-beta rule changes exceedance years for 3 of 15
  distributors in 2021–2024.
- Descriptive: the DPP3 → DPP4 target rise is mostly outcomes at a fixed boundary (+104 of +115 minutes).

**What to read:** plan.md (note section 0, on what was seen before it), deviations.md (D1, D2), report.md, code/
(transcribe.py, panel.py, rules.py, analysis.py, figures.py), results/tables/ (panel_checks.json, validation.json,
primary.json, decomposition.csv, annual_rules.csv), results/figures/.

**Git.** Read-only git is fine. Verify that plan.md preceded every outcome aggregate: panel_annual.csv, primary.json,
and validation.json, which contains reference-period parameters.

**Environment.** Python is venv/bin/python, with -I. Do NOT pip install. It is CPU-only. Put scripts and outputs under
review/reviewer_checks/.

Check at least:

1. **The re-implementation of the Commission's rule (rules.py).**
   - The rolling 24-hour totals, the rank-1,104 boundary and the small-distributor ranks.
   - Major-event membership (windows containing a half-hour) and the cap at boundary ÷ 48.
   - Target, SD × √365.25 and limit.
   - Does the validation in validation.json really reproduce the Commission's outputs, or could it match for the
     wrong reason?
   - Why do 9 of 17 DPP3 limits not reproduce (D2)? Does that undermine H3's "recomputed limits" design?
2. **The panel (panel.py).**
   - The day-first date fix (D2), and the disclosure-year consistency assert.
   - The splice and the overlap check.
   - The Centralines decision.
   - Is the 2025 exclusion (D1) justified? Is the ICP-count proxy (median ICP minutes ÷ SAIDI) sound for weights?
3. **H1/H2 (analysis.py).**
   - The IEEE rule: calendar days, non-zero days, ddof, and excluding rather than capping.
   - The national index and trend.
   - The cluster bootstrap with 16 clusters, and the year bootstrap.
   - Is "no trend to mask" fair, or is the window too short or storm-dominated to say anything?
   - The no-2023 sensitivity's mechanical "Supported" (a negative raw trend): is it handled honestly?
4. **H3.**
   - Is the IEEE rule (b) a fair counterpart: daily capping at a 10-year 2.5-beta boundary, limit target + 2 SD?
   - Are the 3 differing distributors robust to small choices, such as strict vs non-strict thresholds, ICP minutes,
     or the Powerco and Aurora handling?
   - Is "the rule decides compliance" overstated, given that contravention rules and major-external-factor exclusions
     are not modelled?
   - Invercargill's IEEE boundary (55.9) is about equal to its limit (55.9). Is rule (b) degenerate for small
     distributors?
5. **Decomposition and descriptives.**
   - Is the boundary/outcome split order-dependent?
   - Are the plan section 0 descriptives (median +2%, cap bound 13 of 15) right?
6. **Report.** Check every number against the tables, and that the plain-terms section is fair. Is the title
   defensible?

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.
