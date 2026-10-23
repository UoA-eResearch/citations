"""Reviewer check 4 (replaces the failed c1: pass2 stores DOIs as lowercased full URLs). One read-only pass over
data/cohort_raw: (a) retraction-notice DOIs that sit in the cohort as 'articles'; (b) for labelled cohort articles,
retraction year vs publication year by label source and window; (c) for every 2021-2022 test article, the author-prior
and reference-retraction features recomputed with a one-year buffer (retraction year <= Y-2 instead of <= Y-1), then the
frozen H2 (no_A) and full models rescored. Aggregates only."""
import glob, json, pickle, re, time
import numpy as np, pandas as pd
RUN = "/mnt/citations/research-lab/runs/trust-retraction-risk-frozen-forecast"; SRC = "/mnt/data/retraction-markers/raw"
LK = RUN + "/data/lookup/"; t0 = time.time()
def ndoi(x):
    if not isinstance(x, str): return None
    x = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", x.strip().lower())
    return x if x.startswith("10.") else None
lab = pd.read_parquet(RUN + "/data/labels.parquet"); lab["ry"] = lab.date.dt.year.astype(int)
labidx = {d: i for i, d in enumerate(lab.doi)}
notice = set()
for line in open(SRC + "/crossref_notices.jsonl"):
    it = json.loads(line); own = ndoi(it.get("DOI"))
    if not own: continue
    for u in it.get("update-to") or []:
        if (u.get("type") or "").lower() == "retraction" and ndoi(u.get("DOI")) != own: notice.add(own)
rw = pd.read_csv(SRC + "/retraction_watch.csv", dtype=str, usecols=["RetractionDOI", "OriginalPaperDOI", "RetractionNature"], encoding_errors="replace")
for d, o, n in zip(rw.RetractionDOI, rw.OriginalPaperDOI, rw.RetractionNature):
    if n == "Retraction" and ndoi(d) and ndoi(d) != ndoi(o): notice.add(ndoi(d))
notice -= set(labidx)
w_wid = np.load(LK + "w_wid.npy", mmap_mode="r"); w_ret = np.load(LK + "w_ret.npy", mmap_mode="r")
ar_key = np.load(LK + "ar_a.npy").astype(np.int64) * 4096 + np.load(LK + "ar_r.npy").astype(np.int64)
def lookup(sorted_ids, ids):
    i = np.searchsorted(sorted_ids, ids); i = np.minimum(i, len(sorted_ids) - 1); return i, np.asarray(sorted_ids[i]) == ids
rows, nrows, buf = [], [], []
for fi, f in enumerate(sorted(glob.glob(RUN + "/data/cohort_raw/*.npz"))):
    z = np.load(f)
    if "empty" in z.files: continue
    year = z["year"].astype(np.int64); wid = z["wid"]; host = z["host"]; n = len(wid)
    doi = [re.sub(r"^https?://(dx\.)?doi\.org/", "", d) for d in z["doi"]]
    for j, d in enumerate(doi):
        k = labidx.get(d)
        if k is not None: rows.append((int(wid[j]), int(year[j]), int(host[j]), k))
        elif d in notice: nrows.append((int(wid[j]), int(year[j]), int(host[j])))
    # (c) buffered features for test rows
    te = np.flatnonzero((year == 2021) | (year == 2022))
    if len(te) == 0: continue
    sel = np.zeros(n, bool); sel[te] = True
    aoff = z["au_off"]; acnt = np.diff(aoff); aseg = np.repeat(np.arange(n), acnt); aid = z["au_id"]
    m = sel[aseg]; aseg_t = aseg[m]; aid_t = aid[m]; ay = year[aseg_t]
    lo = np.searchsorted(ar_key, aid_t * 4096, "left")
    p1 = np.searchsorted(ar_key, aid_t * 4096 + ay, "left") - lo          # retraction year <= Y-1 (as in features.py)
    p2 = np.searchsorted(ar_key, aid_t * 4096 + ay - 1, "left") - lo      # retraction year <= Y-2 (one-year buffer)
    p1[aid_t == 0] = 0; p2[aid_t == 0] = 0
    n1 = np.bincount(aseg_t, weights=(p1 > 0), minlength=n)[te]; n2 = np.bincount(aseg_t, weights=(p2 > 0), minlength=n)[te]
    mx1 = pd.Series(p1).groupby(aseg_t).max().reindex(te).fillna(0).to_numpy(); mx2 = pd.Series(p2).groupby(aseg_t).max().reindex(te).fillna(0).to_numpy()
    roff = z["rf_off"]; rcnt = np.diff(roff); rseg = np.repeat(np.arange(n), rcnt); rm = sel[rseg]; rseg_t = rseg[rm]
    k, okR = lookup(w_wid, z["rf"][rm]); rr = np.where(okR, np.asarray(w_ret)[k], 0).astype(np.int64); ry = year[rseg_t]
    ny = np.bincount(rseg_t, weights=okR, minlength=n)[te]
    s1 = np.bincount(rseg_t, weights=(rr > 0) & (rr <= ry - 1), minlength=n)[te]; s2 = np.bincount(rseg_t, weights=(rr > 0) & (rr <= ry - 2), minlength=n)[te]
    buf.append(pd.DataFrame({"wid": wid[te], "apn1": n1, "apn2": n2, "apm1": mx1, "apm2": mx2,
                             "rrs1": np.where(ny > 0, s1 / np.maximum(ny, 1), np.nan), "rrs2": np.where(ny > 0, s2 / np.maximum(ny, 1), np.nan)}))
    if (fi + 1) % 400 == 0: print(fi + 1, "files", len(rows), len(nrows), round(time.time() - t0), "s", flush=True)
L = pd.DataFrame(rows, columns=["wid", "year", "host", "k"]).merge(lab[["ry", "rw", "crossref", "self_update"]], left_on="k", right_index=True)
N = pd.DataFrame(nrows, columns=["wid", "year", "host"])
win = lambda y: np.where(y <= 2019, "train", np.where(y <= 2022, "test", "forward"))
L["win"] = win(L.year.values); N["win"] = win(N.year.values)
L["src"] = np.where(L.rw, "rw", np.where(L.self_update, "crossref_only_self_update", "crossref_only_other"))
L["rel"] = np.where(L.ry < L.year, "ret_before_pub", np.where(L.ry == L.year, "ret_same_year", "ret_after_pub"))
vc = lambda s: {str(k): int(v) for k, v in s.value_counts().items()}
out = {"notice_dois_total": len(notice), "labelled_in_cohort": int(len(L)), "notices_in_cohort": int(len(N)), "notices_in_cohort_by_window": vc(N.win),
       "notices_in_test_by_host_top5": vc(N[N.win == "test"].host.head(10**9)) if False else {str(k): int(v) for k, v in N[N.win == "test"].host.value_counts().head(5).items()},
       "labelled_by_window": vc(L.win), "labelled_rel_by_window": {w: vc(g.rel) for w, g in L.groupby("win")},
       "test_positives_by_source": vc(L[L.win == "test"].src), "test_rel_by_source": {s: vc(g.rel) for s, g in L[L.win == "test"].groupby("src")},
       "train_positives_ry_le_2020_by_source": vc(L[(L.win == "train") & (L.ry <= 2020)].src),
       "train_positives_ry_le_2020_same_year_by_source": vc(L[(L.win == "train") & (L.ry <= 2020) & (L.ry == L.year)].src),
       "train_labelled_but_ry_gt_2020": int(((L.win == "train") & (L.ry > 2020)).sum()),
       "test_positives_by_ret_year": {str(int(k)): int(v) for k, v in L[L.win == "test"].ry.value_counts().sort_index().items()},
       "test_hindawi_positives_by_ret_year": {str(int(k)): int(v) for k, v in L[(L.win == "test") & (L.host == 4310319869)].ry.value_counts().sort_index().items()},
       "forward_already_retracted": int((L.win == "forward").sum())}
print(json.dumps(out, indent=1), flush=True)
L[["wid", "year", "host", "ry", "src", "win"]].to_parquet(RUN + "/review/reviewer_checks/c4_labelled_cohort_wids.parquet", index=False)
# (c) rescore the frozen models with buffered features
Bf = pd.concat(buf, ignore_index=True); del buf
parts = []
for f in sorted(glob.glob(RUN + "/data/features/*.parquet")):
    d = pd.read_parquet(f); parts.append(d[d.year.between(2021, 2022)])
test = pd.concat(parts, ignore_index=True); del parts
hashes = json.load(open(RUN + "/results/tables/model_hashes.json")); fmap = {int(k): v for k, v in hashes["field_codes"].items()}
test["field_c"] = test.field.map(fmap).fillna(0).astype(int)
test = test.merge(Bf, on="wid", how="left"); y = (test.ret > 0).to_numpy().astype(float)
out["buffer_check"] = {"test_rows": int(len(test)), "rows_with_recomputed_features": int(test.apn1.notna().sum()),
    "recomputed_Y-1_matches_stored_auth_prior_ret_n": round(float((test.apn1.fillna(-1) == test.auth_prior_ret_n).mean()), 5),
    "recomputed_Y-1_matches_stored_ref_retracted_share": round(float((np.nan_to_num(test.rrs1, nan=-1) == np.nan_to_num(test.ref_retracted_share, nan=-1)).mean()), 5),
    "share_auth_prior_gt0_Y-1": round(float((test.apn1 > 0).mean()), 4), "share_auth_prior_gt0_Y-2": round(float((test.apn2 > 0).mean()), 4),
    "retracted_share_auth_prior_gt0_Y-1": round(float((test.apn1[y > 0] > 0).mean()), 4), "retracted_share_auth_prior_gt0_Y-2": round(float((test.apn2[y > 0] > 0).mean()), 4)}
def E(s, yy, k=0.01):
    m = max(1, int(round(k * len(s)))); t = np.argsort(-s, kind="stable")[:m]; return round(float(yy[t].mean() / yy.mean()), 3)
for name in ("hgb_no_A.pkl", "hgb_full.pkl", "hgb_B_only.pkl", "hgb_C_only.pkl"):
    b = pickle.load(open(RUN + "/data/models/" + name, "rb")); X = test[b["cols"]].copy()
    s0 = b["model"].predict_proba(X)[:, 1]
    for c, src in (("auth_prior_ret_n", "apn2"), ("auth_prior_ret_max", "apm2"), ("ref_retracted_share", "rrs2")):
        if c in X.columns: X[c] = test[src].to_numpy()
    s2 = b["model"].predict_proba(X)[:, 1]
    out["buffer_check"][name] = {"E1_stored_features": E(s0, y), "E1_buffered_Y-2": E(s2, y), "E0.1_stored": E(s0, y, 0.001), "E0.1_buffered_Y-2": E(s2, y, 0.001)}
    print(name, out["buffer_check"][name], flush=True)
json.dump(out, open(RUN + "/review/reviewer_checks/c4_scan_cohort_and_buffer.json", "w"), indent=1)
print(json.dumps(out["buffer_check"], indent=1)); print("done", round(time.time() - t0), "s")
