#!/usr/bin/env python
"""EXPLORATORY diagnostic for the mechanism in deviations.md D3: across voxels, does the size of the group effect track
the between-subject spread? If so, voxel-specific shrinkage (weight tau2 / (tau2 + s2_v)) shrinks the strongest voxels
most. Full samples. Output: results/tables/variance_effect.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def main():
    rows = []
    for k, (dom, *_rest) in A.CONTRASTS.items():
        Y, _, _ = A.load(k)
        m, sd = Y.mean(0), Y.std(0, ddof=1)
        top = np.abs(m) >= np.percentile(np.abs(m), 90)
        rows.append(dict(key=k, domain=dom, n=Y.shape[0], r_abs_effect_sd=np.corrcoef(np.abs(m), sd)[0, 1],
                         sd_ratio_top10_vs_rest=sd[top].mean() / sd[~top].mean()))
    t = pd.DataFrame(rows)
    t.to_csv(RUN / "results" / "tables" / "variance_effect.csv", index=False)
    print(t.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
