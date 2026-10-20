"""Validate the two detection routes against known-fabricated and known-real citations (plan section 4, step 5).

The six citations invented in the filings behind *Mata v. Avianca* are the field's canonical fabrications, and
they are the sharpest available test of whether this screen can see one. Each is run through both routes:

  by citation  does the reporter-volume-page resolve to a case in the corpus?
  by name      does any of the ten million case names carry these party names?

Writes results/tables/detection_validation.json.
"""
import json
import pickle
import sys
from pathlib import Path

import numpy as np
from rapidfuzz import fuzz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from namenorm import norm_name, party_score, tokens_of  # noqa: E402  the same definition the index was built with

RUN = Path(__file__).resolve().parents[1]
IDX, T = RUN / "data" / "index", RUN / "results" / "tables"

# The six fabricated citations from Mata v. Avianca, and genuine controls.
FABRICATED = [
    ("Varghese v. China Southern Airlines Co.", 925, "F.3d", 1339),
    ("Shaboon v. Egyptair", None, None, None),
    ("Petersen v. Iran Air", 905, "F. Supp. 2d", 121),
    ("Martinez v. Delta Airlines, Inc.", None, None, None),
    ("Estate of Durden v. KLM Royal Dutch Airlines", None, None, None),
    ("Miller v. United Airlines, Inc.", 174, "F.3d", 366),
]
REAL = [
    ("Mata v. Avianca, Inc.", None, None, None),
    ("Roe v. Wade", 410, "U.S.", 113),
    ("Brown v. Board of Education", 347, "U.S.", 483),
    ("Gideon v. Wainwright", 372, "U.S.", 335),
]


def norm_reporter(r):
    return "".join(ch for ch in r.lower() if ch.isalnum())


def main():
    T.mkdir(parents=True, exist_ok=True)
    z = np.load(IDX / "pages.npz", allow_pickle=False)
    offs, pages, clusters = z["offs"], z["pages"], z["clusters"]
    keymap = {(r, int(v)): i for i, (r, v) in enumerate(zip(z["reporters"], z["volumes"]))}
    names = np.load(IDX / "names.npy", allow_pickle=True)
    tokens = pickle.load(open(IDX / "tokens.pkl", "rb"))
    dropped = set(json.load(open(IDX / "dropped_tokens.json"))["dropped"])
    name_tokens = [set(n.split()) for n in names]

    def by_citation(vol, rep, page):
        if vol is None:
            return {"route": "citation", "verdict": "not a reporter citation"}
        i = keymap.get((norm_reporter(rep), int(vol)))
        if i is None:
            return {"route": "citation", "verdict": "unresolved", "why": "reporter-volume absent"}
        a, b = offs[i], offs[i + 1]
        pg, cl = pages[a:b], clusters[a:b]
        j = np.searchsorted(pg, page, side="right") - 1
        if j < 0:
            return {"route": "citation", "verdict": "unresolved", "why": "page below the volume"}
        nxt = int(pg[j + 1]) if j + 1 < len(pg) else None
        if int(pg[j]) == page:
            return {"route": "citation", "verdict": "RESOLVES", "cluster": int(cl[j]), "why": "exact first page"}
        if nxt is None or page < nxt:
            return {"route": "citation", "verdict": "RESOLVES", "cluster": int(cl[j]),
                    "why": f"inside the case beginning at {int(pg[j])}"}
        return {"route": "citation", "verdict": "unresolved", "why": "falls in a gap"}

    def by_name(case, threshold=80):
        """Score the cited name against the corpus.

        Requiring every token to be present is too strict -- a caption written "Delta Air Lines" against a
        citation written "Delta Airlines" would be reported as a case that does not exist. Requiring only common
        tokens is too loose: "Martinez v. Delta Airlines" matches some unrelated Martinez case. So the rarest
        tokens select candidates and rapidfuzz scores the whole name, and the output is a score for a human to
        check, not a verdict. The threshold is a screening cut, and every candidate below it is verified by hand.
        """
        want = tokens_of(norm_name(case)) - dropped     # too common to be evidence either way
        if not want:
            return {"route": "name", "verdict": "too generic to screen"}
        pools = {t: tokens.get(t) for t in want}
        missing = sorted(t for t, p in pools.items() if p is None or len(p) == 0)   # in no caption anywhere
        present = {t: p for t, p in pools.items() if p is not None and len(p) > 0}
        if not present:
            return {"route": "name", "verdict": "NO SUCH CASE", "tokens": sorted(want),
                    "why": f"no case name anywhere contains {missing}"}
        # the two rarest tokens are the most selective; intersect their postings for candidates
        rarest = sorted(present, key=lambda t: len(present[t]))[:2]
        cand = present[rarest[0]]
        for t in rarest[1:]:
            cand = np.intersect1d(cand, present[t], assume_unique=False)
        if len(cand) == 0:
            return {"route": "name", "verdict": "NO SUCH CASE", "tokens": sorted(want),
                    "why": f"no case name contains both {rarest}", "missing_tokens": missing}
        target = norm_name(case)
        scored = [(party_score(fuzz, target, str(names[i])), int(i)) for i in cand[:60000]]
        best, bi = max(scored)
        return {"route": "name", "verdict": "found" if best >= threshold else "NO SUCH CASE",
                "best_score": round(float(best), 1), "best_match": str(names[bi])[:70],
                "candidates": len(cand), "missing_tokens": missing}

    out = {"fabricated": [], "real": []}
    for group, items in (("fabricated", FABRICATED), ("real", REAL)):
        for case, vol, rep, page in items:
            out[group].append({"case": case, "cite": f"{vol} {rep} {page}" if vol else None,
                               "citation_route": by_citation(vol, rep, page), "name_route": by_name(case)})

    fab_caught = sum(1 for r in out["fabricated"] if r["name_route"]["verdict"] == "NO SUCH CASE")
    fab_cleared_by_cite = sum(1 for r in out["fabricated"] if r["citation_route"]["verdict"] == "RESOLVES")
    real_found = sum(1 for r in out["real"] if r["name_route"]["verdict"] == "found")
    out["summary"] = {
        "fabricated": len(FABRICATED), "caught_by_name": fab_caught,
        "would_be_cleared_by_citation_alone": fab_cleared_by_cite,
        "real_controls": len(REAL), "real_found_by_name": real_found,
    }
    json.dump(out, open(T / "detection_validation.json", "w"), indent=1)
    print(json.dumps(out["summary"], indent=1))
    for g in ("fabricated", "real"):
        print(f"\n{g.upper()}")
        for r in out[g]:
            print(f"  {r['case'][:44]:<44} cite:{r['citation_route']['verdict']:<12} "
                  f"name:{r['name_route']['verdict']}")


if __name__ == "__main__":
    main()
