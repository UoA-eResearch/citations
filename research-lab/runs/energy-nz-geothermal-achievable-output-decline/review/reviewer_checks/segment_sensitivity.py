"""Start-of-segment artefacts and the Ohaaki run-down's endpoint sensitivity, using the study's own analysis.py
functions (imported read-only) so differences are attributable to the window, not the method."""
import sys, json, warnings
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, sys.argv[1])            # code/ directory
import analysis as A
warnings.filterwarnings("ignore")
T = Path(sys.argv[2])
fm = pd.read_csv(T / "field_monthly.csv"); mem = pd.read_csv(T / "field_membership.csv")
fm["m"] = pd.PeriodIndex(fm.month, freq="M")

print("Wairakei field P95 by month 2014-01..2015-12 (sum of plants):")
w = fm[(fm.field == "Wairakei") & (fm.month >= "2014-01") & (fm.month <= "2015-12")]
print(w[["month", "p95", "n_plants"]].round(1).T.to_string(header=False))

def trend_window(field, a, b):
    segs = [g for g in A.segments(fm, mem, field) if str(g.m.min()) <= a <= str(g.m.max())]
    g = segs[0]; g = g[(g.m >= pd.Period(a, "M")) & (g.m <= pd.Period(b, "M"))]
    r = A.seg_trend(g)
    return A.pct(r["b"]), A.pct(r["b"] - 1.96 * r["se"]), A.pct(r["b"] + 1.96 * r["se"]), r

print("\nWairakei 2014-04..2026-09 segment with the start moved:")
for a in ["2014-04", "2014-10", "2015-01", "2015-07", "2016-01"]:
    p, lo, hi, _ = trend_window("Wairakei", a, "2026-09"); print(f"  start {a}: {p:+.3f} [{lo:+.3f}, {hi:+.3f}]")
print("\nNgatamariki 2013-09..2025-12 segment with the start moved:")
for a in ["2013-09", "2014-10", "2015-01"]:
    p, lo, hi, _ = trend_window("Ngatamariki", a, "2025-12"); print(f"  start {a}: {p:+.3f} [{lo:+.3f}, {hi:+.3f}]")
print("\nKawerau 2008-12..2016-12 (KGL only) with start moved:")
for a in ["2008-12", "2010-01", "2014-01"]:
    p, lo, hi, _ = trend_window("Kawerau", a, "2016-12"); print(f"  start {a}: {p:+.3f} [{lo:+.3f}, {hi:+.3f}]")
print("\nTauhara (Te Huka) 2010-11..2023-10 with start moved:")
for a in ["2010-11", "2012-01", "2013-01"]:
    p, lo, hi, _ = trend_window("Tauhara", a, "2023-10"); print(f"  start {a}: {p:+.3f} [{lo:+.3f}, {hi:+.3f}]")

print("\nOhaaki run-down, endpoint sensitivity (same GLS-AR(1) model):")
for a, b in [("2008-01", "2013-12"), ("2008-01", "2012-12"), ("2009-01", "2013-12"), ("2008-08", "2013-06"), ("2009-07", "2011-05"), ("2008-01", "2011-05"), ("2008-01", "2016-12"), ("2008-01", "2026-09"), ("2007-11", "2013-12")]:
    p, lo, hi, r = trend_window("Ohaaki", a, b); print(f"  {a}..{b} n={r['n']}: {p:+.2f} [{lo:+.2f}, {hi:+.2f}]")

# fleet recomputed with alternative Wairakei / Ngatamariki handling
res = A.field_trends(fm, mem)
base = A.fleet(res); print(f"\nfleet as reported: {A.pct(base['b']):+.4f} [{A.pct(base['b']-1.96*base['se']):+.3f}, {A.pct(base['b']+1.96*base['se']):+.3f}]")
def refleet(label, mods):
    r2 = {k: dict(v) for k, v in res.items()}
    for field, (a, b) in mods.items():
        _, _, _, rr = trend_window(field, a, b)
        # replace the field's segment list with just this one window (for 1-segment fields) or swap the matching segment
        segs = [s for s in r2[field]["segments"] if not (s["start"] <= a <= s["end"])] + [rr]
        w = np.array([1 / s["se"] ** 2 for s in segs]); b_ = float(np.sum(w * [s["b"] for s in segs]) / w.sum())
        r2[field].update(b=b_, se=float(1 / np.sqrt(w.sum())), segments=segs, resid=pd.concat([s["resid"] for s in segs]))
    fl = A.fleet(r2); v = A.verdicts(r2, fl)
    print(f"{label}: fleet {A.pct(fl['b']):+.4f} [{A.pct(fl['b']-1.96*fl['se']):+.3f}, {A.pct(fl['b']+1.96*fl['se']):+.3f}]  H1 {v['H1']['verdict']}")
refleet("Wairakei 2014 segment from 2015-01", {"Wairakei": ("2015-01", "2026-09")})
refleet("Ngatamariki from 2014-10", {"Ngatamariki": ("2014-10", "2025-12")})
refleet("both", {"Wairakei": ("2015-01", "2026-09"), "Ngatamariki": ("2014-10", "2025-12")})
# drop Wairakei's 2006-13 segment (Poihipi steam connection 2006-2011, NZGA) 
r3 = {k: dict(v) for k, v in res.items()}
segs = [s for s in r3["Wairakei"]["segments"] if s["start"] != "2006-01"]
w = np.array([1 / s["se"] ** 2 for s in segs]); r3["Wairakei"].update(b=float(np.sum(w*[s["b"] for s in segs])/w.sum()), se=float(1/np.sqrt(w.sum())), segments=segs, resid=pd.concat([s["resid"] for s in segs]))
fl = A.fleet(r3); print(f"Wairakei without 2006-13 segment: fleet {A.pct(fl['b']):+.4f} [{A.pct(fl['b']-1.96*fl['se']):+.3f}, {A.pct(fl['b']+1.96*fl['se']):+.3f}]  Wairakei {A.pct(r3['Wairakei']['b']):+.3f}")
# all three
r4 = {k: dict(v) for k, v in r3.items()}
for field, (a, b) in {"Wairakei": ("2015-01", "2026-09"), "Ngatamariki": ("2014-10", "2025-12")}.items():
    _, _, _, rr = trend_window(field, a, b)
    segs = [s for s in r4[field]["segments"] if not (s["start"] <= a <= s["end"])] + [rr]
    w = np.array([1 / s["se"] ** 2 for s in segs]); r4[field].update(b=float(np.sum(w*[s["b"] for s in segs])/w.sum()), se=float(1/np.sqrt(w.sum())), segments=segs, resid=pd.concat([s["resid"] for s in segs]))
fl = A.fleet(r4); v = A.verdicts(r4, fl); print(f"all three adjustments: fleet {A.pct(fl['b']):+.4f} [{A.pct(fl['b']-1.96*fl['se']):+.3f}, {A.pct(fl['b']+1.96*fl['se']):+.3f}]  H1 {v['H1']['verdict']}")
# present-capacity weights (last 12 months' mean P95 of each field's final segment) instead of all-time mean P95
print("\nweights: all-time mean P95 vs last-12-month mean P95 of final segment")
for f, r in res.items():
    last = r["segments"][-1]; ser = fm[(fm.field == f) & (fm.month <= last["end"])].tail(12).p95.mean()
    print(f"  {f:12s} {r['mean_mw']:7.1f}  {ser:7.1f}")
