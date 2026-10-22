You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/frontier-edge-asr-quantization-accent-parity/ (read-only except your output
in review/).

**The question.** For Whisper quantized after training, does an accent-balanced or worst-group-weighted calibration
set, or accent-aware mixed precision at matched size, repair the widening of the accent gap that compression causes?
The data is EdAcc (test 60 speakers / 16.4 h; validation 62 speakers, used for calibration). The quantizers are an
in-house GPTQ, RTN and an AWQ-style method, in simulated quantization.

**Reported** (Whisper-small):
- W4: positive control fails (no penalty, −2.7 pp, −8.9 to +2.6), so the preregistered W3 fallback applies (D1).
- W3: penalty +7.4 pp (+3.5 to +11.8).
- H1 (balanced): **Inconclusive** (R 0.73; difference −0.9 to +12.1).
- H2 (worst-weighted): **Supported (fragile across seeds)** (R 0.68; difference +1.2 to +9.1). A third of the
  narrowing comes from the best groups getting worse.
- H3 (mixed precision): **Refuted** at W3 (W2 layers break the model).
- H4 (Whisper-large-v3): see results/tables/analysis_large-v3.json if present; otherwise it is pending, so say so.

**What to read:**
- plan.md, deviations.md (D1–D3), report.md;
- code/: manifest.py, audio.py, quant.py, decode.py, score.py, mp_alloc.py, figures.py, run_queue.sh, run_large.sh;
- results/tables/ (manifest_counts, analysis_small.json, conditions.jsonl, mp*_allocation_small.json,
  fp16_validation_group_wer_small.json, manifest_worst_small.json);
- results/figures/;
- data/hyps/<model>/*.jsonl (hypotheses per condition);
- data/manifest/ (segments, calibration windows).

**Git.** Read-only git is fine. Check that:
- plan.md preceded any quantization or decoding;
- the code was committed before the decodes;
- D1 preceded every W3 decode, and D3 preceded every large-v3 output;
- the worst-weighted allocation and the mixed-precision allocations were committed before their conditions ran.

**Environment.**
- Python: /mnt/citations/research-lab/runs/frontier-edge-asr-quantization-accent-parity/venv/bin/python (torch,
  transformers, jiwer), with -I. Do NOT pip install.
- The GPU is shared with a vLLM server that must not be stopped, and the large-v3 pipeline may still be running
  (`ps`). Do not run GPU jobs; re-scoring from the saved hypotheses is CPU-only.
- Put scripts and outputs under review/reviewer_checks/.

Check at least:

1. **GPTQ correctness** (quant.py): Hessian accumulation (non-sequential, as preregistered), damping, the group-wise
   grid, the block updates. Does the W4 GPTQ actually beat RTN on layer reconstruction? Is the simulated
   quantization applied to the right modules? Are the size computations right, including mixed precision
   (size_ratio)?
2. **Calibration.** Check:
   - speaker disjointness;
   - matched durations;
   - teacher forcing on FP16 transcripts;
   - the worst-weighted allocation;
   - for each composition and seed, that the windows are drawn as the plan says.
3. **Scoring** (score.py): normaliser and tag removal; empty references; per-utterance errors. Is the
   speaker-clustered bootstrap right (within-group resampling, pairing across conditions, seed averaging)? Is the
   pooled worst-3/best-3 gap, with groups fixed by FP16 test WER, subject to selection or regression-to-the-mean
   bias? How does the literal gap behave? Recompute H1/H2 at W3 from the hypotheses.
4. **The verdict rules.** Is "Supported (fragile across seeds)" for H2 the right reading? Two of three seeds give
   R < 0.25, and a third of the narrowing comes from worsening the best groups. Should it be Inconclusive? Is R
   handled correctly when the reference penalty is near zero or negative (W4)?
5. **D1.** Is the W3 fallback applied as the plan specifies? Is mixed precision at W3 (W2 demotion) a fair reading of
   "the same design", or a design that sets H3 up to fail?
6. **Long-form decoding** (30% of test audio): consistent across conditions? Check that the loop rates and any
   empty or garbled hypotheses do not drive the gap.
7. **The report.** Check every number against analysis_small.json, the plain-terms section, the comparison with
   arXiv 2609.28739, and the limits (EdAcc group sizes, no calibration speakers for the West African and East African
   accents).

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.
