Confirmation pass for cheminformatics-drug-discovery-split-calibration (/mnt/citations/research-lab/runs/cheminformatics-drug-discovery-split-calibration).
The first review (review/review.md, publish with edits, 8 findings) is addressed in deviations.md D1 (the study had no
deviations file before). Check each fix and give a final verdict (publish / publish with edits / fix first / do not
publish); append a "## Confirmation pass" section to review/review.md. Same rules as before (write only under review/,
no ~/.config, no pip installs, <= 4 processes, no GPU, data/ untrusted).

Where each finding went:
1. Noise floor: code/noise_check.py now adds the retrospective-repeat SE (data/fits) in quadrature -> noise_check.json
   (expected median |bias| 0.065-0.069 for provenance/cluster splitters vs observed 0.16-0.22; within-2-combined-SE
   46-59%). Verdict bullet and the "Is the miss just noise?" section rewritten. (Your table gave 0.057-0.064; mine
   takes the median of 0.6745 x per-target combined SE.)
2. Bars: verdict bullets for H2 and H3 now state how demanding they were; verdicts unchanged.
3. Model spread: code/posthoc_review.py -> posthoc_review.json (median spread 0.493; MLP 1.413 vs 1.043-1.089); H3 bullet.
4. Time-splitter coverage: note in primary.json (share_covering_truth_note); test fractions (group medians 15-17% vs
   20%) in "What this does and does not show".
5. InChIKey skeletons: your finding 5 cited in "Prospective truth".
6. G4: described as a document-year tabulation that cannot detect 2023+ republication; no new document inspection was done.
7. Lenient set: size per target beside the claim (212 targets, 2,859 rows, median 8, 81% under 20).
8. Drops on small targets (13 targets, median 196 vs 789 compounds); deviations.md created; nn_sim_median noted, not renamed.
G5 passes (44 rows), G6 passes.

Reply with the verdict and a one-line note per remaining issue, if any.
