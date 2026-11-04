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

## D2 — 2026-11-05 07:30 NZDT — fixes after the independent review (verdict: fix first)

Everything here followed the review. Items 4 and 9 run preregistered secondaries that had not been run; the rest is
post hoc and is labelled so in the report.

1. **A chance null** (finding 1). Permuting P_orb among detections within each Teff group gives the synchronized
   share that coincidence alone produces: 0.093 cool and 0.048 hot. Observed (unweighted): 0.224 and 0.123.
2. **Credible signals** (finding 2): semi-amplitude above 2 ppt and at least two detecting sectors. The shares are
   0.42 (0.38–0.46, n 614) for cool stars and 0.37 (0.27–0.46, n 104) for hot ones, against chance levels of 0.15 and
   0.06. On credible signals there is no clear step at the Kraft break. The full-sample step tracks spot
   detectability, and the report's title and verdict are corrected accordingly.
3. **Majority-cluster rescue of "inconsistent" stars** (finding 3). Where most detecting sectors agree within 10%
   after harmonisation, only those sectors are used: 5,445 detections, with shares of 0.24 cool and 0.15 hot.
4. **Preregistered secondary 2 in full** (finding 4). With pulsators and possible-beaming stars classified by the same
   rule, the shares are 0.29 cool and 0.25 hot. Cool "pulsators" are 47.5% synchronized, so the pulsator rule catches
   spotted, synchronized stars. It also runs before the ellipsoidal rule, which lets harmonic-rich ellipsoidal
   signals through as pulsators (G4 panel 25).
5. **Completeness** (finding 5). The 339 detections dropped as "C < 0.1" were in fact outside the injection grid
   (amplitude above 2% or period below 0.3 d); `analyse.py` now counts them separately.
6. **The Teff logistic** (finding 6). It is refitted with Teff in thousands of kelvin and a grid of starting values.
   The first fit's midpoint sat on a starting value, and its "width of about 300 K" was an artefact. The refitted
   width, and how often it reaches its lower bound, are in `primary.json`.
7. **Without ACF doubling** (finding 7): shares of 0.25 cool and 0.14 hot. 102 doubled detections were synchronized
   before doubling.
8. **D1** (finding 8). D1 was written before classify.py was first run (the same shell command, D1 first), but it
   was committed eight hours later. Blindness therefore rests on that ordering and file times, not on git. QLP-only
   stars are fainter (median Tmag 11.8 against 11.3), hotter (6,470 K against 6,300 K) and on shorter orbits (3.7 d
   against 4.5 d). The detrended-QLP sensitivity cannot test the exclusion, because its detection rate is still
   97.5%.
9. **Gates and secondaries** (findings 9 and 12):
   - G7 applies to the visual audit and is not met: one rater, who could see the class labels. The audit is
     descriptive.
   - **G4's catalogue was swapped.** The plan called for an independent published TESS rotation catalogue. VizieR is
     unreachable from this machine, so Gaia DR3's own rotation periods were used instead.
   - The panel-25 note is corrected.
   - Preregistered secondary 5 (states by Teff and P_orb, including 10–12 d) and the RUWE distribution are now
     reported: median RUWE is 1.09 for synchronized stars against 1.17 for sub-synchronous ones.
   - The G3 single-star comparison (a positive control outside the sample) was not done.
   - The detection rule is stated plainly as non-selective: it fires in 84.7% of TESS-SPOC sectors.
10. **H2 with a noise-aware circular criterion** (finding 11): e consistent with zero (e < 2σ_e) or SB1C. P_circ,50
    is 4.1 d (4,000–5,500 K), 5.3 d (5,500–6,200 K) and 5.9 d (6,200–7,000 K). P_sync,50 is still undefined, because
    the synchronized share stays below one half, a symptom of the dilution above. H2 stays Inconclusive.

**Confirmation-pass edits** (2026-11-05):
- **Majority cluster.** It now uses classify.py's own max/min ≤ 1.10 test, giving 6,110 detections and shares of
  0.25 cool and 0.15 hot.
- **Hot credible signals.** 38 of the 104 exceed 20 ppt; without them the hot share is 0.42 (n 66).
- **The post hoc circularization cutoff** runs opposite to Bashi et al. (2023), and the report says so.
- **Weighting.** The completeness-weighting caveat is added, and the 338 grid-miss drops are recorded in
  coverage.json.
- **Gaia comparison.** The disagreement with Gaia's rotation periods is called a joint disagreement.
