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

## D4 — 2026-10-23 16:40 NZDT — robustness analyses after the independent review (review/review.md, "fix first"), before they are run

The review found that a few runaway repetition loops dominate the preregistered statistics. These are hypotheses that
run to the 440-token cap because the plan disables Whisper's fallbacks. The review also found that the H2 interval
leaves out calibration-draw variance. The preregistered statistics, rules and verdicts are unchanged. The following
analyses are added (`code/robustness.py`, written to `results/tables/robustness_<model>.json`), all post hoc:

1. **Scoring variants:**
   - errors capped at each utterance's reference length;
   - utterances looped in any condition removed;
   - substitutions and deletions only;
   - short-form and long-form segments separately.

   In each, the worst-3 and best-3 groups are re-fixed from FP16 on that variant's data, as the plan fixes them, and the
   preregistered groups held fixed are reported too.
2. **A draw-aware bootstrap.** The three calibration draws of each composition are resampled along with speakers.
3. **Literal re-ranked gap penalties,** a secondary the plan names that the report omitted.
4. **A split-half estimate** of the bias from choosing the six groups on the same FP16 data.
5. **Per-utterance drivers** of each condition's change in the six groups, as identifiers and counts only.

The same analyses run on Whisper-large-v3 once its W3 conditions finish.

**R and seed R.** `score.py` now leaves R and seed R null when the positive control fails or the reference penalty
is not positive; earlier it wrote values such as 2.04 and −1.95. The decision logic is unchanged.

**Common Voice replication.** Plan section 5 triggers it when H1, H2 or H3 is Supported. H2 is Supported by the
rule (fragile), so it is triggered. Whether it can be run is checked separately and reported. Common Voice 17.0
distribution moved to the Mozilla Data Collective in 2025.

## D5 — 2026-10-23 16:42 NZDT — the Common Voice replication protocol, fixed before any Common Voice audio is decoded

Plan section 5 triggers the replication because H2 is Supported by the rule, but the plan gives no details. They are
fixed here.

- **Source.**
  - Common Voice 17.0 English is used, test and dev splits.
  - The official Hugging Face repository was emptied in October 2025, when Mozilla moved distribution to the Mozilla
    Data Collective, which needs an account. So the transcripts and audio come from the public CC0 mirror
    `fsicoli/common_voice_17_0`: `transcript/en/{test,dev}.tsv` and `audio/en/{test,dev}/en_*_0.tar`.
  - SHA-256 of all four files is recorded in `results/tables/cv_manifest_counts.json`.
- **Accent groups.**
  - The `accents` field is split on commas outside parentheses. Only clips with exactly one label are kept.
  - A label with at least 30 such clips across test and dev is a named group, and other single-label clips form
    "other". Counts from the transcripts alone give 10 named groups: United States, India and South Asia, England,
    Canada, Australia, Southern Africa, Ireland, Hong Kong, New Zealand and Filipino.
  - The speaker is `client_id`, and references are the `sentence` field.
- **Conditions.** Whisper-small only:
  - FP16;
  - GPTQ-W3 under US-only, balanced and worst-weighted calibration, three seeds each.

  These are the same EdAcc calibration sets and code as H1/H2 at W3, which is where H2 was Supported. W4 is not
  decoded. All clips are short-form, decoded in batches of 32 as on EdAcc.
- **Statistics.** These are exactly plan section 5:
  - the worst-3 and best-3 named groups by FP16 WER on this data;
  - speaker-clustered bootstrap within groups (B = 2,000, seed 20261022);
  - the same decision rules, with the positive control P(GPTQ-W3, US-only) > 0.

  The D4 robustness variants are reported alongside. The replication counts as replicating H2 only if H2 is
  Supported on Common Voice by the same rule.
