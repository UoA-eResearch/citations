"""Analytic PE sampling priors in the population parameterization
(mass_1 [source], mass_ratio, redshift, chi_eff), plus the cosmology helpers
shared with the population models, plus the chi_eff-given-q densities induced
by the component-spin distributions used in PE priors and injection draws.

PE prior (bilby_pipe defaults used for GWTC-2.1/3/4 releases):
    * detector-frame component masses uniform (UniformInComponentsChirpMass x
      UniformInComponentsMassRatio) ->  pi(m1_src, q | z) propto m1_src (1+z)^2
    * luminosity distance: UniformSourceFrame  -> pi(z) propto dVc/dz / (1+z)
      (`_mixed_cosmo` GWTC-2.1/3 releases are reweighted to the same form);
      `PowerLaw(alpha=2)` in d_L (nocosmo files) -> pi(z) propto d_L^2 dd_L/dz
    * spins: magnitudes uniform on [0, a_max], isotropic tilts
      -> pi(chi_eff | q) = h(chi_eff; q), tabulated by Monte Carlo.
Overall normalisation constants are irrelevant (they cancel in every Bayes
factor and only shift ln Z by a model-independent constant).

Spin families (component spins i.i.d.; cartesian density g(s) = p(a) p(cos t) / (2 pi a^2)):
    isotropic_uniform  a ~ U(0, a_max), cos t ~ U(-1, 1)       (PE priors; O3 injections)
    essick2025         a ~ TruncNormal(0, 0.5) on [0, 1],
                       cos t ~ 0.3 * (1 + cos t)^3 / 4 + 0.7 * U(-1, 1)
                       (O4a and semi-analytic O1/O2 injections, Essick 2025,
                       arXiv:2508.10638 sec. II; verified empirically on the
                       Zenodo file in selection.py)
The same h(chi_eff; q) tabulation converts the injection draw density from
cartesian spin components to chi_eff (see selection.py).
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import numpy as np
from astropy import units as u
from astropy.cosmology import Planck15
from scipy.interpolate import RegularGridInterpolator
from scipy.special import erf

logger = logging.getLogger("q_chieff_copula")

_Z_GRID = np.linspace(1e-4, 6.0, 3000)
_DL_GRID = Planck15.luminosity_distance(_Z_GRID).to(u.Mpc).value
_DVC_DZ_GRID = 4 * np.pi * Planck15.differential_comoving_volume(_Z_GRID).to(u.Mpc**3 / u.sr).value

SPIN_FAMILIES = ("isotropic_uniform", "essick2025")
ESSICK_SIGMA = 0.5
ESSICK_ALIGNED_FRACTION = 0.3
_ESSICK_ZA = np.sqrt(np.pi / 2) * ESSICK_SIGMA * erf(1.0 / (np.sqrt(2) * ESSICK_SIGMA))   # int_0^1 exp(-a^2/2s^2) da


def dvc_dz(z):
    """Total (4 pi sr) differential comoving volume dVc/dz in Mpc^3 (Planck15)."""
    return np.interp(z, _Z_GRID, _DVC_DZ_GRID)


def redshift_from_dl(dl_mpc):
    return np.interp(dl_mpc, _DL_GRID, _Z_GRID)


def ddl_dz(z):
    return np.interp(z, _Z_GRID, np.gradient(_DL_GRID, _Z_GRID))


def ln_redshift_prior(z, kind: str):
    kind = kind.lower()
    if kind in ("uniform_comoving_source_frame", "uniformsourceframe"):
        return np.log(dvc_dz(z)) - np.log1p(z)
    if kind in ("uniform_comoving_volume", "uniformcomovingvolume"):
        return np.log(dvc_dz(z))
    if kind in ("dl_squared", "powerlaw_dl2", "euclidean"):
        dl = np.interp(z, _Z_GRID, _DL_GRID)
        return 2 * np.log(dl) + np.log(ddl_dz(z))
    raise ValueError(f"unknown redshift prior kind {kind!r}")


def classify_distance_prior_string(s: str) -> str:
    s = s if isinstance(s, str) else s.decode()
    if "UniformSourceFrame" in s:
        return "uniform_comoving_source_frame"
    if "UniformComovingVolume" in s:
        return "uniform_comoving_volume"
    if "PowerLaw" in s and "alpha=2" in s.replace(" ", ""):
        return "dl_squared"
    raise ValueError(f"unrecognised luminosity_distance prior: {s[:120]}")


def parse_spin_amax(s: str | bytes, default: float) -> float:
    s = s if isinstance(s, str) else s.decode()
    m = re.search(r"maximum=([0-9.]+)", s)
    return float(m.group(1)) if m else default


def ln_mass_prior(m1_source, z):
    """pi(m1_src, q | z) propto m1_src (1+z)^2 (uniform in detector-frame components)."""
    return np.log(m1_source) + 2 * np.log1p(z)


# --------------------------------------------------------------------------------------
# component-spin families
# --------------------------------------------------------------------------------------

def sample_spin_family(family: str, amax: float, n: int, rng: np.random.Generator):
    """Draw (a, cos_t) for one component from the family."""
    if family == "isotropic_uniform":
        return rng.uniform(0, amax, n), rng.uniform(-1, 1, n)
    if family == "essick2025":
        # truncated normal on [0, 1] via inverse CDF
        u = rng.uniform(size=n)
        a = np.sqrt(2) * ESSICK_SIGMA * _erfinv(u * erf(1.0 / (np.sqrt(2) * ESSICK_SIGMA)))
        aligned = rng.uniform(size=n) < ESSICK_ALIGNED_FRACTION
        c = np.where(aligned, 2 * rng.uniform(size=n) ** 0.25 - 1, rng.uniform(-1, 1, n))
        return np.clip(a, 0, 1), c
    raise ValueError(family)


def _erfinv(y):
    from scipy.special import erfinv
    return erfinv(y)


def ln_spin_vector_density(family: str, a, cos_t, amax: float = 1.0):
    """ln g(s) of one cartesian spin vector under the family (a = |s|)."""
    a = np.clip(np.asarray(a, float), 1e-9, None)
    if family == "isotropic_uniform":
        return -np.log(4 * np.pi) - 2 * np.log(a) - np.log(amax)
    if family == "essick2025":
        lpa = -a**2 / (2 * ESSICK_SIGMA**2) - np.log(_ESSICK_ZA)
        lpc = np.log(ESSICK_ALIGNED_FRACTION * (1 + np.asarray(cos_t, float)) ** 3 / 4
                     + (1 - ESSICK_ALIGNED_FRACTION) / 2)
        return lpa + lpc - np.log(2 * np.pi) - 2 * np.log(a)
    raise ValueError(family)


class ChiEffPriorTable:
    """h(chi_eff | q): the chi_eff density induced by i.i.d. component spins
    from a spin family, tabulated by Monte Carlo on a (q, chi_eff) grid and
    cached on disk keyed by (family, a_max)."""

    def __init__(self, amax: float, cache_dir: Path, family: str = "isotropic_uniform", n_mc: int = 2_000_000,
                 n_q: int = 80, n_chi: int = 401, seed: int = 0):
        assert family in SPIN_FAMILIES, family
        self.family, self.amax = family, float(amax)
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        tag = f"{family}_amax{self.amax:.4f}" if family == "isotropic_uniform" else family
        self.cache = cache_dir / f"chieff_prior_{tag}_nq{n_q}_nchi{n_chi}.npz"
        if self.cache.exists():
            d = np.load(self.cache)
            self.qs, self.chis, self.table = d["qs"], d["chis"], d["table"]
        else:
            self.qs, self.chis, self.table = self._build(n_mc, n_q, n_chi, seed)
            np.savez(self.cache, qs=self.qs, chis=self.chis, table=self.table)
            logger.info("tabulated chi_eff density for spin family %s (a_max=%.4f) -> %s", family, self.amax, self.cache)
        self._interp = RegularGridInterpolator((self.qs, self.chis), np.log(self.table),
                                               bounds_error=False, fill_value=None)

    def _build(self, n_mc, n_q, n_chi, seed):
        rng = np.random.default_rng(seed)
        qs = np.linspace(0.02, 1.0, n_q)
        edges = np.linspace(-1, 1, n_chi + 1)
        chis = 0.5 * (edges[1:] + edges[:-1])
        table = np.zeros((n_q, n_chi))
        a1, c1 = sample_spin_family(self.family, self.amax, n_mc, rng)
        a2, c2 = sample_spin_family(self.family, self.amax, n_mc, rng)
        for i, q in enumerate(qs):
            chi = (a1 * c1 + q * a2 * c2) / (1 + q)
            h, _ = np.histogram(chi, bins=edges, density=True)
            table[i] = h
        # avoid log(0) at |chi| beyond the physical support (tiny floor)
        table = np.clip(table, 1e-6 * table.max(), None)
        return qs, chis, table

    def ln_prob(self, chi_eff, q):
        q = np.clip(np.asarray(q, float), self.qs[0], self.qs[-1])
        chi = np.clip(np.asarray(chi_eff, float), self.chis[0], self.chis[-1])
        return self._interp(np.stack([q, chi], axis=-1))


def ln_pe_prior(m1_source, q, z, chi_eff, redshift_prior_kind: str, chieff_table: ChiEffPriorTable):
    return (ln_mass_prior(m1_source, z) + ln_redshift_prior(z, redshift_prior_kind)
            + chieff_table.ln_prob(chi_eff, q))
