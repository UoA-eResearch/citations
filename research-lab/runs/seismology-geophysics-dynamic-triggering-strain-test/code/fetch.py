"""Data download (plan section 1). No window, trigger or count is computed here.

  fetch.py listing   -> data/manifest.csv.gz: frozen listing (key, etag, size, last_modified) of western/picks
  fetch.py meta      -> data/raw/stations.parquet, data/raw/availability/<network>.parquet
  fetch.py picks [T] -> data/picks/network=<n>/year=<y>/month=<m>.parquet, one file per partition:
                        columns tid, cha, pha, peak_ms (int64), conf; confidence >= 0.5; peak in 2002-2025; exact
                        duplicates of (tid, cha, pha, peak) dropped. Per-partition counts in data/picks_counts.csv.
All S3 access is anonymous (bucket quakescope-picks-2026, us-east-2).
"""
import csv
import gzip
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.fs as pafs
import pyarrow.parquet as pq

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
BUCKET = "quakescope-picks-2026"
HTTP = f"https://s3.us-east-2.amazonaws.com/{BUCKET}"
LO = pa.scalar(1009843200000, pa.int64())   # 2002-01-01T00:00:00Z in ms
HI = pa.scalar(1767225600000, pa.int64())   # 2026-01-01T00:00:00Z in ms


def listing():
    rows, token = [], None
    while True:
        u = f"{HTTP}?list-type=2&prefix=western/picks/&max-keys=1000"
        if token:
            u += "&continuation-token=" + urllib.parse.quote(token)
        for k in range(6):
            try:
                s = urllib.request.urlopen(u, timeout=120).read().decode()
                break
            except Exception:
                time.sleep(5 * (k + 1))
        rows += re.findall(r"<Key>([^<]+)</Key><LastModified>([^<]+)</LastModified><ETag>&quot;([^&]+)&quot;</ETag>"
                           r"<Size>(\d+)</Size>", s)
        m = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", s)
        if not m:
            break
        token = m.group(1)
    with gzip.open(D / "manifest.csv.gz", "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["key", "last_modified", "etag", "size"])
        w.writerows(rows)
    print(len(rows), "objects;", round(sum(int(r[3]) for r in rows) / 1e9, 2), "GB", flush=True)


def meta():
    (D / "raw" / "availability").mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(f"{HTTP}/western/stations.parquet", D / "raw" / "stations.parquet")
    s = urllib.request.urlopen(f"{HTTP}?list-type=2&prefix=western/availability/&max-keys=1000", timeout=120).read().decode()
    keys = re.findall(r"<Key>([^<]+availability\.parquet)</Key>", s)
    for k in keys:
        net = re.search(r"network=([^/]+)/", k).group(1)
        urllib.request.urlretrieve(f"{HTTP}/{k}", D / "raw" / "availability" / f"{net}.parquet")
    print(len(keys), "availability files", flush=True)


def partition(args):
    (net, year, month), keys, fs = args
    out = D / "picks" / f"network={net}" / f"year={year}" / f"month={month}.parquet"
    if out.exists():
        return net, year, month, -1, -1, -1, 0
    tabs, n_in, n_files_failed = [], 0, 0
    for k in keys:
        for attempt in range(5):
            try:
                t = pq.read_table(f"{BUCKET}/{k}", columns=["tid", "cha", "pha", "peak", "conf"], filesystem=fs)
                break
            except Exception:
                t = None
                time.sleep(3 * (attempt + 1))
        if t is None:
            n_files_failed += 1
            continue
        n_in += t.num_rows
        ms = pc.cast(t["peak"], pa.int64())
        keep = pc.and_(pc.greater_equal(t["conf"], 0.5), pc.and_(pc.greater_equal(ms, LO), pc.less(ms, HI)))
        t = pa.table({"tid": t["tid"], "cha": t["cha"], "pha": t["pha"], "peak_ms": ms, "conf": t["conf"]}).filter(
            pc.fill_null(keep, False))
        tabs.append(t)
    t = pa.concat_tables(tabs) if tabs else None
    n_conf = t.num_rows if t is not None else 0
    if t is not None and t.num_rows:
        import pandas as pd
        df = t.to_pandas()
        df = df.drop_duplicates(["tid", "cha", "pha", "peak_ms"])
        n_out = len(df)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".tmp")
        pq.write_table(pa.Table.from_pandas(df, preserve_index=False), tmp, compression="zstd")
        tmp.rename(out)
    else:
        n_out = 0
    if n_files_failed:
        raise IOError(f"{net} {year}-{month}: {n_files_failed} files failed")    # never write a partial partition
    return net, year, month, n_in, n_conf, n_out, len(keys)


def picks(threads=96):
    pa.set_io_thread_count(threads * 2)
    groups = {}
    with gzip.open(D / "manifest.csv.gz", "rt") as f:
        for r in csv.DictReader(f):
            m = re.search(r"network=([^/]+)/year=(\d+)/month=(\d+)/", r["key"])
            if m and 2001 <= int(m.group(2)) <= 2026:
                groups.setdefault((m.group(1), int(m.group(2)), int(m.group(3))), []).append(r["key"])
    print(len(groups), "partitions,", sum(len(v) for v in groups.values()), "files", flush=True)
    fs = pafs.S3FileSystem(anonymous=True, region="us-east-2", connect_timeout=60, request_timeout=300)
    cnt = D / "picks_counts.csv"
    new = not cnt.exists()
    done = 0
    with open(cnt, "a", newline="") as f, ThreadPoolExecutor(threads) as ex:
        w = csv.writer(f)
        if new:
            w.writerow(["network", "year", "month", "picks_read", "picks_conf_in_range", "picks_kept", "files"])
        futs = [ex.submit(partition, (g, ks, fs)) for g, ks in sorted(groups.items(), key=lambda kv: -len(kv[1]))]
        failed = 0
        for fu in as_completed(futs):
            try:
                r = fu.result()
            except Exception as e:                              # logged; a re-run fills the gap (done partitions skip)
                failed += 1
                print("FAILED", e, flush=True)
                continue
            if r[3] >= 0:
                w.writerow(r); f.flush()
            done += 1
            if done % 200 == 0:
                print(time.strftime("%H:%M:%S"), done, "of", len(groups), flush=True)
    print("== done", done, "failed", failed, flush=True)


if __name__ == "__main__":
    {"listing": listing, "meta": meta, "picks": lambda: picks(*(int(x) for x in sys.argv[2:3]))}[sys.argv[1]]()
