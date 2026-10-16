"""Why the review's cumulative V1 gave -0.17 and review_response.py gives -0.19: the review kept each field's original
mean-P95 weight after trimming; review_response.py recomputes it from the trimmed months. Both shown."""
import sys, warnings; from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, sys.argv[1]); import analysis as A
warnings.filterwarnings("ignore")
T = Path(sys.argv[2]); fm = pd.read_csv(T/"field_monthly.csv"); mem = pd.read_csv(T/"field_membership.csv")
res = A.field_trends(fm, mem)
def trim(g, a): return g[g.m >= pd.Period(a, "M")]
segs = {f: A.segments(fm, mem, f) for f in res}
W = [A.seg_trend(trim(segs["Wairakei"][1], "2015-01"))]; N = [A.seg_trend(trim(segs["Ngatamariki"][0], "2014-10"))]
for label, keep_weights in (("original mean-P95 weights (review)", True), ("recomputed weights (review_response.py)", False)):
    r = {k: dict(v) for k, v in res.items()}
    for f, fits in (("Wairakei", W), ("Ngatamariki", N)):
        w = np.array([1/s["se"]**2 for s in fits]); b = float(np.sum(w*[s["b"] for s in fits])/w.sum())
        upd = dict(b=b, se=float(1/np.sqrt(w.sum())), segments=fits, resid=pd.concat([s["resid"] for s in fits]))
        if not keep_weights: upd["mean_mw"] = float(sum(s["mean_mw"]*s["n"] for s in fits)/sum(s["n"] for s in fits))
        r[f].update(upd)
    fl = A.fleet(r); print(f"{label}: fleet {A.pct(fl['b']):+.4f} [{A.pct(fl['b']-1.96*fl['se']):+.3f}, {A.pct(fl['b']+1.96*fl['se']):+.3f}]  Wairakei weight {fl['weights']['Wairakei']:.3f}")
