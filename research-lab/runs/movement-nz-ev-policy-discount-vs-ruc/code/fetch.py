"""Monthly first registrations by powertrain from NZTA's Motor Vehicle Register (plan section 2).

NZTA's web site refuses scripted requests (an Incapsula challenge, verified 2026-10-20), but its ArcGIS
FeatureServer answers aggregation queries, so no bulk download is needed and no vehicle-level record is
retrieved: the server returns counts grouped by month, motive power, import status and vehicle type.

One query per registration year keeps every response inside the service's 2,000-record page. Writes
data/registrations.csv and data/raw/<year>.json, with logs/fetch.log.
"""
import csv
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
SERVICE = ("https://services.arcgis.com/CXBb7LAjgIIdcsPt/arcgis/rest/services/MVR_Mar26/FeatureServer/0/query")
TYPES = ("PASSENGER CAR/VAN", "GOODS VAN/TRUCK/UTILITY")
YEARS = range(2021, 2027)
UA = {"User-Agent": "UoA research-lab (EV policy study); aggregation queries only"}


def log(msg):
    (RUN / "logs").mkdir(exist_ok=True)
    print(msg, flush=True)
    with open(RUN / "logs" / "fetch.log", "a") as fh:
        fh.write(msg + "\n")


def query(year, tries=5):
    types = ",".join(f"'{t}'" for t in TYPES)
    params = {
        "where": f"FIRST_NZ_REGISTRATION_YEAR={year} AND VEHICLE_TYPE IN ({types})",
        "outStatistics": json.dumps([{"statisticType": "count", "onStatisticField": "OBJECTID",
                                      "outStatisticFieldName": "n"}]),
        "groupByFieldsForStatistics": "FIRST_NZ_REGISTRATION_MONTH,MOTIVE_POWER,IMPORT_STATUS,VEHICLE_TYPE",
        "f": "json",
    }
    url = SERVICE + "?" + urllib.parse.urlencode(params)
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
                d = json.loads(r.read())
            if "features" not in d:
                raise ValueError(str(d)[:200])
            return d
        except Exception as e:                          # noqa: BLE001
            log(f"  {year} attempt {k + 1}/{tries}: {type(e).__name__} {str(e)[:120]}")
            time.sleep(5 * (k + 1))
    return None


def main():
    raw = RUN / "data" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    rows = []
    for y in YEARS:
        d = query(y)
        if d is None:
            log(f"{y}: FAILED, no data (recorded as an error, not as zero)")
            continue
        json.dump(d, open(raw / f"{y}.json", "w"))
        feats = d["features"]
        if len(feats) >= 2000:
            log(f"{y}: WARNING {len(feats)} rows, at the service page limit; split the query")
        for f in feats:
            a = f["attributes"]
            if not a.get("FIRST_NZ_REGISTRATION_MONTH"):
                continue
            rows.append(dict(year=y, month=a["FIRST_NZ_REGISTRATION_MONTH"],
                             motive_power=(a.get("MOTIVE_POWER") or "").strip(),
                             import_status=(a.get("IMPORT_STATUS") or "").strip(),
                             vehicle_type=(a.get("VEHICLE_TYPE") or "").strip(), n=a["n"]))
        log(f"{y}: {len(feats)} groups, {sum(f['attributes']['n'] for f in feats):,} registrations")
        time.sleep(2)
    out = RUN / "data" / "registrations.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "month", "motive_power", "import_status", "vehicle_type", "n"])
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["year"], r["month"], r["motive_power"])))
    log(f"wrote {out} with {len(rows)} rows, {sum(r['n'] for r in rows):,} registrations")


if __name__ == "__main__":
    main()
