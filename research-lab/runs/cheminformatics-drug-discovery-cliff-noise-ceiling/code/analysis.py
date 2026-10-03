#!/usr/bin/env python
"""Noise model, cliff confidence, cliff gaps and hypotheses H1-H2 (plan.md sec 3-6); H3 after null.py.

Usage: analysis.py [--variant primary|normal|t4|sigma_all|sigma_tertile|sigma_intra|n1|nall|per_target] [--stage pre|post]
  (primary applies the plan's coverage rule; 'normal' forces the Gaussian model as a sensitivity arm)
  --stage pre : noise model + molecules.parquet (needed by null.py), H1, H2, secondary
  --stage post: also H3 from results/tables/null_gaps.csv
Output (results/tables/): noise_model.csv, molecules.parquet, cliff_pairs_conf.parquet, gaps_by_target.csv,
  hypotheses_{variant}.csv, secondary.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import models as MD  # noqa: E402
import noise_eb as NE  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
NBOOT = 2000


def boot_targets(values_by_target, stat, nboot=NBOOT, seed=0):
    keys = list(values_by_target)
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(nboot):
        pick = rng.choice(len(keys), len(keys))
        out.append(stat([values_by_target[keys[k]] for k in pick]))
    return np.nanpercentile(out, [2.5, 97.5])


def noise_model(chembl, variant):
    pairs = NE.replicate_pairs(chembl, intra=(variant == "sigma_intra"))
    rng = np.random.default_rng(0)
    hold = rng.random(len(pairs)) < 0.2
    rows = []
    for typ, g in pairs.groupby("standard_type"):
        fit, ho = g[~hold[g.index]], g[hold[g.index]]
        sig = NE.robust_sigma(fit.x1 - fit.x2)
        cover = float((np.abs(ho.x1 - ho.x2) <= 1.645 * np.sqrt(2) * sig).mean())
        cover_t = float((np.abs(ho.x1 - ho.x2) <= 2.132 * np.sqrt(2) * sig).mean())   # t, 4 df, 95th percentile
        rows.append(dict(standard_type=typ, sigma=sig, n_pairs=len(g), heldout_coverage90=cover,
                         heldout_coverage90_t4=cover_t))
    nm = pd.DataFrame(rows)
    if variant == "sigma_all":
        allp = pd.read_parquet(RUN / "data" / "chembl_alltargets_pairs.parquet")
        allp = allp[(allp.x1 - allp.x2).abs() >= 0.005]                        # drop re-reported copies (D2)
        nm["sigma"] = nm.standard_type.map(allp.groupby("standard_type").apply(lambda g: NE.robust_sigma(g.x1 - g.x2)))
    return nm, pairs


def build_molecules(chembl, nm, variant):
    rows = []
    for p in sorted(MD.BENCH.glob("*.csv")):
        df = pd.read_csv(p)
        target, typ = p.stem.split("_")
        mt = NE.match(df, chembl[chembl.dataset == p.stem])
        sig = float(nm.set_index("standard_type").sigma[typ])
        y = df["y [pEC50/pKi]"].values
        if variant == "sigma_tertile":
            ch = chembl[chembl.dataset == p.stem]
            pr = NE.replicate_pairs(ch)
            mid = (pr.x1 + pr.x2) / 2
            q = np.quantile(mid, [1 / 3, 2 / 3]) if len(pr) >= 30 else None
            def sig_for(v):
                if q is None:
                    return sig
                band = (mid <= q[0]) if v <= q[0] else ((mid > q[1]) if v > q[1] else ((mid > q[0]) & (mid <= q[1])))
                return NE.robust_sigma((pr.x1 - pr.x2)[band]) if band.sum() >= 10 else sig
            sigs = np.array([sig_for(v) for v in y])
        else:
            sigs = np.full(len(y), sig)
        n = {"n1": np.ones(len(y)), "nall": mt.n_all.values}.get(variant, mt.n_pre.values)
        rows.append(pd.DataFrame(dict(dataset=p.stem, idx=np.arange(len(df)), y=y, split=df.split.values,
                                      cliff_mol=df.cliff_mol.values, match=mt["match"].values, n_pre=mt.n_pre.values,
                                      n_all=mt.n_all.values, n_post=mt.n_post.values, post_mean=mt.post_mean.values,
                                      s=sigs / np.sqrt(n))))
    return pd.concat(rows, ignore_index=True)


def cliff_confidence(mol, variant, noise="normal"):
    pairs = pd.read_parquet(TAB / "similar_pairs.parquet")
    m = mol.set_index(["dataset", "idx"])
    yi = m.y.loc[list(zip(pairs.dataset, pairs.i))].values
    yj = m.y.loc[list(zip(pairs.dataset, pairs.j))].values
    si = m.s.loc[list(zip(pairs.dataset, pairs.i))].values
    sj = m.s.loc[list(zip(pairs.dataset, pairs.j))].values
    pairs["d"], pairs["sd"] = yi - yj, np.sqrt(si ** 2 + sj ** 2)
    if variant == "per_target":
        conf = np.zeros(len(pairs))
        for name, g in pairs.groupby("dataset"):
            w = NE.npmle(g.d.values, g.sd.values, noise)
            conf[g.index] = NE.confidence(g.d.values, g.sd.values, w, noise)
        pairs["conf"] = conf
    else:
        w = NE.npmle(pairs.d.values, pairs.sd.values, noise)
        pairs["conf"] = NE.confidence(pairs.d.values, pairs.sd.values, w, noise)
    return pairs


def gaps(mol, cp):
    pred = pd.read_parquet(TAB / "predictions.parquet")
    hc = set()
    for r in cp[cp.cliff & (cp.conf >= 0.9)].itertuples():
        hc.add((r.dataset, r.i)); hc.add((r.dataset, r.j))
    mol = mol.copy()
    mol["hc_cliff"] = [(d, i) in hc for d, i in zip(mol.dataset, mol.idx)]
    pm = pred.merge(mol[["dataset", "idx", "cliff_mol", "hc_cliff"]], on=["dataset", "idx"])
    rows = []
    for (name, model, seed), g in pm.groupby(["dataset", "model", "seed"]):
        y, p = g.y.values, g.pred.values
        full, rc, rn = MD.gap(y, p, g.cliff_mol.values == 1)
        restr, _, _ = MD.gap(y, p, g.hc_cliff.values) if g.hc_cliff.any() else (np.nan, 0, 0)
        rmse_all = float(np.sqrt(np.mean((y - p) ** 2)))
        rows.append(dict(dataset=name, model=model, seed=seed, gap=full, gap_restricted=restr, rmse_cliff=rc,
                         rmse_noncliff=rn, gap_vs_all=rc - rmse_all, n_cliff_test=int((g.cliff_mol == 1).sum()),
                         n_hc_test=int(g.hc_cliff.sum())))
    r = pd.DataFrame(rows)
    by_model = r.groupby(["dataset", "model"]).mean(numeric_only=True).reset_index()
    by_target = by_model.groupby("dataset").mean(numeric_only=True).reset_index()
    return by_model, by_target


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="primary")
    ap.add_argument("--stage", default="pre")
    a = ap.parse_args()
    chembl = pd.read_parquet(RUN / "data" / "chembl_bench.parquet")
    nm, reps = noise_model(chembl, a.variant)
    # plan sec 3: if the Gaussian 90% coverage of held-out pairs is outside 85-95%, the t (4 df) model is primary
    gauss_ok = bool(((nm.heldout_coverage90 >= 0.85) & (nm.heldout_coverage90 <= 0.95)).all())
    noise = "t" if (a.variant == "t4" or (a.variant != "normal" and not gauss_ok)) else "normal"
    print("Gaussian coverage within 85-95%:", gauss_ok, "-> noise model:", noise)
    mol = build_molecules(chembl, nm, a.variant)
    cp = cliff_confidence(mol, a.variant, noise)
    by_model, by_target = gaps(mol, cp)
    if a.variant == "primary":
        nm.to_csv(TAB / "noise_model.csv", index=False)
        mol.to_parquet(TAB / "molecules.parquet", index=False)
        cp.to_parquet(TAB / "cliff_pairs_conf.parquet", index=False)
        by_model.to_csv(TAB / "gaps_by_model.csv", index=False)
        by_target.to_csv(TAB / "gaps_by_target.csv", index=False)
    print(nm.round(3).to_string(index=False))
    print("match rates:", mol["match"].value_counts(normalize=True).round(3).to_dict())
    # H1
    cl = cp[cp.cliff]
    frac_by_t = {n: g for n, g in cl.groupby("dataset")}
    stat1 = lambda gs: float(np.mean(np.concatenate([(g.conf <= 0.8).values for g in gs])))
    h1 = stat1(list(frac_by_t.values()))
    lo1, hi1 = boot_targets(frac_by_t, stat1)
    v1 = "supported" if lo1 >= 0.25 else ("contradicted" if hi1 < 0.25 else "inconclusive")
    # H2
    inc = by_target[(by_target.n_hc_test > 0) & (by_target.n_cliff_test >= 10)].set_index("dataset")
    excluded = len(by_target) - len(inc)
    gt = {n: (r.gap, r.gap_restricted) for n, r in inc.iterrows()}
    stat2 = lambda gs: 1 - np.mean([g[1] for g in gs]) / np.mean([g[0] for g in gs])
    h2 = stat2(list(gt.values()))
    lo2, hi2 = boot_targets(gt, stat2)
    v2 = "supported" if (h2 >= 0.40 and lo2 > 0) else ("contradicted" if hi2 < 0.40 else "inconclusive")
    if len(inc) == 0:
        v2 = "not testable (no target has a high-confidence cliff test molecule)"
    res = dict(variant=a.variant, noise=noise, cliff_pairs=len(cl), H1_frac_conf_le_0p8=h1, H1_lo=lo1, H1_hi=hi1, H1=v1,
               mean_gap=float(inc.gap.mean()), mean_gap_restricted=float(inc.gap_restricted.mean()),
               H2_shrinkage=h2, H2_lo=lo2, H2_hi=hi2, H2=v2, H2_targets=len(inc), H2_excluded=excluded)
    if a.stage == "post":
        nullfile = "null_gaps_normal.csv" if noise == "normal" else "null_gaps.csv"
        null = pd.read_csv(TAB / nullfile).groupby(["dataset", "draw"]).gap.mean().groupby("dataset").mean()
        obs = by_target.set_index("dataset").gap
        gt3 = {n: (obs[n], null[n]) for n in obs.index if n in null.index}
        stat3 = lambda gs: np.mean([g[1] for g in gs]) / np.mean([g[0] for g in gs])
        h3 = stat3(list(gt3.values()))
        lo3, hi3 = boot_targets(gt3, stat3)
        v3 = "supported" if (h3 >= 0.5 and lo3 > 0) else ("contradicted" if hi3 < 0.5 else "inconclusive")
        res.update(H3_reproduced=h3, H3_lo=lo3, H3_hi=hi3, H3=v3, mean_null_gap=float(null.mean()))
    pd.DataFrame([res]).to_csv(TAB / f"hypotheses_{a.variant}.csv", index=False)
    print(pd.Series(res).to_string())
    if a.variant == "primary":
        sec = []
        both = mol[mol.n_post > 0].set_index(["dataset", "idx"])
        surv = []
        for r in cl.itertuples():
            if (r.dataset, r.i) in both.index and (r.dataset, r.j) in both.index:
                surv.append(abs(both.post_mean[(r.dataset, r.i)] - both.post_mean[(r.dataset, r.j)]) > 1)
        sec.append(dict(quantity="cliff pairs with post-2021 data for both molecules", value=len(surv)))
        sec.append(dict(quantity="of which still > 10-fold on post-2021 means", value=float(np.mean(surv)) if surv else np.nan))
        for m, g in by_model.groupby("model"):
            sec.append(dict(quantity=f"mean gap {m}", value=float(g.gap.mean())))
        sec.append(dict(quantity="mean gap vs all-test RMSE (MoleculeACE style)", value=float(by_target.gap_vs_all.mean())))
        pd.DataFrame(sec).to_csv(TAB / "secondary.csv", index=False)
        print(pd.DataFrame(sec).to_string(index=False))


if __name__ == "__main__":
    main()
