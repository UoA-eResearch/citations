# Deviations

## D1 — 2026-10-22 17:00 NZDT — the W4 positive control fails; the preregistered W3 fallback, and mixed precision at W3

With all six GPTQ-W4 conditions for Whisper-small decoded (US-only and balanced calibration, three seeds each), the
positive control fails. The penalty under US-only calibration is −2.7 points (95% interval −8.9 to +2.6): 4-bit GPTQ
raises aggregate WER by about 1.5 points but does not widen the pooled worst-versus-best accent gap. As the plan
specifies (section 5), H1–H3 are therefore tested at W3 g128 with the same design, and W4 is reported as showing no
measurable penalty. The W4 conditions already queued (worst-weighted, mixed precision, AWQ-style) are still decoded and
reported as secondaries.

The plan defines mixed precision only around W4 (promote to W8, demote to W3). For the W3 fallback the same rule is
applied one step down, fixed here before any W3 condition is decoded:
- layers are ranked by the accent-differential relative output error of RTN weights at the base precision (W3);
- the highest-scoring layers are promoted to W8 until they cover at least 5% of quantizable weights;
- the lowest-scoring layers are demoted to W2 until total bits match uniform W3 within 1%.

The code is generalised for this (`quant.mixed_allocation` base/hi/lo, `mp_alloc.py MODEL 3`, conditions
`mp3_<comp>_s<seed>`, `score.py` H3_w3). The W4 allocation and its conditions are unchanged.
