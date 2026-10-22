# Deviations

## D1 — 2026-10-22 22:06 NZDT — Landsat source for the 1999–2015 epoch and the guard (before any area is measured)

The scene searches show that Landsat Collection 2 Level-2 (Planetary Computer; Earth Search lists the same
requester-pays assets) holds almost no pre-2013 scenes over these atolls: one Landsat 7 scene for Funafuti in
1999–2015. Google's public Landsat archive, Collection 1 Level-1, frozen in January 2022, holds 52 Landsat 7 scenes for
the same path/row over 1999–2013. Level-2 surface reflectance is not produced for many open-ocean acquisitions; the
Level-1 scenes exist.

So:
1. **Source.** The 1999–2015 epoch (E1) uses Collection 1 Level-1 scenes from Google's public bucket: Landsat 5 TM,
   7 ETM+ and 8 OLI, both tiers.
   - **Reflectance:** top-of-atmosphere, from each scene's MTL coefficients (REFLECTANCE_MULT and ADD). The sun-angle
     term cancels in MNDWI and NDWI.
   - **Clear pixels:** the Collection 1 BQA band — not fill, cloud bit off, cloud confidence and cloud-shadow
     confidence low.
   - **Candidate scenes:** WRS-2 path/rows taken from each atoll's Level-2 scene IDs, with an MTL cloud cover of at
     most 80%.
2. **The sensor-step guard** compares Collection 1 Landsat 8 with Sentinel-2 at 30 m over **2016–2021**, since
   Collection 1 ends in 2021. The plan said 2016–2023. The guard thus checks the same Level-1 product that E1 uses.
3. **Sentinel-2 (E2)** is unchanged: L2A, with each item's own scale and offset (Earth Search applies the baseline-04.00
   offset and records it).

The early epoch is thin even so: about 50 Landsat 7 scenes per path/row over 15 years, before cloud and SLC-off gaps.
Islets failing the plan's minimum of 20 usable scenes over 6 years drop out of H1. If too few remain, H1 cannot be
estimated, and that will be reported.

## D2 — 2026-10-22 22:16 NZDT — the clear-pixel rule and reflectance clipping (after a 6-scene test, before any rate is computed)

A test on the six least cloudy Funafuti Sentinel-2 scenes showed two problems with the plan's measurement.

1. **The cloud classes are wrong for atolls.**
   - *What happened:* within the islet rings, Sen2Cor's scene classification labels much of the land as cloud of
     medium probability (class 8) or unclassified (class 7). That is the known confusion of bright coral sand and
     roofs with cloud. Under the plan's rule (at least 95% of the buffered area in classes 4–6 or 11), almost no scene
     would count as clear over sandy or built-up islets.
   - *What matters instead:* the real risk to an area estimate is cloud or shadow over the water around the islet,
     where it would read as land.
   - *The new rule:*
     - **Water around the islet** (the buffer minus the islet dilated by two pixels): any cloud or shadow (classes 3,
       8, 9, 10) on at most 5% of it.
     - **The islet itself:** high-probability cloud, cirrus or shadow (classes 3, 9, 10) on at most 5%.
     - **Valid data:** at least 99% of the buffer.
     - **Landsat:** the same split, from the Collection 1 BQA. Around the islet: the cloud bit, or cloud or shadow
       confidence of medium or more. On the islet: high cloud confidence, or shadow confidence of medium or more.
   - *Classification:* Otsu's threshold and the land mask use every valid pixel in the buffer, so they no longer
     depend on the cloud classes.
2. **Negative reflectance broke MNDWI.**
   - *What happened:* Sentinel-2's −0.1 offset makes dark-water reflectance slightly negative, which sent MNDWI far
     outside [−1, 1] (an Otsu threshold of 13.5 in the test).
   - *The fix:* reflectance is now clipped at 0 before MNDWI and NDWI are computed, for both sensors.

In the corrected test, measured areas are close to the OpenStreetMap areas: an islet mapped at 43.7 ha measures
39.6–44.7 ha in most scenes. About 39% of islet-scene pairs pass on these scenes. No rate or trend has been computed.

## D3 — 2026-10-22 22:21 NZDT — rates on a common reference area (before any rate is computed)

On Funafuti, Landsat at 30 m measures islet areas well above the OSM areas (54.5 against 43.7 ha; 13.9 against
5.4 ha), from mixed shoreline pixels. The plan expresses each rate as a percentage of the islet's own epoch median, so
an inflated Landsat median would shrink 1999–2015 rates relative to Sentinel-2 rates and build a spurious difference
into H1. Rates are now the Theil–Sen slope of the tide-corrected area in m² per year, divided by one sensor-independent
reference, the islet's OSM area, in both epochs. Uncorrected rates use the same reference. Everything else in plan §3
is unchanged.

## D4 — 2026-10-22 22:58 NZDT — two measurement bugs fixed, and every area re-measured (before any rate is computed)

A check of measured against OSM area per islet and scene on Funafuti (no rates or trends) found two faults.

1. **NaN in the Otsu step.**
   - *The fault:* where both reflectances clip to 0, MNDWI is 0/0. The NaN made the guard `v.min() < v.max()` false,
     so the code fell back to a threshold of 0, which counts bright coral sand (MNDWI slightly above 0) as water and
     gave near-zero areas. The D2 rewrite had dropped the earlier finite-value filter.
   - *The fix:* non-finite values are now removed before Otsu. A scene with no finite threshold is left without an
     area.
2. **Sentinel-2 offsets.**
   - *The fault:* some items with processing baseline 04.00 or later carry the −0.1 offset in their metadata, but
     their data no longer contains it. Open-ocean SWIR reads 4 DN in one such item, impossible if a +1000 offset were
     present, so subtracting 0.1 drove water and sand reflectance negative.
   - *The fix:* within each window, if the 1st percentile of valid SWIR DN is below 500, the offset is taken as
     already removed, and the metadata offset is not applied.

**Results.**
- All area files were re-measured. The faulty ones are kept in `data/areas_buggy/` and are not used.
- After the fixes, on Funafuti's Sentinel-2 series, MNDWI with Otsu (the preregistered primary) is the most precise
  index. Its residual standard deviation after tide regression is 12.1% of islet area, against 14.4% for NDWI. Its
  tide correlation is −0.90, and no area is zero. The index is unchanged.
- Landsat measurements are much noisier: a residual standard deviation of about 49% of islet area.

## D5 — 2026-10-23 00:49 NZDT — which OSM features are islets, and gross-failure scenes (before any rate is computed)

A check of measured against OSM area per islet and scene (no rates or trends computed) found that some OSM features
are not land.
- **Penrhyn.** 28% of clear Sentinel-2 measurements so far are under a quarter of the OSM area. Failure is
  concentrated in small features (1–2.5 ha): 12 fail in 69–90% of their scenes. It does not depend on tide (the same
  share in every tide quintile). Imagery of one (penrhyn_126) shows a submerged lagoon coral knoll. The scene that
  "measures" it as land has a cloud over it that the scene classification missed.
- **Tarawa.** All of the near-zero rows belong to one 181 ha polygon (tarawa_004). It is mostly intertidal reef flat,
  with dry sand only in small patches.

The plan takes islets from OSM at 1 ha or more and has no rule for features that are not land. Measuring a
submerged knoll or a reef flat gives either zero or cloud contamination, and the tide regression is not robust to
either.

**Rules** (in `rates.py`, applied the same way to every atoll, sensor and epoch):
1. **Land screen.** An OSM feature is an islet for this study if its Sentinel-2 MNDWI-Otsu area, uncorrected for
   tide, is at least 25% of its OSM area in at least half of its clear Sentinel-2 scenes. The screen uses only
   Sentinel-2, so one decision covers both epochs. It uses the whole record's share, not its time course.
   - Features that fail are listed in `results/tables/land_screen.csv` with their detection share by year.
   - A feature whose share is at least 0.5 in 2016–2018 and below 0.5 in 2024–2026 is flagged as a possible real
     loss. It is reported and inspected, not silently dropped, and is excluded from the primary analysis but included
     in a sensitivity analysis.
2. **Gross-failure scenes.** Within each retained islet, for each sensor family (Sentinel-2; Landsat 5/7/8) and each
   area series, a scene's value is set aside if its log area is more than 5 scaled MADs (1.4826 × MAD) from the
   islet's median. Theil–Sen is already robust to such values; the tide regression is not.
3. **Not measurable.** An islet whose window fits inside no Sentinel-2 tile is never measured. These are counted and
   listed, with no change to the code (Tarawa: 1 of 33 features of 1 ha or more).

**Unchanged:**
- The D3 reference: rates are expressed as a percentage of the OSM area.
- Every threshold and estimand in plan §3–4.

`land_screen.csv` reports the Sentinel-2-to-OSM area ratio among retained islets, so that any dilution by
over-drawn OSM polygons is visible.

**D5 revised — 2026-10-23 00:52 NZDT, still before any rate is computed.** The land screen as first written above
(Otsu area at least 25% of OSM area in half of the scenes) was tested on the QA outputs only. It kept most Penrhyn
lagoon knolls. Imagery of one (penrhyn_036, kept with 62%) shows why: in a window that is all water, Otsu's threshold
splits shallow water over the knoll from deep lagoon water, so the knoll top is classed as "land" in about 60% of
scenes, independent of tide.

The screen now uses a physical test instead:
- **Dry land:** MNDWI below 0, meaning SWIR brighter than green. No depth of water gives that, because water
  absorbs SWIR within centimetres.
- **The rule:** a feature is an islet if dry land covers at least 10% of its OSM area in at least half of its clear
  Sentinel-2 scenes. The possible-loss flag uses the same test, by year.

**On the atolls measured so far** (Penrhyn and Kapingamarangi still running):
- The share is bimodal. On Penrhyn, 123 features are at or below 5% and 37 are at or above 80%.
- Every Funafuti, Kapingamarangi and Majuro feature passes. Tarawa loses tarawa_004 (the reef flat). Kwajalein loses
  kwajalein_056 (4.7 ha, never dry) and two islets of about 1 ha (shares 0.41 and 0.44). kwajalein_078 is flagged
  as a possible loss.
- **Gross-failure values set aside:**
  - MNDWI-Otsu: Sentinel-2 0.6%, Landsat 2.3%;
  - NDWI: 1.5% and 2.1%;
  - MNDWI at 0: 1.6% and 23% (at 30 m, mixed shoreline pixels often keep a small islet's MNDWI above 0, and that
    series is a sensitivity analysis only).
- The median Sentinel-2-to-OSM area ratio among retained islets is 1.14 (10th–90th percentile 0.93–1.98).

## D6 — 2026-10-23 01:13 NZDT — the guard's minimum span (AFTER the first full rates run)

**This change was made after seeing the first run's output.** That run (`logs/rates.log`, first version) gave:
- the sensor-step guard: **0 islets**, so H1 read "not testable";
- H1 without the guard: D = +0.15%/yr (−0.52 to +0.86), Inconclusive;
- H2: Supported.

**The fault.** The plan requires rates to rest on at least 20 usable scenes spanning at least 6 years. That is right
for the epochs (17 and 10 years), and it was satisfiable in the plan's guard window, 2016–2023: 6 of 8 years. D1 cut
the guard window to 2016–2021, because Collection 1 ends in 2021. Sentinel-2 over these atolls starts in late 2015 or
2016, so a 6.0-year span became impossible and every islet dropped out of the guard. D1 did not notice this.

**The change.** The guard requires a span of at least 4.5 years, which is 75% of its 6-year window, the same share as
the plan's 6 of 8. The 20-scene minimum and everything else are unchanged.

**Why the change cannot pick the verdict.** H1 without the guard is already Inconclusive. The guard can therefore
only decide between "not testable" and "Inconclusive". The report gives both readings.
