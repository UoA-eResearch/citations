"""Group maps and robustness metrics per dataset (plan sections 0 and 2; D1-D4).

Per configuration: a one-sample t-test across subjects on the subject-level fixed-effects maps, within the voxels
every analysed subject covers (finite in every subject's map for nilearn configuration 0); z from the t distribution;
primary threshold voxelwise FDR q < 0.05 two-sided (Benjamini-Hochberg), secondary |z| > 3.1 with clusters of at
least 20 voxels (26-connectivity, positive and negative separately).

Robustness over the 48 nilearn configurations:
  R          mean pairwise signed Dice of the thresholded maps (pairs where both are empty are excluded and counted;
             a pair with one empty map scores 0)
  R_sec      the same with the secondary threshold
  corr       mean pairwise Pearson correlation of the unthresholded z maps
  peak       the share of configurations in which the medoid configuration's peak voxel (largest |z|) keeps its sign
             and is suprathreshold (medoid = highest mean correlation with the others)
  any        the share of configurations with any suprathreshold voxel
Per axis: the mean Dice over pairs that differ only on that axis. Software (D3): on the FSL subjects (the first 20 of
the seeded order), each FSL map against the nilearn map that differs only in software, and nilearn pairs that differ
only in confounds, for reference.

  grouplevel.py DS [DS ...]   -> /mnt/data/omv/out/<ds>/group.npz, results/tables/group/<ds>.json
"""
import itertools
import json
import sys
from pathlib import Path

import nibabel as nb
import numpy as np
from scipy import ndimage, stats

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import driver  # noqa: E402
import firstlevel as F  # noqa: E402

TG = RUN / "results" / "tables" / "group"
NIL = list(range(48))
FSLK = [F.cfg_index(1, 1, 0, c, 1) for c in range(4)]
NIL_MATCH = [F.cfg_index(0, 1, 0, c, 1) for c in range(4)]           # 6 mm, canonical, confound c, OLS


def onesample(Y):
    n = Y.shape[0]
    m, sd = Y.mean(0), Y.std(0, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = m / (sd / np.sqrt(n))
    t = np.nan_to_num(t, nan=0.0)
    p = 2 * stats.t.sf(np.abs(t), n - 1)
    z = np.sign(t) * stats.norm.isf(np.clip(p / 2, 1e-300, 0.5))
    return z, p


def fdr(p, q=0.05):
    s = np.sort(p)
    k = np.nonzero(s <= q * np.arange(1, len(s) + 1) / len(s))[0]
    return p <= s[k[-1]] if len(k) else np.zeros(len(p), bool)


def clusters(z, vox, shape, thr=3.1, k=20):
    out = np.zeros(len(z), bool)
    for sign in (1, -1):
        vol = np.zeros(shape, bool)
        sel = sign * z > thr
        vol[tuple(vox[sel].T)] = True
        lab, n = ndimage.label(vol, structure=np.ones((3, 3, 3)))
        if n:
            sizes = ndimage.sum(vol, lab, range(1, n + 1))
            big = np.isin(lab, np.nonzero(sizes >= k)[0] + 1)
            out |= big[tuple(vox.T)] & sel
    return out


def signed_dice(sa, sb):
    """sa, sb: int8 maps (+1, -1, 0). None if both empty."""
    na, nb_ = (sa != 0).sum(), (sb != 0).sum()
    if na + nb_ == 0:
        return None
    return 2 * ((sa == 1) & (sb == 1)).sum() / (na + nb_) + 2 * ((sa == -1) & (sb == -1)).sum() / (na + nb_)


def summarise(S, Z, keys):
    pairs = list(itertools.combinations(keys, 2))
    d = [signed_dice(S[a], S[b]) for a, b in pairs]
    dv = [x for x in d if x is not None]
    C = np.corrcoef(np.stack([Z[k] for k in keys]))
    iu = np.triu_indices(len(keys), 1)
    med = keys[int(np.argmax((C.sum(1) - 1) / (len(keys) - 1)))]
    pk = int(np.argmax(np.abs(Z[med])))
    sg = np.sign(Z[med][pk])
    return {"R": float(np.mean(dv)) if dv else None, "pairs": len(pairs), "pairs_both_empty": int(sum(x is None for x in d)),
            "corr": float(C[iu].mean()), "medoid": int(med),
            "peak": float(np.mean([(np.sign(Z[k][pk]) == sg) and S[k][pk] != 0 for k in keys])),
            "any": float(np.mean([(S[k] != 0).any() for k in keys]))}


def axis_dice(S, keys):
    labels = {k: F.cfg_label(k) for k in keys}
    out = {}
    for ax in ("smoothing", "hrf", "confounds", "noise"):
        vals = []
        for a, b in itertools.combinations(keys, 2):
            la, lb = labels[a], labels[b]
            if la[ax] != lb[ax] and all(la[x] == lb[x] for x in la if x != ax):
                v = signed_dice(S[a], S[b])
                if v is not None:
                    vals.append(v)
        out[ax] = float(np.mean(vals)) if vals else None
    return out


def maps(E, keys, mask, vox, shape):
    Z, S1, S2 = {}, {}, {}
    for k in keys:
        Y = E[:, k][:, mask].astype(np.float32)
        z, p = onesample(Y)
        Z[k] = z
        S1[k] = (np.sign(z) * fdr(p)).astype(np.int8)
        S2[k] = (np.sign(z) * clusters(z, vox, shape)).astype(np.int8)
    return Z, S1, S2


def run_dataset(ds):
    subs = driver.order(ds)[:driver.CAP]
    files = [(s, F.OUT / ds / f"sub-{s}.npz") for s in subs]
    files = [(s, f) for s, f in files if f.exists()]
    if len(files) < 10:
        return {"ds": ds, "status": f"only {len(files)} subjects"}
    tm = nb.load(F.TEMPLATE)
    tmask = tm.get_fdata() > 0
    vox_all = np.argwhere(tmask)
    E, E2, meta, fsl_ok = [], [], [], []
    for j, (s, f) in enumerate(files):
        z = np.load(f)
        E.append(z["eff"])
        E2.append(z["eff2"] if "eff2" in z else None)
        meta.append(json.loads(str(z["meta"])))
        fsl_ok.append(subs.index(s) < driver.FSL_N and np.isfinite(z["eff"][FSLK[0]].astype(np.float32)).any())
    E = np.stack(E)
    mask = np.isfinite(E[:, 0].astype(np.float32)).all(0)
    vox = vox_all[mask]
    out = {"ds": ds, "status": "ok", "N": len(files), "voxels": int(mask.sum())}
    runs = [m for mm in meta for m in mm if m.get("status") == "ok"]
    out["tsnr"] = float(np.median([m["tsnr"] for m in runs]))
    out["runs_per_subject"] = len(runs) / len(files)
    out["volumes_per_subject"] = float(np.mean([sum(m["n_volumes"] for m in mm if m.get("status") == "ok") for mm in meta]))
    out["fd_median"] = float(np.median([m["fd_median"] for m in runs]))
    Z, S1, S2 = maps(E, NIL, mask, vox, tmask.shape)
    out["primary"] = summarise(S1, Z, NIL)
    out["secondary_threshold"] = summarise(S2, Z, NIL)
    out["axis_dice"] = axis_dice(S1, NIL)
    out["axis_dice_secondary_threshold"] = axis_dice(S2, NIL)
    out["suprathreshold_voxels_median"] = float(np.median([(S1[k] != 0).sum() for k in NIL]))
    if all(e is not None and np.isfinite(e[0].astype(np.float32)).any() for e in E2):
        E2a = np.stack(E2)
        Z2, S21, _ = maps(E2a, NIL, mask, vox, tmask.shape)
        out["task_positive"] = summarise(S21, Z2, NIL)
    # software (D3): FSL subjects only
    fi = [j for j, ok in enumerate(fsl_ok) if ok]
    if len(fi) >= 10:
        Ef = E[fi]
        mf = np.isfinite(Ef[:, FSLK[0]].astype(np.float32)).all(0) & mask
        Zs, Ss, _ = maps(Ef, FSLK + NIL_MATCH, mf, vox_all[mf], tmask.shape)
        sw = [signed_dice(Ss[a], Ss[b]) for a, b in zip(FSLK, NIL_MATCH)]
        swr = [float(np.corrcoef(Zs[a], Zs[b])[0, 1]) for a, b in zip(FSLK, NIL_MATCH)]
        conf = [signed_dice(Ss[a], Ss[b]) for a, b in itertools.combinations(NIL_MATCH, 2)]
        out["software"] = {"subjects": len(fi), "dice_fsl_vs_nilearn": sw, "corr_fsl_vs_nilearn": swr,
                           "dice_nilearn_confound_pairs": conf}
    np.savez_compressed(F.OUT / ds / "group.npz", mask=mask, z=np.stack([Z[k] for k in NIL]).astype(np.float16),
                        s1=np.stack([S1[k] for k in NIL]), s2=np.stack([S2[k] for k in NIL]))
    TG.mkdir(parents=True, exist_ok=True)
    (TG / f"{ds}.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    return out


if __name__ == "__main__":
    for ds in sys.argv[1:]:
        r = run_dataset(ds)
        print(json.dumps({k: v for k, v in r.items() if k in ("ds", "status", "N", "primary")}, default=float), flush=True)
