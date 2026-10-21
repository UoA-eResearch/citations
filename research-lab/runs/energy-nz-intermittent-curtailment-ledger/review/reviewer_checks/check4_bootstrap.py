"""Reviewer check 4: the block bootstrap relabels resampled days to the original calendar positions, so each
resample's calibration quarters mix days from different true quarters. Compare interval widths with the study's
relabelling against a variant that keeps each resampled day's true quarter (seasonal calibration preserved).
Fewer resamples than the study (B=150 each) to keep runtime down; percentile intervals."""
import sys, time
import numpy as np, pandas as pd
RUN = "/mnt/citations/research-lab/runs/energy-nz-intermittent-curtailment-ledger"
sys.path.insert(0, f"{RUN}/code")
import analysis as A
B = 150
d = A.prepare(pd.read_parquet(f"{RUN}/data/panel.parquet"))
def resample_keep(dd, rng):
    days = np.sort(dd.date.unique()); n = len(days)
    starts = rng.integers(0, n - A.BLOCK + 1, size=int(np.ceil(n / A.BLOCK)))
    pick = np.concatenate([days[s:s + A.BLOCK] for s in starts])[:n]
    by_day = {k: v for k, v in dd.groupby("date")}
    parts = [by_day[t].assign(date=pd.Timestamp(days[i]), rep=i) for i, t in enumerate(pick)]   # true quarter/year labels kept
    return pd.concat(parts, ignore_index=True)
for lab, per in [("2020", A.BASE), ("2025/26", A.RECENT)]:
    dd = A.period(d, *per)
    rng = np.random.default_rng(A.SEED); t0 = time.time()
    study = np.array([A.shares(A.calibrate(A.block_resample(dd, rng)))["share"] for _ in range(B)])
    rng = np.random.default_rng(A.SEED)
    keep = np.array([A.shares(A.calibrate(resample_keep(dd, rng)))["share"] for _ in range(B)])
    pt = A.shares(A.calibrate(dd))["share"]
    q = lambda v: np.percentile(v, [2.5, 97.5])
    print(f"{lab}: point {pt:.4f}; study relabelled B={B}: mean {study.mean():.4f} CI {q(study).round(4)}; "
          f"true-quarter labels: mean {keep.mean():.4f} CI {q(keep).round(4)}  ({time.time()-t0:.0f}s)")
# how mixed are the quarters under relabelling? share of rows whose relabelled quarter differs from the true quarter
rng = np.random.default_rng(1)
dd = A.period(d, *A.RECENT); tq = dd.set_index("date").quarter
rs = A.block_resample(dd.assign(true_q=dd.quarter), rng)
print("share of resampled rows whose calibration quarter differs from the day's true quarter:", round(float((rs.quarter != rs.true_q).mean()), 3))
