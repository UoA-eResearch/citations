"""Validate the measured panel before any model output is looked at.

Three checks:
  1. shape, completeness and the censoring share of the DeepDTA Davis matrix;
  2. the pKd transform and matrix orientation, against known pharmacology — for five well-known
     inhibitors, the kinases they bind most strongly in the panel should be the ones the literature
     associates with them;
  3. the panel rectangle's own dynamic range.
Writes results/tables/data_validation.txt.
"""
import json
import pickle
import sys
from pathlib import Path

import numpy as np

RUN = Path(__file__).resolve().parents[1]
KNOWN = {"5291": "imatinib (expect ABL1 and DDR1)", "44259": "staurosporine (expect almost everything)",
         "123631": "an EGFR inhibitor (expect EGFR and its deletion mutants)",
         "5328940": "an ABL inhibitor (expect ABL1 and its mutants)",
         "3062316": "an ABL inhibitor (expect ABL1 and its mutants)"}


def main():
    Y = np.asarray(pickle.load(open(RUN / "data" / "davis_Y", "rb"), encoding="latin1"), float)
    prot = list(json.load(open(RUN / "data" / "davis_proteins.txt")))
    lig = list(json.load(open(RUN / "data" / "davis_ligands_iso.txt")))
    pkd = 9 - np.log10(Y)
    P = json.load(open(RUN / "data" / "panel.json"))
    rows = [c["row"] for c in P["ligands"]]
    cols = [k["col"] for k in P["kinases"]]
    sub = pkd[np.ix_(rows, cols)]
    out = [f"Davis matrix: {Y.shape[0]} ligands x {Y.shape[1]} kinase assays, "
           f"{int(np.isnan(Y).sum())} missing cells, Kd {Y.min():g}-{Y.max():g} nM",
           f"censored at the 10 uM ceiling: {int((Y >= 10000).sum())} cells "
           f"({(Y >= 10000).mean():.1%}); pKd range {pkd.min():.2f}-{pkd.max():.2f}", ""]
    for cid, what in KNOWN.items():
        if cid not in lig:
            out.append(f"CID {cid} not in the DeepDTA packaging")
            continue
        i = lig.index(cid)
        top = np.argsort(-pkd[i])[:5]
        out.append(f"CID {cid} - {what}: {int((Y[i] < 10000).sum())} uncensored of {Y.shape[1]}; "
                   "strongest " + ", ".join(f"{prot[j]} {pkd[i, j]:.2f}" for j in top))
    out += ["",
            f"panel rectangle: {sub.shape[0]} ligands x {sub.shape[1]} kinases, "
            f"{int((sub > 5).sum())} uncensored cells ({(sub > 5).mean():.1%}), "
            f"pKd {sub.min():.2f}-{sub.max():.2f}",
            f"per-ligand uncensored cells: min {int((sub > 5).sum(1).min())}, "
            f"median {int(np.median((sub > 5).sum(1)))}, max {int((sub > 5).sum(1).max())}",
            f"per-kinase uncensored cells: min {int((sub > 5).sum(0).min())}, "
            f"median {int(np.median((sub > 5).sum(0)))}, max {int((sub > 5).sum(0).max())}",
            f"per-ligand spread of measured pKd (SD): median {np.median(sub.std(1)):.2f}",
            f"per-kinase spread of measured pKd (SD): median {np.median(sub.std(0)):.2f}"]
    txt = "\n".join(out) + "\n"
    (RUN / "results" / "tables" / "data_validation.txt").write_text(txt)
    print(txt)


if __name__ == "__main__":
    sys.exit(main())
