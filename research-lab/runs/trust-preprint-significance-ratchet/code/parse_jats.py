"""Parse JATS full text (Europe PMC preprint shards, or single PMC articles) into section-level plain text.

For each article: identifiers (archive PPR id, DOI, PMCID), version, server/journal, title, and a list of sections
(title, type, text), keeping the abstract separately. Tables and figure captions are kept as their own sections,
labelled, because statistics often sit there. MathML is flattened to its text; inline formatting is dropped.
Structure only: no statistic is extracted here.
"""
import gzip
import json
import re
import sys
from pathlib import Path

from lxml import etree

WS = re.compile(r"\s+")


def text_of(el):
    if el is None:
        return ""
    t = "".join(el.itertext())
    return WS.sub(" ", t).strip()


def sec_type(title):
    t = (title or "").lower()
    for k in ("abstract", "introduction", "background", "method", "material", "result", "discussion", "conclusion",
              "supplement", "acknowledg", "reference"):
        if k in t:
            return k
    return "other"


def parse_article(a):
    meta = a.find(".//article-meta")
    ids = {i.get("pub-id-type"): (i.text or "").strip() for i in (meta.findall("article-id") if meta is not None else [])}
    ver = meta.find("article-version") if meta is not None else None
    jt = a.find(".//journal-meta/journal-id")
    rec = dict(ppr=ids.get("archive"), doi=(ids.get("doi") or "").lower() or None, pmcid=ids.get("pmc") or ids.get("pmcid"),
               version=(ver.text.strip() if ver is not None and ver.text else None),
               server=(jt.text.strip() if jt is not None and jt.text else None),
               title=text_of(a.find(".//article-title")),
               abstract=" ".join(text_of(x) for x in a.findall(".//abstract")), sections=[])
    body = a.find("body")
    if body is not None:
        for s in body.iter("sec"):
            if s.getparent() is not None and s.getparent().tag == "sec":
                continue                                   # top-level sections only; subsections are inside
            title = text_of(s.find("title"))
            rec["sections"].append(dict(title=title, type=sec_type(title), text=text_of(s)))
        if not rec["sections"]:
            rec["sections"].append(dict(title="", type="body", text=text_of(body)))
    for tw in a.iter("table-wrap"):
        rec["sections"].append(dict(title=text_of(tw.find("label")), type="table", text=text_of(tw)))
    for fg in a.iter("fig"):
        rec["sections"].append(dict(title=text_of(fg.find("label")), type="figure", text=text_of(fg.find("caption"))))
    return rec


def iter_shard(path):
    with gzip.open(path, "rb") as fh:
        for _, el in etree.iterparse(fh, tag="article", recover=True, huge_tree=True):
            yield parse_article(el)
            el.clear()
            while el.getprevious() is not None:
                del el.getparent()[0]


def main(shards, out):
    n = 0
    with gzip.open(out, "wt", encoding="utf-8") as fo:
        for s in shards:
            for rec in iter_shard(s):
                fo.write(json.dumps(rec, ensure_ascii=False) + "\n"); n += 1
            print(s, n, flush=True)
    print("articles", n)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:-1], sys.argv[-1]))
