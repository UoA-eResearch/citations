#!/usr/bin/env python
"""D27b: physically parameterised mock PE (samples importance-resampled to the PE prior) (the standard population-study construction), replacing the translated
likelihood-shape kernels of stage 04 / v2, which cannot reproduce the q -> 1 pile-up (mock_validation_full.json).

Measurement model, in y = (ln Mc_det, eta, chi_eff, ln d_L), with eta = q / (1 + q)^2 <= 1/4:
  * each real event i gives a Gaussian approximation of its likelihood in y: covariance Sigma_i from the event's samples
    reweighted to a prior flat in y (weights pi_flaty / pi_PE);
  * a mock event with true y_t borrows Sigma from one of the k = 5 real events nearest in (ln Mc_det, ln d_L)
    (which set the SNR); the observed point is y_obs = y_t + N(0, Sigma) (eta_obs may exceed 1/4: noise does that);
  * the mock likelihood is N(y | y_obs, Sigma) truncated to the physical region (eta <= 1/4, |chi_eff| < 1);
    2000 samples are drawn from it by rejection, converted to (m1_src, q, chi_eff, z);
  * the stored ln_prior is ln pi_flaty(theta) = ln |d y / d theta| = -ln m1 + ln(1 - q) - 3 ln(1 + q) + ln(d d_L/dz / d_L),
    so the hierarchical likelihood (samples / prior) recovers the Gaussian likelihood exactly.
The q -> 1 pile-up then follows from d eta / d q = 0 at q = 1, as for real signals.
Populations as in v2: posterior draws of copula_indep_plp at rho_true (null + calibration), plus 'width'
(lvk_bpl2p_width) and 'mean' (baseline_plp_mean) alternatives.

Output: data/mocks/v3/mocks_full_<tag>.h5 ; data/mocks/v3/mock_generation_v3.json

D27c (v3c, env PDET=1 -> data/mocks/v3c): the v3b world decides detection from the TRUE parameters (a found injection)
and draws the PE noise independently, so the event's data are (y_obs, detected) and its likelihood is
N(y_obs | y(theta), Sigma) * P_det(theta). v3b dropped the P_det factor, which makes the standard hierarchical
likelihood inconsistent with how the mocks were generated (Essick & Fishbach 2024, arXiv:2310.02017; the rho scan at
the true nuisance is biased by about -0.14 on v3b). v3c includes it in the importance weights, so each mock posterior
is N * P_det * pi_PE and the standard analysis (samples / pi_PE) is exact for the mocks, as it is for real events.
P_det(theta) is the density-ratio estimate from the found injections (analysis/pdet_grid.py).

D29d (v3d, env PDET=1 DONOR_KEY=4d -> data/mocks/v3d): as v3c, but the donor covariance is matched in all four
coordinates (ln Mc_det, eta, chi_eff, ln d_L) instead of (ln Mc_det, ln d_L) alone. The real likelihoods' eta-chi_eff
correlation depends on the spin (median +0.43 for events with chi_eff > 0.3, +0.09 otherwise), so a high-spin mock
event must inherit its degeneracy shape from a high-spin real event for the PE prior to act on it as it does on real
events (prior_response_unit_test.py, prior_shift_surface.py).
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
from models_registry import build_model  # noqa: E402
from pe_priors import ChiEffPriorTable, ddl_dz, ln_pe_prior, redshift_from_dl  # noqa: E402

COLS = ("mass_1", "mass_ratio", "chi_eff", "redshift")
N_KERNEL, K_NEAREST, N_RAW = 2000, 5, 12000


def dl_of_z(z):
    from astropy.cosmology import Planck15
    return Planck15.luminosity_distance(z).value


_ZG = np.linspace(1e-4, 3.5, 20000)
_DLG = None


def dl_fast(z):
    global _DLG
    if _DLG is None:
        _DLG = dl_of_z(_ZG)
    return np.interp(z, _ZG, _DLG)


def z_fast(dl):
    global _DLG
    if _DLG is None:
        _DLG = dl_of_z(_ZG)
    return np.interp(dl, _DLG, _ZG)


def to_y(m1, q, chi, z):
    mc_det = m1 * q ** 0.6 / (1 + q) ** 0.2 * (1 + z)
    return np.stack([np.log(mc_det), q / (1 + q) ** 2, chi, np.log(dl_fast(z))], axis=-1)


def from_y(y):
    lnmc, eta, chi, lndl = y[..., 0], np.clip(y[..., 1], 1e-6, 0.25), y[..., 2], y[..., 3]
    s = np.sqrt(np.clip(1 - 4 * eta, 0, None))
    q = (1 - s) / (1 + s)                                  # q <= 1 root of eta = q / (1 + q)^2
    q = np.clip(q, 1e-4, 1.0)
    z = z_fast(np.exp(lndl))
    m1_det = np.exp(lnmc) * (1 + q) ** 0.2 / q ** 0.6
    return m1_det / (1 + z), q, chi, z


def ln_pi_flaty(m1, q, chi, z):
    """ln |d(ln Mc_det, eta, chi_eff, ln d_L) / d(m1_src, q, chi_eff, z)| (upper-triangular Jacobian)."""
    dl = dl_fast(z)
    return (-np.log(m1) + np.log(np.clip(1 - q, 1e-12, None)) - 3 * np.log1p(q)
            + np.log(np.asarray(ddl_dz(z), float)) - np.log(dl))


class GaussBank:
    def __init__(self, posteriors, meta=None, table=None, pdet=None, key_dims=(0, 3)):
        self.pdet = pdet
        self.key_dims = list(key_dims)
        self.names = sorted(posteriors)
        self.zprior = [meta[n]["redshift_prior"] for n in self.names] if meta else None
        self.table = table
        self.ess = []
        self.mu, self.cov = [], []
        for n in self.names:
            d = posteriors[n]
            m1, q, chi, z, lp = (d[c].values for c in COLS + ("ln_prior",))
            lw = ln_pi_flaty(m1, q, chi, z) - lp
            w = np.exp(lw - lw.max())
            w = np.minimum(w, np.quantile(w, 0.999))
            w /= w.sum()
            y = to_y(m1, q, chi, z)
            mu = (w[:, None] * y).sum(0)
            dy = y - mu
            self.mu.append(mu)
            self.cov.append((w[:, None, None] * dy[:, :, None] * dy[:, None, :]).sum(0))
        self.mu, self.cov = np.array(self.mu), np.array(self.cov)
        self.key = self.mu[:, self.key_dims]
        self.key_scale = self.key.std(0)
        self.chol = np.linalg.cholesky(self.cov + 1e-12 * np.eye(4))

    def mock_event(self, y_t, rng):
        d = np.sqrt((((self.key - y_t[self.key_dims]) / self.key_scale) ** 2).sum(1))
        j = int(rng.choice(np.argsort(d)[:K_NEAREST]))
        L = self.chol[j]
        y_obs = y_t + L @ rng.standard_normal(4)
        out, n_have = [], 0
        for _ in range(400):
            s = y_obs + rng.standard_normal((2 * N_RAW, 4)) @ L.T
            ok = (s[:, 1] <= 0.25) & (s[:, 1] > 1e-4) & (np.abs(s[:, 2]) < 0.999)
            out.append(s[ok])
            n_have += int(ok.sum())
            if n_have >= N_RAW:
                break
        s = np.concatenate(out)[:N_RAW]
        # D27b: importance-resample the flat-in-y likelihood samples to the donor event's PE prior, so each mock event
        # carries a posterior formed exactly like a released LVK posterior (stored prior = ln pi_PE)
        m1, q, chi, z = from_y(s)
        lnpe = ln_pe_prior(m1, q, z, chi, self.zprior[j], self.table)
        lw = lnpe - ln_pi_flaty(m1, q, chi, z)
        if self.pdet is not None:                          # D27c: the detection factor of the v3 world's likelihood
            lw = lw + self.pdet.ln_pdet(m1, q, chi, z)
        w = np.exp(lw - lw.max())
        w /= w.sum()
        self.ess.append(1.0 / np.sum(w**2))
        idx = rng.choice(len(s), size=N_KERNEL, replace=True, p=w)
        return np.stack([m1[idx], q[idx], chi[idx], z[idx]], axis=-1), lnpe[idx], y_obs, j


def main():
    cfg = load_config(mode="full", config_path=str(HERE.parent / "config.yaml"))
    rng = np.random.default_rng(cfg.seed_for("mocks_v3"))
    posteriors, _ = read_sample_table(cfg.sample_table_path())
    n_events = len(posteriors)
    inj = read_injection_table(cfg.injection_table_path())
    d_inj = {k: jnp.asarray(inj[k]) for k in COLS}
    G = Grids(cfg, cfg.mode_value("mass_spline_nodes"), cfg.mode_value("marginal_spline_nodes"))
    _, meta = read_sample_table(cfg.sample_table_path())
    sc = cfg.raw["sample"]
    table = ChiEffPriorTable(0.99, cfg.path("processed_dir") / "chieff_prior_cache", n_mc=int(sc["chieff_prior_mc_samples"]),
                             n_q=int(sc["chieff_prior_q_grid"]), n_chi=int(sc["chieff_prior_chi_grid"]), seed=cfg.seed_for("chieff_prior"))
    use_pdet = os.environ.get("PDET", "0") == "1"
    pdet = None
    if use_pdet:
        sys.path.insert(0, str(HERE))
        from pdet_grid import PdetGrid
        pdet = PdetGrid(cfg.path("processed_dir") / "pdet_grid_full.npz")
    donor4 = os.environ.get("DONOR_KEY", "2d") == "4d"
    bank = GaussBank(posteriors, meta, table, pdet, key_dims=(0, 1, 2, 3) if donor4 else (0, 3))
    sd = np.sqrt(np.diagonal(bank.cov, axis1=1, axis2=2))
    print("Gaussian bank: median sd (ln Mc_det, eta, chi_eff, ln d_L) =", np.round(np.median(sd, 0), 4), flush=True)
    outdir = cfg.path("mocks_dir") / (("v3d" if donor4 else "v3c") if use_pdet else ("v3_4d" if donor4 else "v3"))
    outdir.mkdir(parents=True, exist_ok=True)
    only = os.environ.get("ONLY")

    def draws(model, n):
        post = np.load(cfg.fit_dir(model) / "posterior.npz", allow_pickle=True)
        names = [str(x) for x in post["names"]]
        sel = rng.choice(len(post["samples"]), n, replace=False)
        return [dict(zip(names, post["samples"][i])) for i in sel], sel

    sets = [(f"rho{r:+.2f}", "copula_gauss_plp", "copula_indep_plp", r, 200 if r == 0 else 40) for r in [0.0, -0.6, -0.4, -0.2, 0.2]]
    sets += [("width", "lvk_bpl2p_width", "lvk_bpl2p_width", None, 40), ("mean", "baseline_plp_mean", "baseline_plp_mean", None, 40)]
    summary = {}
    for tag, gen_model, post_model, rho, n_mocks in sets:
        if only and tag not in only.split(","):
            continue
        # independent random stream per set (sets may be generated by parallel processes)
        # (v3c reuses the v3b seeds: same true events and noise draws, only the PE weights differ)
        rng = np.random.default_rng(cfg.seed_for(f"mocks_v3_{tag}") if tag != "rho+0.00" else cfg.seed_for("mocks_v3"))
        spec, _, fixed, _ = build_model(gen_model, cfg)
        pars, sel = draws(post_model, n_mocks)
        path = outdir / f"mocks_full_{tag}.h5"
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
                idx = rng.choice(len(w), size=n_events, replace=True, p=w)
                tr = [inj[c][idx] for c in COLS]
                y_true = to_y(*tr)
                samples = np.zeros((n_events, N_KERNEL, 4))
                lnpr = np.zeros((n_events, N_KERNEL))
                y_obs = np.zeros((n_events, 4))
                kern = np.zeros(n_events, int)
                for e in range(n_events):
                    samples[e], lnpr[e], y_obs[e], kern[e] = bank.mock_event(y_true[e], rng)
                m1, q, chi, z = (samples[..., k] for k in range(4))
                g = f.create_group(f"mock_{i:04d}")
                for c, arr in zip(COLS, (m1, q, chi, z)):
                    g.create_dataset(c, data=arr)
                g.create_dataset("ln_prior", data=lnpr)
                g.create_dataset("true", data=np.stack(tr, axis=-1))
                g.create_dataset("observed_y", data=y_obs)
                g.create_dataset("kernel_event", data=kern)
                g.create_dataset("injection_index", data=idx)
                g.attrs["posterior_draw_index"] = int(sel[i])
                g.attrs["params"] = json.dumps({k: float(v) for k, v in p.items()})
        path.with_suffix(".h5.part").rename(path)
        summary[tag] = dict(n=n_mocks, generating_model=gen_model, rho=rho, pe_resample_ess_median=float(np.median(bank.ess[-n_mocks * n_events:])),
                            pe_resample_ess_p5=float(np.quantile(bank.ess[-n_mocks * n_events:], 0.05)))
        print(f"{tag:<9} {n_mocks:3d} mocks -> {path.name}; PE-resampling ESS median {summary[tag]['pe_resample_ess_median']:.0f} "
              f"(5th pct {summary[tag]['pe_resample_ess_p5']:.0f})", flush=True)
    json.dump(dict(summary=summary, k_nearest=K_NEAREST, measurement_space="ln Mc_det, eta, chi_eff, ln d_L",
                   median_sd=np.median(sd, 0).tolist()), open(outdir / f"mock_generation_v3_{(only or 'all').replace(',', '_')}.json", "w"), indent=2)


if __name__ == "__main__":
    main()
