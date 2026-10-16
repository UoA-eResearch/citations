# Independent review: "Does New Zealand's geothermal fleet hold its output?"

Reviewer: Claude (Fable 5.1), adversarial review of the pre-review draft at commit 2b39db6. Date: 2026-10-17.
Everything I ran is under `review/reviewer_checks/` (scripts listed at the end). No file outside `review/` was changed.

## Recommendation: publish with edits

The preregistered verdicts hold. I reproduced every segment, field and fleet number in `primary.json` to three
decimals from `field_monthly.csv`, recomputed eight field-month P95 values straight from the raw EMI CSVs with
independent code (all exact), refit every segment with three other error models, and re-ran the fleet estimate under
several defensible alternative segmentations. H1 stays Supported (worst lower bound −0.33%/yr, far from −1.5) and H2
stays Refuted in every case. The git record is clean: the analysis code is unchanged since the plan commit, the only
pre-results code change is the D2 date fix, `data/processed/` was created seven seconds after the plan commit, and
`supplementary.py` ran three seconds after it was committed.

What does not hold is the draft's framing. Three things must change before publication, none of which touches a
verdict:

1. **"Flat" is not robust, and "upkeep has paid for it" is not shown.** The fleet interval contains zero only
   because two commissioning ramps leak into segments and a documented capacity change (Poihipi's connection to the
   Wairakei steamfield, 2006–2011) was not cut. Handling those gives −0.09 to −0.17%/yr, with an interval that
   excludes zero in the last case; the last decade is −0.44. The within-segment positive trends that offset Mokai's
   decline are plant uprates and commissioning artefacts (Kawerau KGL 2009–14, Ngā Tamariki 2013–14, Te Huka
   2011–12, Poihipi 2006–11), not demonstrated make-up drilling. The study has no drilling data. The abstract and
   the plain-language summary assert a mechanism the data cannot support.
2. **The data do not cover every geothermal plant, and the report says they do.** Te Ahi O Maui (25 MW, 2018) is
   not identifiable in Generation_MD before 2025-09; GDL (8 MW, 2008), TOPP1 (21 MW, 2013) and the Kawerau binary
   are absent or buried; Ngāwhā OEC4's 31.5 MW does not appear until 2024-01, three years after commissioning. The
   Kawerau "field" is KGL plus fragments whose identity I could not pin down. The plan's "covers every geothermal
   plant" and the report's field-as-unit logic for Kawerau need correcting.
3. **The Ohaaki post-hoc numbers are over-read.** The −10.4%/yr is fixed by the chosen endpoints (peak year to
   return-to-baseline year), so "three times faster than MBIE's 3%" is arithmetic, not a finding. The attribution
   to a drilling programme rests on an undated NZGA sentence that gives a different level (~50 MWe); Contact's own
   2013 account (via Kortright, WGC 2015) says output has been "around 40–45 MW net since 1999" and does not
   mention the 2007–09 episode at all. The cause of the 2007-11 to 2009-08 plateau at 60–68 MW is undocumented.

The rest of the issues below are smaller: a mis-stated capacity (KGL 117 vs 107 MW), intervals that are nominally
95% but cover ~87–90% for the high-autocorrelation segments, an inverse-variance combination that gives a 5.5 MW plant
28% of Kawerau's weight, P95's blindness to multi-month single-unit outages, and several wording points.

## Numbered issues

Severity: **A** must fix before publication; **B** should fix; **C** wording or nice-to-have.

### A1. The headline "flat, consistent with zero" depends on two commissioning ramps and one uncut capacity change
*Location:* report.md abstract ("has not declined", "That is flat"), "In plain terms", "What this does and does not
show" §It shows, "For planning".
*Evidence (reviewer_checks/segment_sensitivity.py):*
- Te Mihi's ramp outlasted the 6-month exclusion. Wairakei field P95 was 322–331 MW in 2014-04..09 while Te Mihi
  rose 152 → 167 MW and the Wairakei station swung 126–165 MW; from 2014-12 the field settled at 337–349. Starting the
  segment at 2015-01 instead of 2014-04 moves the Wairakei 2014–26 trend from −0.18 (−0.49, +0.13) to
  **−0.40 (−0.61, −0.19)**. Any start from 2014-10 to 2016-01 gives −0.40 to −0.47.
- Ngā Tamariki ran at 72–78 MW P95 for 2014-01..09 and exactly 86–87 MW every month since 2014-10. Its +0.46%/yr is
  entirely the early low; from 2014-10 the trend is **+0.05 (−0.09, +0.18)**.
- Poihipi was "connected with the main Wairakei steamfield in 2006 and gradually brought ... up to full capacity in
  2011" (NZGA Wairakei page; FGGS: "run jointly ... with an interconnected steam supply system"). Poihipi's P95 went
  29 → 49 MW in 2006-10 and 29 → 51 across 2006–2012. This is a documented capacity change of a reporting plant and
  by the plan's own rule should have been cut; it was missed because the plan used only FGGS Table 2. It is the
  whole of the Wairakei 2006–13 segment's +1.19%/yr.
- Kawerau KGL rose 97 → 105–108 MW over 2009–2014 (the plan's 2017 "rerate" is not visible; see B3). The 2008–16
  segment's +1.38 (+0.73, +2.03) is +0.06 (−0.14, +0.27) from 2014-01.

Fleet, same model and weights: as reported **+0.02 (−0.18, +0.22)**; Wairakei from 2015-01 **−0.09 (−0.27,
+0.09)**; plus Ngā Tamariki from 2014-10 **−0.13 (−0.29, +0.02)**; plus dropping Wairakei 2006–13 **−0.17 (−0.33,
−0.02)**. H1 Supported throughout. Equal-weights and last-decade sensitivities already point the same way (+0.15 is
the only one more positive, and it up-weights the four small fields with artefact-driven positive trends).
*Fix:* Keep the preregistered estimate as the verdict number, but (i) add these as a labelled post-hoc sensitivity
(code in supplementary.py, a row in the sensitivity table, a sentence in Results); (ii) rewrite the abstract to
"between flat and about −0.2%/yr depending on how commissioning ramps are handled, −0.4%/yr over the last decade;
well inside the preregistered bar"; (iii) delete or qualify "That is flat, as New Zealand's scenario models assume"
and "26 years of metering say ... the offset has worked".

### A2. "Upkeep, not the reservoir, is what keeps the fleet level" and "across the fleet it has been [paid for]" are not supported
*Location:* "In plain terms" last two paragraphs; abstract last sentence; "Post hoc" last paragraph ("fleet-wide,
operators have offset it").
*Why:* The study measures output, not drilling. The offsets identified in A1 are turbine/steamfield uprates,
interconnections and commissioning. The one place the report infers drilling (Ohaaki 2007–08) is unverified (A3).
Also "Only one field, Mokai, shows a steady decline" is false for the last decade, where Wairakei is −0.52 (−0.78,
−0.27) and Ohaaki since 2019 is −1.3 (−1.9, −0.7) (the report's own numbers).
*Fix:* Replace the mechanism claims with what is shown: "Across the eight fields the net change in achievable output
over 2000–2026 is close to zero. That net is made of a steady decline at Mokai, a slow decline at Wairakei since
2015 and at Ohaaki since 2019, and increases at Kawerau, Poihipi and the newer binary plants that are mostly plant
and steamfield upgrades. Whether make-up drilling has kept pace cannot be read from metering." Drop "Only one
field".

### A3. Data scope: Generation_MD does not cover every geothermal plant; Kawerau is not a field in these data
*Location:* plan.md §3 ("covers every geothermal plant"), report "How it was done" §Data and §The field is the unit,
Results table row "Kawerau", limitation 4.
*Evidence (reviewer_checks/audit_raw.py and plant_monthly.csv):*
- Every geothermal-coded (POC, Gen_Code) in all 321 files is one of 19 keys, all mapped; Fuel_Code "Geo"/"GEO"
  both handled; no geothermal plant hides under another fuel code (the only name hit, Matahina, is hydro). So the
  mapping is complete *for what is in the files*. What is not in the files:
- **Te Ahi O Maui** (25 MW, commercial Oct 2018). The EMI register puts it at KAW0111 from 2017-12-31 to
  2025-09-03, then KAW2201. In Generation_MD nothing new appears at Kawerau in 2018–19. From 2020-01 a series
  "kawerau" at KAW0111 with network code **HEDL** (Horizon Energy, the Eastern Bay lines company) runs at 13–15 MW
  P95, drops to 7.6 in 2025-09 and is 0.0 from 2025-10, exactly when "kawerau_(topp2)" (network code TAOM) appears at
  KAW2201 at 25.6 MW (TAOM's size) and then 73–77 MW (TAOM + TOPP2's 49 MW). So either the HEDL series is TAOM's
  *net* injection through a distribution network (half its nameplate), or it is GDL (8–9 MW) plus the old Kawerau
  binary (4 MW) and TAOM is absent for 2018-10..2025-08. I could not resolve which; neither is "plant output".
- **GDL** (8 MW bottoming binary, 2008), **TOPP1** (21 MW, 2013) and the **Kawerau binary** (4 MW) never appear as
  series; "kawerau_geo" (BOPE, 5.5 MW) stops in 2008-03 and nothing but KGL is reported at Kawerau from 2008-04 to
  2019-12. "norskeskog" (KAW0112, 28–37 MW, from 2020-01) is a mill net-export figure whose composition is unknown.
- **Ngāwhā OEC4** (31.5 MW, commissioned Dec 2020/Jan 2021): Ngāwhā's P95 stays 24–25 MW through 2023-12 and jumps
  to 55–58 MW in 2024-01. Three years of OEC4 output are not in Generation_MD. (Not used by the study, but it shows
  the embedded-generation gap is systematic, not a Kawerau quirk.)
- Kawerau's consents are held by four groups (FGGS Table 5); fluid is not a single shared take, so the field-as-unit
  argument (made for Wairakei) does not transfer.
*Fix:* Correct plan §3's claim in deviations (D4) and in the report; label the Kawerau row "Kawerau (KGL; small
embedded plant from 2020)"; add to limitation 4 the specific plants missing and the HEDL ambiguity; state that the
Kawerau 2020–25 segment includes net-injection series. Consider dropping the 2020–25 Kawerau segment from the
primary estimate as a sensitivity (its weight is small; the field trend barely moves).

### A4. Ohaaki post hoc: endpoint-determined slope and unverified attribution
*Location:* abstract ("jumped by two-thirds ... consistent with the well-investment programme ... ran down at about
10% a year"), "In plain terms", Post hoc §Ohaaki and last paragraph, F2's orange marker, F1 caption.
*Evidence:*
- Same model, other windows (segment_sensitivity.py): 2008–13 **−10.4**; 2008–12 −12.1; 2009–13 −9.8; 2008–16
  −5.1; 2008–26 −1.7 (−3.1, −0.3). R3's rule (start at the step year, end at the first year back at the pre-step
  level) guarantees a steep slope whenever a level shift reverses. "Three times faster than 3%" is a property of
  the rule.
- The rise was staged: P95 36–40 MW to 2007-08, 47.7 (2007-09), 48.2 (2007-10), 62.7 (2007-11), 64–68 through
  2009-08, then a smooth decline to ~47 by 2011. A two-step rise and a gradual fall are more like steam being
  brought on and running down than a metering change; but with one POC and no unit-level data a reporting change
  (a second IP unit's meter joining OKI2201) cannot be excluded, and I found no document for either.
- Sources: the NZGA Ohaaki page (search snippet; the page itself would not load) says "output dropped to as low as
  30 MWe but an investment programme, including several new wells, has restored production to about 50 MWe
  (450 GWh/year)", undated and at a different level from the 66 MW metered. Kortright (WGC 2015, citing Contact's
  April 2013 consent application): "Since 1999 output has stabilised at around 40–45 MW net"; "Between 1993 and
  1999 output steadily declined ... making drilling of makeup wells economically unattractive". Contact's FY2008
  report was not retrievable. So the 2007–09 plateau is not in the public narrative at all.
*Fix:* Report the episode as "output rose in two steps in late 2007 to 60–68 MW, held for about two years, and
returned to ~40 MW by 2013; the cause is not documented in the sources we could reach". Replace "−10.4%/yr" with
the level change and duration, or keep the number with the sentence "this slope is fixed by the chosen endpoints".
Delete "three times faster than 3%". Keep the hollow marker in F2 only if the caption says the window was chosen
post hoc from the series.

### B1. Intervals are nominally 95% but cover 87–90% for the high-autocorrelation segments
*Location:* "Trend" paragraph; all intervals; plan §6 item 3.
*Evidence (reviewer_checks/coverage_sim.py, 300 draws each, seasonal dummies included):* GLSAR coverage at the fitted
(n, ρ) pairs: n=93 ρ=0.67 → 0.880; n=148 ρ=0.87 → 0.867; n=318 ρ=0.94 → 0.877; n=97 ρ=0.71 → 0.897; n=150
ρ=0.25 → 0.920; n=194 ρ=0.74 → 0.947; n=225 ρ=0.48 → 0.957. SARIMAX-AR(1) is 0.88–0.96 at the same settings; OLS is
0.22–0.83. The plan's single check (ρ=0.6, n=144 → 0.95) was the easy case. Residual ACF beyond lag 1
(refit_trends.py): Kawerau 2008–16 lag-5 ACF −0.49, Ljung–Box p<0.001; Rotokawa p=0.025; Ngā Tamariki p=0.052;
others fine. AR(2) errors give Kawerau +0.98 (+0.34, +1.62), Mokai −1.50 (−1.90, −1.10), Ngā Tamariki +0.40 (−0.77,
+1.58), Ngāwhā +0.33 (−0.51, +1.17); fleet +0.02 (−0.20, +0.24).
*Fix:* Say the intervals are approximate (true coverage roughly 87–95%), report the AR(2) fleet interval as a
sensitivity, and note the Kawerau 2008–16 residual structure.

### B2. Inverse-variance combination across segments with different plant mix; capacity weights are all-time means
*Location:* "Trend" paragraph; Results table; F1 Kawerau panel.
*Evidence:* Kawerau's three segments are a 5.5 MW plant (2000–08, se 0.52), KGL at 102 MW (se 0.33) and 148 MW of
mixed series (se 1.46). Inverse-variance weights are 28% / 68% / 4%, so a plant that is 4% of the field's capacity
gets 28% of its trend. Mokai's 2000–04 segment (55 MW, +2.65, se 2.05) is harmless only because it is noisy. The
fleet weights use mean P95 over all segment months: Kawerau 77 MW (151 MW in its last 12 months), Wairakei 283 (330),
Mokai 92 (83). Present-capacity weights would push the fleet slightly positive (Kawerau up-weighted), so the choice
does not bias toward decline; equal weights give +0.15. No sign bias found, but the Kawerau combination is
conceptually wrong: segments are different plants, not draws of one parameter.
*Fix:* Weight segments by their mean P95 (capacity) rather than inverse variance when they have different plant
sets, or report Kawerau as KGL only; say in F1's caption that the Kawerau 2000–08 segment is a 5.5 MW plant.

### B3. The Kawerau 2017 "rerate 100 → 117 MW" is contradicted by FGGS Table 2 and by the metering; the 2018 TAOM window cuts nothing
*Location:* plan §5 events table; analysis.py EVENTS; report "Segments" paragraph.
*Evidence:* FGGS §Kawerau text says "in 2017 rerated to 117 MW"; FGGS Table 2 lists "Kawerau (KGL) 2008 & 2017,
107 MW"; the EMI register says 109 MW; KGL's annual median P95 is 105.9 (2015), 105.3 (2016), 106.8 (2017), 107.9
(2018). There is no 2017 step; the real uprating was gradual over 2009–14 (97 → 105) and sits inside the 2008–16
segment. TAOM is not in the data in 2018 (A3). Both windows are harmless (they orphan 2019, which is dropped) but the
report presents them as the capacity changes that define the segments.
*Fix:* Correct 117 to 107 (cite Table 2), note that no step is visible, and say TAOM does not report in 2018–19.

### B4. P95 is not immune to outages longer than ~29 days, and the report says it "ignores breakdowns and maintenance"
*Location:* "In plain terms"; "Achievable output" paragraph; plan §5.
*Evidence:* Ngā Tamariki 2014-01..09 (one of four units down for months reads as 72–78 vs 86 MW capability); Ohaaki
2018-03..07 (29–34 vs 40); Te Mihi 2014-10 (field P95 213 vs 330, not dropped by the 20%-of-median rule because the
field did not fall far enough). These are what drive the "steps" R2 finds at Ohaaki 2018/2019 and part of Tauhara
2011/2012. Multi-month single-unit outages are indistinguishable from capability loss in this design.
*Fix:* Qualify to "ignores outages and maintenance shorter than about a month"; add single-unit multi-month outages
to the threats list; consider a sensitivity dropping months whose P95 is below 85% of a 13-month rolling median.

### B5. MBIE/EDGS framing: accurate on the 3%, too strong on "EDGS 2024 assumes no decline"
*Location:* plan §1.1; report "What was asked", "It shows" paragraph; F2 label "H2 line (MBIE's 3%)".
*Evidence:* FGGS §3.3 quotes verified word for word ("used an estimate of 3% annual run down", "too low for Ohaaki
for example, and too high for Kawerau", "around one well every 5.5 years", costed as fixed O&M). The D1 reading is
fair and the 3% is indeed gross well/resource run-down for costing make-up drilling. On models: EDGS 2024's only
geothermal lines are new build and a consenting-cost adjustment table (−0.765%/−1.53% are cost adjustments, not
output); it is *silent* on existing geothermal output, which is not the same as "assumes no decline". FGGS itself
says EDGS 2016 treated the Mokai (2024) and Wairakei (2026) consent expiries "as a decommissioning in electricity
modelling exercises like MBIE-EDGS (2016)", i.e. a step to zero rather than a slope. Transpower's 2024 SOSA
reference-case consultation document does not mention geothermal (the plant-level assumptions sit in a spreadsheet
I did not check); CCC not checked. Finally, having corrected the misreading, F2 still labels the −3 line "MBIE's
3%", which re-plants it.
*Fix:* "EDGS 2024 does not model any decline in existing geothermal output; EDGS 2016 modelled consent-expiry
retirements" with the FGGS citation; relabel F2's line "H2 line (−3%/yr)". Mark FGGS's "outrages" as [sic] or
paraphrase rather than silently correcting the quotation.

### B6. Mokai: FGGS contradicts the metering, and direct-use steam is an unmentioned alternative explanation
*Location:* Results §H2; Scope and care.
*Evidence:* FGGS (2020) says Mokai "has been maintaining close to full output"; the metered P95 fell from 113 MW
(2009–11) to 94–98 (2018–20) and 85 (2026), so the metering says something the planning source did not. FGGS also
records "two significant direct use projects ... a large area of geothermally-heated greenhouses, and a milk-
processing plant" (Miraka, production from August 2011) on the same field; fluid taken for heat is fluid not
flashed for power. The main fluid-take consent expired in 2024 (FGGS); I could not find the renewal decision.
Capacity: 55 MW (2000) + 39 (2005) + 18 (2007) = 112–113 MW per Tuaropaki/NZGA, matching the plan's cuts.
*Fix:* Add direct-use diversion and the consent-limit point to the Mokai paragraph (it strengthens, not weakens,
the care language); note that FGGS's "close to full output" is not what the metering shows.

### B7. Novelty: supported, with a narrower claim
*Evidence:* Searches of NZGA reviews, NZGW/WGC proceedings and MBIE/EA material found no fleet-wide, metering-based
estimate of achievable-output trends. But per-plant annual generation is published every year (MBIE Energy in NZ,
NZGA annual reviews, which note that "generation from some geothermal fields declines over time while others ...
maintain output"), and Kortright (2015), O'Sullivan et al. (2015) and FGGS describe Ohaaki qualitatively.
*Fix:* Claim novelty for the capability measure and the segmentation, not for noticing field trends.

### C1. Numbers and facts (all verified unless noted)
- Every number in report.md's tables and text matches primary.json / supplementary.json (table below). report.html
  carries the same numbers (its extra ones are boilerplate: date, "A100").
- "Mokai ... fell from about 115% to about 85% of its segment mean": annual medians are 110–112% in 2008–11; "about
  110%" is more accurate.
- Ohaaki capacities: FGGS 108 MW original / 57 installed / ~40 produced (quoted correctly); other sources give 104
  (Wikipedia, GEM), 105 gross installed and 116 gross original (Kortright 2015), 44 MW (EMI register 2026). The
  register's 44 MW is the rating of what is in service, not a 2019–26 output step (P95 37–41 MW throughout, drift
  −1.3%/yr), so there is nothing to cut. Say that sources disagree.
- Ngā Tamariki OEC5: grid supply from January 2026, reliability run complete by Mercury's April 2026 update (+46 MW,
  86 → 132 MW); window 2026-01 onward is right.
- Ngāwhā OEC4: commissioned Dec 2020/Jan 2021; window right; output absent from the data until 2024-01 (A3).
- TAOM: commercial operation Oct 2018; window right; plant not in the data (A3).
- Wairakei A-station: the field sum does absorb the 2014 reallocation (Wairakei 152–165 → 126–135 MW as Te Mihi rose
  152 → 167); the problem is the ramp length, not the retirement rule (A1).
- Weights 36/21/12/11/10/5/3/3% and "57%" correct; "Twelve segments", "1,704 segment-months", "Five dropped" correct.

### C2. Code and data checks that passed
- kWh × 2 / 1000 → MW: correct for half-hourly kWh. Hand recomputation of eight field-months (incl. a DST-end
  50-period month, a DST-start 46-period month, the Norske Skog duplicate-row months, and a 3-plant Wairakei month)
  matches `field_monthly.csv` to 3 dp with identical valid-half-hour counts.
- Field sum: missing-for-some → NaN, missing-for-all → not a half-hour; DST days are 46/50 periods for all plants
  on the same dates; 2000–2008 DST-start days have 44 periods for every plant (two half-hours lost fleet-wide,
  negligible). One 20-period day (Te Mihi's first day) falls in the ramp.
- Duplicate plant-days: 64, all KAW0112 "norskeskog" 2023-04-28..06-30 across the SKOG → CHHE operator change; one
  row is all zeros, the other carries the day, so summing is correct.
- Dates: all files ISO; D2's fix and the out-of-month guard are right.
- Decision rules in `verdicts()` match plan §1.2 exactly.
- `analysis.py` reads `data/processed/` (present, md5-identical to `results/tables/`); "Reproducing it" works only
  because that copy exists. Say so or point analysis.py at results/tables.

### C3. Wording
- Abstract: "No field declines faster than 3% a year: the steepest is Mokai at −1.5% a year, steady since 2008" is
  fine; "the fleet's achievable output has not declined" is not (A1).
- "Short recent records ... not yet long enough to measure" — add that Ngāwhā's post-OEC4 record is also a reporting
  artefact until 2024.
- Scope and care: careful and accurate. Naming Mokai as "the only field with a clear, sustained decline" next to the
  Tuaropaki Trust is factual and the care paragraph covers it; adding the direct-use point (B6) makes the
  attribution caveat concrete rather than generic.

## Recomputed numbers

| quantity | reported | reviewer | method |
| --- | --- | --- | --- |
| Wairakei 2000-01 field P95 (2 plants) | 199.880 MW | 199.880 | raw CSV, csv module, independent code |
| Wairakei 2016-06 field P95 (3 plants) | 340.352 | 340.352 | same |
| Ohaaki 2008-07 P95 | 67.540 | 67.540 | same |
| Mokai 2020-03 P95 | 100.154 | 100.154 | same |
| Kawerau 2023-05 P95 (duplicate-row month) | 38.751 | 38.751 | same |
| Rotokawa 2012-04 P95 (DST end, 50-period day) | 175.027 (n 1442) | 175.027 (n 1442) | same |
| Ngāwhā 2015-09 P95 (DST start, 46-period day) | 23.700 (n 1438) | 23.700 (n 1438) | same |
| Ngā Tamariki 2019-01 P95 | 85.969 | 85.969 | same |
| Mokai 2008-01..2026-09 trend | −1.543 (−1.80, −1.29) | −1.543 GLSAR; −1.52 Prais–Winsten; −1.52 SARIMAX-AR1; −1.53 AR2 (−1.93, −1.12); −1.44 annual-mean OLS | refit_trends.py |
| Wairakei 2014-04..2026-09 | −0.179 (−0.49, +0.13) | −0.179 GLSAR; −0.15 PW/SARIMAX/AR2; −0.46 annual OLS; **−0.40 (−0.61, −0.19) from 2015-01** | refit_trends.py, segment_sensitivity.py |
| Wairakei 2006-01..2013-09 | +1.189 (+0.43, +1.96) | +1.189 GLSAR; +1.19 PW; +1.51 annual OLS | refit_trends.py |
| Ohaaki 2000-01..2026-09 | −0.118 (−1.65, +1.44) | −0.118 GLSAR (ρ 0.94); −0.19 PW/SARIMAX/AR2 (−1.87, +1.53) | refit_trends.py |
| Kawerau 2008-12..2016-12 | +1.378 (+0.73, +2.03) | +1.378 GLSAR; +1.21 PW; +1.25 AR2 (+0.55, +1.95); LB p<0.001; **+0.06 from 2014-01** | refit_trends.py, segment_sensitivity.py |
| Ngā Tamariki 2013-09..2025-12 | +0.460 (−0.15, +1.07) | +0.460 GLSAR (ρ 0.87); +0.39 SARIMAX (se 2×); **+0.05 (−0.09, +0.18) from 2014-10** | same |
| Field combos (8) | as table | identical to 3 dp from GLSAR refits | refit_trends.py |
| Fleet, capacity-weighted | +0.020 (−0.182, +0.222) | +0.020; ρ=0 interval (−0.158, +0.197); perfect-corr (−0.433, +0.474) ✓; AR2 errors (−0.20, +0.24) | refit_trends.py |
| Fleet, alternative segmentation | — | −0.09 (−0.27, +0.09) / −0.13 (−0.29, +0.02) / −0.17 (−0.33, −0.02); H1 Supported in all | segment_sensitivity.py |
| Weights | 36/21/12/11/10/5/3/3 % | 0.3554/0.2122/0.1150/0.1073/0.0967/0.0522/0.0306/0.0306 | primary.json |
| Ohaaki run-down 2008–13 | −10.4 (−12.5, −8.3) | −10.40 (−12.49, −8.27); 2008–12 −12.1; 2009–13 −9.8; 2008–16 −5.1; 2008–26 −1.7 | segment_sensitivity.py |
| Ohaaki since 2019 | −1.3 (−1.9, −0.7) | −1.256 (−1.853, −0.655) | supplementary.json |
| GLSAR 95% coverage at fitted (n, ρ) | 0.87–0.95 (plan) | 0.867 (148, 0.87); 0.877 (318, 0.94); 0.880 (93, 0.67); 0.897 (97, 0.71); 0.920 (150, 0.25); 0.947 (194, 0.74); 0.957 (225, 0.48) | coverage_sim.py |
| Last-10-years fleet | −0.44 (−0.99, +0.12) | −0.438 (−0.992, +0.118) | primary.json |
| Steps ≥ 15%, rolling ranges | as text | match supplementary.json (Mokai min −3.93, Tauhara max +4.20, Ohaaki −11.18/+21.53) | supplementary.json |
| Segment-months | 1,704; 5 dropped | 1,699 used + 5 dropped = 1,704 | primary.json |
| Git: code vs outcomes | — | analysis.py/test_analysis.py unchanged since c72cc2c; build_series.py changed only at d0be78c (date parsing); supplementary.py unchanged since 0ab005b; primary.json unchanged since 0ab005b; data/processed created 00:53:54 (plan commit 00:53:47); supplementary outputs 00:56:58 (commit 00:56:55) | git, ls --full-time |

## Answers to the twelve points in the brief

1. **D1 / the 3%.** Fair reading, quotes exact. Not a straw man as long as the H2 line is called "−3%/yr" rather
   than "MBIE's 3%" (B5). No document I could reach models existing geothermal as a gradual decline; EDGS 2016
   modelled consent-expiry retirements; EDGS 2024 is silent; Transpower SOSA 2024 consultation text has no
   geothermal content; CCC unchecked. "Planning models assume flat" is approximately right but should be stated as
   "do not model a decline".
2. **build_series.py.** Conversion, mapping, missing rule, dates, DST and duplicates all correct (C2). Mapping is
   complete for the files' contents; the files are incomplete (A3).
3. **P95 as achievable output.** P50/P99/mean agree with P95 to ±0.06%/yr fleet-wide, so dispatch and short
   flexing are not driving the result; month dummies handle the seasonal cycle. P95 does register multi-month
   single-unit outages and commissioning ramps as capability (B4, A1), which is where the bias lives. Consent-limited
   fields (Wairakei, Ngā Tamariki at a constant 86 MW) show the cap, not the reservoir, as the plan says.
4. **Segmentation.** Wairakei binary, Mokai stages, Ngāwhā OEC4, Ngā Tamariki OEC5, Te Huka, NAP 2010 (ramp to
   2010-06), Poihipi: dates right. Kawerau 2017: no step, 107 not 117 (B3). TAOM 2018: not in data (A3). Ohaaki
   44 MW: a rating, not a step (C1). Wairakei retirement: field sum handles it; ramp too short (A1). Missed:
   Poihipi–Wairakei steam connection 2006–11 (A1), KGL gradual uprating 2009–14 (A1).
5. **Trend model.** All numbers reproduce; GLS-AR(1) point estimates agree with three other estimators; intervals
   under-cover at high ρ (B1); inverse-variance combination is wrong for mixed-plant segments (B2); fleet correlation
   handling reproduces and is conservative; capacity weighting does not favour decline (B2).
6. **H1/H2.** Rules match the plan exactly. "The fleet is flat" is a statement about Wairakei and Rotokawa at the
   median and about commissioning artefacts at the margin (A1). The last-decade −0.44 deserves equal billing with
   the 26-year number.
7. **D3.** Endpoint selection fixes the slope; attribution unverified; metering change not excluded (A4).
8. **Mokai.** No capacity change 2008–26 found; direct-use steam and the 2024 consent expiry are alternatives the
   report should name (B6); no reporting change visible (single POC, one network code throughout).
9. **Novelty and facts.** Novelty holds for the measure (B7); facts verified or flagged (C1).
10. **Scope and care.** Careful; add the direct-use point so the Mokai caveat is concrete (B6, C3).
11. **Numbers.** All match (table).
12. **Plain language.** Overstated in two sentences (A2); otherwise accurate.

## What I ran

- `reviewer_checks/audit_raw.py` — fuel codes, every geothermal (POC, Gen_Code, Fuel, Tech) with first/last month,
  name-based search for mis-coded plants, TP counts per plant-day, duplicate plant-days, date formats.
- `reviewer_checks/hand_p95.py` — eight field-month P95 values from raw CSVs with the csv module, no shared code.
- `reviewer_checks/refit_trends.py` — every segment refit by Prais–Winsten, SARIMAX AR(1), SARIMAX AR(2) and
  annual-mean OLS; residual ACF and Ljung–Box of the GLSAR fits; independent field and fleet combination.
- `reviewer_checks/coverage_sim.py` — interval coverage of GLSAR vs SARIMAX vs OLS at the fitted (n, ρ).
- `reviewer_checks/segment_sensitivity.py` — segment-start sensitivity, Ohaaki endpoint sensitivity, fleet under
  alternative segmentations, all-time vs recent capacity weights (uses the study's analysis.py read-only).
- `reviewer_checks/fggs.txt`, `edgs.txt` — pdftotext of the two MBIE PDFs for quote checks.
- Web: ThinkGeoEnergy (TAOM Oct 2018; Ngāwhā OEC4 Jan 2021; TOPP2 synchronised 3 Dec 2025; Eastland portfolio TAOM
  26 / GDL 9 / TOPP1 24 MW), Mercury NZX/April 2026 update (OEC5), NZGA Wairakei page (Poihipi connected 2006, full
  capacity 2011) and Ohaaki page snippet, Kortright 2015 (WGC) on Ohaaki, Tuaropaki/Miraka (Aug 2011), Transpower
  SOSA 2024 consultation PDF (no geothermal content), Contact FY2008 report (not retrievable).
