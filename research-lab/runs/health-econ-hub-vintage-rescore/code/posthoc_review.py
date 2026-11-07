"""Post-hoc checks after the independent review (D2; none of this is preregistered). -> results/tables/posthoc_review.json

  1. Eligibility: the best model when only hub-produced models (FluSight-*) and baselines are excluded, instead of
     any name containing "ensemble" (finding 2a).
  2. Leader instability under one truth: in bootstrap resamples over reference dates, how often the leader under
     first-report truth differs from its own point-estimate leader, and likewise for final truth, beside the
     study's first-vs-final criterion (finding 2b). B = 200.
  3. Finality of 2022-23: old-hub last version against the new hub's latest value for the same location-weeks,
     and the 2022-23 reversal share when "final" is the new hub's latest value (finding 4).
  4. Units dropped for missing truth (finding 5).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import score as S  # noqa: E402

INT, TAB = S.INT, S.TAB
BB, SEED = 200, 20261107


def alt_excluded(m):
    return m.startswith("FluSight-") or "baseline" in m.lower()


def leaders(theta, rule):
    cand = [(v, m) for m, v in theta.items() if not rule(m) and np.isfinite(v)]
    return min(cand)[1] if cand else None


def main():
    F = pd.read_parquet(INT / "forecasts.parquet")
    T = pd.read_parquet(INT / "truth.parquet")
    mat_o, j_o = S.matrices(F[F.hub == "old"], T[T.hub == "old"])
    mat_n, j_n = S.matrices(F[F.hub == "new"], T[T.hub == "new"])
    mat = {**mat_o, **mat_n}
    out = {}

    # 1. eligibility
    _, _, _, best = S.analyse(mat, lambda k, d: np.ones(len(d["cells"])))
    elig = {}
    for k, v in best.items():
        key = f"{k[0]} h{int(k[1])}"
        tf, tl = v["theta_first"], v["theta_final"]
        rank_first = sorted(tf, key=tf.get)
        elig[key] = {"name_rule": {"first": v["first"], "final": v["final"]},
                     "hub_and_baseline_rule": {"first": leaders(tf, alt_excluded), "final": leaders(tl, alt_excluded)},
                     "overall_lowest_first": rank_first[0], "overall_lowest_final": sorted(tl, key=tl.get)[0]}
        if "NEU_ISI-AdaptiveEnsemble" in tf:
            elig[key]["NEU_ISI-AdaptiveEnsemble"] = {"first": round(tf["NEU_ISI-AdaptiveEnsemble"], 3), "final": round(tl["NEU_ISI-AdaptiveEnsemble"], 3)}
    out["eligibility"] = elig
    out["changed_under_hub_and_baseline_rule"] = [k for k, v in elig.items()
                                                  if v["hub_and_baseline_rule"]["first"] != v["hub_and_baseline_rule"]["final"]]

    # 2. leader instability under one truth
    point = {k: (v["first"], v["final"]) for k, v in best.items()}
    rng = np.random.default_rng(SEED)
    seasons = sorted({k[0] for k in mat})
    dates = {s: sorted({d for k, v in mat.items() if k[0] == s for d in v["cells"].ref_date}) for s in seasons}
    cnt = {k: {"first_vs_own_point": 0, "final_vs_own_point": 0, "first_vs_final": 0} for k in best}
    for b in range(BB):
        draw = {s: pd.Series(rng.choice(len(dates[s]), len(dates[s]))).value_counts() for s in seasons}
        dw = {s: pd.Series(draw[s].values, index=[dates[s][i] for i in draw[s].index]) for s in seasons}
        _, _, _, bb = S.analyse(mat, lambda k, d: d["cells"].ref_date.map(dw[k[0]]).fillna(0).to_numpy(float))
        for k, v in bb.items():
            if k not in cnt:
                continue
            cnt[k]["first_vs_own_point"] += v["first"] != point[k][0]
            cnt[k]["final_vs_own_point"] += v["final"] != point[k][1]
            cnt[k]["first_vs_final"] += v["first"] != v["final"]
    out["leader_instability_B"] = BB
    out["leader_instability"] = {f"{k[0]} h{int(k[1])}": {a: round(c / BB, 3) for a, c in v.items()} for k, v in cnt.items()}

    # 3. finality of 2022-23
    o = T[T.hub == "old"].set_index(["location", "target_end_date"])
    n = T[T.hub == "new"].set_index(["location", "target_end_date"])
    both = o[["final_value", "first_value"]].join(n[["final_value"]].rename(columns={"final_value": "new_latest"}), how="inner")
    both = both[(both.index.get_level_values(1) >= "2022-08-01") & (both.index.get_level_values(1) < "2023-08-01") & (both.new_latest > 0)]
    d = (both.final_value - both.new_latest) / both.new_latest * 100
    out["finality_2022_23"] = {"location_weeks": int(len(both)), "share_identical": round(float((d == 0).mean()), 4),
                               "share_differ_over_10pct": round(float((d.abs() > 10).mean()), 4),
                               "median_pct": round(float(d.median()), 2), "mean_pct": round(float(d.mean()), 2)}
    T2 = T[T.hub == "old"].merge(T[T.hub == "new"][["location", "target_end_date", "final_value"]].rename(columns={"final_value": "new_latest"}),
                                 on=["location", "target_end_date"], how="left")
    T2["final_value"] = T2.new_latest
    mat_o2, _ = S.matrices(F[F.hub == "old"], T2.dropna(subset=["final_value"]))
    r, t, per, best2 = S.analyse(mat_o2, lambda k, d: np.ones(len(d["cells"])))
    out["sensitivity_2022_23_final_is_new_hub_latest"] = {"reversals": r, "pairs": t, "share": round(r / t, 4) if t else None,
                                                          "best_changed": [f"{k[0]} h{int(k[1])}" for k, v in best2.items() if v["first"] != v["final"]]}

    # 4. units dropped for missing truth
    units = F[["season", "model", "ref_date", "location", "horizon", "target_end_date"]].drop_duplicates()
    J = pd.concat([j_o, j_n])
    scored = J[["season", "model", "ref_date", "location", "horizon"]].drop_duplicates()
    m = units.merge(scored, how="left", indicator=True)
    dropped = m[m._merge == "left_only"]
    out["units_dropped"] = {"total": int(len(dropped)), "by_season": dropped.season.value_counts().to_dict(),
                            "by_location": dropped.location.value_counts().head(6).to_dict(),
                            "by_model_top": dropped.model.value_counts().head(4).to_dict()}
    (TAB / "posthoc_review.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps({k: out[k] for k in out if k != "eligibility"}, indent=1, default=str))
    for k, v in elig.items():
        if k.startswith("2024") or v["hub_and_baseline_rule"] != v["name_rule"]:
            print(k, v)


if __name__ == "__main__":
    main()
