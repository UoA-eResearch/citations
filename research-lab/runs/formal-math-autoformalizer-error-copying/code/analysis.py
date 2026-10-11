"""Plan sections 6 and 8: the primary rate ratio, the decision rule, and the secondary analyses.

Reads results/catalogue/frozen.jsonl and data/classified/<model>{,_outputs}.jsonl. An output counts as a defect copy
if it elaborates and is certified equivalent to the condition's defective reference (D for O and P, D' for T); the
denominator is every requested temperature sample (16 per model x item x condition), so failed requests, outputs with
no statement and outputs that do not elaborate count as non-copies.
Writes results/tables/primary.json, secondary.json and per-model / per-item tables."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
CAT, TAB = RUN / "results" / "catalogue", RUN / "results" / "tables"
PRIMARY = ["kimina", "goedel", "herald"]
MODELS = PRIMARY + ["dsp_v2", "qwen"]
N, B, SEED = 16, 2000, 20261012


def outcomes(model):
    """One row per requested output: key, idx, cls in {copy, correct, other, noelab}, verbatim."""
    cl = {}
    p = RUN / "data" / "classified" / f"{model}.jsonl"
    if p.exists():
        for line in open(p):
            r = json.loads(line)
            cl[r["uid"]] = r
    rows = []
    for line in open(RUN / "data" / "classified" / f"{model}_outputs.jsonl"):
        o = json.loads(line)
        c = cl.get(o.get("uid"), {})
        cls = ("noelab" if not c.get("elab") else "copy" if c.get("copy") and not c.get("correct")
               else "correct" if c.get("correct") and not c.get("copy") else "other")
        rows.append(dict(model=model, key=o["key"], idx=o["idx"], cls=cls, verbatim=bool(o.get("verbatim")),
                         to_D=bool(c.get("to_D")), to_C=bool(c.get("to_C"))))
    df = pd.DataFrame(rows)
    df["item"], df["cond"] = df.key.str.rsplit("|", n=1).str[0], df.key.str.rsplit("|", n=1).str[1]
    return df


def counts(df, items, models, cond, what="copy", greedy=False):
    """Per item: number of `what` outputs over the given models and condition (temperature samples unless greedy)."""
    d = df[df.model.isin(models) & (df.cond == cond) & df.item.isin(items)]
    d = d[d.idx == "g"] if greedy else d[d.idx != "g"]
    x = d.assign(hit=(d.cls == what) if what != "verbatim" else d.verbatim).groupby("item").hit.sum()
    return x.reindex(items, fill_value=0).to_numpy()


def rr(xo, xt, no, nt):
    return ((xo + 0.5) / no) / ((xt + 0.5) / nt)


def ratio(xo, xt, n_models, n=N, seed=SEED):
    """Pooled RR with the item-cluster percentile bootstrap (plan section 6)."""
    I = len(xo)
    no = nt = I * n_models * n
    est = rr(xo.sum(), xt.sum(), no, nt)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, I, (B, I))
    bs = rr(xo[idx].sum(1), xt[idx].sum(1), no, nt)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return dict(RR=float(est), lower95=float(lo), upper95=float(hi), x_O=int(xo.sum()), x_T=int(xt.sum()), n_O=no, n_T=nt,
                rate_O=float(xo.sum() / no), rate_T=float(xt.sum() / nt), items=I)


def verdict(r):
    if r["x_O"] + r["x_T"] < 20:
        return "Inconclusive (too little defect output)"
    if r["RR"] >= 3 and r["lower95"] > 1.5:
        return "Supported"
    if r["upper95"] < 3:
        return "Refuted"
    return "Inconclusive"


def main():
    TAB.mkdir(parents=True, exist_ok=True)
    fz = pd.read_json(CAT / "frozen.jsonl", lines=True)
    prim = fz[(fz.role == "primary")]
    inc_tw = sorted(prim[(prim.set == "included") & prim.N_twin.notna()].item)
    df = pd.concat([outcomes(m) for m in MODELS if (RUN / "data" / "classified" / f"{m}_outputs.jsonl").exists()])
    present = sorted(df.model.unique())

    # primary
    xo, xt = counts(df, inc_tw, PRIMARY, "O"), counts(df, inc_tw, PRIMARY, "T")
    p = ratio(xo, xt, len(PRIMARY))
    p["verdict"] = verdict(p)
    p["any_excess"] = p["lower95"] > 1
    p["models"] = PRIMARY
    p["mde_caveat"] = len(inc_tw) < 40
    json.dump(p, open(TAB / "primary.json", "w"), indent=1)
    pd.DataFrame(dict(item=inc_tw, copies_O=xo, analog_T=xt)).to_csv(TAB / "primary_by_item.csv", index=False)

    sec = {}
    # 1. by model
    sec["by_model"] = {m: ratio(counts(df, inc_tw, [m], "O"), counts(df, inc_tw, [m], "T"), 1) for m in present}
    # 2. originals vs paraphrases (included items with an accepted paraphrase)
    inc_p = sorted(prim[(prim.set == "included") & prim.paraphrase.notna()].item)
    sec["O_vs_P"] = ratio(counts(df, inc_p, PRIMARY, "O"), counts(df, inc_p, PRIMARY, "P"), len(PRIMARY))
    # 3. greedy outputs: copy share by condition
    sec["greedy"] = {c: dict(copies=int(counts(df, inc_tw, PRIMARY, c, greedy=True).sum()), n=len(inc_tw) * len(PRIMARY))
                     for c in ("O", "T")}
    sec["greedy"]["P"] = dict(copies=int(counts(df, inc_p, PRIMARY, "P", greedy=True).sum()), n=len(inc_p) * len(PRIMARY))
    # 4. verbatim copies of the defective reference
    sec["verbatim"] = {c: int(counts(df, inc_tw if c != "P" else inc_p, PRIMARY, c, "verbatim").sum()) for c in ("O", "T", "P")}
    # 5. by source and category
    sec["by_source"] = {}
    for s, g in prim[prim.item.isin(inc_tw)].groupby("source"):
        it = sorted(g.item)
        sec["by_source"][s] = ratio(counts(df, it, PRIMARY, "O"), counts(df, it, PRIMARY, "T"), len(PRIMARY))
    sec["by_category"] = {}
    for c, g in prim[prim.item.isin(inc_tw)].groupby("category"):
        it = sorted(g.item)
        sec["by_category"][str(c)] = ratio(counts(df, it, PRIMARY, "O"), counts(df, it, PRIMARY, "T"), len(PRIMARY))
    # 6. accuracy: correct rate and equivalence to the benchmark's own reference
    nn = len(inc_tw) * len(PRIMARY) * N
    sec["accuracy"] = {c: dict(correct=float(counts(df, inc_tw, PRIMARY, c, "correct").sum() / nn),
                               copy=float(counts(df, inc_tw, PRIMARY, c, "copy").sum() / nn)) for c in ("O", "T")}
    # 7. negative control (v2-introduced defects): copy rate of the v2 defect and correct (v1) rate, by model
    ctl = sorted(fz[fz.role == "control"].item)
    sec["control"] = {m: dict(copy=int(counts(df, ctl, [m], "O").sum()), correct=int(counts(df, ctl, [m], "O", "correct").sum()),
                              n=len(ctl) * N) for m in present}
    # 8. sensitivities
    one = sorted(prim[prim.set.isin(["included", "one_rater"]) & prim.N_twin.notna()].item)
    sec["one_rater_set"] = ratio(counts(df, one, PRIMARY, "O"), counts(df, one, PRIMARY, "T"), len(PRIMARY))
    tc = sorted(prim[(prim.set == "included") & prim.N_twin.notna() & prim.twin_truth_certified].item)
    sec["truth_certified_twins"] = ratio(counts(df, tc, PRIMARY, "O"), counts(df, tc, PRIMARY, "T"), len(PRIMARY)) if tc else None
    d = df[df.model.isin(PRIMARY) & df.item.isin(inc_tw) & (df.idx != "g")]
    el = d[d.cls != "noelab"].groupby("cond").agg(n=("cls", "size"), copies=("cls", lambda s: int((s == "copy").sum())))
    sec["among_elaborating"] = {c: dict(n=int(r.n), copies=int(r.copies), rate=float(r.copies / r.n) if r.n else None)
                                for c, r in el.iterrows()}
    # 9. classification rate: share "other" among elaborating outputs, by model and condition
    dd = df[df.item.isin(inc_tw + inc_p) & (df.idx != "g")]
    tab = dd.groupby(["model", "cond", "cls"]).size().unstack(fill_value=0)
    tab.to_csv(TAB / "classes_by_model_condition.csv")
    json.dump(sec, open(TAB / "secondary.json", "w"), indent=1, default=float)
    print(json.dumps(p, indent=1))
    print(json.dumps(sec["by_model"], indent=1)[:2000])


if __name__ == "__main__":
    main()
