"""Retraction-marker detection (plan section 2). Committed before any cohort file was parsed.

xml_markers(bytes)  -> dict of marker flags found in a JATS XML file
txt_markers(str)    -> dict of textual marker flags found in the plain-text rendition
Each returns {"structured": bool, "textual": bool, "kinds": [names]}.
"""
import re

from lxml import etree

TITLE = re.compile(r"^\W*(retracted|retraction|withdrawn)\b", re.I)
STATEMENT = re.compile(
    r"\b(?:(?:this|the)\s+(?:article|paper|manuscript|publication|study)\s+(?:has\s+been|have\s+been|was|is)\s+"
    r"(?:formally\s+|officially\s+)?retracted|retraction\s+notice|notice\s+of\s+retraction|retracted\s+article)\b",
    re.I)
TOKEN = re.compile(r"\bRETRACTED\b")


def _local(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _attr(el, name):
    for k, v in el.attrib.items():
        if _local(k) == name:
            return v
    return ""


def xml_markers(data):
    kinds = []
    try:
        root = etree.fromstring(data, parser=etree.XMLParser(recover=True, huge_tree=True, resolve_entities=False,
                                                              no_network=True))
    except etree.XMLSyntaxError:
        return {"structured": False, "textual": False, "kinds": ["unparseable"], "article_type": ""}
    if root is None:
        return {"structured": False, "textual": False, "kinds": ["unparseable"], "article_type": ""}
    for el in root.iter():
        t = _local(el.tag)
        if t == "related-article" and "retract" in _attr(el, "related-article-type").lower():
            kinds.append("related-article")
        elif t == "notes" and "retract" in _attr(el, "notes-type").lower():
            kinds.append("notes")
        elif t == "custom-meta" and "retract" in " ".join(el.itertext()).lower():
            kinds.append("custom-meta")
        elif t == "event" and "retract" in _attr(el, "event-type").lower():
            kinds.append("pub-history-event")
        elif t == "article-version" and "retract" in " ".join(el.itertext()).lower():
            kinds.append("article-version")
    structured = bool(kinds)
    title = ""
    for el in root.iter():
        if _local(el.tag) == "article-title" and any(_local(a.tag) == "title-group" for a in el.iterancestors()) \
                and any(_local(a.tag) == "article-meta" for a in el.iterancestors()):
            title = " ".join(" ".join(el.itertext()).split())
            break
    text = " ".join(root.itertext())
    tk = []
    if TITLE.search(title):
        tk.append("title-prefix")
    if STATEMENT.search(text):
        tk.append("statement")
    if TOKEN.search(text):
        tk.append("token")
    return {"structured": structured, "textual": bool(tk), "kinds": sorted(set(kinds)) + tk,
            "article_type": _attr(root, "article-type"), "title": title[:300]}


def txt_markers(s):
    lines = [l for l in (s or "").splitlines() if l.strip()][:3]
    tk = []
    if any(TITLE.search(l) for l in lines):
        tk.append("title-prefix")
    if STATEMENT.search(s or ""):
        tk.append("statement")
    if TOKEN.search(s or ""):
        tk.append("token")
    return {"structured": False, "textual": bool(tk), "kinds": tk}


if __name__ == "__main__":       # self-test on synthetic documents (no corpus file)
    ns = 'xmlns:xlink="http://www.w3.org/1999/xlink"'
    a = f'<article {ns} article-type="research-article"><front><article-meta><title-group><article-title>RETRACTED: A ' \
        f'study</article-title></title-group><related-article related-article-type="retraction-forward" ' \
        f'xlink:href="10.1/x"/></article-meta></front><body><p>Text.</p></body></article>'.encode()
    b = b'<article article-type="research-article"><front><article-meta><title-group><article-title>Retraction ' \
        b'Watch and the literature</article-title></title-group></article-meta></front><body><p>We studied how ' \
        b'retracted papers are cited.</p></body></article>'
    c = b'<article><front><article-meta><title-group><article-title>Effects of X</article-title></title-group>' \
        b'</article-meta></front><body><p>This article has been retracted at the request of the editors.</p></body></article>'
    for name, doc in (("a", a), ("b", b), ("c", c)):
        print(name, xml_markers(doc))
    print(txt_markers("RETRACTED ARTICLE: Effects of X\n\nAbstract ..."), txt_markers("Effects of X\nAbstract"))


# ---------------- D3: the same rules, ignoring reference lists (validation found PMC flags *cited* retracted works
# with related-article inside <ref>, so a link or retraction wording there says nothing about the citing article)
def _in_refs(el):
    return any(_local(a.tag) in ("ref", "ref-list") for a in el.iterancestors())


def xml_markers_own(data):
    try:
        root = etree.fromstring(data, parser=etree.XMLParser(recover=True, huge_tree=True, resolve_entities=False,
                                                              no_network=True))
    except etree.XMLSyntaxError:
        return {"structured": False, "textual": False, "kinds": ["unparseable"]}
    if root is None:
        return {"structured": False, "textual": False, "kinds": ["unparseable"]}
    kinds, parts = [], []
    for el in root.iter():
        if _in_refs(el):
            continue
        t = _local(el.tag)
        if t == "related-article" and "retract" in _attr(el, "related-article-type").lower():
            kinds.append("related-article")
        elif t == "notes" and "retract" in _attr(el, "notes-type").lower():
            kinds.append("notes")
        elif t == "custom-meta" and "retract" in " ".join(el.itertext()).lower():
            kinds.append("custom-meta")
        elif t == "event" and "retract" in _attr(el, "event-type").lower():
            kinds.append("pub-history-event")
        elif t == "article-version" and "retract" in " ".join(el.itertext()).lower():
            kinds.append("article-version")
        if el.text and not isinstance(el.tag, type(etree.Comment)):
            parts.append(el.text)
        if el.tail and el.getparent() is not None and not _in_refs(el.getparent()) and _local(el.getparent().tag) not in ("ref", "ref-list"):
            parts.append(el.tail)
    title = ""
    for el in root.iter():
        if _local(el.tag) == "article-title" and not _in_refs(el) \
                and any(_local(a.tag) == "title-group" for a in el.iterancestors()) \
                and any(_local(a.tag) == "article-meta" for a in el.iterancestors()):
            title = " ".join(" ".join(el.itertext()).split())
            break
    text = " ".join(parts)
    tk = []
    if TITLE.search(title):
        tk.append("title-prefix")
    if STATEMENT.search(text):
        tk.append("statement")
    if TOKEN.search(text):
        tk.append("token")
    return {"structured": bool(kinds), "textual": bool(tk), "kinds": sorted(set(kinds)) + tk}
