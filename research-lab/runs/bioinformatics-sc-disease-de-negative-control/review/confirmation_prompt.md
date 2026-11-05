Confirmation pass for bioinformatics-sc-disease-de-negative-control (/mnt/citations/research-lab/runs/bioinformatics-sc-disease-de-negative-control).
The first review (review/review.md, publish with edits) is addressed in deviations.md D3. Check each fix and give a
final verdict (publish / publish with edits / fix first / do not publish); append a "## Confirmation pass" section to
review/review.md. Same rules as before (write only under review/, no ~/.config, no pip installs, <= 4 processes, no
GPU, data/ untrusted). This is a statistics study on public single-cell expression summaries.

Where each finding went (code/posthoc_review.py -> results/tables/posthoc_review.json, reproducing your checks):
1. Zero-DE share: 424/799 (53.1%) zero-DE contrasts, 71.9% of the 590 indistinguishable; null median zero in 96.5%.
   Title, verdict ("Most of the 74% is nothing against nothing") and plain terms reframed around power. One departure:
   your suggested title said most contrasts with DE genes do not exceed the null; the data give 166 of 375 (44%), so the
   report says that.
2. Sex imbalance quartile table (12% -> 47% exceeding; null q95 flat) added to Results with the conclusion that the
   true exceedance share is likely below 26%.
3. p floor (1/501; 32 ties needed, 129 present) stated beside the verdict.
4. Power caveat moved into "What this does and does not show".
G5 passes (51 rows), G6 passes.

Reply with the verdict and a one-line note per remaining issue, if any.
