"""Fetch the open inputs (plan section 2) into data/raw/: the EAGLE-I figshare record 24237376 (outages 2015-2025,
MCC, coverage history, DQI) and PUDL's EIA-861 yearly reliability table. Large files are fetched as 64 MB byte-range
segments, 16 at a time (single connections run at about 60 KB/s from this machine), each through a fresh figshare
redirect; segments are resumable and joined when all are complete; sizes are checked against the figshare record;
SHA-256 to data/raw/SHA256SUMS; failures to data/raw/fetch_errors.txt."""
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
UA = {"User-Agent": "research-lab outage study (mailto:noreply@anthropic.com)"}
PUDL = "https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/stable/core_eia861__yearly_reliability.parquet"


def get(url, dest, size=None):
    if dest.exists() and (size is None or dest.stat().st_size == size):
        return "have"
    err = ""
    for i in range(5):
        try:
            tmp = dest.with_suffix(dest.suffix + ".part")
            with requests.get(url, headers=UA, timeout=600, stream=True) as r:
                r.raise_for_status()
                with open(tmp, "wb") as fh:
                    for chunk in r.iter_content(1 << 20):
                        fh.write(chunk)
            if size is not None and tmp.stat().st_size != size:
                raise IOError(f"size {tmp.stat().st_size} != {size}")
            tmp.rename(dest)
            return "ok"
        except Exception as e:  # noqa: BLE001
            err = str(e)[:150]; time.sleep(30 * (i + 1))
    with open(RAW / "fetch_errors.txt", "a") as fh:
        fh.write(f"{url}\t{err}\n")
    return "error"


SEG = 64 << 20


def segment(url, dest, k, lo, hi):
    part = dest.with_name(f"{dest.name}.seg{k:04d}")
    want = hi - lo + 1
    if part.exists() and part.stat().st_size == want:
        return "have"
    err = ""
    for i in range(6):
        try:
            loc = requests.get(url, headers=UA, timeout=60, allow_redirects=False).headers.get("Location", url)
            with requests.get(loc, headers={**UA, "Range": f"bytes={lo}-{hi}"}, timeout=600, stream=True) as r:
                if r.status_code != 206:
                    raise IOError(f"HTTP {r.status_code}")
                with open(part, "wb") as fh:
                    for chunk in r.iter_content(1 << 20):
                        fh.write(chunk)
            if part.stat().st_size != want:
                raise IOError(f"segment size {part.stat().st_size} != {want}")
            return "ok"
        except Exception as e:  # noqa: BLE001
            err = str(e)[:150]; time.sleep(20 * (i + 1))
    with open(RAW / "fetch_errors.txt", "a") as fh:
        fh.write(f"{url} segment {k}\t{err}\n")
    return "error"


def join(dest, n, size):
    parts = [dest.with_name(f"{dest.name}.seg{k:04d}") for k in range(n)]
    if not all(p.exists() for p in parts):
        return False
    with open(dest.with_suffix(dest.suffix + ".part"), "wb") as out:
        for p in parts:
            out.write(p.read_bytes())
    tmp = dest.with_suffix(dest.suffix + ".part")
    if tmp.stat().st_size != size:
        return False
    tmp.rename(dest)
    for p in parts:
        p.unlink()
    return True


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    rec = requests.get("https://api.figshare.com/v2/articles/24237376", headers=UA, timeout=120).json()
    jobs = [(f["download_url"], RAW / f["name"], f["size"]) for f in rec["files"]
            if f["name"].endswith(".csv") and f["name"] != "eaglei_outages_2014.csv"]
    jobs.append((PUDL, RAW / "core_eia861__yearly_reliability.parquet", None))
    small = [j for j in jobs if (j[2] or 0) < SEG]
    big = [j for j in jobs if (j[2] or 0) >= SEG and not (j[1].exists() and j[1].stat().st_size == j[2])]
    res = [get(*j) for j in small]
    segs = [(u, d, k, lo, min(lo + SEG, n) - 1) for u, d, n in big for k, lo in enumerate(range(0, n, SEG))]
    with ThreadPoolExecutor(16) as ex:
        sres = list(ex.map(lambda a: segment(*a), segs))
    joined = [join(d, len(range(0, n, SEG)), n) for _, d, n in big]
    print(len(jobs), "files;", {s: res.count(s) for s in set(res)}, "small;", {s: sres.count(s) for s in set(sres)}, "segments;",
          sum(joined), "of", len(big), "large files joined; figshare version", rec.get("version"), flush=True)
    with open(RAW / "SHA256SUMS", "w") as fh:
        for _, d, _ in jobs:
            if d.exists():
                h = hashlib.sha256()
                with open(d, "rb") as f:
                    for chunk in iter(lambda: f.read(1 << 24), b""):
                        h.update(chunk)
                fh.write(f"{h.hexdigest()}  {d.name}\n")


if __name__ == "__main__":
    main()
