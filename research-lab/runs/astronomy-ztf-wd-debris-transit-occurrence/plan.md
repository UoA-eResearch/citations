# Plan (preregistration): how common are white dwarfs with transiting planetary debris that ZTF can see?

Lead: `astronomy-ztf-wd-debris-transit-occurrence`. Written 2026-11-05, before any white-dwarf catalogue row or ZTF
light curve was downloaded.

**Seen before this plan:**
- **The lead's text.**
- **Published abstracts** of Vanderbosch et al. 2020 and 2021, Guidry et al. 2021, Bhattacharjee et al. 2025 and van
  Roestel et al. 2026. They report about 20 confirmed debris-transit white dwarfs; none publishes a completeness-
  corrected occurrence rate from ZTF.
- **The access test:**
  - the IRSA ZTF light-curve service answered one test query (column names only);
  - the Warwick-hosted Gentile Fusillo et al. (2021) catalogue file responds (first 1 kB, header only).
- No catalogue row and no light curve.

## 0. Hypotheses

**Sample.** High-confidence white dwarfs from Gentile Fusillo et al. (2021): P_WD > 0.75, G < 20, declination
> −28° (ZTF's sky), within 500 pc. Each needs at least 100 good ZTF epochs: catflags = 0, magerr < 0.25, in g and r
combined.

**Detection** (fixed here, run blind to which stars are known transiters):
- **Short dips** (WD 1145-like, recurring minutes to hours). The faint-outlier excess is the number of good epochs
  more than 3 robust σ (MAD) fainter than the star's median, minus the number more than 3σ brighter, pooled over g
  and r. A star is flagged if the excess is at least 5, a one-sided binomial test against the bright count gives
  p < 1e-6, and the faint outliers fall on at least 3 different nights.
- **Long dips** (J0139-like or one-off obscurations, days to years). The light curve is binned to 30-day medians. A
  star is flagged if at least 2 bins (each with ≥ 5 epochs) are fainter than the global median by more than 5 times
  the bin's standard error and by at least 5% in flux.
- **Candidates** are stars flagged by either test after removing known non-debris variables, using Gaia DR3
  `vari_classifier_result` classes ECL, CV, RS and SOLAR_LIKE and SIMBAD-free name lists of known CVs or AM CVn
  systems if obtainable. What remains is a list, not confirmations.

**Positive controls.** The known debris-transit white dwarfs, compiled from those papers' tables before running
detection. Recovery of the ones inside the sample is reported.

**Completeness.** Injection into the light curves of 5,000 random sample stars, three signal classes, 10 injections
each:
- **WD 1145-like:** period 3–12 h, duty cycle 5–30%, depth 10–60%, active in a random 50–100% of observing seasons.
- **J0139/J0328-like:** period 10 h–120 d, dip duration 2% of the period to 25 d, depth 10–50%.
- **One-off obscuration:** a single event lasting 30–400 d, depth 25–100%.

Recovery means the detection rule flags the star. C_k(G, N_epochs) is tabulated per class.

**Occurrence.** For each class, the rate is N / Σ_i C_k,i, summed over sample stars, with Poisson intervals. It is
computed twice:
- **lower:** N = recovered known systems;
- **upper:** N = recovered known systems plus unexplained candidates.

**H1 (the lead).** The occurrence of ZTF-detectable debris transits, all classes combined (taking each star's
completeness under the best class for it), is below 5e-4.
- *Supported* if the upper rate's 95% upper limit is below 5e-4.
- *Refuted* if the lower rate's 95% lower limit is above 5e-4.
- Otherwise *Inconclusive*.

The implied geometric probability × duty cycle, assuming 25–50% metal pollution, is reported descriptively.

## 1. Data

- **Gentile Fusillo et al. (2021)** Gaia EDR3 white-dwarf catalogue, from the Warwick-hosted FITS file (VizieR is
  unreachable from this machine).
- **ZTF public light curves** from IRSA, the latest data release available on download day, as bulk files or by
  position. Each white dwarf takes the ZTF object with the most epochs within 2 arcsec of its Gaia position,
  propagated to epoch 2019.0.
- **Gaia DR3** `vari_classifier_result` for the removal of known variables.

## 2. Secondary analyses (reported, not confirmatory)

1. Rates by class, by G magnitude bin and by distance (≤ 100, 100–200, 200–500 pc).
2. Thresholds varied: 2.5σ and 3.5σ for short dips; 3 and 7 for the long-dip bins.
3. The faint-outlier excess distribution for all stars, with the known systems marked.
4. Candidates' Gaia colours and absolute magnitudes against the sample.

## 3. Leakage audit (G1)

- **Nothing is trained.** All thresholds are fixed above, before any light curve is read.
- **Detection is blind to the known systems.** It runs on all stars with the same rule, and the known-system list is
  compiled from published tables before detection.
- **Injections are random and seeded.**
- **No LLM or agent labels any star.** Candidate vetting is by catalogue cross-match only.

## 4. Other gates

- **G2:** `results/tables/coverage.json`, covering catalogue rows, the sample cuts, ZTF matches, epoch cuts and flags.
- **G3:** `results/plausibility.md`, with three traces (a known transiter, a flagged non-transiter and a quiet star)
  and the completeness surface.
- **G4:** the known-system recovery rate, with its denominator, and a check of 30 random flags against their light
  curves by a script-only rule (the dip epochs coincide in g and r within a night).
- **G5 and G6:** at write-up.
- **G7:** if any human or agent visual labelling is added later, it needs two blind raters.

## 5. Limits stated in advance

- **ZTF's sparse cadence (about 2–3 days)** gives low completeness for short, low-duty-cycle dips; the rate is for
  ZTF-detectable transits as defined by the injections.
- **Candidates are not confirmed** (no spectroscopy), hence the lower and upper rates.
- **The injection models are simplified.** The rate depends on them, and this is reported per class.
- **Blending and calibration artefacts** near faint white dwarfs can create dips. The g/r coincidence check and the
  variable cross-match mitigate this but do not remove it.
