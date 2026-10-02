#!/usr/bin/env python
"""Checks added after independent review (deviations.md D6).

(1) Sensitivity of the mass-crossing step: a "sustained" crossing = the first checkpoint after which mean five-shot
    letter mass stays above 0.5 at every later checkpoint (the preregistered rule needs only two in a row).
(2) Crossover rule anatomy: how many defined crossovers are in runs that never leave chance, and how many are at a
    run's first checkpoint.
(3) Per-unit final MCF accuracy above chance in units that never depart.
(4) OLMo-1B-0724 diagnostic (needs MODEL_DIR of its final checkpoint): the top-5 next tokens after "Answer:" on 10
    five-shot items per task, to see where its probability goes instead of the answer letters.
Usage: review_checks.py [MODEL_DIR]
Output: results/tables/review_sustained_mass.csv, review_crossover.csv, review_olmo1b_top5.csv (if MODEL_DIR)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"


def sustained(tokens, mass):
    for i in range(len(mass)):
        if (mass[i:] > 0.5).all():
            return tokens[i]
    return np.nan


def main():
    w = pd.read_csv(TAB / "checkpoint_metrics.csv").sort_values(["run", "task", "tokens"])
    u = pd.read_csv(TAB / "units.csv")
    rows = []
    for (run, task), g in w.groupby(["run", "task"]):
        rows.append(dict(run=run, task=task, sustained_mass=sustained(g.tokens.values, g.mass_mcf5.values)))
    s = u.merge(pd.DataFrame(rows), on=["run", "task"])
    d = s[s.departure_mcf5.notna()].copy()
    d["lead_prereg"] = d.departure_mcf5 / d.masscross_mcf5
    d["lead_sustained"] = d.departure_mcf5 / d.sustained_mass
    out = d[["run", "task", "masscross_mcf5", "sustained_mass", "departure_mcf5", "lead_prereg", "lead_sustained"]]
    out.to_csv(TAB / "review_sustained_mass.csv", index=False)
    print((out.assign(masscross_mcf5=out.masscross_mcf5 / 1e9, sustained_mass=out.sustained_mass / 1e9,
                      departure_mcf5=out.departure_mcf5 / 1e9)).round(2).to_string(index=False))
    print("violations under the sustained rule:", int((d.sustained_mass.isna() | (d.sustained_mass > d.departure_mcf5)).sum()))
    # (2)
    first = w.groupby(["run", "task"]).tokens.min().rename("first_tokens_ck")
    c = u.merge(first, on=["run", "task"])
    defined = c[c.crossover.notna()]
    dep_runs = set(u[u.departure_mcf5.notna()].run)
    cr = dict(defined=len(defined), in_never_departing_runs=int((~defined.run.isin(dep_runs)).sum()),
              at_first_checkpoint=int((defined.crossover == defined.first_tokens_ck).sum()),
              in_departing_runs=int(defined.run.isin(dep_runs).sum()),
              genuine=int((defined.run.isin(dep_runs) & (defined.crossover > defined.first_tokens_ck)).sum()))
    pd.DataFrame([cr]).to_csv(TAB / "review_crossover.csv", index=False)
    print("crossover anatomy:", cr)
    # (3)
    nd = u[u.departure_mcf5.isna()]
    ex = (nd.final_acc_mcf5 - nd.final_chance) * 100
    print("per-unit final MCF excess in never-departing units: %.1f to %.1f points" % (ex.min(), ex.max()))
    # (4)
    if len(sys.argv) > 1:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        md = sys.argv[1]
        tok = AutoTokenizer.from_pretrained(md)
        model = AutoModelForCausalLM.from_pretrained(md, dtype=torch.bfloat16).to("cuda").eval()
        rows = []
        for t in ("arc_easy", "arc_challenge", "csqa", "piqa", "hellaswag", "mmlu"):
            items = [json.loads(l) for l in open(RUN / "data" / "items" / f"{t}.jsonl")][:10]
            for it in items:
                ids = tok(it["mcf5"], return_tensors="pt").input_ids.to("cuda")
                with torch.no_grad():
                    p = model(ids).logits[0, -1].float().softmax(-1)
                top = torch.topk(p, 5)
                rows.append(dict(task=t, id=it["id"], top5=" | ".join(f"{tok.decode([i])!r}:{v:.2f}" for v, i in
                                                                       zip(top.values.tolist(), top.indices.tolist()))))
        tb = pd.DataFrame(rows)
        tb.to_csv(TAB / "review_olmo1b_top5.csv", index=False)
        for t, g in tb.groupby("task"):
            print(t, "|", g.top5.iloc[0], "||", g.top5.iloc[1])


if __name__ == "__main__":
    main()
