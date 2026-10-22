"""Parallel ranged download (archive.org serves ~70 KB/s per connection). Resumable via <out>.parts.json.
  pget.py URL OUT [--threads 48] [--chunk-mb 64]"""
import argparse
import json
import os
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor


def size_of(url):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "research-lab"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return int(r.headers["Content-Length"]), r.geturl()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url"); ap.add_argument("out")
    ap.add_argument("--threads", type=int, default=48); ap.add_argument("--chunk-mb", type=int, default=64)
    a = ap.parse_args()
    n, url = size_of(a.url)
    cs = a.chunk_mb << 20
    chunks = [(i, min(i + cs, n) - 1) for i in range(0, n, cs)]
    pj = a.out + ".parts.json"
    done = set(json.load(open(pj))) if os.path.exists(pj) else set()
    if not os.path.exists(a.out):
        with open(a.out, "wb") as f:
            f.truncate(n)
    fd = os.open(a.out, os.O_WRONLY)
    lock = threading.Lock()
    t0, got = time.time(), [0]

    def one(c):
        s, e = c
        if s in done:
            return
        for k in range(10):
            try:
                req = urllib.request.Request(url, headers={"Range": f"bytes={s}-{e}", "User-Agent": "research-lab"})
                with urllib.request.urlopen(req, timeout=300) as r:
                    data = r.read()
                if len(data) != e - s + 1:
                    raise IOError(f"short read {len(data)}")
                os.pwrite(fd, data, s)
                with lock:
                    done.add(s)
                    got[0] += len(data)
                    json.dump(sorted(done), open(pj, "w"))
                return
            except Exception as ex:
                time.sleep(10 * (k + 1))
        raise RuntimeError(f"chunk {s} failed")
    with ThreadPoolExecutor(a.threads) as ex:
        futs = [ex.submit(one, c) for c in chunks]
        for k, f in enumerate(futs, 1):
            f.result()
            if k % 10 == 0:
                print(f"{len(done)}/{len(chunks)} chunks, {got[0] / (time.time() - t0) / 1e6:.2f} MB/s", flush=True)
    os.close(fd)
    print("complete", a.out, n, flush=True)


if __name__ == "__main__":
    main()
