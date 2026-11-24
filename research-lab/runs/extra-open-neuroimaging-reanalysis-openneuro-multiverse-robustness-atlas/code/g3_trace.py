"""G3 plausibility traces (plan section 4), with seeded random choices (seed 20261110).

1. One random analysed subject and one random nilearn configuration: the subject's BOLD is fetched again, the
   design matrix of its first run is dumped (columns, events per condition in the events file, contrast weights,
   confound columns of the configuration), the subject's first level is rerun into a temporary folder and compared
   with the stored maps (all 48 nilearn configurations), and the stored map's peak is reported in MNI coordinates.
2. Three random datasets: the group map of the spec-closest configuration (16) is recomputed from the stored
   subject maps and compared with group.npz; the number of subjects is reconciled with the first-level log and
   the atlas; the group peak is reported in MNI coordinates.

  g3_trace.py -> results/tables/g3_trace.json
The stored outputs are not modified.
"""
import json
import sys
import tempfile
from pathlib import Path

import nibabel as nb
import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import fetch  # noqa: E402
import firstlevel as F  # noqa: E402
import grouplevel as G  # noqa: E402

SEED = 20261110
CFG = F.cfg_index(0, 1, 0, 0, 0)


def mni(vox_index, tvox, affine):
    return [round(float(c), 1) for c in nb.affines.apply_affine(affine, tvox[vox_index])]


def subject_trace(rng, tvox, affine):
    log = pd.read_csv(RUN / "results" / "tables" / "firstlevel_log.csv", dtype=str)
    last = log.drop_duplicates(["ds", "sub"], keep="last")
    ok = last[last.status == "ok"].sort_values(["ds", "sub"]).reset_index(drop=True)
    pick = ok.iloc[int(rng.integers(len(ok)))]
    ds, sub = pick.ds, pick["sub"]
    k = int(rng.integers(48))
    label = F.cfg_label(k)
    E = pd.read_csv(RUN / "results" / "tables" / "eligible.csv").set_index("ds")
    task = E.loc[ds, "task"]
    spec, details = F.spec_for(ds)
    runs = fetch.fetch_subject(ds, sub, task)
    F.prepare_events(ds, task, runs, details)
    F.normalise_events(spec, runs)
    D = F.designs(ds, sub, spec, label["hrf"] == "derivative")
    r = runs[0]
    rn = int(dict(fetch.ents(r["stem"])).get("run", 1))
    X = D[rn]["X"]
    ev = pd.read_csv(r["events"], sep="\t", na_values="n/a")
    confs, fd_med, n_spk = F.confound_sets(r["confounds"])
    C = confs[label["confounds"]]
    design = {
        "run": rn, "n_volumes": int(len(C)), "tr": float(r["tr"]),
        "task_columns": [c for c in X.columns if not c.startswith("cosine")],
        "cosine_columns": sum(c.startswith("cosine") for c in X.columns),
        "contrast": {c: float(w) for c, w in zip(X.columns, D[rn]["con"]) if w != 0},
        "events_per_trial_type": ev["trial_type"].value_counts().to_dict() if "trial_type" in ev else {},
        "confound_columns": list(C.columns) if hasattr(C, "columns") else int(np.asarray(C).shape[1]),
        "fd_median": round(float(fd_med), 4), "spikes": int(n_spk),
        # the task regressors should rise after event onsets: correlation of each convolved task column with the
        # boxcar of its own trial type, shifted 5 s (the HRF peak)
    }
    # rerun the subject's first level into a temporary folder (stored maps untouched)
    stored = np.load(F.OUT / ds / f"sub-{sub}.npz")["eff"].astype(np.float32)
    real_out = F.OUT
    with tempfile.TemporaryDirectory(dir="/mnt/data/omv") as tmp:
        F.OUT = Path(tmp)
        try:
            res = F.run_subject(ds, sub, arms=("nilearn",), keep_bold=False)
            new = np.load(Path(tmp) / ds / f"sub-{sub}.npz")["eff"].astype(np.float32)
        finally:
            F.OUT = real_out
    diffs = [float(np.nanmax(np.abs(new[j] - stored[j]))) for j in range(48)]
    v = stored[k]
    peak = int(np.nanargmax(np.abs(v)))
    return {"dataset": ds, "subject": sub, "configuration": k, "label": label, "design_first_run": design,
            "rerun_status": res.get("status"), "rerun_max_abs_diff_48_configs": max(diffs),
            "stored_map": {"finite_voxels": int(np.isfinite(v).sum()), "peak_value": round(float(v[peak]), 3),
                           "peak_mni": mni(peak, tvox, affine), "abs_95th_percentile": round(float(np.nanpercentile(np.abs(v), 95)), 3)}}


def dataset_trace(ds, tvox, affine, atlas):
    log = pd.read_csv(RUN / "results" / "tables" / "firstlevel_log.csv", dtype=str)
    last = log[log.ds == ds].drop_duplicates("sub", keep="last")
    n_log = int((last.status == "ok").sum())
    files = sorted((F.OUT / ds).glob("sub-*.npz"))
    E = []
    for f in files:
        e = np.load(f)["eff"]
        if all(np.isfinite(e[j].astype(np.float32)).any() for j in G.NIL):
            E.append(e[CFG])
    E = np.stack(E)
    g = np.load(F.OUT / ds / "group.npz")
    mask = g["mask"]
    z_re, p = G.onesample(E[:, mask].astype(np.float32))
    z_st = g["z"][CFG].astype(np.float32)
    peak = int(np.argmax(np.abs(z_st)))
    vox_index = np.nonzero(mask)[0][peak]
    n_atlas = int(atlas.loc[ds, "N"])
    return {"dataset": ds, "subjects_npz_complete": len(E), "subjects_ok_in_log": n_log, "N_in_atlas": n_atlas,
            "reconciles": len(E) == n_log == n_atlas,
            "group_z_max_abs_diff": round(float(np.max(np.abs(z_re - z_st))), 4),   # float16 storage: ~1e-2 at z~10
            "fdr_voxels": int((G.fdr(p)).sum()), "stored_fdr_voxels": int((g["s1"][CFG] != 0).sum()),
            "peak_z": round(float(z_st[peak]), 2), "peak_mni": mni(vox_index, tvox, affine)}


def main():
    rng = np.random.default_rng(SEED)
    tmpl = nb.load(F.TEMPLATE)
    tvox = np.argwhere(np.asarray(tmpl.dataobj) > 0)
    atlas = pd.read_csv(RUN / "results" / "tables" / "atlas.csv").set_index("ds")
    out = {"seed": SEED}
    datasets = sorted(atlas.index)
    picks = [datasets[i] for i in rng.choice(len(datasets), 3, replace=False)]
    out["datasets"] = [dataset_trace(ds, tvox, tmpl.affine, atlas) for ds in picks]
    out["subject"] = subject_trace(rng, tvox, tmpl.affine)
    (RUN / "results" / "tables" / "g3_trace.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
