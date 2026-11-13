"""Run the first level for every eligible dataset and subject (plan sections 0 and 5; D1-D3).

Subject order per dataset: one seeded permutation of the spec's subject list (seed 20261110). The first 100 are
analysed (all, if fewer); the first 20 also get the reduced FSL arm (D3). A prefetch thread downloads subjects ahead
of the workers while free space on /mnt stays above 40 GB and at most PREFETCH subjects are waiting; a process pool
of WORKERS runs firstlevel.run_subject. Completed subjects (an existing .npz with the needed maps) are skipped, so the
driver can be restarted.

  driver.py [WORKERS] [DS ...]   -> /mnt/data/omv/out/<ds>/sub-*.npz, results/tables/firstlevel_log.csv
"""
import json
import random
import shutil
import sys
import threading
import time
import traceback
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import fetch  # noqa: E402
import firstlevel as F  # noqa: E402

SEED, CAP, FSL_N, PREFETCH, MIN_FREE = 20261110, 100, 20, 6, 40e9
NIL = [k for k in range(48)]
FSLK = [F.cfg_index(1, 1, 0, c, 1) for c in range(4)]


def order(ds):
    spec, _ = F.spec_for(ds)
    subs = list(spec["Input"]["subject"])
    return random.Random(SEED).sample(subs, len(subs))


def done(ds, sub, fsl):
    f = F.OUT / ds / f"sub-{sub}.npz"
    if not f.exists():
        return False
    e = np.load(f)["eff"]
    need = NIL + (FSLK if fsl else [])
    return all(np.isfinite(e[k].astype(np.float32)).any() for k in need)


def work(args):
    ds, sub, fsl = args
    try:
        return F.run_subject(ds, sub, arms=("nilearn", "FSL") if fsl else ("nilearn",))
    except Exception as e:
        return {"ds": ds, "sub": sub, "status": "failed", "error": f"{type(e).__name__}: {e}"[:400],
                "trace": traceback.format_exc()[-1500:]}


def main():
    a = sys.argv[1:]
    workers = int(a[0]) if a and a[0].isdigit() else 12
    only = [x for x in a if x.startswith("ds")]
    E = pd.read_csv(RUN / "results" / "tables" / "eligible.csv")
    E = E[E.status == "eligible"]
    queue = []
    for r in E.itertuples():
        if only and r.ds not in only:
            continue
        for j, sub in enumerate(order(r.ds)[:CAP]):
            fsl = j < FSL_N
            if not done(r.ds, sub, fsl):
                queue.append((r.ds, sub, fsl, r.task))
    print(f"{len(queue)} subjects to run on {workers} workers", flush=True)
    fetched, lock = set(), threading.Lock()

    def prefetch():
        for ds, sub, fsl, task in queue:
            while True:
                with lock:
                    waiting = len(fetched)
                if waiting < PREFETCH and shutil.disk_usage("/mnt").free > MIN_FREE:
                    break
                time.sleep(20)
            try:
                fetch.fetch_subject(ds, sub, task)
            except Exception:
                pass
            with lock:
                fetched.add((ds, sub))
    threading.Thread(target=prefetch, daemon=True).start()
    log = RUN / "results" / "tables" / "firstlevel_log.csv"
    rows = pd.read_csv(log).to_dict("records") if log.exists() else []
    pending = list(queue)
    with ProcessPoolExecutor(workers) as ex:
        futs = {}
        while pending or futs:
            while pending and len(futs) < workers:
                with lock:
                    ready = [q for q in pending if (q[0], q[1]) in fetched]
                if not ready:
                    break
                q = ready[0]
                pending.remove(q)
                futs[ex.submit(work, q[:3])] = q
            if not futs:
                time.sleep(10)
                continue
            finished, _ = wait(list(futs), timeout=30, return_when=FIRST_COMPLETED)
            for f in finished:
                q = futs.pop(f)
                r = f.result()
                r["fsl"] = q[2]
                r["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
                rows.append({k: v for k, v in r.items() if k != "trace"})
                with lock:
                    fetched.discard((q[0], q[1]))
                pd.DataFrame(rows).to_csv(log, index=False)
                print(json.dumps({k: v for k, v in r.items() if k != "trace"}), flush=True)
                if r["status"] == "failed":
                    print(r.get("trace", ""), flush=True)


if __name__ == "__main__":
    main()
