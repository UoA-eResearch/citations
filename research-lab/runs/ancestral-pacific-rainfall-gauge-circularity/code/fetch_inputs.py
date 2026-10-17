"""Fetch the gauge records and the CHIRPS stations-used lists (plan section 2). Polite: one request at a time, 1 s apart.
  data/raw/ghcn/stations.csv            Pacific Island GHCN-Daily stations with PRCP after 1985 (from the inventory)
  data/raw/ghcn/dly/<id>.dly            per-station daily records
  data/raw/chirps_used/<yyyy.mm>.csv    CHIRPS monthly stations-used lists, 1981-2025
Failures are logged to data/raw/fetch_errors.jsonl and retried on the next run, never treated as empty."""
import json
import time
from pathlib import Path

import pandas as pd
import requests

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
S = requests.Session(); S.headers["User-Agent"] = "research-lab rainfall study (mailto:noreply@anthropic.com)"
CC = {"FM", "GQ", "FJ", "AQ", "RM", "PP", "PS", "FP", "KR", "NH", "BP", "NC", "TV", "TN", "CW", "NE", "TL", "PC", "WS", "CQ", "NR", "WF",
      "WQ", "JQ", "MQ", "LQ", "HQ", "KQ", "DQ"}


def get(url, f):
    if f.exists() and f.stat().st_size > 0:
        return True
    for k in range(4):
        try:
            r = S.get(url, timeout=120)
            if r.status_code == 200:
                f.write_bytes(r.content); return True
            err = f"HTTP {r.status_code}"
        except Exception as e:  # noqa: BLE001
            err = str(e)[:120]
        time.sleep(10 * (k + 1))
    with open(RAW / "fetch_errors.jsonl", "a") as fh:
        fh.write(json.dumps(dict(url=url, error=err)) + "\n")
    return False


def main():
    inv = pd.read_fwf(RAW / "ghcn" / "ghcnd-inventory.txt", colspecs=[(0, 11), (12, 20), (21, 30), (31, 35), (36, 40), (41, 45)],
                      names=["id", "lat", "lon", "el", "first", "last"])
    st = inv[(inv.el == "PRCP") & inv.id.str[:2].isin(CC) & (inv["last"] >= 1985)].drop(columns="el")
    names = pd.read_fwf(RAW / "ghcn" / "ghcnd-stations.txt", colspecs=[(0, 11), (41, 71)], names=["id", "name"]).set_index("id").name
    st = st.assign(name=st.id.map(names), cc=st.id.str[:2])
    st.to_csv(RAW / "ghcn" / "stations.csv", index=False)
    (RAW / "ghcn" / "dly").mkdir(exist_ok=True)
    for sid in st.id:
        get(f"https://www.ncei.noaa.gov/pub/data/ghcn/daily/all/{sid}.dly", RAW / "ghcn" / "dly" / f"{sid}.dly"); time.sleep(1)
    print("ghcn", len(st), "stations", flush=True)
    (RAW / "chirps_used").mkdir(exist_ok=True)
    for y in range(1981, 2026):
        for m in range(1, 13):
            u = f"https://data.chc.ucsb.edu/products/CHIRPS-2.0/diagnostics/list_of_stations_used/monthly/global.stationsUsed.{y}.{m:02d}.csv"
            get(u, RAW / "chirps_used" / f"{y}.{m:02d}.csv"); time.sleep(1)
    print("stations-used lists done", flush=True)


if __name__ == "__main__":
    main()
