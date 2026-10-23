"""Reviewer check: label structure of the 2014-15 and 2021 surveys (plan section 1, prompt item 3).

Aggregate output only; no coordinates are written.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-kauri-dieback-multitemporal-lidar")
OUT = RUN / "review" / "reviewer_checks"
raw = pd.read_parquet(RUN / "data" / "raw" / "obskauri.parquet")
xy = pd.read_parquet(RUN / "data" / "trees_xy.parquet")
t = pd.read_csv(RUN / "results" / "tables" / "trees.csv")
assert (t.OBJECTID.to_numpy() == xy.OBJECTID.to_numpy()).all(), "trees.csv / trees_xy.parquet row order differs"
t["x"], t["y"] = xy.x.to_numpy(), xy.y.to_numpy()
res = {}

for sv, name in (("Waitakere Track Survey 2014-2015", "s2014"), ("Waitakere Survey 2021", "s2021")):
    s = raw[(raw.SurveyName == sv) & raw.KDBFieldStatus.isin([1, 3, 4])].dropna(subset=["x", "y"]).copy()
    r = {"records": int(len(s)), "status_counts": {int(k): int(v) for k, v in s.KDBFieldStatus.value_counts().items()}}
    # nearest-neighbour distance among all records (any status)
    P = s[["x", "y"]].to_numpy()
    d, _ = cKDTree(P).query(P, k=2)
    nn = d[:, 1]
    r["nn_all_records_m"] = {"q05": round(float(np.percentile(nn, 5)), 2), "q25": round(float(np.percentile(nn, 25)), 2),
                             "median": round(float(np.median(nn)), 2), "q75": round(float(np.percentile(nn, 75)), 2),
                             "share_lt_2m": round(float((nn < 2).mean()), 3), "share_eq_0": round(float((nn == 0).mean()), 3),
                             "share_lt_5m": round(float((nn < 5).mean()), 3), "share_lt_15m": round(float((nn < 15).mean()), 3)}
    # the study's merge: same 2 m grid cell and same status
    cell = (np.round(s.x / 2).astype(int).astype(str) + "_" + np.round(s.y / 2).astype(int).astype(str))
    s["cell"] = cell
    merged = s.drop_duplicates(["cell", "KDBFieldStatus"])
    r["after_study_merge"] = {int(k): int(v) for k, v in merged.KDBFieldStatus.value_counts().items()}
    # proper 'within 2 m' merge (connected components of pairs < 2 m apart, same status) for comparison
    comp = {}
    for st, g in s.groupby("KDBFieldStatus"):
        Q = g[["x", "y"]].to_numpy()
        pairs = cKDTree(Q).query_pairs(2.0)
        parent = list(range(len(Q)))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a
        for a, b in pairs:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
        comp[int(st)] = len({find(i) for i in range(len(Q))})
    r["after_true_within_2m_merge"] = comp
    # class conflicts: 2 m cells holding both a positive and a negative
    pos_cells = set(s.cell[s.KDBFieldStatus.isin([3, 4])])
    neg_cells = set(s.cell[s.KDBFieldStatus == 1])
    r["cells_with_both_classes"] = len(pos_cells & neg_cells)
    r["positive_cells"] = len(pos_cells)
    # distance from each positive to the nearest negative, and vice versa
    pos = s[s.KDBFieldStatus.isin([3, 4])][["x", "y"]].to_numpy()
    neg = s[s.KDBFieldStatus == 1][["x", "y"]].to_numpy()
    dpn = cKDTree(neg).query(pos)[0]
    dnp = cKDTree(pos).query(neg)[0]
    r["positive_to_nearest_negative_m"] = {"median": round(float(np.median(dpn)), 1),
                                           "share_lt_2m": round(float((dpn < 2).mean()), 3),
                                           "share_lt_5m": round(float((dpn < 5).mean()), 3),
                                           "share_lt_15m": round(float((dpn < 15).mean()), 3),
                                           "share_lt_30m": round(float((dpn < 30).mean()), 3)}
    r["negative_to_nearest_positive_m"] = {"median": round(float(np.median(dnp)), 1),
                                           "share_lt_15m": round(float((dnp < 15).mean()), 3)}
    # how many negatives have a positive inside their 15 m circle (so the circle contains a symptomatic tree)
    cnt = cKDTree(pos).query_ball_point(neg, 15.0, return_length=True)
    r["negatives_with_positive_within_15m"] = int((cnt > 0).sum())
    # dates
    dt = pd.to_datetime(s.StartDate, unit="ms", errors="coerce")
    r["dates"] = {"min": str(dt.min().date()), "max": str(dt.max().date()), "n_unique_days": int(dt.dt.date.nunique())}
    res[name] = r

# status 2 (ill thrift) excluded: how many sit within 15 m of a kept negative?
s14 = raw[(raw.SurveyName == "Waitakere Track Survey 2014-2015")].dropna(subset=["x", "y"])
neg = s14[s14.KDBFieldStatus == 1][["x", "y"]].to_numpy()
st2 = s14[s14.KDBFieldStatus == 2][["x", "y"]].to_numpy()
cnt = cKDTree(st2).query_ball_point(neg, 15.0, return_length=True)
res["s2014_negatives_with_status2_within_15m"] = int((cnt > 0).sum())

# descriptors in trees.csv by survey/status
desc = {}
for (sv, st), g in t.groupby(["survey", "status"]):
    desc[f"{sv}_{st}"] = {"n": int(len(g)), "median_dist_track": round(float(g.dist_track.median()), 1),
                          "median_p95_e1_r15": round(float(g.p95_e1_m_r15.median()), 1),
                          "median_valid_r15": round(float(g.valid_r15.median()), 3),
                          "share_valid_r15_lt1": round(float((g.valid_r15 < 1).mean()), 3),
                          "median_slip_share_r15": round(float(g.slip_share_r15.median()), 3),
                          "share_slip_gt_0.25": round(float((g.slip_share_r15 > 0.25).mean()), 3),
                          "median_elev": round(float(g.elev.median()), 1), "median_slope": round(float(g.slope.median()), 1)}
res["trees_csv_descriptors"] = desc
res["slip_share_vs_slope_spearman_s2014"] = round(float(t[t.survey == "s2014"][["slip_share_r15", "slope"]].corr("spearman").iloc[0, 1]), 3)
json.dump(res, open(OUT / "labels_check.json", "w"), indent=1)
print(json.dumps(res, indent=1))
