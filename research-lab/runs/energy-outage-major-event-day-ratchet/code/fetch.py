"""Fetch the open inputs (plan section 2) into data/raw/: the EAGLE-I figshare record 24237376 (outages 2015-2025,
MCC, coverage history, DQI) and PUDL's EIA-861 yearly reliability table. Two download streams; resumable (.part then
rename); size checked against the figshare record; SHA-256 to data/raw/SHA256SUMS; failures to data/raw/fetch_errors.txt."""
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


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    rec = requests.get("https://api.figshare.com/v2/articles/24237376", headers=UA, timeout=120).json()
    jobs = [(f["download_url"], RAW / f["name"], f["size"]) for f in rec["files"]
            if f["name"].endswith(".csv") and f["name"] != "eaglei_outages_2014.csv"]
    jobs.append((PUDL, RAW / "core_eia861__yearly_reliability.parquet", None))
    with ThreadPoolExecutor(2) as ex:
        res = list(ex.map(lambda j: get(*j), sorted(jobs, key=lambda j: j[2] or 0)))
    print(len(jobs), "files:", {s: res.count(s) for s in set(res)}, "figshare version", rec.get("version"))
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
