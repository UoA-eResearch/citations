"""Recompute the numbers affected by (1) the broken largest-component rule, using the reviewer's re-run of the failed
fits (cache/refit_failed.jsonl), and (2) the two disputed contrast-level direction calls (cache/refit_corrected_direction.jsonl)."""
import json, math, numpy as np, pandas as pd
from scipy.stats import norm
RUN = "/mnt/citations/research-lab/runs/future-health-nma-rank-temporal-fragility"
dr = pd.read_csv(f"{RUN}/results/tables/direction.csv", dtype={"record": str}).set_index("record")
hold = pd.read_csv(f"{RUN}/data/holdouts.csv", dtype={"record": str}).set_index("record")
rng = np.random.default_rng(2)
def pscore(TE, se, trts, keep, small):
    idx = [trts.index(t) for t in keep]; A = np.asarray(TE, float)[np.ix_(idx, idx)]; S = np.asarray(se, float)[np.ix_(idx, idx)]
    s = 1 if small == "good" else -1
    with np.errstate(all="ignore"): z = norm.cdf(s * (-A) / S)
    np.fill_diagonal(z, np.nan); return dict(zip(keep, np.nanmean(z, axis=1)))
def top(d): return max(d, key=lambda k: (d[k], k))
def wilson(k, n, z=1.959964):
    p = k / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den; return c - h, c + h
fits = {}
for line in open(f"{RUN}/data/fits.jsonl"):
    r = json.loads(line); fits[r["record"]] = {f["name"]: f for f in r["fits"]}
redo = {}
for line in open(f"{RUN}/review/reviewer_checks/cache/refit_failed.jsonl"):
    r = json.loads(line); redo[(r["record"], r["name"])] = r
print("re-run fits:", len(redo), "; still failing:", sum(1 for r in redo.values() if r.get("error")))
# patch in the re-run fits
for (rec, name), r in redo.items():
    if not r.get("error"): fits[rec][name] = r
def res(full, pre, small):
    keep = [t for t in pre["trts"] if t in full["trts"]]
    pre_ps = dict(zip(pre["trts"], pre["pscore"])); pre_ps = {t: pre_ps[t] for t in keep}
    fs = pscore(full["TE"], full["seTE"], full["trts"], keep, small)
    fa = pscore(full["TE"], full["seTE"], full["trts"], full["trts"], small)
    pt, ft = top(pre_ps), top(fs)
    out = dict(flip=int(pt != ft), new_top=int(top(fa) not in keep), pre_top=pt, k_pre=pre["n_studies"])
    if "pbest" in pre: pb = dict(zip(pre.get("pbest_trts", pre["trts"]), pre["pbest"])); out["pbest_top"] = pb[pt]
    return out
rows = []
for rec, F in fits.items():
    full = F["full"]
    if full.get("error"): continue
    small = dr.loc[rec, "small_values"]; row = dict(record=rec, set=hold.loc[rec, "set"], confidence=dr.loc[rec, "confidence"])
    for name in ["T10", "S1", "S2", "S3"]:
        pre = F.get(name)
        if pre is None or pre.get("error"): row[name + "_ok"] = False; continue
        row[name + "_ok"] = True
        for k, v in res(full, pre, small).items(): row[f"{name}_{k}"] = v
    fl = [res(full, F[n], small)["flip"] for n in F if n.startswith("R") and not F[n].get("error")]
    row["rand_n"] = len(fl); row["rand_flip"] = np.mean(fl)
    rows.append(row)
df = pd.DataFrame(rows)
P = df[(df.set == "primary") & df.T10_ok]
print(f"\n== With the largest-component rule applied as preregistered ==")
k, n = int(P.T10_flip.sum()), len(P); lo, hi = wilson(k, n); print(f"H1: {k}/{n} = {k/n:.4f} [{lo:.4f}, {hi:.4f}]")
print("501229 T10 result:", df[df.record == "501229"][["T10_flip", "T10_new_top", "T10_pbest_top", "T10_k_pre"]].to_dict("records"))
mp, ret = P.T10_pbest_top.mean(), 1 - P.T10_flip.mean(); print(f"H2: mean pbest {mp:.4f} retention {ret:.4f} gap {mp-ret:.4f}")
nc = P; d = nc.T10_flip - nc.rand_flip; vals = [d.iloc[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)]
print(f"NC: temporal {nc.T10_flip.mean():.4f} random {nc.rand_flip.mean():.4f} diff {d.mean():.4f} [{np.percentile(vals,2.5):.4f}, {np.percentile(vals,97.5):.4f}]; random fits used {int(nc.rand_n.sum())}")
# flip rate among the re-run random fits alone (the disconnected holdouts)
rr = [(rec, name, res(fits[rec]["full"], r, dr.loc[rec, "small_values"])["flip"]) for (rec, name), r in redo.items() if not r.get("error") and name.startswith("R") and hold.loc[rec, "set"] == "primary"]
print(f"   flip rate within the {len(rr)} previously failed (disconnected) random holdouts of primary networks: {np.mean([x[2] for x in rr]):.3f}")
for name in ["S1", "S2", "S3"]:
    x = P[P[name + "_ok"]]; kk = int(x[f"{name}_flip"].sum()); nn = len(x); lo, hi = wilson(kk, nn)
    print(f"{name}: {kk}/{nn} = {kk/nn:.3f} [{lo:.3f}, {hi:.3f}]; mean pbest {x[f'{name}_pbest_top'].mean():.3f} retention {1 - x[f'{name}_flip'].mean():.3f}")
# (2) corrected directions for 501220 and 501274
corr = {}
for line in open(f"{RUN}/review/reviewer_checks/cache/refit_corrected_direction.jsonl"):
    r = json.loads(line); corr[(r["record"], r["name"])] = r
for rec in ["501220", "501274"]:
    old = res(fits[rec]["full"], fits[rec]["T10"], dr.loc[rec, "small_values"]) if fits[rec]["T10"].get("trts") else None
    new = res(corr[(rec, "full")], corr[(rec, "T10")], "bad")
    print(f"\n{rec}: study's call -> {old}; corrected ('bad') -> {new}")
    df.loc[df.record == rec, ["T10_flip", "T10_new_top", "T10_pbest_top"]] = [new["flip"], new["new_top"], new["pbest_top"]]
    df.loc[df.record == rec, "T10_ok"] = True
A = df[df.T10_ok]; k, n = int(A.T10_flip.sum()), len(A); print(f"\niv sensitivity (all, corrected directions + fixed component rule): {k}/{n} = {k/n:.4f}; mean pbest {A.T10_pbest_top.mean():.3f} retention {1-A.T10_flip.mean():.3f}")
H = df[df.T10_ok & ((df.set == "primary") | (df.confidence == "high"))]; k, n = int(H.T10_flip.sum()), len(H); print(f"iv high-confidence set: {k}/{n} = {k/n:.4f}")
df.to_csv(f"{RUN}/review/reviewer_checks/recomputed_with_fixes.csv", index=False)
