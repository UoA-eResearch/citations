"""Reviewer check 2: recompute P1-P5, the baselines, the bootstraps and the verdict from
results/tables/pairs_panel.csv, without importing code/analysis.py.

Deliberate independence: matrices are rebuilt from the tidy CSV (not from predictions.jsonl via
assemble.matrices), Spearman is computed with a hand-rolled tie-corrected rank correlation checked
against scipy, and the bootstrap is re-seeded from scratch.
"""
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RUN = Path("/mnt/citations/research-lab/runs/cheminformatics-drug-discovery-cofold-selectivity")
TAB = RUN / "results" / "tables"
CENSOR_NM = 10000.0
SEED = 20261013
NBOOT = 2000

# ---------------------------------------------------------------- build matrices from the tidy CSV
t = pd.read_csv(TAB / "pairs_panel.csv")
assert len(t) == 1024, len(t)
P = json.load(open(RUN / "data" / "panel.json"))
cids = [c["cid"] for c in P["ligands"]]          # panel order (int-sorted by cid in panel.json)
accs = [k["acc"] for k in P["kinases"]]
t["cid"] = t.cid.astype(str)
pred = t.pivot_table(index="cid", columns="protein", values="pred_pic50").loc[cids, accs].to_numpy(float)
prob = t.pivot_table(index="cid", columns="protein", values="prob_binary").loc[cids, accs].to_numpy(float)
meas = t.pivot_table(index="cid", columns="protein", values="pkd").loc[cids, accs].to_numpy(float)
cens = t.pivot_table(index="cid", columns="protein", values="censored").loc[cids, accs].to_numpy(float)
conf = t.pivot_table(index="cid", columns="protein", values="confidence_score").loc[cids, accs].to_numpy(float)
print(f"matrices {pred.shape}; nan in pred {np.isnan(pred).sum()}; nan in meas {np.isnan(meas).sum()}")
print(f"censored share {cens.mean():.6f}; cells at pkd 5.0 exactly {(meas == 5.0).mean():.6f}")

# cross-check the measured matrix against the raw Davis pickle
Y = np.asarray(pickle.load(open(RUN / "data" / "davis_Y", "rb"), encoding="latin1"), float)
rows_i = [c["row"] for c in P["ligands"]]
cols_i = [k["col"] for k in P["kinases"]]
meas_raw = 9.0 - np.log10(Y[np.ix_(rows_i, cols_i)])
print(f"measured matrix matches raw Davis pickle: {np.allclose(meas, meas_raw)}  "
      f"max abs diff {np.nanmax(np.abs(meas - meas_raw)):.2e}")


# ---------------------------------------------------------------- estimators (independent)
def my_spearman(x, y):
    """Tie-corrected Spearman from first principles: Pearson on average ranks."""
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if x.size < 3 or np.unique(y).size < 2 or np.unique(x).size < 2:
        return np.nan
    rx, ry = stats.rankdata(x), stats.rankdata(y)
    return float(np.corrcoef(rx, ry)[0, 1])


def rho(x, y, zero_if_flat=True):
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3 or np.unique(y[m]).size < 2:
        return np.nan
    if np.unique(x[m]).size < 2:
        return 0.0 if zero_if_flat else np.nan
    return my_spearman(x, y)


def within_lig(p, y, unc_only=False, min_unc=5):
    out = np.full(p.shape[0], np.nan)
    for i in range(p.shape[0]):
        a, b = p[i], y[i]
        if unc_only:
            keep = b > 5.0
            if keep.sum() < min_unc:
                continue
            a, b = a[keep], b[keep]
        out[i] = rho(a, b)
    return out


def within_kin(p, y):
    return np.array([rho(p[:, j], y[:, j]) for j in range(p.shape[1])])


def med(v):
    v = np.asarray(v, float)
    return float(np.nanmedian(v)) if np.isfinite(v).any() else np.nan


def boot_ci(stat_fn, n, seed, nboot=NBOOT):
    rng = np.random.default_rng(seed)
    d = np.array([stat_fn(rng.integers(0, n, n)) for _ in range(nboot)])
    d = d[np.isfinite(d)]
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


# sanity: my_spearman vs scipy on the real data
r_mine = within_lig(pred, meas)
r_scipy = np.array([stats.spearmanr(pred[i], meas[i]).statistic for i in range(32)])
print(f"my Spearman vs scipy spearmanr, max abs diff over 32 ligands: "
      f"{np.nanmax(np.abs(r_mine - r_scipy)):.2e}\n")

res = {}
# ---- P1
r1 = within_lig(pred, meas)
res["P1"] = (med(r1),) + boot_ci(lambda ix: med(r1[ix]), 32, SEED)
# ---- P2
r2 = within_lig(pred, meas, unc_only=True)
res["P2"] = (med(r2),) + boot_ci(lambda ix: med(r2[ix]), 32, SEED)
print(f"P2 defined for {np.isfinite(r2).sum()} of 32 ligands")
# ---- P3
r3 = within_kin(pred, meas)
res["P3"] = (med(r3), np.nan, np.nan)
# ---- P4
def hitvec(p, y, top=3):
    n = p.shape[0]
    t1, p3 = np.full(n, np.nan), np.full(n, np.nan)
    sizes = []
    for i in range(n):
        yy, pp = y[i], p[i]
        if np.unique(yy).size < 2:
            continue
        cut = np.sort(yy)[-top]
        true = set(np.where(yy >= cut)[0])
        sizes.append(len(true))
        order = np.argsort(-pp)
        t1[i] = float(order[0] in true)
        p3[i] = len(set(order[:top]) & true) / top
    return t1, p3, sizes


h1, h3, sizes = hitvec(pred, meas)
res["P4_top1"] = (float(np.nanmean(h1)), np.nan, np.nan)
res["P4_p3"] = (float(np.nanmean(h3)), np.nan, np.nan)
print(f"true-top-3 set size per ligand: min {min(sizes)} median {int(np.median(sizes))} "
      f"max {max(sizes)} mean {np.mean(sizes):.2f}  (chance top-1 = mean size / 32 = "
      f"{np.mean(sizes) / 32:.4f}; report quotes 0.094 = 3/32)")

# ---- P5 two-way
def two_way(m):
    mu = np.nanmean(m)
    a = np.nanmean(m, 1) - mu
    b = np.nanmean(m, 0) - mu
    fa = np.repeat(a[:, None], m.shape[1], 1)
    fb = np.repeat(b[None, :], m.shape[0], 0)
    e = m - mu - fa - fb
    tot = np.nansum((m - mu) ** 2)
    return (np.nansum(fa ** 2) / tot, np.nansum(fb ** 2) / tot, np.nansum(e ** 2) / tot)


tw_p, tw_m = two_way(pred), two_way(meas)
print(f"\nP5 predicted  ligand {tw_p[0]:.4f} kinase {tw_p[1]:.4f} interaction {tw_p[2]:.4f} "
      f"(sum {sum(tw_p):.4f})")
print(f"P5 measured   ligand {tw_m[0]:.4f} kinase {tw_m[1]:.4f} interaction {tw_m[2]:.4f} "
      f"(sum {sum(tw_m):.4f})")

# ---- sensitivity bootstraps
rng = np.random.default_rng(SEED + 1)
kb = [med(within_lig(pred[:, c], meas[:, c])) for c in (rng.integers(0, 32, 32) for _ in range(500))]
res["P1_kinase_boot"] = (np.nan, float(np.percentile(kb, 2.5)), float(np.percentile(kb, 97.5)))
rng = np.random.default_rng(SEED + 2)
db = []
for _ in range(500):
    ri, cj = rng.integers(0, 32, 32), rng.integers(0, 32, 32)
    db.append(med(within_lig(pred[np.ix_(ri, cj)], meas[np.ix_(ri, cj)])))
res["P1_dyadic_boot"] = (np.nan, float(np.percentile(db, 2.5)), float(np.percentile(db, 97.5)))

# ---- probability head
rp = within_lig(prob, meas)
res["P1_probability"] = (med(rp),) + boot_ci(lambda ix: med(rp[ix]), 32, SEED)
res["P3_probability"] = (med(within_kin(prob, meas)), np.nan, np.nan)

# ---- high confidence half
cut = np.nanmedian(t.confidence_score)
hi = np.where(conf >= cut, pred, np.nan)
rh = within_lig(hi, meas)
res["P1_high_conf"] = (med(rh),) + boot_ci(lambda ix: med(rh[ix]), 32, SEED)
print(f"\nhigh-confidence cut {cut:.6f}; cells kept {np.isfinite(hi).sum()} of 1024")

# ---------------------------------------------------------------- baselines
Ypkd = 9.0 - np.log10(Y)
rows, cols = rows_i, cols_i
sub_all = Ypkd[:, cols]            # 68 x 32

B0 = np.repeat(np.nanmean(Ypkd[rows], 1)[:, None], 32, 1)
B1 = np.empty((32, 32))
for a, i in enumerate(rows):
    keep = np.ones(68, bool)
    keep[i] = False
    B1[a] = sub_all[keep].mean(0)
B1_full = np.repeat(sub_all.mean(0)[None, :], 32, 0)
mw = np.array([c["mw"] for c in P["ligands"]], float)
B3 = np.repeat(mw[:, None], 32, 1)

from rdkit import Chem, DataStructs, RDLogger  # noqa: E402
from rdkit.Chem import rdFingerprintGenerator  # noqa: E402
RDLogger.DisableLog("rdApp.*")
lig_all = list(json.load(open(RUN / "data" / "davis_ligands_iso.txt")).items())
gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
fps = [gen.GetFingerprint(Chem.MolFromSmiles(s)) for _, s in lig_all]
B2 = np.empty((32, 32))
nbrs = []
for a, i in enumerate(rows):
    sims = np.array(DataStructs.BulkTanimotoSimilarity(fps[i], fps))
    sims[i] = -1
    j = int(np.argsort(-sims)[0])
    nbrs.append((lig_all[i][0], lig_all[j][0], round(float(sims[j]), 3)))
    B2[a] = sub_all[j]

print("\n==== baselines, selectivity axis (P1) ====")
bl = {}
for name, B in (("B0_ligand_only", B0), ("B1_promiscuity", B1), ("B2_neighbour", B2), ("B3_mw", B3)):
    rb = within_lig(B, meas)
    rb2 = within_lig(B, meas, unc_only=True)
    hb1, hb3, _ = hitvec(B, meas)
    pt, lo, hi_ = med(rb), *boot_ci(lambda ix: med(rb[ix]), 32, SEED)
    # paired difference, same bootstrap indices as the model
    dpt = med(r1) - med(rb)
    dlo, dhi = boot_ci(lambda ix: med(r1[ix]) - med(rb[ix]), 32, SEED)
    h1lo, h1hi = boot_ci(lambda ix: float(np.nanmean(h1[ix]) - np.nanmean(hb1[ix])), 32, SEED)
    h3lo, h3hi = boot_ci(lambda ix: float(np.nanmean(h3[ix]) - np.nanmean(hb3[ix])), 32, SEED)
    # P2 paired difference (NOT in the report)
    d2pt = med(r2) - med(rb2)
    d2lo, d2hi = boot_ci(lambda ix: med(r2[ix]) - med(rb2[ix]), 32, SEED)
    bl[name] = dict(P1=(pt, lo, hi_), P2=med(rb2), P3=med(within_kin(B, meas)),
                    top1=float(np.nanmean(hb1)), p3=float(np.nanmean(hb3)),
                    dP1=(dpt, dlo, dhi), dtop1=(float(np.nanmean(h1) - np.nanmean(hb1)), h1lo, h1hi),
                    dp3=(float(np.nanmean(h3) - np.nanmean(hb3)), h3lo, h3hi),
                    dP2=(d2pt, d2lo, d2hi),
                    worst=float(np.nanmin(rb)), n_below0=int((rb < 0).sum()),
                    n_below025=int((rb < 0.25).sum()))
    print(f"  {name:16s} P1 {pt:+.4f} [{lo:+.4f},{hi_:+.4f}]  P2 {med(rb2):+.4f}  "
          f"P3 {med(within_kin(B, meas)):+.4f}  top1 {np.nanmean(hb1):.4f}  p@3 {np.nanmean(hb3):.4f}")
    print(f"  {'':16s} dP1 {dpt:+.4f} [{dlo:+.4f},{dhi:+.4f}]   "
          f"dP2 {d2pt:+.4f} [{d2lo:+.4f},{d2hi:+.4f}]   "
          f"dtop1 {np.nanmean(h1) - np.nanmean(hb1):+.4f} [{h1lo:+.4f},{h1hi:+.4f}]")

print(f"\nB1 within-kinase using the LOO version: {med(within_kin(B1, meas)):+.6f}")
print(f"B1 within-kinase using the no-LOO version: {med(within_kin(B1_full, meas)):+.6f}")
print(f"B1 on the SELECTIVITY axis without LOO: P1 = {med(within_lig(B1_full, meas)):+.4f}  "
      f"(with LOO {med(within_lig(B1, meas)):+.4f})")
print(f"B1-no-LOO P2 = {med(within_lig(B1_full, meas, unc_only=True)):+.4f}")
print("\nB2 nearest neighbours (cid, neighbour cid, tanimoto), first 8:", nbrs[:8])
print(f"B2 tanimoto: min {min(n[2] for n in nbrs)} median {np.median([n[2] for n in nbrs]):.3f} "
      f"max {max(n[2] for n in nbrs)}")

# model floor
print(f"\n==== per-ligand floor ====")
print(f"model worst {np.nanmin(r1):+.4f}  below 0: {(r1 < 0).sum()}  below 0.25: {(r1 < 0.25).sum()}")
for n in ("B1_promiscuity", "B2_neighbour"):
    print(f"{n:16s} worst {bl[n]['worst']:+.4f}  below 0: {bl[n]['n_below0']}  "
          f"below 0.25: {bl[n]['n_below025']}")
# does the floor survive uncensored-only?
print(f"\nuncensored-only (P2) floors: model {np.nanmin(r2):+.4f} ({(r2 < 0).sum()} below 0); "
      f"B1 {np.nanmin(within_lig(B1, meas, unc_only=True)):+.4f} "
      f"({(within_lig(B1, meas, unc_only=True) < 0).sum()} below 0); "
      f"B2 {np.nanmin(within_lig(B2, meas, unc_only=True)):+.4f} "
      f"({(within_lig(B2, meas, unc_only=True) < 0).sum()} below 0)")

# ---------------------------------------------------------------- verdict
p1_pt, p1_lo, p1_hi = res["P1"]
v = "Refuted" if p1_lo >= 0.25 else ("Supported" if p1_hi < 0.25 and res["P3"][0] >= 0.4
                                     else "Inconclusive")
print(f"\n==== verdict ====\nP1 {p1_pt:.4f} [{p1_lo:.4f},{p1_hi:.4f}]  P3 {res['P3'][0]:.4f} -> {v}")
print(f"protein-blind label (interval includes 0): {p1_lo <= 0 <= p1_hi}")

# ---------------------------------------------------------------- spread / compression
print(f"\n==== compression ====")
print(f"median within-ligand SD: pred {np.median(np.nanstd(pred, 1)):.4f} "
      f"meas {np.median(np.nanstd(meas, 1)):.4f}")
print(f"whole-panel SD: pred {np.nanstd(pred):.4f} meas {np.nanstd(meas):.4f}")

# ---------------------------------------------------------------- store
out = {k: [None if not np.isfinite(x) else round(float(x), 6) for x in v] for k, v in res.items()}
out["baselines"] = {k: {kk: ([round(float(x), 6) for x in vv] if isinstance(vv, tuple)
                            else round(float(vv), 6) if isinstance(vv, float) else vv)
                        for kk, vv in v.items()} for k, v in bl.items()}
out["P5_pred"], out["P5_meas"] = [round(x, 6) for x in tw_p], [round(x, 6) for x in tw_m]
out["per_ligand_model_P1"] = [round(float(x), 6) for x in r1]
json.dump(out, open(Path(__file__).parent / "recomputed.json", "w"), indent=1)
print("\nwrote recomputed.json")
