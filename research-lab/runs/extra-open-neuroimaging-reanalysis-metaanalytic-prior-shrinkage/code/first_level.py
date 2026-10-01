#!/usr/bin/env python
"""First-level model for one (dataset, task, subject) row of data/manifest.tsv (plan.md sec 3).

Downloads the MNI preprocessed BOLD, brain mask, confounds and events from OpenNeuro's S3 bucket, smooths at native
resolution (6 mm FWHM), fits a nilearn FirstLevelModel on the NeuroQuery 4 mm grid (mask = NeuroQuery mask intersected
with the subject's brain mask), computes the domain contrast (effect size, percent signal change), and deletes the BOLD.

Usage: first_level.py ROW_INDEX
Output: data/first_level/{dataset}_{task}/{sub}.npz with effect (float32 over the 28,542 grid-mask voxels, NaN outside
the subject's mask), coverage, mean_fd, n_vols, t_r; or {sub}.err with the failure message (downloads are then kept
in data/tmp for a rerun).
"""
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

import nibabel as nb
import numpy as np
import pandas as pd
from nilearn import image
from nilearn.glm.first_level import FirstLevelModel

RUN = Path(__file__).resolve().parents[1]
B = "https://s3.amazonaws.com/openneuro.org/"
CONTRASTS = {
    "workingmemory": "0.5*active_change + 0.5*active_nochange - passive",
    "emomatching": "emotion - control",
    "gstroop": "incongruent - congruent",
    "anticipation": "cue_negative - cue_neutral",
    "faces": "0.2*anger + 0.2*contempt + 0.2*joy + 0.2*neutral + 0.2*pride",
    "stopsignal": "succesful_stop - go",
}
MOTION = [f"{a}_{x}" for a in ("trans", "rot") for x in "xyz"]


def fetch(key, dest, tries=6):
    for i in range(tries):
        r = subprocess.run(["curl", "-sf", "--retry", "3", "-o", str(dest), B + key])
        if r.returncode == 0 and dest.exists() and dest.stat().st_size > 0:
            return
        time.sleep(10 * (i + 1))
    raise RuntimeError(f"download failed: {key}")


def main():
    i = int(sys.argv[1])
    row = pd.read_csv(RUN / "data" / "manifest.tsv", sep="\t").iloc[i]
    out = RUN / "data" / "first_level" / f"{row.dataset}_{row.task}"
    out.mkdir(parents=True, exist_ok=True)
    if (out / f"{row['sub']}.npz").exists():
        return
    tmp = RUN / "data" / "tmp" / f"{row.dataset}_{row.task}_{row['sub']}"
    tmp.mkdir(parents=True, exist_ok=True)
    lock = tmp.with_suffix(".lock")
    try:
        os.mkdir(lock)                                                   # atomic: one worker per subject
    except FileExistsError:
        return
    try:
        if not (out / f"{row['sub']}.npz").exists():                     # another worker may have just finished
            _fit(row, out, tmp)
    finally:
        lock.rmdir()


def _fit(row, out, tmp):
    try:
        bold, conf, smask, ev = (tmp / "bold.nii.gz", tmp / "conf.tsv", tmp / "mask.nii.gz", tmp / "events.tsv")
        for k, d in ((row.conf_key, conf), (row.mask_key, smask), (row.events_key, ev)):
            fetch(k, d)
        if not (bold.exists() and bold.stat().st_size == int(row.bold_size)):    # cached from a failed attempt
            fetch(row.bold_key, bold)
        grid = nb.load(RUN / "data" / "grid" / "mask.nii.gz")
        gm = np.asarray(grid.get_fdata()) > 0
        sm = image.resample_to_img(nb.load(smask), grid, interpolation="nearest", force_resample=True, copy_header=True)
        sub_m = gm & (np.asarray(sm.get_fdata()) > 0)
        coverage = sub_m.sum() / gm.sum()
        img = nb.load(bold)
        t_r = float(img.header.get_zooms()[3])
        c = pd.read_csv(conf, sep="\t")
        mean_fd = float(np.nanmean(c["framewise_displacement"]))
        cols = MOTION + [m + "_derivative1" for m in MOTION] + ["csf", "white_matter"] + \
            [x for x in c.columns if x.startswith("non_steady_state_outlier")]
        confounds = c[cols].fillna(0.0)
        events = pd.read_csv(ev, sep="\t")[["onset", "duration", "trial_type"]].dropna(subset=["trial_type"])
        smoothed = image.smooth_img(img, 6)
        glm_mask = nb.Nifti1Image(sub_m.astype(np.uint8), grid.affine)
        flm = FirstLevelModel(t_r=t_r, slice_time_ref=0.5, hrf_model="glover", drift_model="cosine", high_pass=1 / 128,
                              noise_model="ar1", smoothing_fwhm=None, signal_scaling=0, mask_img=glm_mask,
                              minimize_memory=True)
        flm.fit(smoothed, events=events, confounds=confounds)
        eff = flm.compute_contrast(CONTRASTS[row.task], output_type="effect_size")
        e = np.asarray(eff.get_fdata())
        vec = np.where(sub_m, e, np.nan)[gm].astype(np.float32)
        np.savez_compressed(out / f"{row['sub']}.npz", effect=vec, coverage=coverage, mean_fd=mean_fd,
                            n_vols=img.shape[3], t_r=t_r)
    except Exception:
        (out / f"{row['sub']}.err").write_text(traceback.format_exc())
        return                                                           # keep the downloads for a rerun
    for f in tmp.glob("*"):
        f.unlink()
    tmp.rmdir()
    (out / f"{row['sub']}.err").unlink(missing_ok=True)


if __name__ == "__main__":
    main()
