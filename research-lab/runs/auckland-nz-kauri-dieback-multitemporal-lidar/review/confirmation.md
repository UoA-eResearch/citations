# Confirmation pass: auckland-nz-kauri-dieback-multitemporal-lidar (D1, commit 920bde5)

Reviewer: Fable, 2026-10-24. Check script and output: `review/reviewer_checks/confirm_checks.py` / `.json` / `.log`
(aggregate only; the first review's outputs are untouched).

## Verdict: **publish with edits**

The D1 fixes are real and correctly implemented. Every number in report.md that I can check against primary.json
matches, and my independent recomputation on the D1 tree set reproduces the per-fold AUCs to four decimals (change
0.5464 / static 0.5733 / static + change 0.5946; 2021: 0.5569 / 0.5903 / 0.6104) and the shuffle nulls (40 shuffles:
0.476, 95th pct 0.521 vs the study's 0.481 / 0.522; 2021: 0.539 / 0.553 vs 0.539 / 0.560). Three small factual edits
are needed before publication (new issues 1–3 below); none changes a verdict.

## Findings of the review, one line each

1. **Estimator bias (MAJOR) — fixed.** `model.py:60-69` computes AUC within each test fold and averages over the 25
   fold evaluations; `boot_auc` (:72-82) block-bootstraps the per-fold AUC with the same block draw for all three
   models (paired gain, :113); `shuffle_null` (:85-97) permutes labels within blocks and refits (200 shuffles). All
   correct. The report drops the "chance" language, states the null (0.48 / 0.52) and keeps the preregistered rules;
   H1 Refuted (upper 0.58 < 0.70) and H2 Refuted (upper 0.0445 < 0.05) follow from them.
2. **2021 "faint signal" (MAJOR) — fixed.** report.md:23-24, :41, :117 now say no signal beyond place can be
   claimed (0.557 vs null 0.539 / 0.560); the within-block difference −0.10 m (−0.21 to +0.02) reproduces on the D1
   set (−0.098, −0.212 to +0.019).
3. **Label geometry (MAJOR) — addressed, with one wrong number (new issue 1).** The co-location is in the title,
   summary, plain terms and "does / does not show"; the generalisation is restricted (report.md:115-116, :45-46).
   The 92% and "a quarter" shares reproduce on the D1 positives (0.916; median 0.231). The "1.4 m" is misattributed.
4. **2 m merge (MODERATE) — fixed.** `features.py` now does single linkage within 2 m by status (cKDTree
   `query_pairs` + connected components); 6,871 / 222 / 77 matches my independent count exactly; deviations.md D1-1
   records it. The count of conflicting same-location statuses that deviations.md says is "counted" does not appear
   anywhere (new issue 4, optional).
5. **"Dropped for invalid LiDAR" (MODERATE) — fixed.** report.md:64 and the primary.json key now say slip mask;
   28 trees on the D1 set. The 2021 drop-outs (57 trees, 3%) and the slope correlation of the mask are not mentioned
   (optional).
6. **Height-dependent rise (MODERATE) — fixed.** Summary :25-27 and results :106-108 give the class range (about 0
   under 5 m to +3 m above 30 m), the definition range (1.06–1.88 m) and the datum checks (+0.05 m ground, +0.01 m
   bare-ground CHM); "stable" is no longer used in the report text.
7. **Provenance (MINOR) — fixed.** deviations.md:3-5 records the post-commit features.py edit; report.md:129.
   `primary_pre_d1.json` is byte-identical to the first run's primary.json.
8. **Bootstrap over fixed predictions (MINOR) — described honestly.** report.md:91-92 and the model.py docstring
   say the bootstrap holds each repeat's fold predictions fixed and that per-repeat spread is of the same size.
9. **Verified items — still hold.** trees.csv has no coordinate columns (10,027 rows, OBJECTID/survey/status +
   features); trees_xy.parquet remains untracked; rows align by OBJECTID; figures and captions are aggregate.

## New issues

1. **Wrong number in three places (edit before publishing).** report.md:18 ("a symptomatic tree's nearest healthy
   record is a median 1.4 m away"), :37 ("sick and healthy trees often stand a metre or two apart") and :114 ("Sick
   and healthy trees stand a median 1.4 m apart"). 1.4 m is the median nearest-neighbour distance among *all* 2014–15
   records regardless of status. A symptomatic tree's nearest healthy record is a median **3.2 m** away on the D1
   positives (3.6 m on raw records; `confirm_checks.json`, `labels_check.json`). Suggested wording: "survey records
   stand a median 1.4 m apart; a symptomatic tree's nearest healthy record is a median 3 m away, and 92% have one
   within 15 m". The title's "metres apart" is fine.
2. **Within-block 2014–15 difference is quoted from the pre-D1 tree set.** report.md:102 gives −0.13 m (−0.27 to
   −0.02), computed in the review on the grid-merged set. On the D1 set it is **−0.12 m (−0.26 to −0.01)**
   (`confirm_checks.json`). Update the number or say it was computed on the pre-D1 set; the conclusion is unchanged.
   Likewise "a median 25% symptomatic" (:20) is 23% on the D1 set; "about a quarter" is safe.
3. **deviations.md:17-18 overstates the null.** "Every model is also compared with a within-block shuffle null" —
   `model.py:119-120` computes it for the change model only (primary and 2021), which is what the report's table shows.
   Change to "the change model".
4. **Optional.** Add the conflicting same-location statuses (56 exact locations: 38 with status 1 + 2, 14 with 1 + 3,
   3 with 1 + 4, 1 with 2 + 3) that deviations.md says are counted; note that one third of 2014–15 negatives have a
   status 2–4 record within 15 m; consider softening the F2 title ("symptomatic trees rose slightly less") to match
   the within-block caveat in the text. "probably because the 2024 scan has more laser points" (report.md:43) is
   hedged but unverified; "consistent with" is the defensible form.

## Not changed by D1 and still fair

Plan rules, thresholds and the H1/H2 decision procedure are as preregistered; the switch of estimator is logged as a
post-hoc deviation forced by a flaw in the preregistered one, which is the right way to record it. No coordinates are
published in any tracked file or in the review outputs.
