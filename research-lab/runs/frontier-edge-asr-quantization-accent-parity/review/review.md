# Review: frontier-edge-asr-quantization-accent-parity (Whisper-small; H4 large-v3 pending)

Reviewer: independent adversarial review, 2026-10-23. Scripts and outputs: `review/reviewer_checks/`
(`utt_errors.py` -> per-utterance scoring of every saved hypothesis; `recompute.py` -> exact replication of
`score.py` plus stress variants, `recompute.log`/`recompute.json`; `calib_checks.py` -> calibration audit,
`calib_checks.json`; `gptq_check.py` -> GPTQ vs RTN on real activations, CPU, `gptq_check.json`). Nothing outside
`review/` was modified; no GPU job was touched.

## Verdict: **fix first**

The pipeline is sound and preregistration was honoured, and every number in the report matches
`analysis_small.json`. But the headline statistics are carried by a handful of runaway repetition loops (220-500
words emitted against 3-83 reference words), and the report does not say so. One looping utterance is the entire
reason the W4 positive control "fails"; at W3, 50-64 looped utterances (0.6-0.75 % of utterances) carry 21-27 % of
all errors, and under any loop-robust scoring H2 is Inconclusive or Refuted and the W3 "penalty" shrinks from +7.4
to +0.6..+1.9 points. The H2 interval also omits calibration-draw variance; with it, the effect crosses zero. The
preregistered rule does return "Supported (fragile)", and that label may stay in the analysis file, but the report's
verdict line, plain-terms section and the lab's one-word verdict_tag should read **Inconclusive / not robust**, with
the sensitivity analysis shown. H4 is pending (see finding 13) and was not reviewed.

## Findings

### 1. Critical - the failed W4 positive control is one looping hypothesis

- Evidence (`recompute.log`, "drivers"): under GPTQ-W4 US-only, Latin American (a best-3 group: 2 speakers,
  2,337 reference words) goes 14.0 % -> 31.9/31.8/31.4 % in all three seeds. 100 % of the change is utterance
  `test-00001:574` (speaker EDACC-C26-A, 31.9 s, 83 reference words): 443-449 errors, 423-426 insertions, a 500-word
  hypothesis ending "na na na ..." (FP16: 84 words, 32 errors; balanced and RTN-W4: 83-92 words). That single
  utterance lifts pooled best-3 WER from 13.8 % to 17.7 % and makes the penalty -2.7 (-8.9, +2.6).
- The same pattern explains the other W4 swings the report does not mention: Southern British English
  23.1 -> 35.7 % (one 330-word loop on a 24-word reference, `test-00006:820`), Chinese 19.3 -> 31.2 % (one
  396-word loop on a 1-word reference, `test-00007:139`).
- With errors capped at the reference length (WER <= 100 % per utterance) the W4 US-only penalty is
  +0.1 (-0.6, +0.8); excluding utterances looped in any condition, +0.1 (-0.2, +0.5); counting only substitutions
  and deletions, +0.3 (-0.0, +0.6). So "no measurable W4 penalty" is right, and far better supported than the
  reported interval suggests, but for a different reason.
- The plain-terms claim "Every accent got slightly worse, about equally" (`report.md:38-39`) is contradicted by the
  study's own group table (`analysis_small.json` per_condition group_wer).
- Fix: report the W4 result on loop-robust scoring alongside the preregistered statistic; add the per-utterance
  driver table; rewrite the plain-terms paragraph.

### 2. Critical - the W3 penalty and both "repairs" are loop-mass effects; H2 does not survive loop-robust scoring

- Mechanism: short-form decoding is greedy, no timestamps, `max_new_tokens=440` (`decode.py:53`), and the plan
  switches off every fallback (`decode.py:64-66`, plan section 6). When the model fails to emit end-of-text, it runs
  to the cap. Examples at W3 US-only: a 3.4 s Scottish utterance with 10 reference words -> 439 words of "a bit of a
  bit of ..." (`gptq_w3_us_s2`, `test-00000:198`, 439 errors); an 8.8 s Jamaican utterance, 3 reference words ->
  220 x "no" (`gptq_w3_us_s1`, `test-00008:19`, 217 errors). Whisper's reference inference suppresses exactly this
  through the compression-ratio fallback the plan disabled.
- Error mass (`recompute.log`, "loop / runaway diagnostics"): looped utterances carry 7.5 % of errors at FP16,
  11-13 % at GPTQ-W4, 21-27 % at GPTQ-W3 US-only, 42 % for 3-bit mixed precision; insertions are 26-30 % of all W3
  errors; the top-3 utterances carry 54-101 % of each large group swing (Bulgarian 10.2 -> 30.0 % under
  `gptq_w3_worst_s1` is one 378-word hypothesis on a 79-word reference).
- Recomputed verdicts (`recompute.log`, variants):

  | scoring | W3 US-only penalty | H1 (R, diff CI) | H2 (R, diff CI) |
  |---|---|---|---|
  | preregistered | +7.4 (3.5, 11.8) | Inconclusive (0.73; -0.9, 12.1) | **Supported (fragile)** (0.68; 1.2, 9.1) |
  | capped at 100 % per utterance | +1.9 (0.8, 3.3) | Inconclusive (0.26; -0.4, 1.1) | Inconclusive (0.19; -0.2, 1.1) |
  | utterances looped in any condition removed (7,784 kept) | +0.6 (-0.1, 1.5), control fails | Inconclusive (0.23) | Inconclusive (-0.67) |
  | substitutions + deletions only | +1.5 (0.8, 2.6) | Inconclusive (0.32; -0.0, 0.9) | **Refuted** (0.02; -0.4, 0.5) |
  | short-form only (8,214 utts) | +8.9 (3.8, 14.1) | Inconclusive (0.97; -1.6, 19.8) | Inconclusive (0.71; -0.1, 13.4) |
  | long-form only (323 utts) | +0.5 (-2.5, 3.8) | Inconclusive | Inconclusive |

- Reading: at 3 bits the accent gap widens because loops become more frequent and land on a few short utterances
  of a few worst-group speakers. That is a real and reportable effect (and the same mechanism arXiv 2609.28739
  describes for INT4 HQQ), but it is not the graded degradation the report implies, and "worst-weighted calibration
  repairs 68 % of it" is not a robust statement. Counting a 440-word loop on a 3-word reference as 437 errors is the
  preregistered choice, not a protocol breach; the breach is in not reporting what the statistic is made of.
- Fix: add the table above to the report; name the mechanism; present H2 as "Supported by the preregistered rule,
  not robust to scoring or to calibration draw"; rewrite the title and the plain-terms section.

### 3. Major - the H2 interval ignores calibration-draw variance; with it, the support disappears

- `analysis_small.json` H2_w3: seed_R 0.18 / 1.44 / 0.21. Per-seed differences P(US) - P(worst): +1.1, +12.6,
  +1.6 points; the whole mean effect is seed 1, where `gptq_w3_worst_s1` has P = -3.9 (gap narrower than FP16).
- `recompute.log`, "speaker + calibration-draw bootstrap": resampling the three draws as well as the speakers gives
  a 95 % interval of (-1.8, +13.5) for H2 and (-2.9, +14.5) for H1; the speaker-only intervals are (1.2, 9.1) and
  (-0.9, 12.1). A t-interval on the three per-seed differences is (-11, +21).
- The plan fixed seeds as averaged, so the rule output is legitimate, and the fragile flag exists for this. But the
  lead's own text says the 3-seed repeat exists "so that calibration-sampling noise is separated from the
  intervention effect"; the report should then not headline "Supported".
- Should it be Inconclusive? Answer: by the preregistered rule, no; by every robustness check, yes. Recommended
  wording: "H2: the preregistered rule returns Supported (fragile across seeds); the effect rests on one of three
  calibration draws and is not present under loop-robust scoring or a draw-aware interval. Verdict_tag:
  Inconclusive." The bootstrap is otherwise correct (within-group resampling incl. "other", paired weights, seeds
  averaged inside each resample, `score.py:89-117`), though with 2-speaker groups each group has only three
  distinguishable resamples, so the intervals are coarse.

### 4. Major - "worst-weighted" and "balanced" are nearly the same calibration set; H1 vs H2 is noise

- `calib_checks.json`: the largest-remainder allocation gives 1-3 windows per accent (raw 0.99-3.29) against 2 for
  balanced; only 5 of 48 windows move; the drawn sets share 24-26 of ~33 speakers.
- Validation accent WER does not predict test accent WER: Spearman rho = 0.045 over the 11 shared accents.
  Validation worst-3 are Indonesian English, Vietnamese, Indian English; test worst-3 are Jamaican, Kenyan,
  Vietnamese. Bulgarian is 30.9 % on validation (so it gets 3 "worst" windows) and 10.2 % on test (a best-3 group).
  With 2-5 speakers per accent, the "worst-group" composition weights validation speakers' idiosyncrasies, not an
  accent property.
- Fix: say so in the report; do not interpret H1 != H2 as a composition effect; note that the two arms test
  "accent-diverse vs US-only" twice.

### 5. Major - preregistered secondaries and a triggered replication are missing from the report

- Literal re-ranked gap (plan.md:92-94, "reported as a secondary") is computed (`analysis_small.json`
  literal_gap) but absent from `report.md`. At W3 US-only its penalty is +14 to +18.5 points with intervals
  excluding 0; it is biased upward by noise (max - min of noisy groups), which the report should say.
- Common Voice replication (plan.md:122): "only if H1, H2 or H3 is Supported ... If not run, this is stated."
  H2 is Supported by rule, so the condition fired; the report neither runs it nor states it.
- The lead asked for two independent quantizer implementations including HQQ, plus latency/energy; the plan
  deviated (in-house GPTQ/RTN/AWQ-style, simulated). Fine as preregistered, but the comparison with
  arXiv 2609.28739 must say the HQQ recipe was not reproduced.

### 6. Major - the comparison with arXiv 2609.28739 is mis-framed

- `report.md:138-141` says the W4 null "differs from the INT4 HQQ and Wanda-pruning results". The prior paper's
  INT4 result is specifically that HQQ "compounds catastrophic transcript loops on West African accents" 5-7x
  (AfriSpeech-200); its gap-doubling result is for 50 % Wanda pruning of large-v3, not quantization.
- This study agrees on mechanism (its W3 penalty is loop compounding) and finds the loop rate barely moves at
  GPTQ-W4 g128 (0.33 % -> 0.36-0.41 %). That is the actual point of difference: recipe and bit-width, not the
  existence of the effect. EdAcc's West African groups are test-only (Nigerian, 5 speakers; Ghanaian pooled into
  "other"), so the study cannot speak to the prior paper's population.
- Fix: rewrite the comparison around loops; state recipe (GPTQ g128 vs HQQ), bit-width, dataset and group
  differences.

### 7. Minor - fixing worst-3/best-3 on FP16 test WER biases penalties downward (regression to the mean)

- `recompute.log`, "split-half": over 20 random within-speaker splits, choosing the six groups on one half and
  measuring the penalty on the other half gives penalties 0.6-1.8 points *higher* than in-sample for rtn_w4,
  gptq_w3_us, gptq_w3_balanced and gptq_w3_worst (selected-best groups regress up, selected-worst down). Modest
  against the loop effect, but the same size as the "repaired" W3 penalties (+2.0, +2.3).
- The FP16 ranking is itself loop-affected: under capped scoring the worst-3 become Nigerian, Jamaican, Vietnamese
  (Kenyan drops out; FP16 has 28 looped utterances, 7.5 % of its errors).
- Fix: state the bias as a limitation; optionally report the split-half estimate.

### 8. Minor - D1's mixed precision at W3 follows the plan but "mixed precision fails" is over-general

- `deviations.md:12-16` keeps hi = W8 and sets lo = W2. From a W3 base, 5.1 % of weights at W8 costs 0.25 bit/weight,
  which forces 25.6 % of weights to W2 (`mp3_allocation_small.json`; `quant.py:203-224`), versus 20.5 % to W3 at the
  W4 base. Other "same design" readings (promote to W4, demote ~5 % to W2) would not have broken the model. The
  "step back if overshot" comment at `quant.py:223` is not implemented (harmless here: ratios 0.9993 and 0.99908).
- The layer ranking has almost no signal: median |err_worst - err_best| is 1.5e-5 against errors of ~6e-3 (0.2 %),
  so the "accent-differential" order is mostly noise and ends up demoting the large fc2 layers. The plan did not
  preregister a check that the scores exceed resampling noise.
- H3 "Refuted" at W3 is correct by rule for this allocation (and the W4 version widens the gap, +2.8 vs -2.7).
  Fix: narrow the claim to "this allocation rule, at hi = W8, fails"; note that under capped scoring H3_w3 is
  Inconclusive only because the model is broken either way (aggregate +10 points).

### 9. Minor - R is reported when the reference penalty is <= 0 or the control fails

- `score.py:128,136`: R = 1 - P(arm)/P(US) is written for every comparison, giving H1_w4 R 0.45, H2_w4 R 1.16,
  H3 R 2.04 and seed_R values like -1.95 and 25.99 when P(US) is -2.7 or near zero. The verdict is protected by
  the control gate, but the JSON is misleading. Fix: null when the control fails or P(US) <= 0.

### 10. Minor - number and wording errors in the report

- Loop rates (`report.md:118-119`): W3 is 0.44-0.75 % (us_s1 0.75 %), not "0.5-0.65 %"; 3-bit mixed precision is
  1.15-2.30 %, not "1.6-2.0 %". The utterance-share framing also hides that these utterances carry a fifth to a
  quarter of all errors.
- "9,228 segments" (`report.md:4-5`): 691 references (7.5 %) are empty after tag removal and are dropped
  (plan-conformant); 8,537 utterances are scored. Say so.
- Test-only accents (`report.md:68`): Nigerian, Kenyan, Ghanaian, Lithuanian, plus Israeli (in the plan), Indonesian
  and Romanian. "Indonesian" (test) and "Indonesian English" (validation) are different labels for presumably the
  same accent, so the validation worst group has no test counterpart under its name.
- "The worst test accents, West African and East African Englishes, have no validation speakers" (`report.md:150`):
  of the worst-3, Jamaican has 43 validation windows and Vietnamese 63; only Kenyan has none. Rephrase.
- 4 of the 331 teacher-forcing transcripts are themselves loops (3-gram repeated >= 5 times; one is 293 words for
  <= 30 s of audio), so a few calibration targets are looped FP16 output. Note it.
- AWQ-style (`quant.py:156-176`): the per-channel input scale is simulated as free for every layer, but for fc2 and
  out_proj no preceding linear can absorb it in Whisper (GELU and attention sit in between). Secondary only; note it.

### 11. What checks out

- GPTQ (`quant.py:50-81`): H = 2XX^T/n from the FP16 model, non-sequential (all Hessians collected before any
  weight is written, `quant.py:136-148`); 1 % damping with escalation; upper Cholesky factor of H^-1; lazy block
  updates; per-group grid from the already-compensated weights at each group boundary (block = group = 128). The
  identity-Hessian test reduces exactly to RTN; on held-out windows GPTQ/RTN relative output error is 0.21-0.71 in 7
  of 8 layers at both W4 and W3 (`gptq_check.json`; `decoder.8.encoder_attn.out_proj` is ~1.0 held-out while 0.25
  in-sample, i.e. overfit to US-only activations). Quantised modules are all 192 block linears; conv, embeddings
  (tied projection) and layer norms untouched. Size: 198,180,864 weights, 4.25 bits/weight at W4, FP16 and W3/W8
  totals and the mixed-precision ratios all recomputed correctly.
- Calibration (`calib_checks.json`): all nine draws reproduced bit-exactly from the recorded seeds; zero test
  speakers; every window one speaker, consecutive segments, 20-30 s; totals 1,204-1,260 s (spread 4.6 %); worst
  allocation reproduced; teacher-forcing text present for all 331 windows.
- Scoring: the ten corpus tags all match the regex; 0 speaker overlap across splits; `recompute.py` reproduces
  every number in `analysis_small.json` (baseline rows); empty hypotheses are scored as deletions.
- Git order: plan 15:37:51 < code 15:42:22 < first decode ~15:43; D1 17:01:34 < first W3 decode 18:41:28; the mp3
  allocation (in the D1 commit) < first mp3 decode 20:13; worst-weighted and W4 mixed-precision allocations
  15:56:11 < their first conditions 16:58 / 17:24; D3 22:00:33 < pipeline restart 22:00:35 < first large-v3 output
  23:00:53. `score.py`'s post-decode edit (22:03) adds descriptive fields only; the decision logic is unchanged.
- Long-form decoding: 323 segments, 27.5 % of reference words, 16-20 % of errors; settings identical across
  conditions; long-only penalties are small and noisy. It does not drive the gap; the loops are mostly short-form.

### 12. Suggested edits to the verdict line

"H1 Inconclusive; H2 Supported by the preregistered rule but not robust (Inconclusive on loop-robust scoring and
with calibration-draw uncertainty); H3 Refuted for this allocation; W4: no measurable penalty, and the raw statistic
is dominated by single looping utterances; H4 pending." Verdict_tag: Inconclusive.

### 13. H4 (Whisper-large-v3) - pending, not reviewed

`results/tables/analysis_large-v3.json` (written 10:38 today) holds only the W4 conditions: US-only penalty +0.4
(-0.1, +1.2), control fails as D2 anticipated, no Latin American artifact. The W3 fallback is decoding
(`gptq_w3_us_s2` running at review time; `balanced_s2` and `worst_s0-s2` to follow, about 75 min each). The H4 review
should run `utt_errors.py large-v3` and the same variants; the per-utterance machinery here takes the model name.
