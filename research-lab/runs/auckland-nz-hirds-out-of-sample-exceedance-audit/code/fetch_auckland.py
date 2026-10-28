"""Auckland Council gauges (plan section 1; D4) from the Environment Auckland portal (AQUARIUS WebPortal), whose terms
the lab owner agreed to on 2026-10-28: Auckland Council is acknowledged as the source, the data are for the lab's own
use, and raw values stay under data/ (not in git).

Same candidate rule as the Hilltop gauges (record span covering the out-of-sample window); water years 1995/96 to
2025/26; points as recorded (tips and logged zeros), NZST (UTC+12), with grade codes (NEMS).

  fetch_auckland.py -> data/inventory_auckland.parquet, data/series/Auckland__<id>_<name>.npz, data/fetch_log_auckland.csv
"""
import csv
import http.cookiejar
import io
import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
OUT = D / "series"
BASE = "https://environmentauckland.org.nz"
UA = {"User-Agent": "UoA research-lab HIRDS audit (non-commercial research)"}
FIRST_WY, LAST_WY = 1995, 2025


def session():
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    op.addheaders = list(UA.items())
    page = op.open(BASE + "/Disclaimer", timeout=120).read().decode("utf-8", "replace")
    tok = re.search(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"', page).group(1)
    op.open(BASE + "/AcceptDisclaimer", data=urllib.parse.urlencode(
        {"__RequestVerificationToken": tok, "returnUrl": "/Data/Map/Parameter/Rainfall"}).encode(), timeout=120).read()
    return op


def datasets(op):
    body = urllib.parse.urlencode({"sort": "", "page": 1, "pageSize": 5000, "group": "", "filter": "", "interval": "Latest",
                                   "calendar": "CALENDARYEAR", "parameters[0]": 78}).encode()
    r = urllib.request.Request(BASE + "/Data/Data_List", data=body, headers={"X-Requested-With": "XMLHttpRequest"})
    d = pd.DataFrame(json.loads(op.open(r, timeout=300).read())["Data"])
    d["from"] = pd.to_datetime(d.StartOfRecord, errors="coerce"); d["to"] = pd.to_datetime(d.EndOfRecord, errors="coerce")
    return d


def export(op, ds, a, b, tries=5):
    q = urllib.parse.urlencode({"DataSet": ds, "Calendar": "CALENDARYEAR", "DateRange": "Custom", "StartTime": f"{a} 00:00:00",
                                "EndTime": f"{b} 00:00:00", "UnitID": 332, "Conversion": "", "IntervalPoints": "PointsAsRecorded",
                                "ApprovalLevels": "False", "Qualifiers": "False", "Notes": "False", "Step": 1, "RoundData": "False",
                                "GradeCodes": "True", "InterpolationTypes": "False", "Timezone": 12, "ExportFormat": "csv",
                                "Compressed": "false"})
    for i in range(tries):
        try:
            r = urllib.request.Request(BASE + "/Export/DataSetToken?" + q, data=b"", headers={"X-Requested-With": "XMLHttpRequest"})
            tok = json.loads(op.open(r, timeout=120).read())["Token"]
            return op.open(BASE + "/Export/DataSet?" + q + "&" + urllib.parse.urlencode({"Token": tok}), timeout=900).read().decode("utf-8", "replace")
        except Exception as e:
            err = e
            time.sleep(10 + 20 * i)
    raise RuntimeError(str(err)[:200])


def one(args):
    op, row = args
    f = OUT / f"Auckland__{row.LocationIdentifier}_{re.sub(r'[^A-Za-z0-9._-]+', '_', row.Location)}.npz"
    if f.exists():
        return row.LocationIdentifier, "done", 0
    T, V, Q, bad = [], [], [], 0
    first = max(FIRST_WY, row["from"].year if row["from"].month >= 7 else row["from"].year - 1)
    for y in range(first, LAST_WY + 1):
        txt = export(op, row.DatasetIdentifier, f"{y}-07-01", f"{y + 1}-07-01")
        start = pd.Timestamp(f"{y}-07-01")               # windows share their boundary instant: keep it once (D5)
        for rec in csv.reader(io.StringIO(txt)):
            if len(rec) >= 2 and re.match(r"\d{4}-\d\d-\d\d \d\d:\d\d", rec[0]):
                if y > first and rec[0].startswith(f"{y}-07-01 00:00") and pd.Timestamp(rec[0]) == start:
                    continue
                try:
                    V.append(float(rec[1])); T.append(rec[0]); Q.append(int(rec[2]) if len(rec) > 2 and rec[2].strip() else -1)
                except ValueError:
                    bad += 1
    if not T:
        np.savez_compressed(f, t=np.array([], np.int64), v=np.array([], np.float32), q=np.array([], np.int16))
        return row.LocationIdentifier, "empty", 0
    # seconds are kept and nothing else is de-duplicated: several tips can share a minute (D5)
    t = pd.to_datetime(pd.Series(T)).to_numpy("datetime64[s]").astype(np.int64) / 60.0
    o = np.argsort(t, kind="stable")
    t, v, q = t[o], np.array(V, np.float32)[o], np.array(Q, np.int16)[o]
    np.savez_compressed(f, t=t, v=v, q=q, measurement=row.DatasetIdentifier, lat=row.LocY, lon=row.LocX)
    return row.LocationIdentifier, f"ok ({bad} unparsed)" if bad else "ok", int(len(t))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    op = session()
    d = datasets(op)
    d.to_parquet(D / "inventory_auckland.parquet")
    c = d[((d["from"] <= "2018-07-01") & (d["to"] >= "2026-06-30")) | ((d["from"] <= "2017-07-01") & (d["to"] >= "2025-06-30"))]
    c = c.sort_values("from").drop_duplicates("LocationIdentifier")
    print(len(d), "rainfall datasets;", len(c), "candidates", flush=True)
    log = []
    with ThreadPoolExecutor(2) as ex:                     # two connections: modest load on the council's portal
        for k, res in enumerate(ex.map(lambda r: _safe(op, r), [r for _, r in c.iterrows()]), 1):
            log.append(res)
            if k % 5 == 0:
                print(time.strftime("%H:%M:%S"), k, "/", len(c), flush=True)
    pd.DataFrame(log, columns=["site", "status", "records"]).to_csv(D / "fetch_log_auckland.csv", index=False)
    print("== done", pd.Series([s.split(" ")[0].rstrip(":") for _, s, _ in log]).value_counts().to_dict(), flush=True)


def _safe(op, r):
    try:
        return one((op, r))
    except Exception as e:
        return r.LocationIdentifier, "failed: " + str(e)[:120], 0


if __name__ == "__main__":
    main()
