"""Selection-function inputs: parse the real Zenodo O1-O4a injection mixture
file into the pipeline's flat injection table in the population
parameterization (mass_1, mass_ratio, redshift, chi_eff), with the draw
density converted accordingly.

Conventions (Zenodo record metadata gwtc-4_o1234a_sensitivity-estimates.md;
Essick 2021/2023/2025):
    components   o1o2_semi = rows with no search FAR (semi-analytic O1/O2),
                 o3 = rows with an o3_* FAR, o4a = rows with an o4a_* FAR
    found        o1o2_semi: semianalytic network SNR > snr_thr;
                 o3 / o4a : min FAR over the run's searches < far_thr
    P_det(Lambda) = sum_found w_j p_pop(theta_j|Lambda) / p_draw(theta_j) / N_generated
so gwpopulation's "prior" column is p_draw / w_j.

`lnpdraw` is the per-component draw density over (m1, m2, z, s1x..s2z)
(verified: nearest-neighbour comparisons across components differ
systematically, so it is not one mixture density). The component-spin draw
is i.i.d. per component with a known family (pe_priors.SPIN_FAMILIES):
o3 -> isotropic with magnitudes uniform on [0, a_max]; o4a and o1o2_semi ->
Essick 2025 (truncated-Gaussian magnitudes, 30/70 aligned/isotropic tilts).
Both assignments are validated on the file itself (`spin_draw_check`): after
removing the assumed spin density, the mass/z-controlled residual of lnpdraw
must be uncorrelated with the spin variables. Then
    p_draw(m1, q, z, chi_eff) = p_draw(m1, m2, z) * m1 * h_c(chi_eff | q)
with p_draw(m1, m2, z) = exp(lnpdraw) / (g_c(s1) g_c(s2)).
"""
from __future__ import annotations

import logging

import h5py
import numpy as np
from scipy.spatial import cKDTree

from pe_priors import ChiEffPriorTable, ln_spin_vector_density

logger = logging.getLogger("q_chieff_copula")

LNPDRAW_KEY = "lnpdraw_mass1_source_mass2_source_redshift_spin1x_spin1y_spin1z_spin2x_spin2y_spin2z"
SNR_SEMI_KEY = "semianalytic_observed_phase_maximized_snr_net"
COMPONENTS = ("o1o2_semi", "o3", "o4a")
DEFAULT_SPIN_FAMILIES = {"o1o2_semi": "essick2025", "o3": "isotropic_uniform", "o4a": "essick2025"}


def _decode(x):
    return x.decode() if isinstance(x, bytes) else str(x)


def spin_draw_check(m1, m2, z, a1, a2, ct1, ct2, lnpdraw, ln_g, n_max=60000, k=20) -> dict:
    """Mass/z-controlled residual test: r = lnpdraw - ln g(s1) - ln g(s2) minus
    the mean of r over the k nearest neighbours in (ln m1, ln m2, 3z). If the
    assumed spin density is right, r is uncorrelated with the spin variables."""
    n = min(len(m1), n_max)
    sl = slice(0, n)
    X = np.column_stack([np.log(m1[sl]), np.log(m2[sl]), 3 * z[sl]])
    _, nb = cKDTree(X).query(X, k=k + 1)
    nb = nb[:, 1:]
    corr = lnpdraw[sl] - ln_g[sl]
    r = corr - corr[nb].mean(axis=1)
    raw = lnpdraw[sl] - lnpdraw[sl][nb].mean(axis=1)

    def c(v):
        return float(np.corrcoef(r, v)[0, 1])

    out = {"n": int(n), "resid_std_raw": float(raw.std()), "resid_std_corrected": float(r.std()),
           "corr_ln_a1": c(np.log(np.clip(a1[sl], 1e-6, None))), "corr_a1": c(a1[sl]),
           "corr_cos_t1": c(ct1[sl]), "corr_cos_t2": c(ct2[sl]), "corr_ln_a2": c(np.log(np.clip(a2[sl], 1e-6, None)))}
    out["supported"] = bool(out["resid_std_corrected"] < 0.5 * out["resid_std_raw"]
                            and max(abs(out[k]) for k in out if k.startswith("corr_")) < 0.12)
    return out


def standardize_real_injections(raw_path, far_threshold: float, snr_threshold: float,
                                chieff_cache_dir, chieff_kwargs: dict, slice_n: int | None = None,
                                rng: np.random.Generator | None = None,
                                spin_families: dict | None = None) -> tuple[dict, dict]:
    spin_families = dict(DEFAULT_SPIN_FAMILIES, **(spin_families or {}))
    with h5py.File(raw_path, "r") as f:
        attrs = dict(f.attrs)
        searches = [_decode(s) for s in attrs.get("searches", [])]
        ev = f["events"]
        names = ev.dtype.names
        n_rec = ev.shape[0]
        far_cols = [f"{s}_far" for s in searches if f"{s}_far" in names] or sorted(c for c in names if c.endswith("_far"))
        logger.info("%s: %d injections recorded, searches=%s", raw_path, n_rec, searches)
        far_min = np.full(n_rec, np.inf)
        has_o3 = np.zeros(n_rec, bool)
        has_o4a = np.zeros(n_rec, bool)
        for c in far_cols:
            v = np.asarray(ev[c])
            far_min = np.minimum(far_min, np.nan_to_num(v, nan=np.inf))
            (has_o3 if c.startswith("o3") else has_o4a)[:] |= np.isfinite(v)
        semi = ~has_o3 & ~has_o4a
        comp = np.where(semi, 0, np.where(has_o3, 1, 2)).astype(np.int8)     # index into COMPONENTS
        snr_semi = np.asarray(ev[SNR_SEMI_KEY]) if SNR_SEMI_KEY in names else np.zeros(n_rec)
        found = (semi & (np.nan_to_num(snr_semi, nan=-np.inf) > snr_threshold)) | (~semi & (far_min < far_threshold))
        idx = np.flatnonzero(found)
        n_found_total = int(len(idx))
        counts = {COMPONENTS[i]: {"recorded": int((comp == i).sum()), "found": int((comp[idx] == i).sum())} for i in range(3)}
        logger.info("found injections: %d (o1o2_semi via semianalytic SNR>%.3g: %d; o3/o4a via FAR<%.3g/yr: %d); "
                    "per component %s", n_found_total, snr_threshold, int((semi & found).sum()), far_threshold,
                    int((~semi & found).sum()), counts)
        total_generated = float(attrs["total_generated"])
        if slice_n is not None and slice_n < n_found_total:
            rng = rng or np.random.default_rng(0)
            idx = np.sort(rng.choice(idx, size=slice_n, replace=False))
            total_generated *= slice_n / n_found_total
            logger.info("smoke slice: %d found injections, total_generated scaled to %.1f", slice_n, total_generated)
        cols = ["mass1_source", "mass2_source", "redshift", "spin1x", "spin1y", "spin1z", "spin2x", "spin2y",
                "spin2z", "weights", LNPDRAW_KEY]
        d = {c: np.asarray(ev[c])[idx].astype(float) for c in cols}
        comp = comp[idx]
        analysis_time_s = float(attrs.get("total_analysis_time", np.nan))

    m1, m2, z = d["mass1_source"], d["mass2_source"], d["redshift"]
    a1 = np.sqrt(d["spin1x"] ** 2 + d["spin1y"] ** 2 + d["spin1z"] ** 2)
    a2 = np.sqrt(d["spin2x"] ** 2 + d["spin2y"] ** 2 + d["spin2z"] ** 2)
    ct1 = d["spin1z"] / np.clip(a1, 1e-9, None)
    ct2 = d["spin2z"] / np.clip(a2, 1e-9, None)
    q = m2 / m1
    chi_eff = (m1 * d["spin1z"] + m2 * d["spin2z"]) / (m1 + m2)

    ln_g = np.zeros(len(m1))
    ln_h = np.zeros(len(m1))
    check = {"components": {}, "spin_families": spin_families, "found_rule": "o1o2_semi: SNR>thr; o3/o4a: FAR<thr"}
    amax_by_comp = {}
    for i, name in enumerate(COMPONENTS):
        m = comp == i
        if not m.any():
            continue
        fam = spin_families[name]
        amax = float(np.ceil(max(a1[m].max(), a2[m].max()) * 1000) / 1000) if fam == "isotropic_uniform" else 1.0
        amax_by_comp[name] = amax
        ln_g[m] = (ln_spin_vector_density(fam, a1[m], ct1[m], amax) + ln_spin_vector_density(fam, a2[m], ct2[m], amax))
        table = ChiEffPriorTable(amax, chieff_cache_dir, family=fam, **chieff_kwargs)
        ln_h[m] = table.ln_prob(chi_eff[m], q[m])
        if m.sum() >= 200:
            chk = spin_draw_check(m1[m], m2[m], z[m], a1[m], a2[m], ct1[m], ct2[m], d[LNPDRAW_KEY][m], ln_g[m])
        else:
            chk = {"supported": None, "n": int(m.sum())}
        chk.update(family=fam, amax=amax, n_found=int(m.sum()))
        check["components"][name] = chk
        logger.info("component %s (%d found): spin family %s, a_max=%.3f, draw check %s", name, m.sum(), fam, amax, chk)
        if chk.get("supported") is False:
            logger.warning("component %s: assumed spin family %s NOT supported by the file; chi_eff draw density "
                           "conversion is then approximate", name, fam)
    check["all_supported"] = all(c.get("supported") is not False for c in check["components"].values())

    ln_pdraw_m1m2z = d[LNPDRAW_KEY] - ln_g
    ln_prior = ln_pdraw_m1m2z + np.log(m1) + ln_h - np.log(d["weights"])
    out = {
        "mass_1": m1, "mass_ratio": q, "chi_eff": chi_eff, "redshift": z, "ln_prior": ln_prior,
        "component": comp.astype(np.int8),
        "total_generated": total_generated, "analysis_time_yr": analysis_time_s / (365.25 * 86400),
        "n_found_total": n_found_total, "amax_inj": amax_by_comp.get("o3", 1.0),
    }
    return out, check
