# Preregistration: did the 2023 Auckland storms muddy Auckland's estuaries, in proportion to the land they stripped?

Lead: `auckland-nz-2023-storms-estuary-mud-natural-experiment` (Auckland/NZ signature area). Written 2026-10-23,
before any 2023 or 2024 outcome value was looked at and before any exposure was computed.

**Examined beforehand (nothing estimated):**
- The LAWA Estuary Health file (v2, data to 3 Sep 2025; sha256 `4945999a…f89c1`): sheet and column names,
  indicator counts, and the number of Auckland mud-content rows per year and per sampling date code.
- **Sampling dates.** Auckland mud-content dates are coded to the month or year. Every 2023 row is dated October (41)
  or November (22) 2023, after both storms (27 January and 14 February 2023). Every 2024 row is dated October (40) or
  November (19). Rows coded 1 January (year only) occur from 2010 to 2022 and never after.
- **Site counts.** 92 Auckland sites have mud content in at least 5 distinct years from 2010 to 2022. 56 of them have
  a 2023 value, and 51 have a 2024 value.
- **No outcome values** for 2023 or 2024, of any indicator, have been viewed. Pre-2023 values have not been viewed
  either, beyond the counts above.
- **Exposure sources:**
  - The LINZ elevation bucket lists Auckland 2024 DEM collections (parts 1 and 2).
  - Auckland Council's Cyclone Gabrielle bare-earth pilot is public, but only as vector tiles, for five catchments.

**Novelty** (from the lead, rechecked 2026-10-23). No exposure-graded test of estuary change after the 2023 storms was
found. Auckland Council's pilot mapped bare-earth sources in five catchments but did not link them to estuaries.

## 1. Sites and outcome

- **Outcome:** mud content (% of sediment finer than 63 µm), the LAWA indicator `Mud_content`, one value per site and
  year (no site-year has two rows).
- **Sites:** Auckland Council sites with mud content in at least 5 distinct years from 2010 to 2022 and a 2023 value
  (56 sites). The list is written to `results/tables/sites.csv` from dates and counts alone, before any value is
  read.
- **Harbour clusters:** LAWA's `Estuary name`.

## 2. Exposure: newly bare land draining to the coast near each site

1. **Elevation and routing.** The LINZ Auckland 2024 1 m DEM (parts 1 and 2) is read at 10 m, by block mean. Gaps
   are filled from the 2016–2018 north and south collections, read the same way. Then:
   - depressions are filled;
   - flow is routed by D8;
   - every land cell is traced to the cell where its flow path leaves the land (its coastal outlet).
2. **Contributing land C(R) of a site:** every land cell whose coastal outlet lies within R km of the site. R = 5 km
   is primary; 2 km and 10 km are sensitivity analyses.
3. **Newly bare ground,** from Sentinel-2 L2A (Earth Search):
   - Per-pixel median NDVI over clear observations (scene classification classes 4 and 5) in two windows: before
     (1 November to 31 December 2022) and after (15 February to 30 April 2023). Each window needs at least 2 clear
     observations.
   - A pixel is **newly bare** if its NDVI is at least 0.5 before and at most 0.3 after.
4. **Exposure E of a site:** newly bare cells as a share of the land cells in C(5 km) that have valid NDVI in both
   windows.
5. **Terciles** of E across the 56 sites are frozen in `results/tables/exposure.csv`. That file is committed before
   any outcome contrast is computed.
6. **Validation (descriptive, not a gate).** Where Auckland Council's pilot bare-earth vector tiles can be decoded,
   agreement with the newly bare map inside the pilot catchments is reported. If they cannot be decoded, this is
   reported instead.

## 3. Hypotheses and tests

**Model.** For site i and year t:

mud_it = α_i + τ_t + β · Top_i · 1[t = 2023] + γ · Top_i · 1[t = 2024] + ε_it

Years run from 2010 to 2024. The model uses top-tercile and bottom-tercile sites only, with Top_i the top-tercile
indicator.

**Inference.** A wild cluster bootstrap by harbour (Webb six-point weights, 9,999 draws, null imposed, percentile-t),
reported as a 95% interval. CR2 cluster-robust intervals are reported alongside.

- **H1 (primary): the 2023 mud rise at the most exposed sites exceeds that at the least exposed by at least 4
  percentage points.** The test is β.
  - **Supported** if β ≥ 4 pp and the interval excludes 0.
  - **Refuted** if the interval's upper bound is below 4 pp.
  - **Inconclusive** otherwise.
- **H2 (co-primary, continuous dose-response).** All 56 sites, with δ · E_i · 1[t = 2023] and η · E_i · 1[t = 2024]
  in place of the tercile terms. δ is scaled to the interquartile range of E.
  - **Supported** if the 95% interval of δ × IQR excludes 0 on the positive side.
  - **Refuted** if its upper bound is below 1 pp.
  - **Inconclusive** otherwise.

The lead's own numbers put the minimum detectable effect near 4 pp, so H1 has about 50% power. A null result is
informative only when the upper bound is below 4 pp, and this is stated with the result.

## 4. Secondary analyses (reported, not confirmatory)

1. **Persistence:** γ and η (2024).
2. **Event study:** top-versus-bottom differences by year, 2010–2024, relative to the 2010–2022 mean, to show any
   pre-trend.
3. **Placebos:** each year from 2015 to 2021 treated in turn as the event year, using pre-2023 data only, with the same
   exposure. Reported as the distribution of placebo β.
4. **Leave one harbour out** for β and δ.
5. **Exposure radius:** 2 km and 10 km.
6. **Year-only rows dropped:** rows dated 1 January, to remove any uncertainty about sampling season.
7. **Other outcomes:**
   - LAWA `Macrofauna` (2023 and 2024; a lagged response is expected);
   - copper, zinc and lead, if sampled in 2023, as an urban stormwater signal.
8. **National replication** (only if time allows; exploratory): the same exposure pipeline on LAWA sites in the
   other storm-hit regions (Northland, Waikato and Coromandel, Hawke's Bay, Tairāwhiti).

## 5. Limits stated in advance

- About 19 sites per tercile and one post-storm survey in each of two years.
- Fine sediment can be flushed or redistributed before the October–November survey, so a transient pulse may be
  missed.
- Harbour sites draw on distant catchments, and a 5 km outlet radius is a crude exposure.
- Construction that strips vegetation between December 2022 and April 2023 counts as newly bare.
- Post-storm Sentinel-2 imagery is cloudy, so pixels without two clear observations in each window are excluded.

## 6. Care note

No Māori data or customary-fisheries data are used. The Kaipara and Manukau harbours are taonga under active mana
whenua kaitiakitanga. The report will say so, and will point to the forums, such as Kaipara Moana Remediation and the
Manukau Harbour Forum, where results like these belong. The lab cannot do the engagement itself, and this does not
gate the study.

## 7. Outputs

`results/tables/` holds:
- `sites.csv`, `exposure.csv`, `primary.json`;
- the event-study and placebo tables.

`results/figures/` holds the exposure map, the event study and the dose-response. `deviations.md` records any change
before the result it affects.
