# Confirmation pass: frontier-edge-asr-quantization-accent-parity

Reviewer: same independent reviewer as `review/review.md`; 2026-10-24. Checked commit f8a6d4d (and 159d37b, 3965a2c,
8a6d8c4 leading to it) against the thirteen findings, without redoing the review. New check script:
`review/reviewer_checks/splithalf_check.py` (+ `.json`). Nothing outside `review/` was touched; no GPU job was run.

## Verdict: **publish with edits**

Every finding is addressed, the robustness analyses reproduce mine, the Common Voice protocol was fixed before any
Common Voice audio was fetched or decoded, H4's "not testable" follows the plan's rule, and the new verdict line and
title are fair. The remaining edits are wording and two ranges; none changes a verdict.

## Findings, one line each

1. (W4 control = one loop) Addressed: report lines 16-22 and 52-54 name the utterance, give capped (+0.1, -0.6 to +0.8)
   and loop-removed (+0.1, -0.2 to +0.5) penalties, both matching `robustness_small.json`; the "about equally" claim
   is gone.
2. (W3 penalty and H2 are loop mass) Addressed: mechanism named (lines 23-27, 103-104), the sensitivity table
   (lines 132-138) matches `robustness_small.json` cell by cell, H2 presented as "Supported by the rule, not robust"
   with capped R 0.19 / loops-removed control fails / subs+dels Refuted R 0.02, all as in my recompute.
3. (draw variance) Addressed: per-draw differences +1.1/+12.6/+1.6 and draw-aware interval -1.5 to +13.3 (mine
   -1.8 to +13.5, different RNG stream) reported; headline verdict is Inconclusive.
4. (balanced and worst-weighted nearly identical) Addressed, lines 148-151, with the 5-of-48-windows and rho 0.05
   figures.
5. (missing secondaries, replication) Addressed: literal gap reported (lines 159-164, numbers match); Common Voice
   replication preregistered (D5) and run; HQQ not reproduced stated (line 206).
6. (2609.28739 framing) Addressed, lines 70-72 and 203-208: agreement on the loop mechanism, recipe and bit-width
   difference, test-only West African groups, Wanda is pruning.
7. (split-half selection bias) Addressed, lines 165-167, as "direction not established". See the reconciliation
   below: neither estimate is wrong; both are undersampled.
8. (H3 over-general) Addressed: "Refuted for this allocation rule", 25.6% at W2, 0.2% ranking signal (lines 39-41,
   168-173, 214-215).
9. (R when not meaningful) Addressed: `score.py` and `robustness.py` leave R and seed R null when the control fails
   or P(ref) <= 0; the JSONs show null; decision logic unchanged (diff checked).
10. (numbers and wording) Addressed: loop-rate ranges corrected (0.44-0.75%, 1.15-2.30%), 8,537 scored utterances
    and the 691 empty references stated, all seven test-only accents listed with the Indonesian label note, the
    "West and East African" sentence removed, teacher-forcing loops and the AWQ scale caveat noted. Two new small
    slips below.
12. (verdict line and title) Fair. "Verdict: Inconclusive" with H2 "Supported by the preregistered rule, but not
    robust", H3 "Refuted, for this allocation rule", H4 "not testable"; the title states the loop finding plainly.
13. (H4) Complete. W4 control +0.4 (-0.1 to +1.2) and W3 control -0.04 (-0.5 to +0.5) both fail, so by plan section 5
    ("if W3 fails too ... not testable, which is itself a finding") as extended to H4 by D2, "not testable" is the
    rule's output. The W3 fallback was decoded in full before the verdict (hypotheses 11:54-21:27 on the 23rd).

## The additional checks

- **robustness.py vs recompute.py.** Same definitions: capped = min(errors, reference length); loops removed =
  looped in any condition of the model (753 utterances, equal to my 8,537 - 7,784); subs+dels; draw bootstrap
  resamples the three draws of each arm independently inside each speaker resample. Same speaker-bootstrap weights
  (seed 20261022). Its numbers agree with mine to the rounding, and the report's tables match
  `robustness_small.json`, `robustness_large-v3.json` and `robustness_small_cv.json` wherever I checked (EdAcc
  table, draw-aware intervals, literal gap, loop shares, H4 table, Common Voice table).
- **Common Voice protocol before decoding.** D5 committed 2026-10-23 16:43:32 (159d37b). Transcript TSVs were
  fetched at 16:41 (D5 says its group list comes from transcript counts, so this is disclosed); the audio tars arrived
  at 16:44, the manifest at 16:47 (8a6d8c4), and the ten decodes ran 21:29-21:56 after large-v3 released the GPU.
  No Common Voice audio or hypothesis preceded the protocol. The analysis follows D5: single-label split rule
  (`cv.py:39-41`), >= 30 clips -> the ten named groups listed in D5, speaker = client_id (16-character prefix, which
  is unique over the 2,331 speakers), FP16 + GPTQ-W3 x 3 compositions x 3 draws with the EdAcc calibration sets,
  `score.py analyze small cv` with the plan's rules and bootstrap, positive control at W3. H2 is Inconclusive on
  Common Voice (difference -2.6, -10.8 to +4.0), so by D5's own criterion it does not replicate.
- **H4 "not testable".** Follows the rule (finding 13).
- **Split-half sign disagreement.** Neither is wrong. Re-implementing D4's procedure (Bernoulli halves, one
  direction, 20 replicates, seed 20261024) on my per-utterance table reproduces D4's numbers exactly
  (gptq_w3_us -1.34, rtn_w4 +0.57, gptq_w4_us -0.68 in D4's out-minus-in convention), so the code is right; my
  review used within-speaker balanced halves in both directions with a different seed. Both 20-replicate means have
  standard errors of 0.5-0.8 points against effects under 1 point, so they are noise. With 300 replicates (600
  evaluations) the two schemes agree: in-sample penalties are 0.3-0.7 points *below* out-of-sample for the three W3
  compositions (SE 0.15), 1.7 points below for RTN-W4, and 0.3-0.5 points above for GPTQ-W4 US-only, whose
  in-sample statistic is the loop artefact (`splithalf_check.json`). So the bias is small, slightly negative for the
  W3 conditions, and immaterial to any verdict. Suggested wording for lines 165-167 and 217-218: "A split-half check
  puts the bias under one point (in-sample penalties slightly lower); it does not affect any verdict."

## New issues (all minor; wording or a range)

1. `report.md:153-154`: "39-54% under 3-bit mixed precision" should be "28-54%": `mp3_balanced_s2` has 27.5% of
   its errors in looped utterances (`robustness_small.json` loops).
2. `report.md:157`: "Loop rates: 0.33-0.43% at W4" is the GPTQ-W4 range; RTN-W4 is 0.45% and AWQ-style 0.41-0.46%.
   Say "GPTQ-W4" or widen to 0.33-0.46%.
3. `report.md:37-38, 192-193`: "with loops removed both arms are Refuted (R 0.03)" holds with the groups re-fixed on
   the loop-removed data (where best-3 becomes New Zealand, Australia, Canada). With the preregistered Common Voice
   groups held fixed, the loop-removed control fails (+1.15, -0.18 to +2.43) and both arms are Inconclusive; on
   subs+dels H1 is Refuted re-fixed but Inconclusive on the fixed groups. "Does not replicate" is true either way;
   say "Refuted or Inconclusive depending on how the groups are fixed".
4. `report.md:184`: "Robust scoring agrees. Its largest penalty is +0.5 (0.0 to 0.9) at W3, with errors capped."
   Two corrections: the largest robust large-v3 penalty is balanced-calibration capped, +0.7 (+0.2 to +1.4); and
   under capped and subs+dels scoring with re-fixed groups the W3 US-only control technically holds (+0.47, +0.04 to
   +0.87; +0.51, +0.07 to +0.93) while neither composition repairs it (R -0.5 and 0.01; -0.2 and -0.17;
   Inconclusive). Suggested: "Under loop-robust scoring a penalty of about half a point is detectable at W3, and
   neither calibration composition reduces it."
5. D5 says all Common Voice clips are short-form; one clip (142.5 s, Canadian English, a 14-word sentence, probably
   corrupt audio) exceeded 30 s and went through long-form decoding. Harmless; note it or drop the clip.
6. `robustness_small_cv.json` "long" variant holds NaN (that single clip); harmless, but a strict JSON parser will
   reject the file.
7. The split-half wording (above) can be made definite rather than "direction not established".
