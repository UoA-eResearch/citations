"""Independent re-fetch of posting and publication dates for the 28 census papers (D5 R17)."""
import json, time
import pandas as pd, requests
from pathlib import Path
RUN = Path(__file__).resolve().parents[2]; C = RUN / "review/reviewer_checks/cache"
cod = pd.read_csv(RUN / "results/tables/verified_coding.csv")
vc = pd.read_csv(RUN / "results/tables/verified_crossings.csv")
k2 = pd.read_csv(RUN / "results/tables/alignment_validation_v2.csv").set_index("id")
ids = [i for i in cod.id if i.startswith("w") and cod.set_index("id").code[i].startswith("changed")]
papers = sorted({k2.pair[i] for i in ids})
pairs = pd.DataFrame([json.loads(l) for l in open(RUN / "data/aligned/pairs.jsonl")]).set_index("preprint_doi")
UA = {"User-Agent": "independent review (mailto:noreply@anthropic.com)"}
cache = C / "census_gaps.jsonl"; have = {json.loads(l)["doi"]: json.loads(l) for l in open(cache)} if cache.exists() else {}
def fmt(dp): return "-".join(f"{x:02d}" if i else str(x) for i, x in enumerate(dp)) if dp and dp[0] else None
def get(doi):
    if doi in have: return have[doi]
    for k in range(4):
        try:
            m = requests.get(f"https://api.crossref.org/works/{doi}?mailto=noreply@anthropic.com", headers=UA, timeout=60).json()["message"]
            r = dict(doi=doi, **{key: fmt(((m.get(key) or {}).get("date-parts") or [[None]])[0]) for key in ("posted", "created", "published-online", "published-print", "published", "issued")})
            with open(cache, "a") as fh: fh.write(json.dumps(r) + "\n")
            have[doi] = r; return r
        except Exception: time.sleep(2 ** k)
    return dict(doi=doi)
rows = []
for d in papers:
    a, b = get(d), get(pairs.published_doi[d]); time.sleep(0.2)
    pre = a.get("posted") or a.get("created")
    pub = next((b.get(k) for k in ("published-online", "published-print", "published", "created") if b.get(k) and len(b[k]) == 10), None)
    gap = (pd.Timestamp(pub) - pd.Timestamp(pre)).days if pre and pub else None
    rows.append(dict(preprint=d, posted=pre, published=pub, gap=gap))
df = pd.DataFrame(rows); print(df.to_string(index=False))
print("\nn", len(df), "known", df.gap.notna().sum(), "gap<=30:", int((df.gap <= 30).sum()), "negative:", int((df.gap < 0).sum()), "min gap", df.gap.min())
