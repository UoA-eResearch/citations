# Deviations and implementation details

The plan (plan.md) was committed in e74eaea at 2026-10-03 21:32 NZDT. After that the sealed post-period file was opened,
once its SHA-256 had been checked (code/snap_crashes.py). Entries are timestamped with `date`.

## D1. Event-study figure (2026-10-03 21:37 NZDT)

The event-study figure (results/figures/event_window.png, results/tables/event_window.csv) drops two groups:

- the 2025H1 transition half, because the cohort's treated segments are dropped in their transition half, so its
  indicator is empty;
- the 2025H2 cohort, which is 86 segments, only 2 of them with any injury crash in the window.

This affects the figure only. The primary estimate includes both cohorts as planned.

## D2. Cohort-specific (ETWFE-style) row (2026-10-03 21:37 NZDT)

The model includes both cohort indicators. Only the 2025H1 cohort's coefficient is reported, because the 2025H2
cohort has 2 treated segments with crashes and its coefficient is not informative.

## D3. Manipulation check details (2026-10-03 21:37 NZDT)

The plan did not fix which crashes or segments the check uses. It is implemented on all crash severities, on the
2025H1 cohort's treated segments, comparing 2023H2-2024H2 with 2025H2-2026H1.

## D4. Exploratory descriptive tables added after unsealing (2026-10-03 21:37 NZDT)

The manipulation check showed that, on urban 30/40->50 segments, CAS-recorded limits do not follow the register. Two
descriptive tables were added to characterise those segments. Neither enters any estimate.

- **results/tables/treated_reason_at_t0.csv.** 72% of urban 30/40->50 treated segments were 30 km/h zones with the
  NSLR reason "The presence of a school".
- **results/tables/variable_zone_overlap.csv.** Only 0.2% of them are covered by a Variable-category record at t1.

The reviewer showed that this midpoint-in-polygon test understates the overlap with school zones; see D7.

## D5. Expressway corridor string (2026-10-03 21:37 NZDT)

The exploratory expressway model builds its corridor from the raw OSM name, not the normalised one. The clusters are
equivalent in practice.

## D6. Post-plan change to snap_crashes.py (2026-10-03 21:58 NZDT)

After the plan was committed, snap_crashes.py gained a tolerance argument so that the planned 15 m and 50 m robustness
snaps could be run. The 30 m default output is unchanged.

## D7. Checks added after independent review (2026-10-03 21:58 NZDT; code/review_checks.py)

The review verdict was "publish with edits". None of these checks changes the preregistered primary estimate.

- **All-crash secondary (review F1).** Results depend on where the window starts:

  | Window start | Rate ratio (95% CI) |
  |---|---|
  | 2017H2 | 1.07 (0.96-1.19) |
  | 2020H2 | 1.08 (0.98-1.20) |
  | 2022H1 (preregistered) | 1.13 (1.02-1.26) |
  | 2023H2 | 1.09 (0.97-1.22) |
  | 2024H1 | 1.05 (0.92-1.20) |

  Non-injury crashes alone give 1.18 (1.05-1.34). The all-crash event study, relative to 2024H2, has a pre-reversal
  dip in 2023H1 (0.85, z -2.3) and post halves 1.07 (z 0.7) and 1.11 (z 1.2). This secondary result is reported as
  exploratory and not robust.
- **Manipulation check (review F2).** The CAS speedLimit field follows the register with a lag of about 18 months on
  treated and control roads alike. The 2023 reductions appear in CAS only from late 2024. The field therefore cannot
  test whether the 2025 raises were signposted.
- **School zones (review F2).**
  - Variable school zones live between Jul 2025 and Jun 2026 lie within 30 m of 5.6% of treated segments, 50 m of
    7.7% and 100 m of 14.6%.
  - The primary estimate without treated segments within 50 m of such a zone is 1.01 (0.82-1.25).
  - The primary estimate without treated segments whose reason at t0 was "presence of a school" is 1.01 (0.82-1.25).
- **Strata (review F4).** Treated and control injury crashes by stratum are in results/tables/review_strata.csv.
  Several large treated strata have few control crashes.

## D8. Dating artefacts from re-certification records (2026-10-03 21:58 NZDT; review F5, F6)

- **What the code did.** build_units.py dates the reduction from the record in force at t0, and dates the cohort from
  the record in force at t1. Re-certification records can make either date later than the real change.
- **Correction.** The corrected dating uses the first post-t22 record carrying v0, and the first post-t0 record
  carrying v1. It moves 69 treated segments' cohorts; most of the "2025H2 cohort" was raised in 2025H1.
- **Effect.** The primary estimate with the corrected strata and cohorts is 1.02 (0.83-1.26). The preregistered
  coding is kept as primary.

## D9. Placebo calibration for every stratum (2026-10-03 21:58 NZDT; review F3)

- **The problem.** The pre-period placebo fake-treated every control in strata where treated segments outnumber
  controls. Those strata then dropped out of the comparison, and they hold 56% of treated segments.
- **The re-run.** At most half the controls of each stratum were fake-treated: placebo SD 0.110 against a mean
  clustered SE of 0.105 (ratio 1.05), with 6.0% rejection at |z| > 1.96.
- **Conclusion.** The clustered SE remains adequate.

## D10. Register coverage gaps in the post period (2026-10-03 21:58 NZDT; review F8)

For 1,552 treated segments the v1 records end in May-June 2026 without a replacement. The share with an unknown month
is similar for treated (14%) and control (17.5%) segments. This needs a fresh check at Stage 2.
