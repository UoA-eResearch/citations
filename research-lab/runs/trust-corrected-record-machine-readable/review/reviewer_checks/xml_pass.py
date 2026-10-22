"""Reviewer check: an independent pass over every fetched XML (primary, recent, undated), recording WHERE each
retraction marker sits (article-meta / front / body / back / reference list / sub-article), the article type, the
title, body length and notice-like features. Writes xml_pass.parquet next to this script.
Run: venv/bin/python -I xml_pass.py
"""
import concurrent.futures as cf
import re
import sys
from pathlib import Path

import pandas as pd
from lxml import etree

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
FILES = RUN / "data" / "files"

TITLE = re.compile(r"^\W*(retracted|retraction|withdrawn)\b", re.I)
STATEMENT = re.compile(
    r"\b(?:(?:this|the)\s+(?:article|paper|manuscript|publication|study)\s+(?:has\s+been|have\s+been|was|is)\s+"
    r"(?:formally\s+|officially\s+)?retracted|retraction\s+notice|notice\s+of\s+retraction|retracted\s+article)\b", re.I)
TOKEN = re.compile(r"\bRETRACTED\b")
TCLASS = re.compile(r"^\W*(retracted|retraction|withdrawn|withdrawal|notice of retraction|expression of concern|erratum|"
                    r"corrigendum|correction|editorial expression|statement of retraction|retraction note)", re.I)


def L(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def attr(el, name):
    for k, v in el.attrib.items():
        if L(k) == name:
            return v
    return ""


def loc(el):
    anc = [L(a.tag) for a in el.iterancestors()]
    if "ref" in anc or "ref-list" in anc:
        return "ref"
    if "sub-article" in anc or "response" in anc:
        return "sub-article"
    if "article-meta" in anc:
        return "article-meta"
    if "front" in anc:
        return "front"
    if "body" in anc:
        return "body"
    if "back" in anc:
        return "back"
    return "other"


def one(pmcid):
    out = {"pmcid": pmcid}
    p = FILES / f"{pmcid}.xml"
    if not p.exists():
        out["err"] = "missing"
        return out
    try:
        root = etree.fromstring(p.read_bytes(), parser=etree.XMLParser(recover=True, huge_tree=True,
                                                                        resolve_entities=False, no_network=True))
    except Exception as e:
        out["err"] = repr(e)[:80]
        return out
    if root is None:
        out["err"] = "none"
        return out
    out["article_type"] = attr(root, "article-type")
    texts = {k: [] for k in ("article-meta", "front", "body", "back", "ref", "sub-article", "other")}
    rels, notes, cm, subs = [], [], 0, []
    title = ""
    ver = ""
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        t = L(el.tag)
        lc = loc(el)
        if t == "related-article":
            rels.append(f"{attr(el, 'related-article-type') or '?'}@{lc}")
        elif t == "notes" and attr(el, "notes-type"):
            notes.append(f"{attr(el, 'notes-type')}@{lc}")
        elif t == "custom-meta" and "retract" in " ".join(el.itertext()).lower():
            cm += 1
        elif t == "sub-article":
            subs.append(attr(el, "article-type") or "?")
        elif t == "article-id" and attr(el, "pub-id-type") == "pmcid-ver":
            ver = (el.text or "").strip()
        elif t == "article-title" and not title and lc == "article-meta":
            title = " ".join(" ".join(el.itertext()).split())
        if el.text:
            texts[lc].append(el.text)
        if el.tail and el.getparent() is not None:
            texts[loc(el.getparent())].append(el.tail)
    out.update(title=title[:300], pmcid_ver=ver, n_sub=len(subs), sub_types=";".join(subs), rel="|".join(rels),
               notes="|".join(notes), custom_meta=cm, body_chars=sum(len(x) for x in texts["body"]),
               title_class=(TCLASS.match(title).group(1).lower() if TCLASS.match(title) else ""),
               title_rule=bool(TITLE.search(title)))
    stmt, tok, snip = [], [], ""
    for k, parts in texts.items():
        s = " ".join(parts)
        m = STATEMENT.search(s)
        if m:
            stmt.append(k)
            if not snip and k != "ref":
                snip = s[max(0, m.start() - 80):m.end() + 80]
        if TOKEN.search(s):
            tok.append(k)
    out.update(stmt_locs=";".join(stmt), token_locs=";".join(tok), snippet=" ".join(snip.split())[:220])
    return out


def main():
    c = pd.read_parquet(RUN / "data" / "cohort.parquet")
    c = c[c.in_snapshot & ~c.notice & c.stratum.isin(["primary", "recent", "undated"])]
    ids = list(c.pmcid)
    print(len(ids), "files", flush=True)
    with cf.ProcessPoolExecutor(20) as ex:
        rows = list(ex.map(one, ids, chunksize=100))
    d = pd.DataFrame(rows)
    d.to_parquet(HERE / "xml_pass.parquet", index=False)
    print(d.err.notna().sum() if "err" in d else 0, "errors;", len(d), "rows written")


if __name__ == "__main__":
    main()
