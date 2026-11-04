# Tidal synchronization in Gaia's close binaries shows up clearly in TESS light curves, but too diluted by measurement to test where it stops; the apparent step at the Kraft break appears to follow spot detectability

*Gaia DR3 SB1 orbits (181,529) were cut to 49,960 main-sequence binaries. Rotation periods for the 23,577 with
orbits shorter than 12 days and a TIC match came from 70,531 TESS-SPOC full-frame-image light curves. A rotation
counts as synchronized if it lies within 10% of the orbital (or pseudo-synchronous) period. The plan was committed
before any data were downloaded. This version follows an independent review that returned "fix first" (D2).*

**Verdict: H1 Refuted; H2 Inconclusive.**

- **H1 (more than 70% synchronized below 6,200 K, under 30% above 6,500 K, a transition under 400 K wide): Refuted.**
  - Among cool binaries (4,000–6,200 K, P_orb < 10 d) with a detected period, **20.5%** are synchronized (95%
    interval 18.7–22.5%, completeness-weighted); among hot binaries (6,500–7,500 K), **9.3%** (6.9–12.1%).
  - These are about 6.5% of all cool binaries with light curves, since only 29% have a usable period.
- **Synchronization is real, at well above chance.** Pairing each detected period with a random orbital period gives
  0.09 (cool) and 0.05 (hot), against observed shares of 0.22 and 0.12 (unweighted).
- **There is no clear step at the Kraft break once the signal is credible.**
  - The full sample's step from 0.21 to 0.09 appears to track how detectable spots are rather than tides.
  - Restricted to credible signals (amplitude above 2 ppt, seen in at least two sectors), the shares are **0.42**
    (0.38–0.46, n 614) for cool and **0.37** (0.27–0.46, n 104) for hot binaries, with overlapping intervals.
  - These credible-signal results are post hoc (D2). 38 of the 104 hot signals exceed 20 ppt, the scale of ellipsoidal
    variation in F stars; without them the hot share is 0.42 (n 66). The hot interval still allows a drop of up to a
    third.
- **H2 (synchronization extends to longer orbital periods than circularization): Inconclusive.**
  - The synchronized share never reaches one half, so P_sync,50 is undefined. This is most likely a symptom of the
    dilution above rather than a property of the binaries.
  - The plan's circular criterion, e < 0.05, also fails, because Gaia's eccentricities are biased upward by noise.
  - With a noise-aware criterion (e consistent with zero; post hoc), the circularization cutoff is 4.1–5.9 days
    across the three Teff bins, rising with Teff. That is the opposite of Bashi et al. (2023), who found 6.5 falling to
    2.5 d on the same orbits, and the indicator depends on Gaia's error estimates, so this cutoff is not reliable.

## In plain terms

In close pairs of stars, tides are expected to lock each star's spin to its orbit, the way the Moon always shows
Earth the same face. Theory says this should happen readily for cooler, Sun-like stars, and much less for hotter
stars above about 6,200 K. We tested this on about 17,000 binaries whose orbits Gaia measured, reading each star's
spin from starspot dimming in TESS light curves.

Locked spins are clearly there, at two to three times the rate chance would give. But our automatic period finder also
picked up many signals that are not the star's spin: noise and, probably, light from neighbouring stars. These
dilute the locked fraction to about a fifth. When we keep only clear, repeated signals, about two in five binaries
look locked, with no clear difference between hot and cool. The drop we first reported above 6,200 K appears to come from hot stars' spots being
harder to detect, not from weaker tides.

So the test we planned could not be done cleanly with these data. It needs either vetted light curves, as earlier
eclipsing-binary studies used, or spin measured from spectral line broadening.

## What was asked

- **Prior work.** Gaia DR3's SB1 orbits enabled a population study of circularization (Bashi et al. 2023).
  Synchronization had been measured only in eclipsing samples: in Lurie et al. (2017), 79% of visually vetted Kepler
  eclipsing binaries with P < 10 d; Hobson-Ritz et al. (2025); Hadad et al. (2025).
- **The lead** (`astronomy-gaia-sb1-tess-synchronization-boundary`) asked whether the non-eclipsing Gaia sample,
  with TESS periods, shows the boundary tracking the Kraft break.

## How it was done

- **Sample.** SB1 and SB1C solutions with parallax_over_error > 10, within −1.0 to +0.75 mag of the Pecaut &
  Mamajek dwarf sequence, with Teff from dereddened BP−RP. TIC IDs came through Gaia DR2 identifiers, unambiguous
  matches only.
- **Light curves.** TESS-SPOC (PDCSAP) for every available sector. QLP light curves were excluded from the primary
  analysis, because the detection rule fired in 99.5% of their sectors (D1). QLP-only stars are fainter, hotter and
  on shorter orbits.
- **Periods.** Lomb–Scargle over 0.2–13 d per sector, with FAP < 1e-5 counting as a detection. This rule is not
  selective: it fires in 84.7% of TESS-SPOC sectors.
  - A star's period is the median over detecting sectors.
  - It is *inconsistent* if sectors disagree by more than 10%.
  - An autocorrelation rule doubles double-dip periods.
- **Ambiguous signals**, excluded from the primary analysis: ellipsoidal or double-spot (P_orb / 2), possible beaming,
  and multi-periodic pulsators.
- **Synchronized** means within 10% of P_orb, or of Hut's (1981) pseudo-synchronous period when e ≥ 0.05. Shares are
  weighted by 1/completeness from 35,840 injected spot signals.

## Results

| synchronized share (cool / hot, P_orb < 10 d) | result | status |
|---|---|---|
| **primary (weighted)** | **0.205 / 0.093** | preregistered |
| chance (P_orb permuted) | 0.09 / 0.05 | post hoc |
| unweighted | 0.23 / 0.11 | preregistered secondary |
| pulsators and beaming included | 0.29 / 0.25 | preregistered secondary |
| ellipsoidal-or-double-spot counted as synchronized | 0.26 / 0.66 | preregistered secondary |
| bounds over all stars with light curves | 0.06–0.18 / 0.02–0.09 | preregistered secondary |
| within 300 pc | 0.22 / 0.12 | preregistered secondary |
| **credible signals only** (> 2 ppt, ≥ 2 sectors) | **0.42 / 0.37** | post hoc |
| majority-cluster rescue of "inconsistent" stars | 0.25 / 0.15 | post hoc |
| no ACF doubling | 0.25 / 0.14 | post hoc |
| against P_orb instead of the pseudo-synchronous period | 0.26 / 0.09 | post hoc |
| with detrended QLP | 0.23 / 0.11 | D1 sensitivity, uninformative |

- **The share tracks data quality.** It is 0.10 with one detecting sector, 0.27 with two, 0.35 with three and 0.40
  with four or more; 0.26 for bright stars and 0.12 for faint ones. Synchronized stars also have cleaner Gaia
  astrometry (median RUWE 1.09 against 1.17 for sub-synchronous ones), consistent with light from other stars
  contaminating the rest.
- **The Teff logistic's step is not located.** Refitted after review, its width sits at the 10 K lower bound in 82%
  of bootstrap fits, and its midpoint interval runs from 5,160 to 6,380 K.
- **Hot ellipsoidal signals.** 62% of hot binaries with a usable signal show one at half the orbital period. Tidal
  distortion produces that whether or not the star is synchronized.

## What this does and does not show

- **Shown: synchronized rotation is common enough to see above chance in non-eclipsing Gaia binaries.** It is
  strongest at orbital periods of 2–6 d among cool stars.
- **Not shown: the level, or where it stops.** The automatic TESS periods are too contaminated:
  - in a visual audit, 16 of 30 periods had no coherent signal;
  - only 41 of the 135 stars that also have a Gaia DR3 rotation period agree with it, a joint disagreement, since Gaia's
    sparse-sampled periods are noisy too.

  Both the step at the Kraft break and the H2 comparison are lost in that dilution.
- **The rules shape the level** (D2):
  - Hut's pseudo-synchronous target, applied to noise-inflated Gaia eccentricities, misclassifies stars that rotate
    at P_orb;
  - the 10% window misses the slightly sub-synchronous population Lurie et al. found;
  - the pulsator rule catches spotted synchronized stars (cool "pulsators" are 47.5% synchronized).
- **Limits.**
  - **Sample.** RVS-bright, biased towards large semi-amplitudes; some companions are luminous.
  - **Periods** are limited to 13 d.
  - **QLP-only stars** are absent from the primary (D1).
  - **G7 is not met** for the visual audit: one rater, who could see the class labels.
  - **Completeness weighting** (1/C) up-weights low-amplitude detections, which the audit suggests are mostly noise.
    The unweighted shares are similar (0.23 / 0.11).

## Process and deviations

- **Preregistration:** `plan.md`, committed before any data were downloaded.
- **Deviations:**
  - D1: data access, the ellipsoidal test before doubling, and QLP excluded (written before the first
    classification but committed later);
  - D2: fixes after review.
- **Post hoc analyses:** `code/posthoc.py` and `posthoc2.py`, labelled in the table.
- **Gates:**
  - G1: in the plan.
  - G2: `results/tables/coverage.json`.
  - G3: `results/plausibility.md`.
  - G4: `results/tables/g4_check.json`, covering Gaia DR3 rotation periods (135 overlap: 41 agree, 15 at a harmonic,
    79 at none) and the visual audit (`results/figures/g4_folded.png`).
  - G5: `review/overclaim_check.md`.
  - G6: `results/attribution_ledger.csv`.
  - G7: not met for the visual audit (D2).
- **Independent review:** fix first (12 findings); fixes in D2; confirmation pending.

## Reproducing it

`code/gaia.py`, `sample.py`, `tic_match.py`, `lc_index.py`, `qlp_index.py`, `download.py`, `periods.py`,
`classify.py`, `inject.py`, `analyse.py`, `posthoc.py`, `posthoc2.py`, `g3_traces.py`, `g4_check.py`, `g4_visual.py`
and `coverage_lc.py`.
