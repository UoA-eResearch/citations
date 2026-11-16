"""Step 2d: works nominated by researchers, matched to OpenAlex where possible.

Blue Pacific Horizons collects lists of relevant work from researchers whose output the open record
under-counts (law and the humanities especially). Input, internal and not in the public repository:
<WORK>/nominated/nominated.json, a list of
  {researcher, author_ids: [OpenAlex author IDs; the first is the main profile, the rest are split profiles],
   field, subfield, source,
   items: [{title, year, type, venue, authors (count), forthcoming?, match? (title to match on, e.g. the
            reviewed book), also_match? [other titles OpenAlex may use]}]}

Each item is looked up in OpenAlex: first among the works of the researcher's profiles, then any work with a
matching title and an author with the researcher's surname; publication year within one of the item's; title
similarity >= 0.82 on folded titles (or the item's title contained in the record's). The best record becomes
the work (published versions preferred to preprints); other records matching the same item (a preprint copy,
a split profile's copy) are listed as duplicates, so each work is counted once. Items OpenAlex does not hold
(blog posts, submissions, forthcoming work, some chapters) become records built from the citation itself.

Writes <WORK>/nominated_works.jsonl (OpenAlex records with "_nom") and <WORK>/nominated_extra.jsonl.
"""

import difflib
import hashlib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import oa  # noqa: E402
from fetch_works import SELECT  # noqa: E402

WORK = Path(os.environ.get("BPH_WORK", "/mnt/data/ubuntu/bph-work"))
TYPE_RANK = {"preprint": 2, "other": 1}          # lower is preferred when scores tie


def fold(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", s)).strip()


def score(item, title):
    t = fold(title)
    best = 0.0
    for m in [item.get("match"), item["title"], *(item.get("also_match") or [])]:
        if not m:
            continue
        f = fold(m)
        r = difflib.SequenceMatcher(None, f, t).ratio()
        if len(f) > 25 and (f in t or t in f):
            r = max(r, 0.9)
        best = max(best, r)
    return best


def query(s):
    """Folded title without one-letter tokens (an apostrophe's stray "s" breaks OpenAlex search)."""
    return " ".join(t for t in fold(s).split() if len(t) > 1)


def candidates(item, ids, surname):
    # search every title the item may go by; a two-year gap is allowed (yearbooks and edited books often
    # carry a later date) but only for a near-exact title, see good()
    y = item["year"]
    yr = f"publication_year:{y - 2}-{y + 2}"
    titles = [t for t in [item.get("match"), item["title"], *(item.get("also_match") or [])] if t]
    out = []
    for t in titles:
        out += oa.get("/works", {"search": query(t)[:200], "filter": f"authorships.author.id:{'|'.join(ids)},{yr}", "per_page": 15, "select": SELECT})["results"]
    if not any(good(item, w) for w in out):
        for t in titles:
            words = " ".join(query(t).split()[:10])
            more = oa.get("/works", {"filter": f"title.search:{words},{yr}", "per_page": 25, "select": SELECT})["results"]
            out += [w for w in more if any(surname in fold((a.get("author") or {}).get("display_name")) for a in w.get("authorships") or [])]
    return out


def good(item, w):
    s, dy = score(item, w.get("display_name")), abs((w.get("publication_year") or 0) - item["year"])
    return s >= (0.82 if dy <= 1 else 0.95)


def main():
    src = WORK / "nominated" / "nominated.json"
    lists = json.loads(src.read_text()) if src.exists() else []
    used, works, extra = set(), [], []
    for L in lists:
        ids, surname = L["author_ids"], fold(L["researcher"]).split()[-1]
        n_match = 0
        for item in L["items"]:
            cands = {oa.short(w["id"]): w for w in candidates(item, ids, surname)}
            scored = sorted(((score(item, w.get("display_name")), w) for k, w in cands.items() if k not in used and good(item, w)),
                            key=lambda x: (-round(x[0], 2), TYPE_RANK.get(x[1].get("type"), 0)))
            nom = dict(researcher=L["researcher"], author_ids=ids, item=item["title"], forthcoming=bool(item.get("forthcoming")),
                       source=L.get("source"), field=L.get("field"), subfield=L.get("subfield"))
            if scored and scored[0][0] >= 0.82:
                s, w = scored[0]
                wid = oa.short(w["id"])
                used.add(wid)
                dupes = [oa.short(x["id"]) for sc, x in scored[1:] if sc >= 0.9 and oa.short(x["id"]) not in used]
                used.update(dupes)
                w["_nom"] = dict(nom, score=round(s, 3), dupes=dupes)
                works.append(w)
                n_match += 1
                print(f"  matched {s:.2f} {w.get('type'):12s} {wid} {'+' + str(len(dupes)) + ' dupes' if dupes else ''} | {item['title'][:70]}")
            else:
                key = hashlib.sha1(f"{L['researcher']}|{item['title']}|{item['year']}".encode()).hexdigest()[:10]
                extra.append(dict(nom, id="NOM-" + key, title=item["title"], year=item["year"], type=item.get("type", "other"),
                                  venue=item.get("venue"), authors=item.get("authors", 1), author_id=ids[0]))
                print(f"  not in OpenAlex      | {item['title'][:70]}" + (f" (best {scored[0][0]:.2f}: {scored[0][1].get('display_name', '')[:40]})" if scored else ""))
        print(f"{L['researcher']}: {len(L['items'])} items, {n_match} matched to OpenAlex, {len(L['items']) - n_match} built from the citation")
    with open(WORK / "nominated_works.jsonl", "w") as f:
        for w in works:
            f.write(json.dumps(w, ensure_ascii=False) + "\n")
    with open(WORK / "nominated_extra.jsonl", "w") as f:
        for e in extra:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"{len(works)} nominated works in OpenAlex, {len(extra)} from citations; spent {oa.spent()}")


if __name__ == "__main__":
    main()
