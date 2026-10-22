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
