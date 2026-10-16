"""Preprint -> published-article links, and an independent confirmation of each.

Assertion routes (all ultimately asserted by the preprint server):
  biorxiv   bioRxiv/medRxiv API /pubs/{server}/{interval}/{cursor}: the server's own preprint->publication matches
  crossref  Crossref works/{preprint doi}: relation "is-preprint-of" (deposited by the server, "asserted-by subject")
            - for Research Square, Preprints.org, ChemRxiv etc. this is the only route
  (Europe PMC's "Preprint of" links are loaded from Crossref, and PreprintToPaper's "Published" label is bioRxiv's
  own link, so neither is independent; they are not used as separate routes.)
Independent confirmation, computed here: the published article's Crossref title is similar to the preprint title
(token-set Jaccard >= 0.5, stop words removed). A pair is used only if asserted AND confirmed. The alignment
validation (hand-coded pairs) is the further check that linked pairs are the same study.

Usage: venv/bin/python code/link.py biorxiv | crossref <parsed.jsonl.gz ...> | confirm <parsed.jsonl.gz ...>
"""
import gzip
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

RUN = Path(__file__).resolve().parents[1]
L = RUN / "data" / "raw" / "links"
UA = {"User-Agent": "research-lab preprint study (mailto:noreply@anthropic.com)"}


def get(url, tries=6):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=60)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except Exception:
            time.sleep(min(60, 2 ** i))
    return None


def biorxiv():
    for server in ("biorxiv", "medrxiv"):
        out = L / f"pubs_{server}.jsonl"
        cursor, n = 0, 0
        with open(out, "w") as fh:
            while True:
                d = get(f"https://api.biorxiv.org/pubs/{server}/2013-01-01/2026-10-17/{cursor}")
                if not d or not d.get("collection"):
                    break
                for r in d["collection"]:
                    fh.write(json.dumps({k: r.get(k) for k in ("preprint_doi", "published_doi", "published_journal",
                                                               "preprint_date", "published_date")}) + "\n"); n += 1
                total = int(d["messages"][0].get("total", 0))
                cursor += len(d["collection"])
                if cursor >= total:
                    break
        print(server, n, flush=True)


def preprint_dois(parsed):
    dois = set()
    for p in parsed:
        for l in gzip.open(p, "rt"):
            r = json.loads(l)
            if r.get("doi"):
                dois.add(r["doi"].lower())
    return sorted(dois)


def crossref(parsed):
    out = L / "crossref_relations.jsonl"
    done = set()
    if out.exists():
        done = {json.loads(l)["doi"] for l in open(out)}
    todo = [d for d in preprint_dois(parsed) if d not in done]

    def one(doi):
        d = get(f"https://api.crossref.org/works/{doi}?mailto=noreply@anthropic.com")
        rel = ((d or {}).get("message") or {}).get("relation") or {}
        return dict(doi=doi, found=d is not None, is_preprint_of=[x.get("id", "").lower() for x in rel.get("is-preprint-of", [])
                                                                   if x.get("id-type") == "doi"])
    with open(out, "a") as fh, ThreadPoolExecutor(8) as ex:
        for k, r in enumerate(ex.map(one, todo)):
            fh.write(json.dumps(r) + "\n")
            if k % 2000 == 0:
                print("crossref", k, "/", len(todo), flush=True)


def tokens(s):
    return set(re.findall(r"[a-z0-9]+", (s or "").lower())) - {"the", "a", "an", "of", "in", "and", "for", "on", "to", "with", "by"}


def confirm(parsed):
    """Build the candidate pair table: asserted by >= 1 server route, confirmed by title similarity."""
    pre = {}
    for p in parsed:
        for l in gzip.open(p, "rt"):
            r = json.loads(l)
            if r.get("doi"):
                pre.setdefault(r["doi"].lower(), r)
    asserted = {}
    for server in ("biorxiv", "medrxiv"):
        f = L / f"pubs_{server}.jsonl"
        if f.exists():
            for l in open(f):
                r = json.loads(l)
                if r["preprint_doi"] and r["published_doi"]:
                    asserted.setdefault((r["preprint_doi"].lower(), r["published_doi"].lower()), set()).add("biorxiv_api")
    f = L / "crossref_relations.jsonl"
    if f.exists():
        for l in open(f):
            r = json.loads(l)
            for pub in r["is_preprint_of"]:
                asserted.setdefault((r["doi"], pub), set()).add("crossref")
    cand = [(a, b, s) for (a, b), s in asserted.items() if a in pre]
    meta = L / "published_crossref_meta.jsonl"
    have = {json.loads(l)["doi"]: json.loads(l) for l in open(meta)} if meta.exists() else {}
    todo = sorted({b for _, b, _ in cand} - set(have))

    def one(doi):
        d = get(f"https://api.crossref.org/works/{doi}?mailto=noreply@anthropic.com")
        m = (d or {}).get("message") or {}
        au = (m.get("author") or [{}])[0]
        return dict(doi=doi, title=" ".join(m.get("title") or []), first_family=(au.get("family") or "").lower(),
                    journal=" ".join(m.get("container-title") or []), issued=m.get("issued"))
    with open(meta, "a") as fh, ThreadPoolExecutor(8) as ex:
        for k, r in enumerate(ex.map(one, todo)):
            fh.write(json.dumps(r) + "\n"); have[r["doi"]] = r
            if k % 2000 == 0:
                print("published meta", k, "/", len(todo), flush=True)
    rows = []
    for a, b, s in cand:
        p, m = pre[a], have.get(b, {})
        ta, tb = tokens(p.get("title")), tokens(m.get("title"))
        jac = len(ta & tb) / len(ta | tb) if ta | tb else 0.0
        rows.append(dict(preprint_doi=a, published_doi=b, routes=sorted(s), ppr=p.get("ppr"), server=p.get("server"),
                         version=p.get("version"), title_jaccard=round(jac, 3), published_journal=m.get("journal"),
                         confirmed=bool(jac >= 0.5)))
    with open(RUN / "data" / "pairs_candidates.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print("candidates", len(rows), "confirmed", sum(r["confirmed"] for r in rows))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "biorxiv":
        biorxiv()
    else:
        {"crossref": crossref, "confirm": confirm}[cmd](sys.argv[2:])
