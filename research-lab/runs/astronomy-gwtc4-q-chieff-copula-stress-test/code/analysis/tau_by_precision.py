#!/usr/bin/env python
"""D23 (exploratory): is the point-estimate q-chi_eff rank correlation carried by well- or poorly-measured events?

A population-level correlation should be clearest in the best-measured events; a measurement artefact of point
estimates should live in the poorly-measured events, whose medians depend most on the measure. For the real
catalog and the 200 null mocks, under two measures (flatx = the mocks' native measure, pop = population-informed):
events are ranked by measurement precision (the 90% width of chi_eff, and separately of q, under the same
measure) and split at the median; Kendall tau of the medians is computed within each half.

Outputs: results/tables/tau_by_precision_full.csv, results/tables/tau_by_precision_full.json
"""
from __future__ import annotations

import json
import os
import sys
from multiprocessing import get_context
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

import e2_tau as E  # noqa: E402  (reuses its measures, weights and the null population)
from io_utils import read_sample_table  # noqa: E402

MEAS = ("flatx", "pop")


def wquantile(x, w, qs):
    o = np.argsort(x, axis=1)
    xs, ws = np.take_along_axis(x, o, 1), np.take_along_axis(w, o, 1)
    c = np.cumsum(ws, axis=1)
    c /= c[:, -1:]
    out = []
    for q in qs:
        i = np.minimum((c < q).sum(axis=1), x.shape[1] - 1)
        out.append(xs[np.arange(x.shape[0]), i])
    return out


def split_stats(m1, q, chi, z, ln_native, row):
    clip_q = E._G["clip_q"]
    lnp = E.ln_pop(m1, q, chi, z)
    target = {"flatx": E.ln_flatx(m1, q, z), "pop": lnp}
    for M in MEAS:
        lw = target[M] - ln_native
        w = np.ones_like(m1) if np.allclose(lw, lw[:, :1]) else E.clipped_weights(lw, clip_q)
        q5, q50, q95 = wquantile(q, w, (0.05, 0.5, 0.95))
        c5, c50, c95 = wquantile(chi, w, (0.05, 0.5, 0.95))
        for key, width in (("chiw", c95 - c5), ("qw", q95 - q5)):
            good = width <= np.median(width)
            row[f"{M}_{key}_tau_good"] = E.tau(q50[good], c50[good])
            row[f"{M}_{key}_tau_poor"] = E.tau(q50[~good], c50[~good])
            row[f"{M}_{key}_diff"] = row[f"{M}_{key}_tau_poor"] - row[f"{M}_{key}_tau_good"]
    return row


def _mock(task):
    import h5py
    rho, path, key = task
    with h5py.File(path, "r") as f:
        g = f[key]
        m1, q, chi, z = (np.asarray(g[c]) for c in E.COLS)
        ln_native = np.asarray(g["ln_prior"])
    return split_stats(m1, q, chi, z, ln_native, dict(kind="mock", rho_true=rho, mock=int(key.split("_")[1])))


def main():
    cfg_path = str(HERE.parent / "config.yaml")
    E._init(cfg_path, "full")
    cfg = E._G["cfg"]
    posts, _ = read_sample_table(cfg.sample_table_path())
    names = sorted(posts)
    K, rng = 4000, np.random.default_rng(20260925)
    arr = {c: np.empty((len(names), K)) for c in E.COLS + ("ln_prior",)}
    for i, n in enumerate(names):
        d = posts[n]
        idx = rng.choice(len(d), K, replace=len(d) < K)
        for c in E.COLS + ("ln_prior",):
            arr[c][i] = d[c].values[idx]
    real = split_stats(arr["mass_1"], arr["mass_ratio"], arr["chi_eff"], arr["redshift"], arr["ln_prior"],
                       dict(kind="real", rho_true=np.nan, mock=-1))
    print("real:", {k: round(v, 3) for k, v in real.items() if isinstance(v, float)}, flush=True)
    import h5py
    with h5py.File(cfg.mocks_path(0.0), "r") as f:
        tasks = [(0.0, str(cfg.mocks_path(0.0)), k) for k in sorted(k for k in f if k.startswith("mock_"))]
    rows = [real]
    with get_context("spawn").Pool(16, initializer=E._init, initargs=(cfg_path, "full")) as pool:
        rows += list(pool.imap_unordered(_mock, tasks, chunksize=2))
    df = pd.DataFrame(rows)
    df.to_csv(cfg.path("tables_dir") / "tau_by_precision_full.csv", index=False)
    null = df[df.kind == "mock"]
    out = {}
    for col in [c for c in df.columns if c.endswith(("_good", "_poor", "_diff"))]:
        v, o = null[col].values, real[col]
        out[col] = dict(observed=float(o), null_median=float(np.median(v)), null_p2p5=float(np.quantile(v, 0.025)),
                        null_p97p5=float(np.quantile(v, 0.975)),
                        fpr_one_sided=float(np.mean(v <= o) if o <= np.median(v) else np.mean(v >= o)))
        print(f"{col:<22} observed {o:+.3f} | null median {out[col]['null_median']:+.3f} "
              f"[{out[col]['null_p2p5']:+.3f}, {out[col]['null_p97p5']:+.3f}] | FPR {out[col]['fpr_one_sided']:.3f}", flush=True)
    json.dump(out, open(cfg.path("tables_dir") / "tau_by_precision_full.json", "w"), indent=2)


if __name__ == "__main__":
    main()
