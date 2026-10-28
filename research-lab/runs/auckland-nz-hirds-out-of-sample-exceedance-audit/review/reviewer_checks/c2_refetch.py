"""Reviewer check 2: refetch a handful of gauge-years raw from the Hilltop servers (one connection, sequential) and
compare record by record with the stored series; and a window straddling a water-year boundary, to see what Hilltop
returns at the From/To instants and whether the stored splice preserves the rain across 1 July."""
import re, sys, time, urllib.parse, urllib.request
from pathlib import Path
import numpy as np, pandas as pd
RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-hirds-out-of-sample-exceedance-audit")
D = RUN / "data"
SERVERS = {"Northland": "https://hilltop.nrc.govt.nz/Data.hts", "HawkesBay": "https://data.hbrc.govt.nz/Envirodata/EMAR.hts",
           "Wellington": "https://hilltop.gw.govt.nz/Data.hts", "WestCoast": "https://hilltop.wcrc.govt.nz/Data.hts",
           "Tasman": "https://envdata.tasman.govt.nz/data.hts"}
UA = {"User-Agent": "UoA research-lab HIRDS audit (independent review check)"}
REC = re.compile(r"<E><T>([^<]+)</T><I1>([^<]*)</I1>(?:<Q1>([^<]*)</Q1>)?")
inv = pd.read_parquet(D / "inventory.parquet")
inv["stem"] = inv.server + "__" + inv.site.map(lambda s: re.sub(r"[^A-Za-z0-9._-]+", "_", s))

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600).read().decode("utf-8", "replace")

def fetch(stem, a, b):
    z = np.load(D / "series" / f"{stem}.npz", allow_pickle=False)
    meas = str(z["measurement"])
    row = inv[(inv.stem == stem) & (inv.measurement == meas)].iloc[0]
    url = (f"{SERVERS[row.server]}?Service=Hilltop&Request=GetData&Site={urllib.parse.quote(row.site)}"
           f"&Measurement={urllib.parse.quote(meas)}&From={a}&To={b}&ShowQuality=Yes")
    x = get(url)
    recs = REC.findall(x)
    t = pd.to_datetime(pd.Series([r[0] for r in recs])).to_numpy("datetime64[s]").astype(np.int64) / 60.0
    v = np.array([float(r[1]) for r in recs]); q = np.array([int(r[2]) if r[2] else -1 for r in recs])
    other = re.findall(r"<(Gap|Gaps|Error)[^>]*>", x)
    return t, v, q, len(x), other

def stored(stem, lo, hi):
    z = np.load(D / "series" / f"{stem}.npz", allow_pickle=False)
    t, v, q = z["t"].astype(float), z["v"].astype(float), z["q"].astype(int)
    m = (t >= lo) & (t <= hi)
    return t[m], v[m], q[m]

def mins(s):
    return int(pd.Timestamp(s).value // 60_000_000_000)

# (1) two full gauge-years from servers not covered by g4_raw_check (Northland, West Coast), compared record by record
for stem, wy in (("Northland__Waitangi_at_Ohaeawai", 2021), ("WestCoast__Haast_Rv_Roaring_Billy_WCRC", 2019)):
    a, b = f"{wy}-07-01", f"{wy + 1}-07-01"
    t, v, q, nbytes, other = fetch(stem, a, b)
    ts, vs, qs = stored(stem, mins(a), mins(b))
    print(f"== {stem} {wy}/{wy+1}: raw {len(t)} recs, {v.sum():.2f} mm | stored {len(ts)} recs, {vs.sum():.2f} mm | other tags {set(other)}")
    same_t = len(t) == len(ts) and np.allclose(t, ts)
    print("   identical times:", same_t, "| identical values:", same_t and np.allclose(v, vs), "| identical codes:", same_t and (q == qs).all())
    print("   first/last raw:", pd.Timestamp(int(t[0] * 60), unit="s"), v[0], q[0], "|", pd.Timestamp(int(t[-1] * 60), unit="s"), v[-1], q[-1])
    print("   same-minute tip pairs in raw:", int((np.diff(np.floor(t)) == 0).sum()), "| exact-duplicate times:", int((np.diff(t) == 0).sum()))
    print("   records exactly at From/To instants (raw):", int((t == mins(a)).sum()), int((t == mins(b)).sum()))
    time.sleep(2)

# (2) a window straddling 1 July 2022 at the Wellington gauge the lab traced, fetched in one request
stem = "Wellington__Akatarawa_River_at_Cemetery"
a, b = "2022-06-28", "2022-07-04"
t, v, q, nbytes, other = fetch(stem, a, b)
ts, vs, qs = stored(stem, mins(a), mins(b))
print(f"== boundary window {stem} {a}..{b}: raw {len(t)} recs {v.sum():.2f} mm | stored {len(ts)} recs {vs.sum():.2f} mm")
bd = mins("2022-07-01")
print("   raw has a record exactly at 2022-07-01 00:00:", int((t == bd).sum()), "| stored has:", int((ts == bd).sum()))
# records around the boundary in both
def show(tt, vv, qq, label):
    m = (tt >= bd - 180) & (tt <= bd + 180)
    print(f"   {label} records within 3 h of the boundary:", [(str(pd.Timestamp(int(x * 60), unit='s'))[5:16], round(float(y), 2), int(z)) for x, y, z in zip(tt[m], vv[m], qq[m])][:30])
show(t, v, q, "raw   "); show(ts, vs, qs, "stored")
# totals either side of the boundary
for lab, tt, vv in (("raw", t, v), ("stored", ts, vs)):
    print(f"   {lab}: rain in records with t <= boundary {vv[tt <= bd].sum():.2f}; t > boundary {vv[tt > bd].sum():.2f}")
# also compare raw vs stored at exact duplicate time stamps (several tips per second) in this window
print("   exact-duplicate times raw:", int((np.diff(t) == 0).sum()), "stored:", int((np.diff(ts) == 0).sum()))
