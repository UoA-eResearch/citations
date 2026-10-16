You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/energy-nz-geothermal-achievable-output-decline/ (read-only except your output
in review/).

The question: has New Zealand's existing geothermal fleet held its achievable output, 2000-2026, as planning models
assume? Measured as each field's monthly 95th percentile (P95) of half-hourly metered generation (EMI Generation_MD),
with trends between capacity changes. The lead compared realised decline with "MBIE's 3%/yr run down"; the plan
reinterpreted that before any data (D1).

**What to read:**

- plan.md (preregistration, commit c72cc2c, before any output series was built);
- deviations.md (D1-D3). D1 predates the plan; D2 (a date-parsing bug) was found before any trend existed; D3 is
  post hoc;
- report.md and report.html (pre-review draft, commit 2b39db6);
- code/: build_series.py, analysis.py, test_analysis.py, supplementary.py, figures.py, prefetch_gmd.sh;
- results/tables/ and results/figures/; data/raw/docs/ (the MBIE FGGS 2020 and EDGS 2024 PDFs).

**Git.** Read-only git in /mnt/citations is fine. Sequence: c72cc2c (plan + code, synthetic only) -> d0be78c (D2 fix)
-> 0ab005b (results + D3 code unrun) -> 2b39db6 (draft). Check each stage's code predates its outcomes.

**Environment:** venv/bin/python in the run directory (numpy 1.26, pandas 3, statsmodels, scipy, matplotlib). Raw
EMI files under data/raw/emi_gmd/ (symlinked to the HDD). Do NOT pip install into that venv; make your own under
review/reviewer_checks/ if needed. Do not start or stop any Docker container.

Check at least:

1. **The reinterpretation of MBIE's 3% (D1).** Read FGGS 2020 s3.3 yourself. Is "gross run-down before make-up
   drilling" a fair reading, or is the report now testing a straw man? Does any MBIE/EDGS/Transpower/CCC document
   actually model existing geothermal output as declining? Is "planning models assume flat" accurate?
2. **build_series.py.** Verify the kWh->MW conversion, the field mapping (every geothermal Gen_Code in every file,
   including ones that might be coded Geo/GEO/geothermal or mis-coded), the field sum's missing-value rule, the
   date handling (D2), DST days (46/50 periods), and duplicated plant-days. Recompute P95 by hand for at least
   three field-months from the raw CSVs.
3. **Is P95 "achievable output"?** Geothermal sometimes flexes (Wairakei is the field's swing plant; some plants
   ran down during low-price periods or transmission constraints). Could P95 trends reflect dispatch, consent
   changes or fluid reallocation rather than capability? Does month-of-year adjustment handle ambient effects
   adequately? Is P95 too insensitive (it needs only ~36 hours at capability a month)?
4. **Segmentation.** Are the documented events right and complete (dates, which plant, whether that plant is in
   Generation_MD)? Check at least: Wairakei binary (2005), Mokai stages, Kawerau KGL rerate 2017, TAOM 2018 (is it
   in the data in 2018-19 under another code?), Ngawha OEC4 date, Te Huka, Nga Awa Purua's 2010 commissioning,
   Poihipi, Ohaaki derating (installed 57 MW in 2019, register 44 MW in 2026 - when, and is it a capacity change
   that should have been cut, or decline that should not?). Is "retirements are not cut" right for Wairakei
   (A-station units retired around Te Mihi's commissioning, a reallocation, not decline)?
5. **The trend model and intervals.** Recompute at least three field trends independently. Is GLS-AR(1) adequate
   (residual ACF beyond lag 1)? Is inverse-variance combination of segments sensible when segments differ in
   plant mix? Is the fleet interval's correlation handling right? Does capacity weighting by mean P95 favour
   fields with a particular sign?
6. **H1/H2 and the verdict.** Do the decision rules match the plan exactly? With Wairakei and Rotokawa 57% of the
   weight, is "the fleet is flat" a statement about two fields? The last-10-years sensitivity is -0.44 (-0.99 to
   +0.12): is the report's emphasis on 26-year flatness fair?
7. **Post hoc (D3).** The Ohaaki -10.4%/yr run-down is fitted from a start year chosen at a peak and an end chosen
   where the series returns to its pre-step level - is that selection biasing it? Is attributing the 2008 jump to
   drilling supported (the report cites the NZGA field page; check it and any Contact annual reports)? Could the
   2008 jump instead be a metering/reporting change (e.g., a unit moving into OKI2201)?
8. **Mokai.** -1.53%/yr from 2008: check consent history (2024 expiry, renewal), any capacity change 2008-2026,
   and whether a reporting change could produce it.
9. **Novelty and facts.** Web-search for any fleet-wide NZ geothermal output-decline analysis (NZGW proceedings,
   NZGA reviews, EA reports). Verify quoted facts (Ohaaki capacities; Ngā Tamariki OEC5 dates; MBIE quotes).
10. **Scope and care.** Is the framing of iwi-owned/hosted fields careful and accurate? Any statement that could
    read as judging stewardship?
11. **Numbers.** Does every number in report.md and the figures match the results files?
12. **Plain-language summary.** Accurate and not overstated? Especially "Upkeep, not the reservoir, is what keeps
    the fleet level" and "across the fleet it has been".

Write your review to review/review.md with:

- a recommendation (publish / publish with edits / fix first);
- numbered issues, each with its location and a concrete fix;
- a table of the numbers you recomputed.
