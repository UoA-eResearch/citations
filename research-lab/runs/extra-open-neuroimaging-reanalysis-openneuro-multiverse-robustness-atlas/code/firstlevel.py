"""First level for one subject: 48 nilearn and 48 FSL configurations (plan section 0; D1, D2).

Design. pybids (pinned to openneuro_glmfitlins' commit) applies the spec's run-level transformations to the events,
after the project's own per-dataset events preparation (`code/vendor_glmfitlins/modify_events.py`, MIT licence) when
the spec's basic details ask for it. The spec's motion terms (trans_*, rot_*) are removed from X; the task regressors,
intercept and cosine drift regressors stay. Each configuration then appends one confound set from fMRIPrep's table.

Configuration index (0..95): software (0 nilearn, 1 FSL) * 48 + smoothing (4, 6, 8 mm) * 16 + HRF (canonical,
+ temporal derivative) * 8 + confounds (6P, 24P, 24P+aCompCor5, 6P+spikes) * 2 + noise (nilearn: AR(1), OLS;
FSL: FILM prewhitening, none).

nilearn arm: Gaussian smoothing (nilearn), the run's fMRIPrep brain mask, percent-signal scaling, `run_glm`.
FSL arm (Docker image omv-fsl:6.0.7-slim): FEAT's pre-stats on preprocessed data (mask, SUSAN with FEAT's brightness
threshold, grand-mean scaling to 10,000, `-bptf` high-pass at 128 s with the mean added back), then for each design
`feat_model` (double-gamma HRF, optional temporal derivative, 3-column EVs from the pre-convolution pybids variables,
EV high-pass, confound EVs) and `film_gls` with or without prewhitening.
Both arms: run-level contrast effect and variance, fixed effects across the subject's runs per configuration.

  firstlevel.py DS SUB [--timing]   -> /mnt/data/omv/out/<ds>/sub-<sub>.npz (eff[96, V] float16 within the template
                                       mask, NaN outside the subject's mask; per-run metadata)
"""
import copy
import json
import math
import subprocess
import sys
import time
import warnings
from pathlib import Path

import nibabel as nb
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
sys.path.insert(0, str(RUN / "code" / "vendor_glmfitlins"))
import fetch  # noqa: E402

OUT = fetch.ROOT / "out"
TEMPLATE = RUN / "data" / "template" / "MNI152NLin2009cAsym_res-02_desc-brain_mask.nii.gz"
SMOOTH, HRFS, CONFS, NOISE = (4, 6, 8), ("canonical", "derivative"), ("6P", "24P", "24P+aCompCor", "6P+spikes"), (0, 1)
IMAGE = "omv-fsl:6.0.7-slim"
MOTION = ["trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z"]


def cfg_index(sw, si, hi, ci, ni):
    return sw * 48 + si * 16 + hi * 8 + ci * 2 + ni


def cfg_label(k):
    sw, r = divmod(k, 48)
    si, r = divmod(r, 16)
    hi, r = divmod(r, 8)
    ci, ni = divmod(r, 2)
    noise = ("AR1", "OLS")[ni] if sw == 0 else ("prewhiten", "noprewhiten")[ni]
    return {"software": ("nilearn", "FSL")[sw], "smoothing": SMOOTH[si], "hrf": HRFS[hi], "confounds": CONFS[ci], "noise": noise}


def spec_for(ds):
    spec = json.loads(next((RUN / "data" / "specs" / ds).glob("*_specs.json")).read_text())
    details = json.loads((RUN / "data" / "specs" / ds / f"{ds}_basic-details.json").read_text())
    return spec, details


def prepare_events(ds, task, runs, details):
    """openneuro_glmfitlins' per-dataset events preparation, applied once per events file."""
    if not details.get("Tasks", {}).get(task, {}).get("preproc_events"):
        return
    import inspect
    import modify_events
    fn = getattr(modify_events, ds)
    for r in runs:
        flag = Path(str(r["events"]) + ".prepared")
        if flag.exists():
            continue
        kw = {"eventspath": str(r["events"]), "task": task}
        if "bids_layout" in inspect.signature(fn).parameters:
            from bids import BIDSLayout
            kw["bids_layout"] = BIDSLayout(fetch.ROOT / ds / "raw", validate=False)
        out = fn(**kw)
        if out is not None:
            out.to_csv(r["events"], sep="\t", index=False)
        flag.write_text("ok")


def designs(ds, sub, spec, derivative):
    """-> {run: {"X": task design (DataFrame, dense at TR), "con": weights over X columns, "evs": pre-convolution
    variables for FSL [(name, onset, duration, value)], "dense_other": [names of non-convolved task columns]}}"""
    from bids import BIDSLayout
    from bids.modeling import BIDSStatsModelsGraph
    s = copy.deepcopy(spec)
    node = next(n for n in s["Nodes"] if n["Level"].lower() == "run")
    s["Nodes"], s["Input"]["subject"] = [node], [sub]
    s.pop("Edges", None)
    node["Model"]["X"] = [x for x in node["Model"]["X"] if not (isinstance(x, str) and (x.startswith("trans_") or x.startswith("rot_")))]
    for ins in node.get("Transformations", {}).get("Instructions", []):
        if ins["Name"] == "Convolve":
            ins["Model"] = "spm"
            if derivative:
                ins["Derivative"] = True
    if derivative:                       # wildcard entries (e.g. trial_type.*) already pick up the derivative columns
        conv = {c for ins in node.get("Transformations", {}).get("Instructions", []) if ins["Name"] == "Convolve"
                for c in ins.get("Input", [])}
        node["Model"]["X"] += [x + "_derivative" for x in list(node["Model"]["X"])
                               if isinstance(x, str) and "*" not in x and x in conv]
    node["Contrasts"] = node["Contrasts"][:1]
    lay = BIDSLayout(fetch.ROOT / ds / "raw", derivatives=[fetch.ROOT / ds / "deriv" / "fmriprep"], validate=False)
    g = BIDSStatsModelsGraph(lay, s)
    g.load_collections(subject=[sub])
    out = {}
    for o in g.root_node.run(group_by=node["GroupBy"], force_dense=True, transformation_history=True):
        X = o.X.copy()
        con = o.contrasts[0]
        w = pd.Series(0.0, index=X.columns)
        for c, wt in zip(con.conditions, con.weights):
            w[c] = wt
        hist = o.trans_hist
        ci = max(i for i, h in enumerate(hist) if h.transformation_name == "Convolve")
        pre = hist[ci - 1].output.variables
        import fnmatch                           # Convolve's input_cols keep wildcards such as trial_type.*
        convolved = {v for pat in hist[ci].input_cols for v in pre if fnmatch.fnmatchcase(v, pat)}
        evs = []
        for name in X.columns:
            if name in convolved and name in pre and hasattr(pre[name], "onset"):
                v = pre[name]
                vals = v.values.values if hasattr(v.values, "values") else np.asarray(v.values)
                evs.append((name, np.asarray(v.onset, float), np.asarray(v.duration, float), np.asarray(vals, float)))
        other = [c for c in X.columns if c not in convolved and c != "intercept" and not c.startswith("cosine")
                 and not c.endswith("_derivative")]
        out[int(o.entities.get("run", 1))] = {"X": X, "con": w, "evs": evs, "dense_other": other,
                                             "contrast": con.name}
    return out


def confound_sets(conf_path):
    C = pd.read_csv(conf_path, sep="\t")
    six = C[MOTION]
    d1 = C[[m + "_derivative1" for m in MOTION]]
    p2 = C[[m + "_power2" for m in MOTION]]
    d1p2 = C[[m + "_derivative1_power2" for m in MOTION]]
    p24 = pd.concat([six, d1, p2, d1p2], axis=1)
    acc = C[[f"a_comp_cor_{k:02d}" for k in range(5)]]
    fd = C["framewise_displacement"].fillna(0).to_numpy()
    spikes = pd.DataFrame({f"spike{j:03d}": (np.arange(len(C)) == j).astype(float) for j in np.where(fd > 0.5)[0]})
    sets = {"6P": six, "24P": p24, "24P+aCompCor": pd.concat([p24, acc], axis=1),
            "6P+spikes": pd.concat([six, spikes], axis=1) if len(spikes.columns) else six}
    return {k: v.fillna(0).reset_index(drop=True) for k, v in sets.items()}, float(np.median(fd)), int((fd > 0.5).sum())


def tsnr(bold, mask, X_cos):
    Y = bold[mask].T.astype(np.float64)                                  # T x V
    if X_cos.shape[1]:
        B = np.linalg.lstsq(X_cos, Y - Y.mean(0), rcond=None)[0]
        R = Y - Y.mean(0) - X_cos @ B
    else:
        R = Y - Y.mean(0)
    sd = R.std(0)
    ok = sd > 0
    return float(np.median(Y.mean(0)[ok] / sd[ok]))


def nilearn_arm(bold, affine, rmask, D, confs, tmask):
    from nilearn.glm.contrasts import compute_contrast
    from nilearn.glm.first_level import run_glm
    from nilearn.image.image import smooth_array
    keep = rmask[tmask]                                                  # template voxels inside this run's mask
    res = {}
    for si, fwhm in enumerate(SMOOTH):
        data = smooth_array(bold, affine, fwhm=fwhm, ensure_finite=True, copy=True)   # float32 kept
        Y = data[tmask][keep].T                                          # T x V(run)
        m = Y.mean(0)
        ok = m > 0
        Y = np.where(ok, (Y / np.where(ok, m, 1) - 1) * 100, 0).astype(np.float32)
        del data
        for hi, hrf in enumerate(HRFS):
            d = D[hrf]
            for ci, cname in enumerate(CONFS):
                X = pd.concat([d["X"].reset_index(drop=True), confs[cname].add_prefix("conf_")], axis=1)
                cv = np.r_[d["con"].to_numpy(), np.zeros(confs[cname].shape[1])]
                for ni, noise in enumerate(("ar1", "ols")):
                    labels, results = run_glm(Y, X.to_numpy(), noise_model=noise, n_jobs=1)
                    c = compute_contrast(labels, results, cv, stat_type="t")
                    eff = np.full(tmask.sum(), np.nan, np.float32)
                    var = np.full(tmask.sum(), np.nan, np.float32)
                    eff[keep], var[keep] = c.effect_size().ravel(), c.effect_variance().ravel()
                    res[cfg_index(0, si, hi, ci, ni)] = (eff, var)
    return res


FSF_HEAD = """set fmri(version) 6.00
set fmri(level) 1
set fmri(analysis) 2
set fmri(relative_yn) 0
set fmri(help_yn) 1
set fmri(featwatcher_yn) 0
set fmri(sscleanup_yn) 0
set fmri(tr) {tr}
set fmri(npts) {npts}
set fmri(ndelete) 0
set fmri(tagfirst) 1
set fmri(multiple) 1
set fmri(inputtype) 2
set fmri(filtering_yn) 0
set fmri(brain_thresh) 10
set fmri(critical_z) 5.3
set fmri(noise) 0.66
set fmri(noisear) 0.34
set fmri(mc) 0
set fmri(sh_yn) 0
set fmri(regunwarp_yn) 0
set fmri(dwell) 0.7
set fmri(te) 35
set fmri(signallossthresh) 10
set fmri(unwarp_dir) y-
set fmri(st) 0
set fmri(bet_yn) 0
set fmri(smooth) 0
set fmri(norm_yn) 0
set fmri(perfsub_yn) 0
set fmri(temphp_yn) 1
set fmri(templp_yn) 0
set fmri(melodic_yn) 0
set fmri(stats_yn) 1
set fmri(prewhiten_yn) {prewhiten}
set fmri(motionevs) 0
set fmri(motionevsbeta) ""
set fmri(scriptevsbeta) ""
set fmri(robust_yn) 0
set fmri(mixed_yn) 2
set fmri(randomisePermutations) 5000
set fmri(evs_orig) {evs_orig}
set fmri(evs_real) {evs_real}
set fmri(evs_vox) 0
set fmri(ncon_orig) 1
set fmri(ncon_real) 1
set fmri(nftests_orig) 0
set fmri(nftests_real) 0
set fmri(constcol) 0
set fmri(poststats_yn) 0
set fmri(threshmask) ""
set fmri(thresh) 0
set fmri(prob_thresh) 0.05
set fmri(z_thresh) 3.1
set fmri(paradigm_hp) 128
set fmri(totalVoxels) 0
set fmri(confoundevs) 1
set confoundev_files(1) "{confounds}"
"""


def write_fsf(path, tr, npts, evs, ev_dir, deriv, confounds_file, con_weights, prewhiten):
    """evs: [(name, kind, file)] kind 3 = three-column (convolved, double gamma), 2 = one value per volume (not
    convolved). con_weights: weight per original EV."""
    n = len(evs)
    real = sum(2 if (deriv and k == 3) else 1 for _, k, _ in evs)
    s = FSF_HEAD.format(tr=f"{tr:.6f}", npts=npts, prewhiten=int(prewhiten), evs_orig=n, evs_real=real, confounds=confounds_file)
    for i, (name, kind, f) in enumerate(evs, 1):
        s += (f'set fmri(evtitle{i}) "{name}"\nset fmri(shape{i}) {kind}\nset fmri(convolve{i}) {3 if kind == 3 else 0}\n'
              f'set fmri(convolve_phase{i}) 0\nset fmri(tempfilt_yn{i}) 1\nset fmri(deriv_yn{i}) {int(deriv and kind == 3)}\n'
              f'set fmri(custom{i}) "{f}"\n')
        for j in range(n + 1):
            s += f"set fmri(ortho{i}.{j}) 0\n"
    s += 'set fmri(con_mode_old) real\nset fmri(con_mode) real\nset fmri(conpic_real.1) 1\nset fmri(conname_real.1) "c1"\n'
    k = 1
    for i, (_, kind, _) in enumerate(evs):
        s += f"set fmri(con_real1.{k}) {con_weights[i]}\n"
        k += 1
        if deriv and kind == 3:
            s += f"set fmri(con_real1.{k}) 0\n"
            k += 1
    s += 'set fmri(conpic_orig.1) 1\nset fmri(conname_orig.1) "c1"\n'
    for i in range(n):
        s += f"set fmri(con_orig1.{i + 1}) {con_weights[i]}\n"
    Path(path).write_text(s)


def fsl_arm(run, D, confs, tmask, work, timing, reduced=True):
    """FSL configurations for one run in one container. reduced (D3): 6 mm, canonical, 4 confound sets, no
    prewhitening. -> {cfg: (eff, var)}"""
    work.mkdir(parents=True, exist_ok=True)
    img = nb.load(run["bold"])
    npts, tr = img.shape[3], float(run["tr"])
    jobs = []
    for hi, hrf in enumerate(HRFS):
        d = D[hrf]
        evs, weights = [], []
        for name, on, du, va in D["canonical"]["evs"]:
            f = work / f"ev_{len(evs):02d}.txt"
            np.savetxt(f, np.c_[on, du, va], fmt="%.6f")
            evs.append((name, 3, f"/work/{f.name}"))
            weights.append(float(d["con"].get(name, 0.0)))
        for name in D["canonical"]["dense_other"]:
            f = work / f"evd_{len(evs):02d}.txt"
            np.savetxt(f, d["X"][name].to_numpy(), fmt="%.6f")
            evs.append((name, 2, f"/work/{f.name}"))
            weights.append(float(d["con"].get(name, 0.0)))
        for ci, cname in enumerate(CONFS):
            cf = work / f"conf_{ci}.txt"
            np.savetxt(cf, confs[cname].to_numpy(), fmt="%.6f")
            for ni, pw in enumerate((1, 0)):
                if reduced and (hi != 0 or ni != 1):
                    continue
                tag = f"h{hi}c{ci}n{ni}"
                write_fsf(work / f"{tag}.fsf", tr, npts, evs, work, hrf == "derivative", f"/work/{cf.name}", weights, pw)
                jobs.append((tag, hi, ci, ni, pw))
    lines = ["set -e", "cd /work",
             "fslmaths /in/bold -mas /in/mask prefiltered", "fslmaths prefiltered -Tmean mean_func",
             "MED=$(fslstats prefiltered -k /in/mask -p 50)", "BT=$(awk -v m=$MED 'BEGIN{print m*0.75}')"]
    sis = [1] if reduced else list(range(len(SMOOTH)))
    for si in sis:
        fwhm = SMOOTH[si]
        sig = fwhm / 2.355
        hp = 128.0 / (2.0 * tr)
        lines += [f"susan prefiltered $BT {sig:.4f} 3 1 1 mean_func $BT sm{si}",
                  f"fslmaths sm{si} -mas /in/mask sm{si}",
                  f"M2=$(fslstats sm{si} -k /in/mask -p 50); SC=$(awk -v m=$M2 'BEGIN{{print 10000/m}}')",
                  f"fslmaths sm{si} -mul $SC in{si}", f"fslmaths in{si} -Tmean tm{si}",
                  f"fslmaths in{si} -bptf {hp:.4f} -1 -add tm{si} ff{si}", f"rm -f sm{si}.nii.gz in{si}.nii.gz tm{si}.nii.gz"]
        for tag, hi, ci, ni, pw in jobs:
            out = f"s{si}{tag}"
            lines += [f"cp {tag}.fsf {out}.fsf", f"feat_model {out} conf_{ci}.txt > /dev/null",
                      f"film_gls --in=ff{si} --rn={out}_stats --pd={out}.mat --thr=1000 --con={out}.con "
                      + ("--sa --ms=5" if pw else "--noest") + " > /dev/null",
                      f"mv {out}_stats/cope1.nii.gz {out}_cope.nii.gz; mv {out}_stats/varcope1.nii.gz {out}_varcope.nii.gz; rm -rf {out}_stats"]
        lines += [f"rm -f ff{si}.nii.gz"]
        if timing:
            lines += [f"echo smoothing {si} done $(date +%s)"]
    (work / "run.sh").write_text("\n".join(lines) + "\n")
    import os
    cmd = ["docker", "run", "--rm", "--user", f"{os.getuid()}:{os.getgid()}", "--cpus", "1",
           "-v", f"{work}:/work", "-v", f"{Path(run['bold']).parent}:/indir:ro", "-e", "FSLOUTPUTTYPE=NIFTI_GZ",
           IMAGE, "bash", "-c",
           f"mkdir -p /tmp/in && ln -s /indir/{Path(run['bold']).name} /tmp/in/bold.nii.gz && "
           f"ln -s /indir/{Path(run['mask']).name} /tmp/in/mask.nii.gz && sed -i 's#/in/#/tmp/in/#g' /work/run.sh && bash /work/run.sh"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError("FSL arm failed: " + p.stderr[-800:])
    if timing:
        print(p.stdout.strip(), flush=True)
    rmask = nb.load(run["mask"]).get_fdata() > 0
    keep = rmask[tmask]
    res = {}
    for si in sis:
        for tag, hi, ci, ni, pw in jobs:
            out = f"s{si}{tag}"
            e = nb.load(work / f"{out}_cope.nii.gz").get_fdata(dtype=np.float32)[tmask]
            v = nb.load(work / f"{out}_varcope.nii.gz").get_fdata(dtype=np.float32)[tmask]
            e[~keep], v[~keep] = np.nan, np.nan
            res[cfg_index(1, si, hi, ci, ni)] = (e, v)
    for f in work.glob("*.nii.gz"):
        f.unlink()
    return res


def fixed_effects(per_run):
    """per_run: list of {cfg: (eff, var)} -> {cfg: eff}"""
    out = {}
    for k in per_run[0]:
        E = np.stack([r[k][0] for r in per_run])
        V = np.stack([r[k][1] for r in per_run])
        W = np.where(np.isfinite(V) & (V > 0), 1.0 / np.where(V > 0, V, 1), np.nan)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[k] = np.nansum(W * E, 0) / np.nansum(W, 0)
        out[k][~np.isfinite(out[k])] = np.nan
    return out


def run_subject(ds, sub, arms=("nilearn", "FSL"), timing=False, keep_bold=False, fsl_reduced=True):
    E = pd.read_csv(RUN / "results" / "tables" / "eligible.csv").set_index("ds")
    task = E.loc[ds, "task"]
    spec, details = spec_for(ds)
    dest = OUT / ds / f"sub-{sub}.npz"
    dest.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    runs = fetch.fetch_subject(ds, sub, task)
    t_fetch = time.time() - t0
    if not runs:
        return {"ds": ds, "sub": sub, "status": "no usable run"}
    prepare_events(ds, task, runs, details)
    D = {"canonical": designs(ds, sub, spec, False), "derivative": designs(ds, sub, spec, True)}
    tmask = nb.load(TEMPLATE).get_fdata() > 0
    per_run, meta = [], []
    t_nil = t_fsl = 0.0
    for r in runs:
        rn = int(dict(fetch.ents(r["stem"])).get("run", 1))
        if rn not in D["canonical"]:
            meta.append({"run": rn, "status": "no design"}); continue
        Dr = {h: D[h][rn] for h in HRFS}
        confs, fd_med, n_spk = confound_sets(r["confounds"])
        img = nb.load(r["bold"])
        bold = img.get_fdata(dtype=np.float32)
        rmask = nb.load(r["mask"]).get_fdata() > 0
        cos = Dr["canonical"]["X"][[c for c in Dr["canonical"]["X"].columns if c.startswith("cosine")]].to_numpy()
        ts = tsnr(bold, rmask, cos)
        res = {}
        if "nilearn" in arms:
            t1 = time.time(); res.update(nilearn_arm(bold, img.affine, rmask, Dr, confs, tmask)); t_nil += time.time() - t1
        del bold
        if "FSL" in arms:
            t1 = time.time(); res.update(fsl_arm(r, Dr, confs, tmask, OUT / ds / "work" / f"sub-{sub}_run-{rn}", timing, reduced=fsl_reduced)); t_fsl += time.time() - t1
        per_run.append(res)
        meta.append({"run": rn, "status": "ok", "tsnr": ts, "fd_median": fd_med, "n_spikes": n_spk,
                     "n_volumes": int(len(confs["6P"])), "n_evs": len(Dr["canonical"]["evs"]),
                     "contrast": Dr["canonical"]["contrast"]})
    if not per_run:
        return {"ds": ds, "sub": sub, "status": "no run with a design"}
    ff = fixed_effects(per_run)
    eff = np.full((96, tmask.sum()), np.nan, np.float16)
    if dest.exists():                                   # keep maps already computed (e.g. the timing run's)
        eff = np.load(dest)["eff"]
    for k, v in ff.items():
        eff[k] = v.astype(np.float16)
    np.savez_compressed(dest, eff=eff, meta=json.dumps(meta))
    if not keep_bold:
        fetch.drop_subject(ds, sub)
    out = {"ds": ds, "sub": sub, "status": "ok", "runs": len(per_run), "t_fetch": round(t_fetch), "t_nilearn": round(t_nil),
           "t_fsl": round(t_fsl)}
    return out


if __name__ == "__main__":
    a = sys.argv
    print(json.dumps(run_subject(a[1], a[2], timing="--timing" in a, keep_bold="--keep" in a, fsl_reduced="--full-fsl" not in a)))
