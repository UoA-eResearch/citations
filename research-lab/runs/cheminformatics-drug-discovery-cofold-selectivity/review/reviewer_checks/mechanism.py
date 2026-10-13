"""Reviewer check 3: what is actually driving the P1 / hit-rate disagreement?

(a) split the within-ligand signal into binder-vs-nonbinder discrimination (AUC over the censored block)
    and ordering among real numbers (concordance among uncensored cells only);
(b) rank-weighted statistics (NDCG, AUC restricted to the top of the profile) to test whether they side
    with P1 or with top-1;
(c) McNemar on the top-1 indicators as an exact cross-check of the paired bootstrap;
(d) whether B0/B3 hit rates are artefacts of the kinase column ordering;
(e) whether the "never below zero" floor claim survives the uncensored-only subset.
"""
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RUN = Path("/mnt/citations/research-lab/runs/cheminformatics-drug-discovery-cofold-selectivity")
TAB = RUN / "results" / "tables"
SEED = 20261013

t = pd.read_csv(TAB / "pairs_panel.csv")
P = json.load(open(RUN / "data" / "panel.json"))
cids = [c["cid"] for c in P["ligands"]]
accs = [k["acc"] for k in P["kinases"]]
t["cid"] = t.cid.astype(str)
pv = lambda col: t.pivot_table(index="cid", columns="protein", values=col).loc[cids, accs].to_numpy(float)
pred, prob, meas = pv("pred_pic50"), pv("prob_binary"), pv("pkd")
cens = meas <= 5.0

Y = np.asarray(pickle.load(open(RUN / "data" / "davis_Y", "rb"), encoding="latin1"), float)
Ypkd = 9.0 - np.log10(Y)
rows = [c["row"] for c in P["ligands"]]
cols = [k["col"] for k in P["kinases"]]
sub_all = Ypkd[:, cols]
B1 = np.empty((32, 32))
for a, i in enumerate(rows):
    keep = np.ones(68, bool); keep[i] = False
    B1[a] = sub_all[keep].mean(0)
B0 = np.repeat(np.nanmean(Ypkd[rows], 1)[:, None], 32, 1)
mwv = np.array([c["mw"] for c in P["ligands"]], float)
B3 = np.repeat(mwv[:, None], 32, 1)
from rdkit import Chem, DataStructs, RDLogger  # noqa: E402
from rdkit.Chem import rdFingerprintGenerator  # noqa: E402
RDLogger.DisableLog("rdApp.*")
lig_all = list(json.load(open(RUN / "data" / "davis_ligands_iso.txt")).items())
gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
fps = [gen.GetFingerprint(Chem.MolFromSmiles(s)) for _, s in lig_all]
B2 = np.empty((32, 32))
for a, i in enumerate(rows):
    s = np.array(DataStructs.BulkTanimotoSimilarity(fps[i], fps)); s[i] = -1
    B2[a] = sub_all[int(np.argsort(-s)[0])]

MODELS = dict(boltz_value=pred, boltz_prob=prob, B1_promiscuity=B1, B2_neighbour=B2,
              B0_ligand_only=B0, B3_mw=B3)


def auc(scores, labels):
    """AUC of scores for separating labels==1 from labels==0 (ties get 0.5)."""
    pos, neg = scores[labels == 1], scores[labels == 0]
    if pos.size == 0 or neg.size == 0:
        return np.nan
    d = pos[:, None] - neg[None, :]
    return float(((d > 0).sum() + 0.5 * (d == 0).sum()) / d.size)


def concordance(s, y):
    """Share of comparable (non-tied in y) pairs ordered correctly; ties in s count 0.5."""
    ds = s[:, None] - s[None, :]
    dy = y[:, None] - y[None, :]
    ok = dy != 0
    iu = np.triu(np.ones_like(ok, bool), 1) & ok
    if iu.sum() == 0:
        return np.nan
    agree = (np.sign(ds) == np.sign(dy))[iu].sum() + 0.5 * (ds == 0)[iu].sum()
    return float(agree / iu.sum())


def ndcg(s, y, k=None):
    """NDCG with gain = max(0, pKd - 5) so the ceiling block contributes nothing."""
    g = np.maximum(y - 5.0, 0.0)
    order = np.argsort(-s)
    kk = k or len(s)
    disc = 1.0 / np.log2(np.arange(2, kk + 2))
    dcg = (g[order][:kk] * disc).sum()
    idcg = (np.sort(g)[::-1][:kk] * disc).sum()
    return float(dcg / idcg) if idcg > 0 else np.nan


print("=" * 100)
print("(a) WHERE THE WITHIN-LIGAND SIGNAL LIVES: censored-block discrimination vs ordering real numbers")
print("=" * 100)
print(f"{'predictor':16s} {'P1(all)':>9s} {'P2(unc)':>9s} {'AUC cens':>9s} {'conc unc':>9s} "
      f"{'NDCG':>8s} {'NDCG@3':>8s} {'NDCG@5':>8s}")
res = {}
for name, S in MODELS.items():
    p1, p2, au, co, nd, nd3, nd5 = [], [], [], [], [], [], []
    for i in range(32):
        s, y, c = S[i], meas[i], cens[i]
        p1.append(stats.spearmanr(s, y).statistic if np.unique(s).size > 1 else 0.0)
        u = ~c
        p2.append((stats.spearmanr(s[u], y[u]).statistic if np.unique(s[u]).size > 1 else 0.0)
                  if u.sum() >= 5 else np.nan)
        au.append(auc(s, (~c).astype(int)))               # can it tell binders from ceiling cells?
        co.append(concordance(s[u], y[u]))                # can it order the real numbers?
        nd.append(ndcg(s, y)); nd3.append(ndcg(s, y, 3)); nd5.append(ndcg(s, y, 5))
    res[name] = dict(p1=np.array(p1), p2=np.array(p2), auc=np.array(au), conc=np.array(co),
                     ndcg=np.array(nd), ndcg3=np.array(nd3), ndcg5=np.array(nd5))
    r = res[name]
    print(f"{name:16s} {np.nanmedian(r['p1']):>9.4f} {np.nanmedian(r['p2']):>9.4f} "
          f"{np.nanmedian(r['auc']):>9.4f} {np.nanmedian(r['conc']):>9.4f} "
          f"{np.nanmean(r['ndcg']):>8.4f} {np.nanmean(r['ndcg3']):>8.4f} {np.nanmean(r['ndcg5']):>8.4f}")

print("\nPaired ligand bootstrap (2000 draws, seed 20261013) of model - baseline on each statistic:")


def pboot(a, b, agg=np.nanmedian):
    rng = np.random.default_rng(SEED)
    d = np.array([agg(a[ix]) - agg(b[ix]) for ix in (rng.integers(0, 32, 32) for _ in range(2000))])
    d = d[np.isfinite(d)]
    return agg(a) - agg(b), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


for base in ("B1_promiscuity", "B2_neighbour"):
    print(f"\n  vs {base}:")
    for stat, agg in (("p1", np.nanmedian), ("p2", np.nanmedian), ("auc", np.nanmedian),
                      ("conc", np.nanmedian), ("ndcg", np.nanmean), ("ndcg3", np.nanmean),
                      ("ndcg5", np.nanmean)):
        pt, lo, hi = pboot(res["boltz_value"][stat], res[base][stat], agg)
        star = "  *EXCLUDES 0*" if (lo > 0 or hi < 0) else ""
        print(f"    {stat:6s} {pt:+.4f} ({lo:+.4f}, {hi:+.4f}){star}")

print("\n" + "=" * 100)
print("(c) TOP-1: exact McNemar cross-check of the paired bootstrap")
print("=" * 100)


def hitvec(S, top=3):
    t1 = np.full(32, np.nan)
    for i in range(32):
        y = meas[i]
        cut = np.sort(y)[-top]
        true = set(np.where(y >= cut)[0])
        t1[i] = float(np.argsort(-S[i])[0] in true)
    return t1


h = {n: hitvec(S) for n, S in MODELS.items()}
for base in ("B1_promiscuity", "B2_neighbour"):
    a, b = h["boltz_value"], h[base]
    n01 = int(((a == 0) & (b == 1)).sum()); n10 = int(((a == 1) & (b == 0)).sum())
    pval = stats.binomtest(n10, n10 + n01, 0.5).pvalue if n10 + n01 else 1.0
    print(f"  boltz vs {base:16s}: model-only hits {n10}, baseline-only hits {n01}, "
          f"both {int(((a == 1) & (b == 1)).sum())}, neither {int(((a == 0) & (b == 0)).sum())}"
          f"  -> exact McNemar p = {pval:.5f}")
print("  (32 ligands, one Bernoulli draw each; the paired bootstrap on 32 indicators is the same "
      "information)")

print("\n" + "=" * 100)
print("(d) ARE B0 / B3 HIT RATES ARTEFACTS OF THE KINASE COLUMN ORDER?")
print("=" * 100)
rng = np.random.default_rng(1)
for name in ("B0_ligand_only", "B3_mw"):
    vals = []
    for _ in range(200):
        perm = rng.permutation(32)
        S = MODELS[name][:, perm]
        mp = meas[:, perm]
        tt = []
        for i in range(32):
            cut = np.sort(mp[i])[-3]
            tt.append(float(np.argsort(-S[i])[0] in set(np.where(mp[i] >= cut)[0])))
        vals.append(np.mean(tt))
    print(f"  {name:16s} reported top-1 {np.nanmean(h[name]):.4f}; over 200 random kinase column "
          f"orders: mean {np.mean(vals):.4f}, range {min(vals):.4f}-{max(vals):.4f}")
print("  A constant predictor has no ranking; argsort returns column order, so the reported value is "
      "whichever kinases happen to sit in columns 0-2.")

print("\n" + "=" * 100)
print("(e) DOES THE 'NEVER BELOW ZERO' FLOOR SURVIVE THE UNCENSORED-ONLY SUBSET?")
print("=" * 100)
print(f"{'predictor':16s} {'P1 worst':>9s} {'<0':>4s} {'<0.25':>6s} | {'P2 worst':>9s} {'<0':>4s} "
      f"{'<0.25':>6s} | {'conc worst':>11s} {'<0.5':>5s}")
for name in ("boltz_value", "boltz_prob", "B1_promiscuity", "B2_neighbour"):
    r = res[name]
    print(f"{name:16s} {np.nanmin(r['p1']):>9.4f} {int((r['p1'] < 0).sum()):>4d} "
          f"{int((r['p1'] < 0.25).sum()):>6d} | {np.nanmin(r['p2']):>9.4f} "
          f"{int((r['p2'] < 0).sum()):>4d} {int((r['p2'] < 0.25).sum()):>6d} | "
          f"{np.nanmin(r['conc']):>11.4f} {int((r['conc'] < 0.5).sum()):>5d}")

print("\n" + "=" * 100)
print("(f) HOW MUCH OF B1's P1 IS THE CENSORED BLOCK? P1 recomputed with the ceiling cells' measured")
print("    values replaced by their true rank-ties vs removed entirely (already P2).")
print("=" * 100)
for name in ("boltz_value", "B1_promiscuity"):
    r = res[name]
    print(f"  {name:16s} median P1 (all cells) {np.nanmedian(r['p1']):.4f} -> "
          f"median P2 (uncensored) {np.nanmedian(r['p2']):.4f}  "
          f"(change {np.nanmedian(r['p2']) - np.nanmedian(r['p1']):+.4f})")
print(f"\n  median per-ligand AUC for separating the 27% ceiling block from real binders:")
print(f"    boltz value head {np.nanmedian(res['boltz_value']['auc']):.4f}   "
      f"B1 promiscuity {np.nanmedian(res['B1_promiscuity']['auc']):.4f}   "
      f"boltz prob head {np.nanmedian(res['boltz_prob']['auc']):.4f}")

json.dump({n: {k: [None if not np.isfinite(x) else round(float(x), 6) for x in v]
               for k, v in r.items()} for n, r in res.items()},
          open(Path(__file__).parent / "mechanism.json", "w"), indent=1)
print("\nwrote mechanism.json")
