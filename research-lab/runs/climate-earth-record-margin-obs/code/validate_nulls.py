#!/usr/bin/env python
"""EXPLORATORY validation of the null models (deviations.md; prompted by R2 < 1 at threshold 0).

Synthetic truth per qualifying station: its own LOESS trend (smooth warming) + stationary AR(1) noise with the station's
residual standard deviation and lag-1 autocorrelation (clipped to [0, 0.8]), on the station's own validity mask. The
full pipeline (LOESS refit, sigma, margins, both nulls) is then run on the synthetic series exactly as on the data.
Because the truth has constant variability, a calibrated trend-preserving null should give R2 = 1 at every threshold,
and the stationary null R1 > 1 by the amount the trend implies. A second synthetic world with NO trend (AR(1) only)
checks R1 = 1. Three replicates per station.
Output: results/tables/null_validation.csv
"""
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import YEARS, detrend, pooled, station  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
PROC, TAB = RUN / "data" / "processed", RUN / "results" / "tables"


def synth(args):
    sid, x, valid, world, rep, seed, method, resample = args[:8]
    truth = args[8] if len(args) > 8 else method
    rng = np.random.default_rng(seed)
    nv = int(valid.sum())
    trend, _ = detrend(YEARS[valid], x[valid], truth)            # the synthetic truth's trend shape
    res = x[valid] - trend[valid]
    sig = np.std(res, ddof=1)
    phi = float(np.clip(np.corrcoef(res[:-1], res[1:])[0, 1], 0, 0.8))
    e = np.zeros(len(YEARS))
    e[0] = rng.normal(0, sig)
    for i in range(1, len(YEARS)):
        e[i] = phi * e[i - 1] + rng.normal(0, sig * np.sqrt(1 - phi ** 2))
    xs = (trend if world == "trend" else trend[YEARS <= 1980].mean()) + e
    out = station((sid, np.where(valid, xs, np.nan), valid, 3, seed + 7, method, resample))
    if out:
        out.pop("m_obs", None)
        out.update(world=world, rep=rep, phi=phi)
    return out


def main():
    method = sys.argv[1] if len(sys.argv) > 1 else "loess"
    resample = sys.argv[2] if len(sys.argv) > 2 else "bootstrap"
    truth = sys.argv[3] if len(sys.argv) > 3 else method
    base = pd.read_parquet(PROC / "station_results_txx_L3.parquet")[["station", "cell"]]
    ex = pd.read_parquet(PROC / "extremes.parquet")
    ex = ex[ex.station.isin(set(base.station))]
    jobs = []
    for k, (sid, g) in enumerate(ex.groupby("station")):
        g = g.set_index("year").reindex(YEARS)
        valid = g.valid.fillna(False).values.astype(bool) & np.isfinite(g.txx.values)
        for world in ("trend", "no_trend"):
            for rep in range(3):
                jobs.append((sid, g.txx.values.astype(float), valid, world, rep, 50000 + 10 * k + rep + (0 if world == "trend" else 5), method, resample, truth))
    with Pool(28) as pool:
        res = [r for r in pool.imap_unordered(synth, jobs, chunksize=16) if r]
    df = pd.DataFrame(res).merge(base, on="station", how="left")
    rows = []
    for world in ("trend", "no_trend"):
        d = df[df.world == world]
        for thr in (0.0, 1.0, 2.0):
            r, nc = pooled(d, thr, nboot=300)
            rows.append(dict(world=world, threshold=thr, n=len(d), R1=r["R1_obs_over_stationary"]["est"],
                             R1_lo=r["R1_obs_over_stationary"]["lo"], R1_hi=r["R1_obs_over_stationary"]["hi"],
                             R2=r["R2_obs_over_trend"]["est"], R2_lo=r["R2_obs_over_trend"]["lo"], R2_hi=r["R2_obs_over_trend"]["hi"],
                             R4=r["R4_E2_over_E1"]["est"], freq_obs=r["freq_obs_E2"]["est"], freq_trend=r["freq_trend_E2"]["est"],
                             freq_stat=r["freq_stat_E2"]["est"]))
    out = pd.DataFrame(rows)
    tag = "" if (method, resample, truth) == ("loess", "bootstrap", "loess") else f"_{method}_{resample}" + ("" if truth == method else f"_truth-{truth}")
    out.to_csv(TAB / f"null_validation{tag}.csv", index=False)
    print(out.round(3).to_string(index=False))
    print("median lag-1 autocorrelation of residuals:", round(float(df.phi.median()), 3))


if __name__ == "__main__":
    sys.exit(main())
