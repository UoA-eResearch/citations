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
