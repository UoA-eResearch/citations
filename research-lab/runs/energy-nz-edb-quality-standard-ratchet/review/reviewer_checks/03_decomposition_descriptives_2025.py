"""Reviewer check 3: decomposition order-dependence; plan section 0 descriptives; the 2025 usability test redone with
the disclosure table's 'All' network rows only; model file vs disclosed Class C by year; DPP3 limits reconciled with
the Commission's Table J1 (+/-5% inter-period cap on targets).

Read-only on the study. Writes 03_decomposition_descriptives_2025.json next to this script.
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

T = RUN / "results" / "tables"
RAW = RUN / "data" / "raw"
pd.set_option("display.width", 250)
out = {}

# ---- 1. decomposition: alternative order (boundary first) and Shapley average ----------------------------------------
U = pd.read_parquet(R.INT / "unplanned.parquet")
dec = pd.read_csv(T / "decomposition.csv").set_index("edb")
rows = []
for e, u in U.groupby("edb"):
    if e not in dec.index:
        continue
    n4, n3 = R.RANK["dpp4"].get(e, 1104), R.RANK["dpp3"].get(e, 1104)
    gg = u[(u.start.dt.normalize() >= "2014-03-31") & (u.start.dt.normalize() <= "2024-03-31")]
    g3 = u[u.start.dt.normalize() >= "2009-03-31"]
    w4 = R.commission(gg, "2014-03-31 00:00", "2024-03-31 23:30", list(range(2015, 2025)), n4)
    w3 = R.commission(g3, "2009-03-31 00:00", "2019-03-31 23:30", list(range(2010, 2020)), n3, rank_from="2009-04-01 00:00", strict=False)
    w3_at_bv4 = R.commission(g3, "2009-03-31 00:00", "2019-03-31 23:30", list(range(2010, 2020)), n3, bound=w4["bound"], strict=False)
    w4_at_bv3 = R.commission(gg, "2014-03-31 00:00", "2024-03-31 23:30", list(range(2015, 2025)), n4, bound=w3["bound"])
    d = w4["target"] - w3["target"]
    b_study = w4["target"] - w4_at_bv3["target"]          # study: boundary effect evaluated on DPP4 outcomes
    b_alt = w3_at_bv4["target"] - w3["target"]            # boundary effect evaluated on DPP3 outcomes
    rows.append({"edb": e, "d_target": d, "boundary_study": b_study, "outcome_study": d - b_study,
                 "boundary_alt": b_alt, "outcome_alt": d - b_alt, "boundary_shapley": 0.5 * (b_study + b_alt)})
dd = pd.DataFrame(rows)
print("Decomposition order dependence (minutes):")
print(dd.round(2).to_string(index=False))
sums = dd.drop(columns="edb").sum().round(2).to_dict()
print("sums:", sums)
out["decomposition"] = {"rows": dd.round(3).to_dict(orient="records"), "sums": sums,
                        "study_csv_sums": {"d_target": round(float(dec.d_target.sum()), 2), "boundary": round(float(dec.d_boundary_part.sum()), 2)}}

# ---- 2. plan section 0 descriptives from transcription_check.json -----------------------------------------------------
tc = json.loads((T / "transcription_check.json").read_text())
c4 = pd.DataFrame(tc["second_sources"]["DPP4_vs_commission_uncapped"]["rows"])
c4["pct"] = (c4.saidi_uncapped / c4.saidi_dpp3 - 1) * 100
c4["bound"] = (c4.saidi_uncapped < 0.95 * c4.saidi_dpp3) | (c4.saidi_uncapped > 1.05 * c4.saidi_dpp3)
c4["held"] = np.where(c4.saidi_uncapped < 0.95 * c4.saidi_dpp3, "up", np.where(c4.saidi_uncapped > 1.05 * c4.saidi_dpp3, "down", "-"))
noA = c4[c4.edb != "Aurora Energy"]
desc = {"median_pct_change_uncapped_16": round(float(c4.pct.median()), 2), "median_pct_change_uncapped_15_no_aurora": round(float(noA.pct.median()), 2),
        "range_no_aurora": [round(float(noA.pct.min()), 1), round(float(noA.pct.max()), 1)], "aurora_pct": round(float(c4[c4.edb == "Aurora Energy"].pct.iloc[0]), 1),
        "bound_of_15": int(noA.bound.sum()), "held_up": int((noA.held == "up").sum()), "held_down": int((noA.held == "down").sum()),
        "bv_fell_of_16": int((c4.saidi_bv_final < pd.read_csv(T / "dpp_limits.csv").query("dpp=='DPP3'").set_index("edb_current").loc[c4.edb, "saidi_bv"].to_numpy()).sum())}
print("\nSection 0 descriptives:", desc)
out["section0"] = desc

# ---- 3. the 2025 usability test redone with network == 'All' ----------------------------------------------------------
p = pd.read_parquet(RAW / "EDB_ID_Full_2026-06-01.parquet")
q = p[(p.section == "10(i): Interruptions") & (p.category == "SAIFI and SAIDI by class") & (p.sub_category == "SAIDI")]
qa = q[q.network.fillna("All") == "All"]
NAMES = {"Horizon Networks": "Horizon Energy"}
d4 = pd.read_parquet(R.INT / "dpp4.parquet")
nonexempt = sorted(set(d4.edb))
cc25 = qa[qa.description.str.startswith("Class C", na=False) & (qa.disc_yr == 2025)].groupby("edb").value.sum().rename(index=NAMES)
allun25 = qa[qa.description.str.match(r"Class [CDEFGI]", na=False) & (qa.disc_yr == 2025)].groupby("edb").value.sum().rename(index=NAMES)
i5 = pd.read_parquet(R.INT / "id2025_raw.parquet")
un5 = i5[i5.planned_or_unplanned.astype(str).str.lower().str.startswith("unplanned")].groupby("edb").saidi_value.sum().rename(index=NAMES)
j = pd.concat({"class_c_all": cc25, "all_unplanned_classes": allun25, "raw10a_unplanned": un5}, axis=1)
j = j.loc[[e for e in nonexempt if e in j.index]]
j["rel_c"] = (j.raw10a_unplanned / j.class_c_all - 1).round(4)
j["rel_allcls"] = (j.raw10a_unplanned / j.all_unplanned_classes - 1).round(4)
print("\n2025 identification test, network == 'All', 16 non-exempt distributors:")
print(j.round(2).to_string())
w5 = int((j.rel_c.abs() <= 0.05).sum())
print(f"within 5% of Class C: {w5} of {len(j)}  -> plan rule (>=12 and >=80%) usable = {w5 >= 12 and w5 / len(j) >= 0.8}")
print("missing non-exempt distributors:", [e for e in nonexempt if e not in j.index])
out["id2025_redo"] = {"rows": j.round(3).reset_index().to_dict(orient="records"), "within_5pct_of_class_c": w5, "n": int(len(j)),
                      "usable_by_plan_rule": bool(w5 >= 12 and w5 / len(j) >= 0.8), "missing": [e for e in nonexempt if e not in j.index]}
# what the study's summation did for the same distributors (all network rows)
cc25_sum = q[q.description.str.startswith("Class C", na=False) & (q.disc_yr == 2025)].groupby("edb").value.sum().rename(index=NAMES)
infl = (cc25_sum / cc25).round(2)
print("inflation factor of the study's Class C sum (all network rows / 'All' row):", infl[infl > 1.01].to_dict())
out["id2025_redo"]["study_sum_inflation"] = infl[infl > 1.01].to_dict()

# ---- 4. model file vs disclosed Class C ('All') by year, 2014-2024 --------------------------------------------------
ccy = qa[qa.description.str.startswith("Class C", na=False)].groupby(["edb", "disc_yr"]).value.sum().rename(index=NAMES, level=0)
m = d4[d4.pu == "unplanned"].groupby(["edb", "disc_yr"]).saidi.sum()
k = pd.concat({"cc": ccy, "model": m}, axis=1).dropna()
k["rel"] = k.model / k.cc - 1
piv = k.rel.unstack("disc_yr")
piv = piv[[c for c in piv.columns if 2014 <= c <= 2024]]
off = k[(k.rel.abs() > 0.01) & (k.index.get_level_values(1) >= 2014)].round(3)
print("\nModel file vs disclosed Class C ('All'), cells off by >1%:")
print(off.to_string())
out["model_vs_class_c"] = {"cells": int(piv.notna().sum().sum()), "off_by_more_than_1pct": off.reset_index().to_dict(orient="records")}

# ---- 5. DPP3 limits reconciled with Table J1 (Commission's +/-5% inter-period target cap) -------------------------------
J1 = {"Alpine Energy": -3.19, "Aurora Energy": -14.66, "Centralines": 26.84, "EA Networks": 0.0, "Eastland Network": 0.54,
      "Electricity Invercargill": 5.57, "Horizon Energy": 0.0, "Nelson Electricity": 29.68, "Network Tasman": 0.0, "Orion NZ": 0.0,
      "OtagoNet": -3.17, "Powerco": 0.0, "The Lines Company": -0.42, "Top Energy": 3.11, "Unison Networks": 2.88,
      "Vector Lines": -13.65, "Wellington Electricity": -1.94}
st = pd.read_stata(RAW / "comcom" / "dpp3_zip" / "Final model - Publication version" / "Outputs" / "Unplanned parameters.dta").set_index("edb")
lim = pd.read_csv(T / "dpp_limits.csv")
d3 = lim[lim.dpp == "DPP3"].set_index("edb")
val = json.loads((T / "validation.json").read_text())
v3 = pd.DataFrame(val["dpp3"]["rows"]).set_index("edb")
rows = []
for e in st.index:
    e_cur = "Firstlight Network" if e == "Eastland Network" else e
    recon = st.loc[e, "saidi_target"] * (1 + J1[e] / 100) + 2 * st.loc[e, "saidi_deviation"]
    rows.append({"edb": e, "stata_uncapped_limit": round(float(st.loc[e, "saidi_cap"]), 3), "rules_py_limit": v3.loc[e_cur, "saidi_limit"],
                 "rules_vs_stata_rel": round(abs(v3.loc[e_cur, "saidi_limit"] / st.loc[e, "saidi_cap"] - 1), 5),
                 "J1_adj_pct": J1[e], "reconstructed_det_limit": round(float(recon), 2), "determination": float(d3.loc[e, "saidi_limit"]),
                 "recon_rel_diff": round(abs(recon / d3.loc[e, "saidi_limit"] - 1), 4)})
rec = pd.DataFrame(rows)
print("\nDPP3 limits: rules.py vs Stata uncapped, and Table J1 reconstruction vs determination:")
print(rec.to_string(index=False))
out["dpp3_limits_reconciliation"] = {"rows": rec.to_dict(orient="records"), "max_rules_vs_stata_rel": float(rec.rules_vs_stata_rel.max()),
                                     "max_recon_rel_diff": float(rec.recon_rel_diff.max()), "n_J1_adjusted": int((rec.J1_adj_pct != 0).sum())}
(HERE / "03_decomposition_descriptives_2025.json").write_text(json.dumps(out, indent=1, default=float))
print("written", HERE / "03_decomposition_descriptives_2025.json")
