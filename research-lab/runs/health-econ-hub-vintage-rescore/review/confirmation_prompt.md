Confirmation pass for health-econ-hub-vintage-rescore (/mnt/citations/research-lab/runs/health-econ-hub-vintage-rescore).
The first review (review/review.md, fix first, 6 findings) is addressed in deviations.md D2. Check each fix and give a
final verdict (publish / publish with edits / fix first / do not publish); append a "## Confirmation pass" section to
review/review.md. Same rules as before (write only under review/, no ~/.config, no pip installs, <= 4 processes, no
GPU, data/ untrusted).

Where each finding went:
1. Pooled revisions: code/score.py now computes revisions per scoring hub on forecast target weeks (primary.json
   "revision", with median lag and share > 7 days). The numbers reproduce your table (1,841 / 47.5% / 9.3% / +4.3%;
   1,748 / 13.6%; 1,625 / 44.1% / -8.0% / -10.5%). Title, verdict table and "bias, not size" bullet rewritten.
2. H2: code/posthoc_review.py -> posthoc_review.json. (a) Eligibility: with only FluSight-* and baselines excluded,
   NEU_ISI-AdaptiveEnsemble leads 2024-25 h1-h3 under first truth and h2-h3 under final truth; the leader changes
   only at h1 (NEU_ISI -> PSI-PROF_beta). Your text said "under both truths at h1-h3"; the data give h2-h3 under
   final truth. (b) Single-truth instability (B = 200): 2024-25 h0-h2 55-63% (first) and 59-65% (final) against
   first-vs-final 50-77%. The verdict line keeps the preregistered "Supported" but says it is not robust to the rule
   and not distinguishable from that instability.
3. Late first reports: `code/score.py late7` -> primary_late7.json drops location-weeks whose first version is > 7 days
   late (8.1% of 2023-24, 4.6% of 2024-25 scored forecasts): 6.4% (4.9-7.6%), H1 unchanged; the 2024-25 leader also
   changes at h0.
4. 2022-23 finality: 23% identical, 40% differ > 10% (median 0, mean +3.5%); re-scored against the new hub's latest
   values, 2022-23 reverses 0.5% (8 of 1,708), no leader change. In "What this does and does not show".
5. Numbers: lags 1.5 / 4.5 days; 186 dropped units (179 in 2023-24, MN 91, MA 88; 7 in 2022-23); SigSci-BECAM,
   FluSight-base_seasonal and the 2025-05-03 Metaculus-cp file stated.
G5 passes (39 rows), G6 passes.

Reply with the verdict and a one-line note per remaining issue, if any.
