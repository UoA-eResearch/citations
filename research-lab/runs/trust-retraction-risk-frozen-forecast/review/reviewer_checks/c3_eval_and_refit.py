"""Reviewer check 3: recompute the test evaluation from the frozen models; bootstrap variants; host composition of the
top 1%; enrichment within and without Hindawi; own-retraction leak; score ties; metadata completeness by retraction
status; validation curves of the frozen models; refits with fixed iteration counts; H2 without Hindawi.
Aggregates only: no per-article score is written anywhere."""
import glob, hashlib, json, pickle, time
import numpy as np, pandas as pd
RUN = "/mnt/citations/research-lab/runs/trust-retraction-risk-frozen-forecast"
FE, MD, T = RUN + "/data/features", RUN + "/data/models", RUN + "/results/tables"
OUTF = RUN + "/review/reviewer_checks/c3_eval.json"
SEED = 20261022; HIND, ELS, SPR, MYST = 4310319869, 4310320990, 4310319900, 1299303238
A = ["src_rate", "host_rate", "src_growth", "src_missing", "stype", "oa", "field_c"]
B = ["nauth", "auth_prior_ret_n", "auth_prior_ret_max", "newcomer_share", "n_inst", "inst_max_rate", "n_countries"]
C = ["n_refs", "ref_unresolved_share", "ref_retracted_share", "ref_same_source_share", "ref_year_sd", "ref_recency_gap"]
CAT = ["stype", "field_c"]; SETS = {"full": A + B + C, "no_A": B + C, "A_only": A, "B_only": B, "C_only": C}
out = {}; t0 = time.time()
def log(*a): print(round(time.time() - t0), "s", *a, flush=True)
hashes = json.load(open(T + "/model_hashes.json")); fmap = {int(k): v for k, v in hashes["field_codes"].items()}
for name, h in hashes["models"].items():
    assert hashlib.sha256(open(MD + "/" + name, "rb").read()).hexdigest() == h["sha256"], name
# ---- load: test in full, train as 5% negatives + positives (per file, same scheme as model.py, own draw)
rng = np.random.default_rng(SEED); te, tr = [], []
for f in sorted(glob.glob(FE + "/*.parquet")):
    d = pd.read_parquet(f)
    te.append(d[d.year.between(2021, 2022)])
    x = d[d.year.between(2015, 2019)].drop(columns=["country1"])
    y = ((x.ret > 0) & (x.ret <= 2020)).to_numpy()
    tr.append(x[y | (rng.random(len(x)) < 0.05)])
test = pd.concat(te, ignore_index=True); del te
train = pd.concat(tr, ignore_index=True); del tr
for d in (test, train): d["field_c"] = d.field.map(fmap).fillna(0).astype(int)
test["country1"] = test.country1.astype("category")
y = (test.ret > 0).to_numpy().astype(float); n = len(test)
ytr = ((train.ret > 0) & (train.ret <= 2020)).to_numpy(); wtr = np.where(ytr, 1.0, 20.0)
out["test"] = {"articles": n, "retracted": int(y.sum()), "base_rate": round(float(y.mean()), 6)}
out["train_sample"] = {"rows": len(train), "positives": int(ytr.sum())}
log("loaded", out["test"], out["train_sample"])
# ---- helpers
def topmask(s, k):
    m = max(1, int(round(k * len(s)))); t = np.zeros(len(s), bool); t[np.argsort(-s, kind="stable")[:m]] = True; return t
def E(s, yy, k):
    t = topmask(s, k); return float(yy[t].mean() / yy.mean()) if yy.mean() > 0 else float("nan")
def agg(s, yy, cl, k):
    t = topmask(s, k); cid, inv = np.unique(cl, return_inverse=True)
    return np.stack([np.bincount(inv, minlength=len(cid)), np.bincount(inv, weights=yy, minlength=len(cid)),
                     np.bincount(inv, weights=t, minlength=len(cid)), np.bincount(inv, weights=yy * t, minlength=len(cid))])
def ratio(S): return (S[:, 3] / np.maximum(S[:, 2], 1)) / (S[:, 1] / np.maximum(S[:, 0], 1))
def ci(e): return [round(float(np.percentile(e, 2.5)), 2), round(float(np.percentile(e, 97.5)), 2)]
def boot_poisson(G, B=1000):
    r = np.random.default_rng(SEED); e = []
    for _ in range(B // 50): e.append(ratio(r.poisson(1.0, size=(50, G.shape[1])).astype(np.float32) @ G.T))
    return ci(np.concatenate(e))
def boot_multinomial(G, B=1000):
    r = np.random.default_rng(SEED); m = G.shape[1]; e = []
    for _ in range(B):
        w = np.bincount(r.integers(0, m, m), minlength=m).astype(np.float32); e.append(ratio((w @ G.T)[None, :])[0])
    return ci(np.array(e))
def boot_iid(s, yy, k, B=1000):
    t = topmask(s, k); r = np.random.default_rng(SEED)
    Rt, Nt, R, N = yy[t].sum(), t.sum(), yy.sum(), len(yy)
    rt = r.poisson(Rt, B); nt = r.poisson(Nt, B); rr = r.poisson(R - Rt, B); nr = r.poisson(N - Nt, B)
    return ci((rt / np.maximum(nt, 1)) / ((rt + rr) / np.maximum(nt + nr, 1)))
def clusters(d): h = d.host.to_numpy().astype(np.int64); return np.where(h > 0, h, -(np.arange(len(d)) + 1))
def clusters_src(d): h = d.src.to_numpy().astype(np.int64); return np.where(h > 0, h, -(np.arange(len(d)) + 1))
from sklearn.metrics import average_precision_score
# ---- frozen models: predictions and recomputed metrics
scores, out["frozen"] = {}, {}
cl = clusters(test); cls = clusters_src(test)
for name in hashes["models"]:
    b = pickle.load(open(MD + "/" + name, "rb")); m = b["model"]
    s = m.predict_proba(test[b["cols"]])[:, 1]; scores[name] = s
    r = {"E": {f"{k:g}": round(E(s, y, k), 3) for k in (0.001, 0.01, 0.05, 0.1)}, "pr_auc": round(float(average_precision_score(y, s)), 5),
         "distinct_scores": int(len(np.unique(s)))}
    G = agg(s, y, cl, 0.01)
    r["ci_E1_poisson_host"] = boot_poisson(G); r["ci_E1_multinomial_host"] = boot_multinomial(G)
    r["ci_E1_iid_article"] = boot_iid(s, y, 0.01); r["ci_E1_poisson_source"] = boot_poisson(agg(s, y, cls, 0.01))
    if hasattr(m, "validation_score_"):
        r["n_iter"] = int(m.n_iter_); r["validation_score_"] = [round(float(v), 5) for v in m.validation_score_]
        r["train_score_"] = [round(float(v), 5) for v in m.train_score_]
    # ties at the 1% boundary
    k1 = max(1, int(round(0.01 * n))); srt = np.sort(s)[::-1]; thr = srt[k1 - 1]
    tie = s == thr; above = s > thr
    r["ties_at_1pct_boundary"] = {"threshold": float(thr), "n_strictly_above": int(above.sum()), "n_at_threshold": int(tie.sum()),
                                  "retracted_at_threshold": int(y[tie].sum()), "retracted_strictly_above": int(y[above].sum())}
    if tie.sum() > 1:
        need = k1 - above.sum(); p = y[tie].mean(); rt = y[above].sum()
        r["ties_at_1pct_boundary"]["E1_expected_random_tiebreak"] = round(float((rt + need * p) / k1 / y.mean()), 3)
        r["ties_at_1pct_boundary"]["E1_best_case"] = round(float((rt + min(need, y[tie].sum())) / k1 / y.mean()), 3)
        r["ties_at_1pct_boundary"]["E1_worst_case"] = round(float((rt + max(0, need - (tie.sum() - y[tie].sum()))) / k1 / y.mean()), 3)
    # by year
    r["E1_by_year"] = {}
    for yr in (2021, 2022):
        mk = (test.year == yr).to_numpy(); r["E1_by_year"][str(yr)] = round(E(s[mk], y[mk], 0.01), 3)
    out["frozen"][name] = r; log(name, r["E"], r["ci_E1_poisson_host"])
# ---- host composition of the top 1%
out["top1_host_composition"] = {}
for name in ("hgb_full.pkl", "hgb_no_A.pkl", "hgb_A_only.pkl"):
    t1 = topmask(scores[name], 0.01)
    g = pd.DataFrame({"host": test.host.to_numpy(), "top": t1, "y": y}).groupby("host").agg(n=("top", "size"), top=("top", "sum"), ret=("y", "sum"))
    g["cohort_share"] = g.n / n; g["top1_share"] = g.top / t1.sum(); g["ret_share"] = g.ret / y.sum()
    g["ret_rate_in_host"] = g.ret / g.n; g["top1_rate_in_host"] = g.top / g.n
    g = g.sort_values("top1_share", ascending=False)
    cum = g.top1_share.cumsum()
    out["top1_host_composition"][name] = {"hosts_covering_50pct_of_top1": int((cum < 0.5).sum() + 1),
        "top8": {str(int(h)): {c: round(float(v), 4) for c, v in row.items() if c in ("cohort_share", "top1_share", "ret_share", "ret_rate_in_host", "top1_rate_in_host")} for h, row in g.head(8).iterrows()}}
# ---- within / without a host, frozen scores (no refit)
out["within_without_host"] = {}
for name in ("hgb_full.pkl", "hgb_no_A.pkl", "hgb_A_only.pkl", "hgb_B_only.pkl", "hgb_C_only.pkl"):
    s = scores[name]; r = {}
    for lab, h in (("hindawi", HIND), ("host_1299303238", MYST), ("elsevier", ELS)):
        mk = (test.host == h).to_numpy()
        r[lab] = {"n": int(mk.sum()), "retracted": int(y[mk].sum()), "E1_within": round(E(s[mk], y[mk], 0.01), 3) if y[mk].sum() else None,
                  "E1_excluding": round(E(s[~mk], y[~mk], 0.01), 3), "ci_E1_excluding_poisson_host": boot_poisson(agg(s[~mk], y[~mk], cl[~mk], 0.01))}
    mk = np.isin(test.host.to_numpy(), [HIND, MYST])
    r["excluding_both_hindawi_and_1299303238"] = {"E1": round(E(s[~mk], y[~mk], 0.01), 3), "ci": boot_poisson(agg(s[~mk], y[~mk], cl[~mk], 0.01))}
    out["within_without_host"][name] = r
log("host blocks done")
# ---- own-retraction leak: test articles whose own retraction year <= year-1 (counted as a prior retraction of its authors)
leak = ((test.ret > 0) & (test.ret <= test.year - 1)).to_numpy()
r = {"n_test_articles_ret_year_le_pubyear_minus1": int(leak.sum()), "of_which_auth_prior_ret_n_gt0": int((test.auth_prior_ret_n.to_numpy()[leak] > 0).sum())}
for name in ("hgb_full.pkl", "hgb_no_A.pkl", "hgb_B_only.pkl"):
    s = scores[name]; t1 = topmask(s, 0.01)
    r[name] = {"leak_articles_in_top1": int((t1 & leak).sum()), "E1_without_leak_articles": round(E(s[~leak], y[~leak], 0.01), 3)}
out["own_retraction_leak"] = r
# ---- how much of H2 is 'known offender' signal
apr = test.auth_prior_ret_n.to_numpy(); rrs = np.nan_to_num(test.ref_retracted_share.to_numpy()); imr = test.inst_max_rate.to_numpy()
s = scores["hgb_no_A.pkl"]; t1 = topmask(s, 0.01)
out["h2_signal_decomposition"] = {
    "share_auth_prior_gt0": {"cohort": round(float((apr > 0).mean()), 4), "retracted": round(float((apr[y > 0] > 0).mean()), 4), "top1_no_A": round(float((apr[t1] > 0).mean()), 4)},
    "share_ref_retracted_gt0": {"cohort": round(float((rrs > 0).mean()), 4), "retracted": round(float((rrs[y > 0] > 0).mean()), 4), "top1_no_A": round(float((rrs[t1] > 0).mean()), 4)},
    "share_inst_max_rate_gt0": {"cohort": round(float((imr > 0).mean()), 4), "retracted": round(float((imr[y > 0] > 0).mean()), 4), "top1_no_A": round(float((imr[t1] > 0).mean()), 4)},
    "E1_no_A_among_auth_prior_eq0": round(E(s[apr == 0], y[apr == 0], 0.01), 3),
    "E1_no_A_among_auth_prior_eq0_and_ref_ret_eq0": round(E(s[(apr == 0) & (rrs == 0)], y[(apr == 0) & (rrs == 0)], 0.01), 3),
    "retracted_share_with_neither_signal": round(float(((apr == 0) & (rrs == 0))[y > 0].mean()), 4),
    "hindawi_share_of_top1_no_A": round(float((test.host.to_numpy()[t1] == HIND).mean()), 4),
    "E1_no_A_hindawi_only_within": round(E(s[test.host.to_numpy() == HIND], y[test.host.to_numpy() == HIND], 0.01), 3)}
# ---- metadata completeness: retracted vs not, overall and within hosts
def comp(mk):
    d = test[mk]; yy = y[mk]; rows = {}
    for lab, sel in (("retracted", yy > 0), ("not_retracted", yy == 0)):
        x = d[sel]; rows[lab] = {"n": int(len(x)), "no_refs": round(float((x.n_refs == 0).mean()), 4), "no_authors": round(float((x.nauth == 0).mean()), 4),
                                 "no_country": round(float((x.country1.astype(str) == "").mean()), 4), "no_inst": round(float((x.n_inst == 0).mean()), 4),
                                 "src_missing": round(float((x.src_missing == 1).mean()), 4), "median_n_refs": float(x.n_refs.median()),
                                 "mean_ref_unresolved": round(float(np.nanmean(x.ref_unresolved_share)), 4), "oa_share": round(float(x.oa.mean()), 4),
                                 "median_nauth": float(x.nauth.median()), "mean_newcomer_share": round(float(x.newcomer_share.mean()), 4)}
    return rows
out["completeness"] = {"all": comp(np.ones(n, bool)), "hindawi": comp((test.host == HIND).to_numpy()), "elsevier": comp((test.host == ELS).to_numpy()),
                       "springer": comp((test.host == SPR).to_numpy()), "host_1299303238": comp((test.host == MYST).to_numpy())}
log("completeness done")
# ---- refits with fixed iteration counts (no early stopping) and early-stopping seeds
from sklearn.ensemble import HistGradientBoostingClassifier as H
def fit(cols, max_iter, early, seed=SEED, X=None, yy=None, w=None):
    X = train if X is None else X; yy = ytr if yy is None else yy; w = wtr if w is None else w
    m = H(max_iter=max_iter, early_stopping=early, validation_fraction=0.1, random_state=seed, categorical_features=[c in CAT for c in cols])
    m.fit(X[cols], yy, sample_weight=w); return m
def ev(m, cols, d=None, yy=None, clz=None):
    d = test if d is None else d; yy = y if yy is None else yy; clz = cl if clz is None else clz
    s = m.predict_proba(d[cols])[:, 1]
    hm = (d.host == HIND).to_numpy()
    return {"n_iter": int(m.n_iter_), "E0.1": round(E(s, yy, 0.001), 3), "E1": round(E(s, yy, 0.01), 3), "E5": round(E(s, yy, 0.05), 3),
            "ci_E1_poisson_host": boot_poisson(agg(s, yy, clz, 0.01)), "pr_auc": round(float(average_precision_score(yy, s)), 5),
            "E1_excluding_hindawi_frozen_scores": round(E(s[~hm], yy[~hm], 0.01), 3), "distinct_scores": int(len(np.unique(s)))}
out["refits"] = {}
for setname, it in (("full", 10), ("full", 32), ("full", 100), ("full", 300), ("no_A", 10), ("no_A", 32), ("no_A", 100), ("A_only", 64), ("A_only", 300)):
    out["refits"][f"{setname}_fixed_{it}"] = ev(fit(SETS[setname], it, False), SETS[setname]); log("refit", setname, it, out["refits"][f"{setname}_fixed_{it}"]["E1"])
for seed in (1, 2, 3):
    out["refits"][f"full_earlystop_seed{seed}"] = ev(fit(SETS["full"], 300, True, seed), SETS["full"]); log("refit es", seed, out["refits"][f"full_earlystop_seed{seed}"])
    out["refits"][f"no_A_earlystop_seed{seed}"] = ev(fit(SETS["no_A"], 300, True, seed), SETS["no_A"])
# full model without the three publisher-level rate features but with the rest of block A
out["refits"]["full_minus_src_host_rate_earlystop"] = ev(fit([c for c in SETS["full"] if c not in ("src_rate", "host_rate")], 300, True), [c for c in SETS["full"] if c not in ("src_rate", "host_rate")])
# H2 leave-Hindawi-out refit (plan-style: drop the host from train and test, refit no_A)
mk_tr = (train.host != HIND).to_numpy(); mk_te = (test.host != HIND).to_numpy()
m = fit(SETS["no_A"], 300, True, X=train[mk_tr], yy=ytr[mk_tr], w=wtr[mk_tr])
out["refits"]["no_A_leave_hindawi_out_refit"] = ev(m, SETS["no_A"], test[mk_te], y[mk_te], cl[mk_te])
m = fit(SETS["full"], 300, True, X=train[mk_tr], yy=ytr[mk_tr], w=wtr[mk_tr])
out["refits"]["full_leave_hindawi_out_refit_(replicates_lopo)"] = ev(m, SETS["full"], test[mk_te], y[mk_te], cl[mk_te])
log("refits done")
json.dump(out, open(OUTF, "w"), indent=1)
print(json.dumps(out, indent=1))
