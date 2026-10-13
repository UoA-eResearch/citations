"""Reviewer check 4: the geometry arm.

(a) is the "removing ligand means" centring doing anything to the distance matrix?
(b) the compression claim: the report compares a median-of-per-pair-ratios (5 near pairs, 0.57) with a
    ratio-of-medians (496 pairs, 0.50). Recompute both quantities both ways.
(c) is compression actually independent of identity? Regress log ratio on identity and test it, which is
    the check the "uniform compression" claim needs and does not have.
"""
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RUN = Path("/mnt/citations/research-lab/runs/cheminformatics-drug-discovery-cofold-selectivity")
TAB = RUN / "results" / "tables"

t = pd.read_csv(TAB / "pairs_panel.csv")
P = json.load(open(RUN / "data" / "panel.json"))
cids = [c["cid"] for c in P["ligands"]]
accs = [k["acc"] for k in P["kinases"]]
t["cid"] = t.cid.astype(str)
pv = lambda c: t.pivot_table(index="cid", columns="protein", values=c).loc[cids, accs].to_numpy(float)
pred, meas = pv("pred_pic50"), pv("pkd")
ident = pd.read_csv(TAB / "kinase_identity.csv", index_col=0)
assert list(ident.columns) == accs, "identity matrix column order differs from panel order"
ident = ident.to_numpy(float)


def centred_distance(m, centre=True):
    c = m - np.nanmean(m, axis=1, keepdims=True) if centre else m
    k = c.shape[1]
    d = np.zeros((k, k))
    for i in range(k):
        for j in range(i + 1, k):
            d[i, j] = d[j, i] = np.sqrt(np.nanmean((c[:, i] - c[:, j]) ** 2))
    return d


def tri(m):
    i, j = np.triu_indices(m.shape[0], 1)
    return m[i, j]


print("=" * 96)
print("(a) IS THE LIGAND-MEAN CENTRING A NO-OP FOR THE DISTANCE MATRIX?")
print("=" * 96)
for nm, m in (("pred", pred), ("meas", meas)):
    dc, du = centred_distance(m, True), centred_distance(m, False)
    print(f"  {nm}: max |centred - uncentred| over 496 pairs = {np.abs(tri(dc) - tri(du)).max():.3e}")
print("  -> subtracting a per-ligand constant cancels in (c[:,i] - c[:,j]); the centring step cannot")
print("     change any distance. The report describes it as if it controlled for the ligand effect.")

dp, dm = centred_distance(pred), centred_distance(meas)
print(f"\n  Mantel pred-vs-meas, centred   {stats.spearmanr(tri(dp), tri(dm)).statistic:.6f}")
print(f"  Mantel pred-vs-meas, uncentred {stats.spearmanr(tri(centred_distance(pred, False)), tri(centred_distance(meas, False))).statistic:.6f}")

print("\n" + "=" * 96)
print("(b) THE COMPRESSION CLAIM: ratio-of-medians vs median-of-ratios")
print("=" * 96)
# the report's per-pair quantity is mean |difference| over ligands, not the RMS distance
n = 32
pm, pp, idt = [], [], []
for i in range(n):
    for j in range(i + 1, n):
        pm.append(np.nanmean(np.abs(meas[:, i] - meas[:, j])))
        pp.append(np.nanmean(np.abs(pred[:, i] - pred[:, j])))
        idt.append(ident[i, j])
pm, pp, idt = np.array(pm), np.array(pp), np.array(idt)
ratio = pp / pm
print(f"  all 496 pairs:")
print(f"    median measured diff  {np.median(pm):.4f}   median predicted diff {np.median(pp):.4f}")
print(f"    RATIO OF MEDIANS      {np.median(pp) / np.median(pm):.4f}   <- the 0.50 the report quotes")
print(f"    MEDIAN OF PER-PAIR RATIOS {np.median(ratio):.4f}   <- the like-for-like comparator")
print(f"    per-pair ratio: mean {ratio.mean():.4f} sd {ratio.std():.4f} "
      f"IQR {np.percentile(ratio, 25):.4f}-{np.percentile(ratio, 75):.4f} "
      f"range {ratio.min():.4f}-{ratio.max():.4f}")
near = idt >= 0.5
print(f"\n  the 5 near pairs (identity >= 0.5):")
print(f"    median of their per-pair ratios {np.median(ratio[near]):.4f}   <- the 0.57 the report quotes")
print(f"    ratio of their medians          {np.median(pp[near]) / np.median(pm[near]):.4f}")
print(f"\n  LIKE FOR LIKE (median of per-pair ratios): near pairs {np.median(ratio[near]):.4f} vs "
      f"all pairs {np.median(ratio):.4f}  -> near pairs are compressed "
      f"{'MORE' if np.median(ratio[near]) < np.median(ratio) else 'LESS'} than average")
u = stats.mannwhitneyu(ratio[near], ratio[~near], alternative="two-sided")
print(f"  Mann-Whitney near vs rest: p = {u.pvalue:.4f} (n = 5 vs {int((~near).sum())})")

print("\n" + "=" * 96)
print("(c) IS COMPRESSION INDEPENDENT OF IDENTITY? (the test the 'uniform compression' claim lacks)")
print("=" * 96)
print(f"  Spearman(identity, per-pair ratio) over 496 pairs = "
      f"{stats.spearmanr(idt, ratio).statistic:+.4f}")
# dyadic permutation test (permute kinase labels, preserving dependence)
rng = np.random.default_rng(20261013)
obs = stats.spearmanr(idt, ratio).statistic
idm = np.zeros((n, n)); rm = np.zeros((n, n))
k = 0
for i in range(n):
    for j in range(i + 1, n):
        idm[i, j] = idm[j, i] = idt[k]; rm[i, j] = rm[j, i] = ratio[k]; k += 1
null = []
for _ in range(9999):
    p = rng.permutation(n)
    null.append(stats.spearmanr(tri(idm[np.ix_(p, p)]), tri(rm)).statistic)
null = np.array(null)
print(f"  dyadic permutation p (9999 perms) = {(1 + (np.abs(null) >= abs(obs)).sum()) / 10000:.4f}")
print(f"  null 95% band [{np.percentile(null, 2.5):+.4f}, {np.percentile(null, 97.5):+.4f}]")
# kinase bootstrap of the near-pair vs all-pair ratio difference
boot = []
for _ in range(2000):
    idx = rng.integers(0, n, n)
    keep = np.triu(np.ones((n, n), bool), 1) & (idx[:, None] != idx[None, :])
    im = idm[np.ix_(idx, idx)][keep]; rr = rm[np.ix_(idx, idx)][keep]
    if (im >= 0.5).sum() >= 2 and (im < 0.5).sum() >= 2:
        boot.append(np.median(rr[im >= 0.5]) - np.median(rr[im < 0.5]))
boot = np.array(boot)
print(f"\n  kinase bootstrap of median(ratio | near) - median(ratio | rest):")
print(f"    point {np.median(boot):+.4f}  95% ({np.percentile(boot, 2.5):+.4f}, "
      f"{np.percentile(boot, 97.5):+.4f})  share of draws > 0: {np.mean(boot > 0):.3f}  "
      f"(n draws {len(boot)})")
print("  -> an interval this wide cannot establish that compression is uniform; it cannot rule out")
print("     near pairs being compressed substantially more OR less than average.")

print("\n" + "=" * 96)
print("(d) report's near-pair table, recomputed")
print("=" * 96)
names = {k["acc"]: k["davis_name"] for k in P["kinases"]}
k = 0
for i in range(n):
    for j in range(i + 1, n):
        if ident[i, j] >= 0.5:
            print(f"  {names[accs[i]]:9s}/{names[accs[j]]:9s} ident {ident[i, j]:.3f}  "
                  f"meas {np.nanmean(np.abs(meas[:, i] - meas[:, j])):.3f}  "
                  f"pred {np.nanmean(np.abs(pred[:, i] - pred[:, j])):.3f}  "
                  f"ratio {np.nanmean(np.abs(pred[:, i] - pred[:, j])) / np.nanmean(np.abs(meas[:, i] - meas[:, j])):.2f}")
