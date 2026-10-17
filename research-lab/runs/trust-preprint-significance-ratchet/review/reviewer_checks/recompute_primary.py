"""Recompute the primary: the exact-tuple crossings in the v1 population, their paper bootstrap (same seed as
analysis.py), exact interval, and the all-crossings estimate. Also version/population tabulations."""
import gzip, json, sys
import numpy as np, pandas as pd
from scipy import stats as st
from pathlib import Path
RUN = Path(__file__).resolve().parents[2]
AL = RUN / "data" / "aligned"
pairs = pd.DataFrame([json.loads(l) for l in open(AL / "pairs.jsonl")])
print("pairs", len(pairs), "distinct published DOIs", pairs.published_doi.nunique())
pairs["vu"] = pairs.version_used.astype(str)
print("\nversion_used by server:\n", pd.crosstab(pairs.server.fillna("None"), pairs.vu).to_string())
v1 = set(pairs[pairs.vu == "1"].preprint_doi)
print("\nn v1 pairs", len(v1), "distinct published among v1", pairs[pairs.vu == "1"].published_doi.nunique())
print("v1 by server", pairs[pairs.vu == "1"].server.value_counts().to_dict())
rows = [json.loads(l) for l in gzip.open(AL / "statistics.jsonl.gz", "rt")]
cr = [r for r in rows if r["status"] == "aligned" and r["cls"] in ("crossing_up", "crossing_down")]
print("\nall crossings all versions", len(cr), "up", sum(r["cls"] == "crossing_up" for r in cr))
cr1 = [r for r in cr if r["pair"] in v1]
print("v1 crossings", len(cr1), "papers", len({r['pair'] for r in cr1}), "up", sum(r["cls"] == "crossing_up" for r in cr1))
ex = [r for r in cr1 if r["how"] == "exact"]
print("\n=== exact tuple crossings in v1:", len(ex))
for r in ex:
    print(json.dumps(dict(pair=r["pair"], cls=r["cls"], pre=r["pre"], pub=r["pub"]), ensure_ascii=False, indent=1))

def boot(df, seed=20261017, nboot=2000):
    g = df.groupby("pair").up.agg(["sum", "count"]); s, n = g["sum"].to_numpy(), g["count"].to_numpy()
    idx = np.random.default_rng(seed).integers(0, len(g), size=(nboot, len(g)))
    v = s[idx].sum(1) / n[idx].sum(1)
    return s.sum() / n.sum(), np.percentile(v, 2.5), np.percentile(v, 97.5), len(g)

def clopper(k, n):
    lo = 0.0 if k == 0 else st.beta.ppf(0.025, k, n - k + 1); hi = 1.0 if k == n else st.beta.ppf(0.975, k + 1, n - k)
    return lo, hi
dfx = pd.DataFrame(dict(pair=[r["pair"] for r in ex], up=[r["cls"] == "crossing_up" for r in ex]))
print("\nexact v1: share, boot lo, hi, n_papers:", boot(dfx), "clopper", clopper(int(dfx.up.sum()), len(dfx)))
dfa = pd.DataFrame(dict(pair=[r["pair"] for r in cr1], up=[r["cls"] == "crossing_up" for r in cr1]))
print("all crossings v1:", boot(dfa))
dfall = pd.DataFrame(dict(pair=[r["pair"] for r in cr], up=[r["cls"] == "crossing_up" for r in cr]))
print("all crossings all versions:", boot(dfall))
# exact tuple crossings over all versions (D2.5 tally said 8 up / 5 down)
exa = [r for r in cr if r["how"] == "exact"]
print("exact all versions:", len(exa), "up", sum(r["cls"] == "crossing_up" for r in exa))
# v1-sample verified crossings: which are in the v1 population?
k1 = pd.read_csv(RUN / "results/tables/alignment_validation.csv")
ok = k1[(k1.stratum == "crossing") & (k1.correct == 1)]
vu = pairs.set_index("preprint_doi").vu.to_dict()
print("\nv1-sample correct crossings, version_used:", [(i, vu.get(p)) for i, p in zip(ok.id, ok.pair)])
# the v1 validation sample's population
print("v1 sample strata by version_used:\n", pd.crosstab(k1.stratum, k1.pair.map(vu).fillna("None")).to_string())
