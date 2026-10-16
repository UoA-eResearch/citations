You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/blue-pacific-port-cyclone-recovery/ (read-only except your output in review/).

The question: how long do ports take to recover after Category 3+ cyclones, and are small island ports - which often
carry most of a country's imports - slower? The lead claimed a Pacific-island median of >= 14 days, >= 2x non-island
ports, and that import share beats port size (dAIC >= 10). Data: IMF PortWatch daily port calls (2019-01 to 2026-07),
the PortWatch ports database, IBTrACS. Includes a forecast for the 2026-27 South Pacific season frozen before 1 Nov 2026.

**What to read:**

- plan.md (preregistration, commit d12c3f0 - committed before any recovery time was computed);
- deviations.md (D1-D7). D1-D3 predate the plan; D4 (analysis.py crashed on first run; descriptive tables were seen
  before the fix) and D5 (forecast part B drops the small-island indicator) came after the H1/H2 numbers existed;
  D6 records the forecast hashes; D7 is post hoc;
- report.md and report.html (pre-review draft, commit 1ad81ca);
- code/: events.py, recovery.py, test_recovery.py, detectability.py, analysis.py, test_analysis.py, forecast.py,
  score_forecast.py, supplementary.py, figures.py;
- results/tables/ and results/figures/.

**Git.** Read-only git in /mnt/citations is fine. Commit sequence: d12c3f0 (plan + all code + detectability, outcomes
unrun) -> 3c194e6 (D4 fix + test_analysis) -> 0c928af (results + frozen forecast) -> 7ff8873 (D7 code, unrun) ->
1ad81ca (draft). Check each stage's code predates the outcomes it produced.

**Environment:** venv/bin/python in the run directory (numpy 1.26, pandas, statsmodels, lifelines 0.30.3, scipy).
Data under data/raw/ (symlinked to the HDD at /mnt/data; daily.csv is 649 MB - read only the columns you need).
data/processed/ holds events_all.csv and recovery.csv. Do NOT pip install into that venv; if you need a package, make
your own venv under review/reviewer_checks/. Do not start or stop any Docker container. Multiprocessing is fine
(the machine has ~30 cores), but recovery.py takes ~30 min - rerun only subsets.

Check at least:

1. **Timing and disclosure.** Was every decision threshold fixed before the outcome it governs? D4: the descriptive
   table (1 of 17 small-island events disrupted) was seen before the H2 not-estimable guard was written. Is that guard
   a legitimate fix or an outcome-driven escape? Would any alternative (e.g. Firth-penalised or a pooled two-part
   time ratio) have given H2 a verdict? D5 likewise: is dropping the indicator from part B defensible, and does it
   change the forecast materially?
2. **The event table (events.py).** Spot-check closest-approach distances and categories for at least five events
   against IBTrACS, including antimeridian cases (Fiji, Tonga). Is USA_SSHS / USA_WIND the right category source for
   the South Pacific? Are the SIDS and PICT lists right (the SIDS list includes Singapore, Bahrain, Puerto Rico, Guam,
   the Northern Marianas)? Does including Singapore/Bahrain or excluding them matter?
3. **The recovery algorithm (recovery.py).** This is the core. Check the NB counterfactual, the reference-index
   offset (is the share-of-regional-traffic model sensible when the reference set changes event by event? what if a
   reference port is itself disrupted by a storm not in the event table?), the familywise disruption test, the
   traffic-scaled window, and the recovery rule. Does recovery start from the deepest dip (it changed from "first
   drop" - when, and was it disclosed)? Pick at least five real events (include Kingston/Melissa, Noumea/Niran,
   Cebu/Rai censored at 120, Lake Charles/Laura 56 days) and verify by plotting or tabulating calls vs counterfactual.
   Is the Cebu 120-day censoring a real disruption or an artefact (Omicron, holidays, a PortWatch break)?
4. **Detectability (detectability.py, F1).** Does the simulation match the real pipeline (no reference index in the
   simulation - does that matter)? Complete closures only - how much worse is detection for a 50% reduction? Are the
   false-alarm rates (up to ~12% at 0.25 calls/day) consistent with what the real "not disrupted" rate tells us?
5. **H1.** Recompute dAIC independently. Is a two-part AIC with clustered data meaningful at all here? The part-A
   import-share coefficient is negative (fewer detected disruptions). The report offers "ships cannot divert" and
   "residual detectability" - are there others (share correlates with being a national gateway port, port
   authority priority, bigger breakwaters; PortWatch's share is model-derived)? Is the sign stated as strongly as it
   should be, or more strongly?
6. **H2 and the "almost never disrupted" headline.** 1 of 17 vs 27 of 68. Are the 17 small-island events
   comparable (8 storms; Beryl/Melissa dominate; distances; categories)? The report's strongest surviving claim is
   "complete closures of two weeks or more were not what happened" at measurable small-island ports, resting on
   simulated power ~0.95. Attack this: power for a complete closure is not power for the closures that happen;
   ports reopening to a few ships would not register; Melissa at Montego Bay (Cat 4 at 16 km, dip to 0.54) is one.
   Is the claim supportable as worded?
7. **Post-hoc checks (D7, supplementary.py).** Is the power interpolation right (dispersion choice; clamping)? Is
   "simulated power as the control" a reasonable specification? Is the report leaning on post-hoc results harder
   than it should?
8. **The frozen forecast.** Re-derive forecast_table.csv from forecast_model.json with score_forecast.predict, for a
   few rows. Is the scoring procedure well-defined and runnable as written (score_forecast.py reads events_all.csv
   from data/processed after rerunning events.py on a new vintage - is that path handling right)? Medians up to 167
   days exceed the 120-day horizon - does scoring handle censoring? Would a reasonable scorer be able to run it in
   September 2027 without judgement calls?
9. **External check.** The report says the non-SIDS median of 6 days "is the median Verschuur et al. (2020) found".
   Verify the citation (journal, volume, article number, the 6-day median and the p95) by web search. Are the other
   prior-art entries accurate (CyPort arXiv:2509.22656; US DOT report; IMF WP 26/99)? Novelty: has anyone estimated
   port recovery after cyclones for Pacific island ports from AIS/PortWatch?
10. **Scope and framing.** Does the report anywhere suggest island ports are resilient? Is the "does not show" list
    complete (e.g. ports that lost AIS coverage, PortWatch revisions, call counting at anchorages)? Is the framing
    non-stigmatising and free of a country ranking?
11. **Numbers.** Does every number in report.md and the figures match the results files?
12. **Plain-language summary.** Is "## In plain terms" accurate and not overstated? In particular "If a port had been
    fully shut for two weeks, we would very likely have noticed" and "long, complete port closures were not what
    happened at the main island harbours we could see".

Write your review to review/review.md with:

- a recommendation (publish / publish with edits / fix first);
- numbered issues, each with its location and a concrete fix;
- a table of the numbers you recomputed.
