"""Step 2: assemble the Pacific Research Methodologies corpus from OpenAlex.

A work is in the corpus when any of these hold (each reason is recorded per work):
  seed      it is a record of a seed text (seeds_resolved.json)
  cites     it cites a Pacific-specific seed
  cites+pac it cites a broadly cited seed (e.g. Decolonizing Methodologies) AND its title or
            abstract names a Pacific place, people or research context
  term      its title or abstract names a Pacific research methodology or concept
Searches cover the core and expansion corpora (corpus=all), so theses and repository items
that OpenAlex keeps outside its core are included and flagged (is_xpac).

Writes <WORK>/works.jsonl (full records) and <WORK>/institutions.json (geo).
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import oa  # noqa: E402
from queries import PACIFIC_TERMS, PRM_TERMS, PRM_TERMS_NEED_PACIFIC  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("PACIFIC_WORK", "/mnt/data/ubuntu/pacific-work"))
SELECT = ",".join([
    "id", "doi", "display_name", "publication_year", "type", "cited_by_count", "fwci",
    "authorships", "primary_location", "referenced_works", "primary_topic", "language",
    "is_xpac", "open_access", "abstract_inverted_index",
])


def ors(terms):
    return " OR ".join(terms)


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    seeds = json.loads((ROOT / "data/seeds_resolved.json").read_text())["seeds"]
    specific = [r["id"] for s in seeds if not s["broad"] for r in s["records"]]
    broad = [r["id"] for s in seeds if s["broad"] for r in s["records"]]
    seed_ids = specific + broad

    works, reasons = {}, {}

    def add(it, why):
        n = 0
        for w in it:
            wid = oa.short(w["id"])
            works.setdefault(wid, w)
            reasons.setdefault(wid, set()).add(why)
            n += 1
        print(f"  {why:10s} {n:6d} works  (corpus now {len(works)})", flush=True)

    base = {"select": SELECT, "corpus": "all"}
    add(oa.paginate("/works", {**base, "filter": "ids.openalex:" + "|".join(seed_ids)}), "seed")
    add(oa.paginate("/works", {**base, "filter": "cites:" + "|".join(specific)}), "cites")
    add(oa.paginate("/works", {**base, "filter": "cites:" + "|".join(broad)
                               + ",title_and_abstract.search:" + PACIFIC_TERMS}), "cites+pac")
    add(oa.paginate("/works", {**base, "filter": "title_and_abstract.search:" + ors(PRM_TERMS)}), "term")
    add(oa.paginate("/works", {**base, "filter": "title_and_abstract.search:" + ors(PRM_TERMS_NEED_PACIFIC)
                               + ",title_and_abstract.search:" + PACIFIC_TERMS}), "term")

    with open(WORK / "works.jsonl", "w") as f:
        for wid, w in works.items():
            w["_reasons"] = sorted(reasons[wid])
            f.write(json.dumps(w, ensure_ascii=False) + "\n")

    # Institution coordinates for the map (batched, 100 ids per call).
    inst_ids = sorted({oa.short(i["id"]) for w in works.values() for a in w.get("authorships") or []
                       for i in a.get("institutions") or [] if i.get("id")})
    insts = {}
    for k in range(0, len(inst_ids), 100):
        chunk = inst_ids[k:k + 100]
        res = oa.get("/institutions", {"filter": "ids.openalex:" + "|".join(chunk), "per_page": 100,
                                       "select": "id,display_name,country_code,type,geo"})
        for i in res["results"]:
            g = i.get("geo") or {}
            insts[oa.short(i["id"])] = dict(name=i["display_name"], country=i.get("country_code"),
                                            type=i.get("type"), city=g.get("city"),
                                            lat=g.get("latitude"), lng=g.get("longitude"))
    (WORK / "institutions.json").write_text(json.dumps(insts, ensure_ascii=False))
    print(f"{len(works)} works, {len(insts)} institutions; spent {oa.spent()}")


if __name__ == "__main__":
    main()
