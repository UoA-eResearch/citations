"""Step 1: fetch candidate University of Auckland works in or about the Pacific from OpenAlex.

Candidates (UoA lineage, 2020 to date, OpenAlex core corpus) come from five queries:
  P  title/abstract names Pacific Islands or peoples        (lenses.LENS_P)
  O  title/abstract names the Pacific Ocean or its climate   (lenses.LENS_O)
  A  title/abstract names Aotearoa/NZ/Māori AND a theme       (lenses.A_PLACE x A_THEME)
  M  title/abstract names an ocean, Earth or climate term     (lenses.LENS_M)
  X  co-authored with an institution in a Pacific Island country or territory
and the four lens queries again with a written affiliation naming the University of Auckland / Waipapa
Taumata Rau instead of the institution link (R*), for UoA authorships that OpenAlex linked elsewhere.
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

WORK = Path(os.environ.get("BPH_WORK", "/mnt/data/ubuntu/bph-work"))
UOA = "I154130895"
YEARS = "2020-2026"
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
