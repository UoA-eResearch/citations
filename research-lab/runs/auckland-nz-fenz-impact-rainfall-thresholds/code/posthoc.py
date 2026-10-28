"""POST HOC (after the primary result): how much the held-out comparison rests on one event, and the three storm days
the plan names for G3, traced through both models.

  1. D_LL with 25-30 June 2025 (the Nelson-Tasman floods; 24 of the 64 held-out flood suburb-days) left out.
  2. For 27 Jan 2023 (Auckland), 14 Feb 2023 (Hawke's Bay) and 27 Jun 2025 (Nelson and Tasman): panel suburbs,
     suburbs with a callout, median 6-h rain and rarity, and the mean fitted probability under (D) and (R).

  posthoc.py -> results/tables/posthoc.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyse as A  # noqa: E402


def main():
    P = A.prep(pd.read_parquet(A.D / "panel.parquet"))
    tr, te = P[~P.test], P[P.test]
    regions = sorted(P.region.unique())
    models = {}
    for name, col in (("D", "ld6"), ("R", "lr6")):
        des = A.Design(tr, col, regions); models[name] = (des, A.fit(des.X(tr), tr.y.to_numpy()))
    ll = {k: A.logloss(d.X(te), b, te.y.to_numpy()) for k, (d, b) in models.items()}
    keep = (te.day < "2025-06-25").to_numpy()
    diff = ll["D"] - ll["R"]
    g = pd.DataFrame({"day": te.day.to_numpy()[keep], "d": diff[keep]}).groupby("day").d.agg(["sum", "size"])
    rng = np.random.default_rng(A.SEED + 50); s, n = g["sum"].to_numpy(), g["size"].to_numpy()
    bs = [s[k].sum() / n[k].sum() for k in (rng.integers(0, len(s), len(s)) for _ in range(A.B))]
    out = {"D_LL_all": float(diff.mean()), "D_LL_without_late_june_2025": float(diff[keep].mean()),
           "ci_without": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
           "held_out_floods_without": int(te.y.to_numpy()[keep].sum())}
    events = {"Auckland 2023-01-27": (["Auckland Region"], "2023-01-27"), "Hawke's Bay 2023-02-14": (["Hawke's Bay Region"], "2023-02-14"),
              "Nelson-Tasman 2025-06-27": (["Nelson Region", "Tasman Region"], "2025-06-27")}
    out["events"] = {}
    for name, (regs, day) in events.items():
        e = P[P.region.isin(regs) & (P.day == day)]
        p = {k: float((1 / (1 + np.exp(-(d.X(e) @ b)))).mean()) for k, (d, b) in models.items()}
        out["events"][name] = {"panel_suburbs": int(len(e)), "with_callout": int(e.y.sum()), "observed_rate": round(float(e.y.mean()), 3),
                               "median_d6_mm": round(float(e.d6.median()), 1), "median_rarity": round(float((e.d6 / e.M6).median()), 2),
                               "mean_p_depth_model": round(p["D"], 3), "mean_p_rarity_model": round(p["R"], 3)}
    (A.T / "posthoc.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
