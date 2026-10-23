"""Reviewer check 0: sanity of the works lookup and author-retraction keys (read-only, mmap)."""
import numpy as np, pandas as pd, json, sys
LK = "/mnt/citations/research-lab/runs/trust-retraction-risk-frozen-forecast/data/lookup/"
ret = np.load(LK + "w_ret.npy", mmap_mode="r")
year = np.load(LK + "w_year.npy", mmap_mode="r")
out = {}
nz = np.flatnonzero(np.asarray(ret) > 0)
out["works_with_retraction_year"] = int(len(nz))
r = np.asarray(ret)[nz].astype(int); y = np.asarray(year)[nz].astype(int)
out["ret_year_counts"] = {int(k): int(v) for k, v in zip(*np.unique(r, return_counts=True))}
out["ret_before_pubyear"] = int((r < y).sum())
out["ret_eq_pubyear"] = int((r == y).sum())
out["ret_after_pubyear"] = int((r > y).sum())
out["pubyear_zero"] = int((y == 0).sum())
d = r - y
out["ret_minus_pub_quantiles"] = {q: int(np.percentile(d[y > 0], q)) for q in (1, 5, 25, 50, 75, 95, 99)}
ar_r = np.load(LK + "ar_r.npy")
out["ar_rows"] = int(len(ar_r)); out["ar_r_min_max"] = [int(ar_r.min()), int(ar_r.max())]
af = np.load(LK + "a_first.npy", mmap_mode="r")
out["a_first_min_max"] = [int(np.asarray(af).min()), int(np.asarray(af).max())]
rates = pd.read_parquet(LK + "rates.parquet")
out["rates_rows_by_kind_Y"] = rates.groupby(["k", "Y"]).size().to_dict()
out["rates_rows_by_kind_Y"] = {f"{k}_{Y}": int(v) for (k, Y), v in out["rates_rows_by_kind_Y"].items()}
lab = pd.read_parquet("/mnt/citations/research-lab/runs/trust-retraction-risk-frozen-forecast/data/labels.parquet")
out["label_rows"] = int(len(lab)); out["label_year_counts"] = {int(k): int(v) for k, v in lab.date.dt.year.value_counts().sort_index().items()}
out["labels_crossref_only"] = int((lab.crossref & ~lab.rw).sum()); out["labels_crossref_only_selfupdate"] = int((lab.crossref & ~lab.rw & lab.self_update).sum())
print(json.dumps(out, indent=1))
json.dump(out, open("/mnt/citations/research-lab/runs/trust-retraction-risk-frozen-forecast/review/reviewer_checks/c0_lookup_sanity.json", "w"), indent=1)
