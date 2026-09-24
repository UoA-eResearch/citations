#!/usr/bin/env python
"""Stage 04: mock catalogs for the E2 false-positive-rate calibration.

For rho_true in {0} U rho_true_grid:
  * population = the copula model with the q and chi_eff marginals (and m1,
    z sectors) fixed at the posterior median of the real-data independence
    fit (copula_indep_plp), Gaussian copula with the chosen rho_true
    (rho_true = 0: zero intrinsic correlation by construction);
  * detected events are drawn from the found injections with weights
    w_j p_pop(theta_j) / p_draw(theta_j), i.e. from p_pop x p_det with the
    real O1-O4a selection function, N = number of real events;
  * PE uncertainty: each mock event borrows the likelihood-shaped scatter
    of a real event with similar (m1, z) (a random one of the k nearest):
    the real posterior samples are reweighted by 1/prior (likelihood-shaped),
    mapped to x = (ln m1, logit q, chi_eff, ln z) and re-centred to give a
    kernel k(eps). The mock noise model is x_obs = x_true + eps, eps ~ k, so
    the mock likelihood is L(x_obs | x_true) = k(x_obs - x_true) and the mock
    "posterior samples" under a prior flat in x are x_obs - eps', eps' ~ k.
    A prior flat in x is, in the population coordinates (m1, q, chi_eff, z),
    pi(theta) = |dx/dtheta| = 1 / (m1 q (1-q) z); that Jacobian is stored as
    the mock ln_prior column so the hierarchical likelihood divides it out
    exactly as it does for the real PE prior.
Outputs: data/mocks/mocks_<mode>_rho<+x.xx>.h5
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("JAX_PLATFORMS", "cpu")   # cheap stage; no GPU needed

from config import add_common_args, load_config, setup_logging  # noqa: E402
from io_utils import load_json, read_injection_table, read_sample_table, save_json  # noqa: E402
from models_registry import build_model  # noqa: E402

COLS = ("mass_1", "mass_ratio", "chi_eff", "redshift")


def to_internal(m1, q, chi, z):
    q = np.clip(q, 1e-3, 1 - 1e-4)
    return np.stack([np.log(m1), np.log(q / (1 - q)), chi, np.log(np.clip(z, 1e-4, None))], axis=-1)


def from_internal(x):
    m1 = np.exp(x[..., 0])
    q = 1 / (1 + np.exp(-x[..., 1]))
    chi = np.clip(x[..., 2], -0.999, 0.999)
    z = np.exp(x[..., 3])
    return m1, q, chi, z


def ln_flat_internal_prior(m1, q, chi, z):
    """ln pi(m1, q, chi_eff, z) for a prior flat in (ln m1, logit q, chi_eff, ln z)."""
    q = np.clip(q, 1e-6, 1 - 1e-6)
    return -np.log(m1) - np.log(q) - np.log1p(-q) - np.log(np.clip(z, 1e-6, None))


class PEKernelBank:
    """Likelihood-shaped, re-centred scatter kernels from the real events."""

    def __init__(self, posteriors: dict, rng, n_kernel: int, clip_q: float, k_neighbors: int):
        self.names = sorted(posteriors)
        self.k = int(k_neighbors)
        self.dev, self.center = [], []
        for n in self.names:
            df = posteriors[n]
            w = np.exp(-(df["ln_prior"].values - df["ln_prior"].values.max()))
            w = np.minimum(w, np.quantile(w, clip_q))
            w /= w.sum()
            idx = rng.choice(len(df), size=n_kernel, replace=True, p=w)
            x = to_internal(df["mass_1"].values[idx], df["mass_ratio"].values[idx], df["chi_eff"].values[idx],
                            df["redshift"].values[idx])
            med = np.median(x, axis=0)
            self.dev.append(x - med)
            self.center.append(med)
        self.center = np.array(self.center)
        self.dev = np.array(self.dev)          # (N_real, n_kernel, 4)

    def pick(self, x_true, rng):
        """index of a kernel event: random among the k nearest in (ln m1, ln z)."""
        d = np.hypot(self.center[:, 0] - x_true[0], 0.5 * (self.center[:, 3] - x_true[3]))
        nearest = np.argsort(d)[: self.k]
        return int(rng.choice(nearest))

    def scatter(self, x_true, rng):
        """Returns (mock posterior samples (n_kernel, 4), observed point (4,), kernel index)."""
        j = self.pick(x_true, rng)
        dev = self.dev[j]
        obs = x_true + dev[rng.integers(len(dev))]        # x_obs = x_true + eps
        return obs - dev, obs, j                          # x_true | x_obs  ~  x_obs - eps'


def population_weights(inj, params, spec, G, log_population_fn):
    import jax.numpy as jnp
    d = {k: jnp.asarray(inj[k]) for k in COLS}
    p = {k: jnp.asarray(float(v)) for k, v in params.items()}
    lw = np.asarray(log_population_fn(d, p, spec, G)) - inj["ln_prior"]
    lw -= lw.max()
    w = np.exp(lw)
    return w / w.sum()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = load_config(mode=args.mode)
    logger = setup_logging(cfg, "04_mock_catalogs")
    mcfg = cfg.raw["mocks"]
    rhos = [0.0] + cfg.rho_true_grid
    outputs = {r: cfg.mocks_path(r) for r in rhos}
    if not args.force and all(p.exists() for p in outputs.values()):
        logger.info("all mock files exist, skipping (use --force to redo)")
        return

    ref_dir = cfg.fit_dir("copula_indep_plp")
    ref = load_json(ref_dir / "summary.json")
    base_params = {n: q["median"] for n, q in ref["quantiles"].items()}
    base_params.update(ref["fixed"])
    posteriors, meta = read_sample_table(cfg.sample_table_path())
    n_events = len(posteriors)
    inj = read_injection_table(cfg.injection_table_path())
    n_kernel = min(int(cfg.mode_value("max_posterior_samples_per_event")), 2000)
    rng = cfg.rng("mock_catalogs")
    bank = PEKernelBank(posteriors, rng, n_kernel, float(mcfg["kernel_weight_clip_quantile"]),
                        int(mcfg["kernel_neighbors"]))

    from jaxmodels import Grids, log_population
    G = Grids(cfg, cfg.mode_value("mass_spline_nodes"), cfg.mode_value("marginal_spline_nodes"))
    spec, _, _, _ = build_model("copula_gauss_plp", cfg)

    for rho in rhos:
        out = outputs[rho]
        if out.exists() and not args.force:
            continue
        n_mocks = int(cfg.mode_value("n_mock_catalogs") if rho == 0.0 else cfg.mode_value("n_mock_catalogs_per_rho"))
        params = dict(base_params, gaussian_copula_rho=rho)
        w = population_weights(inj, params, spec, G, log_population)
        ess = 1.0 / np.sum(w**2)
        logger.info("rho_true=%+.2f: injection reweighting ESS = %.0f (need >> N=%d); generating %d mocks",
                    rho, ess, n_events, n_mocks)
        if ess < 5 * n_events:
            logger.warning("low ESS for mock generation at rho=%+.2f", rho)
        tmp = out.with_suffix(".h5.part")
        with h5py.File(tmp, "w") as f:
            f.attrs.update(rho_true=rho, n_events=n_events, n_kernel=n_kernel, ess=ess, n_mocks=n_mocks)
            f.attrs["params"] = str(params)
            for i in range(n_mocks):
                idx = rng.choice(len(w), size=n_events, replace=True, p=w)
                x_true = to_internal(*[inj[c][idx] for c in COLS])
                samples = np.zeros((n_events, n_kernel, 4))
                obs = np.zeros((n_events, 4))
                kern = np.zeros(n_events, int)
                for e in range(n_events):
                    samples[e], obs[e], kern[e] = bank.scatter(x_true[e], rng)
                g = f.create_group(f"mock_{i:04d}")
                m1, q, chi, z = from_internal(samples)
                for c, arr in zip(COLS, (m1, q, chi, z)):
                    g.create_dataset(c, data=arr)
                g.create_dataset("ln_prior", data=ln_flat_internal_prior(m1, q, chi, z))
                g.create_dataset("true", data=np.stack(from_internal(x_true), axis=-1))
                g.create_dataset("observed", data=np.stack(from_internal(obs), axis=-1))
                g.create_dataset("kernel_event", data=kern)
                g.create_dataset("injection_index", data=idx)
        tmp.rename(out)
        logger.info("wrote %s", out)
    save_json({"rhos": rhos, "base_params": base_params, "n_events": n_events, "n_kernel": n_kernel},
              cfg.path("mocks_dir") / f"mock_generation_{cfg.mode}.json")
    logger.info("stage 04 (mock_catalogs) complete")


if __name__ == "__main__":
    main()
