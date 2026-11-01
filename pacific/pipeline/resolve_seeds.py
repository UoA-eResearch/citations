"""Step 1: resolve the seed list (seeds.py) to OpenAlex works.

For each seed, search titles across the core and expansion corpora (corpus=all) and accept
records whose title closely matches and whose byline carries one of the seed's surnames (or,
with no byline, an exact title within a year). All accepted records are kept: editions and
duplicate records of one text all count as that seed. Seeds with no accepted record are the
coverage gap: canonical Pacific texts the open scholarly graph does not surface.

Writes data/seeds_resolved.json.
"""

import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import oa  # noqa: E402
from seeds import SEEDS, STRANDS  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data" / "seeds_resolved.json"
SELECT = "id,doi,display_name,publication_year,type,cited_by_count,authorships,primary_location,is_xpac,referenced_works_count"


DASHES = dict.fromkeys(map(ord, "‐‑‒–—―−-"), " ")
OKINA = dict.fromkeys(map(ord, "'‘’ʻʼ`´"), None)


def norm(s):
    s = str(s or "").translate(DASHES).translate(OKINA)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9 ]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def title_sim(a, b):
    a, b = norm(a), norm(b)
    full = SequenceMatcher(None, a, b).ratio()
    # Many records drop or reword the subtitle; compare the main titles too.
    ma, mb = norm(a.split(":")[0]), norm(b.split(":")[0])
    main = SequenceMatcher(None, ma, mb).ratio() if min(len(ma), len(mb)) >= 12 else 0
    # A record that carries the whole seed title plus an extra subtitle (or vice versa).
    short_, long_ = sorted((a, b), key=len)
    contained = 0.95 if len(short_) >= 25 and short_ in long_ else 0
    return max(full, main * 0.97, contained)


def byline_match(work, surnames):
    names = " | ".join(
        norm(a.get("raw_author_name") or "") + " " + norm((a.get("author") or {}).get("display_name") or "")
        for a in work.get("authorships") or [])
    return any(norm(s) and re.search(r"\b" + re.escape(norm(s)) + r"\b", names) for s in surnames)


def query_texts(seed):
    # The main title is the most stable part across records; the full title (diacritics folded)
    # catches records whose main title is short or reworded.
    # Both ways of folding the okina: dropped ("kwaraae") and split ("kwara ae"); the index
    # tokenises some records one way and some the other.
    title = seed["title"]
    main = title.split(":")[0] if len(title.split(":")[0]) >= 18 else title
    split = [re.sub(r"[\"'‘’ʻ()\-–—?!,.;:]", " ", t) for t in (main, title)]
    return list(dict.fromkeys([norm(main), norm(title), *split]))


def resolve(seed):
    hits = {}
    for q in query_texts(seed):
        res = oa.get("/works", {"search": q, "corpus": "all", "per_page": 50, "select": SELECT})
        for w in (res or {}).get("results", []):
            hits[w["id"]] = w
    accepted = []
    for w in hits.values():
        ts = title_sim(seed["title"], w.get("display_name"))
        by = byline_match(w, seed["surnames"])
        yr = w.get("publication_year")
        near = yr is not None and abs(yr - seed["year"]) <= 1
        if (ts >= 0.86 and by) or (ts >= 0.97 and not w.get("authorships") and near):
            accepted.append(dict(
                id=oa.short(w["id"]), title=w.get("display_name"), year=yr, type=w.get("type"),
                cited_by=w.get("cited_by_count", 0), is_xpac=bool(w.get("is_xpac")),
                refs=w.get("referenced_works_count", 0), doi=w.get("doi"),
                source=((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
                title_sim=round(ts, 3)))
    accepted.sort(key=lambda r: -r["cited_by"])
    return accepted


def main():
    out = []
    for s in SEEDS:
        recs = resolve(s)
        status = "missing" if not recs else ("expansion-only" if all(r["is_xpac"] for r in recs) else "core")
        out.append({**s, "status": status, "records": recs,
                    "cited_by": sum(r["cited_by"] for r in recs)})
        print(f"{status:15s} {s['key']:18s} recs={len(recs):2d} cites={sum(r['cited_by'] for r in recs):6d}  "
              f"{(recs[0]['title'][:70] if recs else '')}")
    OUT.write_text(json.dumps({"strands": STRANDS, "seeds": out}, indent=1, ensure_ascii=False))
    n = len(out)
    print(f"\n{sum(o['status'] == 'core' for o in out)}/{n} in core, "
          f"{sum(o['status'] == 'expansion-only' for o in out)} expansion-only, "
          f"{sum(o['status'] == 'missing' for o in out)} missing; spent {oa.spent()}")


if __name__ == "__main__":
    main()
