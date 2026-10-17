"""For bioRxiv/medRxiv pairs: days from the preprint's posting (bioRxiv API preprint_date) to the journal publication
date (published_date), by version_used. A preprint posted at or after journal publication cannot predate peer review."""
import json
import pandas as pd
from pathlib import Path
RUN = Path(__file__).resolve().parents[2]
pairs = pd.DataFrame([json.loads(l) for l in open(RUN / "data/aligned/pairs.jsonl")])
pubs = {}
for l in open(RUN / "data/raw/links/pubs_biorxiv.jsonl"):
    r = json.loads(l)
    if r["preprint_doi"] and r["published_doi"]:
        pubs[(r["preprint_doi"].lower(), r["published_doi"].lower())] = r
pairs["key"] = list(zip(pairs.preprint_doi, pairs.published_doi))
pairs["pre_date"] = pairs.key.map(lambda k: (pubs.get(k) or {}).get("preprint_date"))
pairs["pub_date"] = pairs.key.map(lambda k: (pubs.get(k) or {}).get("published_date"))
d = pairs.dropna(subset=["pre_date", "pub_date"]).copy()
d["gap"] = (pd.to_datetime(d.pub_date, errors="coerce") - pd.to_datetime(d.pre_date, errors="coerce")).dt.days
d = d.dropna(subset=["gap"])
d["vu"] = d.version_used.map(lambda v: "1" if str(v) == "1" else ("unknown" if v is None or pd.isna(v) else "2+"))
print("pairs with both dates:", len(d), "of", len(pairs), "; by server", d.server.value_counts().to_dict())
for (srv, vu), g in d.groupby(["server", "vu"]):
    q = g.gap.quantile([.05, .25, .5, .75, .95]).round().astype(int).tolist()
    print(f"{srv:8s} {vu:8s} n={len(g):5d} gap days q05/25/50/75/95={q}  gap<=0: {(g.gap<=0).mean():.3f}  gap<=30: {(g.gap<=30).mean():.3f}  gap<=60: {(g.gap<=60).mean():.3f}")
v1 = d[d.vu == "1"]
print("\nv1 population (bioRxiv+medRxiv with dates): n", len(v1), " posted on/after publication:", int((v1.gap <= 0).sum()),
      f"({(v1.gap<=0).mean():.1%}); within 30 days before: {int(((v1.gap>0)&(v1.gap<=30)).sum())} ({((v1.gap>0)&(v1.gap<=30)).mean():.1%}); within 60: {((v1.gap<=60).mean()):.1%}")
# the pubs file also has the published_date for the all-versions pairs; show the share of v1 pairs with gap <= 0 by server
print(v1.groupby("server").gap.apply(lambda g: pd.Series(dict(n=len(g), le0=(g<=0).mean().round(3), le30=(g<=30).mean().round(3), median=g.median()))).unstack().to_string())
d[["preprint_doi", "published_doi", "server", "vu", "pre_date", "pub_date", "gap"]].to_csv(RUN / "review/reviewer_checks/cache/date_gap.csv", index=False)
