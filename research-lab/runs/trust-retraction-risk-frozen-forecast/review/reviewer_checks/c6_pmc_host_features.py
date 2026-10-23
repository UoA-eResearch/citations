"""Reviewer check 6: which venue-block values single out the PubMed-Central-hosted (host I1299303238, NIH) test articles."""
import glob, json
import numpy as np, pandas as pd, pyarrow.parquet as pq
RUN = "/mnt/citations/research-lab/runs/trust-retraction-risk-frozen-forecast"; MYST = 1299303238
parts = []
for f in sorted(glob.glob(RUN + "/data/features/*.parquet")):
    t = pq.read_table(f, columns=["year", "src", "host", "stype", "oa", "src_rate", "host_rate", "src_growth", "ret", "n_refs"]).to_pandas()
    parts.append(t[t.year.between(2021, 2022)])
d = pd.concat(parts, ignore_index=True); m = (d.host == MYST).to_numpy()
def desc(x): return {"mean": round(float(x.mean()), 5), "median": round(float(x.median()), 5), "p90": round(float(x.quantile(0.9)), 5)}
out = {"pmc_host_articles": int(m.sum()), "pmc_host_sources": {str(int(k)): int(v) for k, v in d.src[m].value_counts().head(3).items()},
       "pmc_host_stype_counts": {str(int(k)): int(v) for k, v in d.stype[m].value_counts().items()},
       "cohort_stype_counts": {str(int(k)): int(v) for k, v in d.stype.value_counts().items()},
       "pmc_host": {c: desc(d[c][m]) for c in ("src_rate", "host_rate", "src_growth", "oa", "n_refs")},
       "rest_of_cohort": {c: desc(d[c][~m]) for c in ("src_rate", "host_rate", "src_growth", "oa", "n_refs")},
       "pmc_host_retracted": int((d.ret[m] > 0).sum()), "pmc_host_by_year": {str(int(k)): int(v) for k, v in d.year[m].value_counts().items()}}
r = pd.read_parquet(RUN + "/data/lookup/rates.parquet")
out["rates_rows_host_1299303238"] = r[(r.k == "H") & (r.e == MYST)].round(6).to_dict("records")
src_ids = list(d.src[m].value_counts().head(2).index)
out["rates_rows_top_pmc_sources"] = r[(r.k == "S") & (r.e.isin(src_ids)) & (r.Y.isin([2021, 2022]))].round(6).to_dict("records")
# repository-type articles overall: how many are in the cohort and their retraction rate
rep = (d.stype == 2).to_numpy()
out["repository_type_articles"] = {"n": int(rep.sum()), "retracted": int((d.ret[rep] > 0).sum()), "share_pmc_host": round(float(m[rep].mean()), 4)}
out = json.loads(json.dumps(out, default=lambda o: int(o) if hasattr(o, "__int__") else str(o)))
print(json.dumps(out, indent=1)); json.dump(out, open(RUN + "/review/reviewer_checks/c6_pmc_host_features.json", "w"), indent=1)
