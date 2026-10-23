"""Do the UHSLC fast-delivery (FD) and research-quality (RQ) hourly series share a datum? The study's series switch from
RQ to FD at the end of 2021 (Tarawa, Majuro, Funafuti, Kwajalein), inside the Sentinel-2 epoch. tides.py kept RQ where
both exist, so the FD values of the overlap were discarded; this re-downloads FD and compares over 2017-2021."""
import io, sys, urllib.request
import numpy as np, pandas as pd
RUN = "/mnt/citations/research-lab/runs/blue-pacific-reef-island-area-tide-corrected"
for name, gid in (("tarawa", 2), ("majuro", 5), ("funafuti", 25), ("kwajalein", 55)):
    url = f"https://uhslc.soest.hawaii.edu/data/csv/fast/hourly/h{gid:03d}.csv"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research-lab-review"}), timeout=300) as r:
        d = pd.read_csv(io.BytesIO(r.read()), header=None, names=["y", "m", "d", "h", "v"])
    d = d[d.v != -32767]
    d["time"] = pd.to_datetime(dict(year=d.y, month=d.m, day=d.d, hour=d.h), utc=True)
    fd = d.set_index("time").v
    g = pd.read_parquet(f"{RUN}/data/tides/{gid:03d}.parquet").set_index("time")
    rq = g[g.source == "RQ"].level_mm
    j = pd.concat([rq.rename("rq"), fd.rename("fd")], axis=1).dropna()
    j = j[(j.index >= "2017-01-01")]
    diff = j.fd - j.rq
    byy = diff.groupby(j.index.year).agg(["mean", "std", "size"]).round(1)
    print(f"{name} (gauge {gid}): overlap hours {len(j)}, FD-RQ mean {diff.mean():.1f} mm, SD {diff.std():.1f}, |diff|>50 mm in {(diff.abs()>50).mean()*100:.1f}% of hours")
    print(byy.to_string())
    print("  FD hours missing where RQ exists 2017-2021:", int(rq[(rq.index >= '2017-01-01') & (rq.index < '2022-01-01')].index.difference(fd.index).size),
          "; RQ last:", rq.index.max(), "; study series switches to FD at", g[g.source == 'FD'].index.min(), flush=True)
