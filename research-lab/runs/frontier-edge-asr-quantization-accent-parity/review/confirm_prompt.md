You are the independent reviewer of /mnt/citations/research-lab/runs/frontier-edge-asr-quantization-accent-parity/,
doing the CONFIRMATION PASS. Your review is review/review.md ("fix first", findings 1–13, with H4 pending). Your
scripts are in review/reviewer_checks/. Since your review:
- D4 adds code/robustness.py, the robustness analyses you recommended: scoring variants, a draw-aware bootstrap,
  literal gap, split-half and drivers. score.py leaves R null when it is not meaningful.
- D5 preregisters and runs the Common Voice replication: code/cv.py, run_cv.sh; analysis_small_cv.json,
  robustness_small_cv.json.
- H4 (Whisper-large-v3) finished: analysis_large-v3.json, robustness_large-v3.json.
- report.md is rewritten.

Be economical. Check, finding by finding, that each is addressed: 1–10, 12, and 13 now that H4 is complete. Then
check that:
- robustness.py's variants match your recompute.py (capped, loops removed, substitutions and deletions, draw
  bootstrap), and the report's numbers match the robustness JSONs;
- the CV protocol in D5 was logged before any CV decode (git), and the CV analysis follows it;
- H4's "not testable" follows the plan's rule;
- the new verdict line and title are fair.

The split-half estimate here (−1.3 to +0.6 mean) differs in sign from yours. Say whether either is wrong.

Write review/confirmation.md: a verdict (publish / publish with edits / fix first), one line per finding, then any new
issues. Reply with the verdict line and the new issues only.
