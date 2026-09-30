#!/usr/bin/env python
"""EXPLORATORY coverage check of the uncertainty intervals (deviations.md D6; prompted by the independent review).

Synthetic worlds with a KNOWN answer (R = 1) and realistic cross-station dependence: each qualifying station's hinge
trend (trend worlds, testing R2) or no trend (no-trend worlds, testing R1), plus nested noise matched to the data:
a year effect shared by all stations in the same 20x20-degree region (39% of residual variance), a further year effect
shared within the 5x5-degree cell (20%), and station-specific white noise (41%). The shares reproduce the measured
station-weighted mean pairwise correlation of hinge residuals within 20-degree regions (0.39) and within 5-degree
cells (0.59). The full pipeline is run on each world (hinge detrending, block-permutation nulls with
200 surrogates), and the 95% intervals from the cell-only bootstrap and from the two-way (cell x 3-year block) bootstrap
are checked for whether they contain 1.
Second dependence model (argv[2] == "kernel"): Gaussian noise whose correlation decays with great-circle distance,
corr(d) = 0.78 exp(-d / 819 km) (+ 0.22 station-specific), fitted to the measured station-pair correlation of hinge
residuals in 500-km distance bins (0.56 at 0-500 km, 0.33 at 500-1000, 0.18 at 1000-1500, 0.09 at 1500-2000, ~0 beyond),
which unlike the nested model has no artificial region boundaries.
Output: results/tables/coverage_validation.csv, coverage_validation_kernel.csv
"""
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze as A  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
PROC, TAB = RUN / "data" / "processed", RUN / "results" / "tables"
A.NSUR = 200
FRAC20, FRAC5 = 0.39, 0.20


def run_station(args):
    return A.station(args)


KERNEL_A, KERNEL_L = 0.782, 819.0
_CHOL = {}


def kernel_noise(base, rng):
    if "L" not in _CHOL:
        la, lo = np.radians(base.lat.values), np.radians(base.lon.values)
        cosd = np.sin(la)[:, None] * np.sin(la)[None, :] + np.cos(la)[:, None] * np.cos(la)[None, :] * np.cos(lo[:, None] - lo[None, :])
        d = 6371 * np.arccos(np.clip(cosd, -1, 1))
        C = KERNEL_A * np.exp(-d / KERNEL_L) + (1 - KERNEL_A) * np.eye(len(base))
        _CHOL["L"] = np.linalg.cholesky(C + 1e-9 * np.eye(len(base)))
    return _CHOL["L"] @ rng.normal(0, 1, (len(base), len(A.YEARS)))


def world(base, ex, kind, w_seed, dep="nested"):
    rng = np.random.default_rng(w_seed)
    Z = kernel_noise(base, rng) if dep == "kernel" else None
    region = (np.floor(base.lat / 20)).astype(int).astype(str) + "_" + (np.floor(base.lon / 20)).astype(int).astype(str)
    common = {r: rng.normal(0, 1, len(A.YEARS)) for r in region.unique()}
    cellfx = {c: rng.normal(0, 1, len(A.YEARS)) for c in base.cell.unique()}
    jobs = []
    g_all = dict(tuple(ex.groupby("station")))
    for k, (sid, reg, cell) in enumerate(zip(base.station, region, base.cell)):
        g = g_all[sid].set_index("year").reindex(A.YEARS)
        valid = g.valid.fillna(False).values.astype(bool) & np.isfinite(g.txx.values)
        trend, _ = A.detrend(A.YEARS[valid], g.txx.values[valid], "hinge")
        sig = float(np.std(g.txx.values[valid] - trend[valid], ddof=2))
        if Z is not None:
            e = sig * Z[k]
        else:
            e = sig * (np.sqrt(FRAC20) * common[reg] + np.sqrt(FRAC5) * cellfx[cell]
                       + np.sqrt(1 - FRAC20 - FRAC5) * rng.normal(0, 1, len(A.YEARS)))
        x = (trend if kind == "trend" else trend[A.YEARS <= 1980].mean()) + e
        jobs.append((sid, np.where(valid, x, np.nan), valid, 3, int(w_seed * 10000 + k), "hinge", "permute"))
    with Pool(28) as pool:
        res = [r for r in pool.map(run_station, jobs, chunksize=16) if r]
    d = pd.DataFrame(res).merge(base[["station", "cell"]], on="station")
    return d


def main():
    n_worlds = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    dep = sys.argv[2] if len(sys.argv) > 2 else "nested"
    base = pd.read_parquet(PROC / "station_results_txx_L3_hinge_permute_screened.parquet")[["station", "lat", "lon", "cell"]]
    ex = pd.read_parquet(PROC / "extremes.parquet")
    rows = []
    for w in range(n_worlds):
        for kind, key in (("trend", "R2_obs_over_trend"), ("no_trend", "R1_obs_over_stationary")):
            d = world(base, ex, kind, 900 + 2 * w + (kind == "trend") + (5000 if dep == "kernel" else 0), dep)
            for thr in (0.0, 1.0):
                cell, _ = A.pooled(d, thr, nboot=300)
                two = A.pooled_twoway(d, thr, nboot=300)
                rows.append(dict(world=w, kind=kind, threshold=thr, est=cell[key]["est"],
                                 cell_lo=cell[key]["lo"], cell_hi=cell[key]["hi"], two_lo=two[key]["lo"], two_hi=two[key]["hi"]))
            print(f"world {w} {kind}: " + " | ".join(f"thr{int(r['threshold'])} est {r['est']:.2f} cell [{r['cell_lo']:.2f},{r['cell_hi']:.2f}] two-way [{r['two_lo']:.2f},{r['two_hi']:.2f}]"
                                                     for r in rows[-2:]), flush=True)
    out = pd.DataFrame(rows)
    out["cell_covers"] = (out.cell_lo <= 1) & (out.cell_hi >= 1)
    out["two_covers"] = (out.two_lo <= 1) & (out.two_hi >= 1)
    out.to_csv(TAB / f"coverage_validation{'' if dep == 'nested' else '_' + dep}.csv", index=False)
    print(out.groupby(["kind", "threshold"])[["cell_covers", "two_covers"]].mean())
    for (kd, t), g in out.groupby(["kind", "threshold"]):
        print(kd, t, "mean est %.3f  sd log est %.3f  two-way half-width/1.96 %.3f  cell-only %.3f" % (
            g.est.mean(), np.log(g.est).std(), (np.log(g.two_hi) - np.log(g.two_lo)).mean() / 3.92,
            (np.log(g.cell_hi) - np.log(g.cell_lo)).mean() / 3.92))


if __name__ == "__main__":
    sys.exit(main())
