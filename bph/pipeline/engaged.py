"""Step 3b: cross-check the people engaged in developing the SRA against the landscape.

Input: the SRA's stakeholder engagement workbook (internal; path as argument or
<WORK>/engagement/stakeholder_engagement.xlsx). People are merged across its sheets (the master
"Workshops" list, the researcher contact list, staff questionnaire respondents interested in Blue Pacific
Horizons, and workshop invitations), keyed by email where one is given, otherwise by name. Emails are
used only for merging and are never written out.

Each person is matched to UoA authors in the landscape by name (full name, first name + surname, or
initial + surname when unique; OpenAlex splits some people into several profiles, so all matches are kept).
People not found are looked up in OpenAlex (authors with a UoA affiliation) to show whether they are at
UoA but outside the landscape's current scope, and what they research.

Writes data/engaged.json (internal: git-ignored).
"""

import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import difflib

import openpyxl

sys.path.insert(0, str(Path(__file__).parent))
import oa  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("BPH_WORK", "/mnt/data/ubuntu/bph-work"))
UOA = "I154130895"
PROFESSIONAL = re.compile(r"uniservices|pvc maori|research communications|nga ara whetu|rio\b", re.I)


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).replace("ʻ", "").replace("'", "").replace("’", "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z\- ]+", " ", s).replace("-", " ").split()


def clean_name(s):
    return re.sub(r"\s+", " ", str(s or "")).strip().rstrip("?").strip()


def is_person(name):
    n = clean_name(name)
    return len(n.split()) >= 2 and not re.search(r"centre|center|nga ara whetu|\?", n, re.I)


def rows_of(ws):
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return [], {}
    h = {}
    for i, c in enumerate(rows[0]):
        k = re.sub(r"\s+", " ", str(c or "")).strip().lower()
        if k and k not in h:
            h[k] = i
    return rows[1:], h


def load(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    people = {}

    def person(name, email=None):
        name = clean_name(name)
        email = (str(email).strip().lower() if email and "@" in str(email) else None)
        nk = " ".join(norm(name))
        key = email or nk
        tk = nk.split()
        for k, p in people.items():
            same = (email and p["email"] == email) or nk in p["aliases"]
            if not same and not (email and p["email"]):
                # no email on one side: same first name(s) and a near-identical surname (e.g. Ta'ala / Taala)
                for a in p["aliases"]:
                    ta = a.split()
                    if len(ta) == len(tk) and ta[:-1] == tk[:-1] and difflib.SequenceMatcher(None, ta[-1], tk[-1]).ratio() >= 0.8:
                        same = True
            if same:
                p["aliases"].add(nk)
                if email and not p["email"]:
                    p["email"] = email
                return p
        p = people[key] = dict(name=name, nk=nk, aliases={nk}, email=email, faculty=None, expertise=None, roles=set())
        return p

    sheets = {ws.title.strip().lower(): ws for ws in wb.worksheets}
    ws = sheets.get("workshops")
    if ws:
        rows, h = rows_of(ws)
        for r in rows:
            name = r[h["name"]]
            if not is_person(name):
                continue
            p = person(name, r[h.get("email address")])
            p["faculty"] = p["faculty"] or (str(r[h["faculty"]]).strip() if r[h["faculty"]] else None)
            ex = r[h.get("expertise")] if "expertise" in h else None
            if ex and str(ex).strip():
                if "co-convener" in str(ex).lower():
                    p["roles"].add("Co-convener")
                else:
                    p["expertise"] = p["expertise"] or str(ex).strip()
            for col, role in (("workshop two", "Workshop 2"), ("workshop three", "Workshop 3"), ("online hui 1 (wed)", "Online hui"),
                              ("online hui 2 (fri)", "Online hui"), ("survey list", "Self-nominated"), ("survet two list", "Survey 2"),
                              ("conveners list", "Invited by conveners"), ("rio list", "RIO list")):
                if col in h and str(r[h[col]] or "").strip().lower() == "yes":
                    p["roles"].add(role)
    ws = sheets.get("researcher contact list")
    if ws:
        rows, h = rows_of(ws)
        for r in rows:
            name = r[h["name"]]
            if not is_person(name):
                continue
            p = person(name, r[h.get("email address")])
            p["faculty"] = p["faculty"] or (str(r[h["faculty"]]).strip() if r[h["faculty"]] else None)
            ex = r[h.get("expertise")]
            if ex and str(ex).strip() and not p["expertise"]:
                p["expertise"] = str(ex).strip()
            if str(r[h.get("status")] or "").strip() or str(r[h.get("comment")] or "").strip():
                p["roles"].add("Conversation")
            if str(r[h.get("workshop 1 invite list")] or "").strip().lower().startswith("yes"):
                p["roles"].add("Workshop 1")
    ws = sheets.get("staff questionnaire results_1")
    if ws:
        rows, h = rows_of(ws)
        bph = next((i for k, i in h.items() if k.startswith("blue pacific horizons")), None)
        for r in rows:
            if bph is None or not str(r[bph] or "").strip():
                continue
            name = r[h.get("full name")] or r[h.get("name")]
            if not is_person(name):
                continue
            p = person(name, r[h.get("email address")])
            p["faculty"] = p["faculty"] or (str(r[h["faculty/lsri"]]).strip() if r[h.get("faculty/lsri")] else None)
            p["roles"].add("Self-nominated")
    ws = sheets.get("workshop 3 invites")
    if ws:
        rows, h = rows_of(ws)
        for r in rows:
            if is_person(r[h["name"]]):
                person(r[h["name"]])["roles"].add("Workshop 3")
    return list(people.values())


def name_tokens(s):
    """Lower-case ASCII tokens of a name; hyphenated surnames stay one token (e.g. Smith-Jones)."""
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"[ʻ'’‘`\.]", "", s).replace("‐", "-")
    return re.sub(r"[^a-z\- ]+", " ", s).split()


def first_ok(a, b):
    """First names agree: equal, an initial of the other, initials of a hyphenated name (e.g. JP / Jean-Pierre),
    or one a 3+ letter prefix of the other (e.g. Sam / Samantha)."""
    if a == b or (len(a) == 1 and b.startswith(a)) or (len(b) == 1 and a.startswith(b)):
        return True
    for x, y in ((a, b), (b, a)):
        if "-" in x and len(y) <= 3 and "".join(part[:1] for part in x.split("-")) == y:
            return True
    return min(len(a), len(b)) >= 3 and (a.startswith(b) or b.startswith(a))


def surname_parts(tokens):
    last = tokens[-1] if tokens else ""
    return {x for x in [last, *last.split("-")] if len(x) > 1}


def surnames(p):
    """The person's surname parts, plus the surname in their email address (catches spelling variants and hyphenated surnames)."""
    out = surname_parts(name_tokens(p["name"]))
    if p.get("email"):
        local = p["email"].split("@")[0]
        if "." in local:
            out |= surname_parts(name_tokens(local.split(".", 1)[1].replace(".", " ")))
    return out


def match(people, authors):
    by_surname = defaultdict(list)
    for i, a in enumerate(authors):
        t = name_tokens(a["name"])
        if len(t) >= 2:
            for x in surname_parts(t):
                by_surname[x].append((i, t))
    for p in people:
        t = name_tokens(p["name"])
        firsts = [t[0]] + ([t[1]] if len(t[0]) == 1 and len(t) >= 3 else [])   # an initial first, e.g. "J Robert Smith"
        hits = set()
        for L in surnames(p):
            for i, at in by_surname.get(L, []):
                for f in firsts:
                    # the author's first name, or a spelled-out middle name they go by (e.g. Mary Ann Smith known as Ann Smith)
                    if first_ok(at[0], f) or (len(at) > 2 and len(at[1]) >= 3 and len(f) >= 3 and first_ok(at[1], f)):
                        hits.add(i)
        p["atlas"] = sorted(hits)
    return people


def lookup(p):
    queries = [" ".join(p["name"].replace("'", "").split())]
    if p.get("email") and "." in p["email"].split("@")[0]:
        es = p["email"].split("@")[0].split(".", 1)[1].replace(".", " ").replace("-", " ")
        if es.split()[-1] not in queries[0].lower():
            queries.append(p["name"].split()[0] + " " + es)
    res = []
    for q in queries:
        r = oa.get("/authors", {"search": q, "filter": f"affiliations.institution.lineage:{UOA}", "per_page": 5,
                                "select": "id,display_name,works_count,cited_by_count,topics,last_known_institutions"})
        res += (r or {}).get("results", [])
    sn = surnames(p)
    ok = [a for a in res if surname_parts(name_tokens(a["display_name"])) & sn]
    if not ok:
        return None
    a = max(ok, key=lambda x: x.get("works_count") or 0)
    aid = a["id"].rsplit("/", 1)[-1]
    w = oa.get("/works", {"filter": f"author.id:{aid},publication_year:2020-2026", "per_page": 3, "sort": "cited_by_count:desc",
                          "select": "id,display_name,publication_year"})
    return dict(id=aid, name=a["display_name"], works=a.get("works_count"), recent=(w or {}).get("meta", {}).get("count"),
                topics=[x["display_name"] for x in (a.get("topics") or [])[:3]],
                sample=[x["display_name"] for x in (w or {}).get("results", [])[:3]],
                at_uoa=any(i.get("id", "").endswith(UOA) for i in a.get("last_known_institutions") or []))


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else WORK / "engagement" / "stakeholder_engagement.xlsx"
    if not path.exists():
        print("no engagement workbook; skipping")
        (ROOT / "data" / "engaged.json").write_text("[]")
        return
    land = json.loads((ROOT / "data" / "landscape.json").read_text())
    people = match(load(path), land["authors"])
    works_of = defaultdict(set)
    for k, w in enumerate(land["works"]):
        for a in w["a"]:
            works_of[a].add(k)
    out = []
    for p in sorted(people, key=lambda x: x["name"].split()[-1].lower()):
        staff = bool(PROFESSIONAL.search(p["faculty"] or "")) or bool(PROFESSIONAL.search(p["expertise"] or ""))
        n_atlas = len(set().union(*[works_of[i] for i in p["atlas"]])) if p["atlas"] else 0
        rec = dict(name=p["name"], faculty=p["faculty"], expertise=p["expertise"], roles=sorted(p["roles"]),
                   atlas=p["atlas"], n=n_atlas, staff=staff)
        if not p["atlas"]:
            rec["oa"] = lookup(p)
        rec["status"] = "in" if p["atlas"] else ("staff" if staff else ("outside" if rec.get("oa") else "notfound"))
        out.append(rec)
    (ROOT / "data" / "engaged.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    from collections import Counter
    print(len(out), "people;", Counter(r["status"] for r in out), "| spent", oa.spent())
    for r in out:
        if r["status"] != "in":
            o = r.get("oa") or {}
            print(f"  {r['status']:8s} {r['name']:28s} {r['faculty'] or '':24s} recent={o.get('recent')} topics={o.get('topics')}")



if __name__ == "__main__":
    main()
