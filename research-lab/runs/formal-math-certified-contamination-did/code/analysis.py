"""Primary and secondary analyses (plan section 5; deviations D1-D5). Written and committed before any verification
result was read. Inputs: data/verified/<prover>.jsonl (key, idx, status), data/samples/<prover>.jsonl (for the set of
item-versions sampled), results/tables/leak_status_by_prover.csv, leak_pairs_bench_minif2f.csv, reforms certification.
Outputs: results/tables/{pass_by_version.csv, primary.json, secondary.csv, statement_changes.csv}.

Unit: (item, prover) with an original and at least one certified reformulation sampled.
D9 (after the independent review): whitespace-only "changed statement" rejections re-checked (data/verified/<p>_ws.jsonl
overrides); R1 versions textually identical to the original dropped; vacuous benchmark items (results/tables/
bench_items.csv) dropped; added the documented-training and test/valid-only contrasts, per-sample DiDs by prover, the
solve-rate DiD by version and the preregistered mixed logistic model.
d = pass@32(original) - mean pass@32 over the certified reformulations.
DiD = mean d (leaked) - mean d (clean), pooled over DeepSeek-Prover-V2, Goedel-Prover-V2 and Kimina (H1), with a
one-sided 95% item-cluster bootstrap (10,000 draws; items resampled with all their provers)."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
PRIMARY = ["dsp_v2", "goedel_v2", "kimina"]
OWN = {"goedel_v2": ["goedel_pset", "sft_v2", "goedel_lwproofs"], "kimina": ["numina_lean"], "dsp_v2": ["dsp_v1"], "stp": ["stp"]}
RNG = np.random.default_rng(20261009)
B = 10000


def identical_r1():
    """D9: items whose R1 is textually identical to the original (no binders to rename or reorder)."""
    r = pd.read_parquet(RUN / "data" / "reforms.parquet")
    n = lambda x: " ".join(str(x).split())  # noqa: E731
    return set(r.id[r.R1.map(n) == r.orig.map(n)])


def vacuous_items():
    f = TAB / "bench_items.csv"
    if not f.exists():
        return set()
    b = pd.read_csv(f)
    return set(b.item[b.vacuous.fillna(False).astype(bool)])


SAMPLES = []


def load_versions(prover, drop_r1=frozenset()):
    v = pd.DataFrame([json.loads(l) for l in open(RUN / "data" / "verified" / f"{prover}.jsonl")])
    ws = RUN / "data" / "verified" / f"{prover}_ws.jsonl"
    if ws.exists():  # D9: spacing-insensitive re-check of "changed statement" rejections
        o = pd.DataFrame([json.loads(l) for l in open(ws)])
        if len(o):
            o = o.set_index(["key", "idx"]).status
            k = pd.MultiIndex.from_frame(v[["key", "idx"]])
            v["status"] = np.where(k.isin(o.index), o.reindex(k).values, v.status)
    v[["item", "version"]] = v.key.str.split("|", expand=True)
    v = v[~((v.version == "R1") & v["item"].isin(drop_r1))]
    v["ok"] = v.status == "ok"
    SAMPLES.append(v.assign(prover=prover)[["item", "version", "prover", "ok"]])
    g = v.groupby(["item", "version"]).agg(n=("ok", "size"), k=("ok", "sum"),
                                          changed=("status", lambda s: (s == "changed statement").mean()),
                                          truncated=("status", lambda s: (s == "truncated").mean())).reset_index()
    g["pass32"] = (g.k > 0).astype(float)
    g["rate"] = g.k / g.n
    g["prover"] = prover
    return g


def unit_table(g, leak):
    o = g[g.version == "orig"].set_index("item")
    r = g[g.version != "orig"].groupby("item").agg(pass32_ref=("pass32", "mean"), rate_ref=("rate", "mean"), n_ref=("version", "size"))
    u = o[["pass32", "rate"]].join(r, how="inner")
    u["d"] = u.pass32 - u.pass32_ref
    u["d_rate"] = u.rate - u.rate_ref
    u = u.join(leak, how="left")
    u["leaked"] = u.leaked.fillna(False).astype(bool)
    return u.reset_index()


def did(units, col="d"):
    """DiD and one-sided 95% item-cluster bootstrap bounds. Items are resampled with all their (item, prover) units:
    multinomial item weights applied to per-item sums (equivalent to resampling items with replacement)."""
    est = units[units.leaked][col].mean() - units[~units.leaked][col].mean()
    agg = units.groupby("item").apply(lambda g: pd.Series({"sL": g[g.leaked][col].sum(), "nL": g.leaked.sum(),
                                                            "sC": g[~g.leaked][col].sum(), "nC": (~g.leaked).sum()}))
    n = len(agg)
    W = RNG.multinomial(n, np.full(n, 1 / n), size=B)  # B x n_items
    with np.errstate(invalid="ignore", divide="ignore"):
        draws = W @ agg.sL.values / (W @ agg.nL.values) - W @ agg.sC.values / (W @ agg.nC.values)
    lo, hi = np.nanpercentile(draws, [5, 95])
    return dict(DiD=float(est), lower95_one_sided=float(lo), upper95_one_sided=float(hi), n_leaked=int(units.leaked.sum()),
                n_clean=int((~units.leaked).sum()), mean_d_leaked=float(units[units.leaked][col].mean()),
                mean_d_clean=float(units[~units.leaked][col].mean()), sd_d=float(units[col].std()))


def verdict(r, mde):
    if r["DiD"] >= 0.10 and r["lower95_one_sided"] > 0:
        return "Supported"
    if r["n_leaked"] < 20:
        return "Inconclusive (fewer than 20 leaked pairs)"
    if r["upper95_one_sided"] < 0.10 and mde <= 0.10:
        return "Refuted"
    return "Inconclusive"


def mixed_model(P, verified):
    """Plan section 5 secondary: success ~ reformulated x leaked + (1|item) + (1|prover), sample level, primary provers.
    Variational Bayes (statsmodels BinomialBayesMixedGLM); no Laplace/quadrature GLMM is available (D9)."""
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    keep = P.set_index(["item", "prover"]).leaked
    d = verified[verified.set_index(["item", "prover"]).index.isin(keep.index)].copy()
    d["leaked"] = keep.reindex(pd.MultiIndex.from_frame(d[["item", "prover"]])).astype(float).values
    d["reformulated"] = (d.version != "orig").astype(float)
    d["success"] = d.ok.astype(float)
    m = BinomialBayesMixedGLM.from_formula("success ~ reformulated * leaked", {"item": "0 + C(item)", "prover": "0 + C(prover)"}, d)
    import warnings
    with warnings.catch_warnings(record=True) as w:  # D10: larger optimiser budget; record convergence
        warnings.simplefilter("always")
        r = m.fit_vb(minim_opts={"maxiter": 5000})
    converged = not any("converge" in str(x.message).lower() for x in w)
    names = list(m.exog_names)
    i = names.index("reformulated:leaked")
    est, sd = float(r.fe_mean[i]), float(r.fe_sd[i])
    out = dict(term="reformulated:leaked", log_odds=est, sd=sd, lower95=est - 1.96 * sd, upper95=est + 1.96 * sd,
               odds_ratio=float(np.exp(est)), n_samples=len(d), n_units=int(len(keep)),
               fixed_effects={n: [float(a), float(b)] for n, a, b in zip(names, r.fe_mean, r.fe_sd)},
               vc_sd_posterior_mean={n: float(np.exp(a)) for n, a in zip(m.vcp_names, r.vcp_mean)},
               optimiser_converged=converged, maxiter=5000)
    return out


def main(*args):
    st = pd.read_csv(TAB / "leak_status_by_prover.csv")
    pairs = pd.read_csv(TAB / "leak_pairs_bench_minif2f.csv")
    mde = json.load(open(TAB / "mde.json"))
    allg, units, rows_v = [], [], []
    drop_r1, vac = identical_r1(), vacuous_items()
    print(f"D9: {len(drop_r1)} identical-R1 items, {len(vac)} vacuous items dropped: {sorted(vac)}")
    for p in PRIMARY + ([] if "--no-stp" in args else ["stp"]):  # --no-stp while STP verification is incomplete
        f = RUN / "data" / "verified" / f"{p}.jsonl"
        if not f.exists():
            continue
        g = load_versions(p, drop_r1)
        g = g[~g["item"].isin(vac)]
        allg.append(g)
        if p == "stp":
            own = set(pairs[pairs.corpus.isin(OWN["stp"])].item)
            leak = pd.Series({i: i in own for i in g.item.unique()}, name="leaked")
        else:
            s = st[(st.prover == p) & (st.scope == "own corpora")].set_index("item").leaked
            leak = s
        u = unit_table(g, leak)
        u["prover"] = p
        # secondary leak definitions
        u["leaked_L0L1"] = u["item"].isin(set(pairs[pairs.corpus.isin(OWN[p]) & pairs.tier.isin(["L0", "L1"])].item))
        u["leaked_any_corpus"] = u["item"].isin(set(pairs.item))
        u["valid"] = u["item"].str.startswith("valid/")
        units.append(u)
    allg = pd.concat(allg)
    allg.to_csv(TAB / "pass_by_version.csv", index=False)
    U = pd.concat(units, ignore_index=True)
    U.to_csv(TAB / "units.csv", index=False)
    P = U[U.prover.isin(PRIMARY)]
    prim = did(P)
    sd_obs = prim["sd_d"]
    prim["MDE_preregistered_pp"] = mde["MDE_pp"]
    prim["MDE_design_D4_pp"] = 100 * 2.49 * 0.30 * np.sqrt(1 / max(prim["n_leaked"], 1) + 1 / prim["n_clean"])
    prim["MDE_observed_sd_pp"] = 100 * 2.49 * sd_obs * np.sqrt(1 / max(prim["n_leaked"], 1) + 1 / prim["n_clean"])
    prim["verdict"] = verdict(prim, prim["MDE_design_D4_pp"] / 100)
    json.dump(prim, open(TAB / "primary.json", "w"), indent=1)
    print("PRIMARY", json.dumps(prim, indent=1))
    rows = []

    def add(label, units, col="d"):
        if units.leaked.sum() and (~units.leaked).sum():
            r = did(units, col)
            r["analysis"] = label
            rows.append(r)
    for p in PRIMARY + ["stp"]:
        add(f"prover {p}", U[U.prover == p])
    add("per-sample pass rate (pooled)", P, "d_rate")
    add("L0/L1 leaks only (pooled)", P.assign(leaked=P.leaked_L0L1))
    add("leak against any corpus (pooled, sampled items)", P.assign(leaked=P.leaked_any_corpus))
    k = pd.read_parquet(RUN / "data" / "raw" / "minif2f_test" / "data" / "train-00000-of-00001.parquet")
    d15 = pd.read_json(RUN / "data" / "raw" / "dsp15_minif2f.jsonl", lines=True)
    t15 = d15[d15.split == "test"].set_index("name").formal_statement
    revised = {"test/" + r.name for r in k.itertuples() if t15.get(r.name, "").strip() not in r.formal_statement}
    add("excluding the 19 Kimina-revised items (pooled)", P[~P["item"].isin(revised)])
    add("STP prover, leak against STP corpus", U[U.prover == "stp"])
    # D9 additions
    for p in PRIMARY + ["stp"]:
        add(f"per-sample, prover {p}", U[U.prover == p], "d_rate")
    doc = P.assign(leaked=P.leaked | ((P.prover == "dsp_v2") & P.valid))
    add("documented training: miniF2F-valid leaked for DeepSeek-Prover-V2 (pooled)", doc)
    add("documented training, per-sample (pooled)", doc, "d_rate")
    add("documented training: DeepSeek-Prover-V2 alone", doc[doc.prover == "dsp_v2"])
    add("test items only (pooled)", P[~P.valid])
    add("test items only, per-sample (pooled)", P[~P.valid], "d_rate")
    add("valid items only (pooled)", P[P.valid])
    S = U[U.prover == "stp"]
    add("STP, documented training: miniF2F-valid leaked", S.assign(leaked=S.leaked | S.valid))
    add("STP, test items only", S[~S.valid])
    pd.DataFrame(rows).to_csv(TAB / "secondary.csv", index=False)
    # solve-rate DiD by version (descriptive; genuine reformulations only)
    G = allg.copy()
    for p in PRIMARY + ["stp"]:
        gp = G[G.prover == p]
        lk = U[U.prover == p].set_index("item").leaked
        o = gp[gp.version == "orig"].set_index("item")
        for ver in ("R1", "R2"):
            r = gp[gp.version == ver].set_index("item")
            uv = o[["pass32", "rate"]].join(r[["pass32", "rate"]], rsuffix="_v", how="inner").join(lk, how="inner")
            uv["d"], uv["d_rate"] = uv.pass32 - uv.pass32_v, uv.rate - uv.rate_v
            uv = uv.reset_index()
            for col in ("d", "d_rate"):
                if uv.leaked.sum() and (~uv.leaked).sum():
                    x = did(uv, col)
                    rows_v.append(dict(prover=p, version=ver, metric="pass32" if col == "d" else "per-sample", **x,
                                       leaked_orig=float(uv[uv.leaked]["rate" if col == "d_rate" else "pass32"].mean()),
                                       leaked_ver=float(uv[uv.leaked]["rate_v" if col == "d_rate" else "pass32_v"].mean()),
                                       clean_orig=float(uv[~uv.leaked]["rate" if col == "d_rate" else "pass32"].mean()),
                                       clean_ver=float(uv[~uv.leaked]["rate_v" if col == "d_rate" else "pass32_v"].mean())))
    pd.DataFrame(rows_v).to_csv(TAB / "did_by_version.csv", index=False)
    print(pd.DataFrame(rows_v)[["prover", "version", "metric", "DiD", "lower95_one_sided", "upper95_one_sided", "leaked_orig", "leaked_ver", "clean_orig", "clean_ver"]].round(3).to_string())
    if "--no-mixed" not in args:
        mm = mixed_model(P, pd.concat(SAMPLES))
        json.dump(mm, open(TAB / "mixed_model.json", "w"), indent=1)
        print("MIXED", {k: v for k, v in mm.items() if k != "fixed_effects"})
    # D10: sensitivity without the items that lost their leak status in D9 (appended last so no other draws change)
    d8 = TAB.parent / "tables_D8" / "leak_status_by_prover.csv"
    if d8.exists():
        o = pd.read_csv(d8)
        o = o[(o.scope == "own corpora") & o.leaked]
        was = set(zip(o.prover, o["item"]))
        flip = P[[(not l) and ((p, i) in was) for p, i, l in zip(P.prover, P["item"], P.leaked)]]
        n0 = len(rows)
        add(f"excluding the {len(flip)} items that lost leak status in D9 (pooled)", P.drop(flip.index))
        add(f"excluding the {len(flip)} items that lost leak status in D9, per-sample (pooled)", P.drop(flip.index), "d_rate")
        pd.DataFrame(rows).to_csv(TAB / "secondary.csv", index=False)
        print(pd.DataFrame(rows[n0:])[["analysis", "DiD", "lower95_one_sided", "upper95_one_sided", "n_leaked", "n_clean"]].round(4).to_string())
    print(pd.DataFrame(rows)[["analysis", "DiD", "lower95_one_sided", "upper95_one_sided", "n_leaked", "n_clean", "mean_d_leaked", "mean_d_clean"]].round(4).to_string())
    # statement-change diagnostic: share of outputs rejected for restating a different theorem, by version and leak
    allg = allg.merge(U[["item", "prover", "leaked"]], on=["item", "prover"], how="left")
    sc = allg.groupby(["prover", "version", "leaked"]).agg(changed=("changed", "mean"), truncated=("truncated", "mean"),
                                                          pass32=("pass32", "mean"), rate=("rate", "mean"), n=("item", "size")).reset_index()
    sc.to_csv(TAB / "statement_changes.csv", index=False)
    print(sc.round(3).to_string())


if __name__ == "__main__":
    main(*sys.argv[1:])
