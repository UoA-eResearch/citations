"""Step 1: fetch candidate University of Auckland works in or about the Pacific from OpenAlex.

Candidates (UoA lineage, 2020 to date, OpenAlex core corpus) come from five queries:
  P  title/abstract names Pacific Islands or peoples        (lenses.LENS_P)
  O  title/abstract names the Pacific Ocean or its climate   (lenses.LENS_O)
  A  title/abstract names Aotearoa/NZ/Māori AND a theme       (lenses.A_PLACE x A_THEME)
  M  title/abstract names an ocean, Earth or climate term     (lenses.LENS_M)
  X  co-authored with an institution in a Pacific Island country or territory
and the four lens queries again with a written affiliation naming the University of Auckland / Waipapa
Taumata Rau instead of the institution link (R*), for UoA authorships that OpenAlex linked elsewhere.
Two more routes (November 2026, after BPH's meeting):
  U* the four lens queries for works by the UoA authors found above whose record carries no affiliation for
     them (common for book chapters, law and humanities preprints and reports), kept only when the author's
     OpenAlex profile places them at UoA in the publication year or the year before;
  V  the UoA works of 2020 onwards in the Vā Atlas corpus (Pacific research methodologies citation network,
     pacific/), which the title/abstract search can miss.
<WORK>/uoa_author_years.json keeps each author's UoA years for analyse.py.
Each candidate is re-checked locally in analyse.py; this step only gathers records.

Writes <WORK>/works_raw.jsonl (one record per work, with the queries that found it) and
<WORK>/institutions.json (coordinates and country of every co-author institution).
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import oa  # noqa: E402
from lenses import UOA_RAW_SEARCH, lens_filters  # noqa: E402
from tagging import UOA_RAW, _AUT  # noqa: E402

WORK = Path(os.environ.get("BPH_WORK", "/mnt/data/ubuntu/bph-work"))
UOA = "I154130895"
YEARS = "2020-2026"
VA_CORPUS = Path(os.environ.get("VA_CORPUS", "/mnt/data/ubuntu/pacific-work/works.jsonl"))


def uoa_linked(a):
    """UoA by institution link or by written affiliation (never AUT)."""
    if any(oa.short(i.get("id")) == UOA or any(oa.short(x) == UOA for x in i.get("lineage") or [])
           for i in a.get("institutions") or []):
        return True
    return any(UOA_RAW.search(s) and not _AUT.search(s) for s in a.get("raw_affiliation_strings") or [])


def no_affiliation(a):
    return not (a.get("institutions") or []) and not (a.get("raw_affiliation_strings") or [])
PACIFIC_ISLAND_CC = "AS CK FJ FM GU KI MH MP NC NR NU PF PG PN PW SB TK TO TV VU WF WS".split()
SELECT = ",".join([
    "id", "doi", "display_name", "publication_year", "publication_date", "type", "cited_by_count",
    "fwci", "citation_normalized_percentile", "authorships", "primary_location", "primary_topic",
    "topics", "keywords", "sustainable_development_goals", "awards", "funders",
    "abstract_inverted_index", "open_access", "language",
])


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    base = f"authorships.institutions.lineage:{UOA},publication_year:{YEARS}"
    queries = {k: ",".join([base, *v]) for k, v in lens_filters().items()}
    queries["X"] = base + ",institutions.country_code:" + "|".join(PACIFIC_ISLAND_CC)
    for k, v in lens_filters().items():
        queries["R" + k] = ",".join([f"publication_year:{YEARS}", UOA_RAW_SEARCH, *v])
    works, found = {}, {}
    for q, flt in queries.items():
        n = 0
        for w in oa.paginate("/works", {"filter": flt, "select": SELECT}):
            wid = oa.short(w["id"])
            works.setdefault(wid, w)
            found.setdefault(wid, set()).add(q)
            n += 1
        print(f"  {q}: {n} works (union {len(works)})", flush=True)

    # V: UoA works (2020+) in the Vā Atlas corpus, fetched in full by ID
    if VA_CORPUS.exists():
        va = []
        for line in open(VA_CORPUS):
            w = json.loads(line)
            if 2020 <= (w.get("publication_year") or 0) and any(uoa_linked(a) for a in w.get("authorships") or []):
                va.append(oa.short(w["id"]))
        new = [x for x in va if x not in works]
        for k in range(0, len(new), 50):
            res = oa.get("/works", {"filter": "ids.openalex:" + "|".join(new[k:k + 50]), "per_page": 50, "select": SELECT})
            for w in res["results"]:      # OpenAlex may answer with the current ID of a merged record
                works.setdefault(oa.short(w["id"]), w)
                found.setdefault(oa.short(w["id"]), set()).add("V")
        for x in va:
            if x in works:
                found.setdefault(x, set()).add("V")
        print(f"  V: {len(va)} UoA works in the Vā Atlas corpus, {len(new)} new (union {len(works)})", flush=True)

    # U*: works with no affiliation for a UoA author, in years their profile places them at UoA
    seed = sorted({oa.short((a.get("author") or {}).get("id")) for w in works.values() for a in w.get("authorships") or []
                   if (a.get("author") or {}).get("id") and uoa_linked(a)})
    years = {}
    for k in range(0, len(seed), 50):
        res = oa.get("/authors", {"filter": "openalex:" + "|".join(seed[k:k + 50]), "per_page": 50, "select": "id,affiliations"})
        for a in res["results"]:
            ys = set()
            for af in a.get("affiliations") or []:
                ins = af.get("institution") or {}
                if oa.short(ins.get("id")) == UOA or any(oa.short(x) == UOA for x in ins.get("lineage") or []):
                    ys |= set(af.get("years") or [])
            if ys:
                years[oa.short(a["id"])] = sorted(ys)
    (WORK / "uoa_author_years.json").write_text(json.dumps(years))
    ids = sorted(years)
    for q, parts in lens_filters().items():
        n = 0
        for k in range(0, len(ids), 50):
            flt = ",".join([f"publication_year:{YEARS}", "author.id:" + "|".join(ids[k:k + 50]), *parts])
            for w in oa.paginate("/works", {"filter": flt, "select": SELECT}):
                wid = oa.short(w["id"])
                y = w.get("publication_year") or 0
                ok = [oa.short(a["author"]["id"]) for a in w.get("authorships") or []
                      if (a.get("author") or {}).get("id") and oa.short(a["author"]["id"]) in years and no_affiliation(a)
                      and (y in years[oa.short(a["author"]["id"])] or y - 1 in years[oa.short(a["author"]["id"])])]
                if not ok:
                    continue
                if wid not in works:
                    n += 1
                works.setdefault(wid, w)
                found.setdefault(wid, set()).add("U" + q)
        print(f"  U{q}: {n} new works by UoA authors with no affiliation on the record (union {len(works)})", flush=True)
    print(f"  {len(seed)} UoA authors seen; {len(years)} with UoA years in their profile", flush=True)

    with open(WORK / "works_raw.jsonl", "w") as f:
        for wid, w in works.items():
            w["_found_by"] = sorted(found[wid])
            f.write(json.dumps(w, ensure_ascii=False) + "\n")

    inst_ids = sorted({oa.short(i["id"]) for w in works.values() for a in w.get("authorships") or []
                       for i in a.get("institutions") or [] if i.get("id")})
    insts = {}
    for k in range(0, len(inst_ids), 100):
        chunk = inst_ids[k:k + 100]
        res = oa.get("/institutions", {"filter": "ids.openalex:" + "|".join(chunk), "per_page": 100,
                                       "select": "id,display_name,country_code,type,geo"})
        for i in res["results"]:
            g = i.get("geo") or {}
            insts[oa.short(i["id"])] = dict(name=i["display_name"], country=i.get("country_code"), type=i.get("type"),
                                            city=g.get("city"), lat=g.get("latitude"), lng=g.get("longitude"))
    (WORK / "institutions.json").write_text(json.dumps(insts, ensure_ascii=False))
    print(f"{len(works)} works, {len(insts)} institutions; spent {oa.spent()}")


if __name__ == "__main__":
    main()
