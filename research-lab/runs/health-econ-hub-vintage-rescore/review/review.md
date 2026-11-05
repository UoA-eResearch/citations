# Review: health-econ-hub-vintage-rescore

Reviewer: independent adversarial review (Fable 5.1), 2026-11-05. Scripts and outputs in `review/reviewer_checks/`
(`checks1.py`–`checks4.py` with `.txt` outputs, `files_not_loaded.csv`). All checks used `venv/bin/python -I`
with `code/` on `sys.path`; `score.py test` passes; git in the hub clones was read with `-c safe.directory=*`.

## Verdict: fix first

H1 holds: 6.2% of pairwise orderings reverse (527 of 8,441; I reproduced the point estimate from the interim data
and the study's own functions), and the forecast loading is clean (no duplicates, 23 quantiles everywhere, every
unloaded hub file is a non-quantile or peak-target file). But (1) the revision table and the gate-added
"bias, not size" bullet are computed on truth rows pooled from both hubs for the same weeks, so the 2022–23 numbers
are wrong and the 2024–25 bias is understated by half; (2) the H2 "Supported" rests on a name rule that excludes
the model that is actually best at h1–h3 under both truths, and the bootstrap criterion it passes is met by the
leader's baseline instability alone (the leader moves in 55–66% of resamples under a single truth); (3) 8% of
2023–24 and 5% of 2024–25 scored forecasts land on location-weeks whose "first report" is a late, already-revised
version (G1), unreported; (4) the lag figures in the report are wrong.

## Findings

### 1. (Major) Revision statistics pool the old and new hubs for the same location-weeks

Evidence: `checks1.txt` (revision stats by hub × season). `score.py:290-296` groups `T` by the season of
`target_end_date` without conditioning on `hub`. The new hub's `target-hospital-admissions.csv` contains weeks
back to 2022-02-05 and its first commit is 2023-10-03, so for 2022–23 the "first report" in the new hub is a
value published 66–388 days after the week (`lag_med` 244 days) and is almost always the final value. The report's
2022–23 row (27% revised > 10%, median |revision| 1.0%) averages 2,559 old-hub rows (43.6% > 10%, median |rev|
7.8%) with 2,540 new-hub rows (11%, median 0). Restricted to the hub that scored the season and to forecast
target weeks (the set that matters for H1):

| season (hub) | n | revised > 10% | median \|rev\| | median signed | mean signed |
|---|---|---|---|---|---|
| 2022–23 (old) | 1,841 | 47.5% | 9.3% | 0.0% | +4.3% |
| 2023–24 (new) | 1,748 | 13.6% | 1.0% | 0.0% | +0.3% |
| 2024–25 (new) | 1,625 | 44.1% | 8.6% | −8.0% | −10.5% |

So 2022–23 revisions were as heavy as 2024–25's (not "27% vs 36%"), first reports in 2022–23 ran *high* on average,
and the 2024–25 downward bias is about −8% on forecast weeks, not −4.1%. The qualitative story added at the G5/G3
gate (bias rather than size goes with reversals) survives, but every number in the revisions bullet, the results
table's last two columns, overclaim rows 15–17 and the title's "ran low" magnitude must be recomputed per hub.

Fix: `Tt = T[(T.hub == "old") & season == "2022-23" | (T.hub == "new") & season >= "2023-24"]` (and preferably
restrict to forecast target weeks); re-run; re-fill the overclaim rows.

### 2. (Major) H2 depends on excluding, by name, the model that is best at h1–h3 under both truths; the bootstrap criterion is met by noise

Evidence: `checks2.txt` (top-5 tables), `checks3.txt`. In 2024–25, `NEU_ISI-AdaptiveEnsemble` has the lowest
relative WIS at h1, h2 and h3 under both first-report and final truth (0.726/0.649/0.621 first; the next model
is 0.04–0.11 behind). It is a single team's submission and is removed only because its name contains "ensemble"
(`score.py:176-178`). With team submissions eligible and only hub models (`FluSight-*`) and baselines excluded,
the best model is unchanged at h2 and h3, and changes at h1 only from NEU_ISI-AdaptiveEnsemble to PSI-PROF_beta.
The rule is also inconsistent: `MIGHTE-Nsemble` (an ensemble by name and nature) is eligible and 2nd at 2023–24
h2–h3; `FluSight-lop_norm`, `FluSight-trained_mean` and `FluSight-trained_med` (hub ensembles) are eligible.

The bootstrap rule does not rescue H2. Re-running the study's bootstrap (B = 200) and asking how often the leader
differs from the point-estimate leader under the *same* truth: 2024–25 h0 0.61/0.66 (first/final), h1 0.59/0.60,
h2 0.55/0.58, h3 0.56/0.41, against "first ≠ final" shares of 0.79, 0.56, 0.51, 0.41. The h0 case (identical
point-estimate leaders, 78–79% "different" in resamples) shows the criterion fires on near-ties regardless of the
truth version. So "the top model changed in about half of resamples" is a statement about a near-tie, not about
revisions; under a single truth the leader is just as unstable.

Fix: keep the preregistered rule as the primary verdict but state in the verdict bullet that (a) under both truths
the best 2024–25 model at h1–h3 is NEU_ISI-AdaptiveEnsemble, excluded by the name rule, and (b) the bootstrap
instability under one truth equals the first-vs-final share. "Supported, narrowly" should become something like
"Supported under the preregistered name rule; not robust to it, and not distinguishable from leader instability".
Overclaim rows 1, 9–12, 25 and 27 need relabelling. For the future, define ensembles by the hub's own metadata, not
by name.

### 3. (Moderate, G1) "First report" is a late, revised version for 8.1% of 2023–24 and 4.6% of 2024–25 scored forecasts

Evidence: `checks4.txt`. The new hub commits weekly during the season only. The last four 2023–24 target weeks
(2024-05-04 to 05-25) first appear in a commit made months later; for 97% of those 208 location-weeks the
"first" value equals the final one. In 2024–25 the week ending 2025-01-18 (all 53 locations) and 2025-06-21 first
appear > 10 days late (a missed weekly commit), and 41% of those cells have first = final. These cells make the
two truths identical by construction and bias the reversal share toward zero; the report's "median lag 11 days"
hides them and its "none precedes the week's end" is true but not the relevant leak.

Fix: drop cells whose first hub version is more than ~7 days after the week's end (or take first reports from the
NHSN release history), re-run, and report the share dropped.

### 4. (Moderate) 2022–23 "finalised" values are not final

Evidence: `checks2.txt`. For the 2,067 2022–23 location-weeks present in both hubs, only 22% have the same value in
the old repository's last version (2023-11-22) and the new hub's latest file; 36% differ by more than 10% (median
0, mean +3.5%). The plan foresaw this limit, but with a third of values moving by > 10% after the "final" vintage,
the 2022–23 first-vs-final comparison is a comparison of two early vintages. The report should say so with the
number, and could re-score 2022–23 against the new hub's latest values as a sensitivity check.

### 5. (Minor) Numbers in the report that do not match the data

- "median lag … 2 days in 2022–23 and 11 days later": on forecast target weeks the median lag is 1.5 days (old hub,
  Sunday regeneration of a daily feed) and 4.5 days (new hub, the Wednesday NHSN release). 11 is not reproducible
  from `truth.parquet` (`checks1.txt`, `checks2.txt`).
- "27% / 36% revised > 10%", "median 4.1% below": see finding 1.
- Dropped units (G2): 179 forecast units (Massachusetts and Minnesota, 2023–24, missing truth values) and
  `Metaculus-cp` 2025-05-03 are silently dropped; `SigSci-BECAM` (28 files, pmf-only rate-change target) and
  `FluSight-base_seasonal` (peak targets) are correctly not loaded. State the 179 and the non-quantile models.
- The 1.5-day old-hub lag means 2022–23 "first reports" are Sunday aggregates of a daily feed with heavy
  within-week backfill; the two seasons' "first report" are different objects (the plan's comparability caveat
  deserves these numbers).

### 6. (Minor) Things that are right and worth saying

WIS (interval form) matches the pinball identity; quantiles sorted before scoring; the old hub's `forecast_date`
is Monday for every model and target_end_date − ref_date is 5/12/19/26 days, so cells are comparable across
models; location codes normalise correctly ("US" and zero-padding); no duplicate submissions; model counts match
the hubs' quantile-submitting models (33/39/51); pairs ≥ 100 common cells and ties handled; relative WIS uses the
full comparison set with eligibility applied only to the winner (Cramer et al.); plan (03:11) preceded the
scorer (03:13) and all outputs (03:40–03:43); D1 is as allowed by the plan.

## Gate checks

- **G1:** fails as a leak for the late-first-report cells (finding 3); no leak of post-deadline commits into
  first reports otherwise (min lag 1.5/4.4 days after week end).
- **G2:** dropped units not counted in the report (finding 5); none hides a result.
- **G5:** `review/overclaim_check.md` is present and the gate edits were honest, but rows 15–17 rest on the pooled
  revision numbers (finding 1) and rows 1, 9–12, 25, 27 on the name rule and bootstrap criterion (finding 2).
- **G6:** `python3 -I ../../tools/attribution.py check . --show` → "G6 passed (3 claims)".
