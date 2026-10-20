"""Fetch the CourtListener bulk snapshots (plan section 3).

The S3 bucket throttles each connection to about 95 KB/s, so every file is pulled as parallel byte ranges and
reassembled. Each part is written to its own file and skipped if already complete, so an interrupted run resumes.
Nothing is decompressed here; parse.py streams the archives.

Files (snapshot 2026-09-30): opinions 55.3 GB, dockets 5.1 GB, opinion-clusters 2.5 GB, citations 0.13 GB, plus
the Charlotin AI Hallucination Cases database used for recall calibration.
"""
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
S3 = "https://com-courtlistener-storage.s3-us-west-2.amazonaws.com/bulk-data"
SNAP = "2026-09-30"
FILES = {
    "citations.csv.bz2": f"{S3}/citations-{SNAP}.csv.bz2",
    "opinion-clusters.csv.bz2": f"{S3}/opinion-clusters-{SNAP}.csv.bz2",
    "dockets.csv.bz2": f"{S3}/dockets-{SNAP}.csv.bz2",
    "opinions.csv.bz2": f"{S3}/opinions-{SNAP}.csv.bz2",
}
CHARLOTIN = "https://www.damiencharlotin.com/hallucinations/hallucinations/download.csv"
CHUNK_MAX = 256 * 1024 * 1024      # cap on one part
CHUNK_MIN = 16 * 1024 * 1024       # floor, so small files still get several connections
WORKERS = 48                       # per-connection throttling, so concurrency is the only lever
UA = {"User-Agent": "UoA research-lab (citation-integrity screen; one-off bulk pull)"}


def log(msg):
    (RUN / "logs").mkdir(exist_ok=True)
    print(msg, flush=True)
    with open(RUN / "logs" / "fetch.log", "a") as fh:
        fh.write(msg + "\n")


def size_of(url):
    req = urllib.request.Request(url, headers=UA, method="HEAD")
    with urllib.request.urlopen(req, timeout=120) as r:
        return int(r.headers["Content-Length"])


def get_range(url, start, end, dest, tries=6):
    """Download one byte range to `dest`.

    Each attempt rewrites the part from scratch rather than appending to what is already there: a server that
    ignores the Range header, or an error body, would otherwise be appended to a partial part and silently
    corrupt it (an earlier version of this grew a 127 MB file to 534 MB that way). The response must be 206 with
    a Content-Range that starts where we asked, and the part must end up exactly the requested length.
    """
    want = end - start + 1
    if dest.exists() and dest.stat().st_size == want:
        return want
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={**UA, "Range": f"bytes={start}-{end}"})
            with urllib.request.urlopen(req, timeout=900) as r:
                if r.status != 206:
                    raise RuntimeError(f"expected 206, got {r.status}")
                cr = r.headers.get("Content-Range", "")
                if not cr.startswith(f"bytes {start}-{end}/"):
                    raise RuntimeError(f"bad Content-Range {cr!r}")
                with open(dest, "wb") as fh:
                    while True:
                        buf = r.read(1 << 20)
                        if not buf:
                            break
                        fh.write(buf)
            got = dest.stat().st_size
            if got == want:
                return got
            raise RuntimeError(f"short part: {got} of {want}")
        except Exception as e:                      # noqa: BLE001
            log(f"    {dest.name} attempt {k + 1}/{tries}: {type(e).__name__}: {e}")
            dest.unlink(missing_ok=True)
            time.sleep(4 * (k + 1))
    raise RuntimeError(f"{dest.name}: could not fetch bytes {start}-{end}")


def fetch(name, url):
    out = RAW / name
    total = size_of(url)
    if out.exists() and out.stat().st_size == total:
        log(f"{name}: already complete ({total / 1e9:.2f} GB)")
        return
    parts_dir = RAW / f"{name}.parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    # size the parts so even a small file is split across the available connections
    chunk = min(CHUNK_MAX, max(CHUNK_MIN, -(-total // (WORKERS * 4))))
    spans = [(s, min(s + chunk - 1, total - 1)) for s in range(0, total, chunk)]
    log(f"{name}: {total / 1e9:.2f} GB in {len(spans)} parts over {WORKERS} connections")
    done = [0]
    t0 = time.time()

    def one(i):
        n = get_range(url, spans[i][0], spans[i][1], parts_dir / f"{i:05d}")
        done[0] += 1
        el = time.time() - t0
        mb = sum((parts_dir / f"{j:05d}").stat().st_size for j in range(len(spans))
                 if (parts_dir / f"{j:05d}").exists()) / 1e6
        log(f"  [{done[0]}/{len(spans)}] {name} part {i} ({n / 1e6:.0f} MB) "
            f"| {mb / 1e3:.1f} GB down, {mb / max(1, el):.1f} MB/s")
        return n

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        list(ex.map(one, range(len(spans))))
    with open(out, "wb") as fh:
        for i in range(len(spans)):
            fh.write((parts_dir / f"{i:05d}").read_bytes())
    if out.stat().st_size != total:
        raise RuntimeError(f"{name}: assembled {out.stat().st_size} != {total}")
    for i in range(len(spans)):
        os.remove(parts_dir / f"{i:05d}")
    parts_dir.rmdir()
    log(f"{name}: complete, {total / 1e9:.2f} GB")


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1:] or list(FILES)
    dest = RAW / "charlotin.csv"
    if not dest.exists() or dest.stat().st_size == 0:
        with urllib.request.urlopen(urllib.request.Request(CHARLOTIN, headers=UA), timeout=300) as r:
            dest.write_bytes(r.read())
        log(f"charlotin.csv: {dest.stat().st_size / 1e6:.1f} MB")
    for name in only:
        fetch(name, FILES[name])


if __name__ == "__main__":
    main()
