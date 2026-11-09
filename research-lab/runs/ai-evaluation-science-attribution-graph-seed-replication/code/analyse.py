"""H1, H2 and secondaries (plan sections 0-1). Runs locally on data/match/*.jsonl copied from the A100.
-> results/tables/primary.json

H1: per prompt, the share of X's top-10 features with a counterpart in Y, averaged over the 6 ordered A/B/C pairs; the
median over prompts, with a bootstrap over prompts stratified by family (2,000). Supported if the median and its 95%
upper bound are below 0.6; Refuted if the lower bound is at least 0.6; otherwise Inconclusive.
H2: per prompt, subspace replication minus node replication (same averaging); mean paired difference with the same
bootstrap. Supported if the interval is above 0; Refuted if it lies below 0 or within +-0.05 of 0; otherwise
Inconclusive.

D4 (after the independent review): rows come from data/match_d4/ (rebuilt arithmetic prompts; candidate effects stored;
deduplicated subspace; nulls). The preregistered H1 and H2 are computed exactly as before. Post hoc, labelled
sensitivities are added in "posthoc_d4": family exclusions, BOS-margin restriction, the position-1 stratification
(first token after BOS), a two-way bootstrap over prompts and features, top-k and full-rule threshold sensitivity with
verdicts, the paired A-vs-D difference, the subspace nulls and the effect of deduplication. The first run's output is
results/tables/primary_v1_pre_d4.json.
"""
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
M, T = RUN / "data" / os.environ.get("MATCH_DIR", "match_d4"), RUN / "results" / "tables"
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


def verdict(med, ci):
    return "Supported" if med < 0.6 and ci[1] < 0.6 else "Refuted" if ci[0] >= 0.6 else "Inconclusive"


def h1(d, col="counterpart", seed=SEED):
    node = per_prompt(d, col)
    med = float(node.median())
    ci = boot(node, np.median, np.random.default_rng(seed))
    return {"median": round(med, 4), "ci": ci, "prompts": int(len(node)), "verdict": verdict(med, ci)}


def rule(d, cos, frac):
    """The full counterpart rule at other thresholds, from the stored candidates [idx, cosine, effect]."""
    return [any(c[1] >= cos and e != 0 and c[2] * e > 0 and abs(c[2]) >= frac * abs(e) for c in cs)
            for cs, e in zip(d.candidates, d.effect_x)]


def two_way(d, rng, reps=1000):
    """Bootstrap over prompts (within family) and over feature-direction units (X, layer, idx) at once."""
    d = d.copy()
    d["unit"] = d.X + ":" + d.layer.astype(str) + ":" + d.idx.astype(str)
    units = d.unit.unique()
    uix = pd.Series(np.arange(len(units)), index=units)[d.unit].to_numpy()
    fam = d.groupby("i").family.first()
    by_fam = {f: g.index.to_numpy() for f, g in fam.groupby(fam)}
    cp = d.counterpart.astype(float).to_numpy()
    keys = d.i.to_numpy(), (d.X + d.Y).to_numpy()
    meds = []
    for _ in range(reps):
        w = np.bincount(rng.integers(0, len(units), len(units)), minlength=len(units))[uix].astype(float)
        t = pd.DataFrame({"i": keys[0], "dir": keys[1], "w": w, "wc": w * cp})
        g = t.groupby(["i", "dir"])[["w", "wc"]].sum()
        g = g[g.w > 0]
        per = (g.wc / g.w).groupby(level="i").mean()
        pick = np.concatenate([rng.choice(ix, len(ix)) for ix in by_fam.values()])
        vals = per.reindex(pick).dropna().to_numpy()
        meds.append(np.median(vals))
    return {"ci": [round(float(np.percentile(meds, 2.5)), 4), round(float(np.percentile(meds, 97.5)), 4)],
            "share_of_replicates_ge_0.6": round(float(np.mean(np.array(meds) >= 0.6)), 3), "reps": reps}


def posthoc(d, rng):
    """D4 post hoc sensitivities (labelled; not the preregistered verdict)."""
    out = {}
    prompts = {p["i"]: p for p in (json.loads(l) for l in (T / "prompts.jsonl").read_text().splitlines())}
    fams = d.groupby("family").i.nunique()
    big = [f for f, n in fams.items() if n >= 15]
    out["families"] = {f: int(n) for f, n in fams.items()}
    out["H1_without_antonym"] = h1(d[d.family != "antonym"])
    out["H1_families_with_ge_15_prompts"] = {**h1(d[d.family.isin(big)]), "families": big}
    out["H1_without_arithmetic"] = h1(d[d.family != "arithmetic"])
    ok_bos = {i for i, p in prompts.items() if (p.get("bos_margin") or 0) >= 2}
    out["H1_prompts_meeting_margin_with_BOS"] = h1(d[d.i.isin(ok_bos)])
    # position 1 (first token after BOS)
    p1 = d.pos == 1
    out["position_1"] = {"share_of_top10_rows": round(float(p1.mean()), 4),
                         "replication_pos1": round(float(d[p1].counterpart.mean()), 4),
                         "replication_other": round(float(d[~p1].counterpart.mean()), 4),
                         "H1_without_pos1": h1(d[~p1]),
                         "pos1_layers": d[p1].layer.value_counts().sort_index().to_dict(),
                         "share_of_non_replicating_rows_at_pos1": round(float((p1 & ~d.counterpart).sum() / (~d.counterpart).sum()), 4)}
    share = {}
    for S in ("A", "B", "C", "D", "public"):
        n = tot = 0
        for i in prompts:
            f = RUN / "data" / "graphs" / S / f"{i:03d}.json"
            if f.exists():
                g = json.loads(f.read_text())
                if g.get("status") == "ok":
                    n += sum(x["pos"] == 1 for x in g["top10"]); tot += len(g["top10"])
        share[S] = round(n / tot, 4) if tot else None
    out["position_1"]["share_of_top10_by_set"] = share
    late = d.layer >= 14
    out["replication_by_layers"] = {"0-6": round(float(d[d.layer <= 6].counterpart.mean()), 4),
                                    "14-27": round(float(d[late].counterpart.mean()), 4)}
    # feature recurrence and a two-way bootstrap
    d["unit"] = d.X + ":" + d.layer.astype(str) + ":" + d.idx.astype(str)
    up = d.groupby("unit").i.nunique()
    rec = up[up >= 20].index
    out["recurring_units"] = {"units_in_ge_20_prompts": int(len(rec)), "share_of_rows": round(float(d.unit.isin(rec).mean()), 4),
                              "distinct_units": int(len(up))}
    out["H1_two_way_bootstrap"] = two_way(d, rng)
    # the preregistered verdict under 20 other bootstrap seeds (the median sits on a 1/60 lattice)
    node = per_prompt(d, "counterpart")
    vs = [verdict(float(node.median()), boot(node, np.median, np.random.default_rng(1000 + k))) for k in range(20)]
    out["H1_verdict_over_20_bootstrap_seeds"] = {v: vs.count(v) for v in set(vs)}
    # top-k with verdicts
    out["top_k"] = {str(k): h1(d[d["rank"] < k]) for k in (1, 3, 5, 7, 10)}
    # full-rule threshold sensitivity
    grid = {}
    for cos in (0.5, 0.6, 0.7, 0.8, 0.9):
        for frac in (0.3, 0.5, 0.7):
            d["_r"] = rule(d, cos, frac)
            grid[f"cos{cos}_mag{frac}"] = h1(d, "_r")
    out["threshold_grid"] = grid
    # G3 invariants (asserted): a counterpart needs an active candidate at cosine >= 0.7; shares lie in [0, 1];
    # every top feature's own ablation effect is non-zero; 199 prompts x 10 features x 6 directions
    assert not (d.counterpart & (d.best_cos_active.fillna(0) < 0.7)).any()
    assert (d.subspace_norm.between(0, 1.0001)).all() and (d.effect_x != 0).all()
    assert len(d) == d.i.nunique() * 10 * 6
    out["invariants_checked"] = ["counterpart implies active cosine >= 0.7", "subspace norms in [0, 1]", "own effects non-zero",
                                 f"{len(d)} rows = {d.i.nunique()} prompts x 10 x 6"]
    out["rule_check_cos0.7_mag0.5_equals_stored"] = bool((pd.Series(rule(d, 0.7, 0.5), index=d.index) == d.counterpart).all())
    # by direction
    out["by_direction"] = {f"{X}->{Y}": round(float(g.groupby("i").counterpart.mean().median()), 4) for (X, Y), g in d.groupby(["X", "Y"])}
    # subspace: dedup effect and nulls
    out["subspace"] = {"mean_norm": round(float(d.subspace_norm.mean()), 4), "mean_norm_with_duplicates": round(float(d.subspace_norm_dup.mean()), 4),
                       "share_ge_0.7": round(float(d.subspace.mean()), 4),
                       "null_other_family_share_ge_0.7": round(float((d.null_other_family >= 0.7).mean()), 4),
                       "null_same_family_share_ge_0.7": round(float((d.null_same_family >= 0.7).mean()), 4),
                       "null_other_family_mean_norm": round(float(d.null_other_family.mean()), 4),
                       "null_same_family_mean_norm": round(float(d.null_same_family.mean()), 4)}
    d["null_o"] = d.null_other_family >= 0.7
    diff = per_prompt(d, "subspace") - per_prompt(d, "null_o")
    out["subspace"]["paired_minus_other_family_null"] = {"mean": round(float(diff.mean()), 4), "ci": boot(diff, np.mean, rng)}
    d["cos07"] = d.best_cos_active.fillna(0) >= 0.7
    gap = per_prompt(d, "subspace") - per_prompt(d, "cos07")
    out["subspace"]["paired_minus_cosine_only_0.7"] = {"mean": round(float(gap.mean()), 4), "ci": boot(gap, np.mean, rng),
                                                       "share_of_prompts_positive": round(float((gap > 0).mean()), 4)}
    return out


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
    out["by_error_share_tercile_note"] = "row means over top-10 features, not medians per graph"
    # D4: paired data-order difference (same X = A lists): A->D against the mean of A->B and A->C, per prompt
    ad = load([("A", "D")])
    if len(ad):
        pa = ad.groupby(["i", "family"]).counterpart.mean()
        pbc = d[(d.X == "A") & d.Y.isin(["B", "C"])].groupby(["i", "family"]).counterpart.mean()
        pdiff = (pa - pbc).dropna()
        out["data_order_paired_A_D_minus_A_BC"] = {"mean": round(float(pdiff.mean()), 4), "ci": boot(pdiff, np.mean, rng),
                                                   "A_D_mean": round(float(pa.mean()), 4), "A_BC_mean": round(float(pbc.mean()), 4)}
    out["posthoc_d4"] = posthoc(d, np.random.default_rng(SEED + 4))
    # G2 coverage (D4: written here; the first draft's coverage.json was written outside committed code)
    import sys as _s
    _s.path.insert(0, str(RUN.parents[1] / "tools"))
    from coverage import Coverage
    prompts = [json.loads(l)["i"] for l in (T / "prompts.jsonl").read_text().splitlines()]
    ok = fail = 0
    for S in ("A", "B", "C", "D", "public"):
        for i in prompts:
            f = RUN / "data" / "graphs" / S / f"{i:03d}.json"
            st = json.loads(f.read_text()).get("status") if f.exists() else None
            ok += st == "ok"; fail += st != "ok"
    for path in (T / "coverage.json",):
        if path.exists():
            path.unlink()
    cg = Coverage("graphs", T / "coverage.json"); cg.add_counts(ok=ok, drops={"failed or missing": fail}); cg.save()
    pairs = [("A", "B"), ("B", "A"), ("A", "C"), ("C", "A"), ("B", "C"), ("C", "B"), ("A", "D"), ("D", "A"), ("public", "A"), ("A", "public")]
    rows = sum(len(load([pr])) for pr in pairs)
    cm = Coverage("matched_features", T / "coverage.json")
    cm.add_counts(ok=rows, drops={"no row written": len(pairs) * 10 * len(prompts) - rows}); cm.save()
    out["coverage"] = {"graphs_ok": ok, "graphs_failed": fail, "match_rows": rows, "expected_rows": len(pairs) * 10 * len(prompts)}
    (T / "primary.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
