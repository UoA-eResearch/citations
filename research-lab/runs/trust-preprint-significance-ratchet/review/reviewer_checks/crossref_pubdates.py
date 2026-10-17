"""Journal publication dates (Crossref published-online / published-print / created) for the 300 sampled pairs, and
the gap from preprint posting. Cached in cache/crossref_pubdates.jsonl."""
import json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pandas as pd, requests
RUN = Path(__file__).resolve().parents[2]; C = RUN / "review/reviewer_checks/cache"
s = pd.read_csv(C / "crossref_dates_sample.csv")
pairs = pd.DataFrame([json.loads(l) for l in open(RUN / "data/aligned/pairs.jsonl")]).set_index("preprint_doi")
s["published_doi"] = s.preprint_doi.map(pairs.published_doi)
have = {json.loads(l)["doi"]: json.loads(l) for l in open(C / "crossref_pubdates.jsonl")} if (C / "crossref_pubdates.jsonl").exists() else {}
UA = {"User-Agent": "independent review of a research-lab study (mailto:noreply@anthropic.com)"}
def fmt(dp):
    return "-".join(f"{x:02d}" if i else str(x) for i, x in enumerate(dp)) if dp and dp[0] else None
def get(doi):
    for k in range(4):
        try:
            r = requests.get(f"https://api.crossref.org/works/{doi}?mailto=noreply@anthropic.com", headers=UA, timeout=60)
            if r.status_code == 404: return dict(doi=doi, status=404)
            m = r.json()["message"]
            out = dict(doi=doi, status=200)
            for key in ("published-online", "published-print", "published", "issued", "created"):
                dp = ((m.get(key) or {}).get("date-parts") or [[None]])[0]
                out[key] = fmt(dp) if dp and len(dp) >= 3 else (fmt(dp) if dp and dp[0] else None)
            out["type"] = m.get("type"); return out
        except Exception:
            time.sleep(2 ** k)
    return dict(doi=doi, status="error")
todo = [d for d in s.published_doi.dropna().unique() if d not in have]
with open(C / "crossref_pubdates.jsonl", "a") as fh, ThreadPoolExecutor(4) as ex:
    for r in ex.map(get, todo):
        fh.write(json.dumps(r) + "\n"); have[r["doi"]] = r
def pubdate(d):
    r = have.get(d) or {}
    for key in ("published-online", "published-print", "published", "created"):
        v = r.get(key)
        if v and len(v) == 10: return v
    return None
s["pub_full"] = s.published_doi.map(pubdate)
s["gap"] = (pd.to_datetime(s.pub_full, errors="coerce") - pd.to_datetime(s.posted, errors="coerce")).dt.days
s.to_csv(C / "crossref_dates_sample.csv", index=False)
ok = s.dropna(subset=["gap"])
print("sample", len(s), "with both full dates", len(ok))
for srv, g in ok.groupby("server"):
    print(f"{srv:8s} n={len(g):3d} gap days q05/25/50/75/95={g.gap.quantile([.05,.25,.5,.75,.95]).round().astype(int).tolist()}  gap<=0: {(g.gap<=0).sum()} ({(g.gap<=0).mean():.1%})  gap<=30: {(g.gap<=30).sum()} ({(g.gap<=30).mean():.1%})  gap<=60: {(g.gap<=60).sum()} ({(g.gap<=60).mean():.1%})")
print(ok[ok.gap <= 30].sort_values("gap")[["preprint_doi", "server", "posted", "pub_full", "journal", "gap"]].to_string(index=False))
