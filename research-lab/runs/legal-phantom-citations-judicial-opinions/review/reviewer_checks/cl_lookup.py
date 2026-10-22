"""Reviewer check 1: look every re-verification row up on CourtListener's public search API, by the cited party
names (caseName) and by the citation string. Polite: one request per ~1.3 s, anonymous."""
import csv, json, re, time, urllib.parse, urllib.request
RUN = "/mnt/citations/research-lab/runs/legal-phantom-citations-judicial-opinions"
OUT = RUN + "/review/reviewer_checks"
STOP = {"v","vs","the","of","and","et","al","in","re","ex","rel","inc","llc","co","corp","ltd","na"}
UA = {"User-Agent": "research-review (nyou045@aucklanduni.ac.nz)"}
def get(q):
    url = "https://www.courtlistener.com/api/rest/v4/search/?type=o&q=" + urllib.parse.quote(q)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                d = json.load(r)
            return {"count": d.get("count"), "top": [{"name": x.get("caseName"), "cite": x.get("citation"), "date": x.get("dateFiled"), "court": x.get("court_id")} for x in d.get("results", [])[:4]]}
        except Exception as e:  # noqa
            err = str(e); time.sleep(5 + 10 * attempt)
    return {"error": err}
rows = list(csv.DictReader(open(OUT + "/reverify_rows.tsv"), delimiter="\t"))
done = {}
try:
    for l in open(OUT + "/cl_lookup.jsonl"): d = json.loads(l); done[(d["sheet"], d["k"])] = d
except FileNotFoundError: pass
fh = open(OUT + "/cl_lookup.jsonl", "a")
for r in rows:
    key = (r["sheet"], r["k"])
    if key in done: continue
    toks = [t for t in re.findall(r"[a-z0-9]+", r["cited_name"].lower()) if len(t) >= 3 and t not in STOP]
    nq = "caseName:(" + " ".join(toks[:6]) + ")" if toks else None
    out = {"sheet": r["sheet"], "k": r["k"], "cite": r["cite"], "cited_name": r["cited_name"], "label": r["label"]}
    out["by_name"] = get(nq) if nq else None; time.sleep(1.3)
    out["by_cite"] = get('"' + r["cite"] + '"'); time.sleep(1.3)
    fh.write(json.dumps(out) + "\n"); fh.flush()
print("done", len(rows))
