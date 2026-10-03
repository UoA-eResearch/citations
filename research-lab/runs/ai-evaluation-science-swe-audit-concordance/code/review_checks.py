"""Checks added after independent review (deviations.md D1-D4). Preregistered verdicts come from analysis.py.

1. O-definition ladder: O = any annotator >= 1 (preregistered; equals the ensembled max), >= 2 of 3 annotators,
   all 3 annotators; H1 median kappa and H2 ratio with the same bootstrap.
2. Per-pair kappa with task-bootstrap CIs and raw overlaps; three-way overlap of AS, AT, D.
3. AC1 and kappa under independence at the observed prevalences (simulation baseline).
4. Fleiss kappa among OpenAI's annotators at fn >= 1, >= 2, >= 3 (1,699) and fn >= 1 within Verified.
5. Detector: precision / recall / likelihood ratio on the 1,699; post hoc variant D' with normalised text (zero-width
   characters removed, doubled backslashes unescaped, whitespace collapsed) on Verified.
6. Dawid-Skene: bootstrap CI of prevalence; prevalence by rater set; posterior-positive tasks.
7. Leaderboard: random-removal null for tau and max rank change.
Outputs: results/tables/review_*.csv
"""
import itertools
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
import detector as D  # noqa: E402

RUN = A.RUN
TAB = A.TAB
RNG = np.random.default_rng(7)
ZW = re.compile("[​‌‍⁠﻿]")


def norm(s):
    s = ZW.sub("", s or "")
    s = s.replace("\\\\", "\\")
    return re.sub(r"\s+", " ", s)


def detect_norm(task):
    """D': the frozen detector with normalised issue text and test literals (post hoc)."""
    issue = norm(task["problem_statement"])
    tl = [ln for f, ln in D.added(task["test_patch"])]
    gold = "\n".join(ln for f, ln in D.added(task["patch"]))
    issue_words = set(re.findall(D.NAME, issue))
    cand = D.names_used(tl) - D.names_defined(tl)
    cand = {n for n in cand if re.search(rf"\b{re.escape(n)}\b", gold) and n not in issue_words}
    ids = [n for n in cand if not D.in_repo(task["repo"], task["base_commit"], n, True)]
    gw = " ".join(re.findall(r"\w+", gold))
    lits = {s for s in D.literals(tl) if D.shares_3gram(s, gw) and norm(s).lower() not in issue.lower()}
    lits = [s for s in lits if not D.in_repo(task["repo"], task["base_commit"], s, False)]
    return dict(instance_id=task["instance_id"], flag=int(len(ids) + len(lits) >= 1), n_ids=len(ids), n_lits=len(lits))


def main():
    L = pd.read_parquet(RUN / "data" / "labels.parquet")
    ids = L.index.tolist()
    r3 = pd.read_csv(RUN / "data" / "raw" / "openai_annotations" / "samples_with_3_annotations_public.csv")
    cnt = r3.assign(f1=(r3.false_negative >= 1).astype(int)).groupby("instance_id").f1.sum().reindex(ids)
    L["O_maj"] = (cnt >= 2).astype(float)
    L["O_all"] = (cnt >= 3).astype(float)
    rows = []
    for lab, col in [("O = any annotator >= 1 (preregistered)", "O"), ("O = majority (>= 2 of 3)", "O_maj"), ("O = unanimous", "O_all")]:
        Lx = L.assign(O=L[col])
        mk, rat, ks, prev = A.stats_for(Lx, A.SRC)
        bm, br = A.boot(Lx, A.SRC)
        rows.append(dict(definition=lab, O_prevalence=prev[0], median_kappa=mk, mk_lo=np.nanpercentile(bm, 2.5),
                         mk_hi=np.nanpercentile(bm, 97.5), ratio=rat, ratio_lo=np.percentile(br[np.isfinite(br)], 2.5),
                         ratio_hi=np.percentile(br[np.isfinite(br)], 97.5)))
    lad = pd.DataFrame(rows)
    lad.to_csv(TAB / "review_O_ladder.csv", index=False)
    print(lad.round(3).to_string(index=False))
    # per-pair CIs and overlaps
    pr = []
    for x, y in itertools.combinations(A.SRC, 2):
        a, b = L[x].values, L[y].values
        bs = [A.kappa(a[i], b[i]) for i in (RNG.integers(0, 500, 500) for _ in range(2000))]
        pa, pb = np.nanmean(a), np.nanmean(b)
        sim_k, sim_ac1 = [], []
        for _ in range(2000):
            u, v = (RNG.random(500) < pa).astype(float), (RNG.random(500) < pb).astype(float)
            sim_k.append(A.kappa(u, v)); sim_ac1.append(A.ac1(u, v))
        pr.append(dict(a=x, b=y, kappa=A.kappa(a, b), k_lo=np.nanpercentile(bs, 2.5), k_hi=np.nanpercentile(bs, 97.5),
                       flagged_a=int(np.nansum(a)), flagged_b=int(np.nansum(b)), both=int(np.nansum(a * b)),
                       ac1=A.ac1(a, b), ac1_independence_median=np.median(sim_ac1),
                       ac1_independence_95=np.percentile(sim_ac1, 97.5), kappa_independence_95=np.nanpercentile(sim_k, 97.5)))
    pr = pd.DataFrame(pr)
    pr.to_csv(TAB / "review_pairs.csv", index=False)
    print(pr.round(3).to_string(index=False))
    tri = L[(L.AS == 1) & (L.AT == 1) & (L.D == 1)].index.tolist()
    union = int(((L.AS == 1) | (L.AT == 1) | (L.D == 1)).sum())
    print("AS & AT & D:", tri, "| union:", union)
    # Fleiss thresholds
    fl = []
    for thr in (1, 2, 3):
        w = r3.assign(f=(r3.false_negative >= thr).astype(int)).groupby("instance_id").f.apply(list)
        w = np.array([x for x in w if len(x) == 3])
        fl.append(dict(set="1,699 annotated", threshold=f">= {thr}", fleiss=A.fleiss(w)))
    wv = r3[r3.instance_id.isin(ids)].assign(f=lambda x: (x.false_negative >= 1).astype(int)).groupby("instance_id").f.apply(list)
    wv = np.array([x for x in wv if len(x) == 3])
    fl.append(dict(set="500 Verified", threshold=">= 1", fleiss=A.fleiss(wv)))
    pd.DataFrame(fl).to_csv(TAB / "review_fleiss.csv", index=False)
    print(pd.DataFrame(fl).round(3).to_string(index=False))
    # detector validation as a binary flag
    da = pd.read_parquet(RUN / "data" / "detector_annotated.parquet")
    y, f = (da.false_negative >= 2).values, (da.score >= 1).values
    sens, spec = (f & y).sum() / y.sum(), (~f & ~y).sum() / (~y).sum()
    dv = dict(sensitivity=sens, specificity=spec, ppv=(f & y).sum() / f.sum(), npv=(~f & ~y).sum() / (~f).sum(),
              base_rate=y.mean(), lr_pos=sens / (1 - spec), flag_rate=f.mean(), auroc_binary=(sens + spec) / 2)
    pd.Series(dv).to_csv(TAB / "review_detector_validation.csv")
    print({k: round(float(v), 3) for k, v in dv.items()})
    # D' on Verified
    v = pd.read_parquet(RUN / "data" / "raw" / "verified" / "data" / "test-00000-of-00001.parquet")
    dn = pd.DataFrame([detect_norm(t) for t in v.to_dict("records")]).set_index("instance_id").reindex(ids)
    L["Dn"] = dn.flag.astype(float)
    dnp = dict(prevalence=L.Dn.mean(), dropped_vs_D=L[(L.D == 1) & (L.Dn == 0)].index.tolist(),
               **{f"kappa_{s}": A.kappa(L.Dn.values, L[s].values) for s in ("O", "AS", "AT")})
    pd.Series({k: str(v_) for k, v_ in dnp.items()}).to_csv(TAB / "review_detector_normalised.csv")
    print(dnp)
    # Dawid-Skene bootstrap and rater sets
    ds = []
    for lab, cols in [("O, AS, AT, D, B", ["O", "AS", "AT", "D", "B"]), ("O, AS, D, B (no AT)", ["O", "AS", "D", "B"]),
                      ("O, AS, AT, D (no B)", ["O", "AS", "AT", "D"]), ("O, AS, D (no AT, no B)", ["O", "AS", "D"]),
                      ("O majority, AS, AT, D, B", ["O_maj", "AS", "AT", "D", "B"])]:
        X = L[cols].values.astype(float)
        pi, se, sp = A.dawid_skene(X)
        bpi = [A.dawid_skene(X[RNG.integers(0, 500, 500)], iters=300)[0] for _ in range(300)]
        ds.append(dict(raters=lab, prevalence=pi, lo=np.percentile(bpi, 2.5), hi=np.percentile(bpi, 97.5)))
    pd.DataFrame(ds).to_csv(TAB / "review_dawid_skene.csv", index=False)
    print(pd.DataFrame(ds).round(3).to_string(index=False))
    X = L[["O", "AS", "AT", "D", "B"]].values.astype(float)
    pi, se, sp = A.dawid_skene(X)
    l1 = np.log(pi) + (X * np.log(se) + (1 - X) * np.log(1 - se)).sum(1)
    l0 = np.log(1 - pi) + (X * np.log(1 - sp) + (1 - X) * np.log(sp)).sum(1)
    post = 1 / (1 + np.exp(l0 - l1))
    pp = L.assign(posterior=post)[post > 0.5][["O", "AS", "AT", "D", "B", "posterior"]]
    pp.to_csv(TAB / "review_posterior_positive.csv")
    print(pp.round(2).to_string())
    # leaderboard null
    rm = pd.read_parquet(RUN / "data" / "resolved_matrix.parquet")
    top = rm.mean().sort_values(ascending=False).index[:30]
    base = rm[top].mean()
    lb = []
    for s in A.SRC + ["B"]:
        k = int(L[s].fillna(0).sum())
        keep = L[s].fillna(0).values == 0
        sc = rm.loc[keep, top].mean()
        taus, mrc = [], []
        for _ in range(1000):
            kp = np.ones(500, bool); kp[RNG.choice(500, k, replace=False)] = False
            s2 = rm.loc[kp, top].mean()
            taus.append(stats.kendalltau(base, s2).statistic)
            mrc.append((base.rank(ascending=False) - s2.rank(ascending=False)).abs().max())
        lb.append(dict(source=s, removed=k, tau=stats.kendalltau(base, sc).statistic, tau_random_median=np.median(taus),
                       tau_random_5pct=np.percentile(taus, 5),
                       max_rank_change=(base.rank(ascending=False) - sc.rank(ascending=False)).abs().max(),
                       max_rank_change_random_median=np.median(mrc), note="tautological: no top-30 submission solves a B task" if s == "B" else ""))
    pd.DataFrame(lb).to_csv(TAB / "review_leaderboard.csv", index=False)
    print(pd.DataFrame(lb).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
