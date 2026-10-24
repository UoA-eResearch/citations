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
2. **Post hoc checks, after primary.json** (not preregistered):
   - **Neighbouring checkpoints** (`code/spike_check.py`). These test whether the late jumps of 410M seeds 3 and 4
     (and the late rises of small models) are evaluation artefacts. They are not: 410M seed 4 is 2.43 / 2.42 / 2.41
     at steps 141k / 142k / 143k; seed 3 is 2.18 / 2.17 / 2.17 at 99k / 100k / 101k; seed 0 is 1.98 at 142k.
   - **Robustness** (`code/posthoc.py`): W₁ without the ladders that use those two runs, and fresh fits on
     ladders cut at step 64k.

   Neither changes a preregistered verdict, and both are labelled post hoc in the report.
