# Deviations log: citation-context replication deep dive

Every departure from `plan.md`, with a timestamp (NZDT) taken from `date`. Newest last.

### D1. Preregistration (2026-10-01 05:37:01)
`plan.md` committed as ee5c166, before any citation context was collected or scored.

### D2. Specification details fixed before any outcome was joined (2026-10-01 05:56:40)
- **Discipline groups.** They come from the OpenAlex primary-topic field of the original.
  - Psychology: Psychology and Neuroscience.
  - Economics and business: Economics, Econometrics and Finance; Business, Management and Accounting; Decision
    Sciences.
  - Other: everything else.
  - The FLoRA journal field was not needed.
- **Citing-paper years.** A citing paper enters the pre-replication window if year_o ≤ year < first replication year.
- **Negative count per 100** uses all citing papers in the window, with or without contexts, as the denominator.
- **H3 original statistics.** In the FReD subset, n = the median `n_o` over the original's effects. The p-value
  category comes from the median `pval_value_o`; "not reported" if missing.
- **Cross-validation inside bootstrap resamples.** It uses grouped stratified folds, so that duplicated originals stay
  in one fold.
- **SciBERT training.** It ran to the plan's settings. CC30k held-out test: NEGATIVE F1 0.909, macro F1 0.840
  (`results/tables/c1_cc30k_test.csv`).

### D3. Scope of the LLM classifier (C2), and harvest pacing (2026-10-01 06:04:01)
**The problem.** The harvest yields far more contexts than expected: 220,805 from the first 552 originals, so about
850,000 in total. Scoring all of them with the shared local LLM would take about 9 hours of server time. The plan
(§3) said C2 would be "scored on each context".

**The change, made before any outcome was joined:**
- **Validation pool first.** C2 first scores a pool of 20,000 random contexts: 15,000 from pre-replication citing papers
  and 5,000 from post-replication ones (seed 5). The §3 validation sample is drawn from this pool.
- **Analysis contexts only if C2 wins.** If C2 becomes the primary classifier, it scores capped analysis contexts: up
  to 100 random pre-replication and 50 random post-replication citing papers per original, seeded per original.
  C1 is then also analysed with the same caps, for a like-for-like comparison.
- **C1 is unaffected.** It scores every context on the GPU.

**Harvest.**
- **Throttling.** Three parallel workers at 1.1 s spacing were throttled (HTTP 429). A bug would have saved
  throttled originals as empty. It was fixed before any such file was written: no saved file has a 429 status, and
  throttled originals are retried.
- **Pacing.** The harvest now runs with two workers (one in reverse order) at 3 s spacing.

### D4. Classifier validation: neither classifier meets the bar (2026-10-01 08:09:44)
Plan §3 procedure, run before any outcome was joined.

- **Pool.** C2 scored its 19,978-context pool: 703 Negative, 221 Positive.
- **Sample.** 300 contexts drawn: 150 that either classifier calls Negative, 150 others; seeds 21 and 22.
- **Labels.** Assigned blind by the analyst (text only, shuffled) and saved at 08:08:53. SHA1 de6de772...; 9 Negative,
  16 Positive, 275 Neutral.
- **Scores** (NEGATIVE vs rest; `results/tables/validation_metrics.csv`):

  | Classifier | F1 | Precision | Recall |
  |---|---|---|---|
  | C1, SciBERT on CC30k | 0.115 | 0.061 | 1.00 |
  | C2, local LLM | 0.300 | 0.273 | 0.333 |

  - C1 calls Negative 148 of the 300, and 44% of all 787,384 harvested contexts.
  - CC30k's "Negative" class covers contrastive and limitation language ("however, X cannot be applied"), which is
    common in any literature. The CC30k test F1 of 0.91 does not transfer to this task.
  - True reproducibility doubt is rare: 6% of the "either negative" stratum and none of the "other" stratum, about
    2.6% of pool contexts.

**Consequence (plan §3 rule).** Neither classifier reaches F1 0.5. Both are reported, and the study is labelled as
limited by measurement.
- C2 now scores its capped analysis contexts (D3): 255,969 contexts for 1,912 originals, about 2.7 hours at 8
  concurrent requests on the shared server.
- C1 is analysed on all contexts and with the same caps.

### D5. Exploratory keyword detectors (2026-10-01 08:15:38)
SciBERT gave H1 AUC 0.482 [0.448, 0.516] and a failed positive control: V1 post-replication AUC 0.495
[0.459, 0.529]. By plan §5, a failed V1 makes its H1 null uninformative. Its validation had already shown it measures
contrastive language, not reproducibility doubt.

As an exploratory complement (not preregistered), two transparent regular-expression detectors were written, and their
exact patterns fixed in `code/explore_keywords.py` at this timestamp, before being run against any outcome:
- **K1:** explicit replication-failure language;
- **K2:** K1 plus general doubt language.

They are evaluated with the plan's H1 and V1 definitions, plus "any flagged citing paper". The C2 analysis continues
as preregistered.

### D6. Results (2026-10-01 10:32:31)
C1 was run at 08:10-08:15 and C2 at 10:22-10:32, once C2's capped scoring had finished: 255,969 contexts, of which
11,116 Negative and 3,063 Positive. `results/tables/results_{c1,c2,c1_capped}.csv`.

| Analysis | C1, SciBERT | C2, LLM |
|---|---|---|
| H1 AUC | 0.482 [0.448, 0.516] | 0.506 [0.473, 0.540] |
| V1 positive control | 0.495 [0.459, 0.529], fails | 0.546 [0.514, 0.581], passes weakly |
| H2 delta AUC | +0.002 [-0.015, +0.023] | -0.006 [-0.018, +0.012] |
| H3 delta AUC (330 originals) | +0.000 [-0.021, +0.027] | -0.004 [-0.023, +0.022] |

- Verdicts: H1, H2 and H3 contradicted for both classifiers, which is qualified by D4 (limited by measurement).
- C1 with C2's caps: H1 0.485, V1 0.493, H2 +0.001, H3 -0.001.
- Exploratory keywords (D5):
  - K1: before replication 0.535 [0.517, 0.554], after replication 0.628 [0.605, 0.650], incremental +0.016
    [-0.004, +0.040];
  - any K1 flag before replication: 14.3% of failed originals against 7.4% of successful ones.
- Event study (`eventstudy_k1.csv`, exploratory): K1 citing-paper rate
  - 0.2-0.5% in the six years before a recorded failure, against 0.05-0.16% for successes;
  - 1.6% in the replication year.
- A caption drafted before the event-study numbers were read ("separate only after") was wrong and was corrected
  to the data before publication.

### D7. Independent review and corrections (2026-10-01, logged 11:14:01)
A separate reviewer agent (Fable 5.1), given the plan, log, code, data and draft, returned FIX FIRST. It reproduced
the headline numbers, the outcome construction, the windows, the caps and the grouped cross-validation.

**Corrections:**

1. **The positive control was on a different sample from H1.** V1 was computed over all originals with at least 5
   post-replication citing papers, not over the primary sample.
   - It is now computed on the primary originals with at least 5 post citing papers (851); the all-originals version is
     kept for reference.
   - On the matched sample C2's control fails: 0.529 [0.491, 0.567]. The draft's "passes weakly" is withdrawn.
2. **Verdicts now follow plan §5.** A failed positive control makes a null H1 uninformative. For both classifiers,
   H1-H3 are now "uninformative (positive control failed)"; the mechanical "contradicted" is kept only in brackets.
3. **Replication papers leaked into the pre-replication window.**
   - 71 FLoRA replication papers fell in their own original's pre window, mostly dated a year early by an online-first
     date.
   - Every citing paper whose DOI matches a FLoRA or FReD replication DOI is now excluded, in all analyses and the
     event study (`analysis.replication_dois`; citing DOIs added to `build_contexts.py`).
   - The primary sample is now 1,075 originals.
4. **The event study was paper-weighted.**
   - One FLoRA "original" (Camerer et al. 2018, itself a replication-project paper) supplied many generic
     "findings often fail to replicate" contexts.
   - The event study is now original-weighted, with replication papers excluded. It shows a higher but flat
     pre-replication level for failed findings, not a rising trend. The draft's "creeping up" wording is withdrawn.
5. **Validation uncertainty is now reported.** Bootstrap within strata:
   - C1 F1 0.115 [0.052, 0.184];
   - C2 F1 0.300 [0.000, 0.556], P(F1 >= 0.5) = 0.07; only 11 C2-flagged contexts reached the sample, because C1
     dominates the "either negative" stratum;
   - prevalence of doubt 2.6% [1.4%, 6.2%] of pool contexts (pool: 75% pre-, 25% post-window contexts of eligible
     originals).

   The reviewer re-examined about 90 contexts (all 25 non-neutral, and flagged and random others) and agreed on about
   95%. It judged v078 and v130 borderline Neutral and v264 a borderline miss. Multi-citation contexts are ambiguous
   because the target citation is not marked.
6. **Harvest truncation.** The six most-cited originals stopped at 9,000 citing papers, because offset + limit may not
   exceed 10,000, and newest-first ordering drops the oldest citers. Four are in the primary sample. Excluding them
   changes nothing (C1 0.479, C2 0.507).
7. **Counts corrected:**
   - FReD covers 520 of the 2,116 originals;
   - 815,570 citing papers after de-duplication;
   - the validation pool is 20,000 contexts (19,978 distinct texts);
   - "mixed" first-replication outcomes: 483 originals, excluded from the primary analysis;
   - the validation draw also required 20-1,500-character contexts, which the plan did not state.
8. **Sensitivity added.** Excluding OpenAlex-sourced FLoRA entries (C1 0.470, C2 0.509).
9. **K1 provenance.** The file's modification time (08:16:42) is after the D5 stamp, because the analysis section was
   extended then. The regular expressions were not changed after D5. About 10% of K1 matches are generic crisis
   statements or "not yet replicated".

**Corrected results.**

| Analysis | C1 | C2 | K1 (exploratory) |
|---|---|---|---|
| H1 | 0.480 [0.445, 0.514] | 0.507 [0.472, 0.543] | 0.534 [0.515, 0.553] |
| V1, matched sample | 0.497, fails | 0.529, fails | 0.625 [0.598, 0.650], passes |
| H2 delta AUC | +0.004 | -0.006 | +0.014 [-0.006, +0.031] |
| H3 delta AUC | 0.000 | -0.004 | |

K1 also gives:
- window ending 2 years before replication: 0.525 [0.506, 0.544];
- any K1 flag before replication: 13.9% of failed originals against 7.3% of successful ones.
