"""Reviewer check 3: run eyecite and the frozen parse.judge() on the three reviewing-court opinions that discuss a
trial court's fictitious cases (H.C. v. Contreras, Payne v. State, Shahid v. Esaam). Which full citations did
eyecite see, what name did it attach, and what did the screen decide? Read-only: imports the study's code."""
import json, sys
sys.path.insert(0, "/mnt/citations/research-lab/runs/legal-phantom-citations-judicial-opinions/code")
import parse  # noqa: E402
from namenorm import clean_cited  # noqa: E402
docs = json.load(open("/mnt/citations/research-lab/runs/legal-phantom-citations-judicial-opinions/review/reviewer_checks/pulled_docs.json"))
parse.init()
out = {}
for oid in ("11333339", "11320504", "11086650"):
    t = docs[oid]["text"]
    rows = []
    for c in parse.G["get_citations"](t):
        if not isinstance(c, parse.G["FullCaseCitation"]): continue
        g = c.groups
        try: vol, page = int(g.get("volume") or 0), int(g.get("page") or 0)
        except ValueError: continue
        rep = c.corrected_reporter() or g.get("reporter") or ""
        if not (vol and page and rep): continue
        md = c.metadata
        cited = clean_cited(getattr(md, "plaintiff", None) or "", getattr(md, "defendant", None) or "")
        j = parse.judge(rep, vol, page, cited)
        s0, e0 = c.span()
        rows.append({"cite": f"{vol} {rep} {page}", "cited": cited, "verdict": j["verdict"], "route": j["route"],
                     "resolved_name": j.get("resolved_name"), "best": j.get("best_name"), "score": j.get("best_name_score"),
                     "ctx": " ".join(t[max(0, s0 - 160):e0 + 60].split())})
    out[oid] = rows
    print(f"=== {oid} ({docs[oid]['date']}): {len(rows)} full citations")
    for r in rows:
        print(f"  {r['verdict']:<15} {r['cite']:<22} cited={r['cited'][:40]!r:<42} resolved={str(r['resolved_name'])[:35]!r}")
        print(f"      {r['ctx'][:230]}")
json.dump(out, open("/mnt/citations/research-lab/runs/legal-phantom-citations-judicial-opinions/review/reviewer_checks/judge_test.json", "w"), indent=1)
