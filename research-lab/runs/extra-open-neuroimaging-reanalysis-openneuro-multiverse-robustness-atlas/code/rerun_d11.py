"""D11: rerun the nilearn arm for the datasets affected by the review's findings 1 and 3, keeping the FSL maps.

ds000002, ds003397 (the spec's own Derivative setting made the canonical level equal the derivative level),
ds000213 (no derivative columns for regressors named in X) and ds000148 (no cosine drift regressors) are rerun with
the fixed `firstlevel.designs()`. Every subject that has maps is recomputed with the nilearn arm only (into a staging
folder); its FSL rows (configurations 48-95 of eff and eff2), which these defects do not touch, are copied from the old
file; the old file moves to /mnt/data/omv/out_superseded_D11/<ds>/; a row is appended to firstlevel_log.csv.

  rerun_d11.py WORKERS DS [DS ...]      (subjects already rerun, per logs/rerun_d11.jsonl, are skipped)
"""
import json
import shutil
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import firstlevel as F  # noqa: E402

STAGE = Path("/mnt/data/omv/out_d11_stage")
OLD = Path("/mnt/data/omv/out_superseded_D11")
DONE_LOG = RUN / "logs" / "rerun_d11.jsonl"


def init_worker():
    from threadpoolctl import threadpool_limits
    threadpool_limits(1)                     # one BLAS thread per worker, as in driver.py


def rerun(ds, sub):
    t0 = time.time()
    try:
        F.OUT = STAGE
        res = F.run_subject(ds, sub, arms=("nilearn",), keep_bold=False)
        if res.get("status") != "ok":
            return {"ds": ds, "sub": sub, "status": res.get("status"), "error": "rerun did not produce maps"}
        new = np.load(STAGE / ds / f"sub-{sub}.npz")
        old_path = Path("/mnt/data/omv/out") / ds / f"sub-{sub}.npz"
        old = np.load(old_path)
        eff, eff2 = new["eff"].copy(), new["eff2"].copy()
        eff[48:], eff2[48:] = old["eff"][48:], old["eff2"][48:]      # FSL configurations, unchanged
        meta = str(new["meta"])
        (OLD / ds).mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_path), str(OLD / ds / old_path.name))
        tmp = old_path.with_suffix(".tmp.npz")
        np.savez_compressed(tmp, eff=eff, eff2=eff2, meta=meta)
        tmp.rename(old_path)
        (STAGE / ds / f"sub-{sub}.npz").unlink()
        return {"ds": ds, "sub": sub, "status": "ok", "runs": res.get("runs"), "t_nilearn": res.get("t_nilearn"),
                "t_total": round(time.time() - t0)}
    except Exception as e:
        return {"ds": ds, "sub": sub, "status": "failed", "error": f"{type(e).__name__}: {e}",
                "trace": traceback.format_exc()[-1500:]}


def main():
    workers = int(sys.argv[1])
    datasets = sys.argv[2:]
    done = set()
    if DONE_LOG.exists():
        for line in DONE_LOG.read_text().splitlines():
            r = json.loads(line)
            if r.get("status") == "ok":
                done.add((r["ds"], r["sub"]))
    todo = [(ds, f.stem[4:]) for ds in datasets for f in sorted((Path("/mnt/data/omv/out") / ds).glob("sub-*.npz"))
            if (ds, f.stem[4:]) not in done]
    print(f"{len(todo)} subjects to rerun on {workers} workers", flush=True)
    log_csv = RUN / "results" / "tables" / "firstlevel_log.csv"
    with ProcessPoolExecutor(workers, initializer=init_worker) as ex:
        futs = [ex.submit(rerun, ds, sub) for ds, sub in todo]
        for fut in as_completed(futs):
            r = fut.result()
            r["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(DONE_LOG, "a") as f:
                f.write(json.dumps(r) + "\n")
            if r["status"] == "ok":   # ds,sub,status,fsl,finished,error,runs,t_fetch,t_nilearn,t_fsl,runs_dropped
                with open(log_csv, "a") as f:
                    f.write(f"{r['ds']},{r['sub']},ok,False,{r['finished']},D11 rerun (nilearn arm; FSL maps kept),"
                            f"{r.get('runs', '')},,{r.get('t_nilearn', '')},0,\n")
            print(json.dumps({k: v for k, v in r.items() if k != "trace"}), flush=True)


if __name__ == "__main__":
    main()
