# Preregistration: did Auckland's 2016 upzoning cost tree canopy?

Lead: `auckland-nz-upzoning-canopy-lidar-did` (research-lab/leads.json). Written 2026-10-03 and committed to git
before any 2013 or 2024 LiDAR tile is processed and before any canopy measure is tabulated by zone.

## What has been seen before writing (disclosure)

- **LiDAR tiles.** File listings and LAS headers (bounds, point counts) for the OpenTopography collections. The class
  codes of one tile from each epoch, which all use ground 2, vegetation 3/4/5 and building 6, plus noise 7/18 and
  overlap 12.
- **Zoning.** The Unitary Plan residential base-zone polygons and their areas: Single House 84.6 km², Mixed Housing
  Suburban 149.0 km², Mixed Housing Urban 80.5 km², Terrace Housing and Apartment Buildings 26.4 km².
- **One 2016–18 tile processed as a code test.** It covered 409 cells of 30 m, with overall canopy (≥ 3 m) 6.4% and
  building 4.1%. Nothing was tabulated by zone.
- **No 2013 or 2024 canopy has been computed.**

Every later departure goes to `deviations.md` with a timestamp from `date`.

## 1. Question

The Auckland Unitary Plan, operative in part from November 2016, upzoned large areas of existing suburbs to Mixed
Housing Urban (MHU) and Terrace Housing and Apartment Buildings (THAB), while other suburbs stayed Single House (SH).
Did upzoned residential land lose more tree canopy between the 2016–18 and 2024 LiDAR surveys than comparable Single
House land?

## 2. Data

- **LiDAR (classified point clouds from OpenTopography's S3 mirror of LINZ and Auckland Council LiDAR).**

  | Epoch | Collections | Captured |
  |---|---|---|
  | E0 | Auckland_2013 | 2013 |
  | E1 | NZ16_NAuckland, NZ16_SAuckland | Aug 2016 – Aug 2018 (north); 2016–17 (south) |
  | E2 | NZ24_Auckland | Apr – Nov 2024 |

  Only tiles intersecting the residential zones buffered by 50 m are used: 2,202, 2,413 and 2,210 tiles.
- **Zoning.** Auckland Council's open "Unitary Plan Base Zone" layer, residential zones 19 (SH), 18 (MHS), 60 (MHU)
  and 8 (THAB).
- **Statistical Area 2 (SA2) 2023 boundaries** (Stats NZ open ArcGIS service), used for clustering.
- **Auckland Council local board boundaries** (open ArcGIS service).
- **Train station locations** from the Auckland Transport GTFS feed.

## 3. Measurement (fixed in `code/process_tiles.py`)

**Points.** Points classified noise (7, 18) or overlap (12), and withheld points, are dropped.

**Ground and height.**

- The ground is the mean class-2 elevation per 1 m cell. Empty cells take the nearest ground cell's value.
- A point's height above ground is its elevation minus the ground of its 1 m cell.

**1 m cell flags.**

- **Valid:** the cell has any point.
- **Canopy:** a vegetation point (class 3, 4 or 5) at least 3 m above ground. 2 m and 5 m are secondary thresholds.
  Trees over roofs count as canopy.
- **Building:** the cell has a class-6 point.

**Analysis unit: a 30 m × 30 m cell on the NZTM grid.** Its canopy share in an epoch is the number of canopy 1 m cells
over the number of valid 1 m cells. A unit is included if all of these hold:

- at least 90% of its area lies in one residential zone;
- it has at least 810 valid 1 m cells (90% coverage) in every epoch;
- it was built up at E0 and at E1, meaning building 1 m cells are at least 10% of valid cells in both. This excludes
  greenfield land and land first developed between 2013 and 2017.

Where the two E1 collections overlap, a unit takes the collection with more valid cells.

**Groups.**

- High dose (treated): MHU + THAB.
- Low dose: Mixed Housing Suburban (MHS).
- Control: SH.

## 4. Primary analysis

**Outcome.** ΔC = canopy share at E2 minus canopy share at E1, in percentage points.

**Model.** OLS of ΔC on high-dose and low-dose indicators, with SH as the reference.

- **Stratum fixed effects** (coarsened exact matching): local board × E1 canopy band × distance to the city centre ×
  E1 collection (north or south).
  - E1 canopy bands: 0–5, 5–15, 15–30, 30–50 and > 50%.
  - Distance to the city centre is measured to Waitematā/Britomart station, NZTM 1757560, 5920780, in bands of 0–5,
    5–10, 10–20 and > 20 km.
- **Covariate:** distance to the nearest train station (km).
- **Sample:** strata without both high-dose and SH units are dropped.
- **Weighting and standard errors:** units are weighted equally, and standard errors are clustered by SA2.

**Pre-trend.** The same model with ΔC_pre = canopy at E1 minus canopy at E0.

**Decision rules.** β_high is the high-dose minus SH estimate.

| Verdict | Condition |
|---|---|
| Supported | β_high ≤ −1.0 pp, its 95% CI below 0, and the pre-trend estimate within ±0.5 pp |
| Contradicted | the 95% CI lower bound > −1.0 pp (an excess loss of 1 pp ruled out), and the pre-trend within ±0.5 pp |
| Inconclusive | otherwise, including any case where the pre-trend lies outside ±0.5 pp |

## 5. Secondary analyses (no verdicts)

- **Dose response.** The low-dose (MHS) estimate.
- **Mechanism.**
  - Split units into redeveloped (building share changed by at least 10 pp between E1 and E2) and not redeveloped.
  - Report the excess loss within each part and the share of the total coming from redevelopment.
- **Canopy thresholds.** 2 m and 5 m.
- **Zone-boundary sample.** Units within 100 m of an SH boundary with MHU or THAB, with stratum fixed effects
  replaced by boundary-segment pairs (nearest 500 m boundary piece).
- **Trend-adjusted estimate.** β_high minus the pre-trend estimate scaled by the epoch gap (7 years post vs about 4
  years pre). This is reported especially if the pre-trend rule fails.
- **Annualised rates,** using the tile capture years.
- **Collections.** North vs south E1 collections, separately.

## 6. Threats (fixed now)

- **Zoning was not random.** MHU and THAB were placed near centres and transit. Stratification and the pre-trend test
  only partly address this.
- **The current zoning layer** may include changes made after 2016, such as private plan changes. Zones were not
  reconstructed to 2016.
- **Sensor and classification differences between epochs** can create artefactual canopy change.
  - The design compares groups within an epoch pair, so only differences in artefacts between zones bias it, for
    example from building density.
  - Overlap points (class 12) are dropped in all epochs.
- **Timing.** E1 straddles the plan's start (Nov 2016), so some upzoning effect may already be in the E1 baseline.
  That biases the estimate toward 0.
- **Season.** Captures fall in different seasons, so deciduous trees may appear leaf-off, affecting all zones.
- **Intensification rules after 2022 (MDRS / Plan Change 78)** may have partly treated control land late in the
  window.

## 7. Review and reporting

- An independent reviewer agent checks code and results before any verdict.
- The report opens with "In plain terms".
- Derived unit tables are committed; rasters are not (they are large).
