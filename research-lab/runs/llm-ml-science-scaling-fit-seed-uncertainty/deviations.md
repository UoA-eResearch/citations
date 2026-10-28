# Deviations from the preregistration

## D1 — 2026-10-24 07:55 NZDT — evaluation precision (found in the first loss table, before any fit)

**The problem.** The plan evaluated in bf16, with logits in fp32. The first full loss table (`losses_bf16.csv`)
showed losses that rise late in training for most small-model seeds, and for the original Pythia-70M and -160M. That
contradicts their published curves. bf16 is the problem. Late Pythia checkpoints have large activations, and bf16's
8-bit mantissa corrupts them (the models were trained in fp16):

| checkpoint (200 eval sequences) | bf16 | fp16 | fp32 |
|---|---|---|---|
| pythia-70m, step143000 | 4.51 | 3.01 | 2.98 |
| pythia-160m, step143000 | 3.06 | 2.62 | 2.62 |
| pythia-14m-seed6, step143000 | 8.25 | 3.81 | 3.68 |
| pythia-70m, step32000 | 2.96 | 2.95 | 2.95 |

*(Note added 2026-10-28, after the independent review: the table is a 200-sequence subset, whose losses sit about
0.3 above the full corpus. Full-corpus bf16 / fp32 values for the same checkpoints are 4.12 / 2.63, 2.71 / 2.30,
7.95 / 3.32 and 2.61 / 2.61, from `losses_bf16.csv` and `losses.csv`.)*

**The fix.** Every ladder checkpoint, and the 1B and 1.4B targets, are re-evaluated in fp32.
- **Pythia-2.8B** does not fit in fp32 beside the shared vLLM server, so it is evaluated in fp16.
- **The fp16 bias** is measured by evaluating 1B and 1.4B in fp16 as well.
- **What the 2.8B loss affects.** Only secondary 1, extrapolation accuracy. H1 and H2 use only its N.

The bf16 table is kept for the record. No fit had been run.

## D2 — 2026-10-25 01:36 NZDT — batch sizes, and post hoc checks after the fits

1. **Batch sizes.** At 16:39 on 2026-10-24 the fp32 run entered an out-of-memory loop at 410M, because the shared
   server had taken more GPU memory. It was restarted with batch 2 at 410M and batch 1 at 1B–2.8B. Batch size does
   not change a sequence's loss: the 410M seed-4 final checkpoint, first evaluated at batch 4, gives 2.406874 at
   batch 1 too (spike_check.csv).
   - *Timing (noted 2026-10-28, after the review):* the change was made at 16:40 on 2026-10-24 but recorded here
     only at 01:36 on 2026-10-25, after the fits. The plan (section 6) asks for deviations to be recorded when
     made. It does not affect any number.
2. **Post hoc checks, after primary.json** (not preregistered):
   - **Neighbouring checkpoints** (`code/spike_check.py`). These test whether the late jumps of 410M seeds 3 and 4
     (and the late rises of small models) are evaluation artefacts. They are not: 410M seed 4 is 2.43 / 2.42 / 2.41
     at steps 141k / 142k / 143k; seed 3 is 2.18 / 2.17 / 2.17 at 99k / 100k / 101k; seed 0 is 1.98 at 142k.
   - **Robustness** (`code/posthoc.py`): W₁ without the ladders that use those two runs, and fresh fits on
     ladders cut at step 64k.

   Neither changes a preregistered verdict, and both are labelled post hoc in the report.

## Pre-review gate (G5, G6) — 2026-10-25 22:53 NZDT, after all results (wording and attribution only)

The lab's METHODS.md gates were run before this draft's review. No number changed.
- **G5 overclaim check** (`review/overclaim_check.md`, passes):
  - the title's "three seeds barely help" became "did not clearly help", since H2 is Inconclusive with a shrinkage
    interval reaching 0.81;
  - the plain-terms sentence drops the unsourced "a common suggestion" and states the uncertainty.
- **G6 attribution ledger** (`results/attribution_ledger.csv`, 6 claims, passes): PolyPythias, the Hitchhiker's
  Guide, the Chinchilla replication and Porian et al. resolve by arXiv id with matching titles.

## D3 — 2026-10-28 06:39 NZDT (recorded 17:06) — N corrected after the independent review (fix first); all fits re-run

1. **What was wrong.** plan.md preregisters N as non-embedding parameters. `evaluate.py` kept every parameter whose
   name lacks "embed". In the installed transformers the GPT-NeoX output head is named `lm_head`, so N included one
   50,304 × d matrix: 6.4 times the preregistered count at 14M and 1.05 times at 2.8B.
2. **The fix.**
   - `code/fix_n.py` recomputes N from each model's config as L(12d² + 13d) + 2d. It checked that the old N equals
     this plus the head, and rewrote `losses.csv`'s N column; the head-inclusive and total counts are kept as
     columns.
   - `evaluate.py` now excludes `lm_head` and `embed_out` by name, and the v1 tables are kept in
     `results/tables/v1_pre_review/`.
   - `fit.py` (with the seed bootstrap and the procedure decomposition), `posthoc.py` and `figures.py` were re-run
     unchanged (06:39–17:04).
3. **Post hoc, after the review:**
   - `code/sensitivity_total_n.py`: the same 2,000 single-seed ladders with N = total parameters (the Chinchilla
     convention), since the extrapolation bias depends on the convention;
   - `code/posthoc_review.py`: the variance share by seed, the overshoot share, E's percentiles, paired evaluation
     noise and late rises.
4. **The results' verdicts did not change.** H1 and H2 stay Inconclusive. W₁ 0.123 → 0.103, shrinkage 0.16 → 0.10,
   α median 0.25 → 0.10, median extrapolation error +0.068 → +0.061. Under total N the error is +0.017, with 67% of
   forecasts overshooting.
