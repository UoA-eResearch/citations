"""Carbon-aware scheduling simulation (plan section 5; H2). Reads data/series.pkl, results/tables/mef.json and
data/mef_draws.npz. A 20 MW load runs 4 h a day, by default 10:00-14:00 local (half-hours 20-27, 10 MWh each).
Schedulers move it to the lowest-AEF half-hours: within the local day (8 consecutive half-hours; the H2 case), within
+-1 h of the default start, or within the local week (the week's 56 lowest-AEF half-hours). Claimed saving uses the
AEF; realised saving uses the time-of-day MEF (6-hour blocks) at 1 day (for the weekly variant, MEF at 7 days by block
when every block it touches has a first-stage F >= 10, otherwise the 1-day blocks). The capture ratio is
realised / claimed summed over 2015-2024; intervals come from the MEF bootstrap draws. H2 is Inconclusive (weak
instrument) if a block that carries moved load has F < 10. Writes results/tables/simulation.json."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
MWH = 10.0
DEFAULT = list(range(20, 28))


def main():
    s = pd.read_pickle(RUN / "data" / "series.pkl").sort_values("ts").reset_index(drop=True)
    s["aef"] = s.E / s.D
    m = json.load(open(T / "mef.json"))
    dr = np.load(RUN / "data" / "mef_draws.npz")
    b1 = np.array([x["mef"] for x in m["blocks_1d"]]); F1 = np.array([x["F"] for x in m["blocks_1d"]])
    b7 = np.array([x["mef"] for x in m["blocks_7d"]]); F7 = np.array([x["F"] for x in m["blocks_7d"]])
    d1, d7 = dr["blocks"][:, 0:4], dr["blocks"][:, 4:8]
    s["blk"] = s.hh // 12
    s["week"] = pd.to_datetime(s.date).dt.strftime("%G-%V")
    out = {}

    def score(moves, mef, draws, F):
        """moves: list of (from_idx_array, to_idx_array) of half-hour row indices, each carrying MWH."""
        fr = np.concatenate([a for a, _ in moves]); to = np.concatenate([b for _, b in moves])
        claimed = MWH * (s.aef.values[fr].sum() - s.aef.values[to].sum())
        bf, bt = s.blk.values[fr], s.blk.values[to]
        cnt = np.bincount(bf, minlength=4) - np.bincount(bt, minlength=4)          # net MWh/10 removed from each block
        realised = MWH * (cnt @ mef)
        rd = MWH * (draws @ cnt)
        used = sorted(set(bf) | set(bt))
        weak = bool((F[used] < 10).any())
        return claimed, realised, rd, used, weak

    variants = {}
    # 24-hour window: 8 consecutive half-hours of lowest mean AEF within the local day
    moves, days = [], []
    for d, g in s.groupby("date"):
        if len(g) < 46:
            continue
        a = g.aef.values; hh = g.hh.values
        k = int(np.argmin([a[i:i + 8].mean() for i in range(len(a) - 7)]))
        dflt = g.index.values[np.isin(hh, DEFAULT)][:8]
        sch = g.index.values[k:k + 8]
        moves.append((dflt, sch))
        days.append((d, MWH * (s.aef.values[dflt].sum() - s.aef.values[sch].sum()), MWH * (b1[s.blk.values[dflt]].sum() - b1[s.blk.values[sch]].sum())))
    variants["24h"] = (moves, b1, d1, F1, days)
    # 1-hour window: start within +-2 half-hours of the default start
    moves = []
    for d, g in s.groupby("date"):
        if len(g) < 46:
            continue
        hh = g.hh.values; a = g.aef.values
        starts = [st for st in range(18, 23)]
        best = min(starts, key=lambda st: a[np.isin(hh, range(st, st + 8))].mean())
        moves.append((g.index.values[np.isin(hh, DEFAULT)][:8], g.index.values[np.isin(hh, range(best, best + 8))][:8]))
    variants["1h"] = (moves, b1, d1, F1, None)
    # 7-day window: the week's 56 load half-hours to the week's 56 lowest-AEF half-hours
    moves = []
    for w, g in s.groupby("week"):
        if g.date.nunique() < 7:
            continue
        dflt = g.index.values[np.isin(g.hh.values, DEFAULT)]
        sch = g.index.values[np.argsort(g.aef.values)[: len(dflt)]]
        moves.append((dflt, sch))
    use7 = None
    variants["7d"] = (moves, b7, d7, F7, None)
    for name, (mv, mef, draws, F, days) in variants.items():
        c, r, rd, used, weak = score(mv, mef, draws, F)
        note = ""
        if name == "7d" and weak:      # fall back to the 1-day blocks (plan section 5)
            c, r, rd, used, weak = score(mv, b1, d1, F1)
            note = "MEF(7d) blocks weakly identified; scored with 1-day blocks"
        cr = rd / c
        frac = {int(b): float(np.mean(np.concatenate([s.blk.values[t] for _, t in mv]) == b)) for b in range(4)}
        out[name] = dict(claimed_t=float(c), realised_t=float(r), capture_ratio=float(r / c),
                         capture_ci=[float(np.nanpercentile(cr, 2.5)), float(np.nanpercentile(cr, 97.5))],
                         blocks_used=[int(u) for u in used], weak_block=weak, scheduled_share_by_block=frac, note=note)
        if days is not None:
            dd = pd.DataFrame(days, columns=["date", "claimed", "realised"])
            out[name]["share_days_sign_reversal"] = float(((dd.realised < 0) & (dd.claimed > 0)).mean())
    h2 = out["24h"]
    lo, hi = h2["capture_ci"]
    h2["verdict"] = ("Inconclusive (weak instrument)" if h2["weak_block"] else
                     "Supported" if hi < 0.5 else "Refuted" if lo >= 0.5 else "Inconclusive")
    out["aef_by_block_mean"] = s.groupby("blk").aef.mean().round(4).to_dict()
    json.dump(out, open(T / "simulation.json", "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
