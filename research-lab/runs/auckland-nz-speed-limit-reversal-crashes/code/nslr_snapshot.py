"""Snapshot the National Speed Limit Register (NSLR) FeatureServer.

The register is refreshed nightly and its history is rewritten silently (critic note), so the analysis keeps its own
copies:
  python nslr_snapshot.py --full    all fields + polygons (NZTM, EPSG:2193)  -> data/nslr_snapshots/<date>_full.json.gz
  python nslr_snapshot.py           all fields, no geometry                  -> data/nslr_snapshots/<date>_attrs.json.gz
  python nslr_snapshot.py --daemon  attribute snapshot every day at ~03:30 NZ time, full snapshot on Sundays
Each file holds {"meta": {...}, "features": [...]}; meta records the server's dataLastEditDate and the record count,
and a snapshot is rejected (not written) unless the number of features equals the server count.
"""
import argparse
import datetime as dt
import gzip
import json
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from zoneinfo import ZoneInfo

SVC = "https://services.arcgis.com/CXBb7LAjgIIdcsPt/arcgis/rest/services/SpeedLimitZoneFull__View/FeatureServer/0"
OUT = Path(__file__).resolve().parents[1] / "data" / "nslr_snapshots"
NZ = ZoneInfo("Pacific/Auckland")
PAGE = 2000


def get(url, params, tries=6):
    q = url + "?" + urllib.parse.urlencode(params)
    for k in range(tries):
        try:
            with urllib.request.urlopen(q, timeout=180) as r:
                d = json.load(r)
            if "error" in d:
                raise RuntimeError(d["error"])
            return d
        except Exception as e:  # noqa: BLE001
            if k == tries - 1:
                raise
            print("retry", k, e, file=sys.stderr)
            time.sleep(10 * (k + 1))


def snapshot(full):
    meta = get(SVC, {"f": "json"})
    n = get(SVC + "/query", {"where": "1=1", "returnCountOnly": "true", "f": "json"})["count"]
    base = {"where": "1=1", "outFields": "*", "orderByFields": "OBJECTID", "resultRecordCount": PAGE, "f": "json",
            "returnGeometry": "true" if full else "false"}
    if full:
        base["outSR"] = 2193

    def page(off):
        return get(SVC + "/query", base | {"resultOffset": off})["features"]

    with ThreadPoolExecutor(4) as ex:
        feats = [f for p in ex.map(page, range(0, n, PAGE)) for f in p]
    ids = {f["attributes"]["OBJECTID"] for f in feats}
    now = dt.datetime.now(NZ)
    if len(feats) != n or len(ids) != n:
        print(f"{now:%F %T} REJECTED: {len(feats)} features, {len(ids)} unique ids, server count {n}", file=sys.stderr)
        return None
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{now:%Y-%m-%d}_{'full' if full else 'attrs'}.json.gz"
    m = {"taken": now.isoformat(), "service": SVC, "count": n, "geometry": full,
         "dataLastEditDate": meta["editingInfo"]["dataLastEditDate"]}
    with gzip.open(path, "wt") as fh:
        json.dump({"meta": m, "features": feats}, fh)
    print(f"{now:%F %T} wrote {path.name}: {n} records, dataLastEditDate {m['dataLastEditDate']}", flush=True)
    return path


def daemon():
    while True:
        now = dt.datetime.now(NZ)
        nxt = now.replace(hour=3, minute=30, second=0, microsecond=0)
        if nxt <= now:
            nxt += dt.timedelta(days=1)
        time.sleep((nxt - now).total_seconds())
        try:
            snapshot(full=False)
            if nxt.weekday() == 6:
                snapshot(full=True)
        except Exception as e:  # noqa: BLE001
            print(f"{dt.datetime.now(NZ):%F %T} snapshot failed: {e}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--daemon", action="store_true")
    a = ap.parse_args()
    daemon() if a.daemon else snapshot(a.full)
