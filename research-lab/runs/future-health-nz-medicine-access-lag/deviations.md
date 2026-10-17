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

## D2 — 2026-10-17 16:38 NZDT — before any Medsafe, PHARMAC or PBS date was linked

1. **T3 from PHARMAC's monthly XML archive instead of the Schedule Update PDFs.** Two archives exist:
   - the community Pharmaceutical Schedule as monthly XML, 2006–2026 (/pub/schedule/archive);
   - the Hospital Medicines List (Section H) as monthly XML, 2011–2025, plus the current file (/pub/HML).

   Schedule Updates stop reporting Section H changes after 2013, and their PDF layouts vary. So:
   - T3B is the first monthly community Schedule (Section B, including PCT) in which a Chemical, or a Formulation of
     a combination, contains the substance's name;
   - T3H is the same for the HML;
   - T3 is the earlier of the two, dated to the edition's effective month;
   - the Schedule Update PDFs are kept for the validation cross-check.
2. **Old-substance exclusion.** EMA-first substances have no new-active-substance flag. Old medicines first
   centrally authorised inside a 2010+ combination enter the cohort: the first crawl rows include acetylsalicylic
   acid. A cohort substance is therefore excluded as not new if:
   - its Medsafe consent (T2) is more than 1 year before T0; or
   - it is present in the first available community Schedule XML (2006) or more than 1 year before T0.

   Counts are reported. The rule uses only the direction "older than its own first international approval", so it
   cannot shorten or lengthen any included lag.
3. **Crawler.** Medsafe results stream in after the page loads. The first crawler version waited a fixed 1.2 s and
   missed application rows; it was replaced before any results were used (commit de1125a), and the crawl restarted
   from scratch.
