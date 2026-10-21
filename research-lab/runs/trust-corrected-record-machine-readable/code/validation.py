"""Secondary 8: validation sheets, read by the study's AI agent.

  validation.py sheets   8a: 100 primary-cohort documents stratified by parser verdict (50 marked, 50 unmarked),
                         shuffled, verdict hidden: title, front-matter elements and every passage mentioning
                         retraction or withdrawal, for a full read of the XML where needed.
                         8b: 50 unmarked primary documents with their registry evidence (layers, Retraction Watch
                         notice DOI and reason, Crossref notice DOI) for checking that the retraction is real.
  validation.py score    agreement of the parser with the labels in data/validation/8a_labels.csv (sheet_id,
                         marker yes/no) and the registry error rate from 8b_labels.csv (sheet_id, real yes/no/unclear).
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis  # noqa: E402
import markers  # noqa: E402
from match import ndoi, npmid  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
VAL = RUN / "data" / "validation"
CTX = re.compile(r".{0,160}\b(retract\w*|withdraw\w*)\b.{0,160}", re.I | re.S)


def excerpt(pmcid):
    b = (analysis.FILES / f"{pmcid}.xml").read_bytes()
    x = markers.xml_markers(b)
    root = etree.fromstring(b, parser=etree.XMLParser(recover=True, huge_tree=True, resolve_entities=False, no_network=True))
    rel = [etree.tostring(el, encoding="unicode")[:300] for el in root.iter()
           if markers._local(el.tag) in ("related-article", "notes", "custom-meta", "event", "article-version")]
    text = " ".join(" ".join(root.itertext()).split())
    ctx = [m.group(0) for m in CTX.finditer(text)][:8]
    return x.get("title", ""), x.get("article_type", ""), rel[:8], ctx


def sheets():
    VAL.mkdir(parents=True, exist_ok=True)
    d = analysis.frame()
    C = d[(d.stratum == "primary") & d.xml_present.fillna(False) & ~d.notice_type]
    rng = np.random.default_rng(analysis.SEED + 8)
    a = pd.concat([C[C.xml_marked].sample(50, random_state=rng.integers(2**31)),
                   C[~C.xml_marked].sample(50, random_state=rng.integers(2**31))]).sample(frac=1, random_state=rng.integers(2**31))
    key, fh = [], open(VAL / "8a_sheet.md", "w")
    for j, r in enumerate(a.itertuples()):
        sid = f"A-{j:03d}"
        key.append({"sheet_id": sid, "pmcid": r.pmcid, "parser_marked": bool(r.xml_marked)})
        title, at, rel, ctx = excerpt(r.pmcid)
        fh.write(f"## {sid} ({r.pmcid}, article-type {at})\n- title: {title}\n")
        for e in rel:
            fh.write(f"- element: {e}\n")
        for c in ctx:
            fh.write(f"- context: ...{c}...\n")
        fh.write("\n")
    fh.close()
    pd.DataFrame(key).to_csv(VAL / "8a_key.csv", index=False)
    rw = pd.read_csv(analysis.RUN / "data" / "raw" / "retraction_watch.csv", dtype=str, encoding="utf-8",
                     encoding_errors="replace")
    rw = rw[rw.RetractionNature == "Retraction"]
    by_doi = {ndoi(x): i for i, x in zip(rw.index, rw.OriginalPaperDOI) if ndoi(x)}
    by_pmid = {npmid(x): i for i, x in zip(rw.index, rw.OriginalPaperPubMedID) if npmid(x)}
    b = C[~C.xml_marked].sample(50, random_state=rng.integers(2**31))
    fh, key = open(VAL / "8b_sheet.md", "w"), []
    for j, r in enumerate(b.itertuples()):
        sid = f"B-{j:03d}"
        key.append({"sheet_id": sid, "pmcid": r.pmcid})
        i = by_pmid.get(npmid(r.pmid)) if r.pmid else None
        i = i if i is not None else by_doi.get(ndoi(r.doi))
        fh.write(f"## {sid} ({r.pmcid}; doi {r.doi}; pmid {r.pmid})\n- layers: rw={r.rw} crossref={r.crossref} "
                 f"pubmed={r.pubmed} openalex={r.openalex}; retraction date {r.date}\n")
        if i is not None:
            x = rw.loc[i]
            fh.write(f"- Retraction Watch: notice DOI {x.RetractionDOI}, notice PMID {x.RetractionPubMedID}, "
                     f"nature {x.RetractionNature}, reason {str(x.Reason)[:200]}, journal {x.Journal}\n")
        fh.write("\n")
    fh.close()
    pd.DataFrame(key).to_csv(VAL / "8b_key.csv", index=False)
    print("sheets written")


def score():
    k = pd.read_csv(VAL / "8a_key.csv")
    lab = pd.read_csv(VAL / "8a_labels.csv").merge(k, on="sheet_id")
    lab["truth"] = lab.marker.str.lower().eq("yes")
    out = {"8a": {"n": len(lab),
                  "parser_marked_and_true": int((lab.parser_marked & lab.truth).sum()),
                  "parser_marked_but_false": int((lab.parser_marked & ~lab.truth).sum()),
                  "parser_unmarked_but_true": int((~lab.parser_marked & lab.truth).sum()),
                  "parser_unmarked_and_false": int((~lab.parser_marked & ~lab.truth).sum())}}
    b = pd.read_csv(VAL / "8b_labels.csv")
    out["8b"] = b.real.str.lower().value_counts().to_dict()
    json.dump(out, open(analysis.TAB / "validation.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    {"sheets": sheets, "score": score}[sys.argv[1]]()
