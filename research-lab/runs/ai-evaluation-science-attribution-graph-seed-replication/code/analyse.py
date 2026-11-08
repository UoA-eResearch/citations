"""H1, H2 and secondaries (plan sections 0-1). Runs locally on data/match/*.jsonl copied from the A100.
-> results/tables/primary.json

H1: per prompt, the share of X's top-10 features with a counterpart in Y, averaged over the 6 ordered A/B/C pairs; the
median over prompts, with a bootstrap over prompts stratified by family (2,000). Supported if the median and its 95%
upper bound are below 0.6; Refuted if the lower bound is at least 0.6; otherwise Inconclusive.
H2: per prompt, subspace replication minus node replication (same averaging); mean paired difference with the same
bootstrap. Supported if the interval is above 0; Refuted if it lies below 0 or within +-0.05 of 0; otherwise
Inconclusive.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
M, T = RUN / "data" / "match", RUN / "results" / "tables"
ABC = [("A", "B"), ("B", "A"), ("A", "C"), ("C", "A"), ("B", "C"), ("C", "B")]
SEED, B = 20261105, 2000


def load(pairs):
    rows = []
    for X, Y in pairs:
        f = M / f"{X}_{Y}.jsonl"
        if f.exists():
            for line in f.read_text().splitlines():
                if line.strip():
                    rows.append({**json.loads(line), "X": X, "Y": Y})
    return pd.DataFrame(rows)


def per_prompt(d, col):
    a = d.groupby(["i", "family", "X", "Y"])[col].mean().reset_index()
    return a.groupby(["i", "family"])[col].mean()


def boot(per, stat, rng):
    fam = per.index.get_level_values("family")
    groups = {f: per[fam == f].to_numpy() for f in np.unique(fam)}
    bs = []
    for _ in range(B):
        x = np.concatenate([g[rng.integers(0, len(g), len(g))] for g in groups.values()])
        bs.append(stat(x))
    return [round(float(np.percentile(bs, 2.5)), 4), round(float(np.percentile(bs, 97.5)), 4)]


def main():
    rng = np.random.default_rng(SEED)
    d = load(ABC)
    out = {"features_matched": int(len(d)), "prompts": int(d.i.nunique())}
    node = per_prompt(d, "counterpart")
    sub = per_prompt(d, "subspace")
    med = float(node.median())
    ci = boot(node, np.median, rng)
    out["H1"] = {"median_node_replication": round(med, 4), "ci": ci, "mean": round(float(node.mean()), 4),
                 "verdict": "Supported" if med < 0.6 and ci[1] < 0.6 else "Refuted" if ci[0] >= 0.6 else "Inconclusive"}
    diff = (sub - node)
    dci = boot(diff, np.mean, rng)
    within = -0.05 <= dci[0] and dci[1] <= 0.05
    out["H2"] = {"mean_subspace_replication": round(float(sub.mean()), 4), "mean_node_replication": round(float(node.mean()), 4),
                 "mean_paired_difference": round(float(diff.mean()), 4), "ci": dci,
                 "verdict": "Supported" if dci[0] > 0 and not within else "Refuted" if dci[1] < 0 or within else "Inconclusive"}
    # secondary 1 and 6: data order and the public set
    for lab, pairs in (("data_order_A_D", [("A", "D"), ("D", "A")]), ("public_vs_A", [("public", "A"), ("A", "public")])):
        e = load(pairs)
        if len(e):
            n2 = per_prompt(e, "counterpart")
            out[lab] = {"median_node_replication": round(float(n2.median()), 4), "mean": round(float(n2.mean()), 4),
                        "mean_subspace": round(float(per_prompt(e, "subspace").mean()), 4), "prompts": int(len(n2))}
    # secondary 5: family and layer depth
    out["by_family"] = {f: {"median_node": round(float(g.median()), 4), "prompts": int(len(g))}
                        for f, g in node.groupby(level="family")}
    d["depth"] = pd.cut(d.layer, [-1, 6, 13, 20, 27], labels=["0-6", "7-13", "14-20", "21-27"])
    out["by_layer_depth"] = {str(k): {"node": round(float(g.counterpart.mean()), 4), "subspace": round(float(g.subspace.mean()), 4), "features": int(len(g))}
                             for k, g in d.groupby("depth", observed=True)}
    # stratified by graph sparsity and error share (limits)
    d["err_bin"] = pd.qcut(d.error_share_x, 3, labels=["low", "mid", "high"], duplicates="drop")
    out["by_error_share_tercile"] = {str(k): round(float(g.counterpart.mean()), 4) for k, g in d.groupby("err_bin", observed=True)}
    # sensitivities: cosine-only matching at three thresholds; top-5 cut
    for th in (0.6, 0.7, 0.8):
        d[f"cos_{th}"] = d.best_cos_active.fillna(0) >= th
        out[f"cosine_only_{th}"] = round(float(per_prompt(d, f"cos_{th}").median()), 4)
    out["top5_node_replication_median"] = round(float(per_prompt(d[d["rank"] < 5], "counterpart").median()), 4)
    out["ablation_effect_zero_share"] = round(float((d.effect_x == 0).mean()), 4)
    # secondary 7: seeds needed - share of A's top-10 features with counterparts in both B and C, one, or none
    ab = d[(d.X == "A") & (d.Y == "B")].set_index(["i", "rank"]).counterpart
    ac = d[(d.X == "A") & (d.Y == "C")].set_index(["i", "rank"]).counterpart
    j = pd.concat([ab.rename("B"), ac.rename("C")], axis=1).dropna()
    k = j.B.astype(int) + j.C.astype(int)
    out["A_top10_replicated_in"] = {"both": round(float((k == 2).mean()), 4), "one": round(float((k == 1).mean()), 4), "none": round(float((k == 0).mean()), 4)}
    (T / "primary.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
