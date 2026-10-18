"""Scoring and hypotheses (plan sections 1, 4; deviation D5). Reads data/items.jsonl and data/runs.jsonl. Errors count
as incorrect (and are reported). D5: H1 and H2 verdicts use family (b) alone; the preregistered pooled (a)+(b) analysis
is reported alongside. H3 is tested on all 100 NZ counterfactuals and on the 83 that pass the hand screen
(results/tables/nz_counterfactual_screen.csv); it is Supported or Refuted only if both agree. Writes
results/tables/primary.json and results/tables/accuracy.csv."""
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
    rng = np.random.default_rng(SEED)
    ci = lambda v: [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]

    def gap(x, cond):
        y = x[x.condition == cond]
        return y[y.jurisdiction == "NZ"].ok.mean() - y[y.jurisdiction == "AU"].ok.mean()

    def h12(fams):
        ab = d[d.family.isin(fams)]
        chems = sorted(ab.chemical.unique())
        grp = {c: x for c, x in ab.groupby("chemical")}
        draws = []
        for _ in range(B):
            s_ = pd.concat([grp[c] for c in rng.choice(chems, len(chems))])
            g0_, g1_ = gap(s_, "zero"), gap(s_, "retrieval")
            draws.append((g0_, g1_, 1 - g1_ / g0_ if g0_ != 0 else np.nan))
        dr = np.array(draws)
        g0, g1 = gap(ab, "zero"), gap(ab, "retrieval")
        z = ab[ab.condition == "zero"]
        h1 = dict(families="+".join(fams), chemicals=len(chems), nz_n=int((z.jurisdiction == "NZ").sum()), au_n=int((z.jurisdiction == "AU").sum()),
                  nz_acc=float(z[z.jurisdiction == "NZ"].ok.mean()), au_acc=float(z[z.jurisdiction == "AU"].ok.mean()), gap=float(g0), ci=ci(dr[:, 0]))
        h1["verdict"] = "Supported" if h1["ci"][1] < 0 else "Refuted" if h1["ci"][0] >= 0 else "Inconclusive"
        h2 = dict(gap_retrieval=float(g1), gap_retrieval_ci=ci(dr[:, 1]), closure=float(1 - g1 / g0) if g0 else None, closure_ci=ci(dr[:, 2]))
        if h1["verdict"] != "Supported":
            h2["verdict"] = "Inconclusive (H1 not Supported; no gap to close)"
        else:
            h2["verdict"] = "Supported" if h2["closure_ci"][0] >= 0.5 else "Refuted" if h2["closure_ci"][1] < 0.5 else "Inconclusive"
        return h1, h2
    out["H1"], out["H2"] = h12(["b"])                      # D5: confirmatory
    out["H1_pooled_ab"], out["H2_pooled_ab"] = h12(["a", "b"])   # preregistered form, flagged (family (a) key failed its bar)
    out["H1_agrees_with_pooled"] = out["H1"]["verdict"] == out["H1_pooled_ab"]["verdict"]
    kv = json.load(open(T / "key_validation_round2.json"))
    out["family_a_descriptive"] = dict(key_error_negatives=kv["by_cell"]["a_no"], key_error_positives=kv["by_cell"]["a_yes"],
                                       accuracy={f"{c}|{j}": round(float(x.ok.mean()), 3) for (c, j), x in d[d.family == "a"].groupby(["condition", "jurisdiction"])})
    cf = d[(d.family == "d") & (d.truth == "no") & (d.condition == "zero")]
    for j in ("NZ", "AU"):
        x = cf[cf.jurisdiction == j]; k = int((x.answer == "yes").sum())
        out[f"fabrication_{j}"] = dict(n=int(len(x)), affirmed=k, rate=k / len(x) if len(x) else None, ci=wilson(k, len(x)))
    v3 = lambda f: "Supported" if f["ci"][0] >= 0.2 else "Refuted" if f["ci"][1] < 0.2 else "Inconclusive"
    scr = pd.read_csv(T / "nz_counterfactual_screen.csv")
    keep = set(scr[scr.screen == "distinct"].id)
    x = cf[(cf.jurisdiction == "NZ") & cf.id.isin(keep)]; k = int((x.answer == "yes").sum())
    out["fabrication_NZ_screened"] = dict(n=int(len(x)), affirmed=k, rate=k / len(x) if len(x) else None, ci=wilson(k, len(x)))
    y = cf[(cf.jurisdiction == "NZ") & ~cf.id.isin(keep)]
    out["fabrication_NZ_overlapping"] = dict(n=int(len(y)), affirmed=int((y.answer == "yes").sum()))
    a3, s3 = v3(out["fabrication_NZ"]), v3(out["fabrication_NZ_screened"])
    out["H3"] = dict(all=dict(**out["fabrication_NZ"], verdict=a3), screened=dict(**out["fabrication_NZ_screened"], verdict=s3),
                     verdict=a3 if a3 == s3 else "Inconclusive")
    tc = d[(d.family == "d") & (d.truth == "yes")]
    out["true_criterion_accuracy"] = {f"{c}|{j}": round(float(x.ok.mean()), 3) for (c, j), x in tc.groupby(["condition", "jurisdiction"])}
    abst = d[d.condition == "abstain"]
    out["abstention"] = {j: dict(rate=float((x.answer == "not stated").mean()), acc_answered=float(x[x.answer != "not stated"].ok.mean()))
                         for j, x in abst.groupby("jurisdiction")}
    pz = d[d.condition.isin(["zero", "paraphrase"])].pivot_table(index="id", columns="condition", values="answer", aggfunc="first").dropna()
    out["paraphrase_agreement"] = dict(n=int(len(pz)), agree=float((pz.zero == pz.paraphrase).mean()) if len(pz) else None)
    out["accuracy_by_cell"] = {f"{r.condition}|{r.jurisdiction}|{r.family}": round(r.acc, 3) for r in acc.itertuples()}
    json.dump(out, open(T / "primary.json", "w"), indent=1, default=float)
    print(json.dumps({k: out[k] for k in ("items", "calls", "errors", "H1", "H2", "H1_pooled_ab", "H2_pooled_ab", "H3", "fabrication_AU", "abstention", "paraphrase_agreement")}, indent=1, default=float))


if __name__ == "__main__":
    main()
