You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/astronomy-ztf-wd-debris-transit-occurrence/ (read-only except your output in
review/).

**The question.** How common are ZTF-detectable debris transits among Gaia white dwarfs within 500 pc (G < 20, dec >
-28)? Two preregistered rules (short dips: pooled 3-sigma faint-outlier excess; long dips: faint 30-day bins), the
known systems as positive controls, injection-recovery completeness, and lower/upper occurrence rates.

**Reported:** H1 Inconclusive. 109,074 eligible stars; 914 flagged; 21 Gaia DR3 CVs removed; 15 of 18 known systems
recovered; 878 unexplained candidates. Lower rate 2.1e-4 (1.2e-4 to 3.4e-4), upper 1.2e-2. Injection recovery 66% /
50% / 53% by class. D1: float-rounded Gaia IDs found after the first detection pass, fixed, everything re-run.

**What to read:** plan.md, deviations.md, report.md, results/plausibility.md, results/attribution_ledger.csv;
results/tables/ (primary.json, detect.parquet, inject.parquet, candidates.csv, known_systems.csv,
known_candidates_not_controls.csv, flagged_gaia_vari.csv, coverage.json, handtrace.json); code/ (sample.py,
fetch_lc.py, fix_ids.py, detect.py, variables.py, handtrace.py, figures.py). Data: data/sample.parquet, data/lc_v2/
(light-curve shards, good epochs only), data/raw_cat/ (the catalogue FITS).

**Git.** Read-only git is fine. Verify that plan.md preceded the light-curve fetch, that detect.py's rules and
injection details were committed before detect.parquet existed, and that known_systems.csv was committed before
detection.

**Environment.** Use venv/bin/python with -I. Do NOT pip install. Use at most 8 workers. `detect.py detect` takes a
few minutes; IRSA queries take ~40 s each (keep any re-fetch to a handful).

Check at least:
1. **Sample and light curves.** The cuts; the ID fix (are any light curves still merged or mis-assigned?); one object
   per filter; the 2-arcsec match; coverage counts.
2. **Rules.** Robust sigma per filter, the binomial test, nights, the 30-day bins and standard errors; whether the
   faint-outlier asymmetry near the detection limit (77% of stars have negative excess) biases the short rule.
3. **Positive controls.** Is the list complete and correctly matched? Are the class assignments fair? Why are the
   three missed systems missed?
4. **Completeness.** Injection realism (box dips, error scaling, dropping epochs fainter than 21 mag, season
   activity), the G x epoch binning, the exclusion of flagged stars, and the best-class combination.
5. **Rates and verdict.** The Poisson intervals, the lower/upper construction, whether "Inconclusive" is right, and
   whether the lower rate is fairly described as a floor.
6. **Candidates.** Are most long-dip flags plausibly systematics, as the report suggests? Spot-check a few.
7. **Report.** Every number against the tables; the title and plain terms.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.

**Gate checks (METHODS.md G1-G7).** G1 (plan section 3's leakage audit; was detection blind to the known list?), G2
(coverage.json stages catalogue, light_curves, eligible), G3 (plausibility.md), G4 (does not apply unless you find a
label set), G5 (review/overclaim_check.md passes and is honest), G6 (attribution_ledger.csv passes `python3 -I
../../tools/attribution.py check . --show`; spot-check 5 claims), G7 (does not apply). Report any missing or hollow
gate as a finding.
