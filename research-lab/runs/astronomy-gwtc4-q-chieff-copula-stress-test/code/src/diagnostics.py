#!/usr/bin/env python
"""Stage 06: Bayes-factor table, Savage-Dickey cross-check, leave-one-out
stability, mass-binned posterior predictive checks, selection-function
diagnostics, the baseline acceptance gate, and the preregistered verdict.

Outputs (results/tables/): bf_table_<mode>.csv/.md, loo_<mode>.csv,
ppc_<mode>.csv, diagnostics_<mode>.json; results/summary_<mode>.md
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde, kendalltau

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("JAX_PLATFORMS", "cpu")

from config import add_common_args, load_config, setup_logging  # noqa: E402
from fit_models import load_event_arrays  # noqa: E402
from io_utils import load_json, read_injection_table, read_sample_table, save_json  # noqa: E402
from models_registry import BF_COMPARISONS, build_model  # noqa: E402

LN3 = float(np.log(3))


def load_fit(cfg, model):
    d = cfg.fit_dir(model)
    if not (d / "summary.json").exists():
        return None, None
    return load_json(d / "summary.json"), np.load(d / "posterior.npz", allow_pickle=True)


def sddr_ln_bf_dependence(samples, names, prior):
    """ln BF(dependence vs independence) from the Savage-Dickey density ratio at rho=0."""
    rho = samples[:, names.index("gaussian_copula_rho")]
    kde = gaussian_kde(rho)
    p0 = float(kde(0.0)[0])
    return float(np.log(prior.uniform_density("gaussian_copula_rho")) - np.log(max(p0, 1e-300)))


def loo_table(post, names, event_names, param="gaussian_copula_rho", min_ess=50):
    lnL_i = post["lnL_i"]                      # (S, N)
    x = post["samples"][:, names.index(param)]
    full = np.percentile(x, [5, 50, 95])
    rows = []
    for i, ev in enumerate(event_names):
        lw = -lnL_i[:, i]
        lw -= lw.max()
        w = np.exp(lw)
        w /= w.sum()
        ess = 1.0 / np.sum(w**2)
        order = np.argsort(x)
        cw = np.cumsum(w[order])
        q = np.interp([0.05, 0.5, 0.95], cw, x[order])
        rows.append(dict(event=ev, loo_ess=ess, loo_reliable=ess >= min_ess, p5=q[0], median=q[1], p95=q[2],
                         sign_flip=(np.sign(q[1]) != np.sign(full[1])),
                         excludes_zero_full=bool(full[0] > 0 or full[2] < 0),
                         excludes_zero_loo=bool(q[0] > 0 or q[2] < 0)))
    return pd.DataFrame(rows), full


def ppc_mass_bins(cfg, post, names, spec, G, ev_real, inj, bank, rng, n_draws, edges, logger):
    from jaxmodels import log_population
    import jax.numpy as jnp
    from mock_catalogs import to_internal, from_internal
    m1_obs = np.median(ev_real["mass_1"], axis=1)
    q_obs = np.median(ev_real["mass_ratio"], axis=1)
    c_obs = np.median(ev_real["chi_eff"], axis=1)
    N = len(m1_obs)
    d = {k: jnp.asarray(inj[k]) for k in ("mass_1", "mass_ratio", "chi_eff", "redshift")}
    idx_s = rng.choice(len(post["samples"]), size=min(n_draws, len(post["samples"])), replace=False)
    taus = np.full((len(idx_s), len(edges) - 1), np.nan)
    fixed = {k: float(v) for k, v in spec.get("fixed", {}).items()}
    for s, si in enumerate(idx_s):
        p = {n: jnp.asarray(float(v)) for n, v in zip(names, post["samples"][si])}
        p.update({k: jnp.asarray(v) for k, v in fixed.items()})
        lw = np.asarray(log_population(d, p, spec, G)) - inj["ln_prior"]
        w = np.exp(lw - lw.max())
        w /= w.sum()
        idx = rng.choice(len(w), size=N, replace=True, p=w)
        x_true = to_internal(*[inj[c][idx] for c in ("mass_1", "mass_ratio", "chi_eff", "redshift")])
        obs = np.array([bank.scatter(x_true[e], rng)[1] for e in range(N)])
        m1p, qp, cp, _ = from_internal(obs)
        for b in range(len(edges) - 1):
            sel = (m1p >= edges[b]) & (m1p < edges[b + 1])
            if sel.sum() > 4:
                taus[s, b] = kendalltau(qp[sel], cp[sel])[0]
    rows = []
    for b in range(len(edges) - 1):
        sel = (m1_obs >= edges[b]) & (m1_obs < edges[b + 1])
        t_obs = kendalltau(q_obs[sel], c_obs[sel])[0] if sel.sum() > 4 else np.nan
        pred = taus[:, b][np.isfinite(taus[:, b])]
        rows.append(dict(m1_lo=edges[b], m1_hi=edges[b + 1], n_events=int(sel.sum()), tau_obs=t_obs,
                         pred_p5=np.percentile(pred, 5) if len(pred) else np.nan,
                         pred_p50=np.percentile(pred, 50) if len(pred) else np.nan,
                         pred_p95=np.percentile(pred, 95) if len(pred) else np.nan,
                         p_value_two_sided=(2 * min(np.mean(pred <= t_obs), np.mean(pred >= t_obs))
                                            if len(pred) and np.isfinite(t_obs) else np.nan)))
    return pd.DataFrame(rows), taus


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = load_config(mode=args.mode)
    logger = setup_logging(cfg, "06_diagnostics")
    tables = cfg.path("tables_dir")
    out_json = tables / f"diagnostics_{cfg.mode}.json"
    if not args.force and out_json.exists():
        logger.info("outputs exist, skipping (use --force to redo)")
        return
    diag = {"mode": cfg.mode}
    model_set = list(cfg.mode_value("model_set"))
    fits = {m: load_fit(cfg, m) for m in model_set}
    fits = {m: v for m, v in fits.items() if v[0] is not None}

    # ---- ln Z table and preregistered comparisons ----------------------------------
    rows = []
    for m, (s, post) in fits.items():
        rows.append(dict(model=m, n_dim=s["n_dim"], log_z=s["log_z"], max_log_l=s["max_log_l"],
                         inj_n_eff_min=s["injection_n_eff_min"], inj_n_eff_median=s["injection_n_eff_median"],
                         frac_var_below_1=s["frac_var_below_1"],
                         var_tot_p50=(s.get("var_tot_quantiles") or {}).get("p50", np.nan),
                         var_tot_p95=(s.get("var_tot_quantiles") or {}).get("p95", np.nan),
                         cut_mode=s.get("cut_mode", "hard"), wall_min=s["wall_s"] / 60, n_like=s["n_like"],
                         platform=s["platform"]))
    zt = pd.DataFrame(rows)
    comps = []
    for tag, a, b, desc in BF_COMPARISONS:
        if a in fits and b in fits:
            comps.append(dict(endpoint=tag, model=a, reference=b, description=desc,
                              ln_bf=fits[a][0]["log_z"] - fits[b][0]["log_z"]))
    ct = pd.DataFrame(comps)
    # Savage-Dickey cross-check for the Gaussian copula models
    for m in ("copula_gauss_plp", "copula_gauss_splm1"):
        if m in fits:
            s, post = fits[m]
            _, names, _, prior = build_model(m, cfg)
            diag[f"sddr_ln_bf_dependence_{m}"] = sddr_ln_bf_dependence(post["samples"], list(post["names"]), prior)
            diag[f"rho_quantiles_{m}"] = s["quantiles"]["gaussian_copula_rho"]
    zt.to_csv(tables / f"lnz_table_{cfg.mode}.csv", index=False)
    ct.to_csv(tables / f"bf_table_{cfg.mode}.csv", index=False)
    with open(tables / f"bf_table_{cfg.mode}.md", "w") as f:
        f.write("| endpoint | model | reference | ln BF | description |\n|---|---|---|---|---|\n")
        for r in comps:
            f.write(f"| {r['endpoint']} | {r['model']} | {r['reference']} | {r['ln_bf']:+.2f} | {r['description']} |\n")
        f.write("\n| model | dims | ln Z | max ln L | inj n_eff (min/median) | frac var<1 | var_tot p50/p95 | wall (min) |\n|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['model']} | {r['n_dim']} | {r['log_z']:.2f} | {r['max_log_l']:.2f} | "
                    f"{r['inj_n_eff_min']:.0f}/{r['inj_n_eff_median']:.0f} | {r['frac_var_below_1']:.2f} | "
                    f"{r['var_tot_p50']:.2f}/{r['var_tot_p95']:.2f} | {r['wall_min']:.1f} |\n")
    diag["comparisons"] = comps
    e1 = next((c["ln_bf"] for c in comps if c["endpoint"] == "E1"), np.nan)
    diag["E1_ln_bf_dependence"] = e1

    # ---- E3: mean vs width --------------------------------------------------------------
    if "baseline_plp_both" in fits:
        s = fits["baseline_plp_both"][0]
        diag["baseline_mu_chi_eff_1"] = s["quantiles"].get("mu_chi_eff_1")
        diag["baseline_sigma_chi_eff_1"] = s["quantiles"].get("sigma_chi_eff_1")
        nuts = cfg.fit_dir("baseline_plp_both") / "summary_nuts.json"
        if nuts.exists():
            diag["baseline_mu_chi_eff_1_nuts"] = load_json(nuts)["quantiles"].get("mu_chi_eff_1")
        # acceptance gate (plan sec 4.1) vs arXiv:2508.18083 sec 6.5.1: the paper quotes credibility levels,
        # P(delta mu_eff|q < 0) = 0.82 and P(delta ln sigma_eff|q < 0) = 0.95, for its Linear model
        post_b = fits["baseline_plp_both"][1]
        nb = list(post_b["names"])
        p_mu1 = float(np.mean(post_b["samples"][:, nb.index("mu_chi_eff_1")] < 0))
        p_s1 = float(np.mean(post_b["samples"][:, nb.index("sigma_chi_eff_1")] < 0))
        diag["baseline_p_mu1_negative"], diag["baseline_p_lnsigma1_negative"] = p_mu1, p_s1
        if nuts.exists() and (cfg.fit_dir("baseline_plp_both") / "posterior_nuts.npz").exists():
            pn = np.load(cfg.fit_dir("baseline_plp_both") / "posterior_nuts.npz", allow_pickle=True)
            nn = list(pn["names"])
            diag["baseline_p_mu1_negative_nuts"] = float(np.mean(pn["samples"][:, nn.index("mu_chi_eff_1")] < 0))
            diag["baseline_p_lnsigma1_negative_nuts"] = float(np.mean(pn["samples"][:, nn.index("sigma_chi_eff_1")] < 0))
        dcfg = cfg.raw["diagnostics"]
        ref_mu, ref_s = dcfg.get("reference_p_mu1_negative"), dcfg.get("reference_p_lnsigma1_negative")
        if ref_mu is None or ref_s is None:
            diag["gate"] = {"status": "reference not set (fill diagnostics.reference_p_* from arXiv:2508.18083)"}
        else:
            tol_mu = float(dcfg.get("gate_tolerance_p_mu1", 0.15))
            tol_s = float(dcfg.get("gate_tolerance_p_lnsigma1", 0.10))
            ok_mu, ok_s = abs(p_mu1 - ref_mu) <= tol_mu, abs(p_s1 - ref_s) <= tol_s
            diag["gate"] = {"status": "PASS" if (ok_mu and ok_s) else "FAIL",
                            "p_mu1_negative": {"ours": p_mu1, "reference": ref_mu, "tolerance": tol_mu, "ok": bool(ok_mu)},
                            "p_lnsigma1_negative": {"ours": p_s1, "reference": ref_s, "tolerance": tol_s, "ok": bool(ok_s)},
                            "note": "LVK Linear model uses Broken Power Law + 2 Peaks masses; the plan's baseline uses "
                                    "PowerLaw+Peak (plan sec 4.1)"}
        # D17: gate credibilities for every fitted model with both Linear-spin slopes free (E4 variants, LVK model, ablations)
        slope_table = []
        for m_name, (s_m, post_m) in fits.items():
            nm = list(post_m["names"])
            if "mu_chi_eff_1" in nm and "sigma_chi_eff_1" in nm:
                slope_table.append(dict(model=m_name, log_z=s_m["log_z"],
                                        p_mu1_negative=float(np.mean(post_m["samples"][:, nm.index("mu_chi_eff_1")] < 0)),
                                        p_lnsigma1_negative=float(np.mean(post_m["samples"][:, nm.index("sigma_chi_eff_1")] < 0)),
                                        mu1_median=float(np.median(post_m["samples"][:, nm.index("mu_chi_eff_1")])),
                                        lnsigma1_median=float(np.median(post_m["samples"][:, nm.index("sigma_chi_eff_1")]))))
        diag["slope_credibilities_by_model"] = slope_table
        pd.DataFrame(slope_table).to_csv(tables / f"slope_credibilities_{cfg.mode}.csv", index=False)
        # D15: the same Linear spin model on the LVK's own Broken Power Law + 2 Peaks mass model
        if "lvk_bpl2p_both" in fits:
            s_l, post_l = fits["lvk_bpl2p_both"]
            nl = list(post_l["names"])
            p_mu1_l = float(np.mean(post_l["samples"][:, nl.index("mu_chi_eff_1")] < 0))
            p_s1_l = float(np.mean(post_l["samples"][:, nl.index("sigma_chi_eff_1")] < 0))
            diag["lvk_bpl2p_p_mu1_negative"], diag["lvk_bpl2p_p_lnsigma1_negative"] = p_mu1_l, p_s1_l
            diag["lvk_bpl2p_mu_chi_eff_1"] = s_l["quantiles"].get("mu_chi_eff_1")
            diag["lvk_bpl2p_sigma_chi_eff_1"] = s_l["quantiles"].get("sigma_chi_eff_1")
            if ref_mu is not None and ref_s is not None:
                ok_mu_l, ok_s_l = abs(p_mu1_l - ref_mu) <= tol_mu, abs(p_s1_l - ref_s) <= tol_s
                diag["gate_lvk_masses"] = {"status": "PASS" if (ok_mu_l and ok_s_l) else "FAIL",
                                           "p_mu1_negative": {"ours": p_mu1_l, "reference": ref_mu, "tolerance": tol_mu, "ok": bool(ok_mu_l)},
                                           "p_lnsigma1_negative": {"ours": p_s1_l, "reference": ref_s, "tolerance": tol_s, "ok": bool(ok_s_l)},
                                           "note": "Linear spin model on the LVK Broken Power Law + 2 Peaks mass model (D15)"}
        if "copula_frank_plp" in fits:
            sf, pf = fits["copula_frank_plp"]
            nf = list(pf["names"])
            th = pf["samples"][:, nf.index("frank_copula_theta")]
            diag["frank_theta_crosscheck"] = {"ours_quantiles": sf["quantiles"]["frank_copula_theta"],
                                              "ours_p_negative": float(np.mean(th < 0)),
                                              "reference_kappa_q_eff_lvk": dcfg.get("reference_frank_kappa")}

    # ---- E5: LOO and PPC ------------------------------------------------------------------
    ev_real, names_ev, meta = load_event_arrays(cfg, cfg.rng("fit_subsample"), max_samples=2000)
    if "copula_gauss_plp" in fits:
        s, post = fits["copula_gauss_plp"]
        loo, full = loo_table(post, list(post["names"]), list(post["event_names"]),
                              min_ess=int(cfg.raw["diagnostics"]["loo_min_ess"]))
        loo.to_csv(tables / f"loo_{cfg.mode}.csv", index=False)
        diag["loo"] = dict(n_events=int(len(loo)), n_reliable=int(loo["loo_reliable"].sum()),
                           n_sign_flip=int(loo["sign_flip"].sum()),
                           full_rho_p5_50_95=[float(x) for x in full],
                           n_changes_zero_exclusion=int((loo["excludes_zero_loo"] != loo["excludes_zero_full"]).sum()),
                           most_influential=loo.iloc[np.argmax(np.abs(loo["median"] - full[1]))]["event"])

    # ---- E5 per-mass-bin check against the null mocks, under the D21 primary measure (replaces the copula PPC,
    # which compared PE-prior posterior medians with kernel-centred predictions -- the D19/D21 measure mismatch)
    tau_json, tau_csv = tables / f"e2_tau_{cfg.mode}.json", tables / f"e2_tau_{cfg.mode}.csv"
    e2t = load_json(tau_json) if tau_json.exists() else None
    prim_measure, passing = None, []
    if e2t is not None and "marginal_check_frac_m1ge40" in e2t:
        for M in ("post", "pop", "flattheta", "flatx"):          # D21 preference order
            mc = e2t["marginal_check_frac_m1ge40"][M]
            if mc["null_p2p5"] <= mc["observed"] <= mc["null_p97p5"]:
                passing.append(M)
        prim_measure = passing[0] if passing else None
        diag["e2_tau_measure_check"] = {"passing": passing, "primary": prim_measure,
                                        "frac_m1ge40": e2t["marginal_check_frac_m1ge40"]}
        tdf = pd.read_csv(tau_csv)
        real_t = tdf[tdf.kind == "real"].iloc[0]
        null_t = tdf[(tdf.kind == "mock") & (tdf.rho_true == 0.0)]
        edges = cfg.raw["diagnostics"]["mass_bin_edges_full" if cfg.mode == "full" else "mass_bin_edges_smoke"]
        e5 = []
        for M in (["post", "pop", "flattheta", "flatx"]):
            for b in range(len(edges) - 1):
                obs, v = float(real_t[f"tau_{M}_bin{b}"]), null_t[f"tau_{M}_bin{b}"].dropna().values
                e5.append(dict(measure=M, m1_lo=float(edges[b]), m1_hi=float(edges[b + 1]), n_obs=int(real_t[f"n_{M}_bin{b}"]),
                               n_null_median=float(null_t[f"n_{M}_bin{b}"].median()), tau_obs=obs,
                               null_median=float(np.median(v)), null_p16=float(np.quantile(v, 0.16)),
                               null_p84=float(np.quantile(v, 0.84)),
                               fpr_one_sided=float(np.mean(v <= obs) if obs <= 0 else np.mean(v >= obs))))
        pd.DataFrame(e5).to_csv(tables / f"e5_mass_bins_{cfg.mode}.csv", index=False)
        diag["e5_mass_bins"] = e5

    # ---- E2 and verdict (D20, D21) -------------------------------------------------------------
    # tau-based E2 under the D21 primary measure (the measure whose null mocks reproduce the real point-estimate
    # marginal); hierarchical E2 = the parametric-bootstrap rho scan (D20). The stage-05 fpr file is obsolete.
    fpr = {}
    if e2t is not None:
        for M in ("post", "pop", "flattheta", "flatx"):
            st = e2t["stats"][f"tau_{M}"]
            fpr[M] = dict(observed=st["observed"], fpr_one_sided=st["fpr_one_sided"], fpr_two_sided=st["fpr_two_sided"],
                          null_median=st["curve"][0]["median"], rho_true_matching_median=st["rho_true_matching_median"])
    scan_json = tables / f"e2_rhoscan_{cfg.mode}.json"
    scan = load_json(scan_json) if scan_json.exists() else None
    diag["E2"] = {"tau_by_measure": fpr, "tau_primary_measure": prim_measure, "rho_scan": scan}
    # D26 (post-review): the preregistered E2 statistic is Kendall tau of PE-prior posterior medians ("post"), calibrated
    # against the validated physical-mock-PE catalogs when available -- the detection-consistent v3c (D27c), else v3b (D27);
    # no statistic switching (the D21 fallback to the rho scan is withdrawn). The other measures and the rho scan are
    # reported as diagnostics only.
    v3tag = "v3c" if (tables / f"e2_tau_{cfg.mode}_v3c.json").exists() else "v3"
    v3lab = {"v3c": "v3c detection-consistent physical mock PE (D27c)", "v3": "v3b physical mock PE (D27/D29)"}[v3tag]
    v3p = tables / f"e2_tau_{cfg.mode}_{v3tag}.json"
    e2v3 = load_json(v3p) if v3p.exists() else None
    ri_p = tables / f"e2_rhoscan_int_{cfg.mode}_{v3tag}.json"
    if ri_p.exists():
        ri = load_json(ri_p)
        diag["E2_rho_scan_int"] = dict(mocks=v3tag, observed=ri["observed"], fpr=ri["fpr"],
                                       null=ri["sets"].get("rho+0.00"))
    if e2v3 is not None:
        e2_value, e2_basis = e2v3["stats"]["tau_post"]["fpr_one_sided"], f"tau of PE-prior posterior medians vs {v3lab}"
        diag["E2_v3"] = {M: dict(observed=e2v3["stats"][f"tau_{M}"]["observed"], fpr_one_sided=e2v3["stats"][f"tau_{M}"]["fpr_one_sided"],
                                 fpr_two_sided=e2v3["stats"][f"tau_{M}"]["fpr_two_sided"]) for M in ("post", "pop", "flattheta", "flatx")}
    else:
        e2_value, e2_basis = (fpr["post"]["fpr_one_sided"] if "post" in fpr else None), "tau of PE-prior posterior medians vs v1 mocks (invalid, D26)"
    diag["E2_decision_basis"], diag["E2_fpr"] = e2_basis, e2_value
    verdict = "indeterminate"
    if np.isfinite(e1) and e2_value is not None and np.isfinite(e2_value):
        if e1 < LN3 and e2_value > 0.05:
            verdict = f"CONFIRMED (artifact-consistent): ln BF = {e1:+.2f} < ln 3 and E2 FPR = {e2_value:.3f} > 5% [{e2_basis}]"
        elif e1 >= LN3 and e2_value <= 0.05:
            verdict = f"REFUTED candidate: ln BF = {e1:+.2f} >= ln 3 and E2 FPR = {e2_value:.3f} <= 5% [{e2_basis}]; check E4"
        else:
            verdict = (f"INDETERMINATE: E1 ln BF = {e1:+.2f} < ln 3 but E2 FPR = {e2_value:.3f} <= 5% [{e2_basis}] -- E1 and E2 "
                       "disagree (plan sec 7); the E2 statistic sits in the <= 2.5% tail of every simulated hypothesis except the PLP "
                       "mean shift (10%) and is "
                       "dominated by a PE-prior effect the mocks cannot reproduce (D29, D27c)")
    diag["verdict"] = verdict
    save_json(diag, out_json)

    # ---- human-readable summary ------------------------------------------------------------
    lines = [f"# q-chi_eff copula stress test: results summary ({cfg.mode} mode)", "",
             f"Events: {len(names_ev)}; verdict (plan sec 7 logic): **{verdict}**", "",
             "## Preregistered endpoints", "",
             f"* E1 ln BF(Gaussian copula dependence vs independence, PLP m1) = {e1:+.2f}"
             f" (threshold ln 3 = {LN3:.2f}); SDDR cross-check = "
             f"{diag.get('sddr_ln_bf_dependence_copula_gauss_plp', np.nan):+.2f}",
             f"* E2 decision basis: {e2_basis}; FPR = {e2_value}",
             ((f"* E2 vs {v3tag} by measure (FPR one-sided): " + ", ".join(f"{M} {r['observed']:+.3f} ({r['fpr_one_sided']:.3f})"
                                                                     for M, r in diag["E2_v3"].items())) if "E2_v3" in diag else "* E2 v3: not run"),
             ((f"* Hierarchical rho scan (nuisance-integrated, {v3tag} mocks): rho_hat = {diag['E2_rho_scan_int']['observed']['rho_hat']:+.3f}, "
               f"FPR {diag['E2_rho_scan_int']['fpr']['rho_hat_as_extreme']:.3f}; ln BF(flat rho) = "
               f"{diag['E2_rho_scan_int']['observed']['ln_bf_flat']:+.2f}, FPR {diag['E2_rho_scan_int']['fpr']['ln_bf_flat_ge_observed']:.3f}")
              if "E2_rho_scan_int" in diag else "* integrated rho scan: not run"),
             (f"* Hierarchical rho scan (diagnostic; plug-in, v1 mocks): rho_hat = {scan['observed']['rho_hat']:+.3f}, "
              f"FPR(rho_hat) = {scan['fpr']['rho_hat_as_extreme']:.2f}" if scan else "* rho scan: not run"),
             "", "## Bayes-factor table", ""]
    for c in comps:
        lines.append(f"* {c['endpoint']}: ln BF = {c['ln_bf']:+.2f} ({c['description']})")
    if "baseline_mu_chi_eff_1" in diag and diag["baseline_mu_chi_eff_1"]:
        q, qs = diag["baseline_mu_chi_eff_1"], diag.get("baseline_sigma_chi_eff_1") or {}
        lines += ["", "## Baseline (LVK Linear-model) chi_eff-q slopes (PowerLaw+Peak masses)", "",
                  f"* delta mu_eff|q = {q['median']:+.3f} [{q['p5']:+.3f}, {q['p95']:+.3f}] (90%); "
                  f"P(<0) = {diag.get('baseline_p_mu1_negative', np.nan):.3f} (LVK: 0.82; NUTS: "
                  f"{diag.get('baseline_p_mu1_negative_nuts', np.nan):.3f})",
                  f"* delta ln sigma_eff|q = {qs.get('median', np.nan):+.3f} [{qs.get('p5', np.nan):+.3f}, "
                  f"{qs.get('p95', np.nan):+.3f}] (90%); P(<0) = {diag.get('baseline_p_lnsigma1_negative', np.nan):.3f} "
                  f"(LVK: 0.95; NUTS: {diag.get('baseline_p_lnsigma1_negative_nuts', np.nan):.3f})",
                  f"* Gate (plan sec 4.1): **{diag.get('gate', {}).get('status')}**"]
        if "lvk_bpl2p_p_mu1_negative" in diag:
            ql, qsl = diag.get("lvk_bpl2p_mu_chi_eff_1") or {}, diag.get("lvk_bpl2p_sigma_chi_eff_1") or {}
            lines += ["", "## Same Linear spin model on the LVK Broken Power Law + 2 Peaks masses (D15)", "",
                      f"* delta mu_eff|q = {ql.get('median', np.nan):+.3f} [{ql.get('p5', np.nan):+.3f}, {ql.get('p95', np.nan):+.3f}] (90%); "
                      f"P(<0) = {diag['lvk_bpl2p_p_mu1_negative']:.3f} (LVK: 0.82)",
                      f"* delta ln sigma_eff|q = {qsl.get('median', np.nan):+.3f} [{qsl.get('p5', np.nan):+.3f}, {qsl.get('p95', np.nan):+.3f}] (90%); "
                      f"P(<0) = {diag['lvk_bpl2p_p_lnsigma1_negative']:.3f} (LVK: 0.95)",
                      f"* Gate with the LVK mass model: **{diag.get('gate_lvk_masses', {}).get('status')}**"]
        if diag.get("slope_credibilities_by_model"):
            lines += ["", "## Slope credibilities by mass/pairing/prior configuration (D17 ablation)", "",
                      "| model | ln Z | P(delta mu < 0) | P(delta ln sigma < 0) | median delta mu | median delta ln sigma |", "|---|---|---|---|---|---|"]
            for r in diag["slope_credibilities_by_model"]:
                lines.append(f"| {r['model']} | {r['log_z']:.2f} | {r['p_mu1_negative']:.3f} | {r['p_lnsigma1_negative']:.3f} | "
                             f"{r['mu1_median']:+.3f} | {r['lnsigma1_median']:+.2f} |")
        fc = diag.get("frank_theta_crosscheck")
        if fc:
            oq = fc["ours_quantiles"]
            lines.append(f"* Frank copula theta (spline marginals) = {oq['median']:+.2f} [{oq['p5']:+.2f}, {oq['p95']:+.2f}]; "
                         f"P(<0) = {fc['ours_p_negative']:.3f} (LVK kappa_q,eff = -2.1 [-5.0, +0.3], P(<0) = 0.92)")
    if "loo" in diag:
        lines += ["", f"## LOO: {diag['loo']['n_sign_flip']} of {diag['loo']['n_events']} single-event removals flip the sign of "
                  f"the median rho; {diag['loo']['n_changes_zero_exclusion']} change whether the 90% interval excludes 0; "
                  f"most influential event: {diag['loo']['most_influential']}"]
    if fpr:
        lines += ["", "## E2 point-estimate tau by measure against the v1 mocks (D21; SUPERSEDED by the v3c numbers above, D27c)", "",
                  "| measure | observed tau | null median | FPR one-sided | FPR two-sided | passes marginal check |", "|---|---|---|---|---|---|"]
        for M, r in fpr.items():
            lines.append(f"| {M} | {r['observed']:+.3f} | {r['null_median']:+.3f} | {r['fpr_one_sided']:.3f} | "
                         f"{r['fpr_two_sided']:.3f} | {'yes' if M in passing else 'no'} |")
    if scan:
        lines += ["", "## Hierarchical rho scan, plug-in, v1 mocks (D20; SUPERSEDED by the integrated scan vs v3c above, D27c)", ""]
        for r in scan["response_curve"]:
            lines.append(f"* rho_true = {r['rho_true']:+.2f} (n={r['n']}): rho_hat median {r['rho_hat_median']:+.3f} "
                         f"[{r['rho_hat_p16']:+.3f}, {r['rho_hat_p84']:+.3f}]")
    if "e5_mass_bins" in diag and prim_measure:
        lines += ["", f"## E5 per-mass-bin tau vs the v1 null mocks ({prim_measure} medians; v1 mocks are invalid, D26 -- indicative only)", ""]
        for r in diag["e5_mass_bins"]:
            if r["measure"] == prim_measure:
                lines.append(f"* m1 in [{r['m1_lo']:.0f}, {r['m1_hi']:.0f}) (n={r['n_obs']}; null n~{r['n_null_median']:.0f}): observed "
                             f"{r['tau_obs']:+.3f}, null {r['null_median']:+.3f} [{r['null_p16']:+.3f}, {r['null_p84']:+.3f}], "
                             f"FPR {r['fpr_one_sided']:.3f}")
    with open(cfg.path("results_dir") / f"summary_{cfg.mode}.md", "w") as f:
        f.write("\n".join(lines) + "\n")
    logger.info("verdict: %s", verdict)
    logger.info("stage 06 (diagnostics) complete")


if __name__ == "__main__":
    main()
