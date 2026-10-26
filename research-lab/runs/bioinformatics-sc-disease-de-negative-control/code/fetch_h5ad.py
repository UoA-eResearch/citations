"""Parallel, resumable download of the needed Census source H5ADs (D1: this host gets ~120 KB/s per S3 connection,
scaling with connections, while TileDB's sparse reader stays near one connection).

  fetch_h5ad.py [THREADS] [MAX_PENDING] [FILES]
    -> data/h5ad/<dataset_id>.h5ad, then data/h5ad/<dataset_id>.complete once every byte has arrived (size checked).
       pb_h5ad.py consumes complete files and deletes them; at most MAX_PENDING complete-but-unprocessed files wait.
"""
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

RUN = Path(__file__).resolve().parents[1]
META, H5 = RUN / "data" / "meta", RUN / "data" / "h5ad"
BASE = "https://cellxgene-census-public-us-west-2.s3.us-west-2.amazonaws.com/cell-census/2025-11-08/h5ads/"
PIECE = 4 << 20
_tls = threading.local()


def get_range(url, a, b, tries=20):
    s = getattr(_tls, "s", None) or setattr(_tls, "s", requests.Session()) or _tls.s
    for i in range(tries):
        try:
            r = s.get(url, headers={"Range": f"bytes={a}-{b}"}, timeout=(20, 300))
            if r.status_code == 206 and len(r.content) == b - a + 1:
                return r.content
            err = f"HTTP {r.status_code} len {len(r.content)}"
        except Exception as e:  # network errors are retried
            err = repr(e)
        time.sleep(min(60, 2 ** i))
    raise RuntimeError(f"{url} {a}-{b}: {err}")


def fetch(ds, size, pool):
    path, done_log = H5 / f"{ds}.h5ad", H5 / f"{ds}.pieces"
    if (H5 / f"{ds}.complete").exists() or (RUN / "data" / "pb" / f"{ds}.npz").exists():
        return
    if not path.exists() or path.stat().st_size != size:
        with open(path, "wb") as f:
            f.truncate(size)
    have = set(int(x) for x in done_log.read_text().split()) if done_log.exists() else set()
    n = (size + PIECE - 1) // PIECE
    todo = [i for i in range(n) if i not in have]
    url = BASE + f"{ds}.h5ad"
    lock = threading.Lock()
    fd = os.open(path, os.O_WRONLY)
    log = open(done_log, "a")

    def piece(i):
        a, b = i * PIECE, min(size, (i + 1) * PIECE) - 1
        data = get_range(url, a, b)
        os.pwrite(fd, data, a)
        with lock:
            log.write(f"{i}\n"); log.flush()
        return len(data)

    t0, got = time.time(), 0
    for k, nbytes in enumerate(pool.map(piece, todo)):
        got += nbytes
        if (k + 1) % 500 == 0:
            print(f"  {ds} {k + 1}/{len(todo)} pieces, {got / (time.time() - t0) / 1e6:.1f} MB/s", flush=True)
    os.fsync(fd); os.close(fd); log.close()
    assert path.stat().st_size == size
    (H5 / f"{ds}.complete").write_text(str(size))
    done_log.unlink()
    print(time.strftime("%H:%M:%S"), "complete", ds, round(size / 1e9, 2), "GB", f"{size / (time.time() - t0) / 1e6:.1f} MB/s", flush=True)


def main(threads=384, max_pending=2, files=4):
    """Up to `files` H5ADs download at once over one shared pool of range-request threads (a small file alone
    cannot keep the pool busy)."""
    H5.mkdir(parents=True, exist_ok=True)
    sz = pd.read_csv(META / "h5ad_sizes.csv").sort_values("bytes")
    gate = threading.Lock()

    def job(ds, size):
        with gate:                      # admit a new file only while few complete files await processing
            while len(list(H5.glob("*.complete"))) >= max_pending:
                time.sleep(20)
        fetch(ds, int(size), pool)

    with ThreadPoolExecutor(threads) as pool, ThreadPoolExecutor(files) as outer:
        for f in [outer.submit(job, d, s) for d, s in zip(sz.dataset_id, sz.bytes)]:
            f.result()
    print("== done", flush=True)


if __name__ == "__main__":
    main(*(int(a) for a in sys.argv[1:4]))
