# q-chi_eff copula stress test on GWTC-4.0 -- analysis pipeline

Is the mass-ratio / effective-spin anticorrelation in the GWTC-4.0 BBH population real, or an
artifact of mass / pairing-model misspecification? Preregistration: `../plan.md`. Every departure
from it: `../deviations.md`.

The pipeline is a set of stand-alone Python stage scripts (`src/*.py`) driven by `run_all.py`
(or the `Makefile`). Every stage is resumable: it skips itself when its outputs exist, and the
expensive stages checkpoint internally (per model / per mock). All runtime knobs live at the top
of `config.yaml`; seeds are deterministic (`run.seed`, one derived seed per stage).

```
code/
  run_all.py         driver: --mode smoke|full, --stages a,b,c, --force, --backend, --models, --skip-nuts
  run_full_chain.sh  unattended full run: (re)fetch -> build+test -> sample check (153 BBHs) -> GPU stages -> figures
  Makefile           make smoke | make full | make <stage> MODE=full | make gpucheck | make clean-raw
  config.yaml        all configuration (paths, sample cuts, priors, model set, per-mode cost knobs)
  requirements.txt   pinned packages (already installed in ../venv)
  src/
    fetch_data.py     01  GWOSC eventapi -> event list, Zenodo PE files, O1-O4a injection file
    build_sample.py   02  standardized posterior-sample + PE-prior table, injection table
    test_models.py    --  model unit checks (jax models == gwpopulation, normalisations, gradients)
    fit_models.py     03  nautilus fits (ln Z + posterior) of every model; NUTS cross-check
    mock_catalogs.py  04  zero-correlation (and rho_true grid) mock catalogs with real selection + PE kernels
    mock_stats.py     05  correlation statistics on real data and mocks -> false-positive rate, calibration curve
    diagnostics.py    06  BF table, Savage-Dickey check, LOO, mass-binned PPC, gate, preregistered verdict
    make_figures.py   07  figures F1-F9
    gpu_check.py      opt time the compiled likelihood / gradients on the A100 (`--stages gpucheck`)
    jaxmodels.py, models_registry.py   population models, hierarchical likelihood, priors (jax)
    selection.py, pe_priors.py         injection draw-density conversion, analytic PE priors
    gwosc_client.py, io_utils.py, config.py, gpu.py   plumbing (downloads, HDF5 tables, config, GPU/docker protocol)
```

Run-directory layout (everything relative to `../`):
`data/raw/` (downloads), `data/processed/` (standardized tables, chi_eff prior cache),
`data/mocks/`, `results/fits/<mode>/<model>/` (nautilus checkpoint + posterior + summary),
`results/tables/`, `results/figures/`, `results/summary_<mode>.md`, `logs/`.

## Quick start

```bash
cd /mnt/citations/research-lab/runs/astronomy-gwtc4-q-chieff-copula-stress-test/code
../venv/bin/python run_all.py --mode smoke            # ~10-12 min, CPU only, 4 real events -- exercises every stage
../venv/bin/python run_all.py --mode full             # the real thing (see budget below)
```

Equivalent `make smoke` / `make full`. Single stages: `make fit MODE=full`, or
`../venv/bin/python run_all.py --mode full --stages fit --models copula_gauss_plp,copula_indep_plp`.
`--force` recomputes a stage even if its outputs exist (per-model nautilus checkpoints are deleted too).

Smoke mode never touches the GPU or the `vllm` container (`modes.smoke.backend: cpu`); all of its
numbers are meaningless (4 events) -- it only proves the code path.

## The full run, stage by stage

| # | stage | what it does | full-mode outputs | needs GPU? |
|---|---|---|---|---|
| 01 | `fetch` | FAR < 1/yr, point-estimate m2 > 3 Msun candidates from GWTC-2.1-confident + GWTC-3-confident + GWTC-4.0 (de-duplicated; the O1/O2 events carry no FAR on the GWTC-2.1 eventapi and take theirs from GWTC-1-confident, `data_sources.far_fallback_catalogs`; `sample.exclude_events` = GW190814, GW230630_070659 as in arXiv:2508.18083); downloads each event's preferred "Mixed" PE release from Zenodo (12 threads, resumable per file) and the 625 MB O1-O4a injection mixture | `data/processed/event_manifest_full.json`, `data/raw/pe_samples/*.h5`, `data/raw/injections/*.hdf` | no (network-bound) |
| 02 | `build` | reads each PE file, applies the LVK BBH control (1% lower limit of both component-mass posteriors > 3 Msun, arXiv:2508.18083 sec 3.2.2) and `sample.exclude_events`, evaluates the analytic PE prior in (m1, q, z, chi_eff); converts the 1.07 M found injections to the same parameterization with per-component spin-draw families (validated on the file). Expected sample: 153 BBHs (10 O1/O2 + 36 O3a + 23 O3b + 84 O4a), the population paper's count | `sample_table_full.h5`, `injection_table_full.h5`, `sample_qc_full.csv`, `injection_check_full.json`, `sample_summary_full.json` | no |
| -- | `test` | jax PowerLaw+Peak x pairing == gwpopulation to 1e-15; marginals normalised; copulas integrate to 1; every model finite + differentiable | log only | no |
| 03 | `fit` | nautilus (nlive 1000, 4 networks, n_eff 4000) for the 13 models in `modes.full.model_set`; NUTS cross-check of `baseline_plp_both` | `results/fits/full/<model>/{nautilus.h5,posterior.npz,summary.json}` (+ `posterior_nuts.npz`) | **yes** |
| 04 | `mocks` | 200 zero-correlation + 4 x 40 rho_true mock catalogs from the `copula_indep_plp` posterior-median population, drawn through the real O1-O4a selection function, scattered with real-event likelihood kernels | `data/mocks/mocks_full_rho*.h5` | no |
| 05 | `mockstats` | Kendall tau, rho_MAP and profile-LR on the real data and every mock (MAP fits with jax forward-mode gradients); full nautilus refits of 4 rho=0 mocks | `results/tables/mock_stats_full.csv`, `fpr_full.json` (E2 + calibration curve) | **yes** |
| 06 | `diagnostics` | ln Z / BF table (E1, E3, E4), Savage-Dickey cross-check, LOO stability and mass-binned PPC (E5), baseline gate, verdict per plan sec. 7 | `results/tables/{lnz,bf,loo,ppc}_full.*`, `diagnostics_full.json`, `results/summary_full.md` | no |
| 07 | `figures` | F1 data, F2 baseline slopes, F3 copula rho, F4 BF bars, F5 null distributions, F6 calibration curve, F7 marginals, F8 LOO, F9 PPC; one caption file per figure | `results/figures/full_F*.png`, `full_F*.txt` | no |

Primary preregistered comparison: `copula_gauss_plp` vs `copula_indep_plp` (E1) and the Kendall-tau FPR (E2).

## GPU protocol (stages 03 and 05)

The A100 normally hosts the user's vLLM server (docker container `vllm`, ~80 GB). With
`run.manage_vllm: true` (default) a GPU stage does, by itself:

1. if the `vllm` container is running, `docker stop vllm` and wait until the GPU is essentially empty
   (>= 80% of its memory free, up to 3 min) before JAX preallocates -- the stop is unconditional because a
   free-memory test races against a container that has just been (re)started (2026-09-11, D16 note);
2. run the stage on `cuda` (`XLA_PYTHON_CLIENT_MEM_FRACTION=0.85`);
3. `docker start vllm` when the stage ends -- also on exceptions, Ctrl-C and SIGTERM
   (`gpu.GPUSession`). Only a SIGKILL / reboot can leave the container stopped: then `make vllm-start`.

The container is stopped only for the duration of a GPU stage; stages 01, 02, 04, 06, 07 run with it
up. Force CPU with `--backend cpu` (see the CPU-fallback budget below); force the GPU with `--backend gpu`.
`make gpucheck` (`run_all.py --mode smoke --stages gpucheck`, add `EXTRA="--full-scale 150 4000"`
via the script directly) stops the container for ~3 min and writes `logs/gpu_check_*.json` with the
measured seconds per likelihood point / gradient.

## Expected runtime and resources

Measured on this machine (32-core Xeon, 94 GB RAM, A100 80 GB), 2026-09-02.

**Smoke mode (CPU only, 4 events x 300 samples, 10 000 injections; clean `--force` run 2026-09-02):**
fetch 5.2 min (GWOSC API crawl; + ~3 min of downloads the very first time; skipped when the manifest
and files exist), build 0.1 min, test 0.9 min, fit 4.4 min (6 models + NUTS ~3 min), mocks 0.3 min,
mockstats 2.1 min, diagnostics 0.3 min, figures 0.5 min -- **13.6 min end to end, ~8.5 min without fetch.**

**Full mode, likelihood cost at full scale** (150 events x 4000 samples + 1.07 M injections,
`logs/gpu_check_smoke_fullscale.json`): 0.7 ms (baseline) / 0.9 ms (copula) per vectorized
likelihood point on the A100; gradients 26 ms / 65 ms (forward mode). On the CPU the same
likelihood costs ~30-60x more.

| stage | GPU path (default) | CPU-only fallback (`--backend cpu`) | notes |
|---|---|---|---|
| 01 fetch | ~1-1.5 h | same | ~23 GB from Zenodo (GWTC-4.0 ~14.6 GB, GWTC-3 ~5.7 GB, GWTC-2.1 ~2.7 GB) at ~7-10 MB/s with 12 streams (0.4 MB/s per stream). Resumable file by file; safe to start early and re-run. |
| 02 build | ~5 min | same | chi_eff prior tables are cached in `data/processed/chieff_prior_cache/` |
| test | ~1 min | same | |
| 03 fit | ~1.5-3 h | **not feasible** (~4-7 days) | dominated by nautilus's own bounding / network training (measured 7 min for 79 k calls at nlive 1000, 4 networks, 20 dims with a 0.7 ms likelihood; 4.3 min with 2 networks), not by the likelihood: ~5-12 min per model x 13 models, + NUTS <= 25 min. Split with `--models` if needed. |
| 04 mocks | ~5 min | same | |
| 05 mockstats | ~1.5-2.5 h | not feasible | 361 mocks x 2 MAP fits (~300 forward-mode gradients each at ~10-20 ms on the 150 k-injection subsample) ~ 45-60 min, + 8 full nautilus mock refits ~1-1.5 h |
| 06 diagnostics | ~10 min | same | PPC draws (300) are the cost |
| 07 figures | ~2 min | same | |

**Total for the full run: ~5.5-8 h wall-clock on the GPU path**, of which ~1-1.5 h is the download (GPU busy, i.e. vllm stopped, for ~3-5 h of that).
This is inside the ~12 h budget but not by a wide margin; if the fit stage runs long, the knobs are
(in order of harmlessness) `modes.full.n_networks` (4 -> 2), `n_mock_full_refits` (4 -> 2),
`nlive` (1000 -> 750), and dropping secondary models from `modes.full.model_set` (keep at least
`baseline_plp_both`, `baseline_plp_null`, `copula_gauss_plp`, `copula_indep_plp`). Record any such
change in `../deviations.md`.

**CPU-only machine:** stages 01, 02, 04, 06, 07 and the smoke test run fine; stages 03 and 05 at
full scale do not fit in a working day on 32 cores (the vectorized jax likelihood on the CPU is
~30-60x slower than on the A100 and nautilus needs 1e5-1e6 evaluations per model). The realistic
CPU-only option is a reduced run: `max_posterior_samples_per_event: 1000`, `injection_slice: 200000`,
`nlive: 500`, the four primary models only, `n_mock_catalogs: 100` -- roughly 1-2 days.

**Disk:** raw PE downloads ~23 GB + injections 0.6 GB (`data/raw/`); processed tables ~1 GB; mocks
~4 GB (361 catalogs x 150 events x 2000 samples); fits ~1 GB; figures/tables negligible. Peak ~30 GB,
against 622 GB free on `/mnt` (floor: keep 100 GB free). After stage 02 has produced
`sample_table_full.h5` the raw PE files can go: `make clean-raw` (stage 01 re-downloads only what a
later `--force` rebuild needs).

**RAM:** stage 02 loads one PE file at a time (< 2 GB); stage 03/05 hold the event + injection arrays
(~100 MB) plus jax buffers; NUTS / MAP forward-mode gradients allocate ~n_dim x data (< 3 GB on the GPU).

## Resuming after an interruption

Just re-run the same command. Concretely:

* `fetch`: existing files are kept; partial downloads resume via HTTP Range on `*.part`; the
  manifest is rewritten only for events whose PE file exists.
* `build`: skipped when its four outputs exist (`--force` to rebuild).
* `fit`: models with `summary.json` are skipped; an interrupted model resumes from its nautilus
  checkpoint `results/fits/<mode>/<model>/nautilus.h5`; `summary_nuts.json` gates the NUTS re-run.
* `mocks`: one file per rho_true, written atomically (`.part` then rename); existing files are kept.
* `mockstats`: every finished row (real data, each mock) is appended to
  `results/tables/mock_stats_<mode>_partial.csv` and reloaded on restart; mock nautilus refits
  checkpoint like stage 03.
* `diagnostics` / `figures`: cheap; skipped when `diagnostics_<mode>.json` / `<mode>_F9_ppc.png` exist.
* If a GPU stage was killed hard: `make vllm-start`.

Logs: `../logs/<NN_stage>_<mode>.log` (per stage, appended) and whatever you redirect `run_all.py`
to. Long stages should be launched detached, e.g.
`nohup ../venv/bin/python run_all.py --mode full > ../logs/run_all_full.out 2>&1 &`.

## Changes made in the 2026-09-11 execution session (deviations D9-D13)

* Sample: GW190924_021846 and GW190725_174728 (1% lower limit of m2_source 2.77 / 2.67 Msun) are kept through
  `sample.force_include_events` because the paper's 153 = 69 (GWTC-3.0-inherited) + 84 requires them (D9).
* `modes.full.max_posterior_samples_per_event: 10000` (all stored samples; events with fewer are resampled with
  replacement instead of capping K for the whole catalog at 1993) (D10, D12).
* `likelihood.cut_mode: penalty` -- the LVK convergence cuts enter the sampled likelihood as a steep finite penalty
  (effective cut at var_tot ~ 1.001) instead of ln L = -inf, because nautilus cannot start from an all -inf prior
  (0/256 finite prior draws at full scale) (D11). `summary.json` records `var_tot_quantiles` per fit.
* `grids.m1_max: 300`, `grids.n_m1: 2000`, `priors.mmax: [30, 300]`, `modes.full.mass_spline_nodes: 14` because the
  sample contains GW231123 (m1 ~ 135 Msun) (D13).
* `run_gpu_chain.sh` replaces `run_full_chain.sh` for the resumed run (model tests, then the GPU stages).

## Items pinned against arXiv:2508.18083 before the full run (plan.md sec. 4.1, 5, 10; deviations D7-D8)

* Sample: FAR < 1/yr in any pipeline, 1% lower limit of both component masses > 3 Msun, GW190814 and
  GW230630_070659 excluded, O1/O2 FARs from GWTC-1-confident -> 153 BBHs. `data/processed/sample_qc_<mode>.csv`
  lists every candidate with the reason for inclusion/exclusion; `run_full_chain.sh` refuses to start the GPU
  stages unless `sample_summary_full.json` reports 153 events.
* Baseline spin sector = the paper's "Linear" (q, chi_eff) model (App. B.7): truncated-Gaussian chi_eff with
  mean and natural-log width linear in (q - 1), priors from its Table 10 (`priors.mu_chi_eff_1`,
  `priors.sigma_chi_eff_1` = delta ln sigma).
* Acceptance gate (`diagnostics.reference_p_*`): the paper quotes P(delta mu_eff|q < 0) = 0.82 and
  P(delta ln sigma_eff|q < 0) = 0.95; the gate passes when `baseline_plp_both` reproduces both within
  `gate_tolerance_*`. Its Frank-copula kappa_q,eff = -2.1 (+2.4/-2.9) is reported as a cross-check.
* `data_sources.injection_spin_families`: set from Essick 2025 and verified on the file
  (`injection_check_<mode>.json`, `all_supported` must be true; also checked by `run_full_chain.sh`).

## Environment

`../venv` (Python 3.12) with jax 0.11.1 (+ CUDA 12 plugin), numpyro 0.21, nautilus-sampler 1.0.6,
gwpopulation 1.3.1, bilby 2.8.2, h5py, astropy, scipy, pandas, matplotlib -- `requirements.txt`.
Recreate with `python3.12 -m venv venv && venv/bin/pip install -r code/requirements.txt`
(add `"jax[cuda12]"` for the GPU).

## LVK mass model (added 2026-09-11, deviations D15)

The first full-mode fits put the plan's reproduction gate at P(δμ<0) ≈ 0.99 / P(δ ln σ<0) ≈ 0.83 against the
paper's 0.82 / 0.95 -- a mean-shift rather than width-driven verdict under PowerLaw+Peak masses. Because the
paper's Linear-model result uses its default **Broken Power Law + 2 Peaks** mass model (arXiv:2508.18083 App. B.3,
Table 6), that model is now implemented (`jaxmodels.log_p_m1`, `spec.mass = "bpl2p"`: broken power law + two
left-truncated Gaussians, Dir(1,1,1) mixing, m_high pinned at 300 Msun, its own m2 taper, triangular m1,low/m2,low
priors, log-uniform χeff width intercept). Models `lvk_bpl2p_{both,mean,width,null}` give the E3 decomposition
under the LVK masses and a second gate, `gate_lvk_masses`, in `diagnostics_full.json` / `summary_full.md`.

`run_lvk_followup.sh` waits for the main chain to exit, fits the four models on the GPU
(`run_all.py --mode full --stages fit --models lvk_bpl2p_both,... --skip-nuts`, ~10-20 min each), then re-runs
`diagnostics,figures --force`. Log: `../logs/run_all_full_lvk.out`.

## Ablation of the LVK configuration and the final chain (2026-09-11/13, deviations D16-D18)

* D16: after the primary E1 pair, `modes.full.n_networks` was reduced 4 -> 2 and `copula_frank_plp` dropped
  (33-dim nautilus fits took 3-4 h each, dominated by the sampler's own overhead).
* D17: four single-ingredient ablations of the LVK configuration -- `abl_plp_m2taper_both`, `abl_plp_lvkspin_both`,
  `abl_bpl2p_sharedtaper_both`, `abl_bpl2p_plpspin_both` -- identify which ingredient (separate m2 taper,
  log-uniform sigma_0 prior, or the Broken Power Law + 2 Peaks shape itself) removes the chi_eff-mean shift.
  Diagnostics write `results/tables/slope_credibilities_full.csv` (P(delta mu < 0), P(delta ln sigma < 0) for every
  fitted model with both slopes free) and a table in `results/summary_full.md`.
* D18: `copula_indep_splm1` (41 dims) was dropped after its 42-dim twin took 34 h; E1c is reported via the
  Savage-Dickey ratio on `copula_gauss_splm1`.
* Chain scripts, in the order they ran: `run_full_chain.sh` (fetch/build/test, 2026-09-02), `run_gpu_chain.sh`
  (first GPU stages), `run_lvk_followup.sh` (D15 LVK fits), `run_gpu_chain2.sh` (E4 + E1c fits), `run_gpu_chain4.sh`
  (ablations, mocks, mock statistics, final diagnostics and figures). All append to `../logs/run_all_full_gpu.out`
  (the LVK follow-up to `../logs/run_all_full_lvk.out`) and restart `vllm` when they exit.
