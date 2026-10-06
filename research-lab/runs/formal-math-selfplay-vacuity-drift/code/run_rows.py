"""Parallel driver: run check_row over a parquet sample with W REPL workers, appending results to a JSONL file
(resumable: row_ids already present are skipped). Usage:
  run_rows.py <sample.parquet> <out.jsonl> <workers> [--trivial-iters a-b,c-d] [--filter "<pandas query>"] [--quiet]
--quiet prints only throughput and re-verification/split rates (used for the timing pilot, whose vacuity outcomes are
not read)."""
import argparse
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lean_repl import Repl  # noqa: E402
from vacuity import check_row  # noqa: E402

_repl = None


def init():
    global _repl
    _repl = Repl()


def work(item):
    rid, prompt, target, trivial = item
    t0 = time.time()
    try:
        o = check_row(_repl, prompt, target, trivial=trivial)
    except Exception as e:  # noqa: BLE001
        o = dict(worker_error=repr(e)[:300])
        try:
            _repl.restart()
        except Exception:  # noqa: BLE001
            pass
    o["row_id"], o["wall_s"] = int(rid), time.time() - t0
    return o


def in_ranges(it, spec):
    if not spec:
        return False
    for part in spec.split(","):
        a, b = map(float, part.split("-"))
        if a <= it <= b:
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sample"); ap.add_argument("out"); ap.add_argument("workers", type=int)
    ap.add_argument("--trivial-iters", default=""); ap.add_argument("--filter", default=""); ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--ids", default="", help="file with one row_id per line; only these rows are run (D7 fallback pass)")
    a = ap.parse_args()
    df = pd.read_parquet(a.sample)
    if a.filter:
        df = df.query(a.filter)
    if a.ids:
        df = df[df.row_id.isin({int(x) for x in open(a.ids).read().split()})]
    out = Path(a.out)
    done = set()
    if out.exists():
        done = {json.loads(line)["row_id"] for line in out.open()}
    todo = df[~df.row_id.isin(done)]
    items = [(r.row_id, r.prompt, r.target, in_ranges(r.iteration, a.trivial_iters)) for r in todo.itertuples()]
    print(f"{len(df)} rows, {len(done)} done, {len(items)} to run, {a.workers} workers", flush=True)
    t0, n, rv, sp = time.time(), 0, 0, 0
    with mp.Pool(a.workers, initializer=init) as pool, out.open("a") as f:
        for o in pool.imap_unordered(work, items, chunksize=1):
            f.write(json.dumps(o) + "\n"); f.flush()
            n += 1; rv += bool(o.get("reverify")); sp += bool(o.get("split_ok"))
            if n % 200 == 0 or n == len(items):
                el = time.time() - t0
                print(f"{n}/{len(items)} rows | {el/3600:.2f} h | {n/el*3600:.0f} rows/h | reverify {rv/n:.3f} | split {sp/n:.3f}", flush=True)


if __name__ == "__main__":
    main()
