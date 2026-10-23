# Deviations from the preregistration

## D1 — 2026-10-23 17:16 NZDT — PPML separation (POST-RESULT: logged after the first primary run was read)

**The problem.** The first run of `did.py primary` returned log RR −1.11 (SE 0.29), which the rule calls Refuted. Its
event-time coefficients show why that number is degenerate:
- events 0 and 1 are +0.45 and +0.73;
- events 2 to 6 are −2.9 to −12.8.

Those later coefficients belong to cohort × event-time cells with zero editions (`results/tables/cell_counts_d1.csv`),
mostly in calendar years 2024–2025, when Open Library has ingested almost nothing (15 editions in 2025 across all
linked works). In PPML a dummy whose cells are all zero is perfectly separated, and its maximum-likelihood estimate
is −∞. pyfixest returned large negative numbers instead of dropping it, and the event 0–2 aggregate averaged them in.

**The fix.** It follows the standard convention (ppmlhdfe):
- a cohort × event dummy whose cells sum to zero is separated, so its observations are dropped and it is not estimated;
- the event-time aggregates and the RR average only the identified cells, with cohort-size weights renormalised.

Every variant uses this. The first-run numbers are kept (`primary_pre_d1.json`, `event_study_pre_d1.csv`) and
reported.

**What it does to the result.** The fix removes cells that pull the estimate down, so it moves the result towards
H1. It is reported as a post-result change, and the report states the preregistered number.

**Linkage validation** (`results/tables/linkage_validation.json`; 300 registrations, labelled blind by a separate
agent):
- precision is 0.81 (renewed 0.78, never renewed 0.84);
- recall is 0.38 (renewed 0.29, never renewed 0.50).

Renewed, more popular books more often have duplicate Open Library work records. These are either dropped by the
uniqueness rule or have their editions split across records, so the outcome is undercounted for treated works. This
is reported as a limitation. The plan has no gate on it.
