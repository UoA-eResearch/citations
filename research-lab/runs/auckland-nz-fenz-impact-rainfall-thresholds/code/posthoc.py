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
    # Reviewer-prompted (finding 2): the depth model plus the place's climatology, log M6, as an additive covariate.
    class DesignM(A.Design):
        def raw(self, P):
            return np.hstack([super().raw(P), np.log(P.M6.to_numpy())[:, None]])
    dm = DesignM(tr, "ld6", regions); bm = A.fit(dm.X(tr), tr.y.to_numpy())
    ll_dm = A.logloss(dm.X(te), bm, te.y.to_numpy())
    base = A.Design(tr, None, regions); bb = A.fit(base.X(tr), tr.y.to_numpy())
    ll_b = A.logloss(base.X(te), bb, te.y.to_numpy()).mean()
    d2 = ll_dm - ll["R"]
    g2 = pd.DataFrame({"day": te.day.to_numpy(), "d": d2}).groupby("day").d.agg(["sum", "size"])
    rng = np.random.default_rng(A.SEED + 51); s2, n2 = g2["sum"].to_numpy(), g2["size"].to_numpy()
    bs2 = [s2[k].sum() / n2[k].sum() for k in (rng.integers(0, len(s2), len(s2)) for _ in range(A.B))]
    out["depth_plus_logM"] = {"LL_DM": round(float(ll_dm.mean()), 7), "LL_R": round(float(ll["R"].mean()), 7),
                              "DM_minus_R": float(d2.mean()), "ci": [float(np.percentile(bs2, 2.5)), float(np.percentile(bs2, 97.5))],
                              "S_DM_vs_D": round(float((ll_b - ll_dm.mean()) / (ll_b - ll["D"].mean())), 3),
                              "S_R_vs_D": round(float((ll_b - ll["R"].mean()) / (ll_b - ll["D"].mean())), 3)}
    # G3 unit traces (D4, review G3): three place-days followed from the FENZ daily counts and the raw gauge series
    # to both models' fitted probabilities; the 6-hour rain is recomputed exactly from the raw records.
    import g4_check as G4
    picks = {
        "Auckland held-out flood place-day (first by date)": te[(te.region == "Auckland Region") & (te.y > 0)].sort_values(["day", "suburb"]),
        "Tasman flood place-day on 27 June 2025 (largest 6-hour rain)": te[(te.region == "Tasman Region") & (te.day == "2025-06-27") & (te.y > 0)].sort_values("d6", ascending=False),
        "West Coast held-out place-day with no callout and over 20 mm (first by date)": te[(te.region == "West Coast Region") & (te.y == 0) & (te.d6 > 20)].sort_values(["day", "suburb"]),
    }
    out["traces"] = {}
    for name, cand in picks.items():
        r = cand.iloc[0]; e = cand.iloc[[0]]
        p = {k: float(1 / (1 + np.exp(-(d.X(e) @ b)))[0]) for k, (d, b) in models.items()}
        out["traces"][name] = {"suburb": r.suburb, "tla": r.tla, "day": str(pd.Timestamp(r.day).date()), "gauge": r.gauge,
                               "gauge_km": round(float(r.gauge_km), 2), "flood_exposures": int(r.flood), "d6_panel_mm": round(float(r.d6), 2),
                               "d6_raw_recomputed_mm": round(G4.exact_d6(r.gauge, pd.Timestamp(r.day)), 2), "M6_mm": round(float(r.M6), 1),
                               "rarity": round(float(r.d6 / r.M6), 3), "p_depth_model": p["D"], "p_rarity_model": p["R"]}
    (A.T / "posthoc.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
