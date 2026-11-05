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
