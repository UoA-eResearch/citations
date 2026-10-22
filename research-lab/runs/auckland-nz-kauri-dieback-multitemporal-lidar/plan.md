# Preregistration: can open repeat LiDAR see kauri dieback? Crown loss 2016–18 → 2024 at trees graded in the 2014–15 Waitākere survey

Lead: `auckland-nz-kauri-dieback-multitemporal-lidar` (Auckland/NZ signature area). Written 2026-10-23, before any
LiDAR raster was read and before any feature was computed.

**Examined beforehand (nothing estimated):**
- Auckland Council's ObsKauri public layer, downloaded in full (52,867 records; sha256 `e61d310e…eaf8d`): its field
  names, the survey names, and record counts by survey, financial year and field status.
- The Waitakere Track Survey 2014-2015 has 13,861 records:
  - 12,512 non-symptomatic (status 1);
  - 1,013 with ill thrift (2);
  - 246 with possible kauri-dieback symptoms (3);
  - 90 severe (4).
- The Waitakere Survey 2021 has 2,503 records: 1,213 / 281 / 605 / 41 for statuses 1–4, plus 348 "not a kauri" and
  15 "no status".
- The extents and dates of the LINZ Auckland North 2016–2018 DSM/DEM and the Auckland 2024 Part 1 and Part 2 DSM
  collections.

**Framing.** This follows the critic's note on the lead. The 2014–15 labels predate the first LiDAR epoch by one to
four years, so the test is *prognostic*: do trees graded symptomatic from the ground in 2014–15 lose more crown
between 2016–18 and 2024 than trees graded healthy? The 2021 survey supplies a secondary, time-aligned check.

## 1. Labels

- **Primary:** Waitakere Track Survey 2014-2015. Positive = status 3 or 4 (336). Negative = status 1 (12,512).
  Statuses 2, 5 and 6 are excluded.
- **Duplicate points:** records within 2 m of each other with the same status are merged into one tree.
- **Secondary (time-aligned):** Waitakere Survey 2021, with positive = status 3 or 4 and negative = status 1.

## 2. LiDAR features

Canopy height model CHM = DSM − DEM at 1 m for each epoch:
- E1: Auckland North 2016–2018 (DSM and DEM);
- E2: Auckland 2024, Parts 1 and 2 (DSM), with the 2024 DEM.

Inside a 15 m radius of each tree point:
- **Change features:**
  - ΔP95 = P95(CHM, E2) − P95(CHM, E1);
  - Δcover15 = share of cells above 15 m in E2 minus in E1;
  - ΔP50, defined the same way for the median.
- **Slip mask.** Cells whose DEM changed by more than 1 m between epochs are excluded, so that the 2023 storm slips do
  not count as crown loss. A tree with under half its circle valid is dropped.
- **Static features:** elevation and slope from the E1 DEM; P95(CHM, E1); distance to the nearest track (OSM
  `highway` = path, footway or track, Overpass on the plan date).

## 3. Models and tests

Logistic regression (standardised features, no penalty tuning), out-of-fold predictions from spatially blocked
5-fold cross-validation:
- blocks are 500 m grid cells;
- folds are assigned by block, with seed 20261023;
- the split is repeated 5 times with seeds 20261023–27, and predictions are averaged over repeats.

Models:
- **Change:** ΔP95, Δcover15, ΔP50.
- **Static:** elevation, slope, P95(E1), distance to track.
- **Static + change.**

Intervals come from a bootstrap over blocks of the out-of-fold predictions (B = 2,000).

- **H1 (LiDAR change separates trees graded symptomatic in 2014–15).** AUC of the change model.
  - **Supported** if the AUC is at least 0.70 and the 95% interval's lower bound is above 0.60.
  - **Refuted** if the upper bound is below 0.70.
  - **Inconclusive** otherwise.
- **H2 (change adds to what is already known).** AUC(static + change) − AUC(static).
  - **Supported** if it is at least 0.05 and the lower bound is above 0.
  - **Refuted** if the upper bound is below 0.05.
  - **Inconclusive** otherwise.

## 4. Secondary analyses (reported, not confirmatory)

1. **Time-aligned labels:** H1 and H2 with the 2021 survey's labels.
2. **Severe only:** status 4 against status 1.
3. **Radius:** 10 m and 20 m.
4. **No slip mask.**
5. **Stable-area check:** the distribution of ΔP95 at 1,000 random forest points away from any record, to show
   between-epoch artefacts (season, point density, registration).
6. **Mean change by group:** mean ΔP95 and Δcover15 by status group, with block-bootstrap intervals.

## 5. Limits stated in advance

- **Position error.** GPS positions under canopy are often 5–15 m off, and crowns overlap. The 15 m circle and the
  radius checks mitigate this.
- **Already crownless.** Some severe trees may have lost their crowns before 2016–18, which caps the change they can
  show.
- **Epoch differences.** The two epochs differ in season, sensor and point density.
- **What the labels are.** Ground symptoms are not a confirmed infection (soil PCR is sparse).

## 6. Care note

Kauri are taonga. The Waitākere Ranges are under a rāhui placed by Te Kawerau ā Maki, and much of the forest is
closed to protect kauri. This study enters no forest and uses only open remote-sensing data and the council's public
survey layer. Results are reported in aggregate: no map or table of individual symptomatic trees beyond what the
council already publishes. A method like this belongs with the kaitiaki and the council's kauri programme, which the
lab cannot engage directly. The care note does not gate the study.

## 7. Outputs

- `results/tables/`: `trees.csv` (features by OBJECTID, no coordinates), `primary.json`, secondary analyses.
- `results/figures/`.
- `deviations.md` records any change before the result it affects.
