"""JAX population models and the hierarchical (selection-corrected) likelihood.

Population density over (mass_1 [source], mass_ratio, chi_eff, redshift):

    p(theta | Lambda) = p(m1) p(q | m1) p(chi_eff | q) c(F(q|m1), F(chi_eff)) p(z)

Components (selected per model in models_registry.MODEL_SPECS):
    mass   'plp'      PowerLaw+Peak with low-mass smoothing (T&T18; identical
                      conventions to gwpopulation.models.mass.SinglePeakSmoothed
                      MassDistribution, checked numerically in test_models.py)
           'spline'   natural-cubic-spline log density in log m1 (E4 variant)
    pairing 'powerlaw' q^beta S(q m1) on [mmin/m1, 1]  (LVK default pairing)
           'broken'   broken power law in q with break q_b (E4 generalised pairing)
           'spline'   free log-density spline in q (copula "flexible q marginal")
    spin   'truncnorm' chi_eff ~ TN(mu(q), sigma(q); -1, 1), mu and ln sigma
                      linear in (q - 1) (the LVK GWTC-4.0 "Linear" (q, chi_eff)
                      model, arXiv:2508.18083 App. B.7; E3 variants fix the
                      slopes to zero)
           'spline'   free log-density spline in chi_eff (copula flexible marginal)
    copula  None | 'gaussian' | 'frank'   on (F(q|m1), F(chi_eff))
    redshift  PowerLawRedshift: p(z) propto dVc/dz (1+z)^(lamb-1)

Everything is written in log space and vectorized so that a batch of
hyperparameter vectors can be evaluated with jax.vmap on CPU or GPU. The
likelihood functions take the data (event posterior arrays, injection arrays)
as explicit arguments, so one compiled function serves every catalog with the
same array shapes (real data, mock catalogs) without recompilation.
"""
from __future__ import annotations

import numpy as np
from scipy.interpolate import CubicSpline

import jax
import jax.numpy as jnp
from jax.scipy.ndimage import map_coordinates
from jax.scipy.special import logsumexp, ndtr, ndtri

from pe_priors import dvc_dz

jax.config.update("jax_enable_x64", True)

NEG = -1e300          # "log zero" that stays finite in sums
LOG_2PI = float(np.log(2 * np.pi))
DATA_KEYS = ("mass_1", "mass_ratio", "chi_eff", "redshift", "ln_prior")


def natural_cubic_basis(nodes, xs):
    """S with S @ f = natural cubic spline through (nodes, f) evaluated at xs."""
    nodes = np.asarray(nodes, float)
    xs = np.clip(np.asarray(xs, float), nodes[0], nodes[-1])
    S = np.zeros((len(xs), len(nodes)))
    for k in range(len(nodes)):
        e = np.zeros(len(nodes))
        e[k] = 1.0
        S[:, k] = CubicSpline(nodes, e, bc_type="natural")(xs)
    return S


def trapz(y, x, axis=0):
    dx = jnp.diff(x)
    if axis == 0:
        return jnp.sum(0.5 * dx.reshape((-1,) + (1,) * (y.ndim - 1)) * (y[1:] + y[:-1]), axis=0)
    return jnp.sum(0.5 * dx * (y[..., 1:] + y[..., :-1]), axis=-1)


def cumtrapz0(y, x):
    """Cumulative trapezoid along axis 0 with a leading zero."""
    dx = jnp.diff(x).reshape((-1,) + (1,) * (y.ndim - 1))
    inc = 0.5 * dx * (y[1:] + y[:-1])
    return jnp.concatenate([jnp.zeros_like(y[:1]), jnp.cumsum(inc, axis=0)], axis=0)


class Grids:
    """Fixed evaluation grids and spline bases (numpy at construction, jnp for use)."""

    def __init__(self, cfg, n_mass_nodes: int, n_marginal_nodes: int):
        g = cfg.grids
        self.m1s = np.linspace(float(g["m1_min"]), float(g["m1_max"]), int(g["n_m1"]))
        self.qs = np.linspace(float(g["q_min"]), 1.0, int(g["n_q"]))
        self.chis = np.linspace(-1.0, 1.0, int(g["n_chi"]))
        self.zs = np.linspace(1e-6, float(g["z_max"]), int(g["n_z"]))
        self.z_max = float(g["z_max"])
        self.m1_max = float(g["m1_max"])
        self.dvc = dvc_dz(self.zs)
        self.n_mass_nodes, self.n_marginal_nodes = int(n_mass_nodes), int(n_marginal_nodes)
        self.m1_nodes = np.linspace(np.log(self.m1s[0]), np.log(self.m1s[-1]), self.n_mass_nodes)
        qlo, qhi = g["q_node_range"]
        self.q_nodes = np.linspace(float(qlo), float(qhi), self.n_marginal_nodes)
        clo, chi = g["chi_node_range"]
        self.chi_nodes = np.linspace(float(clo), float(chi), self.n_marginal_nodes)
        self.S_m1 = natural_cubic_basis(self.m1_nodes, np.log(self.m1s))
        self.S_q = natural_cubic_basis(self.q_nodes, self.qs)
        self.S_chi = natural_cubic_basis(self.chi_nodes, self.chis)
        self.j = {k: jnp.asarray(v) for k, v in dict(
            m1s=self.m1s, qs=self.qs, chis=self.chis, zs=self.zs, dvc=self.dvc,
            S_m1=self.S_m1, S_q=self.S_q, S_chi=self.S_chi).items()}
        self.dq = float(self.qs[1] - self.qs[0])
        self.dm = float(self.m1s[1] - self.m1s[0])


# --------------------------------------------------------------------------------------
# elementary log densities
# --------------------------------------------------------------------------------------

def log_smoothing(m, mmin, delta_m):
    """log of the gwpopulation Planck-taper low-mass window (step for delta_m=0)."""
    shifted = jnp.clip((m - mmin) / jnp.maximum(delta_m, 1e-12), 1e-6, 1 - 1e-6)
    exponent = 1.0 / shifted - 1.0 / (1.0 - shifted)
    logw = -jnp.logaddexp(0.0, exponent)
    logw = jnp.where(delta_m > 0, logw, 0.0)
    return jnp.where(m >= mmin, logw, NEG)


def log_powerlaw(x, alpha, low, high):
    """log of the normalized power law x^alpha on [low, high] (alpha != -1 handled smoothly)."""
    a1 = 1.0 + alpha
    safe_a1 = jnp.where(jnp.abs(a1) < 1e-8, 1.0, a1)
    log_norm = jnp.where(jnp.abs(a1) < 1e-8, -jnp.log(jnp.log(high / low)),
                         jnp.log(jnp.abs(safe_a1)) - jnp.log(jnp.abs(high**safe_a1 - low**safe_a1)))
    inside = (x >= low) & (x <= high)
    return jnp.where(inside, alpha * jnp.log(jnp.maximum(x, 1e-300)) + log_norm, NEG)


def log_truncnorm(x, mu, sigma, low, high):
    z = (x - mu) / sigma
    norm = ndtr((high - mu) / sigma) - ndtr((low - mu) / sigma)
    lp = -0.5 * z**2 - jnp.log(sigma) - 0.5 * LOG_2PI - jnp.log(jnp.maximum(norm, 1e-300))
    return jnp.where((x >= low) & (x <= high), lp, NEG)


def log_two_component(m, alpha, mmin, mmax, lam, mpp, sigpp, gaussian_mass_maximum=100.0):
    lp_pl = log_powerlaw(m, -alpha, mmin, mmax)
    lp_tn = log_truncnorm(m, mpp, sigpp, mmin, gaussian_mass_maximum)
    return jnp.logaddexp(jnp.log(jnp.maximum(1 - lam, 1e-300)) + lp_pl, jnp.log(jnp.maximum(lam, 1e-300)) + lp_tn)


def log_broken_powerlaw(m, alpha_1, alpha_2, m_break, low, high):
    """log of the LVK GWTC-4.0 broken power law (arXiv:2508.18083 eqs. B12-B13), normalised on
    [low, high]: (m/m_break)^-alpha_1 below the break, (m/m_break)^-alpha_2 above (alpha -> 1 handled)."""
    lm = jnp.log(jnp.maximum(m, 1e-300) / m_break)
    shape = jnp.where(m < m_break, -alpha_1 * lm, -alpha_2 * lm)

    def piece(a, r_lo, r_hi):            # int_{r_lo}^{r_hi} x^-a dx, x in units of m_break
        one_m_a = 1.0 - a
        safe = jnp.where(jnp.abs(one_m_a) < 1e-8, 1.0, one_m_a)
        val = (r_hi**safe - r_lo**safe) / safe
        return jnp.where(jnp.abs(one_m_a) < 1e-8, jnp.log(r_hi / r_lo), val)

    norm = m_break * (piece(alpha_1, low / m_break, 1.0) + piece(alpha_2, 1.0, high / m_break))
    inside = (m >= low) & (m <= high)
    return jnp.where(inside, shape - jnp.log(jnp.maximum(norm, 1e-300)), NEG)


def dirichlet3_from_unit(u0, u1):
    """(lambda_0, lambda_1) ~ Dirichlet(1, 1, 1) (uniform on the simplex) from two unit uniforms:
    lambda_0 = 1 - sqrt(1 - u0) (its Beta(1, 2) marginal), lambda_1 = (1 - lambda_0) u1."""
    u0 = jnp.clip(u0, 1e-9, 1 - 1e-9)
    u1 = jnp.clip(u1, 1e-9, 1 - 1e-9)
    lam0 = 1.0 - jnp.sqrt(1.0 - u0)
    lam1 = (1.0 - lam0) * u1
    return lam0, lam1


def resolve_derived(p: dict, spec: dict):
    """Derived hyperparameters of the LVK-prior models (arXiv:2508.18083 eq. B17, D15):
    mmin_u -> m1,low with the triangular prior on [3, 10] Msun (pi ∝ m1,low - 3);
    mmin2_u -> m2,low ~ U(3, m1,low), so m2,low <= m1,low by construction."""
    if "mmin_u" not in p and "mmin2_u" not in p:
        return p
    p = dict(p)
    if "mmin_u" in p:
        p["mmin"] = 3.0 + 7.0 * jnp.sqrt(jnp.clip(p["mmin_u"], 0.0, 1.0))
    if "mmin2_u" in p:        # m2,low ~ U(3, m1,low) whether m1,low is derived (LVK) or sampled directly (ablation)
        p["mmin2"] = 3.0 + (jnp.maximum(p["mmin"], 3.0) - 3.0) * jnp.clip(p["mmin2_u"], 0.0, 1.0)
    return p


# --------------------------------------------------------------------------------------
# model components
# --------------------------------------------------------------------------------------

def log_p_m1(m1, p, spec, G: Grids):
    if spec["mass"] == "plp":
        def unnorm(m):
            return (log_two_component(m, p["alpha"], p["mmin"], p["mmax"], p["lam"], p["mpp"], p["sigpp"],
                                      G.m1_max) + log_smoothing(m, p["mmin"], p["delta_m"]))
    elif spec["mass"] == "spline":
        f = jnp.stack([p[f"fm1_{k}"] for k in range(G.n_mass_nodes)])
        log_shape_grid = G.j["S_m1"] @ f

        def unnorm(m):
            ls = jnp.interp(jnp.log(m), jnp.log(G.j["m1s"]), log_shape_grid)
            return ls + log_smoothing(m, p["mmin"], p["delta_m"]) + jnp.where(m <= G.m1_max, 0.0, NEG)
    elif spec["mass"] == "bpl2p":
        # LVK GWTC-4.0 Broken Power Law + 2 Peaks (arXiv:2508.18083 App. B.3, eqs. B12-B15, Table 6):
        # mixture of a broken power law and two left-truncated Gaussians, m_high pinned at 300 Msun
        # (= the m1 grid maximum), Planck taper applied to the total; mixing fractions ~ Dir(1, 1, 1).
        lam0, lam1 = dirichlet3_from_unit(p["dir_u0"], p["dir_u1"])
        lam2 = jnp.maximum(1.0 - lam0 - lam1, 1e-300)
        m_high = G.m1_max

        def unnorm(m):
            lp_bp = log_broken_powerlaw(m, p["alpha_1"], p["alpha_2"], p["m_break"], p["mmin"], m_high)
            lp_n1 = log_truncnorm(m, p["mu_1"], p["sigma_1"], p["mmin"], jnp.inf)
            lp_n2 = log_truncnorm(m, p["mu_2"], p["sigma_2"], p["mmin"], jnp.inf)
            mix = jnp.logaddexp(jnp.logaddexp(jnp.log(jnp.maximum(lam0, 1e-300)) + lp_bp,
                                              jnp.log(jnp.maximum(lam1, 1e-300)) + lp_n1),
                                jnp.log(lam2) + lp_n2)
            return mix + log_smoothing(m, p["mmin"], p["delta_m"]) + jnp.where(m <= m_high, 0.0, NEG)
    else:
        raise ValueError(spec["mass"])
    log_norm = jnp.log(jnp.maximum(trapz(jnp.exp(unnorm(G.j["m1s"])), G.j["m1s"]), 1e-300))
    return unnorm(m1) - log_norm


def pairing_log_shape(q, m1, p, spec, G: Grids):
    """log of the (un-normalised) pairing shape in q. For the LVK power-law
    pairing this is gwpopulation's analytically normalised
    powerlaw(q, beta, 1, mmin/m1) (the m1-dependent constant matters because
    gwpopulation interpolates the *product* norm(m1) between grid nodes; we
    reproduce that convention exactly so the baseline matches the LVK code)."""
    kind = spec["pairing"]
    lq = jnp.log(jnp.maximum(q, 1e-300))
    if kind == "powerlaw":
        return log_powerlaw(q, p["beta"], p.get("mmin2", p["mmin"]) / m1, 1.0)
    if kind == "broken":
        qb, db, beta = p["pairing_q_break"], p["pairing_dbeta"], p["beta"]
        return jnp.where(q >= qb, beta * lq, (beta + db) * lq - db * jnp.log(qb))
    if kind == "spline":
        f = jnp.stack([p[f"fq_{k}"] for k in range(G.n_marginal_nodes)])
        return jnp.interp(q, G.j["qs"], G.j["S_q"] @ f)
    raise ValueError(kind)


def q_conditional(m1, q, p, spec, G: Grids, need_cdf: bool):
    """log p(q | m1) at the data and (optionally) the conditional CDF F(q | m1).

    The q-normalisation is tabulated on the m1 grid and interpolated *linearly*
    in m1, exactly as gwpopulation.models.mass.SinglePeakSmoothedMassDistribution
    .norm_p_q does (this matters within ~1 Msun of mmin, where the norm varies
    rapidly between grid nodes)."""
    # the m2 taper is shared with m1 (gwpopulation convention) unless the model carries its own
    # (m2,low, delta_m2), as the LVK GWTC-4.0 pairing function does (arXiv:2508.18083 eq. B16)
    mmin, delta_m = p.get("mmin2", p["mmin"]), p.get("delta_m2", p["delta_m"])

    def unnorm(qq, mm):
        return (pairing_log_shape(qq, mm, p, spec, G) + log_smoothing(qq * mm, mmin, delta_m)
                + jnp.where(qq >= mmin / mm, 0.0, NEG))

    Q, M = G.j["qs"][:, None], G.j["m1s"][None, :]
    pdf_grid = jnp.exp(unnorm(Q, M))                       # (n_q, n_m1)
    # floor at 1e-150 (not 1e-300): the CDF below divides by norms, and the
    # derivative -c/norms^2 must not underflow to 0/0 = nan for m1 < mmin columns
    norms = jnp.maximum(trapz(pdf_grid, G.j["qs"], axis=0), 1e-150)
    log_norm_at = jnp.log(jnp.maximum(jnp.interp(m1, G.j["m1s"], norms), 1e-150))
    log_pq = unnorm(q, m1) - log_norm_at
    if not need_cdf:
        return log_pq, None
    cdf_grid = cumtrapz0(pdf_grid, G.j["qs"]) / norms[None, :]
    iq = (q - G.j["qs"][0]) / G.dq
    im = (m1 - G.j["m1s"][0]) / G.dm
    u = map_coordinates(cdf_grid, [iq, im], order=1, mode="nearest")
    return log_pq, jnp.clip(u, 1e-6, 1 - 1e-6)


def chi_sector(q, chi, p, spec, G: Grids, need_cdf: bool):
    if spec["spin"] == "truncnorm":
        # LVK GWTC-4.0 "Linear" (q, chi_eff) model (arXiv:2508.18083 App. B.7, eqs. B42-B43): the mean and
        # the natural-log width of the truncated Gaussian are linear in (q - 1);
        # mu_chi_eff_1 == delta mu_eff|q and sigma_chi_eff_1 == delta ln sigma_eff|q of the paper.
        mu = p["mu_chi_eff_0"] + p["mu_chi_eff_1"] * (q - 1.0)
        sigma_0 = jnp.exp(p["ln_sigma_chi_eff_0"]) if "ln_sigma_chi_eff_0" in p else p["sigma_chi_eff_0"]
        sigma = sigma_0 * jnp.exp(p["sigma_chi_eff_1"] * (q - 1.0))
        lp = log_truncnorm(chi, mu, sigma, -1.0, 1.0)
        if not need_cdf:
            return lp, None
        # D24: CDF of the truncated normal, for copulas on the LVK parametric marginals (slopes fixed to 0 there,
        # so v = F(chi_eff) is the marginal CDF)
        lo, hi = ndtr((-1.0 - mu) / sigma), ndtr((1.0 - mu) / sigma)
        v = (ndtr((chi - mu) / sigma) - lo) / jnp.maximum(hi - lo, 1e-300)
        return lp, jnp.clip(v, 1e-6, 1 - 1e-6)
    if spec["spin"] == "spline":
        f = jnp.stack([p[f"fchi_{k}"] for k in range(G.n_marginal_nodes)])
        log_grid = G.j["S_chi"] @ f
        pdf_grid = jnp.exp(log_grid)
        norm = jnp.maximum(trapz(pdf_grid, G.j["chis"]), 1e-300)
        lp = jnp.interp(chi, G.j["chis"], log_grid) - jnp.log(norm)
        lp = jnp.where(jnp.abs(chi) <= 1.0, lp, NEG)
        if not need_cdf:
            return lp, None
        cdf_grid = cumtrapz0(pdf_grid, G.j["chis"]) / norm
        v = jnp.interp(chi, G.j["chis"], cdf_grid)
        return lp, jnp.clip(v, 1e-6, 1 - 1e-6)
    raise ValueError(spec["spin"])


def log_copula(u, v, p, spec, m1=None):
    fam = spec.get("copula")
    if fam is None:
        return jnp.zeros_like(u)
    if fam in ("gaussian", "gaussian_mbin"):
        if fam == "gaussian":
            rho = jnp.clip(p["gaussian_copula_rho"], -0.995, 0.995)
        else:   # D22: piecewise-constant rho in primary-mass bins (edges spec["m_edges"]); normalised for every m1
            rho = p["rho_b0"] * jnp.ones_like(u)
            for k, edge in enumerate(spec["m_edges"]):
                rho = jnp.where(m1 >= edge, p[f"rho_b{k + 1}"], rho)
            rho = jnp.clip(rho, -0.995, 0.995)
        x, y = ndtri(u), ndtri(v)
        return -0.5 * jnp.log(1 - rho**2) - (rho**2 * (x**2 + y**2) - 2 * rho * x * y) / (2 * (1 - rho**2))
    if fam == "frank":
        th = p["frank_copula_theta"]
        th = jnp.where(jnp.abs(th) < 1e-4, jnp.where(th < 0, -1e-4, 1e-4), th)
        one_m = -jnp.expm1(-th)                       # 1 - e^{-theta}
        num = jnp.log(jnp.abs(th)) + jnp.log(jnp.abs(one_m)) - th * (u + v)
        den = one_m - jnp.expm1(-th * u) * jnp.expm1(-th * v)
        return num - 2 * jnp.log(jnp.maximum(jnp.abs(den), 1e-300))
    raise ValueError(fam)


def log_p_z(z, p, G: Grids):
    lamb = p["lamb"]
    norm = trapz((1 + G.j["zs"]) ** (lamb - 1.0) * G.j["dvc"], G.j["zs"])
    lp = (lamb - 1.0) * jnp.log1p(z) + jnp.log(jnp.interp(z, G.j["zs"], G.j["dvc"])) - jnp.log(norm)
    return jnp.where((z > 0) & (z <= G.z_max), lp, NEG)


def log_population(d: dict, p: dict, spec: dict, G: Grids):
    """log p(m1, q, chi_eff, z | Lambda) for arrays in d (any common shape)."""
    m1, q, chi, z = d["mass_1"], d["mass_ratio"], d["chi_eff"], d["redshift"]
    need_cdf = spec.get("copula") is not None
    lp = log_p_m1(m1, p, spec, G)
    lq, u = q_conditional(m1, q, p, spec, G, need_cdf)
    lc, v = chi_sector(q, chi, p, spec, G, need_cdf)
    lp = lp + lq + lc + log_p_z(z, p, G)
    if need_cdf:
        lp = lp + log_copula(u, v, p, spec, m1=m1)
    return lp


def constraints_ok(p: dict, spec: dict):
    # (the log-linear chi_eff width is positive by construction: no spin-sector constraint)
    return p["mmin"] < p.get("mmax", 1e9)


# --------------------------------------------------------------------------------------
# hierarchical likelihood
# --------------------------------------------------------------------------------------

def as_event_arrays(events: dict) -> dict:
    """(N, K) float64 jnp arrays for the five DATA_KEYS."""
    return {k: jnp.asarray(np.asarray(events[k], dtype=np.float64)) for k in DATA_KEYS}


def as_injection_arrays(injections: dict) -> dict:
    """(M,) float64 jnp arrays for DATA_KEYS plus the 0-d 'total_generated'."""
    out = {k: jnp.asarray(np.asarray(injections[k], dtype=np.float64)) for k in DATA_KEYS}
    out["total_generated"] = jnp.asarray(float(injections["total_generated"]))
    return out


def forward_mode_vjp(f):
    """Wrap f(theta, ev, inj) -> scalar so that jax.grad / value_and_grad use
    forward-mode (jacfwd) internally. Reverse mode through the 1e6-point
    gathers (interp / map_coordinates) turns into scatter-adds into tiny
    grids, which are atomics-bound on the GPU (measured 0.06-0.5 s per
    gradient at full scale); forward mode costs ~n_dim gather-only passes."""
    @jax.custom_vjp
    def g(theta, ev, inj):
        return f(theta, ev, inj)

    def fwd(theta, ev, inj):
        return f(theta, ev, inj), (theta, ev, inj)

    def bwd(res, ct):
        theta, ev, inj = res
        grad = jax.jacfwd(f)(theta, ev, inj)
        zeros = lambda tree: jax.tree_util.tree_map(jnp.zeros_like, tree)
        return (ct * grad, zeros(ev), zeros(inj))

    g.defvjp(fwd, bwd)
    return g


def _pad_call(fn, thetas, chunk, *data):
    thetas = np.atleast_2d(np.asarray(thetas, dtype=np.float64))
    n = len(thetas)
    n_pad = (-n) % chunk
    padded = np.concatenate([thetas, np.tile(thetas[-1:], (n_pad, 1))], axis=0) if n_pad else thetas
    return [fn(jnp.asarray(padded[i:i + chunk]), *data) for i in range(0, len(padded), chunk)], n


class HierarchicalLikelihood:
    """ln L(Lambda) = sum_i ln <p/pi>_i - N ln P_det(Lambda) with Monte Carlo
    convergence cuts (total variance < max_variance, injection n_eff > 4N).

    The core functions (`loglike_aux_data`, `loglike_soft_data`) are pure in
    (theta, ev, inj) so that jit-compiled versions can be cached per model and
    reused on any catalog with the same array shapes (`cache_key`)."""

    _compiled: dict = {}

    def __init__(self, spec: dict, names: list[str], fixed: dict, events: dict, injections: dict,
                 G: Grids, max_variance: float = 1.0, enforce_injection_convergence: bool = True,
                 cache_key: str | None = None, gradient_mode: str = "forward", cut_mode: str = "hard",
                 penalty_scale: float = 1000.0):
        self.spec, self.names, self.fixed, self.G = spec, list(names), dict(fixed), G
        # cut_mode 'hard': ln L = -inf outside the Monte Carlo convergence region (LVK convention);
        # 'penalty': ln L - penalty_scale * [max(0, ln(var_tot/max_var)) + max(0, ln(4N/n_eff))], finite and
        # monotonically decreasing away from the region, so that a nested sampler can find the region from
        # prior draws (deviations.md D11). Posterior weight outside the region is e^-penalty ~ 0 either way.
        assert cut_mode in ("hard", "penalty"), cut_mode
        self.cut_mode, self.penalty_scale = cut_mode, float(penalty_scale)
        assert gradient_mode in ("forward", "reverse", "auto"), gradient_mode
        if gradient_mode == "auto":   # forward mode wins on the GPU (no scatter-adds), reverse on the CPU
            gradient_mode = "forward" if jax.default_backend() == "gpu" else "reverse"
        self.gradient_mode = gradient_mode
        self._soft_fwd = forward_mode_vjp(self.loglike_soft_data)
        self.ev = as_event_arrays(events)
        self.inj = as_injection_arrays(injections)
        self.n_events, self.n_samples = self.ev["mass_1"].shape
        self.n_generated = float(injections["total_generated"])
        self.max_variance = float(max_variance)
        self.enforce = bool(enforce_injection_convergence)
        self.cache_key = cache_key

    # ---- pure pieces -------------------------------------------------------------------
    def unpack(self, theta):
        p = {n: theta[i] for i, n in enumerate(self.names)}
        p.update({k: jnp.asarray(v, dtype=theta.dtype) for k, v in self.fixed.items()})
        return resolve_derived(p, self.spec)

    def per_event_data(self, p, ev):
        lw = log_population(ev, p, self.spec, self.G) - ev["ln_prior"]      # (N, K)
        n_samples = ev["mass_1"].shape[1]
        lnL_i = logsumexp(lw, axis=1) - jnp.log(n_samples)
        ln_m2 = logsumexp(2 * lw, axis=1) - jnp.log(n_samples)
        var_i = (jnp.exp(ln_m2 - 2 * lnL_i) - 1.0) / n_samples
        return lnL_i, var_i

    def selection_data(self, p, inj):
        lw = log_population(inj, p, self.spec, self.G) - inj["ln_prior"]     # (M,)
        n_gen = inj["total_generated"]
        ln_mu = logsumexp(lw) - jnp.log(n_gen)
        ln_s2 = logsumexp(2 * lw) - 2 * jnp.log(n_gen)
        var = jnp.exp(ln_s2) - jnp.exp(2 * ln_mu) / n_gen
        n_eff = jnp.exp(2 * ln_mu) / jnp.maximum(var, 1e-300)
        return ln_mu, var, n_eff

    def loglike_aux_data(self, theta, ev, inj):
        p = self.unpack(theta)
        n_events = ev["mass_1"].shape[0]
        lnL_i, var_i = self.per_event_data(p, ev)
        ln_mu, var, n_eff = self.selection_data(p, inj)
        lnL = jnp.sum(lnL_i) - n_events * ln_mu
        var_tot = jnp.sum(var_i) + n_events**2 * var / jnp.exp(2 * ln_mu)
        ok = constraints_ok(p, self.spec) & jnp.isfinite(lnL)
        if self.cut_mode == "hard":
            ok = ok & (var_tot < self.max_variance)
            if self.enforce:
                ok = ok & (n_eff > 4 * n_events)
            lnL = jnp.where(ok, lnL, -jnp.inf)
        else:
            pen = jnp.maximum(0.0, jnp.log(var_tot / self.max_variance))
            if self.enforce:
                pen = pen + jnp.maximum(0.0, jnp.log(4 * n_events / jnp.maximum(n_eff, 1e-300)))
            lnL = jnp.where(ok & jnp.isfinite(pen), lnL - self.penalty_scale * pen, -jnp.inf)
        return lnL, {"lnL_i": lnL_i, "var_tot": var_tot, "n_eff_inj": n_eff, "ln_pdet": ln_mu}

    def loglike_soft_data(self, theta, ev, inj):
        """Variant without the hard Monte Carlo cuts (for gradient-based use)."""
        p = self.unpack(theta)
        lnL_i, _ = self.per_event_data(p, ev)
        ln_mu, _, _ = self.selection_data(p, inj)
        return jnp.sum(lnL_i) - ev["mass_1"].shape[0] * ln_mu

    # ---- bound to the stored data --------------------------------------------------------
    def loglike_aux(self, theta):
        return self.loglike_aux_data(theta, self.ev, self.inj)

    def loglike(self, theta):
        return self.loglike_aux(theta)[0]

    def loglike_soft(self, theta):
        """ln L_soft bound to the stored data; differentiable with jax.grad
        (forward-mode internally when gradient_mode == 'forward')."""
        if self.gradient_mode == "forward":
            return self._soft_fwd(theta, self.ev, self.inj)
        return self.loglike_soft_data(theta, self.ev, self.inj)

    # ---- compiled evaluators ---------------------------------------------------------------
    def _get_compiled(self, kind: str):
        key = (self.cache_key, kind, self.gradient_mode, self.ev["mass_1"].shape, self.inj["mass_1"].shape,
               self.max_variance, self.enforce, self.cut_mode, self.penalty_scale)
        if self.cache_key is None or key not in HierarchicalLikelihood._compiled:
            if kind == "vmap_aux":
                fn = jax.jit(jax.vmap(self.loglike_aux_data, in_axes=(0, None, None)))
            elif kind == "vmap":
                fn = jax.jit(jax.vmap(lambda t, e, i: self.loglike_aux_data(t, e, i)[0], in_axes=(0, None, None)))
            elif kind == "soft_value_and_grad":
                fn = jax.jit(jax.value_and_grad(self._soft_fwd if self.gradient_mode == "forward"
                                                else self.loglike_soft_data))
            else:
                raise ValueError(kind)
            if self.cache_key is None:
                return fn
            HierarchicalLikelihood._compiled[key] = fn
        return HierarchicalLikelihood._compiled[key]

    def make_batched(self, chunk: int):
        """Vectorized, chunked evaluator: (n, d) numpy -> (n,) numpy log L."""
        vf = self._get_compiled("vmap")

        def call(thetas):
            outs, n = _pad_call(vf, thetas, chunk, self.ev, self.inj)
            return np.concatenate([np.asarray(o) for o in outs])[:n]

        call.n_dim = len(self.names)
        return call

    def make_batched_aux(self, chunk: int):
        vf = self._get_compiled("vmap_aux")

        def call(thetas):
            outs, n = _pad_call(vf, thetas, chunk, self.ev, self.inj)
            lnL = np.concatenate([np.asarray(o[0]) for o in outs])[:n]
            aux = {k: np.concatenate([np.asarray(o[1][k]) for o in outs])[:n] for k in outs[0][1]}
            return lnL, aux

        return call

    def soft_value_and_grad(self):
        """(theta,) -> (ln L_soft, d ln L_soft / d theta), compiled once per cache_key/shape."""
        vg = self._get_compiled("soft_value_and_grad")

        def call(theta):
            v, g = vg(jnp.asarray(theta, dtype=jnp.float64), self.ev, self.inj)
            return float(v), np.asarray(g, dtype=float)

        return call


def population_log_density_numpy(d: dict, params: dict, spec: dict, G: Grids):
    """Convenience: evaluate log p(theta | Lambda) for numpy arrays."""
    dd = {k: jnp.asarray(np.asarray(d[k], float)) for k in ("mass_1", "mass_ratio", "chi_eff", "redshift")}
    p = resolve_derived({k: jnp.asarray(float(v)) for k, v in params.items()}, spec)
    return np.asarray(log_population(dd, p, spec, G))
