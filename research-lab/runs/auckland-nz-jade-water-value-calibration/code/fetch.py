"""Fetch the JADE weekly runs and the realised prices (plan section 3).

The EMI blob store is listed directly. Each run's `tidy_results.csv` is about 86 MB and there are 152 of them, so
they are streamed and filtered on the fly: only `prices`, `total_storage` and `reslevel` rows at stages 0-4 are
kept, which is a few hundred kilobytes per run instead of 13.4 GB in total. Realised prices come from the monthly
final-price archives under `ByMonth/`, filtered to the three nodes of interest.

Writes data/runs/<year>_<week>.csv (filtered simulation output), data/runs/<year>_<week>_hours.csv,
data/run_index.csv (one row per run, with the input-freeze timestamp), data/prices/<yyyymm>.csv and
logs/fetch.log. Resumable: anything already written is skipped.
"""
import csv
import io
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
DATA = RUN / "data"
BLOB = "https://emidatasets.blob.core.windows.net/publicdata"
WV = "Datasets/Wholesale/Expected water values/"
FEP = "Datasets/Wholesale/DispatchAndPricing/FinalEnergyPrices/ByMonth/"
HMD = "Datasets/Environment/HydrologicalModellingDataset/"
NODES = ("HAY2201", "BEN2201", "OTA2201")
KEEP_TYPES = {"prices", "total_storage", "reslevel"}
MAX_STAGE = 4
UA = {"User-Agent": "UoA research-lab (JADE calibration audit)"}


def log(msg):
    (RUN / "logs").mkdir(exist_ok=True)
    print(msg, flush=True)
    with open(RUN / "logs" / "fetch.log", "a") as fh:
        fh.write(msg + "\n")


def listing(prefix):
    names, marker = [], ""
    while True:
        url = (f"{BLOB}?restype=container&comp=list&prefix={urllib.parse.quote(prefix)}"
               f"&maxresults=5000&marker={marker}")
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
            x = r.read().decode("utf-8", "ignore")
        names += re.findall(r"<Name>([^<]+)</Name>", x)
        m = re.search(r"<NextMarker>([^<]*)</NextMarker>", x)
        if not m or not m.group(1):
            return names
        marker = m.group(1)


def stream(path, tries=4):
    """Yield decoded lines of a blob without holding it in memory."""
    url = BLOB + "/" + urllib.parse.quote(path)
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600) as r:
                for line in io.TextIOWrapper(r, encoding="utf-8", errors="ignore"):
                    yield line
            return
        except Exception as e:                       # noqa: BLE001
            log(f"    stream attempt {k + 1}/{tries}: {type(e).__name__}")
            time.sleep(5 * (k + 1))
    raise RuntimeError(f"could not stream {path}")


def get(path, dest, tries=4):
    if dest.exists() and dest.stat().st_size > 0:
        return True
    url = BLOB + "/" + urllib.parse.quote(path)
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600) as r:
                dest.write_bytes(r.read())
            return True
        except Exception as e:                       # noqa: BLE001
            log(f"    get attempt {k + 1}/{tries}: {type(e).__name__}")
            time.sleep(5 * (k + 1))
    return False


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    (DATA / "runs").mkdir(parents=True, exist_ok=True)
    (DATA / "prices").mkdir(parents=True, exist_ok=True)

    if what in ("all", "runs"):
        names = listing(WV)
        log(f"{len(names)} blobs in the water-values dataset")
        tidy = sorted(n for n in names if n.lower().endswith("tidy_results.csv"))
        index = []
        for path in tidy:
            parts = path.split("/")
            year, folder = parts[3], parts[4]
            m = re.match(r"week\s*(\d+)", folder, re.I)
            if not m:
                continue
            week = int(m.group(1))
            tag = f"{year}_{week:02d}"
            # the input-freeze timestamp is the folder name under Inputs/data_files/
            stamps = sorted({n.split("/")[7] for n in names
                             if n.startswith(f"{WV}{year}/{folder}/Inputs/data_files/") and len(n.split("/")) > 7})
            hours = [n for n in names if n.startswith(f"{WV}{year}/{folder}/Inputs/data_files/")
                     and n.endswith("hours_per_block.csv")]
            index.append(dict(tag=tag, year=int(year), week=week, folder=folder,
                              input_stamp=stamps[-1] if stamps else "", tidy=path))
            out = DATA / "runs" / f"{tag}.csv"
            if hours:
                get(hours[-1], DATA / "runs" / f"{tag}_hours.csv")
            if out.exists() and out.stat().st_size > 0:
                continue
            kept = 0
            with open(out, "w", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["simulation", "stage", "year", "week", "type", "name", "demand", "node", "value"])
                rdr = csv.reader(stream(path))
                header = next(rdr, None)
                col = {c: i for i, c in enumerate(header or [])}
                for row in rdr:
                    if not row or row[col["type"]] not in KEEP_TYPES:
                        continue
                    try:
                        if int(row[col["stage"]]) > MAX_STAGE:
                            continue
                    except ValueError:
                        continue
                    w.writerow([row[col[c]] for c in ("simulation", "stage", "year", "week", "type", "name",
                                                      "demand", "node", "value")])
                    kept += 1
            log(f"  {tag}: kept {kept} rows (stamp {index[-1]['input_stamp']})")
        with open(DATA / "run_index.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["tag", "year", "week", "folder", "input_stamp", "tidy"])
            w.writeheader(); w.writerows(index)
        log(f"{len(index)} weekly runs indexed")

    if what in ("all", "prices"):
        for y in (2023, 2024, 2025, 2026):
            for mth in range(1, 13):
                if y == 2026 and mth > 3:
                    break
                ym = f"{y}{mth:02d}"
                out = DATA / "prices" / f"{ym}.csv"
                if out.exists() and out.stat().st_size > 0:
                    continue
                kept = 0
                try:
                    rdr = csv.reader(stream(f"{FEP}{ym}_FinalEnergyPrices.csv"))
                except RuntimeError:
                    log(f"  prices {ym}: unavailable")
                    continue
                header = next(rdr, None)
                clean = [c.strip().lstrip("﻿") for c in (header or [])]
                col = {c: i for i, c in enumerate(clean)}
                node_col = next((col[c] for c in ("PointOfConnection", "PointofConnection", "Node") if c in col), 0)
                with open(out, "w", newline="") as fh:
                    w = csv.writer(fh)
                    w.writerow(clean)
                    for row in rdr:
                        if row and row[node_col] in NODES:
                            w.writerow(row); kept += 1
                log(f"  prices {ym}: {kept} rows at {len(NODES)} nodes")

    if what in ("all", "hmd"):
        (DATA / "hmd").mkdir(parents=True, exist_ok=True)
        got = 0
        for n in listing(HMD):
            if n.lower().endswith((".csv", ".zip")) and get(n, DATA / "hmd" / Path(n).name):
                got += 1
        log(f"hydrological dataset: {got} files")


if __name__ == "__main__":
    main()
