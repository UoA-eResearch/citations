#!/usr/bin/env python
"""EXPLORATORY (deviations.md D6): who submitted the post-2022 single-submitter benign surge, and do those
submissions cite computational evidence?

For rare missense variants with a REVEL score that were first confidently classified, with 1 star, in 2021-2022
(before) or 2023-2026 (after), find their germline submissions (SCVs) in the current ClinVar submission_summary and
tabulate, per period and label: submitter shares, and the fraction of submissions whose free text (Description /
ExplanationOfInterpretation) cites BP4 / PP3 or computational / in-silico evidence.

Output: results/tables/explore_submitters.csv, results/tables/explore_submitters_summary.json
"""
from __future__ import annotations

import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW, PROC, TAB = RUN / "data" / "raw" / "clinvar", RUN / "data" / "processed", RUN / "results" / "tables"
BP4 = re.compile(r"\bBP4(?:_[A-Za-z]+)?\b")
PP3 = re.compile(r"\bPP3(?:_[A-Za-z]+)?\b")
COMP = re.compile(r"in[ -]?silico|computational|REVEL|AlphaMissense|BayesDel|CADD|prediction (?:tools?|algorithms?)|predicted to be (?:benign|tolerated|damaging|deleterious)", re.I)
B_TERMS = {"Benign", "Likely benign", "Benign/Likely benign"}
P_TERMS = {"Pathogenic", "Likely pathogenic", "Pathogenic/Likely pathogenic"}


def main():
    at = pd.read_parquet(PROC / "analysis_table.parquet")
    allnew = at[at.rare & at.primary_new]
    old_b_genes = set(allnew[(allnew.label == "B") & allnew.year.isin([2021, 2022])].gene)   # genes with benign labels before
    at = at[at.rare & at.revel.notna() & (at.stars == 1) & at.primary_new]
    at["period"] = np.where(at.year <= 2022, "2021-2022", "2023-2026")
    want = dict(zip(at.variation_id, zip(at.period, at.label, at.revel, at.gene)))
    path = RAW / "submission_summary_2026-09-28.txt.gz"
    with gzip.open(path, "rt") as fh:
        for line in fh:
            if line.startswith("#VariationID\t"):          # skip the column-description comment block
                header = line.lstrip("#").rstrip("\n").split("\t")
                break
        sub = pd.read_csv(fh, sep="\t", names=header, dtype=str, usecols=["VariationID", "ClinicalSignificance",
                          "Description", "Submitter", "SCV", "ExplanationOfInterpretation", "ReviewStatus"])
    sub["VariationID"] = pd.to_numeric(sub.VariationID, errors="coerce")
    sub = sub[sub.VariationID.isin(set(want))].copy()
    sub["period"] = sub.VariationID.map(lambda v: want[v][0])
    sub["label"] = sub.VariationID.map(lambda v: want[v][1])
    sub["revel"] = sub.VariationID.map(lambda v: want[v][2])
    sub["new_gene"] = ~sub.VariationID.map(lambda v: want[v][3]).isin(old_b_genes)
    # keep the submissions that match the aggregate label (the ones that make the 1-star confident classification)
    sub = sub[((sub.label == "B") & sub.ClinicalSignificance.isin(B_TERMS)) | ((sub.label == "P") & sub.ClinicalSignificance.isin(P_TERMS))]
    text = (sub.Description.fillna("") + " " + sub.ExplanationOfInterpretation.fillna(""))
    sub["cites_bp4"] = text.str.contains(BP4)
    sub["cites_pp3"] = text.str.contains(PP3)
    sub["cites_comp"] = text.str.contains(COMP)
    sub["has_text"] = text.str.strip().str.len() > 20
    rows = []
    for (period, label), g in sub.groupby(["period", "label"]):
        tot = len(g)
        top = g.Submitter.value_counts().head(8)
        for subm, n in top.items():
            s = g[g.Submitter == subm]
            rows.append(dict(period=period, label=label, submitter=subm, n=int(n), share=n / tot,
                             frac_text=float(s.has_text.mean()), frac_bp4=float(s.cites_bp4.mean()),
                             frac_pp3=float(s.cites_pp3.mean()), frac_comp=float(s.cites_comp.mean()),
                             median_revel=float(s.revel.median()), frac_new_gene=float(s.new_gene.mean())))
    out = pd.DataFrame(rows)
    out.to_csv(TAB / "explore_submitters.csv", index=False)
    summ = {}
    for (period, label), g in sub.groupby(["period", "label"]):
        summ[f"{period} {label}"] = dict(n_scv=int(len(g)), n_submitters=int(g.Submitter.nunique()),
                                         top1_share=float(g.Submitter.value_counts(normalize=True).iloc[0]),
                                         top3_share=float(g.Submitter.value_counts(normalize=True).head(3).sum()),
                                         frac_with_text=float(g.has_text.mean()), frac_cites_bp4=float(g.cites_bp4.mean()),
                                         frac_cites_pp3=float(g.cites_pp3.mean()), frac_cites_comp=float(g.cites_comp.mean()),
                                         median_revel=float(g.revel.median()), frac_new_gene=float(g.new_gene.mean()))
    json.dump(summ, open(TAB / "explore_submitters_summary.json", "w"), indent=2)
    print(json.dumps(summ, indent=1))
    print(out.round(3).to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
