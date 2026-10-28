You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/auckland-nz-fenz-impact-rainfall-thresholds/ (read-only except your output
in review/).

**The question.** Do New Zealand flood callouts (FENZ incident data) track how rare the day's rain is for a place,
its 6-hour maximum divided by the local HIRDS v4 median annual maximum, better than its raw depth?

**Reported:**
- **H1 Supported by the preregistered rule.**
  - Held-out FY2024/25 log-loss difference 3.9×10⁻⁵, storm-day bootstrap 0.6–8.3×10⁻⁵.
  - Skill ratio S = 1.076 (bar 1.05).
  - Leave-one-region-out: 7 of 9 regions.
- **The margin is fragile.** Only 64 held-out flood suburb-days, 24 of them in the Nelson–Tasman floods of late June
  2025. Without those days the interval includes zero (post hoc).
- **Secondaries:** 24 h supports, 1 h slightly favours depth, broader outcome definitions are inconclusive.
- **Onset thresholds:** common to all regions by construction.

**What to read:**
- plan.md and deviations.md:
  - D1: a rain-record physical screen, region per suburb, file formats;
  - D2: geocoding and suburb-key fixes from the G4 audit, and a stopped first run quarantined unread, then opened
    after the final result.
- report.md and results/plausibility.md.
- code/: build_fenz.py, geocode.py, rain_daily.py, panel.py, analyse.py, posthoc.py, g4_check.py, figures.py.
- results/tables/: primary.json, secondary.json, posthoc.json, onset.csv, coverage.json, g4_geocode.json,
  g4_window.csv, geocode.json, fenz_rows.json, v0_unseen_flawed_geocoding/.
- Data under data/ (not in git): panel.parquet, fenz_daily.parquet, suburbs.parquet, rain_daily.parquet, raw/
  (FENZ CSVs and metadata PDF), raw_gaz/.
- The rain series come from ../auckland-nz-hirds-out-of-sample-exceedance-audit/data. Do not copy Auckland
  Council's raw data into review/.

**Git.** Read-only git is fine. Verify:
- plan.md was committed before build_fenz.py's outputs;
- analyse.py was committed before the first run;
- D2's account of the stopped run is accurate (file times, the sha256 it records).

**Environment.** Python is venv/bin/python (symlinked to the HIRDS lead's venv), with -I. Do NOT pip install. Keep to
at most 4 processes. analyse.py takes about 20 minutes; you need not rerun all of it. Put scripts and outputs under
review/reviewer_checks/.

Check at least:

1. **Outcome construction.**
   - Time conversion (civil time to NZST), the 2024/25 day-first dates and encoding, and suburb-day aggregation.
   - Is "Flood" the right primary outcome, given that cyclone-coded incidents dominate Gabrielle day in Hawke's Bay?
2. **Geocoding.**
   - Name normalisation plus the council-consistency filter, which uses gauge locations.
   - Could the filter bias which suburbs enter? Spot-check 10 suburbs against their real locations.
3. **Rain assignment.** Nearest usable gauge within 10 km, daily windows ending in the day, antecedent rain, the
   physical screen, and the quality rule (2xx kept).
4. **The models.**
   - Spline knots chosen separately for depth and rarity from their own distributions; the deviation-coded regions
     (unseen region = average) in leave-one-region-out; the suburb-activity covariate.
   - Is the comparison fair? Rarity divides by a per-gauge constant, so does it smuggle in location information that
     depth lacks? Region effects and suburb activity are in both.
5. **Inference.**
   - The storm-day bootstrap with 64 events.
   - The S condition rewritten as an inequality.
   - Leave-one-region-out counting a region with zero held-out floods.
   - Is "Supported" honest given the post hoc sensitivity to one event?
6. **Onset thresholds.** The plan asked for region-specific thresholds, and the models make them common by
   construction. Is the report's handling adequate?
7. **Report.** Check every number against the tables and the plain-terms section.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/. Paraphrase rather than quote any source text; the lab never commits quoted source text.

> **Gate checks (METHODS.md G1–G7).** Verify:
> - **G1:** plan.md's leakage audit is real and complete; look for label-correlated fields it missed.
> - **G2:** `results/tables/coverage.json` exists, and no unplanned fallback entered a statistic.
> - **G3:** `results/plausibility.md` traces three units, and the asserted invariants hold.
> - **G4:** every validation metric has an error audit with a judgeable denominator.
> - **G5:** `review/overclaim_check.md` passes and is honest; re-label any sentence you disagree with.
> - **G6:** `results/attribution_ledger.csv` passes `tools/attribution.py check`; spot-check 5 claims against
>   their sources, including the role and conditions. Two DOIs in this lab resolved to the wrong paper this week,
>   so check titles, not just resolution.
> - **G7:** validation labels come from two blind labellers, with agreement reported (does not apply; confirm).
>
> Report any gate that is missing or hollow as a finding.

When you finish, reply with a short summary: the verdict and a one-line description of each finding.
