#!/usr/bin/env python
"""H3 (plan.md sec 5): how many ClinGen expert-panel (VCEP) classifications depend on computational evidence?

Each ERepo classification's applied criteria ("Applied Evidence Codes (Met)") are recounted on the ACMG points scale
(Tavtigian et al. 2020): PVS 8, PS 4, PM 2, PP 1, BS -4, BP -1, with the magnitude set by a strength suffix
(_Supporting 1, _Moderate 2, _Strong 4, _VeryStrong 8); BA1 is stand-alone benign. Points -> class: P >= 10,
LP 6-9, VUS 0-5, LB -1..-6, B <= -7. The recount is checked against the published assertion first; H3 uses only the
classifications whose recount agrees. A label is tool-dependent if removing its PP3/BP4 points moves it into VUS.

Outputs: data/processed/vcep_recount.parquet, results/tables/h3_vcep_by_year.csv, results/tables/h3_vcep_summary.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw" / "clingen" / "erepo_classifications_2026-10-01.tsv"
PROC, TAB = RUN / "data" / "processed", RUN / "results" / "tables"
BASE = {"PVS": 8, "PS": 4, "PM": 2, "PP": 1, "BS": -4, "BP": -1}
SUFFIX = {"supporting": 1, "moderate": 2, "strong": 4, "verystrong": 8, "very strong": 8}
CODE = re.compile(r"^(PVS|PS|PM|PP|BA|BS|BP)(\d+)(?:[_ ](.+))?$", re.I)


def points(code: str):
    m = CODE.match(code.strip())
    if not m:
        return None, None
    fam, num, suf = m.group(1).upper(), m.group(2), (m.group(3) or "").strip().lower().replace("-", "").replace("_", " ")
    name = f"{fam}{num}"
    if fam == "BA":
        return name, "BA"
    mag = SUFFIX.get(suf.replace(" ", "")) if suf else None
    base = BASE[fam]
    val = (np.sign(base) * mag) if mag else base
    return name, int(val)


def classify(total, has_ba):
    if has_ba:
        return "B"
    if total >= 10:
        return "P"
    if total >= 6:
        return "LP"
    if total >= 0:
        return "VUS"
    if total >= -6:
        return "LB"
    return "B"


GROUP = {"P": "P", "LP": "P", "VUS": "VUS", "LB": "B", "B": "B"}
ASSERT = {"Pathogenic": "P", "Likely Pathogenic": "LP", "Uncertain Significance": "VUS", "Likely Benign": "LB",
          "Benign": "B"}


def main():
    df = pd.read_csv(RAW, sep="\t", dtype=str)
    df = df[df.get("Retracted", "false").fillna("false").str.lower() != "true"].copy()
    rows = []
    for _, r in df.iterrows():
        codes = [c for c in str(r["Applied Evidence Codes (Met)"] or "").split(",") if c.strip() and c.strip() != "nan"]
        tot, tot_wo, has_ba, pp3, bp4, unparsed = 0, 0, False, 0, 0, 0
        for c in codes:
            name, val = points(c)
            if name is None:
                unparsed += 1
                continue
            if val == "BA":
                has_ba = True
                continue
            tot += val
            if name == "PP3":
                pp3 += val
            elif name == "BP4":
                bp4 += val
            else:
                tot_wo += val
        a = ASSERT.get(str(r["Assertion"]).strip())
        rec = classify(tot, has_ba)
        rec_wo = classify(tot_wo, has_ba)
        rows.append(dict(variation_id=pd.to_numeric(r["ClinVar Variation Id"], errors="coerce"), gene=r["HGNC Gene Symbol"],
                         panel=r["Expert Panel"], approval=pd.to_datetime(r["Approval Date"], errors="coerce"),
                         assertion=a, points=tot, points_wo_comp=tot_wo, pp3_points=pp3, bp4_points=bp4, ba1=has_ba,
                         recount=rec, recount_wo_comp=rec_wo, n_unparsed=unparsed))
    v = pd.DataFrame(rows)
    v["year"] = v.approval.dt.year
    v["agrees"] = v.assertion.map(GROUP) == v.recount.map(GROUP)
    v["agrees_exact"] = v.assertion == v.recount
    v["confident"] = v.assertion.map(GROUP).isin(["P", "B"])
    v["tool_dependent"] = v.confident & v.agrees & (v.recount_wo_comp.map(GROUP) == "VUS")
    v["uses_comp"] = (v.pp3_points != 0) | (v.bp4_points != 0)
    v.to_parquet(PROC / "vcep_recount.parquet", index=False)
    conf = v[v.confident]
    summ = dict(n_classifications=int(len(v)), n_confident=int(len(conf)),
                recount_group_agreement=float(conf.agrees.mean()), recount_exact_agreement=float(conf.agrees_exact.mean()),
                n_unparsed_codes=int(v.n_unparsed.sum()),
                frac_using_pp3_or_bp4=float(conf.uses_comp.mean()),
                frac_tool_dependent_of_agreeing=float(conf[conf.agrees].tool_dependent.mean()))
    by = conf[conf.agrees].groupby(["year", conf[conf.agrees].assertion.map(GROUP)]).agg(
        n=("tool_dependent", "size"), uses_comp=("uses_comp", "mean"), tool_dependent=("tool_dependent", "mean")).reset_index()
    by.columns = ["year", "side", "n", "frac_uses_pp3_bp4", "frac_tool_dependent"]
    by.to_csv(TAB / "h3_vcep_by_year.csv", index=False)
    json.dump(summ, open(TAB / "h3_vcep_summary.json", "w"), indent=2)
    print(json.dumps(summ, indent=1))
    print(by.to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
