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

## Confirmation pass

Reviewer: Fable 5.1, 2026-11-09.

Scope: deviations.md D2, report.md and report.html (both 2026-11-07), overclaim_check.md, code/score.py,
code/posthoc_review.py, results/tables/primary.json, primary_late7.json and posthoc_review.json. I recomputed the
numbers from `data/interim/` myself and did not take them from the brief. The checks in `review/reviewer_checks/`
were written without importing the study's scoring code. They ran with `venv/bin/python -I` (or `python3 -I`) from
outside the run directory, with paths passed as arguments.

- `confirm_1.py` / `.txt`: revision statistics per scoring hub on forecast target weeks, lags, the late (> 7 days)
  first-report cells, 2022–23 finality, and dropped units.
- `confirm_2.py` / `.txt`: what the 7 dropped 2022–23 units are.
- `confirm_3.py` / `.txt`: a full independent re-score:
  - WIS from the pinball-loss form;
  - pairwise reversals;
  - relative WIS and leaders under three rules: the name rule, the hub-and-baseline rule, and no exclusion;
  - the same with late first reports dropped;
  - 2024–25 leader instability (B = 200, a different seed).
- `confirm_4.py` / `.txt`: whether the G5 table matches report.md (using the tool's own `extract`, read-only), stale
  backings, and whether report.html carries the D2 edits.
- `confirm_5_gates.txt`: `tools/overclaim_check.py --verify` and `tools/attribution.py check --show`.

The headline numbers reproduce exactly from my own implementation:
- 527 / 8,441 = 6.24% overall (12/1,708; 79/2,611; 436/4,122);
- late7 541 / 8,439 = 6.41% (12/1,708; 89/2,611; 440/4,120);
- every leader under every rule.

### Final verdict: publish with edits

The D2 fixes are real. Every corrected number reproduces from the stored data, and the H2 verdict is now worded as
the evidence allows. What remains is wording. One sentence in the verdict block misdescribes the 2024–25
late-report cells, and three smaller statements need correcting (below). No result or verdict changes.

**Correction to the first review.** My finding 2 said NEU_ISI-AdaptiveEnsemble was best at h1–h3 "under both
truths". Under final truth at h1, PSI-PROF_beta is lower (NEU_ISI 0.849; `confirm_3.txt`). The report's "h1–h3
under first-report truth and h2–h3 under final truth" is correct.

### Original findings

- **1. Pooled revisions: fixed.** `score.py` now restricts to the scoring hub and to forecast target weeks.
  `confirm_1.txt` reproduces every cell of the report's table:
  - 2022–23: 1,841 / 47.5% / 9.3% / 0.0% / +4.3%;
  - 2023–24: 1,748 / 13.6% / 1.0% / 0.0% / +0.3%;
  - 2024–25: 1,625 / 44.1% / 8.6% / −8.0% / −10.5%;
  - lags 1.5 / 4.5 / 4.5 days.

  The title ("about 8% low"), the verdict table and the "bias, not size" bullet carry these numbers, and so does
  report.html (`confirm_4.txt`). One leftover: the backing column of G5 row 36 still cites the pooled
  "median signed −4.1%; 36% revised >10%". The sentence itself ("several percent low") is acceptable.
- **2. H2 name rule and bootstrap: fixed.** `confirm_3.txt` reproduces the eligibility results independently:
  - NEU_ISI-AdaptiveEnsemble has relative WIS 0.726/0.649/0.621 under first-report truth at h1–h3;
  - it is lowest at h2–h3 under final truth;
  - under the hub-and-baseline rule, the leader changes only at 2024–25 h1 (NEU_ISI → PSI-PROF_beta).

  The verdict line now reads "Supported under the preregistered name rule, but not robust to that rule and not
  distinguishable from the leader's sampling instability". The name-rule inconsistency (MIGHTE-Nsemble and the
  FluSight-lop_norm / trained_* models) is stated, and so is the metadata-based rule as future work.

  The instability percentages match `posthoc_review.json`: 55–63% / 59–65% / 50–77% at h0–h2. My rerun with another
  seed, B = 200, gives 57–75% / 59–68% / 55–81%, so the qualitative conclusion holds. With B = 200 the Monte Carlo
  error is about ±3.5 points, and at h0 the two seeds differ by 12 points. Two related wording points:
  - The table column "first vs final (the H2 criterion)" shows the B = 200 post hoc values (54%, 50% at h1, h2;
    49.5% at h2 is actually below the 50% threshold). The preregistered B = 500 values that decide H2 are 61% and
    53% (`primary.json`), and the text gives 78% for h0 from B = 500. The column should say it is B = 200, post hoc,
    and not the preregistered run.
- **3. Late first reports (G1): partly fixed.** The analysis is right.
  - `confirm_1.txt` reproduces the late-report shares: 8.1% of 2023–24 and 4.6% of 2024–25 scored forecasts;
    10.2% and 6.3% of target weeks.
  - `confirm_3.txt` reproduces the late7 re-score (6.4%, H1 unchanged) and the h0 leader change.

  Two text problems remain:
  - **(a) A verdict-block sentence is wrong for 2024–25.** It reads "Most of these first appeared a month or more
    later, when the values were largely settled: first and final are identical for 84–98% of such weeks". That
    holds for 2023–24: all 178 late target weeks are > 30 days late and 96% are identical. For 2024–25 it does not.
    The 103 late target weeks (2025-01-18 and 2025-06-21) first appeared a median 11.5 days after the week ended,
    none > 30 days, and only 39% are identical (13% for 2025-01-18; 23% of the late scored forecasts). G5 row 9 is
    labelled Supported, with a backing ("> 30 days for 68–100%, first==final 84–98%") that I cannot reproduce for
    2024–25.
  - **(b) One late7 leader change is not reported.** With late cells dropped, the name-rule leader at 2024–25 h2
    under first-report truth becomes FluSight-lop_norm, a hub ensemble the name rule does not catch
    (`primary_late7.json`, `confirm_3.txt`). The report mentions only the h0 change. This belongs with the
    eligibility point.
- **4. 2022–23 finality: fixed.** `confirm_1.txt` reproduces the finality numbers: 2,540 location-weeks, 22.7%
  identical, 39.8% differ > 10%, median 0, mean +3.5%. `confirm_3` matches the re-score of 2022–23 against the new
  hub's latest values (8 of 1,708 reverse, no leader change; posthoc_review.json). These figures are computed over
  all 2022–23 location-weeks. On the 1,834 forecast target weeks they are 18% identical, 37% > 10% and mean +0.8%.
  The report's "the same 2,540 location-weeks" is accurate but could say "all".
- **5. Numbers: partly fixed (one wording error).**
  - Lags (1.5 / 4.5 days), the 179 dropped 2023–24 units (Minnesota 91, Massachusetts 88), SigSci-BECAM,
    FluSight-base_seasonal and the 2025-05-03 Metaculus-cp file are all stated and correct.
  - The report says "186 forecast units were dropped for missing truth values: … 7 in 2022–23". Those 7 are
    MIGHTE-Nsemble forecasts for reference date 2023-03-06 (Alaska and New York) with a missing quantile value
    (`confirm_2.txt`). Every 2022–23 unit has old-hub truth. So 179 units were dropped for missing truth, and 7 for
    incomplete forecasts.
- **6. Positive notes: still hold.** My own pinball-form WIS gives identical pair counts, reversal counts and
  leaders, and 563,252 scored forecasts.

### Gates

- **G5:** `--verify` passes (39 rows). The table matches report.md sentence for sentence: no missing or extra rows
  (`confirm_4.txt`). The pass is not fully honest yet:
  - row 9 is labelled Supported but its 2024–25 claim fails (3a);
  - row 36's backing is stale (finding 1).
- **G6:** passes (3 claims). H1's DOI resolves to Mathis et al., "Evaluation of FluSight influenza forecasting in
  the 2021–22 and 2022–23 seasons…", which is the right work. The ledger still has no rows for three things the
  report relies on:
  - the method citations Bracher et al. 2021 and Cramer et al. 2022;
  - the external fact "national reporting rules changed in late 2024".

  None of these was added or changed by D2, and the tool cannot catch a missing row.
- **G1:** now addressed (finding 3).

### Remaining issues (required edits before publishing)

1. Rewrite the verdict-block sentence on late first reports so it is separate by season:
   - 2023–24: four end-of-season weeks first appeared months later; 96% identical to final.
   - 2024–25: two missed weekly commits about 11 days late; 39% identical.

   Re-label and re-back G5 row 9.
2. State that with late first reports dropped, the 2024–25 h2 first-report leader becomes FluSight-lop_norm, a hub
   ensemble not caught by the name rule.
3. Correct the units sentence: 179 units dropped for missing truth, and 7 MIGHTE-Nsemble units dropped for a
   missing quantile.
4. Label the instability table's last column as B = 200, post hoc, and distinguish it from the preregistered
   B = 500 shares (78/61/53/36%).
5. Re-fill the backing of G5 row 36 with the per-hub numbers.
6. (Optional) Add G6 ledger rows for Bracher 2021, Cramer 2022 and the late-2024 NHSN reporting change. Say "all"
   2022–23 location-weeks in the finality sentence.
