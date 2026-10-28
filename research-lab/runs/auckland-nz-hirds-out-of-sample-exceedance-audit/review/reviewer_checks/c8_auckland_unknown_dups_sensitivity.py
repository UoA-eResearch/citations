"""Reviewer check 8: (a) why Auckland gauge-years lose known time (decomposition, aggregate only); (b) cross-server
duplicates among the 201 included gauges; (c) O/E sensitivity to removing maxima above HIRDS's 250-year depth;
(d) record structure of the Okoraka 2024 burst (council data, Northland Hilltop)."""
import re, sys
from pathlib import Path
import numpy as np, pandas as pd
RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-hirds-out-of-sample-exceedance-audit")
sys.path.insert(0, str(RUN / "code"))
import analyse as A, maxima as MX
M, H, S = A.load()
g = A.gauge_meta(H, S); m6 = A.qualify(M, 6, "primary")
g, dup = A.dedupe(g, m6[m6.ok].groupby("file").size())
yrs = list(range(2017, 2026))

print("== (a) Auckland unknown-time decomposition, water years 2018/19 and 2019/20, 2xx kept (S3 quality rule), 6 h")
rows = []
for f in sorted(x for x in M.file.unique() if x.startswith("Auckland__")):
    t, v, q = MX.load(MX.S / f"{f}.npz")
    if len(t) < 2:
        continue
    s, e, val, qq = t[:-1], t[1:], v[1:], q[1:]; L = e - s; ey = MX.wy_of(e)
    short = L <= 7 * 1440
    sil = pd.Series(np.where(short & (L > 60), L, 0.0)).groupby(ey).sum(); span = pd.Series(np.where(short, L, 0.0)).groupby(ey).sum()
    dense_y = (sil / span.where(span > 0)).fillna(1.0) <= 0.02; dense = pd.Series(ey).map(dense_y).fillna(False).to_numpy()
    bad = MX.bad_quality(qq, "S3") | ~np.isfinite(val) | MX.physical_bad(L, val)
    rain = np.where(bad, 0.0, val); wet = rain > 0
    unres = wet & (L > 15); dry_unk = (~wet) & dense & (L > 60)
    for y in (2018, 2019, 2022):
        m = ey == y; tot = 365.25 * 1440
        if m.sum() < 10:
            continue
        rows.append((y, L[m & bad].sum() / tot, L[m & unres & ~bad].sum() / tot, L[m & dry_unk & ~bad].sum() / tot, (wet & m).sum(), ((~wet) & m).sum(), float(np.median(L[m & wet])) if (m & wet).any() else np.nan,
                     L[m & unres & ~bad & (L > 1440)].sum() / tot))
R = pd.DataFrame(rows, columns=["wy", "bad_quality_share", "unresolved_wet_share", "dry_outage_share", "wet_records", "zero_records", "median_wet_L_min", "unresolved_share_from_gaps_over_1d"])
print(R.groupby("wy").agg(["median", "mean"]).round(3).T.to_string())
print("-> share of Auckland gauge-years (2018/19) whose records contain no logged zeros:", round(float((R[R.wy == 2018].zero_records == 0).mean()), 2))
# comparison: Hilltop non-dense included gauge-years' unresolved share
inc = A.included(m6, g) & set(A.depth_of(H, 6, 0.1).file)
rows = []
for f in sorted(inc)[:400]:
    t, v, q = MX.load(MX.S / f"{f}.npz"); s, e, val, qq = t[:-1], t[1:], v[1:], q[1:]; L = e - s; ey = MX.wy_of(e)
    bad = MX.bad_quality(qq, "primary") | ~np.isfinite(val) | MX.physical_bad(L, val); rain = np.where(bad, 0.0, val); wet = rain > 0
    m = ey == 2019
    if m.sum() > 10:
        rows.append((f.split("__")[0], L[m & wet & (L > 15) & ~bad].sum() / (365.25 * 1440), ((~wet) & m).sum() / m.sum()))
Rh = pd.DataFrame(rows, columns=["server", "unresolved_wet_share_2019", "zero_record_share"])
print("Hilltop included gauges, 2019/20: unresolved-wet share of the year, median by server:", Rh.groupby("server").unresolved_wet_share_2019.median().round(3).to_dict())
print("   zero-record share median by server:", Rh.groupby("server").zero_record_share.median().round(2).to_dict())

print("\n== (b) cross-server near-duplicates among the 201 included gauges (different server, within 2 km, or sharing a distinctive name token)")
gi = g[g.file.isin(inc)].copy(); gi["server"] = gi.file.str.split("__").str[0]
def toks(f):
    return set(w for w in re.split(r"[^a-z0-9]+", f.split("__", 1)[1].lower()) if len(w) > 4 and w not in {"river", "stream", "rainfall", "creek", "climate"})
pairs = []
for i, a in gi.iterrows():
    for j, b in gi.iterrows():
        if a.file < b.file and a.server != b.server:
            dkm = np.hypot((a.lon - b.lon) * 111.32 * np.cos(np.radians(a.lat)), (a.lat - b.lat) * 110.57)
            shared = toks(a.file) & toks(b.file)
            if dkm <= 2 or (shared and dkm <= 15):
                pairs.append((a.file, b.file, round(dkm, 2), sorted(shared)))
for p in pairs:
    print("  ", p)
print("  pairs:", len(pairs))
x = A.oe_table(A.oos_rows(m6, g), A.depth_of(H, 6, 0.1), yrs, inc)
for a, b, dkm, _ in pairs:
    xa, xb = x[x.file == a], x[x.file == b]
    both = xa.merge(xb, on="wy", suffixes=("_a", "_b"))
    print(f"   {a} vs {b}: years in common {len(both)}, exceed both {int((both.exceed_a & both.exceed_b).sum())}, a only {int((both.exceed_a & ~both.exceed_b).sum())}, b only {int((~both.exceed_a & both.exceed_b).sum())}; max ratio median {np.median(both.max_point_a / both.max_point_b):.2f}")

print("\n== (c) O/E sensitivity to removing gauge-years whose maximum exceeds HIRDS's 250-year depth at that duration")
d250 = H[(H.table == "historical") & np.isclose(H.ari, 250)].pivot_table(index="file", columns="duration_h", values="mm")
for d in (1, 6, 24):
    for aep in (0.1, 0.02):
        md = A.qualify(M, d, "primary"); dd = A.depth_of(H, d, aep); incd = A.included(md, g) & set(dd.file)
        xd = A.oe_table(A.oos_rows(md, g), dd, yrs, incd); r250 = xd.max_point / xd.file.map(d250[float(d)])
        O, n = int(xd.exceed.sum()), len(xd)
        for thr in (1.0, 1.5):
            drop = r250 > thr
            print(f"  {d:>2} h {int(aep*100):>2}% AEP: O/E {O/(aep*n):.3f}; dropping {int(drop.sum())} gauge-years above {thr}x the 250-yr depth -> {int((xd.exceed & ~drop).sum())}/{aep*(n-drop.sum()):.1f} = {(xd.exceed & ~drop).sum()/(aep*(n-drop.sum())):.3f}; expected count above the 250-yr depth if HIRDS held: {0.004*n:.1f}")
        break

print("\n== (d) Okoraka at Ngatawhiti Road, 1 Sep 2024 burst: record structure (Northland Hilltop, public)")
f = "Northland__Okoraka_at_Ngatawhiti_Road"
t, v, q = MX.load(MX.S / f"{f}.npz"); s, e, val, qq = t[:-1], t[1:], v[1:], q[1:]; L = e - s
tm = m6[(m6.file == f) & (m6.wy == 2024)].t_max.iloc[0]
w = (e > tm - 360) & (e <= tm)
print("  records in the 6-h window:", int(w.sum()), "| wet:", int((val[w] > 0).sum()), "| quality codes:", dict(zip(*np.unique(qq[w], return_counts=True))))
print("  interval lengths (min) value counts:", pd.Series(L[w]).round(1).value_counts().head(5).to_dict())
print("  records >= 5 mm:", int((val[w] >= 5).sum()), "| >= 10 mm:", int((val[w] >= 10).sum()), "| sum of records >= 5 mm:", round(float(val[w][val[w] >= 5].sum()), 1), "of", round(float(val[w].sum()), 1))
print("  largest 10 records (mm) and their minute offsets from window end:", [(round(float(a), 1), int(tm - b)) for a, b in sorted(zip(val[w], e[w]), reverse=True)[:10]])
print("  year total 2024/25 (mm):", round(float(val[(e >= MX.wy_start(2024)) & (e < MX.wy_start(2025))].sum()), 0), "| other years median:", round(float(np.median([val[(e >= MX.wy_start(y)) & (e < MX.wy_start(y + 1))].sum() for y in range(2017, 2024)])), 0))
print("  the gauge's other annual 6-h maxima 2017-2025:", m6[(m6.file == f) & (m6.wy >= 2017)].set_index("wy").max_point.round(1).to_dict())
