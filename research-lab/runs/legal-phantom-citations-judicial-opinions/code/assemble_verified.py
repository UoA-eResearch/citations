"""Assemble data/screen/verified.csv and verified_misattributions.csv from the sheets and the hand labels (D8; added
after review, D9). A label file lists only the rows given an explicit verdict; every other row on a sheet was read and
found real, and is recorded as "real" with labelled = 0 so the record shows which verdicts carry a written reason.

Label vocabulary (D8, D9): real | phantom (reliance sheet: a judge's reliance on a case found nowhere) | phantom-flag
(the court itself identifies a cited case as nonexistent) | phantom-party-asserted (only a party says it does not
exist) | phantom-party-filing | party-filing-unverified | unverifiable.
"""
import csv
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
S = RUN / "data" / "screen"
SHEETS = [("screened", "reliance"), ("screened", "flag"), ("placebo", "reliance"), ("placebo", "flag")]


def labels(name):
    p = S / "labels" / f"{name}.csv"
    return {int(r["k"]): (r["verdict"], r["note"]) for r in csv.DictReader(open(p))} if p.exists() else {}


def main():
    out = []
    for per, typ in SHEETS:
        lab = labels(f"{per}_{typ}")
        for k, r in enumerate(csv.DictReader(open(S / f"verify_{per}_{typ}.csv"))):
            v, note = lab.get(k, ("real", ""))
            out.append({"opinion_id": r["opinion_id"], "cluster_id": r["cluster_id"], "period": per, "type": typ,
                        "cite": r["cite"], "verdict": v, "notes": note, "sheet_row": k, "labelled": int(k in lab)})
    with open(S / "verified.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    lab = labels("misattributions")
    mis = []
    for k, r in enumerate(csv.DictReader(open(S / "verify_misattributions_sample.csv"))):
        v, note = lab.get(k, ("index-artefact", ""))
        mis.append({"opinion_id": r["opinion_id"], "date": r["date"], "cite": r["cite"], "verdict": v, "notes": note,
                    "labelled": int(k in lab)})
    with open(S / "verified_misattributions.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(mis[0])); w.writeheader(); w.writerows(mis)
    print(len(out), "sheet rows;", sum(o["labelled"] for o in out), "with a written verdict;", len(mis), "misattributions")


if __name__ == "__main__":
    main()
