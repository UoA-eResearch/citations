"""Fetch the open inputs (plan section 2) into data/raw/: EMI Generation_MD, Grid_export_to_Tiwai and HVDC_Flows
(2015-01 to 2024-12), Grid_export (2024, a check), the Hydrological Modelling Dataset storage, flows and
infrastructure files, and Open-Meteo hourly 2 m temperature for five cities. Resumable; failures are logged to
data/raw/fetch_errors.txt and never written as data. SHA-256 of every file goes to data/raw/SHA256SUMS."""
import hashlib
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
BLOB = "https://emidatasets.blob.core.windows.net/publicdata"
UA = {"User-Agent": "research-lab energy study (mailto:noreply@anthropic.com)"}
MONTHS = [f"{y}{m:02d}" for y in range(2015, 2025) for m in range(1, 13)]
CITIES = {"auckland": (-36.85, 174.76), "hamilton": (-37.79, 175.28), "wellington": (-41.29, 174.78),
          "christchurch": (-43.53, 172.64), "dunedin": (-45.87, 170.50)}


def get(url, dest):
    if dest.exists() and dest.stat().st_size > 0:
        return "have"
    dest.parent.mkdir(parents=True, exist_ok=True)
    err = ""
    for i in range(5):
        try:
            r = requests.get(url, headers=UA, timeout=300)
            r.raise_for_status()
            tmp = dest.with_suffix(dest.suffix + ".part"); tmp.write_bytes(r.content); tmp.rename(dest)
            return "ok"
        except Exception as e:  # noqa: BLE001
            err = str(e)[:150]; time.sleep(15 * (i + 1))
    with open(RAW / "fetch_errors.txt", "a") as fh:
        fh.write(f"{url}\t{err}\n")
    return "error"


def listing(prefix):
    names, marker = [], ""
    while True:
        x = requests.get(f"{BLOB}?restype=container&comp=list&prefix={prefix}&marker={marker}", headers=UA, timeout=120).text
        names += re.findall(r"<Name>([^<]+)</Name>", x)
        m = re.search(r"<NextMarker>([^<]+)</NextMarker>", x)
        if not m:
            return names
        marker = m[1]


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    jobs = []
    for ym in MONTHS:
        jobs.append((f"{BLOB}/Datasets/Wholesale/Generation/Generation_MD/{ym}_Generation_MD.csv", RAW / "generation" / f"{ym}.csv"))
        jobs.append((f"{BLOB}/Datasets/Wholesale/Metered_data/Grid_export_to_Tiwai/{ym}_Grid_export_to_Tiwai.csv", RAW / "tiwai" / f"{ym}.csv"))
        jobs.append((f"{BLOB}/Datasets/Wholesale/Metered_data/HVDC_Flows/{ym}_HVDC_flows.csv", RAW / "hvdc" / f"{ym}.csv"))
    for m in range(1, 13):
        jobs.append((f"{BLOB}/Datasets/Wholesale/Metered_data/Grid_export/2024{m:02d}_Grid_export.csv", RAW / "grid_export" / f"2024{m:02d}.csv"))
    for n in listing("Datasets/Environment/HydrologicalModellingDataset/"):
        if n.lower().endswith(".csv"):
            jobs.append((f"{BLOB}/{requests.utils.quote(n)}", RAW / "hmd" / n.split("HydrologicalModellingDataset/")[1]))
    for c, (la, lo) in CITIES.items():
        jobs.append((f"https://archive-api.open-meteo.com/v1/archive?latitude={la}&longitude={lo}&start_date=2014-12-01&end_date=2025-01-31"
                     f"&hourly=temperature_2m&timezone=GMT", RAW / "temperature" / f"{c}.json"))
    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(lambda j: get(*j), jobs))
    print(len(jobs), "files:", {s: res.count(s) for s in set(res)})
    with open(RAW / "SHA256SUMS", "w") as fh:
        for _, d in jobs:
            if d.exists():
                fh.write(f"{hashlib.sha256(d.read_bytes()).hexdigest()}  {d.relative_to(RAW)}\n")


if __name__ == "__main__":
    main()
