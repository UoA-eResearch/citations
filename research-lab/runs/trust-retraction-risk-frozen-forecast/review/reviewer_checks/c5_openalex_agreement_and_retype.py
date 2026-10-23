"""Reviewer check 5: (a) OpenAlex is_retracted (registry layer fetched 2026-10-21) against the study labels and the test
cohort (the plan promised this check; the report omits it); (b) whether retracted works are typed 'article' at the same
rate as other works, by retraction year (re-typing after retraction would drop them from the cohort)."""
import glob, json, re, time
import numpy as np, pandas as pd, pyarrow.parquet as pq
RUN = "/mnt/citations/research-lab/runs/trust-retraction-risk-frozen-forecast"; SRC = "/mnt/data/retraction-markers/raw"
out = {}; t0 = time.time()
def ndoi(x):
    if not isinstance(x, str): return None
    x = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", x.strip().lower())
    return x if x.startswith("10.") else None
oa = [json.loads(l) for l in open(SRC + "/openalex_retracted.jsonl")]
oa_doi = {ndoi(o.get("doi")) for o in oa} - {None}
oa_wid = np.array(sorted(int(o["id"].rsplit("W", 1)[1]) for o in oa if o.get("id")), dtype=np.int64)
lab = pd.read_parquet(RUN + "/data/labels.parquet"); lab_doi = set(lab.doi)
out["openalex_is_retracted_works"] = len(oa); out["openalex_with_doi"] = len(oa_doi); out["labels"] = len(lab_doi)
out["both"] = len(oa_doi & lab_doi); out["labels_only"] = len(lab_doi - oa_doi); out["openalex_only"] = len(oa_doi - lab_doi)
# test cohort: labelled vs OpenAlex-flagged
parts = []
for f in sorted(glob.glob(RUN + "/data/features/*.parquet")):
    t = pq.read_table(f, columns=["wid", "year", "ret", "host"]).to_pandas(); parts.append(t[t.year.between(2021, 2022)])
te = pd.concat(parts, ignore_index=True); del parts
flag = np.isin(te.wid.to_numpy(), oa_wid); labd = (te.ret > 0).to_numpy()
out["test"] = {"articles": int(len(te)), "labelled_retracted": int(labd.sum()), "openalex_flagged": int(flag.sum()),
               "both": int((flag & labd).sum()), "labelled_not_flagged": int((labd & ~flag).sum()), "flagged_not_labelled": int((flag & ~labd).sum()),
               "flagged_not_labelled_top_hosts": {str(int(k)): int(v) for k, v in te.host[flag & ~labd].value_counts().head(5).items()}}
print(json.dumps(out, indent=1), flush=True)
# (b) type 'article' share among retracted works by retraction year (pass-1 arrays: ret, art, year)
R, A, Yr = [], [], []
for f in sorted(glob.glob(RUN + "/data/pass1/*.npz")):
    z = np.load(f); r = z["ret"]; m = r > 0
    R.append(r[m]); A.append(z["art"][m]); Yr.append(z["year"][m])
    if len(R) % 500 == 0: print(len(R), "files", round(time.time() - t0), "s", flush=True)
R, A, Yr = np.concatenate(R), np.concatenate(A), np.concatenate(Yr)
d = pd.DataFrame({"r": R.astype(int), "a": A.astype(bool), "y": Yr.astype(int)})
g = d[d.r >= 2015].groupby("r").a.agg(["size", "mean"])
out["retracted_works_article_type_share_by_retraction_year"] = {str(int(k)): {"n": int(v["size"]), "article_share": round(float(v["mean"]), 3)} for k, v in g.iterrows()}
g2 = d[(d.y >= 2015) & (d.y <= 2026)].groupby("y").a.agg(["size", "mean"])
out["retracted_works_article_type_share_by_pub_year"] = {str(int(k)): {"n": int(v["size"]), "article_share": round(float(v["mean"]), 3)} for k, v in g2.iterrows()}
# overall article share among all works 2015-2026 is not stored in the lookup; approximate from the cohort logs instead (pass2: 16.1M of 476M).
json.dump(out, open(RUN + "/review/reviewer_checks/c5_openalex_agreement_and_retype.json", "w"), indent=1)
print(json.dumps(out, indent=1)); print("done", round(time.time() - t0), "s")
