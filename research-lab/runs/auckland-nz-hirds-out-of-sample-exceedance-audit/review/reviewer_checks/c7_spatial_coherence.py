"""Reviewer check 7: are the maxima far above HIRDS's 250-year depth real storms or data faults? For each such gauge-year
(6 h above 1.3x, 1 h and 24 h above 1.3x the 250-yr depth), the structure of the maximum window and the largest same-duration
total at the other included gauges of the same council within +-12 h of the window end, with the nearest distance."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-hirds-out-of-sample-exceedance-audit")
sys.path.insert(0, str(RUN / "code"))
import analyse as A, maxima as MX
M, H, S = A.load()
g = A.gauge_meta(H, S); m6 = A.qualify(M, 6, "primary")
g, dup = A.dedupe(g, m6[m6.ok].groupby("file").size()); g = g.set_index("file")
d250 = H[(H.table == "historical") & np.isclose(H.ari, 250)].pivot_table(index="file", columns="duration_h", values="mm")
yrs = list(range(2017, 2026))
cache = {}
def series(f):
    if f not in cache:
        t, v, q = MX.load(MX.S / f"{f}.npz"); s, e, val, qq = t[:-1], t[1:], v[1:], q[1:]; L = e - s
        bad = MX.bad_quality(qq, "primary") | ~np.isfinite(val) | MX.physical_bad(L, val)
        rain = np.where(bad, 0.0, val); x = np.r_[s[0], e]; C = np.r_[0.0, np.cumsum(rain)]
        ux, idx = np.unique(x, return_index=True); last = np.r_[idx[1:] - 1, len(x) - 1]
        cache[f] = (ux, C[last], e, val, L, bad)
    return cache[f]
def max_total(f, t0, d, half=720):
    ux, Cu, *_ = series(f)
    ends = np.arange(t0 - half, t0 + half + 1, 5.0)
    return float((np.interp(ends, ux, Cu) - np.interp(ends - d * 60, ux, Cu)).max())
def km(a, b):
    return float(np.hypot((g.lon[a] - g.lon[b]) * 111.32 * np.cos(np.radians(g.lat[a])), (g.lat[a] - g.lat[b]) * 110.57))
out = []
for d in (6, 1, 24):
    md = A.qualify(M, d, "primary"); dd = A.depth_of(H, d, 0.1); inc = A.included(md, g.reset_index()) & set(dd.file)
    xd = A.oe_table(A.oos_rows(md, g.reset_index()), dd, yrs, inc)
    xd["r250"] = xd.max_point / xd.file.map(d250[float(d)])
    for r in xd[xd.r250 > 1.3].sort_values("r250", ascending=False).itertuples():
        ux, Cu, e, val, L, bad = series(r.file)
        w = (e > r.t_max - d * 60) & (e <= r.t_max) & ~bad
        srv = r.file.split("__")[0]
        others = [f for f in inc if f != r.file and f.split("__")[0] == srv]
        peers = sorted(((max_total(f, r.t_max, d), km(r.file, f), f) for f in others), key=lambda z: z[1])
        near = peers[:3]; best = max(peers, key=lambda z: z[0]) if peers else (np.nan, np.nan, "")
        out.append((d, r.file, r.wy, str(pd.Timestamp(int(r.t_max), unit="m"))[:16], round(r.max_point, 1), round(r.mm, 1), round(r.r250, 2), int(w.sum()), int((val[w] > 0).sum()),
                    round(float(val[w].max()), 1), round(float(L[w][np.argmax(val[w])]), 1), round(float(np.median(L[w & (val > 0)])) if (w & (val > 0)).any() else np.nan, 1),
                    "; ".join(f"{t_:.0f}mm@{k_:.1f}km" for t_, k_, _ in near), f"{best[0]:.0f}mm@{best[1]:.1f}km"))
O = pd.DataFrame(out, columns=["d_h", "file", "wy", "t_end", "max", "depth10", "x_250yr", "recs_in_window", "wet_recs", "largest_rec", "its_L_min", "median_wet_L_min", "nearest_3_same_council(total@dist)", "largest_peer"])
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 80)
print(O.to_string(index=False))
O.to_csv(RUN / "review" / "reviewer_checks" / "c7_spatial_coherence.csv", index=False)
