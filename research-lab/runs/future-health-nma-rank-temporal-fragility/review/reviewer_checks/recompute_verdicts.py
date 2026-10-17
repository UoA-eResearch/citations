"""Independent recomputation of H1, H2, H3, the negative control, secondary holdouts and descriptive numbers from
data/fits.jsonl, without importing analysis.py. Also: how often the P-score top is not the P(best) top; the flip
counting new entrants; the effect of the broken largest-component rule on the random control."""
import json, math, numpy as np, pandas as pd, statsmodels.api as sm
from scipy.stats import norm, kendalltau
RUN = "/mnt/citations/research-lab/runs/future-health-nma-rank-temporal-fragility"
dr = pd.read_csv(f"{RUN}/results/tables/direction.csv", dtype={"record": str}).set_index("record")
hold = pd.read_csv(f"{RUN}/data/holdouts.csv", dtype={"record": str}).set_index("record")
rng = np.random.default_rng(1)

def pscore(TE, se, trts, keep, small):
    idx = [trts.index(t) for t in keep]
    A = np.asarray(TE, float)[np.ix_(idx, idx)]; S = np.asarray(se, float)[np.ix_(idx, idx)]
    s = 1 if small == "good" else -1
    with np.errstate(all="ignore"):
        z = norm.cdf(s * (-A) / S)
    np.fill_diagonal(z, np.nan)
    return dict(zip(keep, np.nanmean(z, axis=1)))

def top(d): return max(d, key=lambda k: (d[k], k))

def wilson(k, n, z=1.959964):
    p = k / n; den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h

rows = []; rand = {}
for line in open(f"{RUN}/data/fits.jsonl"):
    r = json.loads(line); rec = r["record"]; F = {f["name"]: f for f in r["fits"]}
    small = dr.loc[rec, "small_values"]; full = F["full"]
    if full.get("error"): continue
    fset = hold.loc[rec, "set"]
    def res(pre):
        keep = [t for t in pre["trts"] if t in full["trts"]]
        pre_ps = dict(zip(pre["trts"], pre["pscore"])); pre_ps = {t: pre_ps[t] for t in keep}
        fs = pscore(full["TE"], full["seTE"], full["trts"], keep, small)
        fa = pscore(full["TE"], full["seTE"], full["trts"], full["trts"], small)
        pt, ft = top(pre_ps), top(fs)
        o = sorted(pre_ps.values(), reverse=True)
        out = dict(pre_top=pt, full_top=ft, flip=int(pt != ft), new_top=int(top(fa) not in keep), gap=o[0] - o[1], k_pre=pre["n_studies"], n_keep=len(keep), n_pre=len(pre["trts"]))
        if "pbest" in pre:
            pb = dict(zip(pre["pbest_trts"], pre["pbest"])); out["pbest_top"] = pb[pt]; out["pbest_max_trt"] = top(pb); out["pbest_max"] = max(pb.values())
            out["kendall"] = kendalltau([pre_ps[t] for t in keep], [fs[t] for t in keep]).statistic if len(keep) >= 3 else np.nan
        return out
    row = dict(record=rec, set=fset, confidence=dr.loc[rec, "confidence"])
    for name in ["T10", "S1", "S2", "S3"]:
        pre = F.get(name)
        if pre is None or pre.get("error"): row[name + "_ok"] = False; continue
        row[name + "_ok"] = True
        for k, v in res(pre).items(): row[f"{name}_{k}"] = v
    fl = [res(F[n])["flip"] for n in F if n.startswith("R") and not F[n].get("error")]
    row["rand_n"] = len(fl); row["rand_flip"] = np.mean(fl) if fl else np.nan
    rows.append(row)
df = pd.DataFrame(rows)
df.to_csv(f"{RUN}/review/reviewer_checks/recomputed_network_results.csv", index=False)
P = df[(df.set == "primary") & df.T10_ok].copy()
print("primary networks with T10 fit:", len(P), "; excluded primary (T10 failed):", ((df.set == "primary") & ~df.T10_ok).sum(), list(df[(df.set == "primary") & ~df.T10_ok].record))
k, n = int(P.T10_flip.sum()), len(P); lo, hi = wilson(k, n)
print(f"H1: {k}/{n} = {k/n:.4f}  Wilson [{lo:.4f}, {hi:.4f}]  -> {'Refuted' if hi < .30 else 'Supported' if k/n >= .3 and lo >= .25 else 'Inconclusive'}")
both = int(((P.T10_flip == 1) | (P.T10_new_top == 1)).sum()); print(f"flip or new-entrant top: {both}/{n} = {both/n:.3f}; new entrant top: {int(P.T10_new_top.sum())}; overlap: {int(((P.T10_flip==1)&(P.T10_new_top==1)).sum())}")
# H2
mp, ret = P.T10_pbest_top.mean(), 1 - P.T10_flip.mean(); d0 = mp - ret
B = 2000; vals = []
for _ in range(B):
    x = P.iloc[rng.integers(0, n, n)]; vals.append(x.T10_pbest_top.mean() - (1 - x.T10_flip.mean()))
l2, u2 = np.percentile(vals, [2.5, 97.5])
print(f"H2: mean P(best) {mp:.4f}, retention {ret:.4f}, overstatement {d0:.4f} [{l2:.4f}, {u2:.4f}] -> {'Refuted' if u2 < .2 else 'Supported' if d0 >= .2 and l2 >= .15 else 'Inconclusive'}")
print(f"   P-score top != P(best) top in {int((P.T10_pre_top != P.T10_pbest_max_trt).sum())} networks; mean max P(best) {P.T10_pbest_max.mean():.4f}")
ret_new = 1 - ((P.T10_flip == 1) | (P.T10_new_top == 1)).mean(); print(f"   retention counting new entrants as loss: {ret_new:.4f} (overstatement {mp - ret_new:.4f})")
# H3
def nagel(y, X):
    X = sm.add_constant(np.asarray(X, float)); m = sm.Logit(np.asarray(y, float), X).fit(disp=0, maxiter=200)
    nn = len(y); cs = 1 - math.exp(2 * (m.llnull - m.llf) / nn); return cs / (1 - math.exp(2 * m.llnull / nn)), m
P["log_k"] = np.log(P.T10_k_pre.astype(float))
r2, m = nagel(P.T10_flip, P[["T10_gap", "log_k"]]); vals = []
for _ in range(B):
    x = P.iloc[rng.integers(0, n, n)]
    try: vals.append(nagel(x.T10_flip, x[["T10_gap", "log_k"]])[0])
    except Exception: pass
l3, u3 = np.percentile(vals, [2.5, 97.5])
pred = m.predict(sm.add_constant(P[["T10_gap", "log_k"]].astype(float)))
pos, neg = pred[P.T10_flip == 1], pred[P.T10_flip == 0]; auc = np.mean([(a > b) + 0.5 * (a == b) for a in pos for b in neg])
print(f"H3: Nagelkerke R2 {r2:.4f} [{l3:.4f}, {u3:.4f}] AUC {auc:.3f} coef {dict(zip(['const','gap','log_k'], m.params.round(3)))} p {dict(zip(['const','gap','log_k'], m.pvalues.round(3)))} -> {'Supported' if u3 < .5 else 'Refuted' if l3 >= .5 else 'Inconclusive'}")
print(f"   flip rate gap<0.05: {P[P.T10_gap < .05].T10_flip.mean():.3f} (n={int((P.T10_gap < .05).sum())}); gap>=0.2: {P[P.T10_gap >= .2].T10_flip.mean():.3f} (n={int((P.T10_gap >= .2).sum())})")
# negative control
nc = P.dropna(subset=["rand_flip"]); d = nc.T10_flip - nc.rand_flip; vals = []
for _ in range(B):
    x = d.iloc[rng.integers(0, len(d), len(d))]; vals.append(x.mean())
print(f"NC: temporal {nc.T10_flip.mean():.4f} random {nc.rand_flip.mean():.4f} diff {d.mean():.4f} [{np.percentile(vals,2.5):.4f}, {np.percentile(vals,97.5):.4f}]; random fits used {int(nc.rand_n.sum())} of {200*len(nc)}")
print(f"   networks with <200 random fits: {int((nc.rand_n < 200).sum())}; flip rate in those: temporal {nc[nc.rand_n<200].T10_flip.mean():.3f} random {nc[nc.rand_n<200].rand_flip.mean():.3f}; in complete ones: temporal {nc[nc.rand_n==200].T10_flip.mean():.3f} random {nc[nc.rand_n==200].rand_flip.mean():.3f}")
# paired sign test / McNemar-ish: networks with temporal flip vs random prob
print(f"   median random flip prob {nc.rand_flip.median():.3f}; share of networks where random prob > 0.5: {(nc.rand_flip > .5).mean():.3f}")
# secondary
for name in ["S1", "S2", "S3"]:
    x = P[P[name + "_ok"]]; kk = int(x[f"{name}_flip"].sum()); nn = len(x); lo, hi = wilson(kk, nn)
    both = int(((x[f"{name}_flip"] == 1) | (x[f"{name}_new_top"] == 1)).sum())
    mp_, ret_ = x[f"{name}_pbest_top"].mean(), 1 - x[f"{name}_flip"].mean()
    print(f"{name}: {kk}/{nn} = {kk/nn:.3f} [{lo:.3f}, {hi:.3f}]  with new entrants {both/nn:.3f}; mean pbest {mp_:.3f} retention {ret_:.3f} gap {mp_-ret_:.3f}")
print(f"Kendall median {P.T10_kendall.median():.3f}; T10 median tranche share: {hold.loc[P.record, 'T10_share'].median():.4f}")
# iv sensitivity
A = df[df.T10_ok]; k, n = int(A.T10_flip.sum()), len(A); print(f"with iv: {k}/{n} = {k/n:.4f}")
H = df[df.T10_ok & ((df.set == "primary") | (df.confidence == "high"))]; k, n = int(H.T10_flip.sum()), len(H); print(f"with iv high: {k}/{n} = {k/n:.4f}")
# calibration bins
for a, b in [(0, .2), (.2, .4), (.4, .6), (.6, .8), (.8, 1.01)]:
    x = P[(P.T10_pbest_top >= a) & (P.T10_pbest_top < b)]
    print(f"bin {a}-{b}: n={len(x)} mean pbest {x.T10_pbest_top.mean():.3f} retention {1 - x.T10_flip.mean():.3f}")
# cases where keep < pre trts
print("T10 fits where pre-update treatments are not all in the full fit:", int((P.T10_n_keep < P.T10_n_pre).sum()))
