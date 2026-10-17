"""How many full fits silently dropped studies (largest component or non-finite contrasts)? Compare studies_used with the std file."""
import json, pandas as pd
RUN = "/mnt/citations/research-lab/runs/future-health-nma-rank-temporal-fragility"
nr = pd.read_csv(f"{RUN}/results/tables/network_results.csv", dtype={"record": str})
inc = set(nr[nr.included].record)
rows = []
for line in open(f"{RUN}/data/fits.jsonl"):
    r = json.loads(line); rec = r["record"]
    F = {f["name"]: f for f in r["fits"]}
    d = pd.read_csv(f"{RUN}/data/std/{rec}.csv", dtype={"study": str})
    allst = set(d.study.unique())
    trts = set(d.t.dropna().astype(int).astype(str)) if "t" in d else set(d.t1.astype(int).astype(str)) | set(d.t2.astype(int).astype(str))
    full = F.get("full", {})
    used = set(full.get("studies_used") or [])
    t10 = F.get("T10", {})
    rows.append(dict(record=rec, included=rec in inc, k_std=len(allst), k_full=full.get("n_studies"), n_used=len(used),
                     dropped_full=len(allst - used), trts_std=len(trts), trts_full=full.get("n_trts"),
                     trts_dropped=len(trts - set(full.get("trts") or [])),
                     t10_err=bool(t10.get("error")), t10_k=t10.get("n_studies"), t10_used=len(t10.get("studies_used") or []),
                     full_err=bool(full.get("error"))))
df = pd.DataFrame(rows)
df.to_csv(f"{RUN}/review/reviewer_checks/full_fit_coverage.csv", index=False)
x = df[df.included]
print("included:", len(x))
print("full fits with studies dropped (studies_used < std studies):", (x.dropped_full > 0).sum())
print(x[x.dropped_full > 0][["record", "k_std", "k_full", "n_used", "dropped_full", "trts_std", "trts_full", "trts_dropped"]].to_string())
print("full fits with treatments dropped:", (x.trts_dropped > 0).sum())
print(x[x.trts_dropped > 0][["record", "k_std", "n_used", "trts_std", "trts_full", "trts_dropped"]].to_string())
