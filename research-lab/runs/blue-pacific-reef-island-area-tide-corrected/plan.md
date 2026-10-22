# Plan: are Pacific reef islets losing area faster since 2016, once each image is corrected for the tide?

Lead: `blue-pacific-reef-island-area-tide-corrected` (Blue Pacific Horizons). Written 2026-10-22, before any satellite
scene was processed or any island area computed.

**Examined beforehand (nothing computed on areas):**
- The STAC catalogues: Earth Search Sentinel-2 L2A COGs, and Planetary Computer Landsat Collection 2 Level-2 (Earth
  Search's Landsat assets are requester-pays).
- One timing probe of a windowed read.
- UHSLC station metadata.
- The OSM islet inventory of the eight atolls below (`code/inventory.py`, `data/inventory.csv`).

**Prior work, and what is new.**
- Island area from Landsat and Sentinel-2 with per-scene tide correction already exists: CoastSat.islands and Cuttler
  et al. 2020.
- Pacific-wide change has been mapped: Sengupta, Ford, Kench and Perry 2025, 568 islands on 42 atolls.
- Most studies use tide-insensitive shoreline proxies (Kottermair et al. 2025).
- **New here:**
  - one pipeline applied to two epochs, 1999–2015 and 2016–2026, to test for *acceleration* since 2016;
  - a measurement of how much a missing tide correction biases rates, on the same islets.

**Care.**
- Island land area bears on statehood, migration and habitability, and on communities who have not been consulted.
- Results are reported in aggregate, by atoll and pooled, with no islet-level habitability framing and no ranking of
  islands.
- This is a measurement of satellite-visible land area at a fixed water level, not of habitability.

## 1. Population

- **Atolls.** The eight with an on-atoll UHSLC tide gauge recording through both epochs:
  - Tarawa (gauge 2), Majuro (5), Funafuti (25), Kwajalein (55), Kanton (13);
  - Kiritimati (11), Penrhyn/Tongareva (24), Kapingamarangi (29).

  An on-atoll gauge removes the gauge-to-site transfer function, the weakest part of the lead's design. That design
  aimed at 20 atolls; this one trades breadth for a direct water level.
- **Islets.** OSM coastline rings, from the inventory of 2026-10-22.
  - **Primary set:** non-engineered islets of at least 1 ha for the Sentinel-2 epoch (326 islets), and of at least
    5 ha for the cross-epoch comparison (128). Landsat's 30 m pixels cannot measure smaller islets.
  - **Engineered islets** are those whose ring touches an airstrip, harbour, pier, breakwater, groyne, port,
    embankment or causeway in OSM (38 islets). They are excluded from the primary estimand and reported apart.

## 2. Measurement

- **Scenes.**
  - Sentinel-2 L2A, 2016-01-01 to 2026-09-30: green (B03, 10 m), SWIR1 (B11, 20 m, upsampled), NIR (B08) and SCL.
  - Landsat 5 TM, 7 ETM+ (with SLC-off gaps masked) and 8 OLI, 1999-01-01 to 2015-12-31: green, SWIR1, NIR and
    QA_PIXEL.
  - Scenes with a catalogue cloud cover above 80% are skipped.
- **Per islet and scene:**
  - The area of interest is the islet ring buffered by 60 m (Sentinel-2) or 90 m (Landsat).
  - The scene is used for that islet only if at least 95% of the area is clear: SCL classes 4–6 and 11 for
    Sentinel-2, QA_PIXEL clear for Landsat, and no SLC gap.
  - Land is MNDWI = (green − SWIR1)/(green + SWIR1) below a threshold. **Primary:** Otsu's threshold within the area.
    **Sensitivity:** a fixed threshold of 0, and NDWI.
  - Area = land pixels × pixel area, limited to the connected land component overlapping the ring.
- **Water level.** The gauge's hourly sea level (UHSLC research-quality, extended by fast-delivery), linearly
  interpolated to the acquisition time and expressed relative to the gauge's mean over 1999–2026.
  - Wave set-up is not modelled; it is a stated limitation.
  - Acquisitions within 3 hours of a gauge gap are dropped.

## 3. Tide correction and rates

- **Tide response.** For each islet and sensor family (Landsat, Sentinel-2), area is regressed on water level, using
  ordinary least squares with a Huber-robust fit as a sensitivity. The slope β is the islet's tide response.
  - Corrected area = area − β × water level, the area at mean sea level.
  - Uncorrected area = the raw area.
- **Rates.** For each islet and epoch:
  - each area is expressed as a percentage of the islet's epoch median;
  - the rate is the Theil–Sen slope over time (%/yr), with at least 20 usable scenes spanning at least 6 years.

## 4. Hypotheses and decision rules

- **Sensor-step guard** (required before H1).
  - On 2016–2023, where Landsat 8 and Sentinel-2 overlap, Sentinel-2 is resampled to 30 m and each islet's
    corrected-area rate is measured with both sensors.
  - If the mean between-sensor rate difference has a 95% interval outside ±0.2%/yr, the cross-epoch comparison is
    not valid and H1 is reported as not testable.
- **H1 (no acceleration).** D is the mean corrected rate for 2016–2026 minus the mean corrected rate for 1999–2015,
  over the primary cross-epoch set, from a mixed model with islets nested in atolls. A negative D means faster loss.
  - **Supported** if the 95% interval's lower bound is at or above −0.2%/yr.
  - **Refuted** if its upper bound is below −0.2%/yr.
  - Otherwise **Inconclusive.**
- **H2 (tide bias).** On the Sentinel-2 epoch's primary set, the mean absolute difference between uncorrected and
  corrected rates is at least 0.3%/yr.
  - **Supported** if its 95% interval's lower bound is at least 0.3.
  - **Refuted** if its upper bound is below 0.3.
  - Otherwise **Inconclusive.**
- **Intervals.** Islets are resampled within atolls (B = 2,000, seed 20261022), and the mixed model's interval is
  reported alongside.
- **Secondaries:**
  - rates by atoll;
  - engineered islets apart;
  - the sensitivity thresholds (fixed MNDWI 0, NDWI);
  - robust tide slopes;
  - islets of 1–5 ha in the Sentinel-2 epoch;
  - an audit of Digital Earth Pacific Coastlines: its annual shoreline rates of change near each islet against the
    corrected and uncorrected rates (correlation and bias).

## 5. Order of work

1. `code/tides.py`: gauge series.
2. `code/scenes.py`: STAC searches.
3. `code/measure.py`: windowed reads, grouped by islet clusters within each scene, processed on the fly. Only per-islet
   areas and quality flags are stored.
4. `code/rates.py`: tide slopes, rates, the guard, H1 and H2.
5. DEP audit, figures and report.

Deviations are logged in `deviations.md` with times from the clock, before the results they could affect.
