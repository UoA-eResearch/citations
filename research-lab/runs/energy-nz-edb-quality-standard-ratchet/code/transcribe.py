"""Double entry of the DPP2-DPP4 unplanned reliability limits and boundary values (before any outcome is read).

Entry A: transcription/dpp_limits_manual.csv, typed from the determinations' tables.
Entry B: an automated parse of the same tables from the PDFs (pdftotext -layout): every line in the table region
with exactly four numbers is a row, in table order.
Second sources (independent of the PDFs):
  DPP2  the limits each distributor disclosed for 2016-2020 (EDB ID Schedule 10(i), "Limit applicable to
        disclosure year"; these are 0.5 x planned + unplanned limits, as in DPP2)
  DPP4  the Commission's own uncapped parameters (EDB_DPP4_quality_final_decision.zip): final limits must equal the
        uncapped limits clamped to DPP3 limit x [0.95, 1.05], and boundary values the uncapped boundary values
DPP1 limits (self-calculated by each distributor) are taken from the 2013-2015 disclosures, descriptively.
Writes results/tables/dpp_limits.csv and results/tables/transcription_check.json.
"""
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
COM = RAW / "comcom"
T = RUN / "results" / "tables"
NUM = re.compile(r"(?<![\w.])\d[\d,]*\.\d+(?![\w.])|(?<![\w.])\d+(?![\w.])")
ALIAS = {"Eastland Network": "Firstlight Network"}            # renamed; same network
TABLES = {  # file, start marker, end marker, column order of the four numbers
    "DPP2": ("dpp2_determination.pdf", "Table 4A.1:", "Calculation of the SAIDI Assessed Values",
             ["saidi_limit", "saidi_bv", "saifi_limit", "saifi_bv"]),
    "DPP3": ("dpp3_determination.pdf", "Table 3.2.1:", "Calculation of the unplanned SAIDI assessed values",
             ["saidi_limit", "saifi_limit", "saidi_bv", "saifi_bv"]),
    "DPP4": ("dpp4_determination.pdf", "Table 3.2.1:", "Calculation of the unplanned SAIDI assessed values",
             ["saidi_limit", "saifi_limit", "saidi_bv", "saifi_bv"]),
}


def parse(dpp):
    f, a, b, cols = TABLES[dpp]
    txt = subprocess.run(["pdftotext", "-layout", str(COM / f), "-"], capture_output=True, text=True, check=True).stdout
    i = txt.index(a)
    seg = txt[i:txt.index(b, i)]
    rows = []
    for line in seg.splitlines():
        nums = [float(x.replace(",", "")) for x in NUM.findall(line) if "." in x]
        if len(nums) == 4:
            rows.append(dict(zip(cols, nums)))
    return pd.DataFrame(rows)


def main():
    man = pd.read_csv(RUN / "transcription" / "dpp_limits_manual.csv")
    out = {"entry_A_vs_B": {}, "second_sources": {}}
    for dpp in TABLES:
        a = man[man.dpp == dpp].reset_index(drop=True)
        b = parse(dpp)
        ok = len(a) == len(b) and np.allclose(a[b.columns].to_numpy(float), b.to_numpy(float), rtol=0, atol=1e-9)
        out["entry_A_vs_B"][dpp] = {"rows_manual": int(len(a)), "rows_parsed": int(len(b)), "identical": bool(ok)}
        if not ok:
            print(dpp, "MISMATCH"); print(a.join(b, rsuffix="_parsed").to_string())
    # DPP2 against the distributors' own disclosures
    p = pd.read_parquet(RAW / "EDB_ID_Full_2026-06-01.parquet")
    q = p[(p.section == "10(i): Interruptions") & p.category.str.contains("limit", case=False, na=False)
          & p.value.notna() & (p.value > 0)]
    lim = q.groupby(["edb", "disc_yr", "sub_category"]).value.max().unstack()
    d2 = man[man.dpp == "DPP2"].assign(edb=lambda x: x.edb.replace(ALIAS)).set_index("edb")
    cmp2 = []
    for e, r in d2.iterrows():
        for y in range(2016, 2021):
            if (e, y) in lim.index:
                cmp2.append({"edb": e, "year": y, "saidi_disc": lim.loc[(e, y), "SAIDI"], "saidi_det": r.saidi_limit,
                             "saifi_disc": lim.loc[(e, y), "SAIFI"], "saifi_det": r.saifi_limit})
    c2 = pd.DataFrame(cmp2)
    c2["saidi_match"] = np.isclose(c2.saidi_disc, c2.saidi_det, rtol=0.005)
    c2["saifi_match"] = np.isclose(c2.saifi_disc, c2.saifi_det, rtol=0.005)
    out["second_sources"]["DPP2_vs_disclosures"] = {
        "edb_years": int(len(c2)), "saidi_match": int(c2.saidi_match.sum()), "saifi_match": int(c2.saifi_match.sum()),
        "mismatches": c2[~(c2.saidi_match & c2.saifi_match)].round(3).to_dict(orient="records")}
    # DPP4 final = uncapped clamped to DPP3 x [0.95, 1.05]; boundary values uncapped
    unc = pd.read_csv(next((COM / "dpp4_zip" / "edb_quality_dpp4" / "outputs").glob("unplanned_norm_param_not_caps*.csv")))
    d3 = man[man.dpp == "DPP3"].assign(edb=lambda x: x.edb.replace(ALIAS)).set_index("edb")
    d4 = man[man.dpp == "DPP4"].set_index("edb")
    rows = []
    for _, u in unc.iterrows():
        e = u.edb
        if e not in d4.index:
            continue
        r = {"edb": e, "saidi_uncapped": u.saidi_cap, "saidi_final": d4.saidi_limit[e], "saidi_bv_uncapped": u.saidi_bound,
             "saidi_bv_final": d4.saidi_bv[e], "saifi_uncapped": u.saifi_cap, "saifi_final": d4.saifi_limit[e]}
        if e in d3.index:
            r["saidi_dpp3"], r["saifi_dpp3"] = d3.saidi_limit[e], d3.saifi_limit[e]
            r["saidi_clamped"] = float(np.clip(u.saidi_cap, 0.95 * d3.saidi_limit[e], 1.05 * d3.saidi_limit[e]))
            r["saifi_clamped"] = float(np.clip(u.saifi_cap, 0.95 * d3.saifi_limit[e], 1.05 * d3.saifi_limit[e]))
        rows.append(r)
    c4 = pd.DataFrame(rows)
    c4["bv_match"] = np.isclose(c4.saidi_bv_uncapped.round(2), c4.saidi_bv_final, atol=0.006)
    c4["clamp_match"] = np.isclose(c4.saidi_clamped.round(2), c4.saidi_final, atol=0.006)
    c4["clamp_match_saifi"] = np.isclose(c4.saifi_clamped.round(4), c4.saifi_final, atol=0.00006)
    out["second_sources"]["DPP4_vs_commission_uncapped"] = {
        "edbs": int(len(c4)), "boundary_values_match": int(c4.bv_match.sum()),
        "saidi_limit_equals_clamp": int(c4.clamp_match.sum()), "saifi_limit_equals_clamp": int(c4.clamp_match_saifi.sum()),
        "rows": c4.round(4).to_dict(orient="records")}
    # DPP1 limits as disclosed (2013-2015), descriptive
    d1 = lim[lim.index.get_level_values(1) <= 2015].reset_index()
    out["DPP1_disclosed_limits"] = d1.round(4).to_dict(orient="records")
    man.assign(edb_current=man.edb.replace(ALIAS)).to_csv(T / "dpp_limits.csv", index=False)
    (T / "transcription_check.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({"entry_A_vs_B": out["entry_A_vs_B"],
                      "DPP2": {k: v for k, v in out["second_sources"]["DPP2_vs_disclosures"].items() if k != "mismatches"},
                      "DPP4": {k: v for k, v in out["second_sources"]["DPP4_vs_commission_uncapped"].items() if k != "rows"}}, indent=1))
    print(pd.DataFrame(out["second_sources"]["DPP2_vs_disclosures"]["mismatches"]).to_string())
    print(c4[["edb", "saidi_dpp3", "saidi_uncapped", "saidi_clamped", "saidi_final", "bv_match", "clamp_match", "clamp_match_saifi"]].round(3).to_string())


if __name__ == "__main__":
    main()
