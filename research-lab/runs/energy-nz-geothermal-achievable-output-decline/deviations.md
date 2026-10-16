# Deviations log

Every departure from the lead and from plan.md, timestamped with `date` when it was made.

## D1 — 2026-10-17 00:53 NZDT — before any output: the 3%/yr is gross run-down, the dataset changes, the unit is the field

1. **What MBIE's 3% means.** The lead treated "MBIE's 3%/yr annual run down" as an assumed decline in plant
   output. The source (FGGS 2020, s. 3.3) uses it as natural well/resource decline to cost make-up drilling, which
   then maintains output. Realised achievable output is after drilling, so the comparison is not like-for-like.
   The lead's thresholds are kept as H1/H2's decision lines, and the report interprets them accordingly; the
   substantive question becomes the flat-capacity assumption (plan section 1.1).
2. **Dataset.** The lead's primary source, Unit_level_generation_IR, has geothermal units only at Wairakei and
   Ohaaki and only for 2000-2003 (inventory, coverage only). Generation_MD (plant-level, all geothermal plant,
   2000-2026) replaces it. The unit-level files stay on disk, unused.
3. **Unit = field, not unit or plant.** Plants on a field share a consented fluid take, and at Wairakei fluid is
   allocated to Te Mihi and Poihipi first, so a plant's output there measures allocation.
4. **Interval method.** Newey-West, the first choice, under-covered in synthetic tests (0.67-0.88); GLS-AR(1)
   covered 0.87-0.95 and is primary. Decided on synthetic data only.
5. **US validation dropped.** The lead suggested EIA-923 (The Geysers) as an outside check. EIA-923 is monthly
   generation, so the P95 measure cannot be computed from it; a monthly-mean check would test a different
   estimator. Not done, and said so.
6. Also first: the EMI download script saved 321 HTML redirect stubs instead of data (no -L); found before use,
   fixed, re-downloaded.

## D2 — 2026-10-17 00:55 NZDT — a date-parsing bug in build_series.py, found before any trend existed

The first build parsed ISO dates (YYYY-MM-DD) with dayfirst=True, which swaps day and month for days 1-12, so
every month kept only about 20 of its 31 days. analysis.py then found no month with >= 80% valid half-hours and
crashed before computing any trend; the valid-fraction check (0.645 in every field and month, data-quality counts
only) showed why. Fixed (ISO parsed explicitly; any row dated outside its file's month now raises an error) and
rebuilt: every segment is now 100% valid. The segments the code builds match those plan.md section 5 predicted
from the inventory, exactly. 5 of 2,068 field-months are dropped as whole-month outages (Ohaaki 3, Rotokawa 1,
Tauhara 1).

## D3 — 2026-10-17 00:56 NZDT — post-hoc descriptive checks of drilling cycles, written after the results were seen

The preregistered results: H1 Supported (fleet +0.02%/yr, -0.18 to +0.22), H2 Refuted (no field below -3%/yr;
Mokai steepest at -1.53%/yr). Ohaaki's linear trend (-0.12%/yr, wide interval -1.65 to +1.44) hides a cycle: annual
median P95 of 35-40 MW in 2000-07, 66 MW in 2008, back to ~40 MW by 2013, flat since - consistent with the
well-investment programme the NZGA field page describes. code/supplementary.py, written now and committed before
it runs, gives rolling 60-month trends per field (R1), flags year-to-year steps of >= 15% (R2), and fits the
preregistered trend model to the run-down after each upward step (R3). Descriptive and exploratory; no verdict
changes.

## D4 — 2026-10-17 08:02 NZDT — acting on the adversarial review (publish with edits; 4 must-fix, 7 should-fix)

The review (review/review.md, Fable 5.1) reproduced every number, recomputed eight field-month P95s from the raw
files exactly, found the git order clean and both verdicts robust (worst fleet lower bound -0.33%/yr). It found the
framing wrong in four places: "flat" depends on two commissioning ramps and an uncut, documented capacity change
(Poihipi's connection to the Wairakei steamfield, 2006-2011, missed because the plan used only FGGS Table 2); the
"upkeep keeps the fleet level" mechanism is not shown (the study has no drilling data, and the offsets it found are
uprates and commissioning artefacts); Generation_MD does NOT cover every geothermal plant (Te Ahi O Maui is not
identifiable before 2025-09, GDL/TOPP1/the Kawerau binary never appear, Ngawha OEC4 is absent until 2024-01), so
plan section 3's claim was wrong and Kawerau is not a field in these data; and the Ohaaki -10.4%/yr is fixed by its
endpoint rule and its drilling attribution is undocumented. Also: KGL's 2017 rerate was to 107 MW per FGGS Table 2
(the text's 117 is contradicted, and no step is visible), TAOM is not in the data in 2018-19, intervals cover
~87-95% rather than 95% at high autocorrelation, and inverse-variance weighting gives Kawerau's 5.5 MW pre-2008 plant
28% of the field. code/review_response.py, written now and committed before it runs, computes the alternative
segmentations, a rule-based variant (12-month ramps, the Poihipi window, Kawerau = KGL), capacity-weighted segment
combination, AR(2) errors, a rolling outage filter and the Ohaaki window sensitivity. The report is then revised.

D4 outcomes (review_response.py): fleet -0.09 (-0.27, +0.09) with Wairakei 2014- from 2015-01; -0.13 (-0.29, +0.02)
adding Nga Tamariki from 2014-10; -0.19 (-0.34, -0.03) also dropping Wairakei 2006-13; rule-based variant (12-month
ramps, Poihipi window 2006-11, Kawerau = KGL) -0.04 (-0.22, +0.14); capacity-weighted segments +0.10 (-0.15, +0.36);
AR(2) +0.02 (-0.19, +0.23); rolling outage filter -0.08 (-0.24, +0.08), 42 months dropped. H1 Supported and H2
Refuted in every case. Ohaaki fall: -10.4 (2008-13), -12.1 (2008-12), -5.1 (2008-16), -1.7 (2008-26). The report
now says "between about 0 and -0.2%/yr, -0.4 over the last decade", drops the drilling mechanism, states the
coverage gaps, labels the Ohaaki slope as endpoint-determined and its cause undocumented, corrects KGL to 107 MW,
calls the intervals approximate, relabels F2's -3 line, adds Mokai's direct-use steam and the FGGS contradiction,
and narrows the novelty claim. analysis.py's EVENTS label still says 117 MW (a description string only; the
window it defines is unchanged and harmless).

Confirmation pass (review/confirmation.md, publish with edits): F2's y-axis labels were clipped - the left margin is
widened and the figure regenerated. Optional wording taken: the last-decade sentence now says its uncertainty spans
flat; "probably" a mill's net export; the commit list completed; the abstract states the full +0.1 to -0.2 range of
specifications beside "0 to -0.2".

