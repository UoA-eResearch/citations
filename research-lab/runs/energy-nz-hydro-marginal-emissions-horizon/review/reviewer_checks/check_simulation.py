"""Reviewer check 5: the H2 scheduling simulation, re-implemented independently. Writes out_simulation.json."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "out_simulation.json"
out = {}
s = pd.read_pickle(RUN / "data" / "series.pkl").sort_values("ts").reset_index(drop=True)
s["aef"] = s.E / s.D
s["blk"] = s.hh // 12
m = json.load(open(RUN / "results" / "tables" / "mef.json"))
sim = json.load(open(RUN / "results" / "tables" / "simulation.json"))
dr = np.load(RUN / "data" / "mef_draws.npz")
b1 = np.array([x["mef"] for x in m["blocks_1d"]]); F1 = np.array([x["F"] for x in m["blocks_1d"]]); d1 = dr["blocks"][:, 0:4]
MWH = 10.0
DEFAULT = set(range(20, 28))   # 10:00-14:00 local

rows = []
for d, g in s.groupby("date"):
    if len(g) < 46:
        continue
    a = g.aef.values; hh = g.hh.values; bl = g.blk.values
    dflt_mask = np.isin(hh, list(DEFAULT))
    dflt = np.where(dflt_mask)[0][:8]
    # 24-h window: the 8 consecutive half-hours (by row order within the local day) with the lowest mean AEF
    means = np.array([a[i:i + 8].mean() for i in range(len(a) - 7)])
    k = int(np.argmin(means)); sch = np.arange(k, k + 8)
    overlap = len(set(dflt) & set(sch))
    claimed = MWH * (a[dflt].sum() - a[sch].sum())
    realised = MWH * (b1[bl[dflt]].sum() - b1[bl[sch]].sum())
    # +-1 h: start in 09:00..11:00
    best = min(range(18, 23), key=lambda st: a[np.isin(hh, range(st, st + 8))].mean())
    sch1 = np.where(np.isin(hh, range(best, best + 8)))[0][:8]
    claimed1 = MWH * (a[dflt].sum() - a[sch1].sum()); realised1 = MWH * (b1[bl[dflt]].sum() - b1[bl[sch1]].sum())
    rows.append(dict(date=d, k=k, start_hh=int(hh[k]), overlap=overlap, claimed=claimed, realised=realised, moved_mwh=MWH * (8 - overlap),
                     sch_blocks=tuple(np.bincount(bl[sch], minlength=4)), night=int((bl[sch] == 0).sum()),
                     claimed1=claimed1, realised1=realised1, overlap1=len(set(dflt) & set(sch1)), moved1=MWH * (8 - len(set(dflt) & set(sch1)))))
df = pd.DataFrame(rows)
out["n_days"] = int(len(df))
tot_load = MWH * 8 * len(df)
out["24h"] = dict(claimed_t=float(df.claimed.sum()), claimed_theirs=sim["24h"]["claimed_t"], realised_point_t=float(df.realised.sum()),
                  realised_theirs=sim["24h"]["realised_t"], total_load_mwh=tot_load, mwh_actually_moved=float(df.moved_mwh.sum()),
                  share_days_overlap=float((df.overlap > 0).mean()), mean_overlap_halfhours=float(df.overlap.mean()),
                  t_per_mwh_total_load=float(df.claimed.sum() / tot_load), t_per_mwh_actually_moved=float(df.claimed.sum() / df.moved_mwh.sum()),
                  share_scheduled_in_night_block=float(df.night.sum() / (8 * len(df))), share_theirs=sim["24h"]["scheduled_share_by_block"]["0"],
                  start_hh_distribution=df.start_hh.value_counts().sort_index().to_dict(),
                  share_days_sign_reversal=float(((df.realised < 0) & (df.claimed > 0)).mean()), theirs_reversal=sim["24h"]["share_days_sign_reversal"])
# bootstrap capture ratio from their block draws
cnt = np.zeros(4)
for r in rows:
    cnt += np.array([2 if b in (1,) else 0 for b in range(4)])  # placeholder replaced below
# recompute net block counts directly
from_counts = np.array([0, 4 * len(df), 4 * len(df), 0], dtype=float)   # default: 4 half-hours in block 1 (10-12) and 4 in block 2 (12-14)
to_counts = np.array(df.sch_blocks.tolist(), dtype=float).sum(axis=0)
net = from_counts - to_counts
rd = MWH * (d1 @ net)
cr = rd / df.claimed.sum()
out["24h"]["capture_ci_mine"] = [float(np.nanpercentile(cr, 2.5)), float(np.nanpercentile(cr, 97.5))]; out["24h"]["capture_ci_theirs"] = sim["24h"]["capture_ci"]
out["24h"]["net_block_counts"] = net.tolist()
# realised saving restricted to the well-identified blocks only (drop night-block load from both sides: not a preregistered quantity, a probe)
# 1-hour variant
out["1h"] = dict(claimed_t=float(df.claimed1.sum()), claimed_theirs=sim["1h"]["claimed_t"], realised_t=float(df.realised1.sum()), realised_theirs=sim["1h"]["realised_t"],
                 capture=float(df.realised1.sum() / df.claimed1.sum()), capture_theirs=sim["1h"]["capture_ratio"],
                 mwh_actually_moved=float(df.moved1.sum()), total_load_mwh=tot_load, mean_overlap=float(df.overlap1.mean()),
                 t_per_mwh_moved=float(df.claimed1.sum() / df.moved1.sum()))
# where does the 1-h realised saving come from: only the net transfer between blocks 1 and 2
# AEF by block and its within-day range
out["aef_by_block"] = s.groupby("blk").aef.mean().round(4).to_dict()
daily_range = s.groupby("date").aef.agg(lambda x: x.max() - x.min())
out["aef_daily_range_t_per_MWh"] = dict(mean=float(daily_range.mean()), median=float(daily_range.median()))
# how often does the 24-h lowest-AEF window start at the very start of the day (k=0) or run to the end (edge effects of the day boundary)
out["24h"]["share_k0"] = float((df.k == 0).mean()); out["24h"]["share_k_end"] = float((df.k == df.k.max()).mean())
# weak-block rule: blocks touched by the moved load
out["blocks_touched_24h"] = sorted(int(b) for b in np.where((from_counts + to_counts) > 0)[0])
out["weak_block_rule_triggered"] = bool((F1[out["blocks_touched_24h"]] < 10).any())
# a 'conservative' scoring probe (not preregistered): set the night-block MEF to the lowest well-identified block value, or to 0
for name, val in (("night_as_morning_block", b1[1]), ("night_as_zero", 0.0), ("night_as_aef", s[s.blk == 0].aef.mean())):
    bb = b1.copy(); bb[0] = val
    out.setdefault("probe_night_block_value", {})[name] = float(MWH * (bb @ net) / df.claimed.sum())
json.dump(out, open(OUT, "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
