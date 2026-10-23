# Deviations from the preregistration

## D1 — 2026-10-23 17:01 NZDT — the panel checks (results/tables/panel_checks.json), before any outcome is aggregated

- **The overlap check passes.** In 2014–2019, the DPP3 and DPP4 model files agree exactly on annual raw unplanned
  SAIDI for all 96 distributor-years. The splice is used as planned.
- **Centralines is dropped.** The DPP4 file's Unison equals Unison alone in the DPP3 file, not Unison plus
  Centralines.
- **2025 is not used, by the plan's own rule.** The 2025 disclosure's unplanned SAIDI is within 5% of the disclosed
  Class C SAIDI for only 20 of 28 distributors. Top Energy, Vector, Firstlight and Unison differ by 68–130%, likely
  because other interruption classes are included. So:
  - the H1 and H2 trend window is 2014–2024;
  - the H3 assessment years are 2021–2024.
- **A correction to plan section 4.** "The cap in its first year: 2025, the first DPP4 assessment year" is an error.
  DPP4's first assessment year is April 2025 – March 2026, which is not in the data. That descriptive item is dropped.

## D2 — 2026-10-23 17:05 NZDT — a date-parsing bug, found by the validation gate (before any hypothesis statistic)

- **The bug.** In the DPP4 model file, 115,643 of 220,880 start times are text in day-first "dd/mm/yyyy hh:mm" form;
  the rest are Excel dates. The first panel build read the text month-first, which put many interruptions on the
  wrong dates. The gate failed: Network Tasman's and Top Energy's boundary values were 11% off.
- **The fix.** Text is now parsed day-first, as the Commission's `as_date()` does. Every start time must fall in
  its recorded disclosure year; at most 0.1% may not.
- **After the fix the gate passes:**
  - all 16 DPP4 boundary values exactly;
  - DPP4 targets and uncapped limits within 0.6%. The remainder is the R model's UTC-date day sums for the SD.
  - all 17 DPP3 boundary values within 0.15%.

  The overlap check, which uses the files' disclosure-year column, was not affected.
- **DPP3 limits** reproduce within 1% for only 8 of 17 distributors (Aurora and Vector are +13%, Centralines −16%,
  Nelson −11%). The determination's limits therefore include something beyond target + 2 SD on the reference
  window. As planned, H3 uses limits recomputed under each rule. Compliance against the determination's own DPP3
  limits is reported alongside.
