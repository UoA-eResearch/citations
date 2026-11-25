"""G3 follow-up (D11, after the review): does little implicit baseline go with a fragile task-positive contrast?

The draft explained the unmet expectation (task-positive contrast more robust than the primary in only 7 of 14
datasets) by designs with little rest, shown for the four sharpest drops. This tests it across all datasets with a
task-positive contrast. Per dataset, over the first 10 analysed subjects (sorted) and all their runs:
  coverage   share of the run (volumes x TR) covered by any event in the events file (union of onset..onset+duration)
  flatness   coefficient of variation (sd / mean) of the summed SPM-convolved event train at the volume times;
             low = nearly flat summed regressor, so "all conditions against baseline" is poorly separable
Events are all rows of the events file (durations missing -> 0.1 s); the specs may model a subset, so both measures
are approximations. Spearman of each against R_task_positive - R (datasets with both defined).

  g3_baseline.py -> results/tables/g3_baseline.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
from nilearn.glm.first_level.hemodynamic_models import compute_regressor  # noqa: E402

ROOT = Path("/mnt/data/omv")
T = RUN / "results" / "tables"


def tr_for(ds, sub_dir, task, bold_stem):
    for p in (sub_dir / "func" / f"{bold_stem}_bold.json", ROOT / ds / "raw" / f"task-{task}_bold.json"):
        if p.exists():
            d = json.loads(p.read_text())
            if "RepetitionTime" in d:
                return float(d["RepetitionTime"])
    return None


def dataset_measures(ds, task):
    subs = sorted(p.stem[4:] for p in (ROOT / "out" / ds).glob("sub-*.npz"))[:10]
    cov, cv = [], []
    for sub in subs:
        sd = ROOT / ds / "raw" / f"sub-{sub}"
        for ev in sorted(sd.rglob(f"sub-{sub}*_task-{task}*_events.tsv")):
            stem = ev.name[: -len("_events.tsv")]
            conf = list((ROOT / ds / "deriv" / "fmriprep" / f"sub-{sub}").rglob(f"{stem}*desc-confounds_timeseries.tsv"))
            tr = tr_for(ds, ev.parent.parent if ev.parent.name == "func" else sd, task, stem)
            if not conf or tr is None:
                continue
            nvol = sum(1 for _ in open(conf[0])) - 1
            E = pd.read_csv(ev, sep="\t", na_values="n/a")
            if not len(E) or "onset" not in E:
                continue
            on = E["onset"].to_numpy(float)
            du = E["duration"].fillna(0.1).clip(lower=0.1).to_numpy(float) if "duration" in E else np.full(len(E), 0.1)
            L = nvol * tr
            grid = np.zeros(int(np.ceil(L * 10)), bool)                  # 0.1 s grid for the union of events
            for o, d in zip(on, du):
                grid[max(0, int(o * 10)): max(0, min(len(grid), int((o + d) * 10)))] = True
            cov.append(grid.mean())
            ft = np.arange(nvol) * tr
            reg, _ = compute_regressor(np.vstack([on, du, np.ones(len(on))]), "spm", ft)
            r = reg[:, 0]
            if r.mean() > 0:
                cv.append(float(r.std() / r.mean()))
    return {"subjects": len(subs), "runs": len(cov),
            "coverage": round(float(np.median(cov)), 3) if cov else None,
            "flatness_cv": round(float(np.median(cv)), 3) if cv else None}


def main():
    A = pd.read_csv(T / "atlas.csv")
    A = A[A.R_task_positive.notna()]
    rows = []
    for _, a in A.iterrows():
        m = dataset_measures(a.ds, a.task)
        rows.append({"ds": a.ds, "R": a.R, "R_task_positive": a.R_task_positive,
                     "gap": (a.R_task_positive - a.R) if pd.notna(a.R) else None, **m})
    df = pd.DataFrame(rows)
    d = df.dropna(subset=["gap", "coverage", "flatness_cv"])
    out = {"datasets": rows,
           "spearman_gap_vs_coverage": {"rho": round(float(spearmanr(d.gap, d.coverage)[0]), 3),
                                        "p": round(float(spearmanr(d.gap, d.coverage)[1]), 3), "n": int(len(d))},
           "spearman_gap_vs_flatness_cv": {"rho": round(float(spearmanr(d.gap, d.flatness_cv)[0]), 3),
                                           "p": round(float(spearmanr(d.gap, d.flatness_cv)[1]), 3), "n": int(len(d))},
           "note": "exploratory, after the review; events from the events files, not the specs' modelled subset"}
    (T / "g3_baseline.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(df.to_string())
    print({k: v for k, v in out.items() if k.startswith("spearman")})


if __name__ == "__main__":
    main()
