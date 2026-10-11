You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/health-econ-gbd-revision-calibration/ (read-only except your output in
review/). Read plan.md (preregistration, commit 6b7a3e2), deviations.md (D1-D2), report.md (draft, commit f672f50),
code/ (build.py, quality.py, analysis.py, exploratory.py, figures.py, run_all.sh), tests/synthetic_test.py,
results/tables/ and results/figures/, logs/. Use the study's venv (./venv/bin/python). You may run read-only git
commands in /mnt/citations (e.g. to confirm the plan was committed before results).

Data: data/raw/ihme/*.zip are IHME GBD Results tool downloads (see data/raw/ihme/SOURCES.tsv); data/raw/meta/ holds
the tool's public cause/location hierarchies; data/raw/who/ the WHO GHE 2021 methods PDF and Mortality Database
availability list; data/raw/appendix/ the GBD 2021 and GBD 2023 causes-of-death appendix 1 PDFs. IHME data are under
non-commercial terms and must not be redistributed: do not copy raw rows or GBD estimates into your review; derived
statistics (shares, counts, differences) are fine. Do not upload any of these files anywhere.

Check at least:
1. Panel construction: rebuild the 55,896-cell panel yourself from the raw zips. Are the joins, the 137 shared
   level-3 cause IDs, years and countries right? Are any causes non-comparable despite a shared ID (the report already
   flags Other neoplasms)? Is the level-3 classification from the hierarchy correct?
2. The C2 statistic: is the argument that P(|z| <= 1.96) >= 0.95 under calibration and non-negative error correlation
   correct? How much do the log-normal approximation, IHME's point estimate being a mean of draws (not the median),
   skewed small-count intervals, zero/near-zero cells and the eligibility rules bias C1, C2 and E1? Is E1 a fair
   benchmark? Would a different but defensible formulation change the verdicts?
3. Recompute the primary results (H1-H4) independently, including the two-way pigeonhole bootstrap, and check that the
   decision rules and the headline rule were applied as preregistered. Is the two-way bootstrap implemented correctly
   (multiplicities, shared cause draw for group contrasts)?
4. Data-quality groups: spot-check the WHO Table 4.1 extraction (pages 9-14 of the WHO PDF) and the country-name
   matching. Is classing the 85 countries absent from Table 4.1 as `none` defensible (absence from the WHO table vs. GBD
   having vital registration for them)? Spot-check the GBD garbage-code table parse (appendix pages 76-78).
5. Were H3/H4, the thresholds and the analysis code fixed before any GBD 2021 vs 2023 comparison (git history)? Do D1
   and D2 disclose everything done after outcomes? Is any exploratory result presented as if confirmatory?
6. Does every number in report.md (and the tiles in results/tables/tiles.json) match the results files?
7. Interpretation: is "intervals too narrow" justified given what GBD says its UIs represent? Is the response to IHME's
   "rounds are not comparable" objection fair? Are "about twice as wide (2.2x)", "about a third of the time", "the most
   useful finding" and the X5 year-split discussion supported and hedged appropriately? What would a GBD methodologist
   or a demographer object to? Use web search for prior work (e.g. Zavalis, Pezzullo and Ioannidis 2026, critiques of GBD
   uncertainty, IHME statements on UI meaning) and to check novelty.
8. Data-use compliance: do the published tables (by_country.csv, by_cause.csv, etc.) contain only derived statistics?

Write your review to review/review.md with a recommendation (publish / publish with edits / fix first), numbered issues
with locations and concrete fixes, and a table of recomputed numbers. Reply with the recommendation and the number of
issues.
