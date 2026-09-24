# Preregistration: Is the GWTC-4.0 q–χeff anticorrelation real or a mass-model artifact?

Run dir: `/mnt/citations/research-lab/runs/astronomy-gwtc4-q-chieff-copula-stress-test`
Author: nyou045@aucklanduni.ac.nz · Drafted: 2026-09-02

## 1. Hypothesis (as given)

The mass-ratio/effective-spin anticorrelation reported in GWTC-4.0 BBHs is an artifact of
mass/pairing-model misspecification. Specifically:

- **H1a (evidence):** under a copula model with independently flexible q and χeff marginals
  (decoupling shape of the marginals from the dependence structure), ln BF for nonzero rank
  correlation < ln 3.
- **H1b (calibration):** mock catalogs built with *zero* intrinsic q–χeff correlation but
  realistic pairing, selection, and PE uncertainty reproduce the observed correlation statistic
  in > 5% of realizations (i.e., the observed statistic is not a rare event under the null).

Both legs use the same underlying claim (mass/pairing misspecification, not real spin–mass
coupling) and are evaluated jointly (see §6).

## 2. Primary endpoints

| # | Endpoint | Definition |
|---|---|---|
| E1 | Copula correlation Bayes factor | ln BF(copula-with-dependence vs. copula-independence), holding q and χeff marginals flexible (spline or binned) and identical between the two models, computed via nested sampling (dynesty/nautilus) on top of the gwpopulation/numpyro hierarchical likelihood |
| E2 | Mock-catalog false-positive rate (FPR) | Fraction of N≈200 zero-correlation mock catalogs (matched marginals, LVK-style selection function from the O1–O4a injection set, PE-scatter kernel drawn from real posterior covariances) whose refit correlation statistic (Kendall's τ or the copula dependence parameter posterior) is ≥ the value observed in real GWTC-4.0 data |

## 3. Secondary / diagnostic endpoints (preregistered, not decisive alone)

- **E3 — mean-shift vs. width decomposition:** compare Δ ln Z for (a) linear χeff-mean(q) only,
  (b) linear χeff-width(q) only, (c) both, under both the LVK baseline model and the copula model.
  Directly adjudicates between arXiv:2604.20941 ("width-driven") and arXiv:2511.22093 ("no
  significant correlation") — see §9.
- **E4 — mass-pairing generalization:** Δ ln Z when the fixed β power-law pairing function is
  replaced by a free pairing-function family (and separately, by a spline mass model), holding
  the spin sector fixed. Tests whether E1/E2 conclusions are mass-model-specific.
- **E5 — leave-one-out / mass-binned stability:** per-event ln BF sensitivity (does removing any
  single event flip the sign or significance of the dependence parameter?) and posterior
  predictive checks in 3 primary-mass bins.

## 4. Statistical tests / model set

1. **Baseline (reproduction target):** PowerLaw+Peak primary mass, default pairing function
   (β power law in q), Default spin model (Beta magnitudes, linear χeff mean(q) via the
   "correlated" extension used in the LVK GWTC-4.0 population paper) — fit with
   `gwpopulation`/`numpyro` on GPU (NUTS + importance-weighted evidence, or nested sampling for
   ln Z). **Acceptance gate:** must reproduce the published GWTC-4.0 q–χeff posterior (arXiv:2508.18083)
   to within its quoted credible interval before any downstream model is trusted.
2. **Copula models:** Gaussian and Frank copulas coupling independently flexible q and χeff
   marginals (Adamcewicz & Thrane 2022 / Adamcewicz et al. 2023 construction, ported to GWTC-4.0
   and re-implemented in gwpopulation/numpyro for GPU nested sampling), each fit against the
   independence (product-of-marginals) special case.
3. **Mass-pairing variants:** generalized pairing function (free exponent(s) or spline in q) and
   spline primary-mass model, crossed with the Default and copula spin sectors.
4. **Selection function:** injection-based Monte Carlo estimator (`gwpopulation.vt`) using the
   O1–O4a cumulative sensitivity injection set, FAR<1/yr matched to the event sample, with
   effective-sample-size diagnostics (Farr 2019) reported for every fit.
5. **Evidence computation:** nested sampling (`nautilus` or `dynesty` via `bilby`) for all ln Z /
   BF claims in E1, E3, E4; NUTS/numpyro for posterior shape only. Rank correlation statistic for
   E2 computed both as Kendall's τ on posterior-mean point estimates and as the copula dependence
   parameter's hierarchical posterior, to avoid the test being an artifact of the summary
   statistic choice.
6. **Mock catalog generator:** draw q, χeff independently from the fitted flexible marginals
   (zero true correlation by construction), forward-model through the O1–O4a injection-based
   selection function to realistic detected-event counts, and scatter each mock true value by a
   PE-uncertainty kernel resampled from real posterior covariance matrices (matching the
   observed SNR/measurement-precision distribution) — not idealized Gaussian noise, per the
   "realistic PE uncertainty" requirement in the hypothesis.

## 5. Sample definition and exclusion rules

- Source: GWTC-4.0 event list via the GWOSC eventapi (`https://gwosc.org/eventapi/json/GWTC-4.0/`),
  129 event-version entries as of 2026-09-02.
- **Inclusion:** FAR < 1/yr (matches the LVK confident-BBH threshold; 86/128 O4a candidates meet
  this per the GWTC-4.0 catalog paper, arXiv:2508.18082); both component masses consistent with
  the BBH regime (exclude NSBH/BNS candidates by posterior mass support, mirroring the LVK
  population paper's selection, to be pinned down exactly against arXiv:2508.18083 §2 in the
  first implementation session — this is a control, not a free choice).
- **PE choice:** use each event's `is_preferred` PE result (the "Mixed" combined-waveform-family
  posterior, e.g. `C00:Mixed` in the PE HDF5) as the primary sample, with the individual
  `IMRPhenomXPHM-SpinTaylor` and `SEOBNRv5PHM` posteriors retained for a waveform-systematics
  sensitivity check (control, not part of the primary endpoints).
- **χeff definition:** use `chi_eff` (standard, LVK population-paper-comparable definition), not
  the newly-observed `chi_eff_infinity` column, unless a sensitivity check motivates otherwise —
  note this second column exists in the GWTC-4.0 release and was not anticipated in the method
  sketch; flag for the LVK-baseline-reproduction step.
- **Exclusions:** events lacking a public PE data release; events whose preferred PE run failed
  standard sampler-convergence diagnostics (documented in the release's `meta_data`); any event
  the LVK population paper itself excludes from its BBH population sample (to be matched exactly,
  since "reproduce the LVK selection-effect treatment exactly" is a named risk/requirement).

## 6. Controls / confounds to handle

- **Marginal-shape confound:** the central manipulation — copula models hold marginals identical
  in flexibility between the dependent and independent fits, so any ln BF difference is
  attributable to dependence structure alone, not to one model having a more flexible marginal.
- **Selection-effect mismatch:** use the *same* injection-based VT estimator and FAR threshold in
  every model in the comparison table, and report effective number of injections / effective
  sample size per fit (Farr 2019 diagnostic) so that a low-BF result can't be an artifact of a
  poorly resolved selection function.
- **Waveform-systematic confound:** cross-check headline results against the per-waveform-family
  PE (not just the Mixed posterior) for a subset of high-SNR events.
- **PE-uncertainty realism in mocks:** mocks must use resampled real posterior covariance
  structure, not simplified Gaussian noise, or E2 risks under-stating the true FPR.
- **Statistic-choice confound:** E2 is computed with at least two different correlation summary
  statistics (Kendall's τ point-estimate and hierarchical copula parameter) to check the FPR
  conclusion isn't an artifact of the particular test statistic.
- **Multiple-model / look-elsewhere effect:** with ~2 mass models × ~3 spin/copula variants × 2
  correlation statistics, apply a preregistered primary comparison (baseline vs. Gaussian-copula,
  PowerLaw+Peak masses) as the headline E1/E2 test; all other combinations are secondary/robustness
  and reported as a full table, not cherry-picked.

## 7. Success / refutation criteria

- **Hypothesis CONFIRMED (artifact):** E1 gives ln BF < ln 3 for nonzero dependence under the
  copula+flexible-marginal model **and** E2 gives FPR > 5%, both in the preregistered primary
  comparison (PowerLaw+Peak masses, Gaussian copula, Kendall's τ statistic). Mass-pairing (E4)
  and mean/width (E3) checks should be consistent with a non-robust, model-dependent signal.
- **Hypothesis REFUTED (correlation likely real):** E1 gives ln BF ≥ ln 3 (decisively favoring
  dependence) under the copula+flexible-marginal model **and** E2 gives FPR ≤ 5%, and this holds
  under the spline-mass and generalized-pairing variants (E4).
- **Indeterminate (the realistic risk flagged in the brief):** E1 and E2 disagree, or land in a
  "moderate" BF regime (1 ≤ ln BF < ln 3 is common in this literature); report the full
  calibration curve, BF table, and E3–E5 diagnostics without forcing a binary claim, and
  explicitly reconcile against the width-driven (2604.20941) and null (2511.22093) results by
  showing where in (mass, statistic, model) space each published conclusion is reproduced.
- Pre-committed reporting: regardless of outcome, publish the full ln Z / BF table (all model ×
  mass-model combinations), the E2 calibration curve (FPR vs. assumed intrinsic correlation
  strength, not just at zero), and code/results release.

## 8. Data access verification (performed 2026-09-02)

All three named datasets were hit live and a working sample was pulled into
`data/sample/`:

| Dataset | Check performed | Result |
|---|---|---|
| GWTC-4.0 PE posteriors (GWOSC/Zenodo) | `GET https://gwosc.org/eventapi/json/GWTC-4.0/` → 129 event-version entries with FAR, masses, χeff; drilled into one event's per-pipeline `parameters` block, found live Zenodo `data_url`s for PE HDF5 files; downloaded the full preferred-PE file for GW240109_050431 | HTTP 200, 60,309,520 bytes; opened with h5py — standard PESummary layout (`C00:Mixed/posterior_samples` etc.), 29,374 samples, columns include `mass_ratio`, `chi_eff` (and a `chi_eff_infinity` variant not anticipated in the method sketch). File saved at `data/sample/pe_samples/GW240109_050431_PEDataRelease.hdf5` |
| O1–O4a sensitivity injections (Zenodo) | `GET https://zenodo.org/api/records/16740128` (GWTC-4.0 cumulative O1-O4a sensitivity estimates) → file listing; downloaded the metadata `.md` in full and the first 8 MB (HTTP 206 range request) of the largest injection mixture HDF5 | Metadata file downloaded in full (9,793 bytes); range request succeeded (HTTP 206) and returned a valid HDF5 magic header (`89 48 44 46 0d 0a 1a 0a`). Full injection set across all mixture files is ≈2.2 GB (smaller than the ~5 GB estimate in the brief), plus ~28 small PSD files. Saved at `data/sample/injections/` |
| gwpopulation code | `GET https://api.github.com/repos/ColmTalbot/gwpopulation` + `pip index versions gwpopulation` | Repo active (62 stars, last push 2026-08-05); PyPI has gwpopulation 1.3.1 installable |

Local venv created at `venv/` (system Python lacked `python3-venv`; installed via
`sudo apt-get install -y python3.12-venv`, then rebuilt the venv — this succeeded and is
reproducible). `h5py`/`numpy` verified working inside it against the real downloaded PE file.

**Disk:** sample downloads used ~66 MB; `/mnt` has 628 GB free (well above the 100 GB floor).
Raw full-scale downloads (full 129-event PE set ~20 GB, full injection set ~2.2 GB) are deferred
to the actual run and should be deleted after the standardized sample/prior table is built, per
the "be a good citizen" instruction.

**GPU note (operational risk, not a data-access problem):** at verification time the A100 80GB
was almost fully occupied by another process on this machine (`VLLM::EngineCore`, ~80.3 GB
resident, plus an unrelated 416 MB python3 process) — effectively 0 free GPU memory. This blocks
GPU-resident numpyro/NUTS fitting until that job releases memory or the GPU is otherwise freed;
flagged here so the run doesn't stall silently on first GPU allocation. CPU-based nested sampling
(dynesty) remains available as a fallback for evidence computation if GPU access is contended.

## 9. Literature check (4 searches, 2026-09-02) — is this exact study already published?

**Conclusion: no.** No paper found combines (a) the copula framework (decoupled flexible q and
χeff marginals) with (b) an explicit mock-catalog false-positive-rate calibration, applied to
GWTC-4.0. The copula test itself has so far only been published on GWTC-2/GWTC-3. However, the
space is more crowded than the brief's "known prior art" list, and two additional close pieces of
prior art were found that materially affect novelty and must be cited/engaged with directly:

- **arXiv:2604.20941** (Chatterjee, Apr 2026, symbolic regression on GWTC-4.0) — confirmed:
  argues the q–χeff and z–χeff correlations are "robustly driven by broadening of the posterior
  widths rather than shifts in the mean." Directly relevant to E3; this study should be read as
  a width-vs-mean baseline, not re-derived from scratch.
- **arXiv:2511.22093** (binned Gaussian process, Nov 2025) — confirmed: finds no significant
  q–χeff correlation in GWTC-4.0, **and already runs a null-hypothesis mock-catalog test**:
  simulated populations with no intrinsic (m1, q, χeff) correlation, injected through the same
  detection/analysis pipeline as real data. This is the single closest piece of prior art to the
  E2 calibration arm of this project — it is not copula-based and is framed around the 35 M☉ peak
  rather than a dedicated q–χeff FPR calibration, but the method sketch should explicitly
  differentiate against it (copula dependence-parameter statistic + explicit FPR-vs-correlation-
  strength curve, vs. their binned-GP null check) rather than present the mock-catalog idea as
  novel in isolation.
- **arXiv:2512.03152** ("Inferring black hole formation channels in GWTC-4.0 via parametric
  mass-spin correlations derived from first principles") — newly found, not in the brief's prior-
  art list: reports *increased* Bayes factors for preferentially-aligned-spin/mass-correlation
  models in GWTC-4.0, but flags that this "requires caution — possibly arising from how variance
  cuts downweight certain parameter-space regions, potentially related to... uniform and isotropic
  spin priors in GWTC-4.0 PE." This is an LVK-adjacent group independently voicing the same
  artifact concern this project tests formally — strengthens the motivation, raises scoop risk.
- **arXiv:2605.24281** ("Evidence for mass-dependent spin subpopulations in GWTC-4") — newly
  found: offers a third structural explanation (discrete subpopulations rather than a continuous
  q–χeff dependence) that the copula framework does not directly model; worth a discussion-section
  comparison but not a blocking overlap.
- **arXiv:2509.05976 / A&A 708, A62 (2026)** ("Reassessing the spin of second-born black holes...
  connection to the χeff–q correlation") — confirmed exists; astrophysical (formation-channel)
  interpretation of the correlation rather than a statistical artifact test; low overlap.
- Targeted searches for an Adamcewicz-group GWTC-4.0 copula update turned up no such paper as of
  2026-09-02 — the scoop risk named in the brief has not yet materialized, but given
  arXiv:2512.03152 and arXiv:2511.22093 both already probe adjacent territory, the window is
  closing and this should be treated as time-sensitive.

**How this project differs from all of the above:** it is the only proposed design that (i) uses
the copula decomposition specifically to isolate dependence structure from marginal shape, (ii)
generalizes the *mass pairing function* (not just the spin model) as an alternative artifact
source, and (iii) pairs both with a quantitative, preregistered false-positive-rate calibration
curve (not a single null check) on GWTC-4.0. The write-up must explicitly reconcile against
2604.20941 and 2511.22093's conflicting conclusions (§7 indeterminate-case handling exists
partly for this reason) and engage with 2512.03152's independent artifact concern.

## 10. Go / no-go

**viable = true.** All three datasets verified live and real; a working local venv and a real
downloaded PE sample + a validated injection-file byte range are in `data/sample/`; the exact
proposed test (copula + explicit mock FPR calibration on GWTC-4.0) is not yet published, though
the margin has narrowed since the brief was written. Two concrete pre-work items before the main
run: (1) resolve GPU contention (currently ~0 free memory on the shared A100), (2) pin down the
LVK population paper's exact BBH inclusion/exclusion cuts (arXiv:2508.18083 §2) before the
sample-and-prior table is built, since an inexact match invalidates the baseline-reproduction
gate in §4.
