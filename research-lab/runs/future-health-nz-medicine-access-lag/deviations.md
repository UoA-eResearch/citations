# Deviations log

Every departure from the lead and from plan.md, timestamped with `date` when it was made.

## D1 — 2026-10-17 16:31 NZDT — before any Medsafe, PHARMAC or PBS date was linked

1. **Australian benchmark restricted to T0 2019–2024.** Historical PBS listing dates are no longer openly available
   (legacy extracts discontinued; the public API holds 12 months). The Medicine Status Website covers submissions from
   about 2019 (plan section 6).
2. **Stages refined.** Medsafe's application search gives a submission date, so the lead's "regulatory stage" is
   split into the sponsor's filing delay (T0→T1) and Medsafe's review (T1→T2). H1a keeps the lead's definition
   (T0→T2).
3. **Primary window 2010–2023 for H1**, following the critic's note on the February 2024 parallel-assessment and 2026
   Rule of Two changes; 2024 is reported separately.
4. **Entity resolution** by deterministic name normalisation, not RxNorm/ATC tooling, validated by an agent check of
   150 substances. No LLM-assisted matching.
5. **No PHARMAC application dates.** The PHARMAC application tracker is not used, so the funding stage runs from
   Medsafe consent, as in the lead, not from a funding application.
