"""S1 (dropped vs added) and S2 (statcheck consistency) recomputed in the v1 population from data/aligned/, with
breakdowns the report does not give: S1 by section; S2 by match type, identical-p share, test type, and the
one-tailed question."""
import gzip, json, sys
from collections import Counter
import numpy as np, pandas as pd
from pathlib import Path
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
from analysis import consistent, recompute_p
pairs = pd.DataFrame([json.loads(l) for l in open(RUN / "data/aligned/pairs.jsonl")])
v1 = set(pairs[pairs.version_used.astype(str) == "1"].preprint_doi)
rows = [json.loads(l) for l in gzip.open(RUN / "data/aligned/statistics.jsonl.gz", "rt") ]
rv1 = [r for r in rows if r["pair"] in v1]
print("v1 rows", len(rv1), Counter(r["status"] for r in rv1))
# ---- S1
S = []
for r in rv1:
    if r["status"] in ("dropped", "added"):
        x = r["pre"] if r["status"] == "dropped" else r["pub"]
        S.append((r["pair"], r["status"], x["section"], x["kind"], x["sig"], x["p"]))
s1 = pd.DataFrame(S, columns=["pair", "status", "section", "kind", "sig", "p"])
det = s1.dropna(subset=["sig"])
print("\nS1 share significant (determined only):")
print(det.groupby("status").sig.agg(["mean", "count"]).to_string())
print("\nby section:")
print(det.groupby(["section", "status"]).sig.agg(["mean", "count"]).unstack().to_string())
print("\nshare of determined dropped/added that are in tables:", det.groupby("status").section.apply(lambda s: (s == "table").mean().round(3)).to_dict())
print("share with p == 1.0 exactly (index-variable artefacts like 'p = 1, ..., P'):", det.groupby("status").p.apply(lambda s: (s == 1.0).mean().round(4)).to_dict())
# paper bootstrap of the difference, as supplementary.py does
g = det.groupby(["pair", "status"]).sig.agg(["sum", "count"]).unstack(fill_value=0)
sa, na, sd, nd = (g[("sum", "added")].to_numpy(), g[("count", "added")].to_numpy(), g[("sum", "dropped")].to_numpy(), g[("count", "dropped")].to_numpy())
idx = np.random.default_rng(20261017).integers(0, len(g), size=(2000, len(g)))
diff = sa[idx].sum(1) / na[idx].sum(1) - sd[idx].sum(1) / nd[idx].sum(1)
print("S1 diff (added - dropped)", sa.sum() / na.sum() - sd.sum() / nd.sum(), "CI", np.percentile(diff, [2.5, 97.5]), "papers", len(g))
# text only
t = det[det.section.isin(["abstract", "result"])]
print("S1 text-only:", t.groupby("status").sig.agg(["mean", "count"]).to_dict())
# ---- S2
tup = [r for r in rv1 if r["status"] == "aligned" and r["pre"]["kind"] == "tuple" and r["pub"]["kind"] == "tuple"]
print("\nS2 aligned tuple pairs", len(tup), "by how", Counter(r["how"] for r in tup))
same_p = sum(1 for r in tup if r["pre"]["p"] == r["pub"]["p"] and r["pre"]["cmp"] == r["pub"]["cmp"])
print(" pairs with identical p and comparator:", same_p)
inc = [(consistent(r["pre"]), consistent(r["pub"]), r) for r in tup]
print(" consistent() None (not evaluable) pre:", sum(a is None for a, _, _ in inc), "of", len(inc))
pre_bad = [(a, b, r) for a, b, r in inc if a is False]
print(" preprint inconsistent", len(pre_bad), " published inconsistent", sum(b is False for _, b, _ in inc), " repaired", sum(b is True for _, b, _ in pre_bad))
print(" among preprint-inconsistent: identical tuple text (stat & p unchanged):", sum(1 for a, b, r in pre_bad if r["pre"]["p"] == r["pub"]["p"] and r["pre"]["stat"] == r["pub"]["stat"]))
print(" by test:", Counter(r["pre"]["test"] for _, _, r in pre_bad))
print(" by how:", Counter(r["how"] for _, _, r in pre_bad))
# how many inconsistencies vanish if a one-tailed p is allowed (reported p ~ half the two-tailed)?
def one_tailed_ok(x):
    p2 = recompute_p(x["test"], x["df"], abs(x["stat"]))
    return p2 is not None and x["cmp"] == "=" and abs(x["p"] - p2 / 2) <= max(0.005, 0.1 * p2)
print(" preprint-inconsistent explained by a one-tailed p:", sum(one_tailed_ok(r["pre"]) for _, _, r in pre_bad))
# decision inconsistencies (reported significance differs from recomputed)
def dec(x):
    p2 = recompute_p(x["test"], x["df"], abs(x["stat"]))
    return p2 is not None and x["sig"] is not None and ((p2 < 0.05) != x["sig"])
print(" preprint decision inconsistencies:", sum(dec(r["pre"]) for _, _, r in pre_bad), " of which repaired:", sum(dec(r["pre"]) and b is True for _, b, r in pre_bad))
print("\n first 25 preprint-inconsistent tuples (test df stat cmp p -> recomputed | published):")
for a, b, r in pre_bad[:25]:
    x, y = r["pre"], r["pub"]
    print(f"  {x['test']}({x['df']})={x['stat']} {x['cmp']} {x['p']}  recomputed={recompute_p(x['test'], x['df'], abs(x['stat']))}  | pub {y['test']}({y['df']})={y['stat']} {y['cmp']} {y['p']} cons={b} how={r['how']}")
# full S2 table for the review
pd.DataFrame([dict(pair=r["pair"], how=r["how"], test=r["pre"]["test"], df=r["pre"]["df"], stat=r["pre"]["stat"], cmp=r["pre"]["cmp"], p=r["pre"]["p"],
                   recomputed=recompute_p(r["pre"]["test"], r["pre"]["df"], abs(r["pre"]["stat"])), pub_stat=r["pub"]["stat"], pub_cmp=r["pub"]["cmp"], pub_p=r["pub"]["p"],
                   pub_consistent=b, one_tailed=one_tailed_ok(r["pre"]), sentence=r["pre"]["sentence"][:200]) for a, b, r in pre_bad]).to_csv(RUN / "review/reviewer_checks/cache/s2_inconsistent.csv", index=False)
