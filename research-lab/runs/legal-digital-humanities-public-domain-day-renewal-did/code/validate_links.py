"""Linkage validation (plan section 1): 300 registrations, stratified by renewal status, labelled blind.

  validate_links.py sample   data/validation/sample.jsonl (what the labeller sees) + key.json (the matcher's choices)
  validate_links.py score    data/validation/labels.json -> results/tables/linkage_validation.json

The sample is drawn from all 1923-1930 registrations, linked or not (150 renewed, 150 not; seed 20261023). Each item
shows the registration (title, author, registration year) and up to 8 candidate Open Library works (every work that
passed the title rule for this registration, best title similarity first), shuffled and lettered, with their titles,
first publish years and author names. The labeller is not told which candidate, if any, the matcher chose.
Labels list every candidate that is the same work (Open Library often holds duplicate work records).
Precision: among sampled registrations the matcher linked, the share whose link is one of the labelled true matches.
Recall (conditional on the candidate set): among sampled registrations with a labelled true match, the share linked
to it.
"""
import json
import string
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
DATA = RUN / "data"
V = DATA / "validation"
T = RUN / "results" / "tables"
SEED = 20261023


def sample():
    V.mkdir(parents=True, exist_ok=True)
    r = pd.read_parquet(DATA / "registrations.parquet")
    r = r[r.reg_year.between(1923, 1930)]
    links = pd.read_parquet(DATA / "links.parquet").set_index("entry_id")
    rng = np.random.default_rng(SEED)
    pick = pd.concat([g.iloc[rng.choice(len(g), 150, replace=False)] for _, g in r.groupby("renewed")])
    cand = pd.read_parquet(DATA / "candidates.parquet")
    cand = cand[cand.entry_id.isin(set(pick.entry_id))]
    names = pd.read_parquet(DATA / "author_names.parquet").set_index("author_key").name
    items, key = [], {}
    for i, row in enumerate(pick.sample(frac=1, random_state=SEED).itertuples()):
        c = cand[cand.entry_id == row.entry_id].sort_values("title_sim", ascending=False).drop_duplicates("work").head(8)
        c = c.sample(frac=1, random_state=SEED + i)
        opts = {}
        for letter, w in zip(string.ascii_uppercase, c.itertuples()):
            auth = [names.get(a, "") for a in str(w.author_keys).split(";") if a]
            opts[letter] = {"title": w.work_title, "first_publish_year": None if pd.isna(w.first_year) else int(w.first_year),
                            "authors": [a for a in auth if a][:4]}
        item = f"R{i + 1:03d}"
        items.append({"item": item, "registration": {"title": row.title, "author": row.author, "registration_year": int(row.reg_year)},
                      "candidates": opts})
        lw = links.work.get(row.entry_id) if row.entry_id in links.index else None
        key[item] = {"entry_id": row.entry_id, "renewed": bool(row.renewed),
                     "linked_letter": next((l for l, w in zip(string.ascii_uppercase, c.work) if w == lw), None) if lw else None,
                     "linked": lw is not None}
    with open(V / "sample.jsonl", "w") as fh:
        for it in items:
            fh.write(json.dumps(it, ensure_ascii=False) + "\n")
    (V / "key.json").write_text(json.dumps(key, indent=1))
    print(len(items), "items;", sum(k["linked"] for k in key.values()), "linked;",
          sum(1 for it in items if not it["candidates"]), "with no candidates")


def score():
    key = json.loads((V / "key.json").read_text())
    lab = json.loads((V / "labels.json").read_text())
    rows = []
    for item, k in key.items():
        L = lab[item]["match"]                   # list of letters (every candidate that is the same work), [] or "unsure"
        unsure = L == "unsure"
        letters = [] if unsure else list(L)
        rows.append({**k, "label": "unsure" if unsure else ",".join(letters) or "none",
                     "correct_link": bool(k["linked"] and k["linked_letter"] in letters), "has_true": bool(letters)})
    d = pd.DataFrame(rows)

    def stats(x):
        linked = x[x.linked & (x.label != "unsure")]
        true = x[x.has_true]
        return {"n": int(len(x)), "linked": int(x.linked.sum()), "unsure": int((x.label == "unsure").sum()),
                "precision": round(float(linked.correct_link.mean()), 4) if len(linked) else None, "precision_n": int(len(linked)),
                "recall": round(float(true.correct_link.mean()), 4) if len(true) else None, "recall_n": int(len(true))}

    out = {"all": stats(d), "renewed": stats(d[d.renewed]), "not_renewed": stats(d[~d.renewed])}
    (T / "linkage_validation.json").write_text(json.dumps(out, indent=1))
    d.drop(columns=["entry_id"]).to_csv(T / "linkage_validation.csv", index=False)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    {"sample": sample, "score": score}[sys.argv[1]]()
