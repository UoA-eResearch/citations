# Deviations from plan.md

## D1 — 2026-10-28 16:48 NZDT — data-assembly fixes, before any model was fitted or any rain–callout relationship inspected

1. **A physical-plausibility screen for rain records,** shared with the HIRDS lead (its D6). A record counts as
   missing if either:
   - it exceeds 50 mm in an interval of 15 minutes or less, or 150 mm in one of an hour or less; or
   - it belongs to a run of 24 or more identical values of at least 2 mm (a stuck sensor).

   Found while building this panel: the largest daily 6-hour value was 39,332 mm. Plan section 2's code-based rule
   does not catch values coded 0.
2. **One region per suburb.** RegionalCouncilName is often blank (most rows in 2018/19), which split one suburb into
   two panel units. A suburb's region is now its most frequent non-empty value.
3. **Reading the files** (build fixes, no analytic content):
   - the 2024/25 file is Windows-1252 and writes day-first dates;
   - the parser now uses explicit formats, because the default guessed month-first for ambiguous dates.
4. **Sensitivity Q** uses the HIRDS index depth *M* of the gauge that Q itself assigns, which can differ from the
   primary gauge.

## D2 — 2026-10-28 17:14 NZDT — geocoding and suburb keys fixed after the G4 audit; a first analysis run stopped unread

**What the G4 geocoding audit found** (gauge council against FENZ regional council):
- **35 suburbs matched to the wrong place.** A FENZ name with a single gazetteer entry was taken even when that entry
  was elsewhere: Browns Bay in Porirua went to Auckland's Browns Bay, Cable Bay in Nelson to Northland's, Dalefield
  in Queenstown to the Wairarapa's.
- **One suburb split into several panel units.** Spellings and TLA strings vary between years ("Queenstown",
  "QUEENSTOWN-LAKES DISTRICT", or blank), so 10,151 keys described 3,629 places.

**Fixes** (no outcome involved):
- A suburb is its normalised name (case, macrons, punctuation) plus its regional council. Blank councils are filled
  from the same suburb and TLA, then from the name if it occurs in one region only.
- A gazetteer candidate is accepted only if its nearest gauge within 10 km belongs to the record's council or a
  neighbouring one. Candidates with no gauge within 10 km stay possible; they cannot enter the panel anyway.
- **Result:** 954 panel suburbs, 2.65M suburb-days, and no distant mismatch. The geocoding audit and the window
  audit (30 suburb-days, grid within 0.6% of the exact maximum) are in `results/tables/g4_*`.

**The stopped run.** The first analysis was started at 16:5x on the flawed panel. It was stopped at 17:11, when the
audit result came in.
- Its `primary.json` had been written at 17:04, but its printed output was buffered and nothing was displayed.
- The file was moved unread to `results/tables/v0_unseen_flawed_geocoding/` (sha256 begins edd777ce0bc1a276).
- It will be opened only after the corrected result is final, to report what the fixes changed.

## D3 — 2026-11-03 12:15 NZDT — rain re-screened with the HIRDS lead's corrected screens, before review

**Why.** FENZ's daily rain (`rain_daily.py`) reuses the HIRDS lead's `physical_bad` screen. During the HIRDS
review and confirmation pass, that screen gained a window test (any 5-minute total above 40 mm or 60-minute total
above 150 mm drops every record in the window), negative increments became faulty records, and a NaN that silently
disabled the window test was fixed (HIRDS D7). FENZ's results had been built with the old screen, so they were
rebuilt, unchanged in every other respect, before the independent review.

**What changed.** 918 more suburb-days lost their last usable gauge within 10 km (159,979 dropped, 2,653,907 kept);
all 918 fell in the held-out year (335,539 test suburb-days), consistent with the window faults found in the HIRDS review lying in recent records. The held-out flood count is unchanged (64).

| statistic | before | after |
|---|---|---|
| H1 | Supported | Supported |
| D_LL (×10⁻⁵, 95% interval) | 3.9 (0.6 to 8.3) | 3.7 (0.8 to 7.6) |
| S | 1.076 | 1.073 |
| regions where rarity wins | 7 of 9 | 7 of 9 |
| without 25–30 June 2025 (post hoc) | 0.9 (−0.5 to 2.6) | 1.3 (−0.1 to 2.9) |
| 1 h: S | 0.986 | 1.001 |
| outcome V2: S | 0.953 | 0.999 |

The other secondaries move by 0.01 or less in S. The report quotes the new numbers throughout.

## D4 — 2026-11-03 13:10 NZDT — fixes from the independent review (verdict: fix first)

**1. One unit per place** (review finding 1). Places were keyed by normalised name plus council, so a place coded under
two councils (mostly at council boundaries: Auckland and Waikato, Manawatū-Whanganui and Wellington) or under two
spellings stayed split. 107 of the 954 panel units sat on 53 shared gazetteer points, with identical rain, and the
twin of every flooded unit recorded no callout. `panel.py` now merges units on the same gazetteer point into the one
with more exposures and sums their callouts per day. Across all geocoded records, 159 were merged (2,768 → 2,609
places); the panel has 900 places and 2,506,001 place-days (316,853 held out). Flood counts are unchanged: 765
training and 64 held out.

**2. Region from the TLA** (finding 5). A unit's region is now its TLA's modal council in the FENZ rows, not the
record's own council, which FENZ sometimes miscodes (101 geocoded units changed). The geocoding audit gained a
judgeable denominator: a random 100 panel places were reverse-geocoded with OpenStreetMap Nominatim. All 100 fall in
their recorded region. The 30 whose OSM territorial authority differs are 29 Auckland local-board names and Ōtaki,
which lies in Kāpiti Coast District (`g4_osm.csv`).

**3. Optimiser tolerances** (finding 4). L-BFGS-B ran at scipy's default tolerances on a mean log-loss of order 10⁻³
and stopped after 8–26 iterations. Tolerances are now ftol 1e-15 and gtol 1e-10. All 21 fits report success, with at
most 1,277 iterations and a largest gradient of 9×10⁻⁹ (`primary.json: fits`).

**4. Reviewer-prompted post hoc: depth plus climatology** (finding 2). The depth model with log M6 as an additional
covariate matches the rarity model on the held-out year (D+M minus R: 0.4×10⁻⁵, −0.6 to 1.7×10⁻⁵; S for D+M 1.064).
The report now says that rarity's gain over depth is the place's climatology, and that the ratio is one way to encode
it.

**5. Gates.** G2 gained two stages, `gauges` (443 attempted, 5 without a HIRDS depth or location) and `places` (the
merge). G3 gained code for the water-year invariant (`g3_invariant.py`) and three unit traces, from FENZ counts and the
raw gauge records to both models' fitted probabilities (`posthoc.json: traces`). Report wording was fixed per finding
7, along with the informative-missingness limit (finding 3: 17.6% of flood place-days have no usable gauge, against
5.6% of all place-days; 26% on 27 January 2023) and a note on the spline knots (finding 6).

| statistic | after D3 | after D4 |
|---|---|---|
| H1 | Supported | Supported |
| D_LL (×10⁻⁵, 95% interval) | 3.7 (0.8 to 7.6) | 4.0 (0.9 to 7.8) |
| S | 1.073 | 1.072 |
| regions where rarity wins | 7 of 9 | 7 of 9 |
| places / held-out place-days | 954 / 335,539 | 900 / 316,853 |
| without 25–30 June 2025 (post hoc) | 1.3 (−0.1 to 2.9) | 1.3 (−0.2 to 3.0) |
