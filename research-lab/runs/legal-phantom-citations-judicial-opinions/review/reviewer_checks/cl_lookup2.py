"""Reviewer check 1 (lean): CourtListener name lookups, one request per ~4 s with backoff on 429.
Rows: every row labelled phantom / phantom-party-filing / party-filing-unverified / unverifiable, plus the 'real'
rows the index aid did not settle, plus the misattribution-sheet phantom."""
import csv, json, re, time, urllib.parse, urllib.request
RUN = "/mnt/citations/research-lab/runs/legal-phantom-citations-judicial-opinions"
OUT = RUN + "/review/reviewer_checks"
STOP = {"v","vs","the","of","and","et","al","in","re","ex","rel","inc","llc","co","corp","ltd","na","dept","div","cnty","grp","assoc","assocs","servs","int","intl","sec","rev","city","county","state","united","states"}
UA = {"User-Agent": "research-review (nyou045@aucklanduni.ac.nz)"}
def get(q):
    url = "https://www.courtlistener.com/api/rest/v4/search/?type=o&q=" + urllib.parse.quote(q)
    err = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                d = json.load(r)
            return {"q": q, "count": d.get("count"), "top": [{"name": x.get("caseName"), "cite": x.get("citation"), "date": x.get("dateFiled"), "court": x.get("court_id")} for x in d.get("results", [])[:5]]}
        except Exception as e:  # noqa
            err = str(e); time.sleep(20 * (attempt + 1))
    return {"q": q, "error": err}
rows = list(csv.DictReader(open(OUT + "/reverify_rows.tsv"), delimiter="\t"))
EXTRA_REAL = {("screened_reliance", "157"), ("placebo_reliance", "189"), ("placebo_reliance", "308"), ("placebo_reliance", "310"), ("placebo_flag", "8"), ("placebo_flag", "123"), ("screened_reliance", "128")}
todo = [r for r in rows if r["label"] not in ("real", "real(default)") or (r["sheet"], r["k"]) in EXTRA_REAL]
todo.append({"sheet": "misattributions", "k": "18", "cite": "185 A.3d 1283", "cited_name": "state v flores", "label": "phantom"})
done = set()
try:
    for l in open(OUT + "/cl_lookup2.jsonl"): d = json.loads(l); done.add((d["sheet"], d["k"]))
except FileNotFoundError: pass
fh = open(OUT + "/cl_lookup2.jsonl", "a")
for r in todo:
    if (r["sheet"], r["k"]) in done: continue
    toks = [t for t in re.findall(r"[a-z0-9]+", r["cited_name"].lower()) if len(t) >= 3 and t not in STOP]
    q = "caseName:(" + " ".join(toks[:5]) + ")" if toks else '"' + r["cite"] + '"'
    out = {"sheet": r["sheet"], "k": r["k"], "cite": r["cite"], "cited_name": r["cited_name"], "label": r["label"], "res": get(q)}
    fh.write(json.dumps(out) + "\n"); fh.flush(); time.sleep(4)
print("done", len(todo))
