"""G3 hand trace (added after review): recompute dv/v for three random scored pair-days from the raw daily correlation
files, independently of dvv.py's loop (brute-force fine grid), and compare with dvv_daily.parquet."""
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
from scipy.signal import butter, sosfiltfilt

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
FS, L = 20.0, 2000
dv = pd.read_parquet(T / "dvv_daily.parquet")
fit = pd.read_csv(T / "fit.csv")
scored = fit[(fit.train_coherence >= 0.5) & (fit.heldout_days >= 180) & fit.heldout_r2.notna()].pair
pairs = pd.read_csv(T / "pairs.csv").set_index("pair")
cand = dv[dv.pair.isin(scored)].sample(3, random_state=20261025)
files = sorted((RUN / "data" / "ccf").glob("*/*.npz"))
fdates = pd.to_datetime([f.stem for f in files])
stations = list(np.load(files[0])["stations"])
combos = list(itertools.combinations(range(len(stations)), 2))
sos = butter(4, [0.5, 2.0], btype="band", fs=FS, output="sos")
pos = np.arange(0, L + 1) / FS
out = []
for r in cand.itertuples():
    a, b = r.pair.split("-")
    p = combos.index((stations.index(a), stations.index(b)))
    seg_days = dv[(dv.pair == r.pair) & (dv.seg == r.seg)].date
    # reference: mean of the pair-segment's valid training days (dead days are not in dv; use days with windows)
    tr_files = [f for f, d in zip(files, fdates) if d <= pd.Timestamp("2020-12-31")]
    sym_of = {}

    def sym(f):
        if f not in sym_of:
            z = np.load(f)
            x = sosfiltfilt(sos, z["ccf"][p].astype(float)) if z["nwin"][p] > 0 else None
            sym_of[f] = None if x is None else 0.5 * (x[L:] + x[L::-1])
        return sym_of[f]
    t1 = float(pairs.loc[r.pair, "t1"]); win = (pos >= t1) & (pos <= t1 + 20); tw = pos[win]
    # segment span from the segments file
    sg = pd.read_csv(T / "segments.csv", parse_dates=["start", "end"])
    ka, kb = divmod(int(r.seg), 100)
    sa = sg[(sg.station == a) & (sg.k == ka)].iloc[0]; sb = sg[(sg.station == b) & (sg.k == kb)].iloc[0]
    lo_, hi_ = max(sa.start, sb.start), min(sa.end, sb.end)
    ref_days = [f for f, d in zip(files, fdates) if lo_ <= d <= min(hi_, pd.Timestamp("2020-12-31"))]
    refs = [s for s in (sym(f) for f in ref_days) if s is not None and np.std(s[win]) > 0]
    ref = np.mean(refs, axis=0)
    cur_days = [f for f, d in zip(files, fdates) if abs((d - r.date).days) <= 5 and lo_ <= d <= hi_]
    cs = [s for s in (sym(f) for f in cur_days) if s is not None and np.std(s[win]) > 0]
    cur = np.mean(cs, axis=0)
    rz = (ref[win] - ref[win].mean()) / ref[win].std()
    spl = CubicSpline(pos, cur)
    grid = np.arange(-0.02, 0.02 + 1e-12, 0.00005)
    S = spl(np.outer(1 + grid, tw)); S = (S - S.mean(1, keepdims=True)) / S.std(1, keepdims=True)
    cc = (S * rz).mean(1); e = grid[int(np.argmax(cc))]
    out.append({"pair": r.pair, "date": str(r.date.date()), "table_dvv_pct": round(float(r.dvv_pct), 4),
                "trace_dvv_pct": round(float(-100 * e), 4), "table_cc": round(float(r.cc), 4), "trace_cc": round(float(cc.max()), 4),
                "ref_days": len(refs), "stack_days": len(cs)})
(T / "handtrace.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
