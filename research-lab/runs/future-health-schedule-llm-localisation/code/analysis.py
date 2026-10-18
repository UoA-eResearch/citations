"""Scoring and hypotheses (plan sections 1, 4). Reads data/items.jsonl and data/runs.jsonl. Errors count as incorrect
(and are reported). Writes results/tables/primary.json and results/tables/accuracy.csv."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
B, SEED = 2000, 20261018


def wilson(k, n, z=1.959964):
    if n == 0:
        return [np.nan, np.nan]
    p = k / n; c = (p + z * z / (2 * n)) / (1 + z * z / n); h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [float(c - h), float(c + h)]


def main():
    it = pd.DataFrame([json.loads(l) for l in open(RUN / "data" / "items.jsonl")])
    rn = pd.DataFrame([json.loads(l) for l in open(RUN / "data" / "runs.jsonl")])
    rn = rn.drop_duplicates(["id", "condition"], keep="last")
    d = rn.merge(it[["id", "family", "jurisdiction", "chemical", "answer"]].rename(columns={"answer": "truth"}), on="id")
    d["ok"] = (d.answer == d.truth).astype(float)
    d["err"] = d.answer.isna()
    acc = d.groupby(["condition", "jurisdiction", "family"]).agg(n=("ok", "size"), acc=("ok", "mean"), errors=("err", "sum"),
                                                                  not_stated=("answer", lambda x: (x == "not stated").mean())).reset_index()
    acc.to_csv(T / "accuracy.csv", index=False)
    out = dict(items=int(len(it)), calls=int(len(rn)), errors=int(d.err.sum()))
    ab = d[d.family.isin(["a", "b"])]
    chems = sorted(ab.chemical.unique())
    grp = {c: x for c, x in ab.groupby("chemical")}
    rng = np.random.default_rng(SEED)

    def gap(x, cond):
        y = x[x.condition == cond]
        return y[y.jurisdiction == "NZ"].ok.mean() - y[y.jurisdiction == "AU"].ok.mean()
    draws = []
    for _ in range(B):
        s = pd.concat([grp[c] for c in rng.choice(chems, len(chems))])
        g0, g1 = gap(s, "zero"), gap(s, "retrieval")
        draws.append((g0, g1, 1 - g1 / g0 if g0 != 0 else np.nan))
    dr = np.array(draws)
    ci = lambda v: [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]
    g0, g1 = gap(ab, "zero"), gap(ab, "retrieval")
    h1 = dict(nz_acc=float(ab[(ab.condition == "zero") & (ab.jurisdiction == "NZ")].ok.mean()),
              au_acc=float(ab[(ab.condition == "zero") & (ab.jurisdiction == "AU")].ok.mean()), gap=float(g0), ci=ci(dr[:, 0]))
    h1["verdict"] = "Supported" if h1["ci"][1] < 0 else "Refuted" if h1["ci"][0] >= 0 else "Inconclusive"
    out["H1"] = h1
    h2 = dict(gap_retrieval=float(g1), gap_retrieval_ci=ci(dr[:, 1]), closure=float(1 - g1 / g0) if g0 else None, closure_ci=ci(dr[:, 2]))
    if h1["verdict"] != "Supported":
        h2["verdict"] = "Inconclusive (H1 not Supported; no gap to close)"
    else:
        h2["verdict"] = "Supported" if h2["closure_ci"][0] >= 0.5 else "Refuted" if h2["closure_ci"][1] < 0.5 else "Inconclusive"
    out["H2"] = h2
    cf = d[(d.family == "d") & (d.truth == "no") & (d.condition == "zero")]
    for j in ("NZ", "AU"):
        x = cf[cf.jurisdiction == j]; k = int((x.answer == "yes").sum())
        out[f"fabrication_{j}"] = dict(n=int(len(x)), affirmed=k, rate=k / len(x) if len(x) else None, ci=wilson(k, len(x)))
    f = out["fabrication_NZ"]
    out["H3"] = dict(**f, verdict="Supported" if f["ci"][0] >= 0.2 else "Refuted" if f["ci"][1] < 0.2 else "Inconclusive")
    tc = d[(d.family == "d") & (d.truth == "yes")]
    out["true_criterion_accuracy"] = tc.groupby(["condition", "jurisdiction"]).ok.mean().round(3).to_dict()
    abst = d[d.condition == "abstain"]
    out["abstention"] = {j: dict(rate=float((x.answer == "not stated").mean()), acc_answered=float(x[x.answer != "not stated"].ok.mean()))
                         for j, x in abst.groupby("jurisdiction")}
    pz = d[d.condition.isin(["zero", "paraphrase"])].pivot_table(index="id", columns="condition", values="answer", aggfunc="first").dropna()
    out["paraphrase_agreement"] = dict(n=int(len(pz)), agree=float((pz.zero == pz.paraphrase).mean()) if len(pz) else None)
    out["accuracy_by_cell"] = {f"{r.condition}|{r.jurisdiction}|{r.family}": round(r.acc, 3) for r in acc.itertuples()}
    json.dump(out, open(T / "primary.json", "w"), indent=1, default=float)
    print(json.dumps({k: out[k] for k in ("items", "calls", "errors", "H1", "H2", "H3", "fabrication_AU", "abstention", "paraphrase_agreement")}, indent=1, default=float))


if __name__ == "__main__":
    main()
