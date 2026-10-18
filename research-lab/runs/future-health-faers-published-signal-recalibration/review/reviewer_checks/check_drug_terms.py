"""Reviewer check 3: the drug-matching terms (ingredient + RxNorm brands + the paper's drug string) actually used for the
406 signals and the 332 controls, from the RxNav cache; temp-table name collisions from the 40-char truncation in
recompute.py; suspicious terms (short, generic words)."""
import json, re, sys
from pathlib import Path
import pandas as pd
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
import rxnorm  # uses the cache; no network needed if cached
from recompute import terms_for, pattern
OUT = Path(__file__).resolve().parent
e = pd.read_csv(RUN / "data" / "signals_eligible.csv", dtype={"paper": str})
nc = pd.read_csv(RUN / "data" / "negative_controls.csv")
cache_keys_before = len(rxnorm.CACHE)
rows = []
for r in e.itertuples():
    terms = terms_for(r.ingredient, r.drug)
    key = r.ingredient + "|" + rxnorm.clean(r.drug).lower()
    name = "d_" + re.sub(r"[^a-z0-9]", "_", key.lower())[:40]
    rows.append(dict(kind="signal", paper=r.paper, k=r.k, drug=r.drug, ingredient=r.ingredient, key=key, table=name, n_terms=len(terms), terms="|".join(terms)))
for r in nc.itertuples():
    terms = terms_for(r.drug, r.drug)
    name = "d_" + re.sub(r"[^a-z0-9]", "_", ("nc_" + r.drug).lower())[:40]
    rows.append(dict(kind="nc", paper="", k=-1, drug=r.drug, ingredient=r.drug, key="nc_" + r.drug, table=name, n_terms=len(terms), terms="|".join(terms)))
assert len(rxnorm.CACHE) == cache_keys_before, "network calls were needed; cache incomplete"
t = pd.DataFrame(rows)
t.to_csv(OUT / "drug_terms_used.csv", index=False)
# collisions: same table name, different term sets
g = t.groupby("table").agg(n_keys=("key", "nunique"), n_termsets=("terms", "nunique"), keys=("key", lambda x: " || ".join(sorted(set(x)))))
col = g[g.n_termsets > 1]
print("temp-table names:", t.table.nunique(), "| names shared by different term sets:", len(col))
if len(col): print(col.to_string())
# suspicious terms: short (<6 chars) or common English words
common = {"ADVANCE", "ALLERGY", "RELIEF", "CLEAR", "COMPLETE", "DAILY", "PLUS", "EXTRA", "FORTE", "JUNIOR", "CHILDREN", "NIGHT", "COLD", "FLU", "SINUS",
          "PAIN", "SLEEP", "COUGH", "FEVER", "ORAL", "CREAM", "GEL", "ULTRA", "MAX", "ONE", "TIME", "CARE", "LIFE", "FREE", "GOLD", "BASIC", "ACNE"}
sus = []
for r in t.itertuples():
    for term in r.terms.split("|"):
        if len(term) <= 5 or term in common or " " in term and any(w in common for w in term.split()):
            sus.append((r.kind, r.drug, r.ingredient, term))
sus = pd.DataFrame(sus, columns=["kind", "drug", "ingredient", "term"]).drop_duplicates()
print("\nshort or generic-word terms (<=5 chars or common word):", len(sus))
print(sus.to_string(index=False))
print("\nterm counts per signal ingredient: median", t[t.kind == "signal"].n_terms.median(), "max", t[t.kind == "signal"].n_terms.max())
print(t[t.kind == "signal"].sort_values("n_terms", ascending=False).head(8)[["ingredient", "n_terms"]].to_string(index=False))
# ingredients whose paper drug string differs from the ingredient (the raw string is added as a term)
d = t[(t.kind == "signal")].copy(); d["clean"] = d.drug.map(lambda x: rxnorm.clean(x).lower())
dd = d[d.clean != d.ingredient][["drug", "ingredient", "clean"]].drop_duplicates()
print("\npaper drug strings that differ from the RxNorm ingredient (each is also used as a match term):", len(dd))
print(dd.to_string(index=False))
