"""H1-H3 and secondaries (plan section 0). Written before any score was computed.

  analyse.py -> results/tables/primary.json, metrics.csv, pairs_h2.csv, tau_h3.csv; coverage stage "scored_targets"
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402

SEED, B, ALPHA = 20261027, 2000, 20.0
METHODS = ["nn", "rf", "gbm", "cb", "mf"]
PRIMARY = "audit04"


def ef(y, s, frac=0.01):
    """Enrichment factor in the top `frac` of the ranking; ties broken by a fixed shuffle of equal scores."""
    n = len(y)
    k = max(1, int(round(frac * n)))
    order = np.argsort(-s, kind="stable")
    hits = y[order[:k]].sum()
    rate = y.mean()
    return float((hits / k) / rate) if rate > 0 else np.nan


def bedroc(y, s, alpha=ALPHA):
    """Truchon & Bayly (2007) BEDROC: RIE scaled to [0, 1] by its minimum and maximum at this active ratio."""
    n, a = len(y), int(y.sum())
    if a == 0 or a == n:
        return np.nan
    r = np.argsort(-s, kind="stable")
    ranks = np.flatnonzero(y[r] == 1) + 1
    ra = a / n
    rie_num = np.exp(-alpha * ranks / n).sum() / a
    rie_den = (1 / n) * (1 - np.exp(-alpha)) / (np.exp(alpha / n) - 1)
    rie = rie_num / rie_den
    rie_max = (1 - np.exp(-alpha * ra)) / (ra * (1 - np.exp(-alpha)))
    rie_min = (1 - np.exp(alpha * ra)) / (ra * (1 - np.exp(alpha)))
    return float((rie - rie_min) / (rie_max - rie_min))


def auprc(y, s):
    from sklearn.metrics import average_precision_score
    return float(average_precision_score(y, s)) if 0 < y.sum() < len(y) else np.nan


def load(ev):
    d = D / f"scores_{ev}"
    if not d.exists():
        return pd.DataFrame()
    return pd.concat([pd.read_parquet(p) for p in sorted(d.glob("*.parquet"))], ignore_index=True)


def metrics_table():
    rows = []
    cov = Coverage("scored_targets", T / "coverage.json")
    for ev in ("new", "lit_cv", "lit_pub"):
        S = load(ev)
        if S.empty:
            continue
        for (target, variant, method), g in S.groupby(["target", "variant", "method"]):
            y, s = g.y.to_numpy(), g.score.to_numpy()
            if method == "nn" and variant == "published":
                pass
            e = ef(y, s)
            rate = float(y.mean())
            rows.append({"eval": ev, "target": target, "variant": variant, "method": method, "n": len(y),
                         "actives": int(y.sum()), "hit_rate": round(rate, 5),
                         "ef1_ceiling": round(min(1 / 0.01, 1 / rate), 2) if rate > 0 else np.nan,   # top 1% holds 0.01n slots
                         "ef1": e,
                         "ef1_normalised": round(e / min(1 / 0.01, 1 / rate), 4) if rate > 0 and np.isfinite(e) else np.nan,  # D2, post hoc
                         "bedroc": bedroc(y, s), "auprc": auprc(y, s)})
        for t, g in S[S.variant.isin([PRIMARY, "published"])].groupby("target"):
            cov.attempt((ev, t))
            cov.ok((ev, t)) if g.method.nunique() == len(METHODS) else cov.drop((ev, t), "not all methods scored")
    cov.save()
    M = pd.DataFrame(rows)
    M.to_csv(T / "metrics.csv", index=False)
    return M


def boot_targets(vals, rng):
    v = np.asarray(vals, float)
    v = v[np.isfinite(v)]
    return np.array([np.median(v[rng.integers(len(v), size=len(v))]) for _ in range(B)])


def h1(M, rng):
    new = M[(M["eval"] == "new") & (M.variant == PRIMARY) & (M.method == "nn")].ef1 - 1
    lit = M[(M["eval"] == "lit_pub") & (M.method == "nn")].ef1 - 1
    bn, bl = boot_targets(new, rng), boot_targets(lit, rng)
    q = np.median(new) / np.median(lit)
    bq = bn / np.where(bl != 0, bl, np.nan)
    ci = [round(float(np.nanpercentile(bq, 2.5)), 3), round(float(np.nanpercentile(bq, 97.5)), 3)]
    v = "Supported" if ci[1] <= 0.5 else "Refuted" if ci[0] > 0.5 else "Inconclusive"
    return {"A_new": round(float(np.median(new)), 3), "A_lit": round(float(np.median(lit)), 3), "Q": round(float(q), 3),
            "Q_ci": ci, "targets_new": int(new.notna().sum()), "targets_lit": int(lit.notna().sum()), "verdict": v}


def h2(rng):
    S = load("new")
    S = S[S.variant == PRIMARY]
    rows = []
    for target, g in S.groupby("target"):
        w = g.pivot_table(index="idx", columns="method", values="score")
        y = g.drop_duplicates("idx").set_index("idx").y.reindex(w.index).to_numpy()
        n = len(y)
        idx = rng.integers(0, n, size=(B, n))
        base = {m: ef(y, w[m].to_numpy()) for m in METHODS if m in w}
        bs = {m: np.array([ef(y[i], w[m].to_numpy()[i]) for i in idx]) for m in ("rf", "cb", "mf") if m in w}
        for m in ("cb", "mf"):
            if m not in bs:
                continue
            d = bs[m] - bs["rf"]
            lo, hi = np.nanpercentile(d, [2.5, 97.5])
            rows.append({"target": target, "embedding": m, "ef_rf": base["rf"], "ef_emb": base[m],
                         "delta": base[m] - base["rf"], "ci_lo": float(lo), "ci_hi": float(hi),
                         "emb_beats_rf": bool(lo > 0), "rf_beats_emb": bool(hi < 0)})
    P = pd.DataFrame(rows)
    P.to_csv(T / "pairs_h2.csv", index=False)
    s2 = float((~P.emb_beats_rf).mean())
    v = "Supported" if s2 >= 0.70 else "Refuted" if s2 < 0.50 else "Inconclusive"
    return {"pairs": int(len(P)), "S2": round(s2, 3), "share_rf_beats_embedding": round(float(P.rf_beats_emb.mean()), 3),
            "median_delta_ef1": round(float(P.delta.median()), 3), "verdict": v}


def h3(M, rng):
    from scipy.stats import kendalltau
    lit = M[(M["eval"] == "lit_pub")].groupby("method").ef1.median()
    consensus = lit.reindex(METHODS).to_numpy()
    new = M[(M["eval"] == "new") & (M.variant == PRIMARY)]
    rows = []
    for t, g in new.groupby("target"):
        v = g.set_index("method").ef1.reindex(METHODS).to_numpy()
        if np.isfinite(v).all():
            rows.append({"target": t, "tau": float(kendalltau(v, consensus).statistic)})
    Tt = pd.DataFrame(rows)
    Tt.to_csv(T / "tau_h3.csv", index=False)
    taus = Tt.tau.to_numpy()
    bs = np.array([np.mean(taus[rng.integers(len(taus), size=len(taus))]) for _ in range(B)])
    ci = [round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)]
    v = "Supported" if ci[1] <= 0.4 else "Refuted" if ci[0] > 0.4 else "Inconclusive"
    return {"targets": int(len(Tt)), "mean_tau": round(float(taus.mean()), 3), "ci": ci,
            "lit_consensus_order": [METHODS[i] for i in np.argsort(-consensus)], "verdict": v}


def noise_ceiling(rng):
    """Mean tau between method rankings on two random halves of each NEW target's evaluation set (secondary)."""
    from scipy.stats import kendalltau
    S = load("new")
    S = S[S.variant == PRIMARY]
    out, skipped = [], []
    for t, g in S.groupby("target"):
        w = g.pivot_table(index="idx", columns="method", values="score")
        y = g.drop_duplicates("idx").set_index("idx").y.reindex(w.index).to_numpy()
        perm = rng.permutation(len(y)); a, b = perm[: len(y) // 2], perm[len(y) // 2:]
        va = [ef(y[a], w[m].to_numpy()[a]) for m in METHODS if m in w]
        vb = [ef(y[b], w[m].to_numpy()[b]) for m in METHODS if m in w]
        # kendalltau is undefined when a half ranks every method equally (e.g. all EF1 zero), so those are counted
        if np.isfinite(va).all() and np.isfinite(vb).all() and len(set(va)) > 1 and len(set(vb)) > 1:
            out.append(float(kendalltau(va, vb).statistic))
        else:
            skipped.append(t)
    return {"targets_used": len(out), "targets_skipped_tied_or_missing": len(skipped),
            "mean_tau_split_half": round(float(np.mean(out)), 3) if out else None}


def main():
    T.mkdir(parents=True, exist_ok=True)
    M = metrics_table()
    rng = np.random.default_rng(SEED)
    out = {"H1": h1(M, rng), "H2": h2(rng), "H3": h3(M, rng), "noise_ceiling": noise_ceiling(rng)}
    # D2 (post hoc): the same hypotheses on the 19 screening-like targets (hit rate <= 5%), where EF1% is not
    # mechanically capped near 2 as it is on the CYP/SYK counterscreens
    low = set(M[(M["eval"] == "new") & (M.hit_rate <= 0.05)].target)
    Ml = M[(M["eval"] != "new") | M.target.isin(low)]
    rng2 = np.random.default_rng(SEED)
    out["posthoc_hit_rate_le_5pct"] = {"targets": len(low), "H1": h1(Ml, rng2), "H3": h3(Ml, rng2)}
    for ev in ("new", "lit_cv", "lit_pub"):
        g = M[M["eval"] == ev]
        if g.empty:
            continue
        out[f"median_ef1_{ev}"] = {v: g[g.variant == v].groupby("method").ef1.median().round(3).to_dict() for v in g.variant.unique()}
        out[f"median_bedroc_{ev}"] = {v: g[g.variant == v].groupby("method").bedroc.median().round(3).to_dict() for v in g.variant.unique()}
    (T / "primary.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(out, indent=1, default=float)[:4000])


if __name__ == "__main__":
    main()
