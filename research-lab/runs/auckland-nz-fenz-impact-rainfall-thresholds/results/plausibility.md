# Plausibility (G3)

## Three storm days traced: FENZ rows and gauges to the models

| day | panel suburbs | called out | median 6-h rain | median rarity | depth model | rarity model |
|---|---|---|---|---|---|---|
| Auckland, 27 Jan 2023 | 174 | 55 (32%) | 135 mm | 2.71 | 33% | 35% |
| Hawke's Bay, 14 Feb 2023 | 91 | 10 (11%) | 61 mm | 1.56 | 8% | 10% |
| Nelson and Tasman, 27 Jun 2025 | 70 | 8 (11%) | 56 mm | 0.97 | 3% | 4% |

- **Auckland.** The fitted probabilities match the observed share of suburbs calling out (32%). The median 6-hour rain
  of 135 mm, 2.7 times the local median annual maximum, is consistent with the record-breaking storm of that day.
- **Hawke's Bay (Cyclone Gabrielle).** Ten of 91 panel suburbs called out.
  - FENZ's coding explains part of the shortfall: of 155 Hawke's Bay exposures on 13–14 February 2023, 41 are coded
    "Wind storm, Tornado, Cyclone" and only 21 "Flood" (93 have no natural-disaster type).
  - So the flood outcome undercounts flood-related callouts during a named cyclone.
- **Nelson and Tasman.** Both models underpredict. The day's 6-hour rain was only moderately rare, which points to
  longer-duration rain the 6-hour term does not capture.

## Base rates

- **Training years:** 765 flood suburb-days among 2.32 million (0.033%).
- **Held-out year:** 64 among 336,457 (0.019%). FY2024/25 had fewer flood callouts than the wet 2021–2023 years.
  This matches FENZ's own yearly flood counts (152 in 2023/24, 306 in 2024/25, against 904–925 in 2021/22–2022/23).
- **Log-loss scale.** Both models cut the held-out log-loss of a no-rain baseline by about a third (0.00166 to
  0.00111–0.00115). The difference between them is 3.4% of the depth model's log-loss, or 7.6% of its skill.

## Invariants checked

- The daily 6-hour maximum per gauge reproduces the HIRDS lead's annual maxima exactly, for all 3,509 gauge-years
  tested (same rules, same windows).
- The window audit (G4): 30 random suburb-days recomputed exactly from raw records are within 0.6% of the panel.
- The geocoding audit (G4): every panel suburb's assigned gauge is in its own council (866) or a neighbouring one
  (88).
