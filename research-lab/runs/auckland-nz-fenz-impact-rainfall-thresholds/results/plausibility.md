# Plausibility (G3)

## Three storm days traced: FENZ rows and gauges to the models

| day | panel places | called out | median 6-h rain | median rarity | depth model | rarity model |
|---|---|---|---|---|---|---|
| Auckland, 27 Jan 2023 | 168 | 55 (33%) | 135 mm | 2.71 | 35% | 37% |
| Hawke's Bay, 14 Feb 2023 | 91 | 10 (11%) | 61 mm | 1.56 | 8% | 10% |
| Nelson and Tasman, 27 Jun 2025 | 64 | 8 (13%) | 56 mm | 0.97 | 3% | 4% |

- **Auckland.** The fitted probabilities match the observed share of places calling out (33%). The median 6-hour rain
  of 135 mm, 2.7 times the local median annual maximum, is consistent with the record-breaking storm of that day.
- **Hawke's Bay (Cyclone Gabrielle).** Ten of 91 panel suburbs called out.
  - FENZ's coding explains part of the shortfall: of 155 Hawke's Bay exposures on 13–14 February 2023, 41 are coded
    "Wind storm, Tornado, Cyclone" and only 21 "Flood" (93 have no natural-disaster type).
  - So the flood outcome undercounts flood-related callouts during a named cyclone.
- **Nelson and Tasman.** Both models underpredict. The day's 6-hour rain was only moderately rare, which points to
  longer-duration rain the 6-hour term does not capture.

## Three place-days traced from source to model (D4; `posthoc.json: traces`)

Each 6-hour total is recomputed exactly from the gauge's raw records (`g4_check.exact_d6`) and matches the panel.

| place-day | flood exposures | gauge distance | 6-h rain (panel = raw) | M6 | rarity | depth model | rarity model |
|---|---|---|---|---|---|---|---|
| Auckland held-out flood day, 4 Mar 2025 | 1 | 1.3 km | 14.8 mm | 43.3 mm | 0.34 | 0.10% | 0.11% |
| Tasman, 27 Jun 2025 (largest 6-h rain among flooded places) | 6 | 8.8 km | 78.4 mm | 49.9 mm | 1.57 | 27% | 36% |
| West Coast, 1 Jul 2024, no callout, over 20 mm | 0 | 6.7 km | 33.8 mm | 80.4 mm | 0.42 | 0.07% | 0.07% |

On the Tasman day the rarity model gives the higher probability (36% against 27%): 78 mm is one and a half times the
local median annual maximum. On the West Coast day, 34 mm is under half the local median annual maximum, and
neither model expects a callout.

## Base rates

- **Training years:** 765 flood place-days among 2.19 million (0.035%).
- **Held-out year:** 64 among 316,853 (0.020%). FY2024/25 had fewer flood callouts than the wet 2021–2023 years.
  This matches FENZ's own yearly flood counts (152 in 2023/24, 306 in 2024/25, against 904–925 in 2021/22–2022/23).
- **Log-loss scale.** Both models cut the held-out log-loss of a no-rain baseline by about a third (0.00176 to
  0.00117–0.00121). The difference between them is 3.3% of the depth model's log-loss, or 7.2% of its skill.

## Invariants checked

- The daily 6-hour maximum per gauge reproduces the HIRDS lead's annual maxima (variant S3) exactly, for all 3,543
  gauge-years present in both (`code/g3_invariant.py`, `results/tables/g3_invariant.json`).
- The window audit (G4): 30 random suburb-days recomputed exactly from raw records match the panel in all 30 (after D3; before D3, a different random 30 were within 0.6%).
- The geocoding audit (G4): a random 100 panel places reverse-geocoded with OpenStreetMap all fall in their recorded
  region (D4). The earlier council-neighbour check could not see wrong points in an adjacent council.
