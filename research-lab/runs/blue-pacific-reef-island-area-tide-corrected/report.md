# Pacific reef islets: tide correction changes a decade's area trend by about 2% a year, and Landsat and Sentinel-2 disagree too much to test for acceleration

*Islet land area was measured in every usable Sentinel-2 image from 2016 to September 2026 and every usable Landsat
5/7/8 image from 1999 to 2015, at the eight Pacific atolls with their own tide gauge. Each area was corrected to mean
sea level with the gauge reading at the image time. Rates are Theil–Sen slopes, as a percentage of the islet's
OpenStreetMap (OSM) area per year.*

**Verdict: H1 not testable (Inconclusive without the guard); H2 Supported.**

- **H2 (a missing tide correction biases decadal rates by at least 0.3%/yr): Supported.**
  - Over 150 islets in 6 atolls, the mean absolute difference between uncorrected and corrected Sentinel-2-era rates
    is **2.08%/yr** (95% interval 1.57 to 2.65).
  - **The bias is not noise.** With each islet's water levels shuffled across its images, the same statistic is
    0.29%/yr. The bias tracks each islet's tide sensitivity times the drift in water level at image time (r = 0.97).
    The drift runs from about −25 mm/yr (Tarawa) to +22 mm/yr (Majuro) over the decade, and +33 mm/yr at the two
    Kiritimati islets.
  - **The sign differs by atoll.** Uncorrected images overstate growth at Funafuti (+2.8%/yr) and overstate loss at
    Kwajalein, Majuro and Tarawa (about −1%/yr). Pooled over atolls the biases largely cancel (mean signed −0.28%/yr).
- **H1 (no acceleration of loss since 2016): not testable by the preregistered rule.**
  - **The guard fails.** On 13 islets measured with both sensors over 2016–2021, Landsat 8 Collection 1 rates exceed
    Sentinel-2 rates at 30 m by **+1.24%/yr** (0.46 to 2.07). The cross-sensor difference allowed is ±0.2%/yr.
  - **Without the guard,** the 1999–2015 and 2016–2026 epochs differ by D = +0.15%/yr (−0.52 to +0.86) over 33
    islets in 4 atolls. That is Inconclusive, with no sign of faster loss.
- **What the islets did in 2016–2026.** The mean tide-corrected rate is −0.28%/yr (−0.59 to +0.04) over 150
  islets. Atoll means run from −0.8%/yr (Tarawa) to +0.9%/yr (Funafuti).
- **Two inventory findings.**
  - 126 of Penrhyn's 163 OSM "islets" of 1 ha or more are submerged lagoon coral knolls. They are never dry in
    Sentinel-2.
  - Sentinel-2 imagery of Kapingamarangi and Kanton begins only in 2022.

## In plain terms

Low coral islands in the Pacific are often said to be shrinking as the sea rises. Satellite studies have mostly found
the opposite: most islands are stable or growing. But how big an island looks from space depends on the tide when the
picture was taken. At low tide a wide beach and reef flat are dry; at high tide they are under water.

We measured islands at eight atolls in every usable satellite picture since 1999. Each atoll has its own tide gauge,
so we corrected every picture to the same water level. Over the last decade, skipping that correction changes an
island's measured trend by about 2% a year. That is larger than most of the trends themselves. It happens because the
water level at the moment the satellites pass over drifted up at some atolls and down at others. Funafuti's islands
look as if they were growing quickly when they were not. Several atolls look as if their islands were shrinking
faster than they were.

We also wanted to know whether islands are shrinking faster now than before 2016. We could not answer it fairly. The
older satellite (Landsat) and the newer one (Sentinel-2) gave different trends for the same islands in the same
years. So any difference between the decades could be the satellites rather than the islands. Taken at face value,
the comparison shows no speed-up.

Once corrected for the tide, the average island changed by about −0.3% a year over the decade, which is close to zero.

## What was asked

The lead (`blue-pacific-reef-island-area-tide-corrected`, Blue Pacific Horizons) asked two questions:
- whether reef-island loss has accelerated since 2016, once each image is corrected for the tide;
- how much the missing correction biases rates.

Published work with per-scene tide correction exists: CoastSat.islands; Cuttler et al. 2020; Sengupta, Ford, Kench
and Perry 2025 (568 islands on 42 atolls). What is new here is one pipeline applied to two epochs at atolls with an
on-atoll gauge, plus a direct measure of the bias on the same islets.

The plan (`plan.md`) was committed before any scene was processed.

## How it was done

- **Atolls:** the eight with an on-atoll UHSLC gauge recording through both epochs: Tarawa, Majuro, Funafuti,
  Kwajalein, Kanton, Kiritimati, Penrhyn (Tongareva) and Kapingamarangi.
- **Islets:** OSM coastline rings of at least 1 ha (364 features). Rings touching an airstrip, harbour, causeway or
  similar are treated as engineered and reported apart.
- **The land screen (D5).** A feature counts as an islet only if dry land covers at least 10% of it in at least half
  its clear Sentinel-2 scenes. Dry land means MNDWI below 0, which no depth of water gives. 228 of the 361 measured
  features pass (`results/figures/F3_land_screen.png`).
  - The first version of the rule used the Otsu area. It kept Penrhyn's lagoon knolls, because in an all-water
    window Otsu splits shallow from deep water. It was replaced before any rate was computed.
- **Areas:**
  - **Measurement:** MNDWI with an Otsu threshold inside each islet's buffered ring (60 m for Sentinel-2, 90 m for
    Landsat), keeping the connected land that touches the ring.
  - **Cloud screening:** a split rule. The water around the islet must be free of any cloud class; the islet itself
    only of high-confidence cloud, because the scene classification marks bright coral sand as cloud (D2).
  - **Sources:** Sentinel-2 L2A for 2016–2026 (161,845 islet-image records, including those rejected for cloud).
    Landsat Collection 1 Level-1 for 1999–2015 (27,401 records), since Collection 2 has almost no pre-2013 scenes
    over these atolls (D1).
  - **Gross failures** (more than 5 robust standard deviations from the islet's median) were set aside: 0.6% of
    Sentinel-2 and 2.2% of Landsat values.
- **Tide correction:**
  - Each image gets the gauge's hourly water level, interpolated to the image time.
  - Each islet's area is regressed on that level, and the fitted response is removed, giving the area at mean sea
    level.
  - 1.7% of images had no gauge reading within 2 hours.
- **Rates:** Theil–Sen slopes of area against time, needing at least 20 images over at least 6 years. They are
  expressed as a percentage of the islet's OSM area (D3), so that Landsat's mixed-pixel inflation of absolute area
  does not rescale its rates.
  - Retained islets measure a median 1.14 times their OSM area in Sentinel-2.
- **Tests:**
  - **The guard:** Landsat 8 against Sentinel-2 at 30 m over the overlap. The window became 2016–2021, because
    Collection 1 ends in 2021 (D1). Its minimum span is 4.5 years (D6).
  - **H1:** the epoch difference D on non-engineered islets of at least 5 ha.
  - **H2:** the mean absolute uncorrected-minus-corrected rate on Sentinel-2 islets of at least 1 ha.
  - **Intervals:** islets resampled within atolls (B = 2,000), with a mixed model alongside.

## Results

### H2: the tide bias (`results/figures/F1_tide_bias.png`)

![Uncorrected against corrected rates, and the bias against tide slope times water-level drift](results/figures/F1_tide_bias.png)

| atoll | islets | corrected rate (%/yr) | uncorrected minus corrected (%/yr) | mean absolute bias | water-level drift at image times (mm/yr) | median tide slope (% of area per m) |
|---|---|---|---|---|---|---|
| Funafuti | 16 | +0.94 | +2.76 | 4.77 | −19 | −72 |
| Kwajalein | 52 | −0.65 | −1.13 | 2.26 | +2 | −35 |
| Majuro | 29 | −0.16 | −1.12 | 1.91 | +22 | −54 |
| Penrhyn | 31 | +0.08 | +0.62 | 0.92 | −5 | −57 |
| Tarawa | 20 | −0.81 | −0.97 | 1.47 | −25 | +2 |
| Kiritimati | 2 | −2.30 | +2.78 | 2.78 | +33 | +3 |

- **The preregistered statistic:** 2.08%/yr (1.57 to 2.65), so Supported.
- **The noise floor (post hoc):** 0.29%/yr with water levels permuted within islets. 88% of islets exceed their own
  floor.
- **The mechanism (post hoc).** Satellites pass at a fixed local time, so they sample the tide at a slowly drifting
  phase, on top of year-to-year sea-level swings. At an islet whose visible area falls by 35–70% per metre of water,
  a drift of 20 mm/yr in sampled water level becomes a trend of 0.7–1.4%/yr in uncorrected area.
  - The bias equals tide slope × drift with r = 0.97 (panel b).
  - Tarawa's islets barely respond to the tide (median +2% per metre). Its bias comes from the few that do.
- **Islet size:** the bias is largest for islets of 1–5 ha (mean 3.1%/yr), against 0.7–1.3%/yr for larger ones.

### H1: acceleration, and why it cannot be tested here (`results/figures/F2_guard_and_epochs.png`)

![Guard and H1 epochs](results/figures/F2_guard_and_epochs.png)

- **The guard.** 13 non-engineered islets of at least 5 ha had enough images from both sensors over 2016–2021.
  Landsat's rates exceed Sentinel-2's by 1.24%/yr (0.46 to 2.07), six times the tolerance. The epochs are measured
  with different sensors, so a cross-epoch difference cannot be attributed to the islets.
  - This guard result rests on a post-result change. The first run found no guard islets at all: D1's shortened
    window made the plan's 6-year span impossible. D6 relaxed the span to 4.5 years after that run, and records that
    the change could only move H1 between "not testable" and "Inconclusive".
- **H1 without the guard:**
  - D = +0.15%/yr (−0.52 to +0.86) over 33 islets in 4 atolls;
  - mixed model +0.97 (−1.55 to +3.49);
  - Inconclusive, pointing if anywhere to slower, not faster, loss.
  - **Sensitivity analyses:**
    - NDWI: −0.65 (−1.96 to +0.60);
    - robust tide slopes: −0.13 (−0.79 to +0.47);
    - fixed MNDWI threshold: −0.77 (−1.37 to −0.13), on 19 islets only. At 30 m that series often drops small
      islets.
- **The early epoch is thin:** a median of 25 usable Landsat images per islet over 1999–2015, against 76 Sentinel-2
  images per islet over 2016–2026.

### The decade's rates

- **Pooled:** the mean tide-corrected rate over 150 non-engineered islets in 6 atolls is −0.28%/yr (−0.59 to +0.04;
  median −0.25).
- **Engineered islets** (23): −0.58%/yr.
- **Islets of 1–5 ha** (79): −0.01%/yr.
- **No rates for Kapingamarangi and Kanton.** Earth Search holds Sentinel-2 imagery for them only from 2022, too
  short for a rate.
- **Kiritimati** contributes only 2 islets of at least 1 ha that were retained and are not engineered. The main
  island is engineered and too large for one image window.

### The inventory (`results/figures/F3_land_screen.png`)

![Land screen](results/figures/F3_land_screen.png)

- **Penrhyn.** 126 of its 163 OSM features of at least 1 ha are submerged coral knolls in the lagoon.
- **Elsewhere,** the screen removes:
  - one 181 ha Tarawa polygon that is mostly intertidal reef flat;
  - one 4.7 ha Kwajalein feature that is never dry;
  - three small features at Kiritimati and two islets of about 1 ha at Kwajalein.
- **One feature is flagged as a possible loss:** kwajalein_078, 1.3 ha. It was dry in at least half the scenes of
  2016–2018 and in fewer than half of 2024–2026. It is excluded from the primary analysis; including it changes
  nothing (the H1 set is unchanged).

### Digital Earth Pacific Coastlines (secondary)

- **Method.** DEP's annual shoreline positions within 100 m of each islet were turned into an areal rate: the mean
  seaward rate × perimeter / area.
- **Islet level.** Over 146 islets, DEP's 2016–2023 rate does not correlate with this study's corrected rate (r =
  −0.20) or uncorrected rate (r = −0.15). Mean absolute differences are 8–10%/yr.
- **Atoll level,** DEP is closer to the corrected rates at:
  - Funafuti: DEP −1.8%/yr, against +1.0 corrected and +4.2 uncorrected;
  - Majuro: −0.2, against −0.2 and −1.3;
  - Tarawa.

  It is closer to the uncorrected rates at Kwajalein and Penrhyn.
- **Reading.** Shoreline-transect rates turned into islet areas do not agree with area time series at this scale.
  Neither can validate the other here.

## What this does and does not show

- **Tide correction is not optional for decadal island-area trends from optical satellites,** at least at atolls
  where islet area responds strongly to water level.
  - Without it, rates at single atolls are off by 1–3%/yr, in directions set by how the overpass samples the tide.
  - Pooled regional means are less affected, because the drifts differ in sign across atolls.
  - This supports correcting each image, as CoastSat.islands and recent Pacific-wide studies do. It cautions against
    uncorrected annual composites.
- **Acceleration since 2016 is not established here, and neither is its absence.**
  - The sensors disagree by more than any plausible acceleration.
  - The early epoch rests on 25-odd Landsat images per islet.
  - Taken at face value, the epochs show no speed-up.
- **Measured over 2016–2026,** corrected islet areas changed by −0.3%/yr on average. That is consistent with the
  literature's finding that most atoll islands are stable on decadal scales.
- **Limits:**
  - **Measurement:**
    - The rates measure satellite-visible land at mean sea level, including beach above that level, not vegetated
      or habitable area.
    - OSM rings define both the islets and the reference area.
    - The tide response is assumed linear and constant within each epoch.
  - **Coverage:**
    - Six atolls give rates; four give H1 islets.
    - Kapingamarangi and Kanton lack a Sentinel-2 decade.
  - **The guard** rests on 13 islets.
- **Care.** The plan's care note stands. Results are reported by atoll and pooled, with no islet-level habitability
  framing and no ranking of islands. The communities of these atolls have not been consulted, and this is a
  measurement study, not an assessment of their land.

## Process and deviations

- **Preregistration:** `plan.md`.
- **Deviations** (`deviations.md`):
  - **D1:** Landsat Collection 1 Level-1 for the early epoch; guard window 2016–2021.
  - **D2:** split cloud rule; reflectance clipped at 0.
  - **D3:** rates as a percentage of OSM area.
  - **D4:** two measurement bugs fixed (an Otsu NaN fallback; a doubly applied Sentinel-2 offset), and every area
    re-measured.
  - **D5:** the land screen (revised once) and the gross-failure rule.
  - **D6:** the guard's minimum span, changed **after** the first rates run, with that run's output kept in
    `results/tables/h1_h2_run1_before_D6.json`.

  D1–D5 were all made before any rate was computed.
- **Post hoc and descriptive:**
  - the H2 noise floor and mechanism (`code/h2_diag.py`);
  - the pooled and per-atoll rates;
  - the DEP comparison.
- **Independent review:** queued (Fable), per the lab's pacing rule.

## Reproducing it

1. `code/inventory.py`, `code/tides.py`, `code/scenes.py`, `code/gcp_scenes.py`: inventory, gauges, catalogues.
2. `code/run_measure.sh`, which drives `code/measure.py ATOLL s2|l1`: areas, about 23,000 scenes, resumable.
3. `code/rates.py`: land screen, tide correction, rates, guard, H1 and H2 (`results/tables/h1_h2.json`,
   `islet_rates.csv`, `land_screen.csv`).
4. `code/h2_diag.py`, `code/dep_audit.py`, `code/dep_compare.py`, `code/figures.py`.
