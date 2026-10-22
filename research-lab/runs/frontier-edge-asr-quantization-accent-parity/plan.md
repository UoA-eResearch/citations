# Plan: does accent-balanced calibration repair the 4-bit compression penalty in Whisper?

Lead: `frontier-edge-asr-quantization-accent-parity`. Written 2026-10-22, before any model was quantized or any
decoding was run. Only corpus metadata (speakers, accent labels, durations, transcript markup) has been inspected.

## 1. Question and hypotheses

Post-training quantization (PTQ) to 4 bits is how speech recognition reaches phones, hearing aids and offline
devices. Recent work shows compression widens the word-error-rate (WER) gap between accent groups (arXiv
2609.28739). Calibration-based PTQ tunes the rounding on a small audio sample, which is usually American English.
For text LLMs, the calibration language mix drives multilingual damage (arXiv 2601.18306). TARQ (arXiv
2605.27808) shifts an ASR calibration set to repair rare-word degradation, and Edge-ASR (arXiv 2507.07877)
benchmarks PTQ on Whisper with a fixed English calibration set. No study varies the *accent* composition of the
calibration set, or allocates precision by accent sensitivity at matched size.

- **H1 (primary).** For Whisper-small quantized with GPTQ to 4 bits (group size 128), an accent-balanced calibration
  set reduces the compression penalty on the worst-versus-best accent gap by at least 50% relative to a US-English-only
  calibration set of the same size. The guardrail: aggregate WER no more than 0.5 percentage points worse.
- **H2.** The same holds for a worst-group-weighted calibration set.
- **H3.** Accent-aware mixed precision at matched size (section 4) reduces the penalty by at least 50% relative to
  uniform 4-bit, both with US-only calibration.
- **H4 (generalisation).** H1–H2 on Whisper-large-v3.

## 2. Data

- **EdAcc** (Edinburgh International Accents of English Corpus; HF mirror `edinburghcstr/edacc`): conversational
  English, speaker-level accent labels.
  - Official splits: test, 60 speakers and 16.4 h; validation, 62 speakers and 15.3 h. No speaker is in both.
  - Segments marked `IGNORE_TIME_SEGMENT_IN_SCORING` are dropped.
- **Evaluation:** the whole official test split.
  - Segments up to 30 s are decoded short-form.
  - Longer segments (323 of 9,228; 30% of test audio) use Whisper's sequential long-form algorithm, since dropping
    them would bias the sample towards short turns.
- **Calibration pool:** the validation split only, so calibration and evaluation speakers are disjoint by
  construction.
- **Accent groups.** These use EdAcc's curated `accent` field.
  - A test group is **named** if it has at least 2 speakers and 10 minutes of speech. That gives 14 groups:
    Bulgarian, Chinese, Indian English, Irish English, Jamaican English, Kenyan English, Latin American, Lithuanian,
    Mainstream US English, Nigerian English, Scottish English, Southern British English, Spanish and Vietnamese.
  - Every other test speaker, including "Don't know", is pooled into an "other" stratum. That stratum counts towards
    aggregate WER but is never ranked.
  - EdAcc has no Māori- or Pacific-identified group. Had one existed, it would have been pooled and not named (the
    lead's care note).
- **Coverage limit.** Nigerian, Kenyan, Ghanaian, Lithuanian and Israeli speakers appear only in test, so no
  calibration set can contain them. H1 therefore asks whether balancing over the accents that *are* available
  transfers to those that are not. This is reported, not hidden.

## 3. Models, quantizers, calibration

- **Models.** `openai/whisper-small` (primary) and `openai/whisper-large-v3` (H4), in FP16.
- **What is quantized.** Every linear layer inside the encoder and decoder blocks: self- and cross-attention q, k, v
  and out, plus fc1 and fc2. The convolutional front end, embeddings, layer norms and the tied output projection stay
  FP16.
- **Simulated quantization.** Weights are quantized and dequantized to FP16 ("fake quantization"). Model size is
  therefore computed analytically from the packed format (bits per weight plus one FP16 scale and one zero per group
  of 128). Size is identical across calibration compositions by construction. Latency on real low-bit kernels is not
  measured; this is a stated limitation, not a tested guardrail.
- **Quantizers**, all implemented in-house in `code/quant.py`:
  - **RTN:** round-to-nearest, asymmetric min–max per group of 128; calibration-free. W8 and W4.
  - **GPTQ** (Frantar et al. 2022): per-layer Hessian H = 2XXᵀ from calibration inputs; damping 1% of the mean
    diagonal; columns in natural order (no act-order); blocks of 128; asymmetric per-group scales computed as each
    group is reached. Hessians are accumulated from the FP16 model in one pass per layer subset (non-sequential
    variant). W4 primary; W3 is the fallback in section 5.
  - **AWQ-style** (secondary): a per-input-channel scale s = mean|x|^α, with α in {0, 0.25, 0.5, 0.75, 1} chosen per
    layer to minimise output MSE on the calibration inputs, then RTN W4 g128. This second calibration-dependent
    method is a robustness check on GPTQ.
- **Calibration sets.** Each has 48 windows of 20–30 s, made by packing consecutive segments of one speaker. The
  decoder is teacher-forced on the FP16 model's own transcript of each window, avoiding the corpus's upper-case,
  unpunctuated reference style. Total speech is matched within ±5% across compositions. Each composition is drawn
  with three seeds (0, 1, 2).
  - **US-only:** Mainstream US English validation speakers (8 speakers, 74 min available).
  - **Balanced:** 2 windows from each of the 24 named validation accents ("Don't know" excluded).
  - **Worst-weighted:** windows allocated in proportion to each validation accent's FP16 WER (Whisper-small, or
    large-v3 for H4, on the validation split), by largest remainder.

## 4. Accent-aware mixed precision (H3)

1. On the validation split, take the 3 accents with the highest and the 3 with the lowest FP16 WER.
2. For every quantizable layer, measure the relative output error of RTN-W4 weights, ‖Wx − Q(W)x‖²/‖Wx‖², on 8
   windows from each of those 6 accents (seed 0). Score each layer by the error on the worst-3 minus the error on
   the best-3.
3. Promote the highest-scoring layers to W8 until they cover at least 5% of quantizable weights.
4. Demote the lowest-scoring layers to W3 until total bits match uniform W4 within 1%.
5. Quantize with GPTQ under US-only calibration (B-US, tests H3) and balanced calibration (B-bal), three seeds each.

## 5. Outcomes and decision rules

- **WER.** Text is normalised with Whisper's English normaliser after removing corpus tags (`<LAUGH>`, `<DTMF>`,
  `<OVERLAP>`, `<NO-SPEECH>`, `<FOREIGN>` and the like). Segments whose reference is empty after normalisation are
  dropped. Group WER = total errors / total reference words.
- **Gap.** Pooled WER of the 3 named groups with the highest FP16 test WER, minus pooled WER of the 3 with the lowest.
  The six groups are fixed from FP16 and used for every condition. Pooling three groups is preregistered for
  stability, since most groups have 2–5 speakers. The literal worst-minus-best gap, re-ranked per condition, is
  reported as a secondary.
- **Penalty.** P(c) = gap(c) − gap(FP16). Each composition's penalty is averaged over its three seeds.
- **Reduction.** R = 1 − P(test arm) / P(US-only).
- **Intervals.** Speaker-clustered bootstrap (speakers resampled within each group, B = 2,000, seed 20261022),
  paired across conditions, seeds averaged within each resample.
- **Positive control.** P(GPTQ-W4, US-only) has a lower 95% bound above 0. If it fails, H1–H3 are tested at W3 g128
  with the same design, and W4 is reported as showing no measurable penalty. If W3 fails too, H1–H3 are not testable
  ("no penalty to repair"), which is itself a finding.
- **H1** (and H2, and H3 with B-US against uniform US-only):
  - **Supported** if all of these hold:
    - the positive control holds;
    - R ≥ 0.5;
    - the lower 95% bound of P(US-only) − P(arm) is above 0;
    - aggregate WER(arm) − aggregate WER(US-only) ≤ 0.5 pp.
  - **Refuted** if the positive control holds and the upper 95% bound of P(US-only) − P(arm) is below
    0.5 × P(US-only). A 50% repair is excluded.
  - Otherwise **Inconclusive.**
  - A Supported verdict that varies by seed (one seed's R below 0.25) is flagged as fragile.
- **H4.** The same rules on Whisper-large-v3, with GPTQ-W4 under US-only, balanced and worst-weighted calibration,
  three seeds each, plus FP16 and RTN-W4.
- **Secondaries:**
  - per-group WER for every condition;
  - aggregate WER;
  - a loop/hallucination rate: utterances whose hypothesis has more than 2 × reference + 10 words, or a 3-gram
    repeated at least 5 times;
  - the RTN-W8 and RTN-W4 penalties (precision dependence);
  - AWQ-style penalties by composition (one seed each);
  - B-bal.
- **Replication** on an accent-labelled Common Voice 17.0 English subset only if H1, H2 or H3 is Supported on EdAcc.
  If not run, this is stated.

## 6. Decoding

- HF transformers, FP16 on the shared A100. The co-tenant vLLM server is never stopped; batch sizes fit the free
  memory.
- Greedy decoding, `language="en"`, `task="transcribe"`, no temperature fallback.
- Short-form: no timestamps, batch 32 (small) or 16 (large-v3).
- Long-form: timestamps on, `condition_on_prev_tokens=False`, batch 8.
- Identical settings for every condition.

## 7. Order of work

1. `code/manifest.py`: segment manifest, groups and floors, calibration windows per composition and seed. Counts
   published before any decoding.
2. FP16 decoding of test and validation (validation WER feeds the worst-weighted composition and the mixed-precision
   ranking).
3. Quantize and decode each condition.
4. `code/score.py`: WER, gaps, bootstrap, decisions.
5. Report.

Deviations are logged in `deviations.md` with timestamps, before the results they could affect.
