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
