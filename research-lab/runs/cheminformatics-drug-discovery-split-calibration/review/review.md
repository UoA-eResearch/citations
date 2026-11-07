# Review: cheminformatics-drug-discovery-split-calibration

Reviewer: independent adversarial review, 2026-11-05. Scripts and outputs in `review/reviewer_checks/`
(`checks1.py`–`checks3.py` with `.txt` outputs). Checks used `venv/bin/python -I` on the stored tables, the fit
JSONs and the ChEMBL InChIKey extracts; no model was retrained.

## Verdict: publish with edits

The study holds up. I could not break the prospective truth: the strict set's compounds really are new, and the
InChIKey concern the brief raises is quantitatively negligible (finding 5). Every number in the report matches its
table, the per-splitter similarity figures quoted from `data/fits` are right, the timeline is as claimed (targets
written 03:49, training started 03:51, committed 05:09, first fit completed 06:34), the three plausibility traces
reproduce exactly, and coverage reconciles (37,600 + 425 + 145 = 38,170). H1 is solid and H3's conclusion is
stronger than the report argues. Three things need correcting: the noise floor behind "not just noise" is
understated by about 40%, the H2 and H3 bars sit close to what the design could ever achieve and the report does
not say so, and the lenient sensitivity rests on sets too small to carry the sentence built on it.

## Findings

### 1. (Moderate) The noise floor for H2 ignores the retrospective estimate's own noise and is understated

Evidence: `checks2.txt`, `code/noise_check.py:16-18`. The exploratory floor (0.045) comes only from the normal-theory
standard error of the prospective RMSE (median 0.066). The retrospective estimate is a mean of 5 repeats whose
standard error I computed from the stored per-repeat RMSEs: 0.068 (document), 0.067 (assay, cluster), 0.052
(author). Combining the two sources:

| splitter | SE(retro mean) | SE(prospective) | combined | expected median \|bias\| from noise | observed |
|---|---|---|---|---|---|
| document | 0.068 | 0.066 | 0.095 | 0.064 | 0.167 |
| assay | 0.067 | 0.066 | 0.094 | 0.063 | 0.156 |
| cluster | 0.067 | 0.066 | 0.094 | 0.064 | 0.176 |
| author | 0.052 | 0.066 | 0.084 | 0.057 | 0.216 |

The conclusion survives: the observed miss is still 2.4 to 3.8 times the floor, so most of it is real. But the
report's "about 0.05" should be "about 0.06, and that is still a lower bound", and `noise_check.py`'s docstring
already admits it ignores the repeats' noise without acting on it.

Fix: add the retrospective-repeat term to `noise_check.py` (the per-repeat RMSEs are in `data/fits`), update the
verdict bullet and the Results section, and relabel overclaim row 17.

### 2. (Moderate) The H2 and H3 bars were close to unachievable, and the report presents their failure as a finding about splitters

Evidence: finding 1; `primary.json` H3. H2 asks the 95% upper bound of the median absolute bias to be at or below
0.12 while the measurement floor is about 0.06 and the bound is estimated over 250 targets; only a splitter whose
true per-target miss was near zero could pass. H3 asks the document splitter's mean τ to reach 0.8 with five model
families, where τ moves in steps of 0.2 per target; the Refuted branch fires whenever the upper bound falls below
0.8, which it does by a wide margin (0.42). Both verdicts follow the preregistered rules and I would not change
them, but a reader is told "document splits are not nearly unbiased" and "no split recovers the ranking" without
being told how demanding the bars were.

Fix: state both bars against the achievable floor in the verdict; keep the verdicts.

### 3. (Confirmatory, strengthens H3) The five model families are not near-tied, so τ ≈ 0.4 is real ranking instability

Evidence: `checks1.txt` §6. The brief asks whether τ ≈ 0.4 is noise among equivalent models. It is not: the
per-target spread of prospective RMSE across the five families has a median of 0.49 log units, and the MLP is
clearly worse than the rest (median prospective RMSE 1.41 against 1.04–1.09). Models that differ this much are
still ranked only loosely by any retrospective split, which makes H3's conclusion stronger than the report claims,
not weaker.

Fix: add the model-spread numbers to the H3 bullet.

### 4. (Minor) Two reported quantities are artefacts of how a splitter was run

- **Time splitter coverage.** `primary.json` gives `share_covering_truth` 0.0 for the time split against 0.40–0.57
  for the other group splits. The time splitter has one repeat (`run.py:181`), so its min and max are the same
  number and the interval has zero width; the 0.0 says nothing about the splitter. The report does not quote it,
  but the figure and table should not either.
- **Test fractions differ.** Random and time splits take exactly 20% of compounds; the group splitters average
  15.7% (scaffold) to 18.2% (author), because `group_split` accepts any draw in 15–25% (`run.py:93-109`). Group
  splits therefore train on 2–4% more data than random splits, which slightly flatters them in the comparison that
  H1 rests on. The effect is far too small to move H1 (−0.37 and −0.27), but it should be stated.

### 5. (Confirmatory) The strict prospective set is effectively leak-free at the InChIKey level

Evidence: `checks2.txt`. The brief's concern is that a salt, stereoisomer or tautomer of a training compound has a
new full standard InChIKey but the same first (skeleton) block. Of 49,657 primary prospective compound-target rows,
0.86% have a skeleton block that already exists in ChEMBL 33 (310 distinct compounds); the worst target reaches
10% and no target exceeds 20%. The share does not correlate with prospective RMSE (r = 0.03). The median
nearest-neighbour similarity of prospective compounds to training is 0.429, below every splitter's test set. The
strict definition does what it claims.

### 6. (Moderate) The G4 delta audit cannot detect the failure it is meant to detect

Evidence: `code/select.py:76-88`; `delta_audit.csv`. The plan says 60 new activities are classified "by inspecting
their document records". The code classifies them by reading `doc_year`: 2023 or later, otherwise older, unless the
same (target, compound, value, document) already exists in release 33. So the audit's 43-of-60 "older publication
newly curated" is a tabulation of the field whose trustworthiness is the question. If a document's year were the
journal year while the measurement was deposited much later, or a 2023+ patent re-published old data, this audit
would pass it through. The denominator (60) is judgeable and the sample is seeded, so G4 is present, but it is
weaker than the report implies when it says the audit "is why the 2023+ restriction is needed".

Fix: say the audit is a document-year tabulation; for a real check, inspect a sample of 2023+ documents (titles,
journals, patent families) for data that predate the document.

### 7. (Minor) The lenient sensitivity is too small to carry its sentence

Evidence: `checks1.txt`, `checks3.txt`. The lenient set has 2,882 compound-target rows over 212 targets: a median
of 8 compounds per target, with 81% of targets under 20. An RMSE from 8 points has a standard error near 0.25. The
sentence "on the lenient set, every splitter understates the error" rests on medians of extremely noisy per-target
RMSEs.

Fix: report the lenient set's size per target beside the claim, or drop it to a footnote.

### 8. (Minor) Smaller points

- 425 dropped repeats and 145 infeasible author graphs fall on small targets (the smallest traced target,
  CHEMBL2899, lost every cluster, document and assay repeat); document and cluster still cover 247 of 250 targets,
  so the bias in which targets enter each splitter is slight, but the coverage table should say the drops
  concentrate on small targets.
- There is no `deviations.md`; the report states "Deviations: none", which is consistent, but the file the brief
  expects does not exist.
- `bias_long.csv`'s `nn_sim_median` column carries the prospective similarity on every row, including retrospective
  ones. Nothing in the analysis misuses it (the stratification wants exactly that), and the report's per-splitter
  figures come from `data/fits` as it says, but the column name invites misreading.

## Gate checks

- **G1:** the audit in plan §7 is real; I found no label-correlated field it missed. Target selection uses counts
  only, hyperparameters are fixed, and splitters see release 33 alone.
- **G2:** `coverage.json` covers activities (both releases), targets and fits; no fallbacks; drops reconcile.
- **G3:** `plausibility.md` traces three targets; all three recompute the stored prospective RMSE to four decimals;
  invariants hold.
- **G4:** present with a judgeable denominator, but mechanical (finding 6).
- **G5:** `review/overclaim_check.md` is honest and matches the tables; row 17 needs relabelling after finding 1,
  and rows 13, 18 and 19 should carry the bar-achievability caveat from finding 2.
- **G6:** `python3 -I ../../tools/attribution.py check . --show` → "G6 passed (7 claims)". I spot-checked L1, L2,
  L4, L5 and L7: sources resolve to the right works, and the roles and conditions are accurate (L1 correctly
  flagged as in-house Merck data, L2 as classification only).
- **G7:** the plan says it does not apply. Correct in that there are no human labels; the delta audit is
  deterministic, so blind double labelling is moot, but see finding 6.

## Confirmation pass

Reviewer: Opus 5.5. Model note: this pass was run on Opus 5.5 instead of Fable 5.1 because Fable 5.1's safeguards blocked the first attempt (flagged as a biology task, request req_011CgjagrJqFpXDhpG1AecdV) before it did any work. The first review was by Fable 5.1.

Date: 2026-11-06. Brief: `review/confirmation_prompt.md`. Read: this review, `review/overclaim_check.md`,
`review/reviewer_checks/checks1-3`, `deviations.md` D1, `report.md`, `code/noise_check.py`, `code/posthoc_review.py`,
`results/tables/{primary,noise_check,posthoc_review,selection,coverage}.json`, `delta_audit.csv`, `code/select.py`
(the G4 code). No study file outside `review/` was changed. `code/noise_check.py` and `code/posthoc_review.py` write
into `results/tables/`, so I did not run them. I reimplemented both independently and compared my output with their
stored JSON. All scripts ran with `venv/bin/python -I` (or `python3 -I`), with paths passed as arguments. One
exception: a single `python3 -c` (no `-I`), run from the study root, printed the key names of one fit JSON. The study
root holds no `.py` files, so nothing could have shadowed a module.

### What I checked, and where

| check | backing file |
|---|---|
| Noise floor recomputed: prospective SE, retrospective-repeat SE, combined in quadrature; three definitions of the expected median \|bias\| plus a Monte Carlo; ratios; share within 2 combined SE; achievability of the H2 bar | `reviewer_checks/confirm_noise.py` → `confirm_noise.txt` |
| Model spread with and without the MLP; adjacent gaps; τ over the four non-MLP families; how often the MLP is ranked last; τ between single repeats and against the prospective ranking (noise ceiling); `tau_long.csv` reproduced; test fractions; time-splitter coverage note; dropped repeats vs infeasible author graphs; lenient-set size | `reviewer_checks/confirm_posthoc.py` → `confirm_posthoc.txt` |
| InChIKey skeleton share re-derived from `data/inchikeys_33.parquet` and `data/prospective.parquet`; lenient 2,859 vs 2,882 reconciled | `reviewer_checks/confirm_inchikey.py` → `confirm_inchikey.txt` |
| G5: the 44 overclaim rows matched sentence by sentence against the current report (via the tool's own extractor), plus `tools/overclaim_check.py --verify`; G6: `tools/attribution.py check . --show` | `reviewer_checks/confirm_gates.py` → `confirm_gates.txt` |
| Report text carries every D1 edit; G4 description matches `code/select.py:75-88` | read directly (no script) |

**Noise-floor reconciliation (finding 1).** The two numbers answer slightly different questions.

- **The first review** got 0.057–0.064 as 0.6745 × hypot(median SE_retro, median SE_pros). That combines medians
  taken separately, so it pairs one target's retrospective SE with another target's prospective SE.
- **The study** got 0.065–0.069 as the median over targets of 0.6745 × hypot(SE_retro,i, SE_pros,i). This pairs each
  target's own two SEs, which is the right pairing. But the median of per-target |N(0, s_i²)| medians is not the
  median of the pooled |bias|.
- **The exact quantity** under a pure-noise model, with bias_i ~ N(0, s_i²) independent across targets, is the median
  of the mixture: solve mean_i(2Φ(m/s_i) − 1) = ½. It is 0.065 (document), 0.061 (author), 0.066 (assay) and 0.067
  (cluster). A Monte Carlo gives the same numbers, with a 95% simulation band of about ±0.01.

Both earlier definitions are defensible approximations within 0.005 of the exact value. The study's is closer and
errs high, which is the conservative direction for a "not just noise" claim, so I would keep it. With the exact
value the ratios become 2.35–3.55, against the report's 2.3–3.3, and the conclusion does not change. Every number in
`noise_check.json` reproduces to three decimals: combined-SE medians 0.096–0.102, within-2-SE shares 0.458–0.591,
and the time splitter correctly falls back to its prospective term only.

### Final verdict: publish with edits

H1, H2 and H3 and their numbers stand, and every D1 edit is in the report. Three sentences added in response to the
first review need changing, though. One of them (H3, "real instability, not near-ties") comes from an inference in
the first review's finding 3 that does not survive a closer check. None of the three needs new analysis; the numbers
are in `confirm_*.txt`.

### Status of the original findings

1. **Noise floor: fixed.** `noise_check.py` adds the repeat SE in quadrature. The JSON reproduces exactly, and the
   verdict bullet and the "Is the per-target miss just noise?" section carry the new numbers. The reconciliation is
   above. One trivial slip: the section gives the retrospective SE as 0.067 for document splits; the JSON says 0.068.
2. **Bars: partly fixed.** Both bullets are added and the verdicts are unchanged, but both overstate how demanding
   the bars were.
   - **H2.** I simulated a constant true per-target miss δ of random sign, plus the observed per-target noise of each
     splitter, then bootstrapped as in the plan (`confirm_noise.txt`). A δ of 0.08 passes the 0.12 bar 98% of the
     time, δ = 0.10 passes 30% (document) and 48% (author), and δ = 0.12 never passes. So a splitter's true miss
     could be about half the observed 0.17–0.22 and still pass, not "near zero". That makes the refutation stronger,
     not weaker.
   - **H3.** "τ moves in steps of 0.2 per target" says nothing about a mean over 247 targets. "The upper bound (0.42)
     is far below 0.8" shows the result missed the bar, not that the bar was hard. The real reason the bar was
     demanding is the noise ceiling: two single repeats of the same splitter, within release 33, agree only at mean
     τ 0.40–0.55, while single repeats against the prospective ranking reach 0.30–0.37 (`confirm_posthoc.txt`).
3. **Model spread: partly fixed.** The numbers are right: median spread 0.493, and the MLP's median 1.413 against
   1.043–1.089. `tau_long.csv` reproduces exactly. But the inference added to the H3 bullet does not hold. The 0.49
   spread is driven by the MLP.
   - **The other four families are close.** Their per-target spread has a median of 0.20 (quartiles 0.14–0.31). Their
     adjacent gaps have a median of 0.059, and the smallest gap a median of 0.019, against a prospective RMSE SE of
     0.066.
   - **τ over those four alone is 0.12–0.18** under every splitter.
   - **The MLP is ranked last** retrospectively in 81–98% of targets, and it is in fact worst prospectively in 78%.
   - **So τ ≈ 0.4 is mostly the splits correctly flagging the MLP**, while four near-tied families stay unordered,
     even between repeats of the same split. "This is real instability, not near-ties" and "makes H3's conclusion
     stronger" are not supported. That inference was the first review's error, and the study adopted it as asked.
4. **Artefacts: fixed.** `primary.json` carries `share_covering_truth_note`, and neither the report nor the figure
   captions quote the time splitter's 0.0. The time splitter has one repeat on every target. The median test
   fractions reproduce: scaffold 15.2%, assay 15.9%, document 16.0%, cluster 16.2%, author 17.1%, against 20.0% for
   random and time. "15–17%" is correct, and the report labels this post hoc.
5. **InChIKey skeletons: fixed.** I re-derived the figures independently: 0.86% of 49,657 rows, 310 compounds, a
   maximum of 10% per target, none above 20%, and r = 0.03 with prospective RMSE. The report cites them correctly
   under "Prospective truth".
6. **G4: fixed.** The report now calls the audit a document-year tabulation (`code/select.py`) that cannot detect a
   2023+ document republishing older data. The Gates line repeats this. That matches the code. No sample of 2023+
   documents was inspected; the report does not claim one was, and the residual risk is stated.
7. **Lenient set: fixed.** 212 targets, 2,859 rows, median 8 and 81% under 20 all reproduce. The first review's 2,882
   (from `selection.json`) adds 23 single-compound targets that were never evaluated, so 2,859 is the right
   denominator for the claim.
8. **Smaller points: partly fixed.** `deviations.md` now exists, and `nn_sim_median` is documented there. But the
   report sentence "The 13 targets with dropped repeats or infeasible author graphs have a median of 196 compounds,
   against 789 for the rest" is wrong in scope.
   - **The 13 targets are dropped repeats only,** because `posthoc_review.py` counts notes starting with "dropped".
   - **29 targets have infeasible author graphs, and they are larger:** median 1,152 compounds against 730.
   - **38 targets are affected in all,** with a median of 481 against 759.
   - `deviations.md` D1 states the dropped-repeats figure correctly. The author splitter's 38 missing targets are
     therefore mostly large targets, not small ones.

**Gates.** G5 holds: 44 rows, all 44 match the current report's extracted sentences in order, none are stale, and
`--verify` passes. Rows 19, 25, 26 and 27 are labelled Supported but carry the overstatements in findings 2 and 3, so
they need relabelling with the edits below. G6 holds: "G6 passed (7 claims)", and all seven source ids resolve to the
cited works.

### Remaining issues

- **(Moderate) H3 bullet, "This is real instability, not near-ties ... makes H3's conclusion stronger".**
  - Replace it with: τ ≈ 0.4 mostly reflects every split correctly ranking the MLP last (81–98% of targets). The
    other four families sit within a median 0.20 of each other, and no split orders them (τ 0.12–0.18).
  - Replace "steps of 0.2" in "This bar was demanding too" with the noise ceiling: two single repeats of the same
    split agree at only τ 0.40–0.55, against 0.30–0.37 for a single repeat against the future.
  - Relabel overclaim rows 25–27.
- **(Minor) H2 bullet, "only a splitter whose true per-target miss was near zero could pass".** Change it to say that
  a true per-target miss of up to about 0.08 would pass, roughly half the observed 0.17–0.22. Relabel overclaim row 19.
- **(Minor) "What this does and does not show", dropped-repeats sentence.** Restrict it to the 13 targets with dropped
  repeats (median 196 against 789). Add that the 29 infeasible author graphs fall on larger targets (median 1,152
  against 730), so author splits miss mostly large targets.
- **(Trivial, optional)** Retrospective SE for document splits: 0.068, not 0.067.
