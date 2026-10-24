"""Reviewer check 2: H3 under small implementation choices, IEEE-rule degeneracy, margins, and the Commission's
own DPP3-period assessed values (DPP4 reasons, Attachment E, Table E3).

Uses the study's rules.py and interim unplanned panel read-only. Writes 02_h3_robustness.json next to this script.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
sys.path.insert(0, str(RUN / "code"))
import rules as R  # noqa: E402
import analysis as A  # noqa: E402

T = RUN / "results" / "tables"
U = pd.read_parquet(R.INT / "unplanned.parquet")
lim = pd.read_csv(T / "dpp_limits.csv")
det = lim[lim.dpp == "DPP3"].set_index("edb_current")

# Commission's record: DPP4 reasons Attachment E, Table E3 (unplanned SAIDI assessed values 2021-2024, DPP3 limits)
E3 = {"Alpine Energy": [77.48, 89.32, 92.94, 86.40], "EA Networks": [75.07, 61.31, 63.41, 50.57],
      "Electricity Invercargill": [9.67, 15.38, 17.80, 11.24], "Firstlight Network": [180.86, 214.72, 295.44, 314.65],
      "Horizon Energy": [133.54, 134.42, 159.84, 133.10], "Nelson Electricity": [0.00, 8.53, 6.21, 3.57],
      "Network Tasman": [87.45, 79.53, 72.01, 49.48], "Orion NZ": [29.70, 52.95, 43.37, 39.57],
      "OtagoNet": [133.20, 141.82, 143.82, 125.80], "Powerco": [None, None, None, 139.38],
      "The Lines Company": [154.74, 159.78, 238.94, 155.53], "Top Energy": [300.83, 342.68, 513.96, 292.29],
      "Unison Networks": [44.64, 69.40, 75.99, 70.19], "Vector Lines": [86.30, 92.42, 118.74, 98.37],
      "Wellington Electricity": [28.41, 25.32, 34.92, 34.28]}
E3_noncompliant = {"Firstlight Network": [2023, 2024], "The Lines Company": [2023], "Top Energy": [2023], "Vector Lines": [2023]}


def ieee_thr(dser, ddof=1):
    v = np.log(dser[dser > 0].to_numpy())
    return float(np.exp(v.mean() + 2.5 * v.std(ddof=ddof)))


def h3_variant(strict_ref=False, strict_ass=True, bv_source="det", ieee_years=(2010, 2019), ddof=1, b_mode="cap",
               use_det_limits=False):
    rows = []
    for e, u in U.groupby("edb"):
        if e == "Aurora Energy" or e not in det.index:
            continue
        yrs = [2024] if e == "Powerco" else [2021, 2022, 2023, 2024]
        if bv_source == "det":
            bv = float(det.loc[e, "saidi_bv"])
            ref = R.commission(u, "2009-03-31 00:00", "2019-03-31 23:30", list(range(2010, 2020)), 1104, bound=bv, strict=strict_ref)
        else:  # recomputed, unrounded, at the DPP3 rank
            n = R.RANK["dpp3"].get(e, 1104)
            ref = R.commission(u, "2009-03-31 00:00", "2019-03-31 23:30", list(range(2010, 2020)), n, rank_from="2009-04-01 00:00", strict=strict_ref)
            bv = ref["bound"]
        la = float(det.loc[e, "saidi_limit"]) if use_det_limits else ref["limit"]
        ass = R.commission(u, "2020-03-31 00:00", "2024-03-31 23:30", [2021], 1104, bound=bv, strict=strict_ass)
        dy = R.disc_year(ass["grid"])
        aa = {y: float(ass["xn"][dy == y].sum()) for y in yrs}
        d, ddy = A.daily_by_year(u)
        refd = d[ddy.between(2010, 2019)]
        thr = ieee_thr(d[ddy.between(*ieee_years)], ddof)
        if b_mode == "cap":
            rn = refd.clip(upper=thr)
            ab = {y: float(d[ddy == y].clip(upper=thr).sum()) for y in yrs}
        else:  # exclude major-event days (set to zero), as in H1/H2
            rn = refd.where(refd <= thr, 0.0)
            ab = {y: float(d[ddy == y].where(d[ddy == y] <= thr, 0.0).sum()) for y in yrs}
        lb = rn.sum() / 10 + 2 * rn.std(ddof=1) * np.sqrt(365.25)
        ea = [y for y in yrs if aa[y] > la]
        eb = [y for y in yrs if ab[y] > lb]
        rows.append({"edb": e, "bv": bv, "a_limit": la, "a_assessed": aa, "a_exceed": ea, "b_thr": thr, "b_limit": lb,
                     "b_assessed": ab, "b_exceed": eb, "differs": ea != eb,
                     "ref_days_over_thr": int((refd > thr).sum()), "ref_nonzero_days": int((refd > 0).sum()),
                     "b_removed_share_ref": float(1 - rn.sum() / refd.sum()), "a_removed_share_ref": float(1 - ref["target"] / (ref["x"][np.isin(R.disc_year(ref["grid"]), range(2010, 2020))].sum() / 10)),
                     "b_thr_over_b_limit": float(thr / lb)})
    r = pd.DataFrame(rows)
    return r


variants = {
    "study (ref >=, assess >, det bv, IEEE 10y, cap)": dict(),
    "assess >= (consistent with ref)": dict(strict_ass=False),
    "ref > (consistent with assess)": dict(strict_ref=True),
    "unrounded recomputed bv": dict(bv_source="recomputed"),
    "IEEE threshold on 5 years 2015-2019": dict(ieee_years=(2015, 2019)),
    "IEEE ddof=0": dict(ddof=0),
    "IEEE exclude days instead of cap": dict(b_mode="exclude"),
    "determination limits for (a)": dict(use_det_limits=True),
}
out = {}
for name, kw in variants.items():
    r = h3_variant(**kw)
    diff = r[r.differs].edb.tolist()
    out[name] = {"differing": diff, "n_differing": len(diff), "exc_a": int(r.a_exceed.map(len).sum()), "exc_b": int(r.b_exceed.map(len).sum()),
                 "a_exceed": {e: v for e, v in zip(r.edb, r.a_exceed) if v}, "b_exceed": {e: v for e, v in zip(r.edb, r.b_exceed) if v}}
    print(f"{name:50s} differing={len(diff)} {diff} | exceedances a={out[name]['exc_a']} b={out[name]['exc_b']}")

# margins and degeneracy in the study's variant
r = h3_variant()
print("\nMargins (assessed / limit) within 5% of 1, study variant:")
marg = []
for _, x in r.iterrows():
    for y in x.a_assessed:
        ra, rb = x.a_assessed[y] / x.a_limit, x.b_assessed[y] / x.b_limit
        if abs(ra - 1) <= 0.05 or abs(rb - 1) <= 0.05:
            marg.append({"edb": x.edb, "year": y, "a_ratio": round(ra, 4), "b_ratio": round(rb, 4)})
print(pd.DataFrame(marg).to_string(index=False))
out["margins_within_5pct"] = marg

deg = r[["edb", "bv", "b_thr", "b_limit", "b_thr_over_b_limit", "ref_days_over_thr", "ref_nonzero_days", "a_removed_share_ref", "b_removed_share_ref"]].copy()
deg["ieee_over_commission_bv"] = deg.b_thr / deg.bv
print("\nIEEE rule (b) diagnostics on the 2010-2019 window:")
print(deg.round(3).to_string(index=False))
out["ieee_diagnostics"] = deg.round(4).to_dict(orient="records")
out["ieee_over_commission_bv_range"] = [round(float(deg.ieee_over_commission_bv.min()), 2), round(float(deg.ieee_over_commission_bv.max()), 2)]

# Commission's Table E3 against the study's rule (a) assessed values
cmp_rows = []
for _, x in r.iterrows():
    for i, y in enumerate([2021, 2022, 2023, 2024]):
        if y in x.a_assessed and E3[x.edb][i] is not None:
            cmp_rows.append({"edb": x.edb, "year": y, "study_a": round(x.a_assessed[y], 2), "comcom_E3": E3[x.edb][i],
                             "rel_diff": round(x.a_assessed[y] / E3[x.edb][i] - 1, 4) if E3[x.edb][i] else None})
c = pd.DataFrame(cmp_rows)
print("\nStudy rule (a) assessed vs Commission Table E3; |rel diff| > 1%:")
print(c[c.rel_diff.abs() > 0.01].to_string(index=False))
print("share within 1%:", round(float((c.rel_diff.abs() <= 0.01).mean()), 3), "of", len(c))
out["table_E3_comparison"] = {"n": int(len(c)), "within_1pct": int((c.rel_diff.abs() <= 0.01).sum()),
                              "over_1pct": c[c.rel_diff.abs() > 0.01].to_dict(orient="records")}
det_var = h3_variant(use_det_limits=True)
study_a_det = {e: v for e, v in zip(det_var.edb, det_var.a_exceed) if v}
out["exceedances_vs_E3"] = {"study_rule_a_det_limits": study_a_det, "commission_E3": E3_noncompliant,
                            "identical": study_a_det == E3_noncompliant}
print("exceedance years, study rule (a) with determination limits == Commission Table E3:", study_a_det == E3_noncompliant)
(HERE / "02_h3_robustness.json").write_text(json.dumps(out, indent=1, default=float))
print("written", HERE / "02_h3_robustness.json")
