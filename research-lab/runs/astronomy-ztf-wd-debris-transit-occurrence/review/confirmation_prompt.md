Confirmation pass for astronomy-ztf-wd-debris-transit-occurrence (/mnt/citations/research-lab/runs/astronomy-ztf-wd-debris-transit-occurrence).
The first review (review/review.md, publish with edits, 6 findings) is addressed in deviations.md D2. Check each fix and
give a final verdict (publish / publish with edits / fix first / do not publish); append a "## Confirmation pass"
section to review/review.md. Same rules as before (write only under review/, no ~/.config, no pip installs, <= 4
processes, no GPU, at most a handful of IRSA queries, data/ untrusted).

Where each finding went:
1. Floor: tiered lower rates (code/posthoc_review.py -> posthoc_review.json): confirmed-only 4.2e-5 (0.9-12e-5),
   + Guidry candidates 7.0e-5, all published 2.1e-4; title and text say "rate implied by published systems and
   candidates", not a floor.
2. i band: detect.py FILTERS = zg,zr (preregistered); detect/variables/inject/occurrence re-run: 108,493 eligible,
   1,006 flagged, 970 candidates, 15/18 known, lower 2.1e-4, upper 1.38e-2, H1 Inconclusive. As-run outputs kept as
   results/tables/withzi_*. (Matches your 108,493 / 1,006.)
3. SBSS 1232+563: a fresh query keeping all objects and flags gives 35 good epochs after MJD 60068 (5 objects, two
   fields); the stored light curve has 29 good epochs in 60068-60848 (your c6 saw none there; please re-check against
   data/lc_v2/shard_0017.parquet). The miss is put down to sparse sampling: one qualifying low bin, rule needs two.
4. G4/calendar: g/r coincidence 1,728 of 1,836 low bins (94%, both bands > 2.5% low; your definition gave 71%);
   calendar: 454 of 769 long-dip candidates in the ten most crowded windows, 140 in June 2020; quiet stars 0.1-0.7%
   faint there. In plausibility.md and the verdict.
5. Verdict states Supported/Refuted were all but unreachable by design.
6. G5 rows rewritten; row 3 now discloses the post-detection ID correction.
G5 passes (48 rows), G6 passes.

Reply with the verdict and a one-line note per remaining issue, if any.
