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

## D2 — 2026-10-18 00:51 NZDT — direction of benefit adjudicated per network; contrast-level networks move to a sensitivity set (before any fit)

Validation V1 (`results/tables/v1_parse_validation.csv`) found the parsing right in 22 of 23 networks. The
exception is one label year missed for one study, from a missing space ("et al.2001"); the regex now accepts it. No
redraw was needed. V1 also exposed a problem the plan did not anticipate: which direction is "better".

1. **The catalogue label is not always the scale.**
   - **Arm-level networks.** The Harmful/Beneficial label and the sheet's own label disagree in 7 binary networks and
     in most continuous ones. Each of the 60 binary or rate networks where they disagree or the sheet has none, and
     all 30 continuous networks, was checked against the outcome description and the arm data (placebo or control
     arms against actives).
   - **Result.** The catalogue label is right in all but one: 501243, heavy bleeding, labelled Beneficial.
   - **The sheets' labels were often wrong.** Many name the concept: "decrease in blood pressure" is labelled
     Beneficial, while y is a signed change where lower is better.
2. **Contrast-level (iv) networks are ambiguous in two ways.**
   - **The label names the outcome concept** ("overall survival" is Beneficial), while the effect is a hazard of the
     event.
   - **The sheets do not say whether effect is t1 vs t2 or t2 vs t1, and both occur.**
     - In 501211, 501237 and 501319, placebo is t1 and the effects are large and positive on higher-is-better scales.
     - In 501403, the CLL8 row gives log 0.67 with FC as t1 and FCR as t2: the published FCR vs FC estimate.
     - nmadb's own netmeta code assumes t1 vs t2 throughout.
   - **The adjudication.** Each of the 30 eligible iv networks was adjudicated from:
     - placebo-controlled contrasts;
     - the sheet's notes;
     - landmark trials whose published estimates appear in the data (MPACT, PRODIGE 4, Hurwitz 2004, GOG-111,
       Alberts 1996, Armstrong 2006, CLL8).
   - **The record.** `code/direction.py` and `results/tables/direction.csv` give the call, the basis and a
     confidence for each. 22 calls are high confidence, 7 medium, and 1 undetermined (501216, psychotherapies with no
     placebo or waitlist node), which is excluded.
3. **The natural-scale rule was wrong.**
   - **What failed.** "All effects positive" is not evidence that a ratio sheet is on the natural scale. 501244 (a
     hazard ratio of no relapse, every one above 1) and 501378 (responder log RR, the values being logs of round
     ratios such as ln 6) are already logged.
   - **The fix.** The natural-scale sheets are now an adjudicated list (479757 and 501200 among eligible networks,
     both with linear-asymmetric CIs). seTE comes from the CI where one is given, including 501200's text CI column.
4. **The primary analysis is restricted to arm-level networks.** Their direction is fixed by what r or y measures,
   and every disagreement was checked; there are 178 of them.
   - **The sensitivity set.** The 29 adjudicated contrast-level networks form an iv sensitivity set, analysed both
     with and without them, and separately with high-confidence calls only.
   - **The rest is unchanged:** hypotheses, thresholds, holdouts and model.
