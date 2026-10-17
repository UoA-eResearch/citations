"""Posting dates for a seeded sample of version-1 Research Square and medRxiv preprints (Crossref 'posted'), against
the journal article's Crossref 'issued' date. Cached in cache/crossref_dates.jsonl."""
import json, random, time, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pandas as pd, requests
RUN = Path(__file__).resolve().parents[2]
CACHE = RUN / "review/reviewer_checks/cache/crossref_dates.jsonl"
pairs = pd.DataFrame([json.loads(l) for l in open(RUN / "data/aligned/pairs.jsonl")])
v1 = pairs[pairs.version_used.astype(str) == "1"]
rnd = random.Random(7)
sample = rnd.sample(list(v1[v1.server == "Res Sq"].preprint_doi), 150) + rnd.sample(list(v1[v1.server == "medRxiv"].preprint_doi), 150)
have = {}
if CACHE.exists():
    have = {json.loads(l)["doi"]: json.loads(l) for l in open(CACHE)}
UA = {"User-Agent": "independent review of a research-lab study (mailto:noreply@anthropic.com)"}
def posted(doi):
    for k in range(4):
        try:
            r = requests.get(f"https://api.crossref.org/works/{doi}?mailto=noreply@anthropic.com", headers=UA, timeout=60)
            if r.status_code == 404: return dict(doi=doi, posted=None, status=404)
            m = r.json()["message"]
            d = (m.get("posted") or m.get("issued") or {}).get("date-parts", [[None]])[0]
            return dict(doi=doi, posted="-".join(f"{x:02d}" if i else str(x) for i, x in enumerate(d)) if d and d[0] else None, type=m.get("type"), status=200)
        except Exception as e:
            time.sleep(2 ** k)
    return dict(doi=doi, posted=None, status="error")
todo = [d for d in sample if d not in have]
with open(CACHE, "a") as fh, ThreadPoolExecutor(4) as ex:
    for r in ex.map(posted, todo):
        fh.write(json.dumps(r) + "\n"); have[r["doi"]] = r
meta = {json.loads(l)["doi"]: json.loads(l) for l in open(RUN / "data/raw/links/published_crossref_meta.jsonl")}
rows = []
for d in sample:
    p = pairs[pairs.preprint_doi == d].iloc[0]
    iss = (meta.get(p.published_doi) or {}).get("issued") or {}
    dp = iss.get("date-parts", [[None]])[0]
    pub = "-".join(f"{x:02d}" if i else str(x) for i, x in enumerate(dp)) if dp and dp[0] else None
    rows.append(dict(preprint_doi=d, server=p.server, posted=have[d].get("posted"), published=pub, journal=p.published_journal))
df = pd.DataFrame(rows)
df["gap"] = (pd.to_datetime(df.published, errors="coerce") - pd.to_datetime(df.posted, errors="coerce")).dt.days
df.to_csv(RUN / "review/reviewer_checks/cache/crossref_dates_sample.csv", index=False)
ok = df.dropna(subset=["gap"])
print("sample", len(df), "with both dates", len(ok))
for s, g in ok.groupby("server"):
    print(f"{s}: n={len(g)} gap days q05/25/50/75/95={g.gap.quantile([.05,.25,.5,.75,.95]).round().astype(int).tolist()} gap<=0: {(g.gap<=0).sum()} ({(g.gap<=0).mean():.1%}) gap<=30: {(g.gap<=30).sum()} ({(g.gap<=30).mean():.1%}) gap<=60: {(g.gap<=60).mean():.1%}")
print(ok[ok.gap <= 30].sort_values("gap")[["preprint_doi", "server", "posted", "published", "journal", "gap"]].to_string())
