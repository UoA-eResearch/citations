You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/auckland-nz-hirds-out-of-sample-exceedance-audit/ (read-only except your
output in review/).

**The question.** Since HIRDS v4, New Zealand's design-rainfall system, was fitted (records ending 2015–2017), have
annual-maximum 6-hour rainfalls exceeded its 10% AEP depths at least 1.3 times as often as stated?

**Reported:**
- **H1 Inconclusive.** O/E is 1.49: 258 against 172.9 expected, over 1,729 gauge-years at 201 gauges in seven
  regions. The 95% water-year block interval is 0.78–2.35.
- **In-sample control** (years up to 2014/15): 0.89 (0.69–1.12), so it holds.
- **Secondaries:**
  - 1 h: 1.52 (1.01–2.06); 24 h: 1.91 (1.06–2.87);
  - against HIRDS's RCP4.5/8.5 2031–2050 depths: 1.01 / 0.97;
  - without Jan–Feb 2023: 1.17.
- **Auckland:** no Auckland gauge meets the inclusion rule; a post hoc relaxed look is reported.
- **A reader bug.** The first full run used corrupted series: tips sharing a minute were dropped. That run gave O/E
  1.29 and was seen before the bug was found (D5). All series were refetched.
- **A physical screen came after the corrected results** (D6: spikes over 50 mm in 15 min, stuck sensors). It
  removed 3 false exceedances (O/E 1.51 → 1.49). Tables from before it are in results/tables/v1_before_screen/.

**What to read:**
- plan.md and deviations.md:
  - D1: the HIRDS API and the G1 rule;
  - D2: completeness, resolution and quality rules;
  - D3: the structural resolution test and early years;
  - D4: Auckland;
  - D5: the reader bug;
  - D6: the physical screen (judge whether its thresholds are generic or tuned).
- report.md and results/plausibility.md.
- code/: inventory.py, fetch.py, fetch_auckland.py, structure.py, depths.py, maxima.py, g4_check.py, analyse.py,
  posthoc_auckland.py, figures.py.
- results/tables/: primary.json, secondary.json, coverage.json, gauges.csv, year_by_year.csv, g4_check.csv,
  g4_raw_check.csv, posthoc_auckland.json, and v0_invalid_minute_dedupe/.
- Data (not in git): data/series/*.npz (t in fractional minutes, v mm, q NEMS code), data/series_early/,
  data/maxima.parquet, data/hirds_depths.parquet, data/hirds_sites.parquet, data/inventory*.parquet.
- Auckland Council's raw data must not be copied into review/ or quoted.

**Git.** Read-only git is fine. Verify:
- plan.md preceded any rainfall value or HIRDS depth;
- D2 and D3 preceded any exceedance;
- analyse.py was committed before the first run;
- D5's account of what was seen, and when, is accurate (commit times against `results/tables/v0_*`).

**Environment.** Python is venv/bin/python, with -I. Do NOT pip install. Keep to at most 4 processes. The council
servers are public. If you refetch to check the reader, take a handful of gauge-years at most, at one connection.
The HIRDS API key is not for your use: do not read ~/.config/niwa-hirds. Use data/hirds_depths.parquet. Put scripts
and outputs under review/reviewer_checks/.

Check at least:

1. **The reader and incremental semantics.** Hilltop and AQUARIUS values are rain since the previous record. Are
   intervals, boundary records and NaN handled correctly in fetch.py, fetch_auckland.py and maxima.py? Is the raw
   refetch check (g4_raw_check.csv) convincing? Spot-check another gauge-year or two.
2. **Completeness rules (D2/D3).**
   - Is treating zero-closed silences as dry in compressed-logging years, and as outages in dense years, defensible?
     Is the 2% "dense" threshold applied sensibly?
   - Does any rule select on rainfall in a way that biases O/E up or down? The report claims the known biases run
     downward. Test that claim, e.g. with the S2 sensitivity and the in-sample control.
3. **Annual maxima.** 5-minute grid; a window is assigned to the water year in which it ends. The 6-hour window is
   compared with HIRDS's sliding-window depths. Any off-by-one or year-assignment problem?
4. **HIRDS depths.** Point API at gauge coordinates; Hawke's Bay's coordinates converted from NZ Map Grid. Spot-check
   a few gauges' coordinates and depths for plausibility. Is AEP = 1/ARI right?
5. **G1.** Out-of-sample windows shift where HIRDS's site list (within 100 m) shows data used into 2017. Is 100 m
   right? Could gauges that fed HIRDS under another name or coordinate be missed? Does the fitting/non-fitting split
   support the claim that overlap does not matter?
6. **Inference.**
   - The water-year block bootstrap has only 9 blocks. Is the interval honest, or too narrow or too wide?
   - Is the storm-cluster bootstrap a fair cross-check?
   - Should the verdict lean on the consistency across durations, given they share storms?
7. **The bug episode (D5).** Was the fix purely mechanical? Did anything else change between the invalid and the
   corrected runs? Does the report disclose the first run adequately?
8. **Auckland.** Is the explanation for zero qualifying Auckland gauges right (G1 shift, 2xx grades)? Is the post hoc
   look labelled and caveated enough?
9. **Report.** Check every number against the tables, and the plain-terms section, especially the climate-projection
   comparison and any causal wording.

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
> - **G7:** validation labels come from two blind labellers, with agreement reported (does not apply here; confirm).
>
> Report any gate that is missing or hollow as a finding.

When you finish, reply with a short summary: the verdict and a one-line description of each finding.
