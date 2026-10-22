"""Confirmation pass, small follow-ups (review/confirmation.md):
- the undated stratum after D5 with the overlay's own_marker (documents_d3.csv.gz covers only part of the parsed set,
  so confirm_primary.py's figure for it is not usable);
- who publishes the 412 moved documents (the report calls them "the 412 undatable Elsevier documents");
- the 382-document residue by publisher ("most of them from Elsevier and Cell Press journals");
- the peS2o v2 share without IEEE's DOI prefix ("the marked share is high only because of IEEE").
Run: venv/bin/python -I confirm_misc.py > confirm_misc.log
"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
T = RUN / "results" / "tables"
SELF = "crossref-self-update (issue date)"


def main():
    c = pd.read_parquet(RUN / "data" / "cohort.parquet")
    p = pd.read_parquet(RUN / "data" / "parsed.parquet")
    d3 = pd.read_csv(T / "documents_d3.csv.gz")
    ov = pd.read_csv(RUN / "results" / "overlay" / "retraction_overlay.csv.gz", usecols=["pmcid", "date_source", "own_marker"])
    d = c.merge(p, on="pmcid", how="inner")
    d = d[~d.article_type.fillna("").str.lower().eq("retraction")]
    d = d.merge(ov, on="pmcid", how="left")
    d["own"] = d.own_marker.fillna(False).astype(bool)
    d["flag"] = d.sidecar_flag.fillna(False).astype(bool)
    print("documents_d3.csv.gz rows:", len(d3), "; parsed non-notice:", len(d), "; d3 coverage by stratum:",
          d[d.pmcid.isin(set(d3.pmcid))].stratum.value_counts().to_dict())
    prim = d[(d.stratum == "primary") & d.xml_present.fillna(False)]
    moved = prim[prim.date_source == SELF]
    C = prim[prim.date_source != SELF]
    U = d[(d.stratum == "undated") & d.xml_present.fillna(False)]
    print("undated parsed:", len(U), "own-unmarked", int((~U.own).sum()), round(float((~U.own).mean()), 4),
          "; moved:", len(moved), "own-unmarked", int((~moved.own).sum()),
          "; combined:", len(U) + len(moved), round(float((int((~U.own).sum()) + int((~moved.own).sum())) / (len(U) + len(moved))), 4),
          "(reported 1,142; 16.6%)")
    pub = moved.publisher.fillna(moved.xml_publisher).fillna("unknown")
    print("\nmoved 412 by publisher:", pub.value_counts().head(8).to_dict())
    unk = moved[pub == "unknown"]
    print("moved with publisher unknown, by RW journal:", unk.journal.fillna("?").value_counts().head(8).to_dict())
    print("moved with publisher unknown, by DOI prefix:", unk.doi.fillna("").str.split("/").str[0].value_counts().head(6).to_dict())
    print("moved, DOI prefix overall:", moved.doi.fillna("").str.split("/").str[0].value_counts().head(6).to_dict())
    res = C[~C.own & ~C.flag]
    rp = res.publisher.fillna(res.xml_publisher).fillna("unknown")
    print("\nresidue 382 by publisher:", rp.value_counts().head(10).to_dict())
    print("residue by DOI prefix:", res.doi.fillna("").str.split("/").str[0].value_counts().head(8).to_dict())
    els = rp.str.contains("Elsevier|Cell Press", case=False) | res.doi.fillna("").str.startswith("10.1016")
    print("residue Elsevier family (publisher name or DOI prefix 10.1016):", int(els.sum()), "of", len(res), round(float(els.mean()), 4))
    pes = pd.read_csv(T / "pes2o_documents_d5.csv")
    ieee = pes.doi.str.startswith("10.1109")
    print("\npeS2o matched: IEEE (10.1109) documents", int(ieee.sum()), "v2", round(float(pes[ieee].v2.mean()), 4),
          "; non-IEEE", int((~ieee).sum()), "v2", round(float(pes[~ieee].v2.mean()), 4),
          "; non-IEEE s2ag", round(float(pes[~ieee & (pes.source == "s2ag")].v2.mean()), 4))
    print("share of v2-marked documents that are IEEE:", round(float((pes.v2 & ieee).sum() / pes.v2.sum()), 4))


if __name__ == "__main__":
    main()
