# Deviations from plan.md

Timestamps are Pacific/Auckland, from `date`.

## D1 — 2026-10-20 20:56 NZDT — what the archive could give, and the basis of the realised series

Recorded after the workbooks were recovered and parsed, and before any forecast was paired with an outcome. The
plan anticipated each of these decisions; this records how they resolved.

1. **Vintages recovered: 1 January 2019 to 1 January 2024 (six), from seven workbooks.** MBIE's own site answers
   scripted requests with an Incapsula challenge, so the Internet Archive is the source. The archived asset holds
   the same file for every capture after August 2024, and the 2025 and 2026 releases (which MBIE announced in June
   2025 and May 2026) are published at URLs the Archive has not captured. **The two most recent releases are
   therefore outside this study**, including the one that cut 2P reserves 23% to 731 PJ. Six vintages clears the
   plan's abort rule of four, so H1 is scored.
2. **One capture per vintage.** Two captures carry the "as at 1 January 2021" workbook (2021-12-30 and
   2022-01-27, different sizes). The later, more revised publication is used. Summing both would have
   double-counted that vintage, and did in a first run before this rule was applied.
3. **Field-level realised production ends at 2023; the national series runs to 2025.** MBIE's field-level table
   (`Gas.xlsx`) was last archived with cached values in February 2025, covering 1974–2023. The gas web tables that
   replaced it are archived without cached values, so they carry no numbers. The national series continues to 2025
   through MBIE's energy overview. The field-level analysis therefore covers target years to 2023 and the national
   analysis to 2025, and each reports how many vintages contribute at each horizon.
4. **The national series is the net basis.** MBIE's energy overview line "Indigenous Production → Natural gas" is
   labelled gross petajoules, but it reproduces the sum of the published field-level **net** production to within
   0.05 PJ in every overlapping year (2019–2023) and its 2025 value, 102.4 PJ, matches the 102 PJ MBIE published
   for 2025 net production. It is used as the net series, and net is the headline basis, as in MBIE's own
   comparison of profiles with outcomes. Field-level results on the gross basis are reported alongside.
5. **"Others" is a residual.** MBIE publishes 18 named fields plus "Others"; the workbooks name more fields, and
   those without a published counterpart (Kauri, Radnor, Supplejack, Hanmer Springs) map to "Others". The
   preregistered sensitivity analyses excluding "Others", and excluding fields producing less than 0.5 PJ, are
   reported.

## D2 — 2026-10-21 17:13 NZDT — after independent review: every edition, and what changed

An independent adversarial review (`review/review.md`) re-extracted the draft's workbooks and confirmed its numbers
as computed, then found that the Internet Archive holds every edition of the workbook from 2014 to 2026, under
`.../Energy/petroleum-reserves/petroleum-reserves-1-jan-YYYY.xlsx`. That was verified here by an independent CDX
query before anything changed.

1. **D1's central scope claim was false.** `fetch.py` searched only the nz-energy-quarterly directory, never the
   petroleum-reserves one, and logged a failed archive query as "CDX gave nothing", the same message as an empty
   result. `plan.md` §3 preregistered *every retrievable* edition, so the full set is the preregistered analysis, not
   a new deviation. The fetcher now searches both directories, records any failed query in the manifest and exits
   non-zero, and keys captures by timestamp *and* URL, because several editions were archived in the same second and
   timestamp-only keys silently kept one per second.
2. **Four parser fixes for the older layouts**, each checked against the workbooks: year headers written as text
   (2017, 2018, 2026); gas reserves on a "Gas and LPG" sheet (2014–2016); categories labelled P90/P50/P10 (2014);
   and, on the 2014–2016 sheets, a gas-plus-LPG table followed by gas-only and LPG tables side by side — the parser
   now takes the gas-only table and confines itself to its columns (verified on starred fields: 2016 Kupe 1P 247.9 PJ
   gas-only, not 300.2 combined). Footnote markers ("Cheal(1)") no longer break field names. Every edition's
   first-year profile total equals its workbook's Total row; the 2017–2026 reserve rows are unchanged by the fixes.
3. **Rimu and Kauri.** MBIE publishes realised Rimu and Kauri as one series, so the workbooks' Kauri forecast now maps
   with Rimu rather than to Others; the draft's map split one field across two rows.
4. **The union rule as preregistered.** A field listed in an edition but blank for a year is now a zero forecast;
   the draft skipped such cells (for example the 2019 edition's blank Maui cells for 2022 and 2023).
5. **Revisions on harmonised fields**, summing the raw names that map to one field, with Others excluded; the draft
   keyed on raw names, so renamed fields dropped out.
6. **Preregistered outputs the draft omitted**, now reported: the three plan §5 validations (all reproduce within 2%),
   error by edition, the zero-forecast and zero-outcome shares, the 5% trimming sensitivity, and revisions in PJ.
   Deliverability against realised deliverability (plan §4) was not done and is not reported.
7. **Provenance.** Three inputs had no fetch record: MBIE's energy overview (which supplies every 2024–2025 outcome),
   MBIE's energy balance tables, and Gas Industry Co's production workbook. `fetch.py` now fetches the two MBIE files
   from exact archive captures (fresh downloads are byte-identical to the files used) and records the GIC file's
   source URL and hash.
8. **Results and readings.** H1 by its rule reads Supported, narrowly (three-year median +15.1% against a +15% bar)
   and not robustly; two preregistered sensitivities read Inconclusive. Following the lab's practice when a
   preregistered test is fragile (as for the FAERS study), the study's verdict tag is Inconclusive, with what the
   test reads stated alongside. The draft's readings that the gap "widens with horizon" and that "the schedule is
   optimistic, not the volumes" are withdrawn: with every edition the error peaks at one to two years, and 2P volumes
   have been revised down every year since 2022. A post-review sensitivity without the union rule's zero forecasts
   is reported, labelled as such.
9. **Smaller corrections from the review:** per-field figures are now given as medians and by volume; the national
   overview matches field-level net only from 2019 (2018 differs by 2.2 PJ); the two 2021 captures are identical
   rather than "more revised"; the parser's docstring and `national.csv` no longer call the series gross.
