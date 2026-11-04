# Deviations from plan.md

## D1 — 2026-11-04 22:06 NZDT — implementation notes and the QLP exclusion, decided before any rotation period was compared with an orbit

**Data access (no analytic effect).**
- **Gaia.** The archive caps anonymous jobs at 50,000 rows, and its default compressed VOTable truncated a 22,784-row
  result to 19,100 without error. The orbits were fetched in eight random_index slices as plain VOTable, each checked
  against a COUNT(*) of the same filter: 181,529 SB1 and SB1C orbits, 183,919 DR2 neighbours.
- **TIC.** Matched through MAST's catalogue filter on the Gaia DR2 ID (CDS XMatch timed out).
- **Light curves.** The plan's per-sector bulk scripts were used for TESS-SPOC. For QLP the per-sector scripts list
  every FFI star (about 25 GB of text over throttled connections), so QLP files were found through MAST's observation
  table queried by TIC ID instead. The same files result either way.

**Flux columns.** TESS-SPOC uses PDCSAP_FLUX. QLP uses SAP_FLUX, because QLP's KSPSAP_FLUX is spline-detrended on
sub-day scales, which would remove rotation signals.

**Ellipsoidal check before doubling.** The plan's ellipsoidal-or-double-spot class (period within 5% of P_orb / 2) is
applied to the undoubled periodogram period. Otherwise an ellipsoidal signal doubled by the ACF rule would land on
P_orb and pass as synchronized. This was written into classify.py before it was run.

**QLP excluded from the primary analysis.** The period search was run on all 139,513 star-sector light curves
(70,531 TESS-SPOC, 68,982 QLP where TESS-SPOC has none). The detection rule (FAP < 1e-5) fires in 84.7% of TESS-SPOC
sectors but in 99.5% of QLP sectors, so on QLP it does not discriminate. The QLP detections also look instrumental:
- 49% of them fall at 9–13 d, against 8.6% for TESS-SPOC;
- their median amplitude is 3.4 ppt, against 1.35 ppt.

QLP's SAP flux carries the scattered-light and orbit-scale trends that TESS-SPOC's PDC removes. The primary analysis
therefore uses TESS-SPOC sectors only: 17,112 of the 23,212 stars with any light curve. The 6,100 stars with QLP only
drop out of the primary. As a sensitivity, QLP sectors are detrended with a quadratic per continuous segment (data
split at gaps over 1 d) and searched with the same rules.

This was decided from the detection statistics above alone. No period had been classified against an orbital period,
and classify.py had not been run.
