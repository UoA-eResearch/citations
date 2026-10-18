"""Reviewer check 5/7: recompute every headline number from data/items.jsonl and data/runs.jsonl without importing
code/analysis.py. Prints a comparison with results/tables/primary.json and the report's tables.
Run: venv/bin/python -I review/reviewer_checks/01_recompute.py"""
import json, collections, math, random
from pathlib import Path
import numpy as np, pandas as pd

RUN = Path(__file__).resolve().parents[2]
it = pd.DataFrame([json.loads(l) for l in open(RUN / "data/items.jsonl")])
raw = [json.loads(l) for l in open(RUN / "data/runs.jsonl")]
rn = pd.DataFrame(raw)
P = json.load(open(RUN / "results/tables/primary.json"))

def wilson(k, n, z=1.959964):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h

print("== counts ==")
print("items", len(it), "runs", len(rn), "dup (id,cond)", rn.duplicated(["id", "condition"]).sum())
print("item cells:", sorted(collections.Counter(zip(it.jurisdiction, it.family, it.answer)).items()))
err = rn[rn.answer.isna()]
print("errors", len(err)); print(err.to_string())
print("conditions:", rn.condition.value_counts().to_dict())
# every item has zero/retrieval/abstain exactly once?
cov = rn[rn.condition.isin(["zero", "retrieval", "abstain"])].groupby("id").condition.nunique()
print("items with all 3 main conditions:", (cov == 3).sum(), "of", len(it))
# paraphrase set reproduces run.py's draw?
items_list = [json.loads(l) for l in open(RUN / "data/items.jsonl")]
para_ids = set(x["id"] for x in random.Random(20261018).sample(items_list, 100))
print("paraphrase ids match run.py draw:", para_ids == set(rn[rn.condition == "paraphrase"].id))

d = rn.merge(it[["id", "family", "jurisdiction", "chemical", "answer"]].rename(columns={"answer": "truth"}), on="id")
d["ok"] = (d.answer == d.truth)
d["yes"] = d.answer == "yes"

print("\n== accuracy by cell vs primary.json accuracy_by_cell ==")
acc = d.groupby(["condition", "jurisdiction", "family"]).ok.agg(["size", "mean"])
bad = 0
for (c, j, f), r in acc.iterrows():
    ref = P["accuracy_by_cell"].get(f"{c}|{j}|{f}")
    flag = "" if ref is not None and abs(ref - round(r["mean"], 3)) < 1e-9 else "  <-- MISMATCH"
    if flag: bad += 1
    print(f"{c:10s} {j} {f} n={int(r['size']):4d} acc={r['mean']:.3f} ref={ref}{flag}")
print("mismatches:", bad)

print("\n== H1 cluster bootstrap (own implementation; same seed sequence as analysis.py, then a second seed) ==")
def gap(x, cond):
    y = x[x.condition == cond]
    return y[y.jurisdiction == "NZ"].ok.mean() - y[y.jurisdiction == "AU"].ok.mean()

def boot(fams, rng, B=2000):
    ab = d[d.family.isin(fams) & d.condition.isin(["zero", "retrieval"])]
    chems = sorted(ab.chemical.unique())
    grp = {c: x for c, x in ab.groupby("chemical")}
    g0s, g1s = [], []
    for _ in range(B):
        pick = rng.choice(chems, len(chems))
        s = pd.concat([grp[c] for c in pick])
        g0s.append(gap(s, "zero")); g1s.append(gap(s, "retrieval"))
    return gap(ab, "zero"), np.percentile(g0s, [2.5, 97.5]), gap(ab, "retrieval"), np.percentile(g1s, [2.5, 97.5]), len(chems)

rng = np.random.default_rng(20261018)
for fams, key in ((["b"], "H1"), (["a", "b"], "H1_pooled_ab")):
    g0, ci0, g1, ci1, nch = boot(fams, rng)
    print(f"{'+'.join(fams)}: chemicals={nch} gap0={g0:+.4f} CI=({ci0[0]:+.4f},{ci0[1]:+.4f})  ref gap={P[key]['gap']:+.4f} CI=({P[key]['ci'][0]:+.4f},{P[key]['ci'][1]:+.4f})"
          f" | retrieval gap={g1:+.4f} CI=({ci1[0]:+.4f},{ci1[1]:+.4f})")
rng2 = np.random.default_rng(7)
for fams in (["b"], ["a", "b"]):
    g0, ci0, g1, ci1, nch = boot(fams, rng2)
    print(f"seed 7 {'+'.join(fams)}: gap0={g0:+.4f} CI=({ci0[0]:+.4f},{ci0[1]:+.4f})")
# a naive (unclustered) normal-approx CI for the (b) zero-shot gap, for scale
z = d[(d.family == "b") & (d.condition == "zero")]
pn, pa = z[z.jurisdiction == "NZ"].ok, z[z.jurisdiction == "AU"].ok
se = math.sqrt(pn.var(ddof=1) / len(pn) + pa.var(ddof=1) / len(pa))
print(f"(b) naive unclustered CI: {pn.mean()-pa.mean():+.4f} +/- {1.96*se:.4f}")

print("\n== H3 ==")
cf = d[(d.family == "d") & (d.truth == "no")]
scr = pd.read_csv(RUN / "results/tables/nz_counterfactual_screen.csv")
print("screen labels:", scr.screen.value_counts().to_dict())
keep = set(scr[scr.screen == "distinct"].id)
for lab, m in (("NZ all 100", (cf.jurisdiction == "NZ")), ("NZ screened", (cf.jurisdiction == "NZ") & cf.id.isin(keep)),
               ("NZ overlapping", (cf.jurisdiction == "NZ") & ~cf.id.isin(keep)), ("AU all 100", (cf.jurisdiction == "AU"))):
    for cond in ("zero", "retrieval", "abstain", "paraphrase"):
        x = cf[m & (cf.condition == cond)]
        if len(x) == 0: continue
        k = int(x.yes.sum()); lo, hi = wilson(k, len(x))
        extra = f" not_stated={int((x.answer=='not stated').sum())}" if cond == "abstain" else ""
        print(f"{lab:16s} {cond:10s} yes={k:3d}/{len(x):3d} = {k/len(x):.3f} Wilson=({lo:.3f},{hi:.3f}){extra}")
tc = d[(d.family == "d") & (d.truth == "yes")]
for j in ("NZ", "AU"):
    for cond in ("zero", "retrieval", "abstain"):
        x = tc[(tc.jurisdiction == j) & (tc.condition == cond)]
        print(f"true criteria {j} {cond:10s} yes={int(x.yes.sum())}/{len(x)} = {x.yes.mean():.3f}")

print("\n== zero-shot yes-rates by truth (report table 'Response bias') ==")
z = d[d.condition == "zero"]
for f in "abd":
    for j in ("NZ", "AU"):
        y1 = z[(z.family == f) & (z.jurisdiction == j) & (z.truth == "yes")].yes
        y0 = z[(z.family == f) & (z.jurisdiction == j) & (z.truth == "no")].yes
        print(f"({f}) {j}: yes|truth=yes {y1.mean():.3f} (n={len(y1)})  yes|truth=no {y0.mean():.3f} (n={len(y0)})")

print("\n== retrieval errors by cell (truth x answer) ==")
r = d[d.condition == "retrieval"]
for (j, f), x in r.groupby(["jurisdiction", "family"]):
    wrong = x[~x.ok]
    print(f"{j} ({f}): wrong={len(wrong)}  by truth->answer:", collections.Counter(zip(wrong.truth, wrong.answer.fillna('ERR'))))

print("\n== abstention ==")
a = d[d.condition == "abstain"]
for (j, f, t), x in a.groupby(["jurisdiction", "family", "truth"]):
    ns = (x.answer == "not stated").mean()
    ans = x[(x.answer != "not stated") & x.answer.notna()]
    print(f"{j} ({f}) truth={t:3s} n={len(x):3d} not_stated={ns:.3f}  acc among answered={ans.ok.mean():.3f} (n={len(ans)})")
for j, x in a.groupby("jurisdiction"):
    ans = x[(x.answer != "not stated") & x.answer.notna()]
    print(f"{j}: not_stated={(x.answer=='not stated').mean():.3f} acc_answered={ans.ok.mean():.3f} (ref {P['abstention'][j]})")

print("\n== paraphrase ==")
pz = d[d.condition.isin(["zero", "paraphrase"])].pivot_table(index="id", columns="condition", values="answer", aggfunc="first")
pz = pz.join(it.set_index("id")[["family", "jurisdiction", "answer"]].rename(columns={"answer": "truth"}))
print("n=", len(pz), "both answered=", pz.dropna(subset=["zero", "paraphrase"]).shape[0])
pq = pz.dropna(subset=["zero", "paraphrase"])
print("agree=", (pq.zero == pq.paraphrase).mean(), " zero acc=", (pq.zero == pq.truth).mean(), " para acc=", (pq.paraphrase == pq.truth).mean())
print("agreement by family:", pq.assign(ag=pq.zero == pq.paraphrase).groupby("family").ag.agg(["size", "mean"]).to_dict())
print("paraphrase cells:", collections.Counter(zip(pq.jurisdiction, pq.family)))
# does paraphrase change the H1 (b) picture? zero vs paraphrase acc by jurisdiction on the (b) subset
for f in "abd":
    s = pq[pq.family == f]
    for j in ("NZ", "AU"):
        t = s[s.jurisdiction == j]
        if len(t): print(f"  ({f}) {j}: n={len(t)} zero acc={(t.zero==t.truth).mean():.2f} para acc={(t.paraphrase==t.truth).mean():.2f}")
