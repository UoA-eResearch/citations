"""Distribution of title Jaccard among candidate pairs and examples of rejected (jaccard < 0.5) pairs with titles."""
import gzip, json, random
import pandas as pd
from pathlib import Path
RUN = Path(__file__).resolve().parents[2]
c = pd.DataFrame([json.loads(l) for l in open(RUN / "data/pairs_candidates.jsonl")])
print("candidates", len(c), "confirmed", int(c.confirmed.sum()))
print("jaccard quantiles:", c.title_jaccard.quantile([.01, .05, .1, .25, .5]).round(3).tolist())
print("share in [0.3,0.5):", round(((c.title_jaccard >= 0.3) & (c.title_jaccard < 0.5)).mean(), 4), " share < 0.3:", round((c.title_jaccard < 0.3).mean(), 4))
rej = c[~c.confirmed]
print("rejected by server:", rej.server.value_counts().to_dict())
meta = {json.loads(l)["doi"]: json.loads(l) for l in open(RUN / "data/raw/links/published_crossref_meta.jsonl")}
random.seed(3); sample = rej.sample(14, random_state=3)
want = set(sample.preprint_doi)
titles = {}
for l in gzip.open(RUN / "data/parsed/preprints.jsonl.gz", "rt"):
    r = json.loads(l)
    if r.get("doi") in want: titles[r["doi"]] = r.get("title"); 
    if len(titles) == len(want): break
for _, r in sample.iterrows():
    print(f"\n[{r.title_jaccard}] {r.server} {r.preprint_doi}\n   PRE: {titles.get(r.preprint_doi)}\n   PUB: {meta.get(r.published_doi, {}).get('title')} ({r.published_journal})")
