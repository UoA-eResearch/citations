# Deviations from plan.md

## D1 — 2026-10-24 22:34 NZDT — data construction, before any model is fitted to the real panel

The panel was built and only the splice checks (`results/tables/splice_validation.json`) were inspected. No
regression has been run on it.

1. **2023 total deaths.** The CDC weekly 2020–2023 file ends in mid-September 2023 (259 days covered), so
   apportioning weeks to calendar years would extrapolate a quarter of the year. 2023 deaths instead come from CDC's
   "VSRR Quarterly provisional estimates for selected indicators of mortality" (`489q-934x`): the all-cause crude
   rate for the 12 months ending 2023 Q4, by state of residence, times SEER population. Against the day-scaled weekly
   figure, the median absolute log difference is 3.6% (maximum 11%). 2018–2022 still use the calibrated weekly
   series, as planned.
2. **Drug-poisoning counts for 2019–2023.** The VSRR provisional counts behave like counts by jurisdiction of
   occurrence: DC is 11–15% above the NCHS residence counts in every overlap year, and NV is 12% above in 2017. As for
   the weekly totals, each state's 2019–2023 VSRR series is multiplied by exp(mean log(NCHS / VSRR)) over 2015–2018.
   The factors run from 0.879 (DC) to 1.065 (median 1.003).
3. **Implementation notes,** none of which changes a planned choice:
   - SEER's "20ages" file has 20 groups (18 = 85–89, 19 = 90+); both map to 85+.
   - The weekly files use two date formats.
   - New York City is added to New York State in both the weekly and VSRR files; neither file's "New York" includes
     NYC.
   - Calendar years not fully covered by weeks are scaled by days. This affects only 2013 and 2023, neither of which
     is used.
   - Employment-to-population uses SEER population aged 15+, as planned.
4. **Splice checks** (plan §6):
   - NBER and CDC total deaths for 1999–2004 agree exactly, and the age-adjusted rates by a median 0.004% (maximum
     1.4%), well inside the 2% trigger.
   - Calibrated weekly totals for 2014–2017 have a median within-state SD of 0.16% around the calibration.
