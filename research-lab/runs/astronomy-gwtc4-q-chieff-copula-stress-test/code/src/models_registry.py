"""Model set (plan.md sec 4), hyper-prior transforms and parameter packing.

Each model is a composition of components understood by jaxmodels.log_population.
`fixed` pins parameters (E3 mean/width/null variants) -- the model then has fewer
free dimensions but the same likelihood code.

Primary preregistered E1 comparison: copula_gauss_plp vs copula_indep_plp.
"""
from __future__ import annotations

import numpy as np
from scipy.special import ndtri as np_ndtri

BASE_PLP = dict(mass="plp", pairing="powerlaw", spin="truncnorm", copula=None)
COPULA_PLP = dict(mass="plp", pairing="spline", spin="spline", copula=None)
# LVK GWTC-4.0 default configuration (arXiv:2508.18083 App. B.3, B.7; Tables 6, 10): Broken Power Law + 2 Peaks
# primary mass with m_high pinned at 300 Msun, power-law pairing with its own m2 taper (m2,low, delta_m2), and the
# Linear (q, chi_eff) model with the paper's log-uniform width intercept. Added 2026-09-11 (deviations D15) to test
# whether the gate values P(delta mu < 0) = 0.82 / P(delta ln sigma < 0) = 0.95 are reproduced with the LVK mass model.
LVK_BPL2P = dict(mass="bpl2p", pairing="powerlaw", spin="truncnorm", copula=None, m2_taper="separate", lvk_priors=True)
NULL_SPIN = {"mu_chi_eff_1": 0.0, "sigma_chi_eff_1": 0.0}

MODEL_SPECS = {
    # LVK-style baseline + E3 mean/width decomposition
    "baseline_plp_both":  dict(**BASE_PLP, fixed={}),
    "baseline_plp_mean":  dict(**BASE_PLP, fixed={"sigma_chi_eff_1": 0.0}),
    "baseline_plp_width": dict(**BASE_PLP, fixed={"mu_chi_eff_1": 0.0}),
    "baseline_plp_null":  dict(**BASE_PLP, fixed=dict(NULL_SPIN)),
    # E1: copula with flexible marginals (identical marginal parameterization)
    "copula_gauss_plp":   dict(**{**COPULA_PLP, "copula": "gaussian"}, fixed={}),
    "copula_indep_plp":   dict(**COPULA_PLP, fixed={}),
    "copula_frank_plp":   dict(**{**COPULA_PLP, "copula": "frank"}, fixed={}),
    # E4: generalized pairing function with the baseline spin sector
    "baseline_bpq_both":  dict(**{**BASE_PLP, "pairing": "broken"}, fixed={}),
    "baseline_bpq_null":  dict(**{**BASE_PLP, "pairing": "broken"}, fixed=dict(NULL_SPIN)),
    # E4: spline primary-mass model crossed with both spin sectors
    "baseline_splm1_both": dict(**{**BASE_PLP, "mass": "spline"}, fixed={}),
    "baseline_splm1_null": dict(**{**BASE_PLP, "mass": "spline"}, fixed=dict(NULL_SPIN)),
    "copula_gauss_splm1": dict(**{**COPULA_PLP, "mass": "spline", "copula": "gaussian"}, fixed={}),
    "copula_indep_splm1": dict(**{**COPULA_PLP, "mass": "spline"}, fixed={}),
    # LVK mass model (D15): the E3 mean/width decomposition under the paper's own Broken Power Law + 2 Peaks
    "lvk_bpl2p_both":  dict(**LVK_BPL2P, fixed={}),
    "lvk_bpl2p_mean":  dict(**LVK_BPL2P, fixed={"sigma_chi_eff_1": 0.0}),
    "lvk_bpl2p_width": dict(**LVK_BPL2P, fixed={"mu_chi_eff_1": 0.0}),
    "lvk_bpl2p_null":  dict(**LVK_BPL2P, fixed=dict(NULL_SPIN)),
    # D17 ablations: which ingredient of the LVK configuration removes the chi_eff-mean shift? Each variant changes
    # ONE ingredient relative to baseline_plp_both (PLP masses, shared taper, uniform sigma_0) or lvk_bpl2p_both.
    "abl_plp_m2taper_both":     dict(**{**BASE_PLP, "m2_taper": "separate"}, fixed={}),          # PLP + separate m2 taper
    "abl_plp_lvkspin_both":     dict(**{**BASE_PLP, "lvk_priors": True}, fixed={}),               # PLP + log-uniform sigma_0
    "abl_bpl2p_sharedtaper_both": dict(**{**LVK_BPL2P, "m2_taper": "shared"}, fixed={}),          # LVK masses, shared taper
    "abl_bpl2p_plpspin_both":   dict(**{**LVK_BPL2P, "lvk_priors": False}, fixed={}),             # LVK masses, uniform sigma_0
}

# (model, reference) pairs whose ln Z differences are the preregistered endpoints
BF_COMPARISONS = [
    ("E1", "copula_gauss_plp", "copula_indep_plp", "Gaussian copula dependence vs independence (PLP m1)"),
    ("E1b", "copula_frank_plp", "copula_indep_plp", "Frank copula dependence vs independence (PLP m1)"),
    ("E1c", "copula_gauss_splm1", "copula_indep_splm1", "Gaussian copula dependence vs independence (spline m1)"),
    ("E3a", "baseline_plp_mean", "baseline_plp_null", "chi_eff mean slope only vs null"),
    ("E3b", "baseline_plp_width", "baseline_plp_null", "chi_eff width slope only vs null"),
    ("E3c", "baseline_plp_both", "baseline_plp_null", "mean + width slopes vs null"),
    ("E4a", "baseline_bpq_both", "baseline_bpq_null", "mean + width slopes vs null (broken pairing)"),
    ("E4b", "baseline_splm1_both", "baseline_splm1_null", "mean + width slopes vs null (spline m1)"),
    ("E4c", "baseline_bpq_both", "baseline_plp_both", "broken pairing vs power-law pairing"),
    ("E4d", "baseline_splm1_both", "baseline_plp_both", "spline m1 vs PowerLaw+Peak m1"),
    ("E3a-LVK", "lvk_bpl2p_mean", "lvk_bpl2p_null", "chi_eff mean slope only vs null (LVK BPL+2P masses)"),
    ("E3b-LVK", "lvk_bpl2p_width", "lvk_bpl2p_null", "chi_eff width slope only vs null (LVK BPL+2P masses)"),
    ("E3c-LVK", "lvk_bpl2p_both", "lvk_bpl2p_null", "mean + width slopes vs null (LVK BPL+2P masses)"),
]


def component_params(spec: dict, n_mass_nodes: int, n_marg_nodes: int) -> list[str]:
    names = []
    if spec["mass"] == "plp":
        names += ["alpha", "mmin", "mmax", "lam", "mpp", "sigpp", "delta_m"]
    elif spec["mass"] == "spline":
        names += ["mmin", "delta_m"] + [f"fm1_{k}" for k in range(n_mass_nodes)]
    elif spec["mass"] == "bpl2p":
        # mmin_u -> m1,low (triangular prior, eq. B17); dir_u0/dir_u1 -> Dirichlet(1,1,1) mixing fractions
        names += ["alpha_1", "alpha_2", "m_break", "mmin_u", "delta_m", "mu_1", "sigma_1", "mu_2", "sigma_2",
                  "dir_u0", "dir_u1"]
    if spec.get("m2_taper") == "separate":
        names += ["mmin2_u", "delta_m2"]          # m2,low ~ U(3, m1,low), delta_m2 ~ U(0, 10)
    if spec["pairing"] == "powerlaw":
        names += ["beta"]
    elif spec["pairing"] == "broken":
        names += ["beta", "pairing_q_break", "pairing_dbeta"]
    elif spec["pairing"] == "spline":
        names += [f"fq_{k}" for k in range(n_marg_nodes)]
    if spec["spin"] == "truncnorm" and spec.get("lvk_priors"):
        names += ["mu_chi_eff_0", "mu_chi_eff_1", "ln_sigma_chi_eff_0", "sigma_chi_eff_1"]   # Table 10 priors
    elif spec["spin"] == "truncnorm":
        names += ["mu_chi_eff_0", "mu_chi_eff_1", "sigma_chi_eff_0", "sigma_chi_eff_1"]
    elif spec["spin"] == "spline":
        names += [f"fchi_{k}" for k in range(n_marg_nodes)]
    if spec.get("copula") == "gaussian":
        names += ["gaussian_copula_rho"]
    elif spec.get("copula") == "frank":
        names += ["frank_copula_theta"]
    names += ["lamb"]
    return [n for n in names if n not in spec.get("fixed", {})]


def is_spline_param(name: str) -> bool:
    return name.startswith(("fm1_", "fq_", "fchi_"))


class PriorTransform:
    """Unit hypercube -> hyperparameters. Uniform bounds from config.priors;
    spline node log-densities follow a Gaussian random walk
    (f_0 ~ N(0, s_first^2), f_k - f_{k-1} ~ N(0, s_step^2)) whose Jacobian is
    unity, so it is a valid prior transform. Works with numpy or jax.numpy
    (`xp`) so the same object serves nautilus and numpyro."""

    def __init__(self, names: list[str], cfg):
        self.names = list(names)
        self.n_dim = len(self.names)
        pri = cfg.raw["priors"]
        self.s_first, self.s_step = float(pri["spline_first_sigma"]), float(pri["spline_step_sigma"])
        self.lo, self.hi, self.kind = [], [], []
        for n in self.names:
            if is_spline_param(n):
                self.lo.append(0.0)
                self.hi.append(1.0)
                self.kind.append("spline")
            else:
                lo, hi = cfg.prior_bounds(n)
                self.lo.append(lo)
                self.hi.append(hi)
                self.kind.append("uniform")
        self.lo, self.hi = np.array(self.lo), np.array(self.hi)
        self.uniform_mask = np.array([k == "uniform" for k in self.kind])
        # spline groups: consecutive indices sharing a prefix
        self.groups = {}
        for i, n in enumerate(self.names):
            if is_spline_param(n):
                self.groups.setdefault(n.split("_")[0], []).append(i)

    def __call__(self, u, xp=np, ndtri=np_ndtri):
        u = xp.asarray(u)
        eps = 1e-10
        theta = self.lo + u * (self.hi - self.lo)
        if not self.groups:
            return theta
        theta = list(theta) if xp is np else [theta[i] for i in range(self.n_dim)]
        for idxs in self.groups.values():
            prev = None
            for j, i in enumerate(idxs):
                gauss = ndtri(xp.clip(u[i], eps, 1 - eps))
                val = self.s_first * gauss if j == 0 else prev + self.s_step * gauss
                theta[i] = val
                prev = val
        return xp.stack(theta) if xp is not np else np.array(theta, dtype=float)

    def log_prior_density(self, theta):
        """ln pi(theta) (up to the uniform-box constant) -- needed for SDDR."""
        theta = np.asarray(theta, float)
        lp = 0.0
        inside = np.all((theta[self.uniform_mask] >= self.lo[self.uniform_mask])
                        & (theta[self.uniform_mask] <= self.hi[self.uniform_mask]))
        if not inside:
            return -np.inf
        for idxs in self.groups.values():
            vals = theta[idxs]
            lp += -0.5 * (vals[0] / self.s_first) ** 2
            lp += -0.5 * np.sum((np.diff(vals) / self.s_step) ** 2)
        return float(lp)

    def sample(self, rng: np.random.Generator, n: int) -> np.ndarray:
        return np.array([self(rng.uniform(size=self.n_dim)) for _ in range(n)])

    def uniform_density(self, name: str) -> float:
        i = self.names.index(name)
        return 1.0 / (self.hi[i] - self.lo[i])


def build_model(name: str, cfg):
    """Returns (spec, names, fixed, prior_transform) for a registered model."""
    spec = dict(MODEL_SPECS[name])
    spec["sigma_floor"] = float(cfg.raw["priors"]["sigma_chi_eff_floor"])
    n_mass, n_marg = int(cfg.mode_value("mass_spline_nodes")), int(cfg.mode_value("marginal_spline_nodes"))
    names = component_params(spec, n_mass, n_marg)
    return spec, names, dict(spec.get("fixed", {})), PriorTransform(names, cfg)
