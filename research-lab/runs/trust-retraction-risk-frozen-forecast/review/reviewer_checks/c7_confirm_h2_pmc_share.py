"""Confirmation check 7: share of the frozen H2 (no_A) top 1% hosted by I1299303238 (PubMed Central), which the
report's host table gives as 0.1% but posthoc_review.json's eight-host H2 list does not contain. Also the full
model's Hindawi and no-host shares, shown as dashes in the report."""
import glob, json, pickle
import numpy as np, pandas as pd, pyarrow.parquet as pq
RUN = "/mnt/citations/research-lab/runs/trust-retraction-risk-frozen-forecast"
hashes = json.load(open(RUN + "/results/tables/model_hashes.json")); fmap = {int(k): v for k, v in hashes["field_codes"].items()}
b = pickle.load(open(RUN + "/data/models/hgb_no_A.pkl", "rb")); cols = b["cols"]
need = sorted(set(cols + ["year", "host", "field"]) - {"field_c"})
parts = []
for f in sorted(glob.glob(RUN + "/data/features/*.parquet")):
    t = pq.read_table(f, columns=need).to_pandas(); parts.append(t[t.year.between(2021, 2022)])
d = pd.concat(parts, ignore_index=True); del parts
d["field_c"] = d.field.map(fmap).fillna(0).astype(int)
s = b["model"].predict_proba(d[cols])[:, 1]
n1 = max(1, int(round(0.01 * len(s)))); top = np.zeros(len(s), bool); top[np.argsort(-s, kind="stable")[:n1]] = True
h = d.host.to_numpy()
out = {"test_rows": int(len(d)), "top1_n": n1, "h2_top1_share_pmc_host": round(float((h[top] == 1299303238).mean()), 4),
       "h2_top1_count_pmc_host": int((h[top] == 1299303238).sum())}
a = json.load(open(RUN + "/results/tables/h1_h2.json"))["bias_audit"]["host"]
out["full_top1_share_hindawi_from_h1_h2"] = a["4310319869"]["top1_share"]; out["full_top1_share_no_host_from_h1_h2"] = a["0"]["top1_share"]
print(json.dumps(out, indent=1)); json.dump(out, open(RUN + "/review/reviewer_checks/c7_confirm_h2_pmc_share.json", "w"), indent=1)
