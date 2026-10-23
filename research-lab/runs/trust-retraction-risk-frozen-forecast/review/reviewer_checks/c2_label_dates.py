"""Reviewer check 2: label dating. RW date parsing, RW-vs-Crossref dates where both exist, self-update dates."""
import json, re
import numpy as np, pandas as pd
SRC = "/mnt/data/retraction-markers/raw"
def ndoi(x):
    if not isinstance(x, str): return None
    x = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", x.strip().lower())
    return x if x.startswith("10.") else None
out = {}
rw = pd.read_csv(SRC + "/retraction_watch.csv", dtype=str, encoding="utf-8", encoding_errors="replace")
out["rw_nature_counts"] = rw.RetractionNature.value_counts().to_dict()
rr = rw[rw.RetractionNature == "Retraction"].copy()
rr["date"] = pd.to_datetime(rr.RetractionDate, format="%m/%d/%Y %H:%M", errors="coerce")
rr["odate"] = pd.to_datetime(rr.OriginalPaperDate, format="%m/%d/%Y %H:%M", errors="coerce")
out["rw_retraction_rows"] = int(len(rr)); out["rw_date_unparsed"] = int(rr.date.isna().sum())
out["rw_unparsed_examples"] = rr.RetractionDate[rr.date.isna()].head(5).tolist()
out["rw_original_date_unparsed"] = int(rr.odate.isna().sum())
d = (rr.date.dt.year - rr.odate.dt.year).dropna()
out["rw_retyear_minus_pubyear_counts"] = {str(int(k)): int(v) for k, v in d.value_counts().sort_index().items() if -2 <= k <= 15}
out["rw_same_year_share"] = round(float((d == 0).mean()), 4); out["rw_negative_share"] = round(float((d < 0).mean()), 5)
rwd = rr.assign(k=rr.OriginalPaperDOI.map(ndoi)).dropna(subset=["k"]).groupby("k").agg(rw_date=("date", "min"), odate=("odate", "min"))
cr = {}
self_created = []
for line in open(SRC + "/crossref_notices.jsonl"):
    it = json.loads(line); own = ndoi(it.get("DOI"))
    for u in it.get("update-to") or []:
        if (u.get("type") or "").lower() != "retraction": continue
        k = ndoi(u.get("DOI"))
        if not k: continue
        dp = ((u.get("updated") or {}).get("date-parts") or [[None]])[0]
        dt = pd.Timestamp(year=dp[0], month=(dp[1] if len(dp) > 1 and dp[1] else 1), day=(dp[2] if len(dp) > 2 and dp[2] else 1)) if dp and dp[0] else pd.NaT
        x = cr.setdefault(k, {"cr_date": pd.NaT, "self": False, "created": pd.NaT, "source": set()})
        x["self"] = x["self"] or (k == own)
        x["source"].add(u.get("source") or "")
        if pd.notna(dt) and (pd.isna(x["cr_date"]) or dt < x["cr_date"]): x["cr_date"] = dt
        cp = ((it.get("created") or {}).get("date-parts") or [[None]])[0]
        cdt = pd.Timestamp(year=cp[0], month=cp[1] if len(cp) > 1 else 1, day=cp[2] if len(cp) > 2 else 1) if cp and cp[0] else pd.NaT
        if pd.notna(cdt) and (pd.isna(x["created"]) or cdt < x["created"]): x["created"] = cdt
crd = pd.DataFrame([{"k": k, "cr_date": v["cr_date"], "self": v["self"], "created": v["created"], "src": ";".join(sorted(v["source"]))} for k, v in cr.items()]).set_index("k")
out["crossref_targets"] = int(len(crd)); out["crossref_self_update_targets"] = int(crd.self.sum())
out["crossref_update_source_counts"] = crd.src.value_counts().head(6).to_dict()
j = crd.join(rwd, how="inner")
out["both_dated"] = int(j.cr_date.notna().sum() and j.rw_date.notna().sum())
dd = (j.cr_date.dt.year - j.rw_date.dt.year).dropna()
out["cr_minus_rw_year_counts_all"] = {str(int(k)): int(v) for k, v in dd.value_counts().sort_index().items() if -10 <= k <= 10}
ds = (j[j.self].cr_date.dt.year - j[j.self].rw_date.dt.year).dropna()
out["cr_minus_rw_year_counts_self_update"] = {str(int(k)): int(v) for k, v in ds.value_counts().sort_index().items() if -10 <= k <= 10}
dn = (j[~j.self].cr_date.dt.year - j[~j.self].rw_date.dt.year).dropna()
out["cr_minus_rw_year_counts_non_self"] = {str(int(k)): int(v) for k, v in dn.value_counts().sort_index().items() if -10 <= k <= 10}
# self-updates: is the crossref 'updated' date the paper's own publication date? compare with RW original paper date
e = (j[j.self].cr_date.dt.year - j[j.self].odate.dt.year).dropna()
out["self_update_cr_year_minus_rw_pubyear_counts"] = {str(int(k)): int(v) for k, v in e.value_counts().sort_index().items() if -3 <= k <= 12}
out["self_update_cr_date_equals_rw_pubdate_share"] = round(float((j[j.self].cr_date == j[j.self].odate).mean()), 4)
out["self_update_cr_year_equals_rw_retyear_share"] = round(float((ds == 0).mean()), 4)
# Crossref-only records (no RW): how many are self-updates and the 'created' vs 'updated' relation
co = crd[~crd.index.isin(rwd.index)]
out["crossref_only"] = int(len(co)); out["crossref_only_self"] = int(co.self.sum())
cc = (co[co.self].cr_date.dt.year - co[co.self].created.dt.year).dropna()
out["crossref_only_self_updated_year_minus_created_year"] = {str(int(k)): int(v) for k, v in cc.value_counts().sort_index().items() if -5 <= k <= 20}
out["crossref_only_self_cr_year_counts"] = {str(int(k)): int(v) for k, v in co[co.self].cr_date.dt.year.value_counts().sort_index().items() if k >= 2010}
print(json.dumps(out, indent=1, default=str))
json.dump(out, open("/mnt/citations/research-lab/runs/trust-retraction-risk-frozen-forecast/review/reviewer_checks/c2_label_dates.json", "w"), indent=1, default=str)
