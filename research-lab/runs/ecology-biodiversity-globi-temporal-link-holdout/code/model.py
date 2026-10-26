"""Evaluation sets, predictors and H1 (plan sections 2-4).

  model.py [PAST]     PAST = 0.6 (default; primary) or 0.8 (secondary 4: rolling origin v0.8 -> v0.11)
  -> results/tables/primary.json (or secondary_origin_v0.8.json), per_class.csv, eval_sets_summary.json,
     per_dataset.csv, graph_summary.json

D2 (after review): the degree-matched sampler fills every positive decile without replacement (uniform and
degree-proportional candidates, accepted by decile until full) and reports the achieved shares; robustness without
trophiCH (whose species-level links are mostly inferred by taxonomic expansion); per-dataset advantage table.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

RUN = Path(__file__).resolve().parents[1]
INT = RUN / "data" / "interim"
T = RUN / "results" / "tables"
SEED, B, NEG, RANK = 20261024, 1000, 10, 32
CLASSES = ("trophic", "pollination", "host")
TROPHICH = "globalbioticinteractions/trophiCH"
MATCH_REPORT = []


def load(v):
    e = pd.read_parquet(INT / f"edges_v{v}.parquet")
    return e


def sample_negatives(rng, srcs, tgts, n, forbid, match_to=None, deg=None):
    """Uniform (or degree-decile matched) non-edge pairs among the given sides, excluding forbid (set of (s,t))."""
    srcs, tgts = np.asarray(srcs), np.asarray(tgts)
    out = set()
    if match_to is None:
        while len(out) < n:
            k = int((n - len(out)) * 1.3) + 10
            for s, t in zip(srcs[rng.integers(0, len(srcs), k)], tgts[rng.integers(0, len(tgts), k)]):
                if (s, t) not in forbid and (s, t) not in out:
                    out.add((s, t))
                    if len(out) >= n:
                        break
        return list(out)
    # degree-matched (D2): fill each positive decile of log(deg_s * deg_t) without replacement, from uniform and
    # degree-proportional candidate draws, until every decile holds NEG x its positives
    lp = np.log1p([deg[0].get(s, 0) * deg[1].get(t, 0) for s, t in match_to])
    edges = np.quantile(lp, np.linspace(0, 1, 11))
    bp = np.clip(np.searchsorted(edges, lp, side="right") - 1, 0, 9)
    need = {b: int((bp == b).sum()) * NEG for b in range(10)}
    got = {b: set() for b in range(10)}
    ws = np.array([deg[0].get(x, 0) for x in srcs], float); ws /= ws.sum()
    wt = np.array([deg[1].get(x, 0) for x in tgts], float); wt /= wt.sum()
    stall = 0
    for _ in range(3000):
        if all(len(got[b]) >= need[b] for b in range(10)):
            break
        before = sum(len(v) for v in got.values())
        k = 100_000
        si = np.r_[rng.integers(0, len(srcs), k), rng.choice(len(srcs), k, p=ws)]
        ti = np.r_[rng.integers(0, len(tgts), k), rng.choice(len(tgts), k, p=wt)]
        ss, tt = srcs[si], tgts[ti]
        lc = np.log1p([deg[0].get(a, 0) * deg[1].get(b, 0) for a, b in zip(ss, tt)])
        bc = np.clip(np.searchsorted(edges, lc, side="right") - 1, 0, 9)
        for a, b2, d in zip(ss, tt, bc):
            if len(got[d]) < need[d] and (a, b2) not in forbid:
                got[d].add((a, b2))
        stall = stall + 1 if sum(len(v) for v in got.values()) == before else 0
        if stall >= 20:                                # a decile has fewer eligible pairs than needed: report it
            break
    MATCH_REPORT.append({"needed": int(sum(need.values())), "got": int(sum(len(v) for v in got.values())),
                         "decile_fill": [round(len(got[b]) / max(1, need[b]), 4) for b in range(10)],
                         "decile_share_negatives": [round(len(got[b]) / max(1, sum(len(v) for v in got.values())), 4) for b in range(10)],
                         "mean_log_deg_pos": round(float(lp.mean()), 3),
                         "mean_log_deg_neg": round(float(np.mean(np.log1p([deg[0].get(a, 0) * deg[1].get(b, 0) for b_ in got.values() for a, b in b_]))), 3)})
    return [p for b in range(10) for p in got[b]]


class Features:
    """Features of (s, t) pairs from a training graph (one class)."""

    def __init__(self, train, species):
        self.train = train
        self.ds = train.groupby("s").size().to_dict()
        self.dt = train.groupby("t").size().to_dict()
        self.cit = species.set_index("species").n_citations.to_dict()
        self.genus = species.set_index("species").genus.to_dict()
        self.family = species.set_index("species").family.to_dict()
        tr = train.assign(tg=train.t.map(self.genus), tf=train.t.map(self.family), sg=train.s.map(self.genus),
                          sf=train.s.map(self.family))
        self.s_tg = tr.groupby(["s", "tg"]).size().to_dict()
        self.s_tf = tr.groupby(["s", "tf"]).size().to_dict()
        self.sg_t = tr.groupby(["sg", "t"]).size().to_dict()
        self.sg_tg = tr.groupby(["sg", "tg"]).size().to_dict()
        self.sf_tf = tr.groupby(["sf", "tf"]).size().to_dict()
        self.pairs = set(zip(train.s, train.t))
        # RDPG
        si = {s: i for i, s in enumerate(sorted(self.ds))}
        ti = {t: i for i, t in enumerate(sorted(self.dt))}
        A = csr_matrix((np.ones(len(train)), ([si[s] for s in train.s], [ti[t] for t in train.t])), shape=(len(si), len(ti)))
        k = min(RANK, min(A.shape) - 1)
        if k >= 1:
            u, sv, vt = svds(A.astype(float), k=k)
            self.U, self.V = u * np.sqrt(sv), vt.T * np.sqrt(sv)
        else:
            self.U, self.V = np.zeros((len(si), 1)), np.zeros((len(ti), 1))
        self.si, self.ti = si, ti

    def rdpg(self, pairs):
        return np.array([float(self.U[self.si[s]] @ self.V[self.ti[t]]) if s in self.si and t in self.ti else 0.0
                         for s, t in pairs])

    def effort(self, pairs):
        return np.array([[np.log1p(self.ds.get(s, 0)), np.log1p(self.dt.get(t, 0)), np.log1p(self.cit.get(s, 0)),
                          np.log1p(self.cit.get(t, 0))] for s, t in pairs])

    def taxo(self, pairs):
        rows = []
        for s, t in pairs:
            self_link = 1 if (s, t) in self.pairs else 0
            g_t, f_t, g_s, f_s = self.genus.get(t), self.family.get(t), self.genus.get(s), self.family.get(s)
            rows.append([self.s_tg.get((s, g_t), 0) - self_link, self.s_tf.get((s, f_t), 0) - self_link,
                         self.sg_t.get((g_s, t), 0) - self_link, self.sg_tg.get((g_s, g_t), 0) - self_link,
                         self.sf_tf.get((f_s, f_t), 0) - self_link])
        return np.log1p(np.clip(np.array(rows, float), 0, None))

    def full(self, pairs):
        return np.hstack([self.effort(pairs), self.rdpg(pairs)[:, None], self.taxo(pairs)])


def fit_models(train, species, rng):
    """Inner split: 10% of training edges are labels, features from the other 90%."""
    m = rng.random(len(train)) < 0.1
    inner, lab = train[~m], train[m]
    F = Features(inner, species)
    pos = [(s, t) for s, t in zip(lab.s, lab.t) if s in F.ds and t in F.dt]
    neg = sample_negatives(rng, list(F.ds), list(F.dt), NEG * len(pos), set(zip(train.s, train.t)))
    pairs, y = pos + neg, np.r_[np.ones(len(pos)), np.zeros(len(neg))]
    eff = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)).fit(F.effort(pairs), y)
    gb = HistGradientBoostingClassifier(early_stopping=False, random_state=SEED).fit(F.full(pairs), y)
    return eff, gb


def auroc(score, y, w=None):
    """Mann-Whitney AUROC with optional integer weights (bootstrap multiplicities)."""
    w = np.ones(len(y)) if w is None else w
    o = np.argsort(score, kind="mergesort")
    s, yy, ww = score[o], y[o], w[o]
    # ranks with ties averaged, weighted
    uniq, inv = np.unique(s, return_inverse=True)
    cw = np.bincount(inv, ww)
    cum = np.cumsum(cw) - cw
    rank = cum[inv] + (cw[inv] + 1) / 2
    npos, nneg = (ww * yy).sum(), (ww * (1 - yy)).sum()
    return float(((rank * ww * yy).sum() - npos * (npos + 1) / 2) / (npos * nneg)) if npos and nneg else np.nan


def evaluate(edges_past, edges_future, species, rng, matched=False):
    out_rows, sets = [], {}
    for mode in ("random", "temporal"):
        P, S, Y, CL, CLU, NEWNS, COLD = [], {"effort": [], "rdpg": [], "taxgb": []}, [], [], [], [], []
        for cls in CLASSES:
            g6 = edges_past[edges_past.cls == cls]
            if mode == "random":
                hide = rng.random(len(g6)) < 0.1
                train, hidden = g6[~hide], g6[hide]
                F = Features(train, species)
                pos_df = hidden[hidden.s.isin(F.ds) & hidden.t.isin(F.dt)]
                pos = list(zip(pos_df.s, pos_df.t))
                clu = list(pos_df.top_namespace)
                forbid = set(zip(g6.s, g6.t))
            else:
                train = g6
                F = Features(train, species)
                fut = edges_future[edges_future.cls == cls]
                new = fut[~fut.set_index(["s", "t"]).index.isin(g6.set_index(["s", "t"]).index)]
                pos_df = new[new.s.isin(F.ds) & new.t.isin(F.dt)]
                pos = list(zip(pos_df.s, pos_df.t))
                clu = list(pos_df.top_namespace)
                forbid = set(zip(g6.s, g6.t)) | set(zip(fut.s, fut.t))
                known_ns = set(n for ns in edges_past.namespaces.dropna() for n in ns.split("|"))
                newns = (~pos_df.top_namespace.isin(known_ns)).to_numpy()
                cold = np.array([F.ds.get(a, 0) == 1 or F.dt.get(b, 0) == 1 for a, b in pos])
                sets[cls] = {"future_new_pairs": int(len(new)), "positives": len(pos),
                             "share_new_namespace": float(newns.mean()) if len(pos) else None,
                             "share_cold": float(cold.mean()) if len(pos) else None}
            if not pos:
                continue
            deg = (F.ds, F.dt)
            neg = sample_negatives(rng, list(F.ds), list(F.dt), NEG * len(pos), forbid,
                                   match_to=pos if matched else None, deg=deg)
            eff, gb = fit_models(train, species, rng)
            pairs = pos + neg
            S["effort"].append(eff.predict_proba(F.effort(pairs))[:, 1])
            S["rdpg"].append(F.rdpg(pairs))
            S["taxgb"].append(gb.predict_proba(F.full(pairs))[:, 1])
            Y.append(np.r_[np.ones(len(pos)), np.zeros(len(neg))])
            CL += [cls] * len(pairs)
            CLU += clu + [None] * len(neg)
            if mode == "temporal":
                NEWNS += list(newns) + [False] * len(neg)
                COLD += list(cold) + [False] * len(neg)
        y = np.concatenate(Y)
        sc = {k: np.concatenate(v) for k, v in S.items()}
        cl = np.array(CL)
        # within-class percentile ranks, so the pooled AUROC is not driven by score scales that differ by class
        pct = {}
        for k, v in sc.items():
            r = np.empty(len(v))
            for c in np.unique(cl):
                m = cl == c
                r[m] = pd.Series(v[m]).rank(pct=True).to_numpy()
            pct[k] = r
        out_rows.append({"mode": mode, "y": y, "scores": sc, "pct": pct, "cls": cl, "cluster": np.array(CLU, dtype=object),
                         "newns": np.array(NEWNS, bool) if NEWNS else None, "cold": np.array(COLD, bool) if COLD else None})
    return out_rows, sets


def pooled_auc(r, k, w=None, keep=None):
    s, y = r["pct"][k], r["y"]
    if keep is not None:
        s, y = s[keep], y[keep]
        w = None if w is None else w[keep]
    return auroc(s, y, w)


def boot_weights(r, rng):
    pos = r["y"] == 1
    clus = r["cluster"][pos]
    uc = np.unique(clus.astype(str))
    pick = rng.choice(uc, len(uc))
    cnt = pd.Series(pick).value_counts()
    w = np.zeros(len(r["y"]))
    w[pos] = pd.Series(clus.astype(str)).map(cnt).fillna(0).to_numpy()
    nidx = np.nonzero(~pos)[0]
    w[nidx] += np.bincount(rng.integers(0, len(nidx), len(nidx)), minlength=len(nidx))
    return w


def main(past="0.6"):
    rng = np.random.default_rng(SEED)
    species = pd.read_parquet(INT / f"species_v{past}.parquet")
    e6, e11 = load(past), load("0.11")
    res, sets = evaluate(e6, e11, species, rng)
    rand, temp = res
    auc = {m["mode"]: {k: pooled_auc(m, k) for k in ("effort", "rdpg", "taxgb")} for m in res}
    best = max(("rdpg", "taxgb"), key=lambda k: auc["random"][k])
    A = {m: auc[m][best] - auc[m]["effort"] for m in auc}
    rho = A["temporal"] / A["random"] if A["random"] else np.nan
    bs = []
    rng2 = np.random.default_rng(SEED + 1)
    for _ in range(B):
        wr, wt = boot_weights(rand, rng2), boot_weights(temp, rng2)
        ar = pooled_auc(rand, best, wr) - pooled_auc(rand, "effort", wr)
        at = pooled_auc(temp, best, wt) - pooled_auc(temp, "effort", wt)
        bs.append((ar, at, at / ar if ar else np.nan))
    bs = np.array(bs)
    q = lambda v: [round(float(np.nanpercentile(v, 2.5)), 4), round(float(np.nanpercentile(v, 97.5)), 4)]
    out = {"past": past, "future": "0.11", "auroc": {m: {k: round(v, 4) for k, v in d.items()} for m, d in auc.items()},
           "best": best, "A_random": round(A["random"], 4), "A_random_ci": q(bs[:, 0]),
           "A_temporal": round(A["temporal"], 4), "A_temporal_ci": q(bs[:, 1]), "rho": round(float(rho), 4), "rho_ci": q(bs[:, 2]),
           "n": {m["mode"]: {"pos": int(m["y"].sum()), "neg": int((1 - m["y"]).sum())} for m in res}, "temporal_sets": sets}
    if out["A_random_ci"][0] <= 0:
        out["H1"] = "not testable (structure does not beat effort on the random holdout)"
    elif out["rho_ci"][1] < 0.5:
        out["H1"] = "Supported"
    elif out["rho_ci"][0] > 0.5:
        out["H1"] = "Refuted"
    else:
        out["H1"] = "Inconclusive"
    # per class AUROCs
    rows = []
    for m in res:
        for c in CLASSES:
            mm = m["cls"] == c
            if mm.any():
                rows.append({"mode": m["mode"], "cls": c, "pos": int(m["y"][mm].sum()),
                             **{k: round(auroc(m["scores"][k][mm], m["y"][mm]), 4) for k in m["scores"]}})
    # secondaries 3 and 5: temporal positives from datasets new since the past snapshot / cold-start endpoints
    sub = {}
    for lab, flag in (("new_dataset", temp["newns"]), ("existing_dataset", ~temp["newns"] & (temp["y"] == 1)),
                      ("cold_start", temp["cold"])):
        keep = (temp["y"] == 0) | (flag & (temp["y"] == 1))
        if (flag & (temp["y"] == 1)).sum() > 0:
            sub[lab] = {"pos": int((flag & (temp["y"] == 1)).sum()),
                        **{k: round(pooled_auc(temp, k, keep=keep), 4) for k in ("effort", "rdpg", "taxgb")}}
    out["temporal_subsets"] = sub
    # D2 robustness: without trophiCH positives (inferred links); joint per-replicate ratio bootstrap (holdouts resampled independently)
    keep = (temp["y"] == 0) | (temp["cluster"].astype(str) != TROPHICH)
    at_n = pooled_auc(temp, best, keep=keep) - pooled_auc(temp, "effort", keep=keep)
    bs2, rng3 = [], np.random.default_rng(SEED + 3)
    for _ in range(B):
        wr, wt = boot_weights(rand, rng3), boot_weights(temp, rng3)
        ar = pooled_auc(rand, best, wr) - pooled_auc(rand, "effort", wr)
        at = pooled_auc(temp, best, wt, keep=keep) - pooled_auc(temp, "effort", wt, keep=keep)
        bs2.append((at, at / ar if ar else np.nan))
    bs2 = np.array(bs2)
    tpos = temp["y"] == 1
    out["without_trophiCH"] = {"positives": int((keep & tpos).sum()), "trophiCH_positives": int((~keep).sum()),
                               "A_temporal": round(float(at_n), 4), "A_temporal_ci": q(bs2[:, 0]),
                               "rho": round(float(at_n / A["random"]), 4), "rho_ci": q(bs2[:, 1]),
                               "auroc": {k: round(pooled_auc(temp, k, keep=keep), 4) for k in ("effort", "rdpg", "taxgb")}}
    clus = pd.Series(temp["cluster"][tpos].astype(str))
    out["temporal_clusters"] = {"clusters": int(clus.nunique()), "largest": clus.value_counts().index[0],
                                "largest_share": round(float(clus.value_counts(normalize=True).iloc[0]), 4),
                                "top3_share": round(float(clus.value_counts(normalize=True).iloc[:3].sum()), 4)}
    pdrows = []
    for ns, cnt in clus.value_counts().items():
        if cnt < 1000:
            break
        kk = (temp["y"] == 0) | (temp["cluster"].astype(str) == ns)
        e_, t_ = pooled_auc(temp, "effort", keep=kk), pooled_auc(temp, best, keep=kk)
        pdrows.append({"dataset": ns, "positives": int(cnt), "effort": round(e_, 4), best: round(t_, 4), "A": round(t_ - e_, 4)})
    pd.DataFrame(pdrows).to_csv(T / "per_dataset.csv", index=False)
    name = "primary.json" if past == "0.6" else f"secondary_origin_v{past}.json"
    (T / name).write_text(json.dumps(out, indent=1, default=str))
    pd.DataFrame(rows).to_csv(T / ("per_class.csv" if name == "primary.json" else f"per_class_origin_v{past}.csv"), index=False)
    # secondary 2: degree-matched negatives (point estimates)
    if name == "primary.json":
        (T / "eval_sets_summary.json").write_text(json.dumps({"temporal_sets": sets, "n": out["n"],
                                                             "temporal_clusters": out["temporal_clusters"]}, indent=1))
        (T / "graph_summary.json").write_text(json.dumps({v: {c: {"edges": int((e.cls == c).sum()), "sources": int(e[e.cls == c].s.nunique()),
                                                                  "targets": int(e[e.cls == c].t.nunique())} for c in CLASSES}
                                                         for v, e in (("v" + past, e6), ("v0.11", e11))}, indent=1))
        MATCH_REPORT.clear()
        resm, _ = evaluate(e6, e11, species, np.random.default_rng(SEED + 2), matched=True)
        out["degree_matched"] = {m["mode"]: {k: round(pooled_auc(m, k), 4) for k in ("effort", "rdpg", "taxgb")} for m in resm}
        out["degree_matched_sampler"] = [dict(r, mode=md, cls=c) for r, (md, c) in zip(MATCH_REPORT, [(m, c) for m in ("random", "temporal") for c in CLASSES])]
        (T / name).write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main(*sys.argv[1:])
