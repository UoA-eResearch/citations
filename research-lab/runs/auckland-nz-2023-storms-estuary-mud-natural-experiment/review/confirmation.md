# Confirmation pass: auckland-nz-2023-storms-estuary-mud-natural-experiment

Reviewer: Fable 5.1, 2026-10-24. Checked commit 3dd86a7 (D5) against review/review.md finding by finding: the
report.md diff (fb30a30..3dd86a7), the D5 entry in deviations.md, the figures.py change and the regenerated F3. No
computation changed and none was re-run. Every new number in the revised text was checked against
review/reviewer_checks/*.out and the tables; all agree (87% / G* 1.3 of 13; 3.3% and 1.1% against 0.02-0.12%;
six harbours at +4 to +16 and seven at +2.6 or less; site median +2.6; harbour-clustered 2.3-7.0; +1.96 against
+1.45, difference 0.5; p = 0.21 at 4 pp; fade within the same 42 sites; 11 sites / 7 bottom-tercile; about 7
distinct exposures; Waikato sites and the +24.6; Auckland 2024 2.26 vs 1.10 site sets).

## Verdict: publish with edits (minor; mechanical; no further review pass needed)

## Findings

1. Exposure maps harvest, conclusions reframed: **fixed.** New title; summary bullet "so H1 and H2 did not test
   storm exposure" with the hotspot densities; plain terms rewritten ("really a test of land near harvest, not near
   slips", "could not test whether slips specifically fed the extra mud"); "What this shows" leads with "The exposure
   test did not test storm exposure". The optional pointer to the open landslide inventories was not added.
2. H2 is a two-site test; "would read as Refuted" struck: **partly fixed.** Summary and conclusions now carry the 87%
   share, "about 1 of 13" effective clusters, and "CR2 ... anti-conservative ... the wild bootstrap governs"; the
   Refuted sentence and "no dose-response under any exposure definition" are gone. But the H2 results paragraph
   "Why the two intervals differ" (report.md lines 157-159) still gives the old explanation ("with 13 harbours the
   bootstrap is sensitive to them"), which reads as if the wild interval were the unreliable one. One sentence aligns
   it: the identifying variation is 87% in Manukau (G* = 1.3), so CR2 understates uncertainty and the wild interval
   is the one to trust.
3. "Not unusual" / "normal wobble": **partly fixed.** Replaced everywhere by "largest in the 15-year series ... but
   2022 was already +1.45, so 2023 exceeds the pre-storm year by only about 0.5 pp" (summary, plain terms,
   conclusions). The 2022 fixed-effects placebo (+1.61, same estimator as H1) is recorded in D5 but not in the
   report's placebo bullet (line 136), where it belongs next to the 2015-2021 values; the summary compares the
   event-study +1.96 with fixed-effects placebos, which the +1.61 would make like-for-like.
4. Pulse concentrated; Waikato; regional site sets: **fixed.** "Almost everywhere / across the board" removed;
   "concentrated, not universal" with the harbour counts, site median and harbour-clustered interval; artefact checks
   cited; Waikato sentence corrected; the two Auckland 2024 site sets explained. (Placement of that explanation
   breaks a table; see new issue A.)
5. Plain terms contradicted "not ruled out": **fixed.** The "no large, lasting, exposure-graded mud signal" sentence
   is gone; "cannot rule out an effect of the size we looked for" stands, with "p = 0.21 at 4 pp" in the conclusions.
6. Drop-year-only rows = the 11 biennial Waitemata Central sites: **fixed** (line 144-145).
7. Effective exposure units and power: **fixed** ("about 7 distinct exposures, not 19"; the "power was about 50%"
   claim removed).
8. F3 title: **fixed.** "2023 mud change against the newly bare exposure (mostly harvest)"; PNG regenerated, caption
   unchanged and still consistent with primary.json.
9. Macrofauna label: **fixed** (LAWA's "Macrofauna - benthic health score" quoted, inference kept as inference).
10. Sea-mask caveat (Waikato River, Lakes Waikare and Whangape, Aka Aka): **fixed** in D5 item 5.

## New issues (all introduced or left by D5; each is a one-line edit)

A. **Broken table.** The note "The regional table's Auckland row (2024: +2.26) uses all Auckland sites ..." was
   inserted between the two rows of the pulse table (report.md lines 169-173), so the "bottom / middle / top
   tercile" row is orphaned and will render as a stray line of pipes. Move the note below the table.
B. **H2 results paragraph** still carries the pre-review explanation (Finding 2 above); align it with the summary.
C. **Residual "storm exposure".** The italic header still says "Each site was given a storm exposure" (line 4),
   which the new title contradicts; "an exposure" or "a bare-land exposure".
D. **"Reached most of Auckland's estuaries"** (line 185, the pulse "Reading") sits awkwardly beside "six harbours
   rose by 4-16 pp, seven by 2.6 or less"; "reached many of" or "most sites" would match the numbers.
E. Cosmetic: the macrofauna bullet has a broken line ("shows no / 2023 contrast", lines 198-200).

Nothing in the revised text overreaches in the other direction: the harbour counts, the "about 0.5 pp" margin, the
artefact-check list and the D5 numbers all match the reviewer outputs. With A-E made, the report is ready.
