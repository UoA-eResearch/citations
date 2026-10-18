"""Reviewer's independent evidence readers (not derived from code/generate.py).
NZ: the October 2026 Schedule PDF text (pdftotext -layout) and the XML's Special Authority request forms.
AU: the raw PBS API JSON for schedule 4751, all programs."""
import glob, html, json, re, sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
from names import norm  # the lab's shared normaliser (copied unchanged from an earlier run)
NS = "{http://schedule.pharmac.govt.nz/2006/07/Schedule#}"; MML = "{http://www.w3.org/1998/Math/MathML}"; XL = "{http://www.w3.org/1999/xlink}href"
ws = lambda s: re.sub(r"\s+", " ", s or "").strip()
nkey = lambda t: re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()
strip = lambda s: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()

def items():
    return [json.loads(l) for l in open(RUN / "data/items.jsonl")]

# ---------- NZ PDF ----------
_pdf = None
def pdf_lines():
    global _pdf
    if _pdf is None:
        _pdf = open(RUN / "data/raw/nz/Schedule_2026-10.txt").read().split("\n")
    return _pdf

HEAD = re.compile(r"^\s*([A-Z][A-Z0-9,\-\(\) ]{2,}?)(\s+–|\s+-|$)")
def nz_pdf_chem_blocks(chem, maxlines=40):
    """Blocks starting at lines that begin with the chemical's upper-cased name, until the next chemical heading."""
    L = pdf_lines(); up = chem.upper(); out = []
    for i, l in enumerate(L):
        if re.match(rf"\s*{re.escape(up)}\b", l) and not re.match(rf"\s*{re.escape(up)}\s*(\d|mg|mcg)", l):
            blk = [l.rstrip()]
            for j in range(i + 1, min(i + maxlines, len(L))):
                m = HEAD.match(L[j])
                if m and len(m.group(1)) > 3 and j > i + 1 and L[j].strip() == L[j].strip().upper()[:len(L[j].strip())] and ("–" in L[j] or " - " in L[j]) and not L[j].strip().startswith(up):
                    break
                if L[j].strip(): blk.append(L[j].rstrip())
            out.append("\n".join(blk))
    return out

def nz_pdf_sa_block(code, maxlines=120):
    """The ➽SA#### Special Authority block(s) from the PDF."""
    L = pdf_lines(); out = []
    for i, l in enumerate(L):
        if re.search(rf"➽\s*{code}\b", l):
            blk = [l.rstrip()]
            for j in range(i + 1, min(i + maxlines, len(L))):
                if re.search(r"➽\s*SA\d+", L[j]) or HEAD.match(L[j]) and ("–" in L[j]) and L[j].strip().split("–")[0].strip().isupper() and len(L[j].strip().split("–")[0].strip()) > 3:
                    break
                if L[j].strip(): blk.append(L[j].rstrip())
            out.append("\n".join(blk))
    return out

# ---------- NZ XML ----------
_xml = {}
def nz_xml(edition="2026-10"):
    if edition not in _xml:
        r = ET.parse(RUN / f"data/raw/nz/Schedule_{edition}.xml").getroot()
        forms = defaultdict(list)
        for q in r.iter(NS + "Request"):
            forms[q.get("Form")] += [ws("".join(ci.itertext())) for ci in q.iter(MML + "ci") if ws("".join(ci.itertext()))]
        sec = [s for s in r.findall(NS + "Section") if s.get("ID") == "B"][0]
        chems = defaultdict(list)  # norm name -> list of Chemical elements
        for ch in sec.iter(NS + "Chemical"):
            chems[norm(ch.findtext(NS + "Name") or "")].append(ch)
        _xml[edition] = (r, forms, chems)
    return _xml[edition]

def nz_sa_codes(chem, edition="2026-10"):
    r, forms, chems = nz_xml(edition); codes = set()
    for ch in chems.get(chem, []):
        for rule in ch.iter(NS + "Rule"):   # chemical, formulation and brand levels (ATC levels carry none)
            if rule.get("Type") == "Special" and rule.get("Attribute") == "Subsidy":
                codes.add(rule.get(XL))
    return codes

def nz_own_criteria(chem, editions=("2026-10", "2025-11")):
    out = set()
    for ed in editions:
        r, forms, chems = nz_xml(ed)
        for code in nz_sa_codes(chem, ed):
            out |= set(forms.get(code, []))
    return out

def nz_formulations(chem, edition="2026-10"):
    r, forms, chems = nz_xml(edition); out = []
    for ch in chems.get(chem, []):
        for f in ch.findall(NS + "Formulation"):
            sp = [x for x in f.iter(NS + "Rule") if x.get("Type") == "Special" and x.get("Attribute") == "Subsidy"]
            csp = [x for x in ch.findall(NS + "Rule") if x.get("Type") == "Special" and x.get("Attribute") == "Subsidy"]
            out.append((ch.findtext(NS + "Name"), f.findtext(NS + "Name"), "SA(chem)" if csp else ("SA(form/brand)" if sp else "")))
    return out

# ---------- AU raw JSON ----------
_au = {}
def au(code=4751):
    if code not in _au:
        load = lambda ep: [x for f in sorted(glob.glob(str(RUN / "data/raw/pbs" / f"{code}_{ep}_*.json"))) for x in json.load(open(f))["data"]]
        items_ = load("items"); rel = defaultdict(set)
        for x in load("item-restriction-relationships"): rel[x["pbs_code"]].add(x["res_code"])
        res = {x["res_code"]: x for x in load("restrictions")}
        pt = {str(x["prescribing_txt_id"]): x for x in load("prescribing-texts")}
        rpt = defaultdict(list)
        for x in load("restriction-prescribing-text-relationships"): rpt[x["res_code"]].append((x["pt_position"] or 0, str(x["prescribing_text_id"])))
        _au[code] = dict(items=items_, rel=rel, res=res, pt=pt, rpt=rpt)
    return _au[code]

def au_items(chem, code=4751, programs=None):
    A = au(code)
    return [x for x in A["items"] if norm(x.get("drug_name") or "") == chem and (programs is None or x.get("program_code") in programs)]

def au_restriction_texts(chem, code=4751, programs=("GE",)):
    """Distinct stripped restriction texts (li_html_text) for the drug's items, plus their prescribing texts by type."""
    A = au(code); out = {}
    for x in au_items(chem, code, programs):
        for rc in A["rel"].get(x["pbs_code"], ()):
            if rc in A["res"] and rc not in out:
                r = A["res"][rc]
                lines = [f"[{r.get('authority_method')} | {r.get('treatment_phase')}] " + strip(r.get("li_html_text") or r.get("schedule_html_text"))]
                out[rc] = "\n".join(lines)
    return out

def au_own_clauses(chem, code=4751, programs=("GE",)):
    """Unique clauses across the drug's GE restriction texts: split on '; AND', '; OR', 'AND', 'OR' sentence joins."""
    cl = set()
    for t in au_restriction_texts(chem, code, programs).values():
        t = re.sub(r"^\[[^\]]*\]\s*", "", t)
        t = re.sub(r"Listing of Pharmaceutical Benefits \(NHL\) - Schedule 4 part \d+", "", t)
        for c in re.split(r";\s*(?:AND|OR)\b|\b(?:AND|OR)\s+(?=Patient|The|Treatment|Must|Pat)|(?<=[a-z\)])\s+(?=Patient must|The treatment must|The condition must|Must be)", t):
            c = c.strip(" ;.")
            if len(c) >= 12: cl.add(c)
    return sorted(cl)
