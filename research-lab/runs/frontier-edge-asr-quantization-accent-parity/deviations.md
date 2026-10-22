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

## D2 — 2026-10-22 19:14 NZDT — H4 follows the same positive-control fallback (before any Whisper-large-v3 decoding)

The plan states H4 as "the same rules on Whisper-large-v3, with GPTQ-W4 under US-only, balanced and worst-weighted
calibration, three seeds each, plus FP16 and RTN-W4". It does not say whether the positive-control fallback of
section 5 (written for H1–H3) applies. It is applied: if the large-v3 GPTQ-W4 US-only penalty has a lower 95% bound at
or below 0, H4 is tested at W3 with the same three compositions and seeds (`code/run_large.sh`). The large-v3
worst-weighted sets use large-v3's own FP16 validation WER, as the plan says. Mixed precision is not part of H4.

## D3 — 2026-10-22 22:00 NZDT — Whisper-large-v3 batch sizes (before any large-v3 output)

The first large-v3 decode, FP16 on the test split, ran out of GPU memory at batch 16. Only about 8.6 GiB is free next
to the co-tenant vLLM server, and large-v3's self- and cross-attention caches grow with the batch. Large-v3 now
decodes short segments in batches of 4 and long-form segments one at a time. Greedy decoding with identical settings
can still differ slightly with batch composition. So every large-v3 condition uses these same sizes, and no large-v3
result is compared with a Whisper-small one except through the per-model penalties. No large-v3 hypothesis was
written, and the pipeline was stopped and restarted from the beginning.
