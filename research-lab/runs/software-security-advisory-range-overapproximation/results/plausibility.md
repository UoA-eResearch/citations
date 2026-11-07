# Plausibility (G3)

Hand traces (`code/handtrace.py`, `results/tables/handtrace.json`) re-download releases and count the fix's deleted
lines by plain substring search on whitespace-stripped text, independently of the pipeline's normalisation:
- **Tight** (GHSA-h3h8-3v2v-rg7m, gradio): the earliest in-range release (4.16.0) contains 2 of 2 deleted lines.
- **Over-approximated** (GHSA-m6hv-x64c-27mm, copyparty): release 0.2.3 contains 0 of 32 deleted lines, although
  its files of the same names exist. The first present release (1.19.17, index 349) contains them. The G4 audit shows
  that cases like this can still be code in an older form.
- **Undetermined** (GHSA-2qjp-fg8c-g878, npm): 2 of 3 deleted lines in the earliest release, between the thresholds.

Invariants:
- Classified advisories have at least one present release.
- Tight ones are present at index 0.
- Corrected pairs never exceed declared pairs.
- Coverage counts reconcile: 800 = 411 classified + 300 undetermined + 79 no signature + 10 no diff.
