# Plausibility (G3)

## Three binaries traced from the Gaia orbit to the classification (`results/tables/g3_traces.json`)

Chosen as the first, by Gaia source_id, among cool stars (4,000–6,200 K) with P_orb < 10 d and at least two detecting
TESS-SPOC sectors, one for each outcome.

| outcome | TIC | Teff | P_orb (d) | e | P_ps (d) | sector periods (d) | P_rot (d) | amplitude |
|---|---|---|---|---|---|---|---|---|
| synchronized | 438260593 | 5,718 K | 3.698 | 0.085 | 3.545 | 3.76, 3.55, 3.55, 3.81, 3.68 | 3.68 | 2.6 ppt |
| sub-synchronous | 400005586 | 5,141 K | 3.846 | 0.107 | 3.600 | 4.27, 4.31, 4.15, 4.21, 4.41, 4.17 | 4.24 | 9.5 ppt |
| ellipsoidal or double-spot | 113799193 | 6,087 K | 4.616 | 0.008 | 4.616 | 2.30, 2.31 | 2.30 | 35 ppt |

- **The first star** rotates at its orbital period. With e = 0.085 the pseudo-synchronous target is 4% shorter, and
  the star still passes.
- **The second shows a weakness of the plan's rule.** Its 4.24-day period is 10% longer than its orbital period, at
  the edge of the window, but 18% longer than the pseudo-synchronous period implied by e = 0.107. Gaia's
  eccentricities for near-circular orbits are biased upward by noise: the median e is 0.07–0.14 even below 3 d. So
  the Hut correction can move the target away from a star that is in fact synchronized. Post hoc, testing against
  P_orb directly moves 262 detections into the synchronized class and 118 out of it (`posthoc.json`).
- **The third** is a textbook ellipsoidal variable: a large semi-amplitude (75 km/s) and a 35 ppt signal at exactly
  half the orbital period. It is excluded from the primary analysis, as planned.

## Injection-recovery (`results/tables/completeness.csv`)

There were 35,840 injections into 1,792 TESS-SPOC light curves without a detection (all such stars, fewer than the
planned 2,000), and 75% were recovered overall.
- **Amplitude dominates recovery:** 5% at a semi-amplitude of 0.005–0.01%, 31% at 0.01–0.03%, 82% at 0.03–0.07%,
  and 95–98% above 0.07%.
- **Recovery is flat in period** (72–77% across 0.3–13 d), so completeness weights hardly change the synchronized
  share; the weighted and unweighted results agree (0.205 and 0.232 for cool stars).

## Do the periods look like rotation?

- **There is a synchronized population.** The ratio P_rot / P_ps among detections has a sharp peak at 1: 796 stars
  in the bin [1, 1.19), against about 300 in each neighbouring bin, on a broad background.
- **Much of the background is probably not the primary's rotation.**
  - The synchronized share rises with data quality: 0.10 with one detecting sector, 0.27 with two, 0.35 with three
    and 0.40 with four or more. By TESS magnitude it is 0.26 for bright stars and 0.12 for faint ones.
  - TESS pixels are 21 arcsec across, so light from neighbours and systematics enters the faint, single-sector cases
    most.
  - Against Gaia DR3's own rotation periods (G4), only 30% of the overlapping stars agree within 10% and 59% agree at
    no harmonic.
- **The spectroscopic check sees almost no clearly super-synchronous rotation:** 0.5% of cool and 2.8% of hot stars
  with Gaia vbroad. That is consistent with synchronized or slower rotation, but vbroad is too coarse to separate
  synchronized from sub-synchronous rotation.

## Why H2 could not be estimated

Neither share reaches one half at any orbital period, so neither midpoint exists.
- **Synchronized share** (among detections): it peaks at 0.34 for 3–5 d.
- **Circular share** (SB1C or e < 0.05): it peaks at 0.38 for 5–7 d. Gaia's SB1 eccentricities rarely fall below
  0.05 even for orbits that are certainly circular, because noise biases them upward.

The plan's e < 0.05 definition was therefore unsuited to Gaia orbits. Bashi et al. (2023) used the upper envelope of
e against P instead.
