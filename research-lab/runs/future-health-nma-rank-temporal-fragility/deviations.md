# Deviations from plan.md

Timestamps are Pacific/Auckland, from `date`.

## D1 — 2026-10-18 00:43 NZDT — publication years: more column names, and the study label as a fallback (before any fit)

The first standardisation run, which fits nothing, found 59 networks with no year column under the names the plan
anticipated.
- **Column names.** Some use "Pub. year" for the year and "study (name)" for the label. Both are now mapped, which is
  within plan §4.
- **Label fallback (new rule).** Where a network has no year column at all, a year written in the study label is
  used ("Smolen, 2008", "Black et al. (2007)"). The pattern is a four-digit year 1950–2029, bounded by spaces,
  punctuation or brackets; the last such year in the label is taken.
- **Gaps are not filled.** The fallback does not fill gaps in an existing year column, where missing years are
  written "NR" or "?".
- **Effect.** 29 of the 208 networks that pass the size and year rules get their years this way. Validation V1
  oversamples them (§ V1 sample below).
- **The 90% coverage rule is unchanged.**
- **Excluded.** One network (no id column) fails to parse.
