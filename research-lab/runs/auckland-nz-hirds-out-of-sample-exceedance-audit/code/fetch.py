"""Rainfall series (plan section 1): native-resolution Hilltop data, with quality codes where served, for every
candidate gauge, water years 2005/06 to 2025/26. Raw values stay under data/ (not in git).

Candidate: a site's raw (not virtual) rainfall measurement whose record span covers at least 8 of the 9
out-of-sample water years (2017/18-2025/26). One measurement per site: "Rainfall" if present, else the longest.

  fetch.py [PER_SERVER] -> data/series/<server>__<site>.npz  (t: int64 minutes since 1970, v: float32 mm, q: int16)
                           data/fetch_log.csv
  fetch.py PER_SERVER early -> data/series_early/ : water years 1995/96-2004/05 for the same gauges, where their record
                           starts before 2005/06 (in-sample years only, for the sanity control; D3)
"""
import re
import sys
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
sys.path.insert(0, str(RUN / "code"))
from inventory import SERVERS, UA  # noqa: E402

FIRST_WY, LAST_WY = 2005, 2025          # water year y runs 1 July y to 1 July y+1
REC = re.compile(r"<E><T>([^<]+)</T><I1>([^<]*)</I1>(?:<Q1>([^<]*)</Q1>)?")
LIMIT = {}                                  # per-server semaphores, set in main(): at most PER_SERVER requests each


def candidates():
    inv = pd.read_parquet(D / "inventory.parquet")
    r = inv[(inv.virtual == False) & inv.measurement.notna()].copy()            # noqa: E712
    r["span_ok"] = ((r["from"] <= "2018-07-01") & (r["to"] >= "2026-06-30")) | ((r["from"] <= "2017-07-01") & (r["to"] >= "2025-06-30"))
    r = r[r.span_ok]
    r["pref"] = (r.measurement == "Rainfall").astype(int)
    r["len"] = (r["to"] - r["from"]).dt.days
    r["from_wy"] = np.where(r["from"].dt.month >= 7, r["from"].dt.year, r["from"].dt.year - 1)
    return r.sort_values(["pref", "len"], ascending=False).drop_duplicates(["server", "site"])


def get(url, tries=5):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600).read().decode("utf-8", "replace")
        except Exception as e:
            err = e
            time.sleep(5 + 10 * i)
    raise RuntimeError(str(err)[:200])


def one(row):
    f = OUT / f"{row.server}__{re.sub(r'[^A-Za-z0-9._-]+', '_', row.site)}.npz"
    first = max(FIRST_WY, int(row.from_wy))
    if f.exists():
        return row.server, row.site, "done", 0
    base = SERVERS[row.server]
    T, V, Q, n_bad = [], [], [], 0
    for y in range(first, LAST_WY + 1):
        url = (f"{base}?Service=Hilltop&Request=GetData&Site={urllib.parse.quote(row.site)}"
               f"&Measurement={urllib.parse.quote(row.measurement)}&From={y}-07-01&To={y + 1}-07-01&ShowQuality=Yes")
        with LIMIT[row.server]:
            x = get(url)
        for t, v, q in REC.findall(x):
            try:
                T.append(t); V.append(float(v)); Q.append(int(q) if q else -1)
            except ValueError:
                n_bad += 1
    if not T:
        np.savez_compressed(f, t=np.array([], np.int64), v=np.array([], np.float32), q=np.array([], np.int16))
        return row.server, row.site, "empty", 0
    t = pd.to_datetime(pd.Series(T)).to_numpy("datetime64[m]").astype(np.int64)
    o = np.argsort(t, kind="stable")
    t, v, q = t[o], np.array(V, np.float32)[o], np.array(Q, np.int16)[o]
    keep = np.r_[True, t[1:] != t[:-1]]                 # the yearly windows share their boundary instant
    np.savez_compressed(f, t=t[keep], v=v[keep], q=q[keep], measurement=row.measurement,
                        easting=row.easting, northing=row.northing)
    return row.server, row.site, "ok", int(keep.sum())


def main(per_server=3):
    import threading
    OUT.mkdir(parents=True, exist_ok=True)
    for s in SERVERS:
        LIMIT[s] = threading.Semaphore(per_server)
    c = candidates()
    print(len(c), "candidate gauges;", c.groupby("server").size().to_dict(), flush=True)
    log = []
    with ThreadPoolExecutor(per_server * len(SERVERS)) as ex:
        futs = [ex.submit(one, r) for r in c.itertuples()]
        for k, fu in enumerate(futs):
            try:
                res = fu.result()
            except Exception as e:
                r = c.iloc[k]; res = (r.server, r.site, "failed: " + str(e)[:120], 0)
            log.append(res)
            if (k + 1) % 20 == 0:
                print(time.strftime("%H:%M:%S"), k + 1, "/", len(c), flush=True)
    pd.DataFrame(log, columns=["server", "site", "status", "records"]).to_csv(D / "fetch_log.csv", index=False)
    print("== done", pd.Series([s.split(":")[0] for _, _, s, _ in log]).value_counts().to_dict(), flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "early":
        FIRST_WY, LAST_WY, OUT = 1995, 2004, D / "series_early"
        _cand = candidates

        def candidates():                        # noqa: F811  same gauges, records starting before 2005/06
            c = _cand()
            return c[c["from"] < "2005-07-01"]
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
