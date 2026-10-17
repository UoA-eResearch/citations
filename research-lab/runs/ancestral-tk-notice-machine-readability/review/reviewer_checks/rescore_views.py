"""Reviewer's independent re-scorer for all 18,000 record-views. Structural parsing (XML/JSON) rather than the study's
regex field windows. Same preregistered definitions: element = Local Contexts URI (/label/, /notice/, /projects/) or an
exact vocabulary name; preserve = element inside a rights-type field distinct from the licence; degrade = present only
in the licence field (schema.org) or in free text / non-rights fields; drop = absent; unavailable = no record.
Writes rescore_all.csv (one row per record-view, with the field paths where the element sits), rescore_disagreements.csv,
rescore_summary.json, and handcheck_rescore_sheet.txt (the reviewer's hand sample)."""
import csv, gzip, json, random, re, sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
RAW = RUN / "data" / "raw" / "views"
V = json.load(open(RUN / "results" / "tables" / "vocabulary.json"))

URI_RE = re.compile(r"localcontexts(?:hub)?\.org/(label|notice|projects?)/([A-Za-z0-9\-]+)", re.I)
NOTICE_NAMES = [r"TK Notice", r"Traditional Knowledge Notice", r"BC Notice", r"Biocultural Notice", r"Attribution Incomplete Notice", r"Open to Collaborate Notice"]
def label_pat(slug):
    kind, rest = slug.split("-", 1)
    words = r"[ \-_]+".join(re.escape(w) for w in rest.split("-"))
    full = {"tk": r"(?:TK|Traditional Knowledge)", "bc": r"(?:BC|Biocultural)"}[kind]
    return re.compile(full + r"[ \-_]+" + words + r"(?:[ \-_]+Label)?\b", re.I)
NAME_RES = [re.compile(r"\b(?:" + "|".join(NOTICE_NAMES) + r")\b", re.I)] + [label_pat(s) for s in V["labels"]]

def has_element(s):
    if not s:
        return False
    return bool(URI_RE.search(s)) or any(r.search(s) for r in NAME_RES)

def body(doi, view):
    return gzip.decompress((RAW / f"{doi.replace('/', '_')}__{view}.gz").read_bytes()).decode("utf-8", "replace")

def local(tag):
    return tag.rsplit("}", 1)[-1]

def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, f"{path}[]")
    elif isinstance(o, str):
        yield path, o

def xml_paths(root):
    """yield (path, text-including-attributes) for every element"""
    def rec(el, p):
        here = p + "/" + local(el.tag)
        txt = " ".join([el.text or ""] + [f'{local(k)}="{v}"' for k, v in el.attrib.items()])
        yield here, txt
        for c in el:
            yield from rec(c, here)
    yield from rec(root, "")

def rescore(view, status, b):
    """-> (call, where) where = sorted set of field paths holding the element"""
    if status != 200 or not b.strip():
        return "unavailable", []
    if view in ("datacite_xml", "oai_datacite", "oai_dc"):
        if "idDoesNotExist" in b or "<error" in b[:2000] and "GetRecord" in b[:2000] and "<record" not in b:
            return "unavailable", []
        try:
            root = ET.fromstring(b.encode("utf-8", "replace"))
        except ET.ParseError:
            return ("drop" if not has_element(b) else "degrade"), ["unparsed"]
        where = sorted({p for p, t in xml_paths(root) if has_element(t)})
        if not where:
            return "drop", []
        rights = [p for p in where if local(p.rsplit("/", 1)[-1]) == "rights"]
        return ("preserve" if rights else "degrade"), where
    if view == "openaire":
        try:
            j = json.loads(b)
        except Exception:
            return "unavailable", ["json error"]
        if not j.get("header", {}).get("numFound"):
            return "unavailable", []
        where = sorted({p for p, s in walk(j.get("results", [])) if has_element(s)})
        if not where:
            return "drop", []
        rights = [p for p in where if re.search(r"\.(license|accessRight|bestAccessRight)\b", p)]
        return ("preserve" if rights else "degrade"), where
    if view in ("crosscite_json", "csl_json", "schemaorg_jsonld"):
        try:
            j = json.loads(b)
        except Exception:
            return ("drop" if not has_element(b) else "degrade"), ["unparsed"]
        where = sorted({p for p, s in walk(j) if has_element(s)})
        if not where:
            return "drop", []
        if view == "crosscite_json":
            rights = [p for p in where if re.match(r"^\.rights(_list|List)?\b", p)]
            return ("preserve" if rights else "degrade"), where
        if view == "csl_json":
            return "degrade", where       # CSL has no rights variable; license/rights would be non-standard
        return "degrade", where           # schema.org: licence-only rule (plan section 3)
    # bibtex, citation_text: no rights field
    if not has_element(b):
        return "drop", []
    where = []
    if view == "bibtex":
        where = sorted({m.group(1) for m in re.finditer(r"^\s*([A-Za-z]+)\s*=\s*\{(.*?)\}\s*,?\s*$", b, re.M | re.S) if has_element(m.group(2))}) or ["bibtex-body"]
    else:
        where = ["citation-text"]
    return "degrade", where

def main():
    rows = [json.loads(l) for l in open(RUN / "data" / "views.jsonl")]
    out, dis = [], []
    for i, r in enumerate(rows):
        b = body(r["doi"], r["view"])
        call, where = rescore(r["view"], r["status"], b)
        out.append(dict(doi=r["doi"], view=r["view"], scorer=r["result"], reviewer=call, where="|".join(where)[:300], body_chars=len(b)))
        if call != r["result"]:
            dis.append(out[-1])
        if i % 3000 == 0:
            print("rescored", i, flush=True)
    with open(HERE / "rescore_all.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    with open(HERE / "rescore_disagreements.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(dis)
    summ = dict(n=len(out), n_disagree=len(dis), disagree_by=Counter(f"{d['view']}:{d['scorer']}->{d['reviewer']}" for d in dis),
                where_by_view_result=defaultdict(Counter))
    for o in out:
        summ["where_by_view_result"][f"{o['view']}:{o['reviewer']}"][o["where"] or "-"] += 1
    summ["where_by_view_result"] = {k: dict(v.most_common(8)) for k, v in summ["where_by_view_result"].items()}
    summ["disagree_by"] = dict(summ["disagree_by"])
    json.dump(summ, open(HERE / "rescore_summary.json", "w"), indent=1)
    print(json.dumps(summ, indent=1))

    # ---- the reviewer's hand sample: all non-schema.org 'degrade', the OpenAIRE 'preserve', the schema.org 'drop',
    #      plus random OpenAIRE drops, schema.org degrades, rights-view preserves and citation-format drops (seed 4242)
    rnd = random.Random(4242)
    byk = defaultdict(list)
    for o in out:
        byk[(o["view"], o["scorer"])].append(o)
    pick = []
    for (v, s), lst in byk.items():
        if s == "degrade" and v != "schemaorg_jsonld":
            pick += lst
        if v == "openaire" and s == "preserve":
            pick += lst
        if v == "schemaorg_jsonld" and s == "drop":
            pick += lst
    pick += rnd.sample(byk[("openaire", "drop")], 10) + rnd.sample(byk[("schemaorg_jsonld", "degrade")], 8)
    for v in ("datacite_xml", "oai_datacite", "oai_dc", "crosscite_json"):
        pick += rnd.sample(byk[(v, "preserve")], 3)
    for v in ("bibtex", "csl_json", "citation_text"):
        pick += rnd.sample(byk[(v, "drop")], 3)
    seen = set(); uniq = []
    for p in pick:
        k = (p["doi"], p["view"])
        if k not in seen:
            seen.add(k); uniq.append(p)
    pats = [URI_RE] + NAME_RES
    sheet = []
    for i, p in enumerate(uniq):
        b = body(p["doi"], p["view"])
        spans = sorted({m.start() for rx in pats for m in rx.finditer(b)})
        ex = []
        last = -10**9
        for s in spans:
            if s - last < 250:
                continue
            ex.append(b[max(0, s - 220):s + 220].replace("\n", " ")); last = s
            if len(ex) >= 3:
                break
        if not ex:
            ex = [b[max(0, m.start() - 60):m.start() + 240].replace("\n", " ") for m in re.finditer(r"rights|licen[cs]e|usageInfo|copyright", b, re.I)][:2] or [b[:400].replace("\n", " ")]
        sheet.append(f"### r{i:03d} {p['doi']} | view={p['view']} | scorer={p['scorer']} | reviewer-parser={p['reviewer']} | where={p['where']} | {p['body_chars']} chars\n" + "\n".join(f"  > {e}" for e in ex) + "\n")
    (HERE / "handcheck_rescore_sheet.txt").write_text("\n".join(sheet))
    with open(HERE / "handcheck_rescore_sample.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "doi", "view", "scorer", "reviewer_parser", "where"])
        for i, p in enumerate(uniq):
            w.writerow([f"r{i:03d}", p["doi"], p["view"], p["scorer"], p["reviewer"], p["where"]])
    print("hand sample:", len(uniq), Counter((p["view"], p["scorer"]) for p in uniq))

if __name__ == "__main__":
    main()
