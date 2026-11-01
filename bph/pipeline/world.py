"""Step 6: world context. UoA's share of the world's Pacific-named research (OpenAlex search level).

Both numerator and denominator use the same OpenAlex title/abstract search (lenses P or O, 2020-2025),
without the local re-check, so the share compares like with like:
  by_subfield  [subfield, world, uoa, share%] for each OpenAlex subfield (primary topic)
  by_year      [year, world, uoa]
  top_insts    institutions with the most Pacific-named outputs worldwide (for context)
Writes data/world.json.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import oa  # noqa: E402
from lenses import LENS_O, LENS_P, ors  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
UOA = "authorships.institutions.lineage:I154130895"


def groups(flt, by):
    r = oa.get("/works", {"filter": flt, "group_by": by, "per_page": 200})
    return {g["key_display_name"] or g["key"]: g["count"] for g in r["group_by"]}, r["meta"]["count"]


def main():
    pac = "publication_year:2020-2025,title_and_abstract.search:" + ors(LENS_P + LENS_O)
    w_sub, w_total = groups(pac, "primary_topic.subfield.id")
    u_sub, u_total = groups(f"{UOA},{pac}", "primary_topic.subfield.id")
    w_year, _ = groups(pac, "publication_year")
    u_year, _ = groups(f"{UOA},{pac}", "publication_year")
    insts, _ = groups(pac, "authorships.institutions.lineage")
    by_sub = sorted(([k, w_sub.get(k, 0), u, round(100 * u / w_sub[k], 2) if w_sub.get(k) else None]
                     for k, u in u_sub.items()), key=lambda r: -r[2])
    # Universities ranked by works naming Pacific Islands & peoples (lens P only), 2020-2025.
    p_only = "publication_year:2020-2025,title_and_abstract.search:" + ors(LENS_P)
    r = oa.get("/works", {"filter": p_only, "group_by": "authorships.institutions.lineage", "per_page": 200})
    p_world = r["meta"]["count"]
    ids = [g["key"].rsplit("/", 1)[-1] for g in r["group_by"]]
    types = {}
    for k in range(0, len(ids), 100):
        res = oa.get("/institutions", {"filter": "ids.openalex:" + "|".join(ids[k:k + 100]), "per_page": 100,
                                       "select": "id,display_name,type,country_code"})
        for i in res["results"]:
            types[i["id"].rsplit("/", 1)[-1]] = (i["type"], i["display_name"], i.get("country_code"))
    unis = [(types[g["key"].rsplit("/", 1)[-1]][1], types[g["key"].rsplit("/", 1)[-1]][2], g["count"])
            for g in r["group_by"] if types.get(g["key"].rsplit("/", 1)[-1], ("",))[0] == "education"]
    doc = dict(world_total=w_total, uoa_total=u_total, share=round(100 * u_total / w_total, 2),
               by_subfield=by_sub, by_year=sorted([int(y), w_year.get(y, 0), u_year.get(y, 0)] for y in w_year),
               top_insts=sorted(insts.items(), key=lambda kv: -kv[1])[:30],
               p_world=p_world, p_universities=unis[:25])
    print("Universities, Pacific Islands & peoples:", [(i + 1, n, c, cnt) for i, (n, c, cnt) in enumerate(unis[:12])])
    (ROOT / "data" / "world.json").write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
    print(f"world {w_total}, UoA {u_total} ({doc['share']}%)")
    print("UoA rank among institutions:", [i for i, (k, v) in enumerate(doc["top_insts"]) if "Auckland" in k], doc["top_insts"][:12])
    print("spent", oa.spent())


if __name__ == "__main__":
    main()
