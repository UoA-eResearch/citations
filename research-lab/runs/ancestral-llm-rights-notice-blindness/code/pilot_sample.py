"""Draw the pilot adjudication sample and, once adjudicated, compare it with the scorer (plan section 5).

  sample   200 pilot responses, stratified over the nine non-NONE conditions (22-23 each) and spread over models and
           framings, seeded; written WITHOUT the scorer's verdict and in shuffled order, so the adjudicator judges
           blind to the regex result. The adjudicator records, per id, whether the response mentions the inserted
           element (by name or by what it asks), in results/tables/pilot_adjudication.csv (id,mention,note).
  compare  sensitivity and specificity of each pattern against the adjudication; written to pilot_validation.json.

Usage: venv/bin/python code/pilot_sample.py sample | compare
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
import build_corpus as B  # noqa: E402
import score as S  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "data" / "pilot_adjudication"
TAB = RUN / "results" / "tables"


def sample():
    d = A.load("pilot")
    d = d[d.ok & (d.condition != "NONE")].reset_index(drop=True)
    rng = np.random.default_rng(20261017)
    picks = []
    for c, g in d.groupby("condition"):
        picks += list(rng.choice(g.index, size=min(len(g), 23 if len(picks) < 23 * 2 else 22), replace=False))
    s = d.loc[picks].sample(frac=1, random_state=7).reset_index(drop=True)
    s["id"] = [f"p{i:03d}" for i in range(len(s))]
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "sample.jsonl", "w") as fh:
        for r in s.itertuples():
            el = B.CONDITIONS[r.condition]
            fh.write(json.dumps(dict(id=r.id, condition=r.condition, element=el["rights"], model=r.model, framing=r.framing,
                                     text=S.strip_echo(r.text)), ensure_ascii=False) + "\n")
    s[["id", "doi", "condition", "model", "framing"]].to_csv(OUT / "sample_key.csv", index=False)
    print(len(s), "sampled;", s.condition.value_counts().to_dict())


def compare():
    s = pd.read_json(OUT / "sample.jsonl", lines=True)
    adj = pd.read_csv(TAB / "pilot_adjudication.csv")
    m = s.merge(adj, on="id")
    m["auto"] = [S.mentions(t, c) for t, c in zip(m.text, m.condition)]
    out = {}
    for c, g in list(m.groupby("condition")) + [("ALL", m)]:
        tp = int(((g.auto == 1) & (g.mention == 1)).sum()); fn = int(((g.auto == 0) & (g.mention == 1)).sum())
        fp = int(((g.auto == 1) & (g.mention == 0)).sum()); tn = int(((g.auto == 0) & (g.mention == 0)).sum())
        out[c] = dict(n=int(len(g)), tp=tp, fn=fn, fp=fp, tn=tn,
                      sensitivity=tp / (tp + fn) if tp + fn else None, specificity=tn / (tn + fp) if tn + fp else None,
                      agreement=(tp + tn) / len(g))
    json.dump(out, open(TAB / "pilot_validation.json", "w"), indent=1)
    print(json.dumps(out, indent=1))
    print("\ndisagreements:")
    for r in m[m.auto != m.mention].itertuples():
        print(r.id, r.condition, "auto", int(r.auto), "adj", int(r.mention), "|", str(r.note)[:80])


if __name__ == "__main__":
    {"sample": sample, "compare": compare}[sys.argv[1]]()
