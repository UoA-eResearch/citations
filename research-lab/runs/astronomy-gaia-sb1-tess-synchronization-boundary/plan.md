# Plan (preregistration): where does tidal synchronization stop in Gaia's close binaries?

Lead: `astronomy-gaia-sb1-tess-synchronization-boundary`. Written 2026-11-03, before any Gaia orbit, TESS light
curve or rotation period was downloaded or looked at.

**Seen before this plan:**
- **The lead's text.**
- **Gaia DR3 documentation** (column names of `nss_two_body_orbit`, `gaia_source`, `astrophysical_parameters`,
  `dr2_neighbourhood`), MAST's descriptions of the TESS-SPOC and QLP FFI light-curve products, and the published
  abstracts of the works in the novelty check (Bashi et al. 2023; Hobson-Ritz et al. 2025; Hadad et al. 2025;
  Wang et al. 2026; Yu et al. 2025).
- No row of data.

## 0. Hypotheses

**Sample.** Gaia DR3 `nss_two_body_orbit` solutions of type SB1 or SB1C, with parallax_over_error > 10, on the main
sequence: dereddened absolute magnitude M_G within −1.0 to +0.75 mag of the Pecaut & Mamajek dwarf sequence at the
star's dereddened BP−RP (dereddening from `ebpminrp_gspphot` and `ag_gspphot` where present, otherwise none, with a
d < 300 pc sensitivity). Teff comes from the dereddened colour through the same table. One solution per source.

**Rotation periods** come from TESS FFI light curves (TESS-SPOC where it exists, otherwise QLP), searched over
0.2–13 d by the rules in section 1. A star's rotation is **synchronized** if |P_rot − P_ps| / P_ps < 0.10, where
P_ps is the orbital period for e < 0.05 (and all SB1C), and Hut's (1981) pseudo-synchronous period otherwise.

**The primary fraction** in a group of stars is the completeness-weighted share of synchronized stars among those
with a detected rotation period: each detection is weighted by 1 / C, where C is the injection-recovery completeness
at its period, amplitude and TESS magnitude (section 1), floored at 0.1 (detections with C < 0.1 are dropped).
Intervals come from 2,000 bootstrap resamples of stars.

**H1 (the synchronization boundary tracks the Kraft break).** Among binaries with P_orb < 10 d:
- f_cool, the primary fraction for 4,000–6,200 K, is above 0.70;
- f_hot, the primary fraction for 6,500–7,500 K, is below 0.30;
- the transition is sharp: a logistic in Teff fitted over 4,000–7,500 K (free floor, ceiling, midpoint T0 and scale
  w, by maximum likelihood on the weighted detections) has a 10–90% width, 4.39 w, below 400 K.

*Supported* if the f_cool interval lies above 0.70, the f_hot interval below 0.30, and the width's point estimate is
below 400 K. *Refuted* if the f_cool interval lies below 0.70, or the f_hot interval above 0.30, or the width
interval above 400 K. Otherwise *Inconclusive*.

**H2 (synchronization reaches longer periods than circularization).** In three Teff bins (4,000–5,500, 5,500–6,200
and 6,200–7,000 K):
- **P_sync,50** is the orbital period at which the synchronized fraction falls to one half: a logistic in log P_orb
  over 0.5–12 d.
- **P_circ,50** is the period at which the circular share (SB1C, or e < 0.05) falls to one half, a logistic in
  log P_orb over 0.5–30 d. It is computed on all sample binaries in the bin, with or without a rotation period.
- **A midpoint beyond 12 d** is recorded as "> 12 d". It counts for H2 when the P_circ,50 interval lies below 12 d.

*Supported* if P_sync,50 > P_circ,50, with the bootstrap interval of their log ratio excluding 0, in at least two
bins, and no bin shows the reverse. *Refuted* if any bin shows the reverse with its interval excluding 0. Otherwise
*Inconclusive*.

## 1. Data and measurement

- **Gaia DR3** through the ESA archive's TAP service. Columns from `nss_two_body_orbit`: period, eccentricity,
  semi_amplitude_primary, t_periastron, arg_periastron and their errors, plus solution type and significance. From
  `gaia_source`: photometry, parallax, ruwe, vbroad. From `astrophysical_parameters`: the GSP-Phot extinction,
  reddening and radius, and the FLAME radius.
- **TIC v8.2** identifiers are matched through `gaiadr3.dr2_neighbourhood` and the TIC's Gaia DR2 column. Only an
  unambiguous one-to-one match is kept.
- **TESS light curves.** The TESS-SPOC FFI and QLP high-level science products from MAST, for every sector
  available on download day. Light curves are fetched only for binaries with P_orb < 12 d.
- **Light-curve preparation.** Quality-flagged cadences are dropped, along with 5σ outliers from a running median.
  Each sector is normalised separately.
- **Period search.** A generalised Lomb–Scargle periodogram on each sector, over 0.2–13 d. A sector *detects* a
  period if its highest peak has a false-alarm probability below 1e-5.
- **A star's period** is the median of its detecting sectors' periods. A star is *inconsistent*, and excluded, if
  those periods disagree by more than 10%. Its amplitude is the median semi-amplitude of a sinusoid at its period.
- **Double-dip correction.** If the autocorrelation function of the best sector has its first major peak at twice
  the periodogram's period, within 15%, the doubled period is used.
- **Ambiguous signals**, excluded from the primary analysis and handled in sensitivities (section 2):
  - **Ellipsoidal or double-spot:** the period is within 5% of P_orb / 2.
  - **Possible Doppler beaming:** the period is within 10% of P_orb and the amplitude is below twice the predicted
    beaming amplitude, 4K/c.
  - **Multi-periodic pulsator:** three or more independent significant peaks in 0.3–3 d after prewhitening, none a
    harmonic of another.
- **Completeness C(P, A, T).** Spot-like signals are injected into the light curves of sample binaries with no
  detection, using the same sectors. The signal is a sinusoid plus first harmonic with random phases, with periods
  log-uniform over 0.3–13 d and semi-amplitudes log-uniform over 0.005–2%. There are 20 injections per light curve,
  for at least 2,000 light curves. Recovery means the same pipeline returns the period within 10%. C is tabulated
  on a grid of log P × log A × TESS magnitude (three bins).

## 2. Secondary analyses (reported, not confirmatory)

1. **Bounds without the detection condition.** For each Teff group, the lower bound is synchronized / all, and the
   upper bound is (synchronized + no detection) / all.
2. **Ambiguous signals.** Rerun with the ellipsoidal or double-spot class counted as synchronized (an upper bound),
   and with the possible-beaming and pulsator classes included.
3. **Unweighted fractions**, and fractions at d < 300 pc.
4. **Spectroscopic check.** For stars with Gaia vbroad and a radius (FLAME, else GSP-Phot), compute
   v_sync = 2πR / P_orb. A synchronized star must have vbroad ≤ v_sync, within errors, for any inclination. The
   share with vbroad > 1.5 v_sync + 2σ, which cannot be synchronized, is reported by Teff group. This needs no spots,
   so it reaches the hot side where photometric periods are scarce.
5. **Sub- and super-synchronous shares** by Teff and P_orb, including binaries with P_orb of 10–12 d.
6. **The circularization cutoff by Teff**, to compare with Bashi et al. (2023), who used the same Gaia orbits.

## 3. Leakage audit (G1)

- **Nothing is trained.** The risk is outcome-informed choices, so every threshold above is fixed before any data
  are read.
- **No visual inspection changes a label.** The G4 audit's visual checks are descriptive, and any change they
  prompt goes into `deviations.md` with the before-and-after numbers.
- **The orbit is never used to choose or adjust a rotation period.** The period search does not know P_orb; it
  enters only in the ambiguity checks and the classification, which are fixed above.
- **No LLM or agent labels any unit.**

## 4. Other gates

- **G2:** `results/tables/coverage.json`, covering:
  - orbits read and kept, and why the rest drop (type, parallax, main-sequence band);
  - TIC matches;
  - light curves found, per product;
  - detections, inconsistent stars and each ambiguous class.
- **G3:** `results/plausibility.md`:
  - three binaries traced from the Gaia orbit through the light curve to the classification;
  - the injection grid's completeness surface;
  - rotation periods of cool single-star TESS targets compared with the literature's ranges.
- **G4:**
  - periods compared with an independent published TESS rotation catalogue where targets overlap, reporting
    agreement within 10%, half and double, and the denominator;
  - 30 random classifications checked against their folded light curves.
- **G5 and G6:** at write-up.
- **G7:** does not apply.

## 5. Limits stated in advance

- **Detecting a period depends on spots,** and spot amplitude depends on rotation and Teff. The primary fraction is
  conditional on detection. Secondary 1 bounds what the undetected stars could change, and secondary 4 sidesteps
  spots altogether.
- **Hot stars have weak spots and often pulsate,** so f_hot may rest on few stars. An *Inconclusive* there is a
  likely outcome, not a failure.
- **TESS sector systematics** (13.7-d orbit) limit periods to below 13 d. Sub-synchronous rotation of the
  longest-period binaries may go undetected.
- **The companion is unseen, but not necessarily dark,** and some SB1s are inner pairs of triples. Light from a
  third star can carry the rotation signal (secondary 3 and the RUWE distribution are reported).
- **Gaia's SB1 sample is RVS-bright (G_RVS ≲ 12) and selection-biased** toward large semi-amplitudes and short
  periods. The fractions are for that sample, not all binaries.
