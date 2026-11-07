Confirmation pass for seismology-geophysics-dynamic-triggering-strain-test (/mnt/citations/research-lab/runs/seismology-geophysics-dynamic-triggering-strain-test).
The first review (review/review.md, fix first, 3 findings) is addressed in deviations.md D2. Check each fix and give a
final verdict (publish / publish with edits / fix first / do not publish); append a "## Confirmation pass" section to
review/review.md. Same rules as before (write only under review/, no ~/.config, no pip installs, <= 4 processes, no
GPU, data/ untrusted).

Where each finding went:
1. Comparable arms: code/comparable.py -> results/tables/comparable.json re-applies analyse.summarise (same rules and
   bootstrap seed) to classes of real pairs. Corrected primary = the null's own exclusion rule applied to real
   triggers: 68 triggers, 43,771 pairs, all +0.000 (-0.008 to +0.008), H1 Inconclusive, H2 Inconclusive. Clean windows
   109 triggers / 72,189 pairs +0.004 (-0.002 to +0.011) (you had 105 / 70,010; my post window runs from the origin,
   not from post0, to the post window's end). Post-contaminated -0.013 (-0.019 to -0.006); contamination share by
   strain quintile 16% -> 33-36%. Title and verdict rewritten; the preregistered "H2 Refuted" stays beside it.
2. Stations: title and verdict say about 1,500 long-running stations (16% of 9,336; median 212 valid pseudo-triggers);
   station-map caveat added.
3. Detectability: recall (46%; 52% at M >= 3), the doubling-in-a-day size, and instantaneous triggering untestable
   are in the verdict; title scoped to day-scale rises.
G5 passes (49 rows), G6 passes.

Reply with the verdict and a one-line note per remaining issue, if any.
