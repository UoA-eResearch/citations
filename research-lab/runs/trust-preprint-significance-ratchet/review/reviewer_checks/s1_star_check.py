"""Share of the post hoc S1 pools (statistics removed from / added to surviving sentences) that are significance-star
legends, and the difference without them and without figure/table sections. Also: one-tailed-explicable decision
inconsistencies among the 29."""
import gzip, json, re, sys
import numpy as np, pandas as pd
from pathlib import Path
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
from analysis_v2 import STAR
from analysis import consistent, recompute_p
GLUE = re.compile(r"[a-z0-9\)%][.!?][A-Z]")
STAR2 = re.compile(r"\*+\s*[:=,]?\s*[pP]\s*(?:<=|≤|<|>|≥|>=|=)|[pP]\s*(?:<=|≤|<)\s*0?\.\d+\s*[:=]?\s*\(?\*|\bns\b.*[pP]\s*[<>]|not significant.*\*")
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
    for st, side, k in (("dropped", "pre", 0), ("added", "pub", 1)):
        if r["status"] == st and r[side]["sig"] is not None and r[side]["sentence"] in keep.get(r["pair"], [set(), set()])[k]:
            x = r[side]; s = x["sentence"]
            S.append(dict(pair=r["pair"], status=st, sig=x["sig"], section=x["section"], star=bool(STAR.search(s) or STAR2.search(s)),
                          longglued=(len(s) > 600) or bool(GLUE.search(s)), cmp=x["cmp"], p=x["p"]))
d = pd.DataFrame(S)
print("star-legend share:", d.groupby("status").star.mean().round(3).to_dict(), " n star:", d.groupby("status").star.sum().to_dict())
print("sig share, star vs not:"); print(d.groupby(["status", "star"]).sig.agg(["count", "mean"]).round(3).to_string())
print("comparator mix (added):", d[d.status == "added"].cmp.value_counts().to_dict(), " (dropped):", d[d.status == "dropped"].cmp.value_counts().to_dict())
def boot(dd, seed=20261017):
    g = dd.groupby(["pair", "status"]).sig.agg(["sum", "count"]).unstack(fill_value=0)
    for col in ("added", "dropped"):
        for k in ("sum", "count"):
            if (k, col) not in g.columns: g[(k, col)] = 0
    sa, na, sd, nd = (g[("sum", "added")].to_numpy(), g[("count", "added")].to_numpy(), g[("sum", "dropped")].to_numpy(), g[("count", "dropped")].to_numpy())
    idx = np.random.default_rng(seed).integers(0, len(g), size=(2000, len(g)))
    diff = sa[idx].sum(1) / np.maximum(na[idx].sum(1), 1) - sd[idx].sum(1) / np.maximum(nd[idx].sum(1), 1)
    return dict(diff=round(float(sa.sum() / na.sum() - sd.sum() / nd.sum()), 4), ci=np.percentile(diff, [2.5, 97.5]).round(4).tolist(), n_dropped=int(nd.sum()), n_added=int(na.sum()),
                sig_dropped=round(float(sd.sum() / nd.sum()), 3), sig_added=round(float(sa.sum() / na.sum()), 3), papers=len(g))
print("\nD5 as reported:", boot(d))
print("without star legends:", boot(d[~d.star]))
print("without star legends and without long/glued:", boot(d[~d.star & ~d.longglued]))
print("text sections only (abstract, result), without star legends and long/glued:", boot(d[~d.star & ~d.longglued & d.section.isin(["abstract", "result"])]))
print("equalities only ('p = x'), text sections, without star/long/glued:", boot(d[~d.star & ~d.longglued & d.section.isin(["abstract", "result"]) & (d.cmp == "=")]))
# decision inconsistencies: one-tailed explicable
tup = [r for r in rv1 if r["status"] == "aligned" and r["pre"]["kind"] == "tuple" and r["pub"]["kind"] == "tuple"]
def dec(x):
    p2 = recompute_p(x["test"], x["df"], abs(x["stat"])); return p2 is not None and x["sig"] is not None and ((p2 < 0.05) != x["sig"])
def one_tail(x):
    p2 = recompute_p(x["test"], x["df"], abs(x["stat"])); return p2 is not None and x["cmp"] == "=" and abs(x["p"] - p2 / 2) <= max(0.005, 0.1 * p2)
bad = [r for r in tup if consistent(r["pre"]) is False]
di = [r for r in bad if dec(r["pre"])]
print("\ndecision inconsistencies:", len(di), " one-tailed explicable:", sum(one_tail(r["pre"]) for r in di), " verbatim unchanged:", sum(1 for r in di if r["pre"]["p"] == r["pub"]["p"] and r["pre"]["stat"] == r["pub"]["stat"]))
for r in di[:29]:
    x = r["pre"]; print(f"   {x['test']}({x['df']})={x['stat']} {x['cmp']} {x['p']} recomputed={recompute_p(x['test'], x['df'], abs(x['stat'])):.4g} one_tailed={one_tail(x)} pub_p={r['pub']['p']}")
