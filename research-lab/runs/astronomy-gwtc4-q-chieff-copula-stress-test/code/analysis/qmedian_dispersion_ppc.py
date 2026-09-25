#!/usr/bin/env python
"""D29c: does the catalog-level PE-prior shift of tau depend on how concentrated the q medians are?

The prior-response unit test (D29b) shows that a Gaussian twin of every real event reproduces the event's prior-induced
q-median shift and the real catalog's tau shift (-0.120 vs -0.120). The v3 mocks nevertheless show only ~-0.03. Here,
per catalog (real, and each v3c null mock), under the prior-removed measure (flat in theta; same weighting as e2_tau):
  sd_q, iqr_q     spread of the per-event q medians across events,
  mean_q          their mean,
  dq_mean         mean prior-induced q-median shift (post - flat),
  tau_dq_chi      Kendall tau between that shift and the chi_eff median (does the prior move high-chi_eff events?),
  tau_shift       tau_post - tau_flat,
and the relation between tau_shift and sd_q across the mocks. A posterior-predictive check of the q-median spread
follows directly (real vs the null mocks' distribution).

Usage: JAX_PLATFORMS=cpu ../venv/bin/python analysis/qmedian_dispersion_ppc.py [--mock-dir ../data/mocks/v3c] [--n 200]
Output: results/tables/qmedian_dispersion_ppc_<tag>.{csv,json}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
import h5py  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from config import load_config  # noqa: E402
from e2_tau import clipped_weights, tau, wmedian  # noqa: E402
from fit_models import load_event_arrays  # noqa: E402

COLS = ("mass_1", "mass_ratio", "chi_eff", "redshift")


def stats(q, chi, lp, clip_q):
    wf = clipped_weights(-lp, clip_q)                        # prior removed (flat in theta)
    wp = np.ones_like(q)                                     # the stored samples are PE-prior posteriors
    qf, cf = wmedian(q, wf), wmedian(chi, wf)
    qp, cp = wmedian(q, wp), wmedian(chi, wp)
    dq = qp - qf
    return dict(sd_q=float(np.std(qf)), iqr_q=float(np.subtract(*np.quantile(qf, [0.75, 0.25]))), mean_q=float(np.mean(qf)),
                frac_q_gt_0p8=float(np.mean(qf > 0.8)), sd_chi=float(np.std(cf)),
                dq_mean=float(dq.mean()), tau_dq_chi=tau(dq, cf), tau_flat=tau(qf, cf), tau_post=tau(qp, cp),
                tau_shift=tau(qp, cp) - tau(qf, cf))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock-dir", default=None)
    ap.add_argument("--n", type=int, default=200)
    args = ap.parse_args()
    cfg = load_config(mode="full", config_path=str(HERE.parent / "config.yaml"))
    clip_q = float(cfg.raw["mocks"]["kernel_weight_clip_quantile"])
    mock_dir = Path(args.mock_dir) if args.mock_dir else cfg.path("mocks_dir") / "v3c"
    ev, _, _ = load_event_arrays(cfg, np.random.default_rng(1000), max_samples=2000)
    rows = [dict(kind="real", mock=-1, **stats(ev["mass_ratio"], ev["chi_eff"], ev["ln_prior"], clip_q))]
    with h5py.File(mock_dir / "mocks_full_rho+0.00.h5", "r") as fh:
        for k in sorted(k for k in fh if k.startswith("mock_"))[: args.n]:
            g = fh[k]
            rows.append(dict(kind="mock", mock=int(k.split("_")[1]),
                             **stats(np.asarray(g["mass_ratio"]), np.asarray(g["chi_eff"]), np.asarray(g["ln_prior"]), clip_q)))
    df = pd.DataFrame(rows)
    real, m = df[df.kind == "real"].iloc[0], df[df.kind == "mock"]
    out = {"mock_dir": str(mock_dir), "n_mocks": int(len(m)), "real": {k: float(real[k]) for k in m.columns if k not in ("kind", "mock")},
           "null": {k: dict(median=float(m[k].median()), p2p5=float(m[k].quantile(0.025)), p97p5=float(m[k].quantile(0.975)),
                            frac_le_real=float(np.mean(m[k] <= real[k])))
                    for k in m.columns if k not in ("kind", "mock")}}
    b = np.polyfit(m.sd_q, m.tau_shift, 1)
    out["tau_shift_vs_sd_q"] = dict(slope=float(b[0]), intercept=float(b[1]), corr=float(np.corrcoef(m.sd_q, m.tau_shift)[0, 1]),
                                    predicted_at_real_sd_q=float(np.polyval(b, real.sd_q)))
    tag = mock_dir.name
    tables = cfg.path("tables_dir")
    df.to_csv(tables / f"qmedian_dispersion_ppc_{tag}.csv", index=False)
    json.dump(out, open(tables / f"qmedian_dispersion_ppc_{tag}.json", "w"), indent=2)
    for k in ("sd_q", "iqr_q", "mean_q", "frac_q_gt_0p8", "sd_chi", "dq_mean", "tau_dq_chi", "tau_flat", "tau_post", "tau_shift"):
        n = out["null"][k]
        print(f"{k:14s} real {real[k]:+.3f} | null median {n['median']:+.3f} [{n['p2p5']:+.3f}, {n['p97p5']:+.3f}] | P(null <= real) {n['frac_le_real']:.3f}")
    print("tau_shift vs sd_q across mocks:", {k: round(v, 3) for k, v in out["tau_shift_vs_sd_q"].items()})


if __name__ == "__main__":
    main()
