# Deviations and implementation details

The plan (plan.md) was committed in ff1996a at 2026-10-04 12:32 NZDT. Entries are timestamped with `date`.

## D1. Validation results and attack A2 precision (2026-10-04 16:01 NZDT)

**A1 validation gate: passed.** The P9 reproduction with the published unswapping parameters recovered the published
P9 peak exactly, in 6,267 s (the limit was 3x 2,722 s = 8,166 s), with 1.8 GB peak GPU memory
(results/P9_A1_mb8192_c0.002_s123.json).

**A2 precision.** Run in complex64 as in the authors' notebook, distillation on P9 crashed with NaN sampling
probabilities. It is now run in complex128.

**A2 on P9 (chi 256, 1,000 samples, 4,930 s).** The voted string is 30 of 56 bits away from the published P9 peak,
which is chance level. Bit-marginal distillation does not work on these permuted (Hqap) circuits. On P11 it is
therefore run once, at chi 256, only after A1 has finished, so that it does not slow A1. It cannot outrank an A1
candidate under the plan's ordering.
