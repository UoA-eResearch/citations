# TESS finds tidally synchronized rotation in a fifth of Gaia's close binaries, not most, and the share steps down at the Kraft break; but much of the shortfall looks like measurement

*Gaia DR3 SB1 orbits (181,529) were cut to 49,960 main-sequence binaries. Rotation periods for the 23,577 with
orbits shorter than 12 days and a TIC match came from 70,531 TESS-SPOC full-frame-image light curves. A rotation
counts as synchronized if it lies within 10% of the orbital (or pseudo-synchronous) period. Shares are weighted by
injection-recovery completeness. The plan was committed before any data were downloaded.*

**Verdict: H1 Refuted; H2 could not be estimated as planned (Inconclusive by the plan's rule).**

- **H1 (more than 70% synchronized below 6,200 K, under 30% above 6,500 K, a transition under 400 K wide): Refuted.**
  - Among cool binaries (4,000–6,200 K, P_orb < 10 d) with a detected period, **20.5%** are synchronized (95%
    interval 18.7–22.5%), far below the hypothesised 70%.
  - Hot binaries (6,500–7,500 K) are at **9.3%** (6.9–12.1%), below 30% as hypothesised.
  - The step between them is near where theory puts it. A profile likelihood places the transition at about 6,300 K, at
    the Kraft break, with a 10–90% width of about 300 K. The preregistered fit's midpoint (6,200 K) sat on one of its
    starting values.
- **H2 (synchronization extends to longer orbital periods than circularization): not estimable.** Neither share
  reaches one half at any period, so neither 50% cutoff exists. The synchronized share peaks at 0.34 (3–5 d) and the
  circular share at 0.38 (5–7 d). The plan's circular criterion, e < 0.05, does not suit Gaia orbits: noise biases
  their eccentricities upward (median 0.07–0.14 even below 3 d).
- **The 20% is better read as a floor than as a measurement.**
  - The share rises steeply with data quality: 0.10 with one detecting sector, 0.27 with two, 0.35 with three, 0.40
    with four or more; 0.26 for bright stars and 0.12 for faint ones.
  - In a visual audit of 30 classified light curves, 16 showed no coherent signal at the pipeline's period.
  - Of the 135 stars that also have a Gaia DR3 rotation period, only 30% agree with it.
  - Kepler eclipsing binaries with P < 10 d are 79% synchronized (Lurie et al. 2017).

## In plain terms

In close pairs of stars, tides are expected to lock each star's spin to its orbit, the way the Moon always shows
Earth the same face. Theory says this should happen readily for cooler, Sun-like stars, whose outer layers churn, and
much less for hotter stars above about 6,200 K, where that churning layer thins out. We tested this on about
17,000 binaries whose orbits Gaia measured, reading each star's spin from the dimming of starspots in TESS
light curves.

We found the step in the expected place: cool stars are about twice as likely as hot ones to be locked, and the
change happens near 6,300 K. But only about a fifth of the cool stars looked locked, not the large majority we
expected. Much of that gap appears to come from the measurement rather than the stars. Many of the "spin periods" our
automatic method found are probably noise or light from neighbouring stars, and the locked fraction climbs towards
half among the stars with the best data. A second test, comparing how fast circular orbits and locked spins give way
at longer orbits, could not be done, because Gaia's orbit shapes are too noisy for the definition we chose in
advance.

## What was asked

- **Prior work.** Gaia DR3's SB1 orbits enabled a population study of circularization (Bashi et al. 2023).
  Synchronization had been measured only in eclipsing samples (Lurie et al. 2017; Hobson-Ritz et al. 2025; Hadad et
  al. 2025) and single clusters.
- **The lead** (`astronomy-gaia-sb1-tess-synchronization-boundary`) asked whether the non-eclipsing Gaia SB1 sample,
  with TESS rotation periods, shows the synchronization boundary tracking the Kraft break, and whether
  synchronization reaches longer orbital periods than circularization.

## How it was done

- **Sample.** SB1 and SB1C solutions with parallax_over_error > 10, within −1.0 to +0.75 mag of the Pecaut & Mamajek
  dwarf sequence, with Teff from dereddened BP−RP. TIC IDs came through Gaia DR2 identifiers, unambiguous matches only.
- **Light curves.**
  - **TESS-SPOC** FFI light curves (PDCSAP flux) for every available sector.
  - **QLP** light curves, where TESS-SPOC had none, were searched too, but excluded from the primary analysis before
    any classification (D1). On QLP the detection rule fired in 99.5% of sectors, with half the "periods" at
    instrumental timescales.
- **Periods.** Lomb–Scargle over 0.2–13 d per sector, a detection meaning FAP < 1e-5. A star's period is the median
  over detecting sectors; it is *inconsistent* if those disagree by more than 10%. An autocorrelation rule handles
  double dips.
- **Ambiguous signals**, excluded from the primary analysis:
  - ellipsoidal or double-spot: a period at P_orb / 2, tested before any doubling;
  - possible Doppler beaming;
  - multi-periodic pulsators.
- **Synchronized** means within 10% of P_orb, or of Hut's (1981) pseudo-synchronous period when e ≥ 0.05. Shares are
  weighted by 1/completeness from 35,840 injected spot signals.

## Results

| group (P_orb < 10 d) | detections | synchronized share (95% CI) |
|---|---|---|
| cool, 4,000–6,200 K | 1,770 | **0.205** (0.187–0.225) |
| hot, 6,500–7,500 K | 566 | **0.093** (0.069–0.121) |

Of 17,112 binaries with TESS-SPOC light curves, 3,661 had a usable period. The other classes:

| class | binaries |
|---|---|
| inconsistent across sectors | 7,267 |
| pulsator | 2,142 |
| ellipsoidal or double-spot | 1,893 |
| no detection | 1,792 |
| possible beaming | 357 |

| sensitivity (cool / hot share) | result | status |
|---|---|---|
| unweighted | 0.23 / 0.11 | preregistered secondary |
| within 300 pc | 0.22 / 0.12 | preregistered secondary |
| bounds over all stars with light curves | 0.06–0.18 / 0.02–0.09 | preregistered secondary |
| ellipsoidal-or-double-spot counted as synchronized | 0.26 / 0.66 | preregistered secondary |
| periods harmonised across sectors (P vs P/2) | 0.22 / 0.12 | post hoc |
| detrended QLP added (D1) | 0.23 / 0.11 | promised in D1 |
| synchronized measured against P_orb, not P_ps | 0.26 / 0.09 | post hoc |

- **Hot ellipsoidal signals.** 66% of hot detections are signals at half the orbital period. Tidal distortion
  produces these whether or not the star is synchronized, so they cannot rescue H1.
- **Gaia line broadening (vbroad)** finds almost no clearly super-synchronous rotation (0.5% cool, 2.8% hot), but it
  cannot separate synchronized from slower rotation.
- **The pseudo-synchronous target hurts.** Measuring against P_orb directly moves 262 detections into the
  synchronized class and 118 out, because Gaia's noise-inflated eccentricities shift the Hut target.

## What this does and does not show

- **The location of the transition matches theory.** The synchronized share halves across about 6,300 K, the Kraft
  break, in every variant.
- **Its level does not, and the level is not trustworthy.**
  - **Spurious periods.** A white-noise false-alarm threshold admits many periods with no visible coherent signal
    (16 of 30 audited).
  - **Blending.** TESS's 21-arcsecond pixels blend neighbours, and the share rises from 0.10 to 0.40 with the number
    of detecting sectors.
  - **Rule choices.** The 10% window misses the slightly sub-synchronous short-period population Lurie et al. found
    (about 13% slow); the ellipsoidal exclusion removes many short-period synchronized stars; and the Hut target
    misclassifies stars on noise-inflated eccentricities.
- **H2 failed on a design flaw.** The circular criterion should have been an eccentricity envelope suited to Gaia's
  noise, as Bashi et al. used, not e < 0.05.
- **Not shown:** a reliable absolute synchronized fraction, or the ordering of the synchronization and
  circularization cutoffs.
- **Limits.**
  - **Selection.** The sample is RVS-bright and biased towards large semi-amplitudes.
  - **Unseen companions.** Some companions are not dark, and some SB1s are inner pairs of triples.
  - **Period range.** Periods are limited to 13 d.
  - **QLP.** Stars observed only by QLP are absent from the primary (D1).
  - **G4 audit.** It was one rater who could see the class labels.

## Process and deviations

- **Preregistration:** `plan.md`, committed before any data were downloaded.
- **Deviations:** D1, covering data-access notes, the ellipsoidal test before doubling, and QLP excluded from the
  primary (decided before classification).
- **Post hoc** analyses are labelled in the table (`code/posthoc.py`, `results/tables/posthoc.json`).
- **Gates:**
  - G1: in the plan; no visual check changed any label.
  - G2: `results/tables/coverage.json`, stages from orbits through classification.
  - G3: `results/plausibility.md`, with three traces, completeness, and why H2 failed.
  - G4: `results/tables/g4_check.json`. Against Gaia DR3 rotation periods, 135 stars overlap: 41 agree, 15 at a
    harmonic, 79 at none. The visual audit of 30 folded light curves (`results/figures/g4_folded.png`) found 14 clear
    and 16 not visibly coherent.
  - G5: `review/overclaim_check.md`.
  - G6: `results/attribution_ledger.csv`.
  - G7: does not apply.
- **Independent review:** queued.

## Reproducing it

`code/gaia.py`, `sample.py`, `tic_match.py`, `lc_index.py` (TESS-SPOC), `qlp_index.py`, `download.py`, `periods.py`,
`classify.py`, `inject.py`, `analyse.py`, `posthoc.py` (needs `QLP_DETREND=1 ONLY_PRODUCT=qlp
PERIODS_OUT=sector_periods_qlpd.parquet periods.py` first), `g3_traces.py`, `g4_check.py`, `g4_visual.py` and
`coverage_lc.py`.
