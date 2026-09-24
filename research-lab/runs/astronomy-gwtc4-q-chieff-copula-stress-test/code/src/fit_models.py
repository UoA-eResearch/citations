#!/usr/bin/env python
"""Stage 03: hierarchical fits of every model in the mode's model set.

Evidence + posterior for each model with nautilus (importance nested sampling,
vectorized likelihood evaluated in jax batches on CPU or GPU; checkpointed to
results/fits/<mode>/<model>/nautilus.h5 so an interrupted run resumes).
Models listed in sampler.nuts_models are additionally sampled with numpyro
NUTS as a posterior-shape cross-check (baseline reproduction gate).

Outputs per model: posterior.npz (equal-weight samples, per-event ln L_i,
injection n_eff, ln Z), summary.json (quantiles, diagnostics, timings).
"""
from __future__ import annotations

import logging

import argparse
import os
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import add_common_args, load_config, setup_logging  # noqa: E402
from gpu import GPUSession  # noqa: E402
from io_utils import read_injection_table, read_sample_table, save_json  # noqa: E402
from models_registry import build_model  # noqa: E402


def load_event_arrays(cfg, rng, max_samples=None):
    posteriors, meta = read_sample_table(cfg.sample_table_path())
    names = sorted(posteriors)
    kmax = int(max_samples or cfg.mode_value("max_posterior_samples_per_event"))
    # Common K = kmax for every event. Events whose public release holds fewer samples (GWTC-3
    # GW200129_065458: 1993, GW150914: 3337 in the Mixed groups) are resampled WITH replacement
    # up to K rather than capping K for the whole catalog (deviations.md D10); their per-event
    # Monte Carlo variance is then under-estimated by the duplication factor (<= 2 for 2/153 events).
    K = kmax
    short = {n: len(posteriors[n]) for n in names if len(posteriors[n]) < K}
    if short:
        logging.getLogger("q_chieff_copula").warning(
            "events with fewer than K=%d posterior samples are resampled with replacement: %s", K, short)
    ev = {c: np.zeros((len(names), K)) for c in ("mass_1", "mass_ratio", "chi_eff", "redshift", "ln_prior")}
    for i, n in enumerate(names):
        df = posteriors[n]
        idx = np.sort(rng.choice(len(df), K, replace=len(df) < K))
        for c in ev:
            ev[c][i] = df[c].values[idx]
    return ev, names, meta


def quantiles(samples, names):
    q = np.percentile(samples, [5, 16, 50, 84, 95], axis=0)
    return {n: {"p5": float(q[0, i]), "p16": float(q[1, i]), "median": float(q[2, i]), "p84": float(q[3, i]),
                "p95": float(q[4, i])} for i, n in enumerate(names)}


def run_nautilus(lik, prior, cfg, fit_dir: Path, seed: int, chunk: int, force: bool, logger):
    from nautilus import Sampler

    batched = lik.make_batched(chunk)

    def prior_fn(u):
        u = np.asarray(u, float)
        return np.array([prior(r) for r in u]) if u.ndim == 2 else prior(u)

    ckpt = fit_dir / "nautilus.h5"
    if force and ckpt.exists():
        ckpt.unlink()
    t0 = time.time()
    sampler = Sampler(prior_fn, batched, n_dim=prior.n_dim, n_live=int(cfg.mode_value("nlive")),
                      n_networks=int(cfg.mode_value("n_networks")), vectorized=True, pass_dict=False,
                      seed=seed, filepath=str(ckpt), resume=not force)
    sampler.run(f_live=float(cfg.raw["sampler"]["f_live"]), n_shell=int(cfg.raw["sampler"]["n_shell"]),
                n_eff=int(cfg.mode_value("posterior_n_eff")), verbose=False)
    wall = time.time() - t0
    points, log_w, log_l = sampler.posterior()
    eq_points, _, eq_log_l = sampler.posterior(equal_weight=True)
    n_like = int(getattr(sampler, "n_like", 0))
    logger.info("nautilus done: ln Z = %.3f, n_eff = %.0f, %d posterior points (%d equal-weight), %d likelihood "
                "calls, %.1f min", sampler.log_z, sampler.n_eff, len(points), len(eq_points), n_like, wall / 60)
    return dict(log_z=float(sampler.log_z), n_eff=float(sampler.n_eff), points=points, log_w=log_w, log_l=log_l,
                eq_points=eq_points, eq_log_l=eq_log_l, n_like=n_like, wall=wall)


def run_nuts(lik, prior, cfg, seed: int, logger):
    import jax
    import jax.numpy as jnp
    import numpyro
    import numpyro.distributions as dist
    from jax.scipy.special import ndtri as jndtri
    from numpyro.infer import MCMC, NUTS

    def model():
        u = numpyro.sample("u", dist.Uniform(0.0, 1.0).expand([prior.n_dim]))
        theta = prior(u, xp=jnp, ndtri=jndtri)
        numpyro.deterministic("theta", theta)
        numpyro.factor("loglike", lik.loglike_soft(theta))

    t0 = time.time()
    kernel = NUTS(model, target_accept_prob=0.8, max_tree_depth=int(cfg.raw["sampler"].get("nuts_max_tree_depth", 10)))
    mcmc = MCMC(kernel, num_warmup=int(cfg.mode_value("numpyro_num_warmup")),
                num_samples=int(cfg.mode_value("numpyro_num_samples")), num_chains=1, progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed))
    theta = np.asarray(mcmc.get_samples()["theta"])
    extra = mcmc.get_extra_fields()
    wall = time.time() - t0
    logger.info("NUTS done: %d samples, %.1f min", len(theta), wall / 60)
    return theta, wall, extra


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common_args(parser)
    parser.add_argument("--models", default=None, help="comma-separated subset of the model set")
    parser.add_argument("--skip-nuts", action="store_true")
    args = parser.parse_args()
    cfg = load_config(mode=args.mode)
    logger = setup_logging(cfg, "03_fit_models")
    model_set = args.models.split(",") if args.models else list(cfg.mode_value("model_set"))
    nuts_models = [] if args.skip_nuts else [m for m in cfg.raw["sampler"].get("nuts_models", []) if m in model_set]

    # D28: SEED_TAG=<k> refits with a different nautilus seed into fits/<mode>/<model>__seed<k> (main fits untouched)
    seed_tag = os.environ.get("SEED_TAG", "")
    fdir = (lambda m: cfg.fit_dir(f"{m}__seed{seed_tag}")) if seed_tag else cfg.fit_dir
    todo = [m for m in model_set if args.force or not (fdir(m) / "summary.json").exists()]
    todo_nuts = [m for m in nuts_models if args.force or not (cfg.fit_dir(m) / "summary_nuts.json").exists()]
    if not todo and not todo_nuts:
        logger.info("all fits present, skipping (use --force to redo)")
        return

    ev, names, meta = load_event_arrays(cfg, cfg.rng("fit_subsample"))
    inj = read_injection_table(cfg.injection_table_path())
    logger.info("data: %d events x %d samples; %d found injections (total_generated=%.0f)", *ev["mass_1"].shape,
                len(inj["mass_1"]), inj["total_generated"])
    lik_cfg = cfg.raw["likelihood"]

    with GPUSession(cfg, args.backend) as gs:
        from jaxmodels import Grids, HierarchicalLikelihood

        chunk = int(cfg.raw["run"][gs.chunk_key])
        G = Grids(cfg, cfg.mode_value("mass_spline_nodes"), cfg.mode_value("marginal_spline_nodes"))
        for model in sorted(set(todo) | set(todo_nuts), key=model_set.index):
            fit_dir = fdir(model)
            spec, pnames, fixed, prior = build_model(model, cfg)
            lik = HierarchicalLikelihood(spec, pnames, fixed, ev, inj, G, max_variance=cfg.max_variance,
                                         enforce_injection_convergence=bool(lik_cfg["enforce_injection_convergence"]),
                                         cache_key=f"ns_{model}", gradient_mode=lik_cfg.get("gradient_mode", "auto"),
                                         cut_mode=lik_cfg.get("cut_mode", "hard"),
                                         penalty_scale=float(lik_cfg.get("penalty_scale", 1000.0)))
            logger.info("model %s: %d free parameters %s; fixed=%s", model, len(pnames), pnames, fixed)
            batched = lik.make_batched(chunk)
            rng = cfg.rng(f"fit_{model}")
            test = prior.sample(rng, 2 * chunk)
            t0 = time.time()
            vals = batched(test)
            t_compile = time.time() - t0
            t0 = time.time()
            vals = batched(test)
            t_eval = time.time() - t0
            logger.info("likelihood timing: compile %.1fs, %.3f s/point (%d points); finite fraction at prior draws %.2f",
                        t_compile, t_eval / len(test), len(test), np.isfinite(vals).mean())
            if model in todo:
                res = run_nautilus(lik, prior, cfg, fit_dir, cfg.seed_for(f"nautilus_{model}{seed_tag}"), chunk, args.force, logger)
                aux_fn = lik.make_batched_aux(chunk)
                _, aux = aux_fn(res["eq_points"])
                np.savez(fit_dir / "posterior.npz", samples=res["eq_points"], log_l=res["eq_log_l"],
                         names=np.array(pnames), log_z=res["log_z"], lnL_i=aux["lnL_i"], n_eff_inj=aux["n_eff_inj"],
                         var_tot=aux["var_tot"], ln_pdet=aux["ln_pdet"], weighted_points=res["points"],
                         weighted_log_w=res["log_w"], event_names=np.array(names))
                summary = dict(model=model, spec={k: v for k, v in spec.items() if k != "fixed"}, fixed=fixed,
                               names=pnames, n_dim=len(pnames), log_z=res["log_z"], posterior_n_eff=res["n_eff"],
                               n_equal_weight=len(res["eq_points"]), n_like=res["n_like"], wall_s=res["wall"],
                               s_per_point=t_eval / len(test), platform=gs.platform, n_events=lik.n_events,
                               n_samples_per_event=lik.n_samples, n_injections=len(inj["mass_1"]),
                               quantiles=quantiles(res["eq_points"], pnames),
                               injection_n_eff_min=float(np.min(aux["n_eff_inj"])),
                               injection_n_eff_median=float(np.median(aux["n_eff_inj"])),
                               frac_var_below_1=float(np.mean(aux["var_tot"] < 1.0)),
                               var_tot_quantiles={f"p{q}": float(np.percentile(aux["var_tot"], q))
                                                  for q in (5, 50, 95, 99)},
                               cut_mode=lik.cut_mode, penalty_scale=lik.penalty_scale,
                               max_variance=lik.max_variance,
                               max_log_l=float(np.max(res["eq_log_l"])))
                save_json(summary, fit_dir / "summary.json")
                logger.info("saved %s (ln Z = %.3f)", fit_dir / "summary.json", res["log_z"])
            if model in todo_nuts:
                theta, wall, extra = run_nuts(lik, prior, cfg, cfg.seed_for(f"nuts_{model}"), logger)
                np.savez(fit_dir / "posterior_nuts.npz", samples=theta, names=np.array(pnames))
                save_json(dict(model=model, names=pnames, wall_s=wall, n_samples=len(theta),
                               quantiles=quantiles(theta, pnames), platform=gs.platform),
                          fit_dir / "summary_nuts.json")
    logger.info("stage 03 (fit_models) complete")


if __name__ == "__main__":
    main()
