# Review: cheminformatics-drug-discovery-pcba-2026

Reviewer: independent adversarial review, 2026-11-05. Scripts and outputs in `review/reviewer_checks/`
(`checks1.txt`). Checks used `venv/bin/python -I` with the study's own `analyse` module on the stored score files;
no model was refitted.

## Verdict: publish with edits

The construction is careful and honest, and the arithmetic holds: every entry in the splits table reproduces from
`metrics.csv`, H1's Q (0.43 from 1.358 / 3.15) and its interval, H2's 0 of 56 and 9 of 56 with medians −1.00 and
−0.56, H3's mean τ of 0.196, the retained shares (12% of LIT, 40% of PCBA-2026 by target median), the coverage
funnel and the deviation timings (every score file was written between 03:31 and 08:34 on 28 October, after D2 at
21:51 and D3 at 00:57). The deviations are exemplary: three implementation errors, including a subsampling rule
that would have wrecked the comparison, were caught by checks and fixed before any score existed.

Two things need changing. The H3 caveat, which the report presents as deflating its own result, is backwards: on
the comparable measurement the within-target replication is clearly better than the cross-benchmark agreement, so
the ranking disagreement is real rather than noise. And the memorization baseline never beats the random forest in
any arm of this study, which contradicts the premise the benchmark was built to address and is not stated.

## Findings

### 1. (Major) The split-half noise ceiling is not comparable to the H3 statistic, and the comparable version reverses the report's reading

Evidence: `checks1.txt` §E; `code/analyse.py:153-171`. The reported ceiling (0.287) is the mean τ between method
rankings on two random halves of a target's evaluation set. The H3 statistic is the τ between a target's full-set
ranking and the LIT consensus, which is a median over 15 LIT targets and therefore far more stable than a half-set
ranking. The ceiling thus carries two noisy rankings where the statistic carries one, and it is estimated from a
single permutation per target. Recomputing with five permutations per target:

| quantity | mean τ |
|---|---|
| full set against the LIT consensus (the H3 statistic) | 0.196 |
| **half set against the LIT consensus** (one noisy ranking, like the statistic) | **0.183** |
| half against half (the reported ceiling) | 0.336 |

Halving a target's data moves its agreement with LIT by 0.013, from 0.196 to 0.183, so the cross-benchmark figure
is not noise-limited. Meanwhile two halves of the same target agree with each other at 0.336, well above the 0.196
they each achieve against LIT. Within-target replication exceeding cross-benchmark agreement is the signature of a
genuine difference between benchmarks, not of measurement noise. The report's sentence that "most of the
disagreement is measurement noise rather than a real difference between benchmarks", and the subtitle "Supported,
but for a duller reason than it sounds", understate the study's own result.

Fix: replace the ceiling with the half-set-against-consensus figure (or report both, labelled), average over
several permutations, and rewrite the H3 bullet to say that rankings replicate within a target better than they
transfer between benchmarks.

### 2. (Moderate) The memorization baseline never beats ECFP4 + random forest, which the report does not say

Evidence: `checks1.txt` §A. Across all seven benchmark × split arms the memorization baseline's median EF1% is
below the random forest's, by 2.35 to 11.13 units:

| benchmark and split | memorization | ECFP4 + RF | difference |
|---|---|---|---|
| PCBA-2026 random | 11.43 | 20.27 | −8.84 |
| PCBA-2026 analog-disjoint 0.4 | 2.36 | 5.65 | −3.29 |
| LIT-PCBA random | 27.83 | 37.29 | −9.46 |
| LIT-PCBA analog-disjoint 0.4 | 3.46 | 8.04 | −4.58 |
| LIT-PCBA as published | 4.15 | 6.50 | −2.35 |

The audit paper this study responds to reports that a parameter-free memorization baseline matches published state
of the art. In this study's hands it does not match even a plain fingerprint random forest, on either benchmark,
under any split. That is a substantive, publishable negative result about the premise, and the report passes over
it. Relatedly, "memorization's advantage" in the title and verdict means its advantage over a random scorer, as the
plan defines A_B; a reader will take it to mean an advantage over other methods, which never existed here.

The directional claim itself holds up: the memorization baseline does collapse hardest when near-twins are removed
(a factor of 4.9 on PCBA-2026 and 8.0 on LIT, against 3.6 and 4.6 for the random forest), so the within-benchmark
contrast is doing real work even though the audit removes, by construction, the compounds that baseline scores on.

Fix: state the comparison with the random forest in the verdict; reword "advantage" to "enrichment over random".

### 3. (Moderate) H2's conclusion is broader than what was tested, and most pairs are simply inconclusive

Evidence: `checks1.txt` §D; `plan.md` §4. The embeddings are frozen, mean-pooled last-hidden-layer
representations with a logistic-regression head. That is one use of a pretrained model and a weak one; no
fine-tuning, no pooling alternative, no task-specific head. The verdict bullet reads "pretrained molecular
embeddings do not beat ECFP4 + random forest", and "Not shown" covers tuned models only in the sense of
hyperparameters. Separately, S2 = 1.0 because no embedding's paired interval excludes zero in its favour, but the
random forest's does so on only 9 of 56 pairs, so 47 pairs are inconclusive in both directions; the plan
anticipated this and reporting the 9 alongside is the right design. The median ΔEF1% of −1.00 (ChemBERTa) and
−0.56 (MoLFormer) carries the direction, not the interval count.

Fix: scope the claim to frozen mean-pooled embeddings with a linear head, in the verdict and the title; add
fine-tuning to "Not shown".

### 4. (Minor) The leakage-audit shares are per-target medians, and the audit shifts which compounds survive

Evidence: `checks1.txt` §C. Retained at the 0.4 threshold: PCBA-2026 39.5% of compounds by target median but 19.6%
pooled over all rows; LIT 11.7% median and 12.1% pooled. The report's "62% have a training neighbour" and "40%
scorable" are the median figures, presented as overall shares; pooled, the audit removes about 80% of PCBA-2026's
evaluation rows. The audit also retains actives at a higher rate (45.7%) than compounds overall (39.5%), so the
median hit rate rises from 2.4% to 3.2% and the EF1% ceiling falls correspondingly. Neither point changes a
verdict, but the brief asks whether the audit biases which actives survive, and it does, measurably.

Fix: label the aggregation and give the pooled figure; add the post-audit hit rate and ceiling shift.

### 5. (Minor) D2's commitment to report the restricted subset is only half kept

Evidence: `report.md` process section; `primary.json` `posthoc_hit_rate_le_5pct`. D2 undertook to report the same
statistics for the 19 targets at or below a 5% hit rate, and to lead with any disagreement. The report mentions the
subset exists but gives none of its numbers. They are in `primary.json`: Q = 0.84 (−3.60 to 8.02, still
Inconclusive) and mean τ = 0.139 (−0.004 to 0.283, still Supported). The verdicts agree, so there is nothing to
lead with, but the numbers should appear.

### 6. (Confirmatory) Checks that passed

- Every value in the splits table, H1's A_new 1.358 and A_lit 3.15, H2's counts and medians, H3's 0.196 and its
  interval, the LIT retained share of 12%, the substance funnel (1,769,491 in, 1,574,697 kept), and the assay
  funnel (32 candidates, 28 kept with per-assay reasons).
- Timing: plan 19:43 before any outcome; D2 21:51 and D3 00:57 both before the earliest score file (03:31 next
  morning), so the hit-rate and cap decisions could not have been informed by a fitted result.
- The subsample cap: the reported check covers the three largest targets; the rule preserves the hit rate exactly
  by construction for targets above the 150-active floor, which is the property EF1%'s ceiling depends on.

## Gate checks

- **G1:** the audit in plan §5 is real. Folds come from structure clusters, the 0.4 removal is by similarity and
  never by label, and hyperparameters are fixed in advance. The contamination caveat for the pretrained models is
  stated and the 2023+ subset is tracked. I found no label-correlated field it missed.
- **G2:** `coverage.json` covers assays, substances, LIT compounds and scored targets (58 = 28 + 15 + 15); no
  fallbacks; drops reasoned.
- **G3:** `plausibility.md` traces three targets and checks the invariants, including a random scorer at EF1% = 1
  and the post-audit memorization values sitting near it.
- **G4:** the leakage audit has judgeable denominators per target, and the realised similarity distributions are
  reported.
- **G5:** `review/overclaim_check.md` is present with 32 labelled rows; the H3 rows and the title row need
  relabelling after findings 1 and 2.
- **G6:** `python3 -I ../../tools/attribution.py check . --show` → "G6 passed (9 claims)". Titles, not just
  resolution, were checked: the MoLFormer and PubChem rows resolve to the right papers, and the deviations record
  that an earlier MF-PCBA identifier resolved to an unrelated paper and was corrected, with its year fixed against
  the lead's statement. This is the failure mode the brief warns about, caught by the gate.
- **G7:** does not apply; no human or agent labels. Confirmed.
