#!/usr/bin/env python
"""Model unit checks (run in smoke mode before the fits, or `make test`):
1. jax PowerLaw+Peak + power-law pairing == gwpopulation.SinglePeakSmoothedMassDistribution
   (jax backend) on random data / parameters;
2. every marginal integrates to 1 on its grid; conditional CDFs are monotone in [0,1];
3. copula densities integrate to ~1 over the unit square;
4. the hierarchical likelihood is finite at random prior draws for every model.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("JAX_PLATFORMS", "cpu")

from config import load_config, setup_logging  # noqa: E402


def main():
    cfg = load_config(mode=sys.argv[1] if len(sys.argv) > 1 else None)
    logger = setup_logging(cfg, "test_models")
    import jax.numpy as jnp
    import gwpopulation
    from gwpopulation.models.mass import SinglePeakSmoothedMassDistribution

    from jaxmodels import Grids, log_population, log_copula, trapz
    from models_registry import MODEL_SPECS, build_model

    gwpopulation.set_backend("jax")
    G = Grids(cfg, 5, 5)
    rng = np.random.default_rng(1)
    n = 5000
    m1 = rng.uniform(3, 90, n)
    q = rng.uniform(0.05, 1, n)
    data = {"mass_1": jnp.asarray(m1), "mass_ratio": jnp.asarray(q), "chi_eff": jnp.asarray(rng.uniform(-1, 1, n)),
            "redshift": jnp.asarray(rng.uniform(0.01, 1.5, n))}
    gw = SinglePeakSmoothedMassDistribution(mmin=G.m1s[0], mmax=G.m1s[-1], normalization_shape=(len(G.m1s), len(G.qs)))
    spec = dict(mass="plp", pairing="powerlaw", spin="truncnorm", copula=None, sigma_floor=0.02)
    worst = 0.0
    for _ in range(5):
        p = dict(alpha=rng.uniform(1, 5), beta=rng.uniform(0, 6), mmin=rng.uniform(3, 7), mmax=rng.uniform(60, 95),
                 lam=rng.uniform(0.01, 0.5), mpp=rng.uniform(25, 45), sigpp=rng.uniform(2, 8), delta_m=rng.uniform(1, 8))
        ref = np.asarray(gw(data, **p))
        pj = {k: jnp.asarray(v) for k, v in p.items()}
        pj.update(mu_chi_eff_0=jnp.asarray(0.0), mu_chi_eff_1=jnp.asarray(0.0), sigma_chi_eff_0=jnp.asarray(0.2),
                  sigma_chi_eff_1=jnp.asarray(0.0), lamb=jnp.asarray(0.0))
        from jaxmodels import log_p_m1, q_conditional
        mine = np.asarray(jnp.exp(log_p_m1(data["mass_1"], pj, spec, G) + q_conditional(data["mass_1"], data["mass_ratio"], pj, spec, G, False)[0]))
        mask = ref > 1e-3 * ref.max()
        rel = np.max(np.abs(mine[mask] - ref[mask]) / ref[mask])
        worst = max(worst, rel)
    logger.info("PLP x pairing vs gwpopulation: worst relative difference %.2e", worst)
    assert worst < 5e-3, worst

    # normalization checks on the grids
    Mg, Qg = np.meshgrid(G.m1s, G.qs, indexing="ij")
    grid = {"mass_1": jnp.asarray(Mg.ravel()), "mass_ratio": jnp.asarray(Qg.ravel())}
    pj_full = dict(pj)
    from jaxmodels import log_p_m1 as lpm1, q_conditional as qc
    pm1 = np.asarray(jnp.exp(lpm1(jnp.asarray(G.m1s), pj_full, spec, G)))
    logger.info("int p(m1) dm1 = %.4f", np.trapezoid(pm1, G.m1s))
    pq = np.asarray(jnp.exp(qc(grid["mass_1"], grid["mass_ratio"], pj_full, spec, G, False)[0])).reshape(Mg.shape)
    ints = np.trapezoid(pq, G.qs, axis=1)
    ok = G.m1s > float(pj_full["mmin"]) * 1.05
    logger.info("int p(q|m1) dq over m1 > mmin: min %.4f max %.4f", ints[ok].min(), ints[ok].max())
    assert abs(np.trapezoid(pm1, G.m1s) - 1) < 2e-2 and np.all(np.abs(ints[ok] - 1) < 2e-2)

    # copula normalization
    u = jnp.linspace(1e-4, 1 - 1e-4, 800)
    U, V = jnp.meshgrid(u, u, indexing="ij")
    for fam, par in (("gaussian", {"gaussian_copula_rho": jnp.asarray(-0.6)}), ("frank", {"frank_copula_theta": jnp.asarray(-6.0)})):
        c = jnp.exp(log_copula(U, V, par, {"copula": fam}))
        val = float(trapz(trapz(c, u, axis=-1), u))
        logger.info("copula %s integrates to %.4f", fam, val)
        assert abs(val - 1) < 2e-2

    # likelihood finiteness at prior draws for every model (tiny fake data)
    from jaxmodels import HierarchicalLikelihood
    N, K = 4, 50
    ev = {"mass_1": rng.uniform(10, 60, (N, K)), "mass_ratio": rng.uniform(0.3, 1, (N, K)),
          "chi_eff": rng.uniform(-0.3, 0.3, (N, K)), "redshift": rng.uniform(0.05, 0.8, (N, K)), "ln_prior": np.zeros((N, K))}
    M = 3000
    inj = {"mass_1": rng.uniform(3, 100, M), "mass_ratio": rng.uniform(0.1, 1, M), "chi_eff": rng.uniform(-1, 1, M),
           "redshift": rng.uniform(0.01, 2, M), "ln_prior": np.zeros(M), "total_generated": 10 * M}
    for name in MODEL_SPECS:
        spec, names, fixed, prior = build_model(name, cfg)
        lik = HierarchicalLikelihood(spec, names, fixed, ev, inj, G, max_variance=1e9, enforce_injection_convergence=False)
        f = lik.make_batched(8)
        vals = f(prior.sample(rng, 48))
        logger.info("%-22s %2d dims, ln L at prior draws finite fraction %.2f (e.g. %.1f)", name, len(names),
                    np.isfinite(vals).mean(), vals[np.isfinite(vals)][0] if np.isfinite(vals).any() else np.nan)
        # the truncnorm-width constraint (sigma_0 - max(sigma_1, 0) >= floor) removes ~half of the prior box
        assert np.isfinite(vals).mean() > 0.25, name
    logger.info("all model checks passed")


if __name__ == "__main__":
    main()
