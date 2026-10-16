# Confirmation pass — revision 9ba8dd3 against review.md

Reviewer: Fable 5.1 (the same reviewer). Checked: report.md, report.html, deviations.md D8, tiles.json, figures and
captions, footprint_grid.py / .json, review_response.py / .json, bell_eq1.json, firms_check.py / .json, the
test_analysis.py and model_targets.py diffs, and the git history 0ef15bd → 456de5a → 9ba8dd3 (response code
committed before its results, as before). New reviewer script: `reviewer_checks/check_confirm.py` (+ .log, .json).

## Verdict on the revision: **publish with edits** (6 edits; two are factual corrections to text the revision added)

All six must-fix items are addressed, and the author's recomputations match mine: hist `bet_Btot` ≡ `bet_Badult`;
GLS-AR(1) +0.198 (−0.225, +0.620); footprint grid identical row for row (model-on-same-cells +0.0322 / +0.0095 as I
had); Bell eq. (1) −13.8% (−9.3 to −19.9); H2 1990–2010 rows; detection-year range 2050–2117 (my 2049–2120, same
inputs, Monte Carlo difference); hinge power 0.082 vs my 0.060 (different design — theirs drops the linear trend
term — both at the test's size). The five should-fix and seven minor items are done. The verdict, tiles, plain
language, F4 and D-log now say what the evidence supports, and the report no longer implies the projection is
wrong. What remains is below; none of it changes a verdict or a headline.

### (a) Does the withdrawn footprint headline leave a trace? — Almost none.

Grepped report.md, report.html, deviations.md, tiles.json, all captions, figures.py and build_report_html.py for
"fleet moved", "not the fish", "had/have not moved east", "vanish", "simply spread", "moved, not". Hits only in
deviations.md lines 110 and 123–124 — the original D6/D7 entries, which an append-only log should keep — and line
143, the withdrawal itself. report.md, report.html body, tiles and F2–F4 captions are clean. plan.md predates it.

Two residuals:
- **F1 caption** (`results/figures/F1_shares.txt`, hence report.html) still says the density share "removes where
  the fleet is allowed to fish". That is the footprint-free reading the revision withdraws ("None of the observed
  series is free of the fleet's footprint"); report.md's own methods paragraph already dropped the phrase. Edit the
  caption to "(each fished cell weighted by catch per fishing day; it still carries the fleet's footprint)".
- **D2.2** still reads "a different quantity: 0.848 × (adult + young) … 0.73–1.00 by cell" with no pointer. The
  correction lives only in D8.3. Since D2 is the entry anyone preparing the SPC note will open, add a bracketed
  in-place marker: "[superseded — see D8.3: the file is the adult-only biomass]". Leave plan.md §4.1 as the frozen
  preregistration; the report's SPC paragraph already says the first description was wrong.

### (b) The closure-band reconciliation — the window explains the *numbers*, not the *reading*.

`check_confirm.py` §(b), outside-EEZ skipjack catch at 180–200°E, kt/yr (full table 2000–2021 in the log):

| years | 140–160°E | 160–180°E | 180–200°E |
| --- | --- | --- | --- |
| 2005–2009 (my window) | 32.6 | 86.5 | 19.9 |
| 2010–2014 (my window) | 10.7 | 12.0 | 21.3 |
| 2000–2009 (author's) | 34.1 | 73.3 | 16.7 |
| 2010–2019 (author's) | 8.6 | 16.9 | 60.9 |
| **2010–2013** | 12.1 | 11.9 | **13.6** |
| **2015–2019** | 6.5 | 21.7 | **100.6** |

The author's figures reproduce exactly, and yes, the difference between our tables is the window. But the
reconciliation offered — "a narrower window shows a smaller eastern rise" — understates what the yearly series
shows: **in the four years after the closure the eastern band gained nothing** (13.6 kt/yr against 16.7 before).
The eastern rise is a 2014–2019 phenomenon (51.9, 173.5, 62.1, 50.6, 73.2, 143.8 kt), tracks ENSO (r = +0.60 with
Niño 3.4 over 1990–2021; 173.5 kt in the 2015 El Niño, 143.8 in 2019), and begins the year after the WCPFC-level
closure lapsed (CMM 2008-01 was superseded on 5 Feb 2013; CMM 2012-01 did not carry the pocket closure for all
vessels). So the sentence "The closure's displaced catch went partly inside the EEZs and partly to the eastern
high seas" is not supported: at the time of displacement it went into the EEZs (inside-EEZ catch 660 → 970 kt/yr,
2005–09 → 2010–14) and nowhere else. **Edit:** keep the 2000–09 / 2010–19 table if you like, but add the 2010–13 and
2015–19 rows and rewrite the reading: displacement in 2010–13 was into the EEZs; the eastern high-seas rise is
later, ENSO-linked and post-dates the lapse of the Commission-level closure.

Two facts the report says it could not confirm can now be stated. PNA announced on 23 April 2010 (Majuro) that
**from 1 January 2011** the high seas between 10°N–20°S and 170°E–150°W (4,555,000 km²) would be closed to purse
seiners licensed to fish in PNA waters (pnatuna.com/node/102; also carried by SeafoodSource and Marianas Variety;
a Solomon Islands regulation implementing the 3IA commences 1 Jan 2011). Replace "around 2010–11 … I could not
confirm whether or when" with that. It applied to PNA-licensed vessels only, so the 2014–19 eastern catch is either
non-PNA-licensed effort or post-dates a relaxation: PNA's document list carries a 3IA amendment dated 13 June 2014
whose title refers to removing the high-seas closure. I could not open it; flag it as the thing to check, not as
fact. If it is what its title says, the 2014 onset fits it too.

### (c) The FIRMS comparison — parsing right, matching right, interpretation needs three corrections.

*Parsing.* CWP 7-digit codes: first digit 6 = 5°×5°; quadrant digit 1 NE, 2 SE, 3 SW, 4 NW; then 2-digit latitude
and 3-digit longitude of the corner nearest 0°,0°. The script's centre formula is correct under that convention.
Sanity: 82 domain cells, centres at lon 122.5–207.5°E and lat ±2.5…±17.5, catch-weighted mean position 160.3°E,
1.0°S — right where the fishery is. All 33,319 WCPFC SKJ purse-seine rows have 7-digit codes starting with 6, so no
1° records are mixed in. Single fleet code (NEI), single processing level, monthly rows by set type (LS/FS/OTH) —
no double counting. Decade ratios reproduce (0.576, 0.705, 0.734, 0.793).

*Matching by centre.* The 5° domain is 120–230°E against the 1° file's 120–228°E; the extra 2° strip carries
negligible catch. Latitude bounds coincide. Fine.

*Interpretation — fix these:*
1. **The 5° data are raised, and the file says so.** The GTA rows carry `measurement_processing_level = "raised"`
   and `measurement_type = "RC"`. The report's "may be raised to total catch" should read "are flagged as raised".
   The 1° file is unraised logsheet data with suppression; the 27% gap is therefore raising (logsheet coverage) +
   suppression + anything reported only at 5°. It does **not** bound suppression. The heading "The 1° file is
   missing a quarter of the catch" and tile 4 ("Catch the 1-degree file holds — 73% — of the 5-degree total") read
   as a suppression figure. Reword both: "the unraised, suppressed 1° file holds 73% of the *raised* 5° total; the
   suppression share of the gap is unknown". Consider dropping the tile — it is the least load-bearing of the four.
2. **120–130°E.** The 1° file has zero skipjack purse-seine catch at 120–130°E in every decade; the 5° data have
   144–578 kt per decade there (Indonesian and Philippine domestic fisheries, reported at 5° or nationally). That
   band is 21% of the whole shortfall and 5% of the 5° total. Excluding it, the 1° file holds 63% (1980s), 76%,
   78%, 82% (2010s); 79% over 1980–2021. Say so: part of the "missing quarter" is a fleet the 1° file never covers
   and the EEZ share never concerns.
3. **The 1980s shortfall is in the east.** In the 1980s the 1° file holds 68% of the 5° catch at 130–160°E but
   **11%** at 160–200°E (15.5 vs 140.9 kt over the decade). The early high EEZ share (0.72–0.95) rests on a file
   that under-represents the 1980s eastern catch; whether that catch sat inside Kiribati/Tuvalu/Marshall/Nauru
   waters or on the high seas is unknown, so the direction is still unknown — but the 1980s share is the part of
   the series least to be trusted, which strengthens the revision's point that the 1980s are the fleet's (and the
   file's) development decade. One sentence in the FIRMS paragraph.

### (d) Does the revision under-claim? — In two places; and it over-claims in one new one.

- **Under-claim 1:** "I could not confirm whether or when that eastern closure took effect" — it can be (above).
- **Under-claim 2 (optional):** on the footprints where the check has power (≥50–70%, model +0.03 to +0.04), the
  observed drift is at or above the projected rate in three of six rule combinations (+0.070, +0.137, +0.094) and
  indistinguishable from zero in three; **none points west** (the lowest is −0.010 ± 0.04). "The ones that could
  see it disagree with each other" is fair; "none of them points west, and three of six exceed the projected rate"
  is equally fair and more informative. Author's call.
- **Over-claim (new):** the closure-displacement reading in (b). Also the section title "SEAPODYM's historical run
  and the observations agree from 1990" — the 1990–2010 differences have intervals of ±0.4–0.5 pp/yr around
  points of −0.04 to +0.34; "point the same way from 1990" is what the table supports. And "8%, the false-alarm
  rate" → "8%, about the false-alarm rate (5%)".
- Everything else reads at the right altitude: "Supported, borderline"; "if anything it has risen" (both
  preregistered intervals and HAC 1–8 exclude or touch zero, GLS does not — fair); "Most of that is the fleet";
  the detection-year range with the pessimistic case explained; the plain-language paragraphs; the SPC paragraph.
  The direct closure evidence (outside-EEZ catch in the pocket longitudes falling ~80% in 2010 with nothing going
  east until 2014) justifies the confidence of "What moves the share: fishing rules and the fleet".

## Edits to make (then rebuild report.html — build_report_html.py switches STATUS to "revised after independent review" once this file exists)

1. Closure paragraph: add 2010–13 / 2015–19 rows; replace the displacement-east reading (b).
2. State the PNA eastern closure: announced 23 Apr 2010, effective 1 Jan 2011, PNA-licensed purse seiners,
   10°N–20°S × 170°E–150°W; flag the 13 June 2014 3IA amendment as unverified (b).
3. FIRMS: "are flagged as raised" not "may be raised"; reword heading and tile 4 (or drop the tile); add the
   120–130°E and 1980s-east sentences (c).
4. F1 caption: remove "which removes where the fleet is allowed to fish" (a).
5. D2.2: in-place "[superseded — see D8.3]" marker (a).
6. Wording: "point the same way from 1990"; "about the false-alarm rate" (d).

## Numbers recomputed in this pass

| Quantity | Revision | Recomputed | Note |
| --- | --- | --- | --- |
| Footprint grid, 15 rows | footprint_grid.json | identical to check_footprint.py §(a) | model-on-cells 0.5: +0.0322, 0.8: +0.0095 |
| GLS-AR(1) | +0.198 (−0.225, +0.620), ρ 0.58 | same | |
| H2 1990–2010 density diff | −0.041 (−0.496, +0.322) | obs +0.180 (HAC −0.126, +0.485), model +0.221 | consistent |
| Hinge power to 2021 | 0.082 | 0.060 | design differs (trend term); both ≈ size |
| Detection-year range | 2050–2117 | 2049–2120 | same inputs, MC noise |
| Bell eq. (1) | −13.8% (−9.3, −19.9) | −13.8% (−9.3, −19.9) | |
| Outside-EEZ 180–200°E, 2000–09 → 2010–19 | 16.7 → 60.9 kt/yr | 16.7 → 60.9 | **2010–13: 13.6; 2015–19: 100.6** |
| corr(180–200°E outside-EEZ catch, Niño 3.4), 1990–2021 | — | +0.60 | |
| 1°/5° ratio by decade | 0.58/0.71/0.73/0.79 | same | excl. 120–130°E: 0.63/0.76/0.78/0.82 |
| 1°/5° at 160–200°E, 1980s | — | 0.11 | 15.5 vs 140.9 kt |
| 120–130°E in the 1° file | — | 0 kt, every decade | 5°: 144–578 kt/decade |
| GTA processing level | "may be raised" | `raised`, type `RC` | in the parquet |
| PNA eastern closure | "could not confirm" | effective 1 Jan 2011, announced 23 Apr 2010 | pnatuna.com/node/102 |
| report.html date | 2026-10-16 (from git) | correct | |
| Trace grep | — | clean except F1 caption, D2.2 unmarked | |
