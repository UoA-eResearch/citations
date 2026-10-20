You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/auckland-nz-jade-water-value-calibration/ (read-only except your own
output in review/).

**The claim.** The Electricity Authority publishes weekly runs of JADE (the open-source hydro scheduling model
from the University of Auckland's EPOC) as its benchmark for hydro water values. This study scores all 152
published runs from 2023 to 2025 against the price actually settled at HAY2201 in each run's first fully
out-of-sample week (stage 2).

- **H1 Supported:** the realised price exceeded the simulated 90th percentile in 59.2% of weeks (95% CI
  46.1-73.0), against a nominal 10% and a preregistered threshold of 20%.
- **H2 Refuted:** low-storage weeks fail more often (90.0% vs 56.0%) but the ratio is 1.61 (95% CI 1.12-2.36),
  upper bound below the threefold threshold.
- **Headline descriptive claim:** the realised price fell outside the simulated 10th-90th band in 86.8% of weeks
  (59.2% above, 27.6% below); the median band is $15.03/MWh wide while realised weekly prices spanned $25.94 to
  $290.88, so the band covers 5.7% of the realised spread.
- **The report's interpretation** is that this measures how much of price variation inflow uncertainty alone can
  reach, NOT that JADE is a bad model. Judge whether that framing is honest, and whether it is applied
  consistently or quietly abandoned in the headline.

**What to read:** plan.md, deviations.md (D1), report.md and report.html; code/ (fetch.py, analysis.py,
figures.py); results/tables/ (primary.json, runs.csv, by_stage.csv); data/ (runs/, prices/, hmd/, run_index.csv).

**Git.** Read-only git is fine. Check that plan.md was committed before any simulated price met a realised one
(commit 1456733) and that fetch.py and analysis.py preceded their outputs.

**Environment.** Python with numpy:
/mnt/citations/research-lab/runs/energy-nz-hydro-marginal-emissions-horizon/venv/bin/python. Do NOT pip install.
Put scripts and outputs under review/reviewer_checks/. You may re-download from the EMI blob store
(https://emidatasets.blob.core.windows.net/publicdata) to verify any cached file; the dataset prefix is
"Datasets/Wholesale/Expected water values/". A full tidy_results.csv is 88 MB, so fetch at most a few.

Check at least:

1. **Is the comparison fair at all?** JADE's HAY node against the HAY2201 GXP final energy price: is that the
   right mapping, and is the model's price a quantity that should equal a settled nodal price? If it is not
   (a shadow price on an energy balance in a 3-node model, a different time convention, a different definition of
   peak/shoulder/offpeak hours), then the exceedance rate measures the mapping and not calibration. This is the
   most important check in the review; the whole study stands or falls on it.
2. **The week alignment.** The study claims stage 1 is the input-freeze week and stage 2 the first fully
   out-of-sample week, verified because every run's input timestamp falls inside its stage-1 week. Verify that
   independently, and check whether the hours_per_block weighting matches the blocks JADE actually prices. Does
   the result survive scoring stage 1 or stage 3 instead (the report says yes; confirm)?
3. **The realised average.** Prices are averaged over half-hour periods, treating each as equal time. Check the
   daylight-saving weeks (334 and 338 periods against JADE's fixed 168 hours), and whether a demand-weighted or
   block-matched average would change the exceedance rate materially.
4. **Re-derive the headline from raw files.** Pick three runs, including one outside the 2024 gas episode, and
   recompute p10/p50/p90 and the realised average from scratch. The report hand-verifies the week of
   12 August 2024 (91 sequences spanning $139.33-$173.04, realised $449.36); check that one and at least two
   others.
5. **The bootstrap.** Moving blocks of four runs over 152 weekly runs that overlap heavily in horizon: does that
   capture the dependence? Try a longer block and a run-level permutation, and say whether the H1 interval is
   trustworthy. For H2, the ratio statistic drops resamples where the denominator group is empty or zero
   (n_bootstrap_valid 1997 of 2000) - does that bias the interval, and is "Refuted" safe given it?
6. **H2's coverage.** The preregistered split uses 104 of 152 runs because the hydrological dataset ends
   2024-12-31, and the storage measure converts lake volumes to energy with a per-scheme GWh/Mm3 ratio. Check that
   conversion, check the week-of-year percentile (it excludes the run's own year), and check whether the
   deseasonalised sensitivity is a fair substitute or a different quantity.
7. **The two-tailed finding.** The spread statistics were added after seeing the results (D1 item 6). Are they
   described honestly as descriptive, and is the PIT histogram's U shape robust to the percentile method
   (linear interpolation on 80-91 points) and to ties?
8. **Over-claiming.** "A $15 band in a $265 market" compares a median within-run band to a between-week spread -
   two different things. Is the report clear about that, or does the headline trade on the confusion? Would a
   fairer statistic (for example the within-run band against realised week-to-week variation at the same horizon)
   tell a weaker story?
9. **The report against the tables.** Every number, the plain-terms section, and whether Supported/Refuted are
   stated with their limits rather than their best face.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered
findings (severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.
