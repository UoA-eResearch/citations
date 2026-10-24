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

## D3 — 2026-10-25 03:05 NZDT — fixes after the independent review (review/review.md, "fix first")

1. **ICP weights** (finding 1). The ICP-count proxy had corrupt values: Alpine 2017 at 327,876,213, which took 99.5%
   of that year's national weight, and The Lines Company 2020 at 2,020. A plausibility guard now replaces values
   outside 1/3 to 3 times the distributor's median with linear interpolation within the distributor. Five
   distributor-years are flagged (`results/tables/icp_flags.json`). Every H1/H2 number, the national index and F1 are
   recomputed.
2. **2025** (finding 2). D1's identification check summed sub-network rows with the "All" row of the disclosure
   table. Corrected to the "All" row, 26 of 28 distributors are within 5% and the plan's rule returns usable, so **D1
   is withdrawn** and the preregistered windows apply: 2014–2025 for H1/H2, 2021–2025 for H3.
   - Horizon's 2025 disclosure name ("Horizon Networks") is mapped.
   - Top Energy 2025 is excluded: its unplanned total includes Transpower-caused interruptions it cannot separate.
   - MainPower's 164 off-year rows are outside the study set.
   - The national index is computed over available distributor-years.
   - A recording-basis check (2025 against 2024) is added: median count ratio 0.93, SAIDI per interruption 0.86.
3. **The DPP3 limit mismatch** (finding 3, replacing D2's "unexplained residual"). It is the Commission's ±5%
   inter-period target cap (DPP3 reasons, Attachment J, Table J1): target × (1 + J1 adjustment) + 2 SD reproduces
   the determination's limits to 0.02%. The validation gate now also compares the uncapped limits with the Stata
   output (all within 0.052%).
4. **H3** (findings 4, 10). Added:
   - a variant with IEEE major-event days excluded rather than capped (4 differ);
   - the reference days over the IEEE threshold (0 for Invercargill, Nelson and Network Tasman: the rule is inert
     there);
   - margins;
   - the boundary ratio range, corrected to 1.3–25×.
   Wording "decides" is softened to "can change".
5. **The decomposition** (finding 5). Both orderings and the Shapley average are reported.
6. **Descriptives and wording** (findings 6–9):
   - the median published uncapped limit change is −1% without Aurora (with Aurora, +2.4%);
   - DPP3's rule is an annual contravention, not a two-of-three-year rule;
   - the Table E3 reproduction is cited as the assessment-mode validation;
   - H1's sign-blind rule is explained for the primary, no-2023 and SAIFI cases;
   - the title is narrowed to what is shown.
