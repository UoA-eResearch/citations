"""Stream NCBI's bioproject.xml into a compact table for limb 2's evidence (plan section 3).

  data/bioprojects.parquet: accession, title, description (first 2,000 characters), pubmed ids, submitter
  organisation (kept for the asymmetric-error analysis only; never used as evidence of origin)
"""
import re
from pathlib import Path

import pandas as pd
from lxml import etree

RUN = Path(__file__).resolve().parents[1]
SRC = RUN / "data" / "raw" / "ncbi" / "bioproject.xml"


def first_text(el, path):
    x = el.find(path)
    t = re.sub(r"<[^>]+>", " ", x.text) if x is not None and x.text else ""     # descriptions carry HTML tags
    return " ".join(t.split())


def main():
    rows = []
    with open(SRC, "rb") as fh:
        for _, el in etree.iterparse(fh, events=("end",), tag="Package", huge_tree=True):
            proj = el.find("Project/Project")
            if proj is None:
                el.clear(); continue
            acc = proj.find("ProjectID/ArchiveID")
            accession = acc.get("accession") if acc is not None else None
            descr = proj.find("ProjectDescr")
            pubs = [p.get("id") for p in (descr.iterfind("Publication") if descr is not None else [])
                    if p.get("id") and p.get("id").isdigit()]
            org = el.find("Project/Submission/Description/Organization/Name")
            rows.append({"accession": accession,
                         "title": first_text(descr, "Title") if descr is not None else "",
                         "description": (first_text(descr, "Description") if descr is not None else "")[:2000],
                         "pubmed_ids": ";".join(pubs),
                         "submitter_org": " ".join((org.text or "").split())[:200] if org is not None else ""})
            el.clear()
            while el.getprevious() is not None:
                del el.getparent()[0]
    d = pd.DataFrame(rows).dropna(subset=["accession"]).drop_duplicates("accession")
    d.to_parquet(RUN / "data" / "bioprojects.parquet", index=False)
    print(len(d), "projects;", int((d.pubmed_ids != "").sum()), "with a PubMed link")


if __name__ == "__main__":
    main()
