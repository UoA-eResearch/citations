"""Reviewer check 5: the 45 flag opinions -- distinct opinion ids vs distinct clusters; which match Charlotin by
cluster id (reproducing flag_vs_database.json, for which no code exists); and a date-free fuzzy re-match of the
unmatched ones against every Charlotin row by case name."""
import csv, json, subprocess, re
from rapidfuzz import fuzz
RUN = "/mnt/citations/research-lab/runs/legal-phantom-citations-judicial-opinions"
S = RUN + "/data/screen"; OUT = RUN + "/review/reviewer_checks"
ver = list(csv.DictReader(open(S + "/verified.csv")))
flag = [v for v in ver if v["verdict"] == "phantom" and v["type"] == "flag"]
ops = {v["opinion_id"] for v in flag}; cl = {v["cluster_id"] for v in flag}
per = {v["period"] for v in flag}
print("flag phantom rows", len(flag), "distinct opinions", len(ops), "distinct clusters", len(cl), "periods", per)
# also: are any of the 45 opinion ids on the sheet more than once with mixed verdicts? and opinions.tsv dates
dates = {}
for r in csv.DictReader(open(S + "/opinions.tsv"), delimiter="\t"):
    if r["opinion_id"] in ops: dates[r["opinion_id"]] = (r["date"], r["type"], r["cluster_id"])
print("date range", min(d[0] for d in dates.values()), max(d[0] for d in dates.values()))
from collections import Counter
print("opinion types", Counter(d[1] for d in dates.values()))
cal = list(csv.DictReader(open(S + "/charlotin_matched.csv")))
matched_ids = {r["cluster_id"] for r in cal if r["matched"] == "1"}
in_db = {c for c in cl if c in matched_ids}
print("clusters matched to Charlotin by cluster id:", len(in_db), "not:", len(cl - in_db))
# cluster names for the unmatched
pat = OUT + "/_ids.txt"; open(pat, "w").write("".join(f"{c}\t" for c in sorted(cl - in_db)))
names = {}
for c in sorted(cl - in_db):
    line = subprocess.run(["grep", "-m1", "-P", f"^{c}\\t", RUN + "/data/index/clusters.tsv"], capture_output=True, text=True).stdout.strip()
    if line:
        f = line.split("\t"); names[c] = {"date": f[1], "status": f[3], "name": f[4]}
raw = list(csv.DictReader(open(RUN + "/data/raw/charlotin.csv", encoding="utf-8")))
def norm(s): return " ".join(re.findall(r"[a-z0-9]+", (s or "").lower()))
res = []
for c, info in names.items():
    nn = norm(info["name"])
    best = max(((fuzz.token_set_ratio(nn, norm(r["Case Name"])), r) for r in raw), key=lambda x: x[0])
    s, r = best
    res.append({"cluster_id": c, "cluster_name": info["name"], "cluster_date": info["date"], "best_charlotin": r["Case Name"], "charlotin_date": r["Date"], "charlotin_party": r["Party(ies)"], "charlotin_court": r["Court"], "score": s})
res.sort(key=lambda x: -x["score"])
json.dump({"flag_rows": len(flag), "distinct_opinions": len(ops), "distinct_clusters": len(cl), "matched_by_cluster": len(in_db), "unmatched": len(cl - in_db), "unmatched_refuzzed": res}, open(OUT + "/flag_counts.json", "w"), indent=1)
for r in res: print(f"{r['score']:5.1f} | {r['cluster_date']} {r['cluster_name'][:55]:<55} | {r['charlotin_date']} {r['best_charlotin'][:50]} [{r['charlotin_party']}]")
