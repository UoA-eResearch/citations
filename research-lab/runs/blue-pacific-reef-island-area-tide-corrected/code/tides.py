"""Hourly sea level for the eight gauge atolls (plan section 2): UHSLC research-quality (RQ) hourly where it exists,
fast-delivery (FD) hourly otherwise. Values in mm; -32767 is missing. Writes data/tides/<gauge>.parquet (time UTC,
level_mm, source) and results/tables/tides_log.json (spans, coverage, mean over 1999-2026)."""
import io
import json
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "data" / "tides"
GAUGES = {"tarawa": 2, "majuro": 5, "funafuti": 25, "kwajalein": 55, "kanton": 13, "kiritimati": 11,
          "penrhyn": 24, "kapingamarangi": 29}
BASE = "https://uhslc.soest.hawaii.edu/data/csv"


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research-lab"}), timeout=300) as r:
        d = pd.read_csv(io.BytesIO(r.read()), header=None, names=["y", "m", "d", "h", "v"])
    d = d[d.v != -32767]
    d["time"] = pd.to_datetime(dict(year=d.y, month=d.m, day=d.d, hour=d.h), utc=True)
    return d[["time", "v"]].rename(columns={"v": "level_mm"})


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {f["properties"]["uhslc_id"]: f["properties"]
            for f in json.load(open(RUN / "data" / "raw" / "uhslc_meta.geojson"))["features"]}
    log = {}
    for name, gid in GAUGES.items():
        m = meta[gid]
        fd = get(f"{BASE}/fast/hourly/h{gid:03d}.csv").assign(source="FD")
        rq = []
        for v in m.get("rq_versions") or []:
            try:
                rq.append(get(f"{BASE}/rqds/{m['rq_basin']}/hourly/h{gid:03d}{v}.csv").assign(source="RQ"))
            except Exception as e:
                print(name, "rq", v, repr(e)[:80])
        d = pd.concat(rq + [fd]).drop_duplicates("time", keep="first").sort_values("time").reset_index(drop=True)
        d.to_parquet(OUT / f"{gid:03d}.parquet", index=False)
        w = d[(d.time >= "1999-01-01") & (d.time < "2026-10-01")]
        hours = (pd.Timestamp("2026-10-01", tz="UTC") - pd.Timestamp("1999-01-01", tz="UTC")) / pd.Timedelta("1h")
        log[name] = {"gauge": gid, "first": str(d.time.min()), "last": str(d.time.max()), "rq_hours": int((d.source == "RQ").sum()),
                     "fd_hours": int((d.source == "FD").sum()), "coverage_1999_2026": round(len(w) / hours, 3),
                     "mean_mm_1999_2026": round(float(w.level_mm.mean()), 1), "rq_versions": m.get("rq_versions")}
        print(name, log[name], flush=True)
    json.dump(log, open(RUN / "results" / "tables" / "tides_log.json", "w"), indent=1)


if __name__ == "__main__":
    main()
