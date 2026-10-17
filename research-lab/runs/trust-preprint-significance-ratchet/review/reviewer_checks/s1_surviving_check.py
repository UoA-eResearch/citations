"""Confirmation check of D5's post hoc S1 (statistics removed from / added to a sentence that survived): how much of
each pool sits in glued or over-long 'sentences' (flattened table/caption text), the sig share by section, and the
difference without such sentences. Also prints raw examples."""
import gzip, json, random, re
import numpy as np, pandas as pd
from pathlib import Path
RUN = Path(__file__).resolve().parents[2]
GLUE = re.compile(r"[a-z0-9\)%][.!?][A-Z]")
pairs = pd.DataFrame([json.loads(l) for l in open(RUN / "data/aligned/pairs.jsonl")])
v1 = set(pairs[pairs.version_used.astype(str) == "1"].preprint_doi)
rows = [json.loads(l) for l in gzip.open(RUN / "data/aligned/statistics.jsonl.gz", "rt")]
rv1 = [r for r in rows if r["pair"] in v1]
keep = {}
for r in rv1:
    if r["status"] == "aligned":
        keep.setdefault(r["pair"], [set(), set()]); keep[r["pair"]][0].add(r["pre"]["sentence"]); keep[r["pair"]][1].add(r["pub"]["sentence"])
S = []
for r in rv1:
    if r["status"] == "dropped" and r["pre"]["sig"] is not None and r["pre"]["sentence"] in keep.get(r["pair"], [set(), set()])[0]:
        x = r["pre"]; S.append(dict(pair=r["pair"], status="dropped", sig=x["sig"], section=x["section"], L=len(x["sentence"]), glued=bool(GLUE.search(x["sentence"])), p=x["p"], sent=x["sentence"]))
    if r["status"] == "added" and r["pub"]["sig"] is not None and r["pub"]["sentence"] in keep.get(r["pair"], [set(), set()])[1]:
        x = r["pub"]; S.append(dict(pair=r["pair"], status="added", sig=x["sig"], section=x["section"], L=len(x["sentence"]), glued=bool(GLUE.search(x["sentence"])), p=x["p"], sent=x["sentence"]))
d = pd.DataFrame(S)
print("pools:", d.status.value_counts().to_dict(), " sig share:", d.groupby("status").sig.mean().round(4).to_dict())
d["long_or_glued"] = (d.L > 600) | d.glued
print("\nshare in long (>600) or glued sentences:", d.groupby("status").long_or_glued.mean().round(3).to_dict())
print("by section (n, sig share):"); print(d.groupby(["status", "section"]).sig.agg(["count", "mean"]).round(3).to_string())
print("\nsig share by status x long_or_glued:"); print(d.groupby(["status", "long_or_glued"]).sig.agg(["count", "mean"]).round(3).to_string())
print("p == 0 or 1 exactly:", d.groupby("status").p.apply(lambda s: ((s == 0) | (s == 1)).mean().round(4)).to_dict())
def boot(dd, seed=20261017):
    g = dd.groupby(["pair", "status"]).sig.agg(["sum", "count"]).unstack(fill_value=0)
    for col in ("added", "dropped"):
        for k in ("sum", "count"):
            if (k, col) not in g.columns: g[(k, col)] = 0
    sa, na, sd, nd = (g[("sum", "added")].to_numpy(), g[("count", "added")].to_numpy(), g[("sum", "dropped")].to_numpy(), g[("count", "dropped")].to_numpy())
    idx = np.random.default_rng(seed).integers(0, len(g), size=(2000, len(g)))
    diff = sa[idx].sum(1) / np.maximum(na[idx].sum(1), 1) - sd[idx].sum(1) / np.maximum(nd[idx].sum(1), 1)
    return round(sa.sum() / na.sum() - sd.sum() / nd.sum(), 4), np.percentile(diff, [2.5, 97.5]).round(4).tolist(), int(nd.sum()), int(na.sum()), len(g)
print("\nall (reproduces D5):", boot(d))
print("without long/glued sentences:", boot(d[~d.long_or_glued]))
print("text sections (abstract, result) only, without long/glued:", boot(d[~d.long_or_glued & d.section.isin(["abstract", "result"])]))
print("sentences with <= 3 statistics on the side in question are not identifiable here; instead: short sentences (<= 300 chars):", boot(d[d.L <= 300]))
random.seed(5)
for st in ("dropped", "added"):
    print(f"\n=== 10 random {st} (short sentences only), with the aligned counterpart sentence")
    sub = d[(d.status == st) & (d.L <= 300)].sample(10, random_state=5)
    for _, x in sub.iterrows():
        # find the counterpart sentence via an aligned row sharing this sentence
        cp = next((r for r in rv1 if r["status"] == "aligned" and r["pair"] == x.pair and r["pre" if st == "dropped" else "pub"]["sentence"] == x.sent), None)
        other = cp["pub" if st == "dropped" else "pre"]["sentence"] if cp else None
        print(f"- [{st} p={x.p} sig={x.sig} sec={x.section}] {x.sent[:230]}\n    counterpart: {str(other)[:230]}")
