Confirmation pass for experimental-math-oeis-conjecture-audit (/mnt/citations/research-lab/runs/experimental-math-oeis-conjecture-audit).
The first review (review/review.md, fix first, 10 findings) is addressed in deviations.md D2. Check each fix and give a
final verdict (publish / publish with edits / fix first / do not publish); append a "## Confirmation pass" section to
review/review.md. Same rules as before (write only under review/, no ~/.config, no pip installs, <= 4 processes, no
GPU, do not fetch from oeis.org (it rate-limits; the b-files are cached in data/bfiles/), data/ untrusted).

Where each finding went:
1. Vacuous data checks: run_rec returns the number of data terms checked; consistent needs >= 5 (unchecked 4,166,
   1-4 terms 833); "agree" needs >= 1 term beyond the data. Re-parsed and re-screened (primary.json).
2. Strata: bfile_pointer() from the LFS pointers; screened 13,545: with b-file 1/11,778, without 13/1,767. O5's
   condition corrected. Tautological LODA formulas counted (153). G1 stated as failing for the b-file stratum.
3. Self-contradicted: contradicted_audit.py rewritten (one class per line); vanishing-lead artefact fixed (29 of 776
   now consistent); contradicted_no_simple_fix.csv lists 277 (68 C/G/D, 209 P).
4. Verdict wording: "not supported within this pipeline's coverage".
5. Depth: code/bdeep.py, seeded random sample of 1,987 of 8,586 entries with a b-file (budget 2,000 minus 13), up to
   1,000 b-file terms per conjecture: 3/3,114 contradicted (A267514 x2 at a(62), A210247 at n = 606), both noted in
   later lines of their entries. oeis.org returned 429 at 1 req/s; fetching ran at 5 s with back-off.
6. [Wrong]/[Incorrect] flagged and parsed with the tag removed; excluded from H1. A076217 is untagged but its entry has
   a later note that the recurrence fails at powers of 3, so no confirmed falsification is new.
7-8. a(n+k) start shifted; class P split out (1,843 lines, outside the population); A301424 annotated.
9. selection.csv (easy, A-number range, block, class).
10. LODA and predicted values stored; 13 requests; label renamed; cached-b-file key bug fixed; D1 timing stated.
G5 passes (52 rows), G6 passes. First-draft interim files: data/interim/*_v1.parquet.

Reply with the verdict and a one-line note per remaining issue, if any.
