"""Data download (plan sections 3-4, steps 1-2). No matching or outcome computation happens here.

  python code/fetch.py months      -> data/months.json (2 months per year 2010-2024, seed 20261011)
  python code/fetch.py meta        -> availability (CI, NC, BK), stations.parquet, FDSN channel tables
  python code/fetch.py phases      -> SCEDC per-event phase files and NCEDC monthly phase files for the sampled months
  python code/fetch.py catalogues  -> NCEDC yearly catalogue CSVs (event type and review status)
  python code/fetch.py picks       -> QuakeScope western pick partitions for the sampled months; frozen listing in
                                      data/manifest_picks.csv
All S3 access is anonymous and path-style (the only form that works from this machine)."""
import concurrent.futures as cf
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
QS = "https://s3.us-east-2.amazonaws.com/quakescope-picks-2026"
SCEDC = "https://s3.us-west-2.amazonaws.com/scedc-pds"
NCEDC = "https://s3.us-east-2.amazonaws.com/ncedc-pds"
NETS = ["CI", "NC", "BK"]
SESSION = requests.Session()


def get(url, dest=None, parts=1, tries=6):
    """GET with retries; large objects in `parts` parallel byte ranges."""
    for k in range(tries):
        try:
            if parts > 1:
                h = SESSION.head(url, timeout=60)
                h.raise_for_status()
                n = int(h.headers["Content-Length"])
                edges = np.linspace(0, n, parts + 1).astype(int)

                def rng(i):
                    for kk in range(tries):
                        try:
                            r = requests.get(url, headers={"Range": f"bytes={edges[i]}-{edges[i + 1] - 1}"}, timeout=900)
                            r.raise_for_status()
                            if len(r.content) == edges[i + 1] - edges[i]:
                                return r.content
                        except Exception:  # noqa: BLE001
                            time.sleep(2 * (kk + 1))
                    raise IOError(f"range {i} failed for {url}")
                with cf.ThreadPoolExecutor(parts) as ex:
                    data = b"".join(ex.map(rng, range(parts)))
                assert len(data) == n
            else:
                r = SESSION.get(url, timeout=900)
                if r.status_code == 404:
                    return None
                r.raise_for_status()
                data = r.content
            if dest:
                Path(dest).parent.mkdir(parents=True, exist_ok=True)
                Path(dest).write_bytes(data)
            return data
        except Exception as e:  # noqa: BLE001
            if k == tries - 1:
                raise
            time.sleep(3 * (k + 1))
    return None


def list_s3(base, prefix, delimiter=None):
    """All keys (with etag, size) or common prefixes under a prefix, following continuation tokens."""
    keys, prefixes, token = [], [], None
    while True:
        params = {"list-type": "2", "prefix": prefix}
        if delimiter:
            params["delimiter"] = delimiter
        if token:
            params["continuation-token"] = token
        for k in range(6):
            try:
                r = SESSION.get(base, params=params, timeout=120)
                r.raise_for_status()
                break
            except Exception:  # noqa: BLE001
                time.sleep(3 * (k + 1))
        t = r.text
        for blk in re.findall(r"<Contents>(.*?)</Contents>", t, re.S):
            keys.append(dict(key=re.search(r"<Key>(.*?)</Key>", blk).group(1),
                             etag=re.search(r"<ETag>(.*?)</ETag>", blk).group(1).replace("&quot;", "").strip('"'),
                             size=int(re.search(r"<Size>(\d+)</Size>", blk).group(1))))
        prefixes += re.findall(r"<CommonPrefixes><Prefix>(.*?)</Prefix></CommonPrefixes>", t)
        m = re.search(r"<NextContinuationToken>(.*?)</NextContinuationToken>", t)
        if not m:
            return keys, prefixes
        token = m.group(1)


def months():
    rng = np.random.default_rng(20261011)
    out = []
    for y in range(2010, 2025):
        for m in sorted(rng.choice(np.arange(1, 13), size=2, replace=False).tolist()):
            out.append([y, int(m)])
    (RUN / "data").mkdir(exist_ok=True)
    json.dump(out, open(RUN / "data" / "months.json", "w"))
    print(out)


def meta():
    for n in NETS:
        get(f"{QS}/western/availability/network={n}/availability.parquet", RAW / "availability" / f"{n}.parquet", parts=16)
        print("availability", n, flush=True)
    get(f"{QS}/western/stations.parquet", RAW / "stations.parquet", parts=4)
    for name, url in (("scedc", "https://service.scedc.caltech.edu/fdsnws/station/1/query?network=CI&level=channel&format=text"),
                      ("ncedc", "https://service.ncedc.org/fdsnws/station/1/query?network=NC,BK&level=channel&format=text")):
        get(url, RAW / "channels" / f"{name}_channels.txt")
        print("channels", name, flush=True)
    with open(RAW / "SHA256_meta.txt", "w") as f:
        for p in sorted((RAW / "availability").glob("*.parquet")) + [RAW / "stations.parquet"] + sorted((RAW / "channels").glob("*.txt")):
            f.write(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(RUN)}\n")


def phases():
    ms = json.load(open(RUN / "data" / "months.json"))
    jobs = []
    for y, m in ms:
        # NCEDC: one compressed file per month
        jobs.append((f"{NCEDC}/event_phases/{y}/{y}.{m:02d}.phase.Z", RAW / "phases" / "ncedc" / f"{y}.{m:02d}.phase.Z"))
        # SCEDC: one file per event, in day folders YYYY_DDD
        d0 = pd.Timestamp(year=y, month=m, day=1)
        for d in pd.date_range(d0, d0 + pd.offsets.MonthEnd(0)):
            keys, _ = list_s3(SCEDC, f"event_phases/{y}/{y}_{d.dayofyear:03d}/")
            for k in keys:
                jobs.append((f"{SCEDC}/{k['key']}", RAW / "phases" / "scedc" / f"{y}_{m:02d}" / Path(k["key"]).name))
        print(y, m, len(jobs), flush=True)
    todo = [j for j in jobs if not j[1].exists()]
    print(len(jobs), "phase files,", len(todo), "to fetch", flush=True)
    with cf.ThreadPoolExecutor(24) as ex:
        for i, _ in enumerate(ex.map(lambda j: get(j[0], j[1]), todo)):
            if (i + 1) % 2000 == 0:
                print(i + 1, flush=True)
    print("phases done", flush=True)


def catalogues():
    ms = json.load(open(RUN / "data" / "months.json"))
    for y in sorted({y for y, _ in ms}):
        get(f"{NCEDC}/earthquake_catalogs/NCEDC/{y}.ehpcsv", RAW / "catalogues" / f"ncedc_{y}.ehpcsv", parts=8)
        print("catalogue", y, flush=True)


def picks():
    ms = json.load(open(RUN / "data" / "months.json"))
    man = []
    for n in NETS:
        for y, m in ms:
            keys, _ = list_s3(QS, f"western/picks/network={n}/year={y}/month={m:02d}/")
            for k in keys:
                k.update(network=n, year=y, month=m)
            man += keys
    man = pd.DataFrame(man)
    man["listed_at"] = pd.Timestamp.now(tz="UTC").isoformat()
    man.to_csv(RUN / "data" / "manifest_picks.csv", index=False)
    print(len(man), "objects,", round(man["size"].sum() / 1e9, 2), "GB", flush=True)
    todo = [r for r in man.itertuples() if not (RAW / r.key).exists() or (RAW / r.key).stat().st_size != r.size]

    def one(r):
        get(f"{QS}/{r.key}", RAW / r.key, parts=8 if r.size > 20e6 else 1)
        return r.size
    done = 0
    with cf.ThreadPoolExecutor(16) as ex:
        for i, s in enumerate(ex.map(one, todo)):
            done += s
            if (i + 1) % 200 == 0:
                print(i + 1, "of", len(todo), round(done / 1e9, 2), "GB", flush=True)
    print("picks done", flush=True)


if __name__ == "__main__":
    {"months": months, "meta": meta, "phases": phases, "catalogues": catalogues, "picks": picks}[sys.argv[1]]()
