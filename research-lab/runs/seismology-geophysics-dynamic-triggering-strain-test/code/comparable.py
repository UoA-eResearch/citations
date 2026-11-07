"""Comparable arms (D2, after the independent review's finding 1; post hoc). -> results/tables/comparable.json

Pseudo-triggers were drawn only at times at least 10 days from any global M >= 7 and 3 days from any M >= 6.5
(windows.py), but real triggers were not filtered. Their windows can carry another large earthquake's surface-wave
detection shadow and aftershock masking, which the null never sees. Here the real pairs are classified, and H1 and
H2 are recomputed with the preregistered rules (analyse.summarise, same bootstrap):

  pseudo_rule      the null's own rule applied to real triggers: no OTHER M >= 7 within 10 days and no other M >= 6.5
                   within 3 days of the origin (the two arms are then comparable by construction; the corrected primary)
  clean_windows    no other M >= 6.5 inside the pair's baseline window or between the origin and the post window's end
  post_contam      another M >= 6.5 between the origin and the post window's end
  base_only        another M >= 6.5 in the baseline window only
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import analyse as A  # noqa: E402

T, D = A.T, RUN / "data"
H, DAY = 3_600_000, 86_400_000


def main():
    pr = pd.read_parquet(T / "pairs_primary.parquet")
    d = pr[pr.in_population].copy()
    tr = pd.read_csv(D / "cat" / "triggers_m7.csv", parse_dates=["time"])
    org = dict(zip(tr.id, tr.time.astype("int64") // 10**6))
    g = pd.read_csv(D / "cat" / "global_m45.csv", usecols=["time", "mag"], parse_dates=["time"])
    t7 = np.sort(g[g.mag >= 7.0].time.astype("int64").to_numpy() // 10**6)
    t65 = np.sort(g[g.mag >= 6.5].time.astype("int64").to_numpy() // 10**6)

    def others(arr, lo, hi, self_t):
        a, b = np.searchsorted(arr, lo), np.searchsorted(arr, hi)
        x = arr[a:b]
        return int((np.abs(x - self_t) > 60_000).sum())          # exclude the trigger itself

    trig_clean = {}
    for tid_, o in org.items():
        trig_clean[tid_] = others(t7, o - 10 * DAY, o + 10 * DAY, o) == 0 and others(t65, o - 3 * DAY, o + 3 * DAY, o) == 0
    o = d.trigger.map(org).to_numpy()
    wave_end = o + d.dist_km.to_numpy() / 2.5 * 1000
    post1 = (np.ceil((wave_end + 2 * H) / H) + 24) * H
    base0 = (o // H - 168) * H
    post_c = np.array([others(t65, oo + 60_000, p1, oo) > 0 for oo, p1 in zip(o, post1)])
    base_c = np.array([others(t65, b0, oo, oo) > 0 for b0, oo in zip(base0, o)])
    d["pseudo_rule"] = d.trigger.map(trig_clean).to_numpy()
    d["post_contam"], d["base_contam"] = post_c, base_c
    rng = np.random.default_rng(A.SEED)
    sets = {"preregistered_all": d, "pseudo_rule": d[d.pseudo_rule], "clean_windows": d[~d.post_contam & ~d.base_contam],
            "post_contam": d[d.post_contam], "base_only": d[d.base_contam & ~d.post_contam]}
    out = {}
    for k, s in sets.items():
        r = A.summarise(s, rng)
        out[k] = {kk: r[kk] for kk in ("pairs", "triggers", "stations", "E", "E_ci95", "E1_ci90", "E5_minus_3E1", "E5_minus_3E1_ci95", "H1", "H2")}
        print(k, json.dumps({kk: out[k][kk] for kk in ("pairs", "triggers", "H1", "H2")}), out[k]["E"]["all"], out[k]["E_ci95"]["all"], flush=True)
    d["q"] = pd.qcut(d.strain.rank(method="first"), 5, labels=False) + 1
    out["post_contam_share_by_quintile"] = d.groupby("q").post_contam.mean().round(3).to_dict()
    out["triggers_failing_pseudo_rule"] = int(sum(1 for t in d.trigger.unique() if not trig_clean[t]))
    out["population_triggers"] = int(d.trigger.nunique())
    (T / "comparable.json").write_text(json.dumps(out, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
