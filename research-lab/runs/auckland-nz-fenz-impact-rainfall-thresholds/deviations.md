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
