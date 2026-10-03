"""Preregistered agreement analysis (plan.md sections 3-4).
Outputs: results/tables/pairwise.csv, primary.csv, secondary.csv, dawid_skene.csv, leaderboard.csv, label_matrix.csv
"""
import itertools
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import roc_auc_score

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
SRC = ["O", "AS", "AT", "D"]
RNG = np.random.default_rng(20261003)
B_REPS = 2000


def kappa(a, b):
    m = ~(np.isnan(a) | np.isnan(b))
    a, b = a[m], b[m]
    po = np.mean(a == b)
    pa, pb = a.mean(), b.mean()
    pe = pa * pb + (1 - pa) * (1 - pb)
    return np.nan if pe == 1 else (po - pe) / (1 - pe)


def ac1(a, b):
    m = ~(np.isnan(a) | np.isnan(b))
    a, b = a[m], b[m]
    po = np.mean(a == b)
    pi = (a.mean() + b.mean()) / 2
    pe = 2 * pi * (1 - pi)
    return (po - pe) / (1 - pe)


def stats_for(L, srcs):
    ks = [kappa(L[x].values, L[y].values) for x, y in itertools.combinations(srcs, 2)]
    prev = [np.nanmean(L[s].values) for s in srcs]
    return np.nanmedian(ks), (max(prev) / min(prev) if min(prev) > 0 else np.inf), ks, prev


def boot(L, srcs):
    n = len(L)
    med, rat = [], []
    for _ in range(B_REPS):
        idx = RNG.integers(0, n, n)
        mk, r, _, _ = stats_for(L.iloc[idx], srcs)
        med.append(mk); rat.append(r)
    return np.array(med), np.array(rat)


def fleiss(r3):
    """r3: instance x 3 binary ratings."""
    n = r3.shape[1]
    p1 = r3.mean(axis=1)
    P = (np.sum(r3, 1) * (np.sum(r3, 1) - 1) + np.sum(1 - r3, 1) * (np.sum(1 - r3, 1) - 1)) / (n * (n - 1))
    pbar = r3.mean()
    pe = pbar ** 2 + (1 - pbar) ** 2
    return (P.mean() - pe) / (1 - pe)


def dawid_skene(X, iters=500):
    """Binary latent class model; X: tasks x raters (nan = missing). Returns prevalence, sens, spec."""
    pi, se, sp = 0.1, np.full(X.shape[1], 0.7), np.full(X.shape[1], 0.9)
    M = ~np.isnan(X)
    Xz = np.nan_to_num(X)
    for _ in range(iters):
        l1 = np.log(pi) + np.sum(M * (Xz * np.log(se) + (1 - Xz) * np.log(1 - se)), 1)
        l0 = np.log(1 - pi) + np.sum(M * (Xz * np.log(1 - sp) + (1 - Xz) * np.log(sp)), 1)
        t = 1 / (1 + np.exp(l0 - l1))
        pi = np.clip(t.mean(), 1e-4, 1 - 1e-4)
        se = np.clip((M * Xz * t[:, None]).sum(0) / (M * t[:, None]).sum(0), 1e-4, 1 - 1e-4)
        sp = np.clip((M * (1 - Xz) * (1 - t)[:, None]).sum(0) / (M * (1 - t)[:, None]).sum(0), 1e-4, 1 - 1e-4)
    return pi, se, sp


def main():
    L = pd.read_parquet(RUN / "data" / "labels.parquet")
    L[SRC + ["B", "W", "O_U", "AS_U", "AT_U", "D_hints"]].to_csv(TAB / "label_matrix.csv")
    # pairwise
    rows = []
    for x, y in itertools.combinations(SRC + ["B"], 2):
        a, b = L[x].values, L[y].values
        m = ~(np.isnan(a) | np.isnan(b))
        t = pd.crosstab(a[m], b[m]).reindex(index=[0, 1], columns=[0, 1], fill_value=0).values
        orr, p = stats.fisher_exact(t)
        rows.append(dict(a=x, b=y, n=int(m.sum()), kappa=kappa(a, b), ac1=ac1(a, b), both=int(t[1, 1]),
                         only_a=int(t[1, 0]), only_b=int(t[0, 1]), odds_ratio=orr, fisher_p=p))
    pw = pd.DataFrame(rows)
    pw.to_csv(TAB / "pairwise.csv", index=False)
    print(pw.round(3).to_string(index=False))
    # primary
    mk, rat, ks, prev = stats_for(L, SRC)
    bm, br = boot(L, SRC)
    lo_m, hi_m = np.nanpercentile(bm, [2.5, 97.5])
    lo_r, hi_r = np.percentile(br[np.isfinite(br)], [2.5, 97.5]) if np.isfinite(br).any() else (np.inf, np.inf)
    v1 = "Supported" if (mk < 0.20 and hi_m < 0.40) else ("Contradicted" if lo_m >= 0.20 else "Inconclusive")
    if np.isinf(rat):
        v2 = "Supported" if max(prev) >= 0.03 else "Inconclusive"
    else:
        v2 = "Supported" if lo_r > 3 else ("Contradicted" if hi_r < 3 else "Inconclusive")
    prim = pd.DataFrame([dict(hypothesis="H1 median pairwise kappa (O, AS, AT, D)", estimate=mk, lo=lo_m, hi=hi_m, verdict=v1),
                         dict(hypothesis="H2 max/min prevalence ratio", estimate=rat, lo=lo_r, hi=hi_r, verdict=v2)])
    prim.to_csv(TAB / "primary.csv", index=False)
    print(prim.round(3).to_string(index=False))
    print("prevalences:", dict(zip(SRC, np.round(prev, 4))), "| B", round(L.B.mean(), 4), "| W", int(L.W.sum()))
    # secondary
    sec = []
    ext = [kappa(L["O"].values, L[s].values) for s in ("AS", "AT")]
    sec.append(dict(analysis="median kappa, external sources only (O, AS, AT)", value=stats_for(L, ["O", "AS", "AT"])[0]))
    sec.append(dict(analysis="kappa O-AS / O-AT (independent external pairs)", value=np.mean(ext), note=str(np.round(ext, 3))))
    for typ in [("O_U", "AS_U", "AT_U")]:
        sec.append(dict(analysis="flaw U: median kappa (O_U, AS_U, AT_U)", value=stats_for(L, list(typ))[0],
                        note=str({s: round(np.nanmean(L[s]), 3) for s in typ})))
    sec.append(dict(analysis="detector with hints: kappa vs primary detector", value=kappa(L.D.values, L.D_hints.values),
                    note=f"prevalence {np.nanmean(L.D_hints):.3f}"))
    r3 = pd.read_csv(RUN / "data" / "raw" / "openai_annotations" / "samples_with_3_annotations_public.csv")
    r3["fn2"] = (r3.false_negative >= 2).astype(int)
    w = r3.groupby("instance_id").fn2.apply(list)
    w = np.array([x for x in w if len(x) == 3])
    sec.append(dict(analysis="Fleiss kappa among OpenAI's 3 annotators (false_negative >= 2, 1,699 instances)", value=fleiss(w),
                    note=f"n={len(w)}"))
    da = pd.read_parquet(RUN / "data" / "detector_annotated.parquet")
    y = (da.false_negative >= 2).astype(int).values
    s = da.score.values
    auc = roc_auc_score(y, s)
    ba = []
    for _ in range(B_REPS):
        i = RNG.integers(0, len(y), len(y))
        if y[i].min() != y[i].max():
            ba.append(roc_auc_score(y[i], s[i]))
    sec.append(dict(analysis="detector AUROC vs OpenAI consensus false_negative >= 2 (1,699)", value=auc,
                    note=f"95% CI {np.percentile(ba, 2.5):.3f}-{np.percentile(ba, 97.5):.3f}; flag rate {np.mean(s >= 1):.3f}; "
                         f"positives {y.mean():.3f}"))
    pd.DataFrame(sec).to_csv(TAB / "secondary.csv", index=False)
    print(pd.DataFrame(sec).round(3).to_string(index=False))
    # Dawid-Skene
    ds = []
    for lab, cols in [("all five (O, AS, AT, D, B)", ["O", "AS", "AT", "D", "B"]), ("without AT (one ABA mode)", ["O", "AS", "D", "B"])]:
        pi, se, sp = dawid_skene(L[cols].values.astype(float))
        ds.append(dict(model=lab, prevalence=pi, **{f"sens_{c}": a for c, a in zip(cols, se)}, **{f"spec_{c}": b for c, b in zip(cols, sp)}))
    pd.DataFrame(ds).to_csv(TAB / "dawid_skene.csv", index=False)
    print(pd.DataFrame(ds).round(3).to_string(index=False))
    # leaderboard
    rm = pd.read_parquet(RUN / "data" / "resolved_matrix.parquet")
    top = rm.mean().sort_values(ascending=False).index[:30]
    base = rm[top].mean()
    lb = []
    for sname in SRC + ["B"]:
        keep = L[sname].fillna(0).values == 0
        sc = rm.loc[keep, top].mean()
        tau = stats.kendalltau(base.rank(), sc.rank()).statistic
        lb.append(dict(source=sname, removed=int((~keep).sum()), kendall_tau=tau, mean_score_before=base.mean(), mean_score_after=sc.mean(),
                       max_rank_change=int((base.rank(ascending=False) - sc.rank(ascending=False)).abs().max())))
    pd.DataFrame(lb).to_csv(TAB / "leaderboard.csv", index=False)
    print(pd.DataFrame(lb).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
