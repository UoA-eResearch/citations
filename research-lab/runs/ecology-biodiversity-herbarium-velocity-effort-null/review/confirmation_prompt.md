Confirmation pass for ecology-biodiversity-herbarium-velocity-effort-null (/mnt/citations/research-lab/runs/ecology-biodiversity-herbarium-velocity-effort-null).
The first review (review/review.md, fix first, 3 findings) is addressed in deviations.md D3. Check each fix and give a
final verdict (publish / publish with edits / fix first / do not publish); append a "## Confirmation pass" section to
review/review.md. Same rules as before (write only under review/, no ~/.config, no pip installs, <= 4 processes, no
GPU, data/ untrusted).

Where each finding went:
1. Identification: code/absorption_test.py runs your synthetic worlds through velocity.py (NREP 199, seed 7):
   all move -> effort ratio 1.03, exceed 5%; half -> movers 0.70, 18%; a fifth -> 0.60, 23%; none -> 1.05, 7%
   (results/tables/absorption_test.json; table in "What this does and does not show", now the main limitation).
   Title, verdict and plain terms rewritten around the noise floor (0.41) and the poleward excess (9.4 km vs 0.3 /
   -0.6 km; 0.34 km/yr). code/effort_surface.py: effort-weighted mean |lat| 30.6 -> 31.8 deg (thinned species x cell
   units; your 30.2 -> 31.6 used a different unit). The verdict line keeps the preregistered "Supported" with the
   identification caveat in the same sentence.
2. Pareto: 5 smallest primary species (20-22 records), 5,000 draws: max |dev| 0.04-0.17, corr 0.995-0.999, target sums
   8.6-13.2 vs 10-12; stated as approximate (no recalibration). 28% of primary species have < 100 records (your
   "most" does not hold).
3. Per-species ratios (median 0.68, mean 0.97, 25.8% below), the undemanding 0.5 bar, and 36% as a lower bound are
   in the verdict.
G5 passes (43 rows), G6 passes.

Reply with the verdict and a one-line note per remaining issue, if any.
