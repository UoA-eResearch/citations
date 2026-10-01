#!/usr/bin/env python
"""Analysis grid and prior maps (plan.md sec 2-4).

The grid is NeuroQuery's 4 mm MNI grid and brain mask. For every query (matched and mismatched) the NeuroQuery
prediction map is saved, plus a vector over mask voxels.
Output: data/grid/mask.nii.gz, results/priors/{query}.nii.gz, results/priors/priors.npz (query -> vector over mask voxels)
"""
from pathlib import Path

import nibabel as nb
import numpy as np
from neuroquery import NeuroQueryModel

RUN = Path(__file__).resolve().parents[1]
QUERIES = ["working memory", "emotional faces", "stroop", "face perception", "anticipation", "stop signal",
           "finger tapping"]


def main():
    model = NeuroQueryModel.from_data_dir(str(RUN / "data" / "neuroquery" / "neuroquery_model"))
    mask = model.get_masker().mask_img_ if hasattr(model.get_masker(), "mask_img_") else model.mask_img
    (RUN / "data" / "grid").mkdir(parents=True, exist_ok=True)
    (RUN / "results" / "priors").mkdir(parents=True, exist_ok=True)
    nb.save(mask, RUN / "data" / "grid" / "mask.nii.gz")
    m = np.asarray(mask.get_fdata()) > 0
    print("grid", mask.shape, "mask voxels", int(m.sum()))
    vecs = {}
    for q in QUERIES:
        img = model(q)["brain_map"]
        assert img.shape == mask.shape and np.allclose(img.affine, mask.affine)
        nb.save(img, RUN / "results" / "priors" / f"{q.replace(' ', '_')}.nii.gz")
        vecs[q] = np.asarray(img.get_fdata())[m].astype(np.float32)
        print(f"{q!r}: max {vecs[q].max():.2f}, nonzero {np.mean(vecs[q] != 0):.2f}")
    np.savez_compressed(RUN / "results" / "priors" / "priors.npz", **vecs)


if __name__ == "__main__":
    main()
