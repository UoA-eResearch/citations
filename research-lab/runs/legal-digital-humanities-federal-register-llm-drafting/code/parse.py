"""Parse GovInfo daily issues into preamble paragraphs (plan section 2). Usage: parse.py [raw|sealed]
For every RULE/PRORULE element: document number from FRDOC, paragraphs (<P>) of SUPLINF with the current heading and a
procedural flag. Joined to data/meta/fr_groups.parquet (group, templated). Writes data/paragraphs_<which>.parquet.
'sealed' may only be run after the plan and the validation results are committed (plan section 4)."""
import re
import sys
from pathlib import Path

import pandas as pd
from joblib import Parallel, delayed
from lxml import etree

RUN = Path(__file__).resolve().parents[1]
PROC = re.compile(r"regulatory flexibility|paperwork reduction|executive order|unfunded mandates|congressional review|"
                  r"national environmental policy|federalism|tribal|energy effects|environmental justice|privacy act|"
                  r"technical standards|information collection|plain language|statutory and executive order|list of subjects|"
                  r"regulatory analys|regulatory notices and analyses|e\.o\. 1|small business regulatory", re.I)
DOCNO = re.compile(r"FR Doc\.?\s*([0-9]{4}-[0-9]+)")


def text_of(el):
    return re.sub(r"\s+", " ", " ".join(el.itertext())).strip()


def parse_issue(path):
    out = []
    try:
        root = etree.parse(str(path), etree.XMLParser(recover=True, huge_tree=True)).getroot()
    except Exception:  # noqa: BLE001
        return out
    date = path.stem.replace("FR-", "")
    for doc in root.iter("RULE", "PRORULE"):
        frdoc = doc.find(".//FRDOC")
        m = DOCNO.search(text_of(frdoc)) if frdoc is not None else None
        if not m:
            continue
        num = m.group(1)
        sup = doc.find(".//SUPLINF")
        if sup is None:
            continue
        heading, idx = "", 0
        for el in sup.iter("HD", "P", "LSTSUB"):
            if el.tag == "LSTSUB":
                break
            if el.tag == "HD":
                heading = text_of(el)
                continue
            t = text_of(el)
            if len(t.split()) < 8:
                continue
            out.append(dict(document_number=num, issue_date=date, para_idx=idx, heading=heading[:200],
                            procedural=bool(PROC.search(heading)), text=t, n_words=len(t.split())))
            idx += 1
    return out


def main(which="raw"):
    files = sorted((RUN / "data" / which / "daily").glob("FR-*.xml"))
    rows = Parallel(n_jobs=8)(delayed(parse_issue)(f) for f in files)
    p = pd.DataFrame([r for rs in rows for r in rs])
    g = pd.read_parquet(RUN / "data" / "meta" / "fr_groups.parquet")[["document_number", "publication_date", "type", "group", "dept", "templated", "title"]]
    p = p.merge(g, on="document_number", how="inner")
    p.to_parquet(RUN / "data" / f"paragraphs_{which}.parquet")
    docs = p.document_number.nunique()
    print(f"{len(files)} issues -> {len(p)} paragraphs in {docs} documents; procedural share {p.procedural.mean():.3f}")
    print(p.groupby(["group"]).document_number.nunique().to_dict())


if __name__ == "__main__":
    main(*sys.argv[1:])
