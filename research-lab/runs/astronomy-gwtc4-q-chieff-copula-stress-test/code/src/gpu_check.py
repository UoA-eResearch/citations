#!/usr/bin/env python
"""Optional stage: verify the GPU code path and time the compiled likelihood.

Stops the vllm container (if the GPU is not free), compiles the batched
likelihood for the primary models on the GPU, times a chunk of evaluations,
runs a very short nautilus loop, restarts vllm, and writes
logs/gpu_check_<mode>.json with seconds-per-likelihood-point. The stopped
window is ~2-3 minutes. Never run by default (`--stages gpucheck`).
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import add_common_args, load_config, setup_logging  # noqa: E402
from fit_models import load_event_arrays  # noqa: E402
from gpu import GPUSession, gpu_free_mib  # noqa: E402
from io_utils import read_injection_table, save_json  # noqa: E402
from models_registry import build_model  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common_args(parser)
    parser.add_argument("--models", default="baseline_plp_both,copula_gauss_plp")
    parser.add_argument("--n-batches", type=int, default=5)
    parser.add_argument("--full-scale", nargs=2, type=int, metavar=("N_EVENTS", "K_SAMPLES"), default=None,
                        help="time the likelihood at full-run array shapes: tile the available events to "
                             "N_EVENTS x K_SAMPLES (resampled with small jitter) and use ALL found injections "
                             "from the raw Zenodo file (no full-mode sample table needed)")
    args = parser.parse_args()
    cfg = load_config(mode=args.mode)
    logger = setup_logging(cfg, "gpu_check")
    rng = cfg.rng("gpucheck_data")
    if args.full_scale:
        n_ev, k = args.full_scale
        from io_utils import read_sample_table
        from selection import standardize_real_injections
        posteriors, _ = read_sample_table(cfg.sample_table_path())
        keys = sorted(posteriors)
        ev = {c: np.zeros((n_ev, k)) for c in ("mass_1", "mass_ratio", "chi_eff", "redshift", "ln_prior")}
        for i in range(n_ev):
            df = posteriors[keys[i % len(keys)]]
            idx = rng.choice(len(df), k, replace=True)
            for c in ev:
                ev[c][i] = df[c].values[idx]
            ev["mass_1"][i] *= np.exp(rng.normal(0, 0.05, k))          # jitter so events are not identical
        names = [f"tiled_{i}" for i in range(n_ev)]
        scfg = cfg.raw["sample"]
        chieff_kwargs = dict(n_mc=int(scfg["chieff_prior_mc_samples"]), n_q=int(scfg["chieff_prior_q_grid"]),
                             n_chi=int(scfg["chieff_prior_chi_grid"]), seed=cfg.seed_for("chieff_prior"))
        inj, _ = standardize_real_injections(
            cfg.path("raw_injections_dir") / cfg.raw["data_sources"]["injection_file_key"], cfg.far_threshold,
            float(scfg["semianalytic_snr_threshold"]), cfg.path("processed_dir") / "chieff_prior_cache", chieff_kwargs,
            slice_n=None, spin_families=cfg.raw["data_sources"].get("injection_spin_families"))
        # full-mode normalisation grids regardless of the smoke overrides
        cfg.raw["modes"][cfg.mode]["grid_overrides"] = cfg.raw["modes"]["full"].get("grid_overrides", {})
        for key in ("mass_spline_nodes", "marginal_spline_nodes"):
            cfg.raw["modes"][cfg.mode][key] = cfg.raw["modes"]["full"][key]
        logger.info("full-scale timing: %d events x %d samples, %d found injections, grids %s", n_ev, k,
                    len(inj["mass_1"]), cfg.grids)
    else:
        ev, names, meta = load_event_arrays(cfg, cfg.rng("fit_subsample"))
        inj = read_injection_table(cfg.injection_table_path())
    report = dict(mode=cfg.mode, full_scale=args.full_scale, n_events=int(ev["mass_1"].shape[0]),
                  n_samples=int(ev["mass_1"].shape[1]), n_injections=int(len(inj["mass_1"])), models={})
    backend = args.backend or "gpu"
    with GPUSession(cfg, backend) as gs:
        import jax
        from jaxmodels import Grids, HierarchicalLikelihood
        report["platform"] = gs.platform
        report["jax_devices"] = [str(d) for d in jax.devices()]
        report["gpu_free_mib_at_start"] = gpu_free_mib()
        logger.info("jax devices: %s", report["jax_devices"])
        chunk = int(cfg.raw["run"][gs.chunk_key])
        G = Grids(cfg, cfg.mode_value("mass_spline_nodes"), cfg.mode_value("marginal_spline_nodes"))
        for model in args.models.split(","):
            spec, pnames, fixed, prior = build_model(model, cfg)
            lik = HierarchicalLikelihood(spec, pnames, fixed, ev, inj, G, max_variance=cfg.max_variance,
                                         enforce_injection_convergence=True, cache_key=f"gpucheck_{model}")
            batched = lik.make_batched(chunk)
            rng = cfg.rng(f"gpucheck_{model}")
            test = prior.sample(rng, chunk * args.n_batches)
            t0 = time.time()
            batched(test[:chunk])
            t_compile = time.time() - t0
            t0 = time.time()
            vals = batched(test)
            t_eval = time.time() - t0
            rep = dict(n_dim=len(pnames), chunk=chunk, compile_s=t_compile, s_per_point=t_eval / len(test),
                       finite_fraction=float(np.isfinite(vals).mean()))
            grads = {}
            for mode in ("forward", "reverse"):
                lik.gradient_mode = mode
                vg = lik.soft_value_and_grad()
                t0 = time.time()
                v0, g0 = vg(test[0])
                rep[f"grad_compile_s_{mode}"] = time.time() - t0
                t0 = time.time()
                for i in range(8):
                    vg(test[i])
                rep[f"s_per_grad_{mode}"] = (time.time() - t0) / 8
                grads[mode] = g0
            rep["grad_fwd_vs_rev_max_abs_diff"] = float(np.max(np.abs(grads["forward"] - grads["reverse"])))
            rep["grad_max_abs"] = float(np.max(np.abs(grads["reverse"])))
            report["models"][model] = rep
            logger.info("%s: compile %.1fs, %.4f s/point (chunk %d); grad forward %.4f s (compile %.1fs), reverse %.4f s "
                        "(compile %.1fs), max|fwd-rev| %.2e (max|grad| %.2e); finite %.2f", model, t_compile,
                        t_eval / len(test), chunk, rep["s_per_grad_forward"], rep["grad_compile_s_forward"],
                        rep["s_per_grad_reverse"], rep["grad_compile_s_reverse"], rep["grad_fwd_vs_rev_max_abs_diff"],
                        rep["grad_max_abs"], np.isfinite(vals).mean())
            lik.gradient_mode = "forward"
        # short nautilus loop on the last model to exercise the full sampler path on the GPU
        from nautilus import Sampler
        t0 = time.time()
        sampler = Sampler(lambda u: prior(u), batched, n_dim=prior.n_dim, n_live=100, n_networks=1,
                          vectorized=True, pass_dict=False, seed=1)
        sampler.run(f_live=0.5, n_shell=1, n_eff=50, n_like_max=3000, verbose=False)
        report["nautilus_smoke"] = dict(log_z=float(sampler.log_z), wall_s=time.time() - t0, n_like=int(sampler.n_like))
        logger.info("nautilus GPU smoke loop: ln Z=%.2f after %d calls in %.1fs", sampler.log_z, sampler.n_like,
                    time.time() - t0)
    report["gpu_free_mib_after_restart"] = gpu_free_mib()
    tag = f"{cfg.mode}_fullscale" if args.full_scale else cfg.mode
    save_json(report, cfg.path("logs_dir") / f"gpu_check_{tag}.json")
    logger.info("gpu check complete: %s", report)


if __name__ == "__main__":
    main()
