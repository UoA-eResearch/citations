"""External check against the published FitLins group maps (plan secondary 3; G4).

For every dataset with a FitLins output in s3://openneuro-derivatives/fitlins/<ds>-fitlins/, the dataset-level z map
of the spec's contrast (the same contrast name; found by listing the task's node folders) is compared with this
study's configuration closest to the spec: nilearn, 6 mm, SPM canonical, 24P, AR(1) (configuration 18; the specs'
motion terms match fMRIPrep's 24P columns, D2; FitLins smoothed at 5 mm), and with the FSL configuration closest to
it (6 mm, double gamma, 24P, no prewhitening; configuration 67, D3) on the dataset's FSL subjects.
  corr   Pearson correlation of the two z maps over the voxels both cover (this study's group mask, and FitLins
         voxels that are finite and non-zero)
  dice   signed Dice of the two maps thresholded identically: voxelwise FDR q < 0.05, two-sided, Benjamini-Hochberg
         (grouplevel.fdr), FitLins p from its z; within the shared voxels
G4 expects corr >= 0.7; datasets below are listed for inspection.

  external_check.py -> results/tables/external_fitlins.csv, results/tables/external_fitlins.json
FitLins maps are kept in /mnt/data/omv/fitlins/.
"""
import concurrent.futures as cf
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

import nibabel as nb
import numpy as np
from scipy import stats

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import firstlevel as F  # noqa: E402
import grouplevel as G  # noqa: E402

DERIV = "https://openneuro-derivatives.s3.amazonaws.com"
CACHE = Path("/mnt/data/omv/fitlins")
CFG = F.cfg_index(0, 1, 0, 1, 0)          # nilearn, 6 mm, canonical, 24P, AR(1)   (D2)
CFG_FSL = F.cfg_index(1, 1, 0, 1, 1)      # FSL, 6 mm, double gamma, 24P, no prewhitening   (D3)


def listing(prefix, delimiter=None):
    """Keys (and common prefixes) under prefix, following continuation tokens."""
    keys, prefixes, token = [], [], None
    while True:
        url = f"{DERIV}/?list-type=2&prefix={prefix}" + (f"&delimiter={delimiter}" if delimiter else "")
        if token:
            url += "&continuation-token=" + subprocess.run(["python3", "-c", "import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1]))", token],
                                                          capture_output=True, text=True).stdout.strip()
        x = subprocess.run(["curl", "-s", "--max-time", "120", url], capture_output=True, text=True).stdout
        keys += re.findall(r"<Key>([^<]+)</Key>", x)
        prefixes += re.findall(r"<Prefix>([^<]+)</Prefix>", x)[1:] if delimiter else []
        m = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", x)
        if not m:
            return keys, prefixes
        token = m.group(1)


def find_map(ds, task, contrast):
    """Key of the dataset-level z map of `contrast`, or None."""
    _, nodes = listing(f"fitlins/{ds}-fitlins/task-{task}/", "/")
    want = f"contrast-{contrast}_stat-z_statmap.nii.gz"
    # dataset-level nodes first (e.g. node-dataLevel), then any other node
    nodes = sorted(nodes, key=lambda p: (0 if "data" in p.lower() else 1, p))
    for node in nodes:
        keys, _ = listing(node)
        hit = [k for k in keys if k.endswith(want) and "sub-" not in k.split("/")[-1]]
        if hit:
            return hit[0]
    return None


def fetch(key):
    target = CACHE / key.split("fitlins/", 1)[1]
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["curl", "-s", "--max-time", "900", "-o", str(target), f"{DERIV}/{key}"], check=True)
    return target


def compare(ds, task, contrast, tmask, tvox):
    key = find_map(ds, task, contrast)
    if key is None:
        return {"ds": ds, "status": "no FitLins map for the contrast"}
    img = nb.load(fetch(key))
    ref = nb.load(F.TEMPLATE)
    if img.shape[:3] != ref.shape or not np.allclose(img.affine, ref.affine, atol=1e-3):
        from nilearn.image import resample_to_img
        img = resample_to_img(img, ref, interpolation="continuous", force_resample=True, copy_header=True)
        resampled = True
    else:
        resampled = False
    fz = np.asarray(img.dataobj, dtype=np.float32).squeeze()[tuple(tvox.T)]   # template voxels
    g = np.load(F.OUT / ds / "group.npz")
    gmask = g["mask"]                                    # template voxels covered by every subject
    oz = g["z"][CFG].astype(np.float32)                  # our z, within gmask
    os1 = g["s1"][CFG]
    fz_m = fz[gmask]
    shared = np.isfinite(fz_m) & (fz_m != 0)
    if shared.sum() < 1000:
        return {"ds": ds, "status": "too few shared voxels", "shared_voxels": int(shared.sum()), "key": key}
    corr = float(np.corrcoef(oz[shared], fz_m[shared])[0, 1])
    p = 2 * stats.norm.sf(np.abs(fz_m[shared]))
    fs = (np.sign(fz_m[shared]) * G.fdr(p)).astype(np.int8)
    dice = G.signed_dice(os1[shared], fs)
    out = {"ds": ds, "status": "ok", "corr": round(corr, 4), "dice": None if dice is None else round(float(dice), 4),
           "shared_voxels": int(shared.sum()), "ours_supra": int((os1[shared] != 0).sum()),
           "fitlins_supra": int((fs != 0).sum()), "resampled": resampled, "key": key}
    # FSL: group map of configuration 67 over the subjects with FSL maps, within the voxels they all cover
    E = []
    for f in sorted((F.OUT / ds).glob("sub-*.npz")):
        e = np.load(f)["eff"][CFG_FSL].astype(np.float32)
        if np.isfinite(e).any():
            E.append(e)
    if len(E) >= 10:
        E = np.stack(E)
        fm = np.isfinite(E).all(0) & np.isfinite(fz) & (fz != 0)
        zf, pf = G.onesample(E[:, fm])
        sf = (np.sign(zf) * G.fdr(pf)).astype(np.int8)
        pfl = 2 * stats.norm.sf(np.abs(fz[fm]))
        ffl = (np.sign(fz[fm]) * G.fdr(pfl)).astype(np.int8)
        d2 = G.signed_dice(sf, ffl)
        out.update({"fsl_subjects": len(E), "fsl_corr": round(float(np.corrcoef(zf, fz[fm])[0, 1]), 4),
                    "fsl_dice": None if d2 is None else round(float(d2), 4)})
    return out


def main():
    tmask = np.asarray(nb.load(F.TEMPLATE).dataobj) > 0
    tvox = np.argwhere(tmask)
    rows = [r for r in csv.DictReader(open(RUN / "results" / "tables" / "eligible.csv")) if r["status"] == "eligible"]
    with cf.ThreadPoolExecutor(8) as ex:
        out = list(ex.map(lambda r: compare(r["ds"], r["task"], r["contrast"], tmask, tvox), rows))
    for o, r in zip(out, rows):
        o["contrast"] = r["contrast"]
    fields = ["ds", "contrast", "status", "corr", "dice", "shared_voxels", "ours_supra", "fitlins_supra",
              "fsl_subjects", "fsl_corr", "fsl_dice", "resampled", "key"]
    with open(RUN / "results" / "tables" / "external_fitlins.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(out)
    ok = [o for o in out if o["status"] == "ok"]
    corrs = [o["corr"] for o in ok]
    summary = {"datasets_compared": len(ok), "not_compared": {o["ds"]: o["status"] for o in out if o["status"] != "ok"},
               "corr_median": round(float(np.median(corrs)), 4) if corrs else None,
               "corr_at_least_0.7": sum(c >= 0.7 for c in corrs),
               "below_0.7": sorted((o["ds"], o["corr"]) for o in ok if o["corr"] < 0.7),
               "dice_median": round(float(np.median([o["dice"] for o in ok if o["dice"] is not None])), 4) if ok else None,
               "fsl_datasets": sum(1 for o in ok if "fsl_corr" in o),
               "fsl_corr_median": round(float(np.median([o["fsl_corr"] for o in ok if "fsl_corr" in o])), 4),
               "fsl_corr_at_least_0.7": sum(1 for o in ok if o.get("fsl_corr", 0) >= 0.7),
               "fsl_below_0.7": sorted((o["ds"], o["fsl_corr"]) for o in ok if "fsl_corr" in o and o["fsl_corr"] < 0.7)}
    (RUN / "results" / "tables" / "external_fitlins.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
