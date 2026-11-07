# Deviations from plan.md

## D1 (2026-10-26 06:43 NZDT; before any centroid, count or null was computed on real records)

- **Effort-null sampling scheme.** The plan drew P1's records without replacement with probability proportional to
  w1 = s1 / (s1 + s2), using exponential keys. A synthetic check showed this reproduces only 66% of a pure effort shift
  (`code/test_effort.py`).
  - In that check, every species has a fixed range and P2 collecting is concentrated in the north half.
  - The reason: successive sampling with those weights does not give inclusion probabilities proportional to them.
  - The target is the chance that a record from a fixed range in cell c was collected in P1: n1·s1 / (n1·s1 + n2·s2).
- **Replacement:** Pareto order sampling (Rosén 1997) with odds θ = s1 / s2. Keys are (U / (1 − U)) / θ, and the n1
  smallest go to P1. Fixed-size sampling of this kind approximates those inclusion probabilities.
  - The same check now reproduces 97% of the effort shift, against 28% for the noise-only null.
  - Fixed ranges with no effort change still give observed ≈ null (0.92 against 0.99 km/yr), with 7.5% of 40
    species above their null 95th percentile.
  - A species moved 4.5° north is recovered at 17.5 km/yr (expected 17.9), with a null of 1.0
    (`code/test_velocity.py`).
- **Edge cases:** cells with P2 effort only (θ = ∞) go to P1 first, and cells with P1 effort only (θ = 0) go last.
  Cells with no effort in either period after leave-one-species-out get θ = 1 and are counted per species.
- **Coverage tool:** `tools/coverage.py` gains `add_counts()` for record-level stages (tens of millions of records)
  too large for per-unit calls. The summary format is unchanged.

## D2 (2026-10-26 08:59 NZDT; after cleaning, before any centroid, count by species or null)

- **G2 caught a silent loss in the first cleaning run.** The coverage counts did not reconcile: 35,526,014 records in,
  but kept plus dropped came to 35,166,346.
- **An independent recount** by a single SELECT over joins, with rules unchanged, sums exactly to the input.
  - The first run's in-place DuckDB UPDATEs on the 35-million-row table (which has a list column) had lost about 1%
    of the records in every class after rule 4.
  - That included 320,852 records that should have been kept: 30,301,548 kept against 30,622,400.
- **Fix:** `code/clean.py` now classifies every record once, in one SELECT with LEFT JOINs to the dense-point and
  land-cell tables, with no UPDATEs. It asserts that kept plus dropped equals the input, and that the joins do not
  change the row count.
- The rules, their order and their thresholds are unchanged. The first run's outputs were overwritten; no analysis
  had read them.

## D3 — 2026-11-07 — fixes after the independent review (verdict: fix first)

Everything here follows the first review (`review/review.md`) and is post hoc. No velocity or null was recomputed;
the preregistered statistic and its verdict (H1 Supported, ratio 0.667) stand.

1. **Identification (finding 1).** New `code/absorption_test.py` runs synthetic worlds through `velocity.py`:
   300 species, 150 records each, uniform and unchanging effort, with all, half, a fifth or none of the species
   moving 1° north. The effort null reproduces 103% of the movers' velocity when all move, 70% when half move and
   60% when a fifth move, so it cannot tell collectors moving from plants moving together. The title, verdict and
   plain terms are rewritten around what the design identifies: the noise floor (ratio 0.41) and the poleward
   excess. The absorption table is in the main limitation. New `code/effort_surface.py` gives the effort surface's
   latitude by period (mean |lat| 30.6° → 31.8°).
2. **Pareto sampling (finding 2).** For the five smallest primary species (20–22 records), empirical inclusion
   probabilities over 5,000 draws deviate from the stated target by at most 0.04–0.17. They correlate with it at
   0.995–0.999, and the targets sum to 8.6–13.2 against counts of 10–12. The report now says the weights are
   approximate per record. No recalibration was run.
3. **Statistics (finding 3).**
   - The per-species ratios are reported (median 0.68, mean 0.97; 25.8% of species below their null median).
   - The 0.5 bar is described as undemanding.
   - The 36% exceedance is described as a lower bound.
   - 28% of primary species have fewer than 100 records; the review's "most" does not hold.
