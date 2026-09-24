#!/usr/bin/env python
"""D27: rebuilt mock catalogs (fixes the two stage-04 defects found in review, D26).

Changes relative to stage 04 (src/mock_catalogs.py):
  1. Jacobian. Kernel samples are the real posterior samples reweighted by pi_flatx / pi_PE, so their density in the
     internal coordinates x = (ln m1, logit q, chi_eff, ln z) is the donor's likelihood L(theta(x)) -- the quantity the
     hierarchical likelihood recovers by dividing mock samples by the flat-x prior. Stage 04 weighted by 1 / pi_PE, which
     multiplied every mock likelihood by m1 q (1 - q) z.
  2. Orientation. Location-family model in x: x_obs = x_true - dev, mock samples = x_obs + dev', dev, dev' ~ kernel. The
     mock likelihood then has the donor's orientation (stage 04 point-reflected it).
  3. Kernel choice. The donor is one of the k nearest real events to the mock event's TRUE parameters in all four
     internal coordinates (standardised; weights 1, 0.5, 0.5, 0.5 for ln m1, logit q, chi_eff, ln z), so likelihood
     shapes near q = 1 come from events whose likelihoods sit near q = 1.
  4. Nuisance. Each mock's population is a random equal-weight posterior draw of the independence fit
     (copula_indep_plp), with the copula rho set to rho_true (posterior-predictive null / calibration).
  5. Alternatives (power): 'width' = lvk_bpl2p_width posterior draws (the LVK Linear-model width effect);
     'mean' = baseline_plp_mean posterior draws (the PowerLaw+Peak mean shift).

Output: data/mocks/v2/mocks_full_<tag>.h5 (tags rho+0.00, rho-0.60, rho-0.40, rho-0.20, rho+0.20, width, mean)
Usage:  ../venv/bin/python analysis/mock_catalogs_v2.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
import h5py  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

import jax  # noqa: E402

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp  # noqa: E402

from config import load_config  # noqa: E402
from io_utils import read_injection_table, read_sample_table  # noqa: E402
from jaxmodels import Grids, log_population, resolve_derived  # noqa: E402
from mock_catalogs import COLS, from_internal, ln_flat_internal_prior, to_internal  # noqa: E402
from models_registry import build_model  # noqa: E402

N_KERNEL, K_NEAREST, CLIP_Q = 2000, 5, 0.999
DIST_W = np.array([1.0, 0.5, 0.5, 0.5])


class KernelBankV2:
    def __init__(self, posteriors, rng):
        self.names = sorted(posteriors)
        self.dev, self.center, self.ess = [], [], []
        for n in self.names:
            df = posteriors[n]
            m1, q, chi, z, lp = (df[c].values for c in ("mass_1", "mass_ratio", "chi_eff", "redshift", "ln_prior"))
            lw = ln_flat_internal_prior(m1, q, chi, z) - lp               # pi_flatx / pi_PE
            w = np.exp(lw - lw.max())
            w = np.minimum(w, np.quantile(w, CLIP_Q))
            w /= w.sum()
            self.ess.append(1.0 / np.sum(w**2))
            idx = rng.choice(len(df), size=N_KERNEL, replace=True, p=w)
            x = to_internal(m1[idx], q[idx], chi[idx], z[idx])
            med = np.median(x, axis=0)
            self.dev.append(x - med)
            self.center.append(med)
        self.center, self.dev = np.array(self.center), np.array(self.dev)
        self.scale = self.center.std(axis=0)

    def pick(self, x_true, rng):
        d = np.sqrt((((self.center - x_true) / self.scale * DIST_W) ** 2).sum(axis=1))
        return int(rng.choice(np.argsort(d)[:K_NEAREST]))

    def scatter(self, x_true, rng):
        j = self.pick(x_true, rng)
        dev = self.dev[j]
        obs = x_true - dev[rng.integers(len(dev))]          # x_obs = x_true - eps
        return obs + dev, obs, j                            # likelihood samples keep the donor's orientation


def main():
    cfg = load_config(mode="full", config_path=str(HERE.parent / "config.yaml"))
    rng = np.random.default_rng(cfg.seed_for("mocks_v2"))
    posteriors, _ = read_sample_table(cfg.sample_table_path())
    n_events = len(posteriors)
    inj = read_injection_table(cfg.injection_table_path())
    d_inj = {k: jnp.asarray(inj[k]) for k in COLS}
    G = Grids(cfg, cfg.mode_value("mass_spline_nodes"), cfg.mode_value("marginal_spline_nodes"))
    bank = KernelBankV2(posteriors, rng)
    print(f"kernel bank: {len(bank.names)} events, kernel ESS median {np.median(bank.ess):.0f} (min {np.min(bank.ess):.0f})", flush=True)
    outdir = cfg.path("mocks_dir") / "v2"
    outdir.mkdir(parents=True, exist_ok=True)

    def draws(model, n):
        post = np.load(cfg.fit_dir(model) / "posterior.npz", allow_pickle=True)
        names = [str(x) for x in post["names"]]
        sel = rng.choice(len(post["samples"]), n, replace=False)
        return [dict(zip(names, post["samples"][i])) for i in sel], sel

    sets = [(f"rho{r:+.2f}", "copula_gauss_plp", "copula_indep_plp", r, 200 if r == 0 else 40)
            for r in [0.0, -0.6, -0.4, -0.2, 0.2]]
    sets += [("width", "lvk_bpl2p_width", "lvk_bpl2p_width", None, 40), ("mean", "baseline_plp_mean", "baseline_plp_mean", None, 40)]
    summary = {}
    for tag, gen_model, post_model, rho, n_mocks in sets:
        spec, _, fixed, _ = build_model(gen_model, cfg)
        pars, sel = draws(post_model, n_mocks)
        path = outdir / f"mocks_full_{tag}.h5"
        ess_list = []
        with h5py.File(path.with_suffix(".h5.part"), "w") as f:
            f.attrs.update(tag=tag, generating_model=gen_model, posterior_of=post_model, n_events=n_events, n_kernel=N_KERNEL)
            for i, par in enumerate(pars):
                p = dict(par)
                p.update(fixed)
                if rho is not None:
                    p["gaussian_copula_rho"] = rho
                pj = resolve_derived({k: jnp.asarray(float(v)) for k, v in p.items()}, spec)
                lw = np.asarray(log_population(d_inj, pj, spec, G)) - inj["ln_prior"]
                w = np.exp(lw - lw.max())
                w /= w.sum()
                ess_list.append(1.0 / np.sum(w**2))
                idx = rng.choice(len(w), size=n_events, replace=True, p=w)
                x_true = to_internal(*[inj[c][idx] for c in COLS])
                samples = np.zeros((n_events, N_KERNEL, 4))
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
                g.attrs["posterior_draw_index"] = int(sel[i])
                g.attrs["params"] = json.dumps({k: float(v) for k, v in p.items()})
        path.with_suffix(".h5.part").rename(path)
        summary[tag] = dict(n=n_mocks, generating_model=gen_model, rho=rho, ess_min=float(np.min(ess_list)),
                            ess_median=float(np.median(ess_list)))
        print(f"{tag:<9} {n_mocks:3d} mocks from {gen_model} (posterior draws of {post_model}); injection ESS median "
              f"{np.median(ess_list):.0f} (min {np.min(ess_list):.0f}) -> {path.name}", flush=True)
    json.dump(dict(summary=summary, kernel_ess_median=float(np.median(bank.ess)), clip_q=CLIP_Q, k_nearest=K_NEAREST,
                   dist_weights=DIST_W.tolist()), open(outdir / "mock_generation_v2.json", "w"), indent=2)


if __name__ == "__main__":
    main()
