#!/usr/bin/env python
"""Synthetic check of the shrinkage code and the gain computation (plan.md sec 7), run before any real group analysis.

Truth: a smooth random field (FWHM 12 mm) on the real 4 mm mask, SD 0.3. Subjects: truth + smooth noise (FWHM 8 mm,
SD 1). Good prior: truth + an independent smooth field of equal variance (r about 0.7 with truth). Bad prior: an
independent smooth field. 200 synthetic subjects, 100 draws per n.
Checks: (1) S against itself gives G = 1 exactly; (2) EB with the good prior beats S and the flat prior; (3) EB with the
bad prior performs within 0.01 of the flat prior.
Output: results/tables/validation_eb.csv
"""
import sys
from pathlib import Path

import nibabel as nb
import numpy as np
import pandas as pd
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eb  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def field(rng, mask, fwhm_mm, n=1):
    sig = fwhm_mm / (2.3548 * 4.0)
    out = []
    for _ in range(n):
        f = ndimage.gaussian_filter(rng.standard_normal(mask.shape), sig)[mask]
        out.append((f - f.mean()) / f.std())
    return np.array(out).squeeze()


def main():
    mask = np.asarray(nb.load(RUN / "data" / "grid" / "mask.nii.gz").get_fdata()) > 0
    rng = np.random.default_rng(7)
    truth = 0.3 * field(rng, mask, 12)
    Y = truth + field(rng, mask, 8, 200)
    good = truth / 0.3 + field(rng, mask, 12)
    bad = field(rng, mask, 12)
    rows = []
    for label, pw in (("good prior as EB-Q, bad prior as EB-W", bad),):
        d = eb.run_draws(Y.astype(np.float32), good, pw, R=100, seed=3)
        g = eb.gains(d, nboot=500)
        s = d[d.n == 15].groupby("method")[["r", "fpr", "beta"]].mean()
        print(label)
        print(s.round(4).to_string())
        print(g.round(3).to_string(index=False))
        for m in eb.METHODS:
            rows.append(dict(method=m, rbar15=s.loc[m, "r"], fpr15=s.loc[m, "fpr"], beta15=s.loc[m, "beta"],
                             G=g.set_index("method").loc[m, "G"]))
    v = pd.DataFrame(rows).set_index("method")
    checks = {
        "S gives G = 1": abs(v.loc["S", "G"] - 1) < 1e-9,
        "EB-Q (good prior) beats S": v.loc["EB-Q", "rbar15"] > v.loc["S", "rbar15"],
        "EB-Q (good prior) beats EB-0": v.loc["EB-Q", "rbar15"] > v.loc["EB-0", "rbar15"],
        "EB-W (bad prior) within 0.01 of EB-0": abs(v.loc["EB-W", "rbar15"] - v.loc["EB-0", "rbar15"]) < 0.01,
    }
    for k, ok in checks.items():
        print(("PASS " if ok else "FAIL ") + k)
    v.assign(**{k: ok for k, ok in checks.items()}).to_csv(RUN / "results" / "tables" / "validation_eb.csv")


if __name__ == "__main__":
    main()
