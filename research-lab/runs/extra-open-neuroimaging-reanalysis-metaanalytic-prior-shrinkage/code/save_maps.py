#!/usr/bin/env python
"""Full-sample group maps for release (deviations.md D4): per contrast, the mean and between-subject SD of the included
subjects' contrast estimates (percent signal change) on the 4 mm NeuroQuery grid.
Output: results/maps/{key}_mean.nii.gz, results/maps/{key}_sd.nii.gz
"""
import sys
from pathlib import Path

import nibabel as nb
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def main():
    grid = nb.load(RUN / "data" / "grid" / "mask.nii.gz")
    gm = np.asarray(grid.get_fdata()) > 0
    out = RUN / "results" / "maps"
    out.mkdir(parents=True, exist_ok=True)
    for k in A.CONTRASTS:
        Y, gmask, _ = A.load(k)
        for name, vec in (("mean", Y.mean(0)), ("sd", Y.std(0, ddof=1))):
            full = np.zeros(gm.sum(), np.float32)
            full[gmask] = vec
            vol = np.zeros(gm.shape, np.float32)
            vol[gm] = full
            nb.save(nb.Nifti1Image(vol, grid.affine), out / f"{k}_{name}.nii.gz")
    print("maps written")


if __name__ == "__main__":
    main()
