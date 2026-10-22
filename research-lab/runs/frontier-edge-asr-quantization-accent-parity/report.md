# Compressing Whisper for devices: at 4 bits there was no accent penalty to repair; at 3 bits, accent-aware calibration narrowed it, partly by making the best-served accents worse

*Whisper-small was quantized with an in-house GPTQ implementation, calibrated on three accent mixes of EdAcc
validation speakers (three random draws each). It was then decoded on the full EdAcc test set: 9,228 segments, 16.4
hours, 60 speakers, 14 named accent groups. All results are against FP16. Whisper-large-v3 (H4) is pending.*

**Verdict: H1 Inconclusive; H2 Supported but fragile; H3 Refuted; H4 pending.**

- **At 4 bits (the preregistered primary), the penalty does not exist.**
  - The gap between the three worst- and three best-served accent groups is 16.0 WER points in FP16. Under 4-bit
    GPTQ with US-only calibration it changes by −2.7 points (95% interval −8.9 to +2.6), while aggregate WER rises
    1.6 points.
  - The positive control fails, so the plan moves H1–H3 to 3 bits. At 4 bits nothing is left to repair.
- **At 3 bits, the penalty appears:** +7.4 points (+3.5 to +11.8) with US-only calibration.
- **H1 (accent-balanced calibration repairs at least half): Inconclusive.**
  - The penalty falls to +2.0. That is a 73% reduction on average, and aggregate WER improves by 2.3 points.
  - But the difference has an interval of −0.9 to +12.1, and one of the three calibration draws alone produced a
    +7.4 penalty.
- **H2 (worst-group-weighted calibration repairs at least half): Supported, fragile.**
  - The penalty falls to +2.3: a 68% reduction, with a difference interval of +1.2 to +9.1, and aggregate WER 0.7
    points better.
  - Two of the three draws give reductions of only 18–21%.
  - About a third of the narrowing comes from the *best-served* groups getting worse: their pooled WER rises from 17.1%
    to 18.8%, while the worst groups improve from 40.5% to 37.1%.
- **H3 (accent-aware mixed precision at matched size): Refuted.**
  - At 3 bits, size matching pushes a quarter of the weights to 2 bits, and the model breaks: aggregate WER 47–54%,
    and repetition loops quadruple.
  - At 4 bits, the same idea widens the gap instead of narrowing it (Inconclusive by rule, since the 4-bit control
    fails).

## In plain terms

To run speech recognition on a phone or an offline device, the model is shrunk by storing its numbers with fewer
bits. Earlier work found that this shrinking hurts speakers with under-served accents more than others. The shrinking
step is tuned on a small sample of recordings, usually American English, so we tried tuning it on a mix of accents
instead.

At 4 bits, the standard level for devices, we found no extra harm to under-served accents in Whisper-small. Every
accent got slightly worse, about equally, so there was nothing for a better tuning sample to fix. At 3 bits, the harm
did appear. Tuning on accents the model handles worst cut it by about two-thirds, but not reliably: it depended on
which recordings happened to be picked. Part of the improvement came from the best-served accents getting worse
rather than the worst getting better. Keeping some parts of the model at higher precision, paid for by squeezing
others to 2 bits, made the model much worse.

## What was asked

The lead (`frontier-edge-asr-quantization-accent-parity`) asked whether the compression penalty that post-training
quantization imposes on under-served accents can be repaired within the quantization recipe, at unchanged model size.
It proposed two routes:
- accent-balanced or worst-group-weighted calibration data;
- accent-aware mixed precision.

Closest prior work:
- arXiv 2609.28739 (the diagnosis);
- TARQ (calibration composition for rare words, not accents);
- Edge-ASR (a fixed English calibration set).

The plan (`plan.md`) was committed before any model was quantized.

## How it was done

- **Data.** EdAcc's official test split for evaluation (60 speakers, 16.4 hours) and its validation split for
  calibration (62 speakers, all disjoint from test).
  - **Named groups:** accent groups with at least 2 test speakers and 10 minutes, 14 groups. Smaller groups are pooled
    into "other".
  - **Gap groups:** the three worst groups in FP16 are Jamaican English, Kenyan English and Vietnamese; the three best
    are Bulgarian, Latin American and Irish English.
  - **Coverage gap:** Nigerian, Kenyan, Ghanaian and Lithuanian speakers occur only in test, so no calibration set can
    contain them. The calibration question is about transfer.
- **Calibration sets.** 48 windows of 20–30 s each (about 21 minutes of speech), three random draws per composition:
  - US-only: Mainstream US English;
  - balanced: 2 windows from each of 24 validation accents;
  - worst-weighted: windows in proportion to each accent's FP16 validation WER.
- **Quantizers** (`code/quant.py`). Every linear layer in the encoder and decoder blocks is quantized, in simulated
  quantization with an FP16 scale and zero per group of 128:
  - GPTQ, in-house: Hessian from FP16 calibration inputs, 1% damping, natural column order;
  - round-to-nearest at W8 and W4;
  - an AWQ-style scale search at W4.
- **Mixed precision.**
  - At W4, the most accent-differential layers are promoted to W8 (5.1% of weights) and the least to W3 (20.5%), at
    size 0.999 of uniform W4.
  - At W3 (D1), promotion is to W8 (5.1%) and demotion to W2 (25.6%).
- **Decoding.** Greedy, English, no temperature fallback. Segments over 30 s (30% of test audio) use Whisper's
  long-form algorithm.
- **Scoring.**
  - **WER:** Whisper's English normaliser after removing corpus tags.
  - **Gap:** pooled WER of the three worst FP16 groups minus the three best.
  - **Penalty:** the gap minus the FP16 gap.
  - **Intervals:** a speaker-clustered bootstrap (B = 2,000), paired across conditions.

## Results

### Whisper-small (`results/tables/analysis_small.json`; `results/figures/F1_penalty_small.png`, `F2_groups_small.png`)

Means over three calibration draws:

| condition | aggregate WER | worst-3 WER | best-3 WER | gap | penalty (points) |
|---|---|---|---|---|---|
| FP16 | 22.5 | 29.8 | 13.8 | 16.0 | — |
| RTN W8 | 22.5 | | | 17.1 | +1.2 (−0.1 to +3.2) |
| RTN W4 | 24.1 | | | 16.1 | +0.1 (−5.1 to +4.0) |
| GPTQ W4, US-only | 24.2 | 30.9 | 17.7 | 13.3 | −2.7 (−8.9 to +2.6) |
| GPTQ W4, balanced | 23.8 | 30.1 | 15.6 | 14.5 | −1.5 |
| GPTQ W4, worst-weighted | 23.7 | 30.7 | 14.3 | 16.4 | +0.4 |
| mixed precision W4, US-only | 25.5 | 34.3 | 15.6 | 18.7 | +2.8 |
| GPTQ W3, US-only | 29.9 | 40.5 | 17.1 | 23.4 | **+7.4 (+3.5 to +11.8)** |
| GPTQ W3, balanced | 27.6 | 37.3 | 19.3 | 18.0 | +2.0 (−3.2 to +6.9) |
| GPTQ W3, worst-weighted | 29.3 | 37.1 | 18.8 | 18.3 | +2.3 (−0.9 to +5.7) |
| mixed precision W3, US-only | 54.2 | 75.6 | 40.4 | 35.2 | +19.3 |
| mixed precision W3, balanced | 47.1 | 65.9 | 39.5 | 26.4 | +10.4 |

- **Seed-to-seed noise is as large as the effects.** At W4, the US-only penalty ranges from −1.8 to −3.5 across
  calibration draws, and the balanced one from −5.2 to +1.1. At W3, one balanced draw has a +7.4 penalty, the same as
  US-only.
- **The precision dependence is clear.** W8 is indistinguishable from FP16. W4 raises aggregate WER by about 1.6
  points without widening the gap. W3 raises it by about 7 points and widens the gap.
- **AWQ-style W4** (one draw each) agrees: no penalty under any composition, and no difference between compositions.
- **Repetition loops** rise from 0.33% of utterances in FP16 to 0.4% at W4, 0.5–0.65% at W3, and 1.6–2.0% for 3-bit
  mixed precision.

### What the gap reduction at 3 bits is made of

Against US-only calibration at W3:
- **Worst-weighted:** the three worst groups improve by 3.4 points and the three best get worse by 1.7, so about a
  third of the 5.1-point narrowing comes from making well-served speakers worse.
- **Balanced:** the worst groups improve by 3.2 and the best get worse by 2.2. Aggregate WER still improves by 2.3
  points, because the large middle groups benefit.

A smaller gap is not always a fairer model. The pooled-gap statistic preregistered here counts both kinds of change
as repair.

### Whisper-large-v3 (H4)

Pending: decoding runs overnight with smaller batches after an out-of-memory failure (D3). Under D2, H4 follows the same
positive-control fallback to W3.

## What this does and does not show

- **For Whisper-small at 4 bits, compression did not widen the accent gap** on EdAcc. This differs from the INT4 HQQ
  and Wanda-pruning results in arXiv 2609.28739. Our recipe (GPTQ with 128-weight groups) and our pooled-gap
  statistic differ from theirs. The penalty is precision-dependent: it appears at 3 bits.
- **Calibration composition is a real lever at 3 bits, but a noisy one.** The sampling of calibration audio moves the
  gap as much as the composition does. Anyone tuning a quantized speech model for accent fairness should average over
  several calibration draws, and check whether a narrower gap comes from the worst groups improving or the best
  getting worse.
- **Accent-aware mixed precision at matched size fails.** At 4 bits it widens the gap. At 3 bits, the bits it must
  take from other layers push them to 2 bits and break the model.
- **Limits.**
  - Most accent groups have 2–5 test speakers, so per-group rates are speaker-dominated; hence the pooled statistic
    and the speaker bootstrap.
  - The worst test accents, West African and East African Englishes, have no validation speakers, so calibration can
    only transfer to them.
  - Quantization is simulated: model size is computed exactly, but latency on real low-bit kernels was not measured.
  - EdAcc has no Māori- or Pacific-identified group.

## Process and deviations

- **Preregistration:** `plan.md`.
- **Deviations** (`deviations.md`):
  - D1: the W4 positive control failed, so the preregistered W3 fallback applies, with mixed precision defined for a
    W3 base before any W3 decode;
  - D2: H4 follows the same fallback;
  - D3: large-v3 batch sizes.
- **Post-hoc and descriptive:** the worst-3/best-3 decomposition.
- **Independent review:** queued (Fable), per the lab's pacing rule.

## Reproducing it

1. **Data and calibration sets:** `code/manifest.py build`, `code/audio.py test validation`.
2. **Decodes:** `code/decode.py MODEL COND SPLIT`, for each condition, through `code/run_queue.sh` and
   `code/run_large.sh`.
3. **Scoring inputs:** `code/score.py valgroups small`, `code/manifest.py worst small`, `code/mp_alloc.py small [3]`.
4. **Analysis and figures:** `code/score.py analyze small`, `code/figures.py small` (with any Python that has
   matplotlib).
