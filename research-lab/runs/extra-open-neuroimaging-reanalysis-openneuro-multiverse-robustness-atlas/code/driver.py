"""Run the first level for every eligible dataset and subject (plan sections 0 and 5; D1-D3).

Subject order per dataset: one seeded permutation of the spec's subject list (seed 20261110). The first 100 are
analysed (all, if fewer); the first 20 also get the reduced FSL arm (D3). A prefetch thread downloads subjects ahead
of the workers within a disk budget: a subject is fetched only if the BOLD of all fetched-but-unfinished subjects
stays within BUDGET and at least MIN_FREE remains free on /mnt; it takes the first queued subject that fits, so large
subjects (ds001734, about 5.7 GB each) never crowd out the small ones. ds001734 is queued first, while the disk is
emptiest. A process pool of WORKERS runs firstlevel.run_subject. Completed subjects (an existing .npz with the needed maps) are skipped, so the
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

SEED, CAP, FSL_N, BUDGET, MIN_FREE = 20261110, 100, 20, 25e9, 8e9
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
    E = pd.concat([E[E.ds == "ds001734"], E[E.ds != "ds001734"]])
    for r in E.itertuples():
        if only and r.ds not in only:
            continue
        for j, sub in enumerate(order(r.ds)[:CAP]):
            fsl = j < FSL_N
            if not done(r.ds, sub, fsl):
                queue.append((r.ds, sub, fsl, r.task))
    print(f"{len(queue)} subjects to run on {workers} workers", flush=True)
    fetched, lock = {}, threading.Lock()          # (ds, sub) -> bytes, for fetched-but-unfinished subjects

    todo, size, reserved = list(queue), {}, {}

    def prefetch():
        while True:
            with lock:
                if not todo:
                    return
                inflight = sum(fetched.values()) + sum(reserved.values())
                free = shutil.disk_usage("/mnt").free - sum(reserved.values())
                pick = None
                for q in todo:
                    if q not in size:
                        size[q] = fetch.subject_bytes(q[0], q[1], q[3])
                    if inflight + size[q] <= BUDGET and free - size[q] >= MIN_FREE:
                        pick = q
                        break
                if pick is not None:
                    todo.remove(pick)
                    reserved[pick] = size[pick]
            if pick is None:
                time.sleep(30)
                continue
            try:
                fetch.fetch_subject(pick[0], pick[1], pick[3])
            except Exception:
                pass
            with lock:
                reserved.pop(pick, None)
                fetched[(pick[0], pick[1])] = size[pick]

    for _ in range(4):                            # 4 subjects downloading at once, ~128 connections
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
                    fetched.pop((q[0], q[1]), None)
                pd.DataFrame(rows).to_csv(log, index=False)
                print(json.dumps({k: v for k, v in r.items() if k != "trace"}), flush=True)
                if r["status"] == "failed":
                    print(r.get("trace", ""), flush=True)


if __name__ == "__main__":
    main()
