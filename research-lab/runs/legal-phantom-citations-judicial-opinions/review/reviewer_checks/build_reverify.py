"""Reviewer check 1: assemble the rows to re-verify. All rows labelled anything other than 'real', plus a seeded
random sample of 12 'real' rows from each of the four sheets (48), joined to the sheet row and the reading aid."""
import csv, json, random
RUN = "/mnt/citations/research-lab/runs/legal-phantom-citations-judicial-opinions"
S = RUN + "/data/screen"; OUT = RUN + "/review/reviewer_checks"
rng = random.Random(20261022)
rows = []
for sh in ("screened_reliance", "screened_flag", "placebo_reliance", "placebo_flag"):
    sheet = list(csv.DictReader(open(f"{S}/verify_{sh}.csv")))
    aid = {a["k"]: a for a in (json.loads(l) for l in open(f"{S}/aid_verify_{sh}.jsonl"))}
    labels = {int(r["k"]): r for r in csv.DictReader(open(f"{S}/labels/{sh}.csv"))}
    assert len(sheet) == len(aid), (sh, len(sheet), len(aid))
    nonreal = [k for k, r in labels.items() if r["verdict"] != "real"]
    real_idx = [k for k in range(len(sheet)) if labels.get(k, {}).get("verdict", "real") == "real"]
    noted_real = [k for k in real_idx if k in labels]
    unnoted_real = [k for k in real_idx if k not in labels]
    pick = sorted(rng.sample(unnoted_real, 9) + rng.sample(noted_real, min(3, len(noted_real))))
    for k in sorted(set(nonreal + pick)):
        r = sheet[k]; a = aid[k]; lab = labels.get(k, {"verdict": "real(default)", "note": ""})
        rows.append({"sheet": sh, "k": k, "opinion_id": r["opinion_id"], "cluster_id": r["cluster_id"], "date": r["date"],
                     "cite": r["cite"], "cited_name": r["cited_name"], "best_name": r["best_name"], "score": r["best_name_score"],
                     "label": lab["verdict"], "note": lab.get("note", ""), "near": json.dumps(a["near"]), "snippet": a["snippet"],
                     "context": " ".join(r["context"].split())})
with open(OUT + "/reverify_rows.tsv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter="\t"); w.writeheader(); w.writerows(rows)
from collections import Counter
print(len(rows), Counter((r["sheet"], r["label"]) for r in rows))
