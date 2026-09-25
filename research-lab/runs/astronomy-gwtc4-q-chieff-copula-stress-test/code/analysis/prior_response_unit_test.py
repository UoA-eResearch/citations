#!/usr/bin/env python
"""D29b: why do real posteriors respond ~4x more strongly to the PE prior than Gaussian mock posteriors? (D27c)

Zero-shift unit test of the v3 measurement model. For every real event i, a noise-free Gaussian mock event is placed
at the event's own likelihood mean mu_i in y = (ln Mc_det, eta, chi_eff, ln d_L) with the event's own covariance
Sigma_i (exactly the v3 kernel, with y_obs = mu_i and donor = i), and both the real event and its Gaussian twin are
summarised by the per-event medians of q and chi_eff under two measures:
  post       the PE prior (the released posterior),
  flattheta  flat in (m1, q, chi_eff, z) (prior removed),
with the same weighting code as e2_tau.py. If the Gaussian reproduces the likelihood, the two catalogs have the same
flattheta medians; if it also reproduces the prior response, they have the same post medians. The catalog-level
Kendall tau under both measures and the per-event prior-induced shifts Delta = median_post - median_flattheta are
compared, and the events whose real shift the Gaussian misses most are listed.

Usage: JAX_PLATFORMS=cpu ../venv/bin/python analysis/prior_response_unit_test.py
Output: results/tables/prior_response_unit_test.{csv,json}
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from config import load_config  # noqa: E402
from io_utils import read_sample_table  # noqa: E402
from pe_priors import ChiEffPriorTable, ln_pe_prior  # noqa: E402
from e2_tau import clipped_weights, tau, wmedian  # noqa: E402
from mock_catalogs_v3 import COLS, GaussBank, from_y, ln_pi_flaty  # noqa: E402

N_RAW = 20000


def medians(m1, q, chi, lw_post, lw_flat, clip_q):
    out = {}
    for lab, lw in (("post", lw_post), ("flat", lw_flat)):
        w = clipped_weights(lw[None, :], clip_q)
        out[f"q_{lab}"] = float(wmedian(q[None, :], w)[0])
        out[f"chi_{lab}"] = float(wmedian(chi[None, :], w)[0])
        out[f"m1_{lab}"] = float(wmedian(m1[None, :], w)[0])
    return out


def main():
    cfg = load_config(mode="full", config_path=str(HERE.parent / "config.yaml"))
    sc = cfg.raw["sample"]
    clip_q = float(cfg.raw.get("e2", {}).get("weight_clip_quantile", 0.999)) if isinstance(cfg.raw.get("e2"), dict) else 0.999
    table = ChiEffPriorTable(0.99, cfg.path("processed_dir") / "chieff_prior_cache", n_mc=int(sc["chieff_prior_mc_samples"]),
                             n_q=int(sc["chieff_prior_q_grid"]), n_chi=int(sc["chieff_prior_chi_grid"]), seed=cfg.seed_for("chieff_prior"))
    posteriors, meta = read_sample_table(cfg.sample_table_path())
    bank = GaussBank(posteriors, meta, table)
    rng = np.random.default_rng(20260925)
    rows = []
    for i, name in enumerate(bank.names):
        d = posteriors[name]
        m1, q, chi, z, lp = (d[c].values for c in COLS + ("ln_prior",))
        r = {"event": name, **{f"real_{k}": v for k, v in medians(m1, q, chi, np.zeros_like(lp), -lp, clip_q).items()}}
        # Gaussian twin: the v3 kernel at the event's own mean and covariance, no noise
        L = bank.chol[i]
        out, n_have = [], 0
        for _ in range(400):
            s = bank.mu[i] + rng.standard_normal((2 * N_RAW, 4)) @ L.T
            ok = (s[:, 1] <= 0.25) & (s[:, 1] > 1e-4) & (np.abs(s[:, 2]) < 0.999)
            out.append(s[ok])
            n_have += int(ok.sum())
            if n_have >= N_RAW:
                break
        s = np.concatenate(out)[:N_RAW]
        gm1, gq, gchi, gz = from_y(s)
        lnpe = ln_pe_prior(gm1, gq, gz, gchi, bank.zprior[i], table)
        lnfy = ln_pi_flaty(gm1, gq, gchi, gz)
        # samples are flat-in-y: post = pi_PE / pi_flaty, prior removed = 1 / pi_flaty
        r.update({f"gauss_{k}": v for k, v in medians(gm1, gq, gchi, lnpe - lnfy, -lnfy, clip_q).items()})
        r["real_chi_lik_sd"] = float(np.sqrt(bank.cov[i][2, 2]))
        r["real_eta_chi_corr"] = float(bank.cov[i][1, 2] / np.sqrt(bank.cov[i][1, 1] * bank.cov[i][2, 2]))
        rows.append(r)
    df = pd.DataFrame(rows)
    for src in ("real", "gauss"):
        df[f"{src}_dq"] = df[f"{src}_q_post"] - df[f"{src}_q_flat"]
        df[f"{src}_dchi"] = df[f"{src}_chi_post"] - df[f"{src}_chi_flat"]
    out = {}
    for src in ("real", "gauss"):
        out[src] = dict(tau_post=tau(df[f"{src}_q_post"], df[f"{src}_chi_post"]), tau_flat=tau(df[f"{src}_q_flat"], df[f"{src}_chi_flat"]),
                        tau_qpost_chiflat=tau(df[f"{src}_q_post"], df[f"{src}_chi_flat"]),
                        dq_median=float(df[f"{src}_dq"].median()), dq_mean=float(df[f"{src}_dq"].mean()),
                        dchi_median=float(df[f"{src}_dchi"].median()),
                        tau_dq_vs_chi_flat=tau(df[f"{src}_dq"], df[f"{src}_chi_flat"]))
        out[src]["prior_shift_tau"] = out[src]["tau_post"] - out[src]["tau_flat"]
    out["agreement"] = dict(q_flat_corr=float(np.corrcoef(df.real_q_flat, df.gauss_q_flat)[0, 1]),
                            chi_flat_corr=float(np.corrcoef(df.real_chi_flat, df.gauss_chi_flat)[0, 1]),
                            dq_corr=float(np.corrcoef(df.real_dq, df.gauss_dq)[0, 1]),
                            dq_slope_real_on_gauss=float(np.polyfit(df.gauss_dq, df.real_dq, 1)[0]),
                            q_flat_mean_diff=float((df.real_q_flat - df.gauss_q_flat).mean()))
    df["dq_miss"] = df.real_dq - df.gauss_dq
    worst = df.sort_values("dq_miss").head(10)
    out["largest_missed_shifts"] = worst[["event", "real_chi_flat", "real_q_flat", "real_dq", "gauss_q_flat", "gauss_dq",
                                          "real_eta_chi_corr"]].round(3).to_dict(orient="records")
    tables = cfg.path("tables_dir")
    df.to_csv(tables / "prior_response_unit_test.csv", index=False)
    json.dump(out, open(tables / "prior_response_unit_test.json", "w"), indent=2)
    for src in ("real", "gauss"):
        o = out[src]
        print(f"{src:5s} tau post {o['tau_post']:+.3f} flat {o['tau_flat']:+.3f} (shift {o['prior_shift_tau']:+.3f}); "
              f"q-median shift median {o['dq_median']:+.3f} mean {o['dq_mean']:+.3f}; tau(dq, chi_flat) {o['tau_dq_vs_chi_flat']:+.3f}")
    print("agreement:", {k: round(v, 3) for k, v in out["agreement"].items()})
    print(worst[["event", "real_chi_flat", "real_q_flat", "real_dq", "gauss_q_flat", "gauss_dq", "real_eta_chi_corr"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
