"""D3 sensitivity (after validation 8a): markers counted only outside reference lists, and withdrawal wording added.

Validation found two parser faults: PMC annotates *cited* retracted works with related-article inside <ref>, which
the preregistered detector counted as the citing article's own marker; and withdrawal notices or statements ("has
been withdrawn", "Withdrawal:") were missed. This script re-reads every primary-cohort XML and text file with
  own        markers.xml_markers_own (reference lists ignored)
  own+wd     own, plus withdrawal wording outside reference lists
and, for the text rendition, PMC's own "RETRACTED ARTICLE" header line or the textual rules before the References
line. Writes results/tables/sensitivity_d3.json. The preregistered numbers in primary.json stand as reported.
"""
import concurrent.futures as cf
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
import markers as M  # noqa: E402

WD_TITLE = re.compile(r"^\W*(withdrawal|withdrawn|notice of withdrawal)\b", re.I)
WD_TEXT = re.compile(r"\b(?:(?:this|the)\s+(?:article|paper|manuscript|publication|study)\s+(?:has\s+been|have\s+been|was|is)"
                     r"\s+withdrawn|withdrawal\s+notice|notice\s+of\s+withdrawal|policy\s+on\s+article\s+withdrawal)\b", re.I)


def one(pmcid):
    b = (A.FILES / f"{pmcid}.xml").read_bytes()
    own = M.xml_markers_own(b)
    from lxml import etree
    root = etree.fromstring(b, parser=etree.XMLParser(recover=True, huge_tree=True, resolve_entities=False, no_network=True))
    title, text = "", []
    if root is not None:
        for el in root.iter():
            if M._local(el.tag) == "article-title" and not M._in_refs(el) and \
                    any(M._local(a.tag) == "article-meta" for a in el.iterancestors()):
                title = " ".join(" ".join(el.itertext()).split())
                break
        for el in root.iter():
            if M._local(el.tag) in ("ref-list",):
                continue
            if not M._in_refs(el) and el.text:
                text.append(el.text)
    wd = bool(WD_TITLE.search(title)) or bool(WD_TEXT.search(" ".join(text)))
    t = (A.FILES / f"{pmcid}.txt").read_bytes().decode("utf-8", "replace")
    head = t.split("\nReferences\n")[0]
    hdr = bool(re.search(r"ARTICLE INFORMATION\n=+\n\s*\n?RETRACTED ARTICLE", t[:3000]))
    txt_own = hdr or M.txt_markers(head)["textual"]
    return {"pmcid": pmcid, "own_structured": own["structured"], "own_textual": own["textual"], "own_kinds": ";".join(own["kinds"]),
            "withdrawal": wd, "txt_header": hdr, "txt_own": txt_own}


def main():
    d = A.frame()
    d = d[~d.notice_type]
    C = d[(d.stratum == "primary") & d.xml_present.fillna(False)].copy()
    with cf.ProcessPoolExecutor(12) as ex:
        r = pd.DataFrame(list(ex.map(one, C.pmcid, chunksize=100)))
    C = C.merge(r, on="pmcid")
    C["own_marked"] = C.own_structured | C.own_textual
    C["own_wd_marked"] = C.own_marked | C.withdrawal
    out = {"n": len(C),
           "preregistered_unmarked": A.boot(C.cluster, (~C.xml_marked).astype(float)),
           "own_unmarked": A.boot(C.cluster, (~C.own_marked).astype(float)),
           "own_plus_withdrawal_unmarked": A.boot(C.cluster, (~C.own_wd_marked).astype(float)),
           "marked_only_via_reference_lists": int((C.xml_marked & ~C.own_marked).sum()),
           "withdrawal_wording_adds": int((~C.own_marked & C.withdrawal).sum()),
           "txt_header_share": round(float(C.txt_header.mean()), 4),
           "H3_own": A.boot(C.cluster, C.own_wd_marked.astype(float) - C.txt_own.astype(float)),
           "own_marked_share": round(float(C.own_wd_marked.mean()), 4), "txt_own_share": round(float(C.txt_own.mean()), 4),
           "sidecar_given_own_unmarked": round(float(C[~C.own_wd_marked].sidecar_flag.fillna(False).mean()), 4),
           "neither_own_marker_nor_flag": int((~C.own_wd_marked & ~C.sidecar_flag.fillna(False)).sum())}
    top = C.publisher_name.value_counts().head(15).index
    out["own_unmarked_by_publisher"] = {p: {"n": int((C.publisher_name == p).sum()),
                                            "unmarked": round(float((~C[C.publisher_name == p].own_wd_marked).mean()), 4)} for p in top}
    json.dump(out, open(A.TAB / "sensitivity_d3.json", "w"), indent=1)
    C[["pmcid", "own_structured", "own_textual", "own_kinds", "withdrawal", "txt_header", "txt_own"]].to_csv(
        A.TAB / "documents_d3.csv.gz", index=False)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
