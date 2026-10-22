"""Parallel ranged download of one large file (per-connection bandwidth to overseas hosts is low here).
  fetch_parallel.py URL OUT [--parts 64]"""
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

url, out = sys.argv[1], Path(sys.argv[2])
parts = int(sys.argv[3]) if len(sys.argv) > 3 else 64
size = int(urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=60).headers["Content-Length"])
step = -(-size // parts)
tmp = out.with_suffix(out.suffix + ".part")
with open(tmp, "wb") as fh:
    fh.truncate(size)


def get(k):
    a, b = k * step, min(size, (k + 1) * step) - 1
    for t in range(8):
        try:
            req = urllib.request.Request(url, headers={"Range": f"bytes={a}-{b}"})
            data = urllib.request.urlopen(req, timeout=300).read()
            assert len(data) == b - a + 1
            with open(tmp, "r+b") as fh:
                fh.seek(a); fh.write(data)
            return
        except Exception:
            continue
    raise RuntimeError(f"part {k}")


with ThreadPoolExecutor(parts) as ex:
    list(ex.map(get, range(parts)))
tmp.rename(out)
print("done", out, size)
