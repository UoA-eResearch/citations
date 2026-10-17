"""Section typing on real records: share of preprints/published articles with a 'result'-typed section, with no
<sec> at all ('body'), and how often table/figure text also sits inside a result section (duplication)."""
import gzip, json, sys, random
from collections import Counter
from pathlib import Path
from lxml import etree
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
import parse_jats as PJ
pairs = [json.loads(l) for l in open(RUN / "data/aligned/pairs.jsonl")]
keep = {p["preprint_doi"]: p for p in pairs}
pmc = {json.loads(l)["doi"]: json.loads(l)["pmcid"] for l in open(RUN / "data/raw/links/doi_pmcid.jsonl")}
# preprints: scan the parsed file for pairs' records (first 4000 matched)
c = Counter(); n = 0; dup = 0; dup_papers = 0; per_server = Counter(); per_server_res = Counter(); titles = Counter()
for l in gzip.open(RUN / "data/parsed/preprints.jsonl.gz", "rt"):
    r = json.loads(l)
    if r.get("doi") not in keep:
        continue
    n += 1
    types = {s["type"] for s in r["sections"]}
    srv = r.get("server"); per_server[srv] += 1
    if "result" in types: c["has_result"] += 1; per_server_res[srv] += 1
    if types == {"body"}: c["body_only"] += 1
    if not r["sections"]: c["no_sections"] += 1
    if "table" in types: c["has_table"] += 1
    if "figure" in types: c["has_figure"] += 1
    for s in r["sections"]:
        if s["type"] == "other": titles[s["title"][:40]] += 1
    # duplication: table text inside a result section
    res = " ".join(s["text"] for s in r["sections"] if s["type"] == "result")
    tabs = [s["text"] for s in r["sections"] if s["type"] == "table" and len(s["text"]) > 80]
    k = sum(1 for t in tabs if t[:80] in res)
    if k: dup += k; dup_papers += 1
    if n >= 4000: break
print("PREPRINTS scanned", n, dict(c))
print(" share with result section by server:", {s: f"{per_server_res[s]}/{per_server[s]}" for s in per_server})
print(" tables whose text also appears inside a result section:", dup, "in", dup_papers, "papers")
print(" most common 'other' section titles:", titles.most_common(25))
# published: random 400 XMLs
random.seed(1); sample = random.sample(pairs, 400)
c2 = Counter(); dup2 = 0; dup2_p = 0; titles2 = Counter(); m = 0
for p in sample:
    f = RUN / "data/raw/published" / f"{pmc.get(p['published_doi'])}.xml"
    if not f.exists(): continue
    root = etree.parse(str(f), etree.XMLParser(recover=True, huge_tree=True)).getroot()
    art = root if root.tag == "article" else root.find(".//article")
    rec = PJ.parse_article(art); m += 1
    types = {s["type"] for s in rec["sections"]}
    if "result" in types: c2["has_result"] += 1
    if types == {"body"}: c2["body_only"] += 1
    if "body" in types: c2["body_untitled"] += 1
    res = " ".join(s["text"] for s in rec["sections"] if s["type"] == "result")
    tabs = [s["text"] for s in rec["sections"] if s["type"] == "table" and len(s["text"]) > 80]
    k = sum(1 for t in tabs if t[:80] in res)
    if k: dup2 += k; dup2_p += 1
    for s in rec["sections"]:
        if s["type"] == "other": titles2[s["title"][:40]] += 1
print("\nPUBLISHED scanned", m, dict(c2))
print(" tables whose text also appears inside a result section:", dup2, "in", dup2_p, "papers")
print(" most common 'other' section titles:", titles2.most_common(25))
