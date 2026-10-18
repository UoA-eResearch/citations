"""Reviewer check 4: retrieval. Rebuilds the BM25 index exactly as code/run.py does and asks, per item: is the item's own
chemical passage in the top 3 (and at what rank)? For counterfactual items: is the SOURCE chemical's passage (which
contains the counterfactual sentence verbatim) in the top 3, and does that predict affirmation? Also examines the 19
AU family-(b) retrieval misses and passage lengths.
Run: venv/bin/python -I review/reviewer_checks/03_retrieval.py"""
import json, re, collections
from pathlib import Path
import pandas as pd
from rank_bm25 import BM25Okapi
RUN = Path(__file__).resolve().parents[2]
Q = {("a", "NZ"): "Is {text} listed for subsidy in the community section of the New Zealand Pharmaceutical Schedule (Pharmac)?",
     ("a", "AU"): "Is {text} listed on the Australian Pharmaceutical Benefits Scheme (PBS) General Schedule?",
     ("b", "NZ"): "Does Pharmac subsidy of {text} in the community require a Special Authority?",
     ("b", "AU"): "Does PBS subsidy of {text} require an authority prescription (Authority Required, including Streamlined Authority)?",
     ("d", "NZ"): "Under Pharmac's Special Authority criteria for {chemical}, is the following one of the criteria: \"{text}\"?",
     ("d", "AU"): "Under the PBS restriction criteria for {chemical}, is the following one of the criteria: \"{text}\"?"}
tok = lambda s: re.findall(r"[a-z0-9]+", s.lower())
items = [json.loads(l) for l in open(RUN / "data/items.jsonl")]
pas = [json.loads(l) for l in open(RUN / "data/passages.jsonl")]
runs = pd.DataFrame([json.loads(l) for l in open(RUN / "data/runs.jsonl")])
ans = {(r.id, r.condition): r.answer for r in runs.itertuples()}
bm = {j: [p for p in pas if p["jurisdiction"] == j] for j in ("NZ", "AU")}
idx = {j: BM25Okapi([tok(p["text"]) for p in docs]) for j, docs in bm.items()}
rows = []
for it in items:
    j = it["jurisdiction"]; q = Q[(it["family"], j)].format(**it)
    top = idx[j].get_top_n(tok(q), bm[j], n=3)
    chems = [p["chemical"] for p in top]
    rows.append(dict(id=it["id"], jur=j, fam=it["family"], truth=it["answer"], chemical=it["chemical"], src=it.get("source_chemical"),
                     own_rank=(chems.index(it["chemical"]) + 1) if it["chemical"] in chems else 0,
                     src_in_top=(it.get("source_chemical") in chems) if it.get("source_chemical") else None,
                     ret=ans.get((it["id"], "retrieval")), abst=ans.get((it["id"], "abstain")), zero=ans.get((it["id"], "zero")),
                     passage_tokens=len(tok(next((p["text"] for p in top if p["chemical"] == it["chemical"]), ""))),
                     ctx_tokens=sum(len(tok(p["text"])) for p in top)))
df = pd.DataFrame(rows)
df.to_csv(RUN / "review/reviewer_checks/retrieval_ranks.csv", index=False)
print("passages per jurisdiction:", {j: len(v) for j, v in bm.items()})
print("passage token lengths: median", int(pd.Series([len(tok(p['text'])) for p in pas]).median()), "max", max(len(tok(p['text'])) for p in pas))
print("\n== own chemical passage in top 3, by jurisdiction x family ==")
print(df.assign(hit=df.own_rank > 0).groupby(["jur", "fam"]).agg(n=("hit", "size"), hit=("hit", "mean"), rank1=("own_rank", lambda r: (r == 1).mean())).round(3).to_string())
miss = df[df.own_rank == 0]
print("\nitems whose own passage was NOT retrieved:", len(miss))
print(miss[["id", "chemical", "truth", "ret", "abst"]].to_string())
print("\nretrieval accuracy when own passage retrieved vs not:")
df["ret_ok"] = df.ret == df.truth
print(df.assign(hit=df.own_rank > 0).groupby(["jur", "fam", "hit"]).ret_ok.agg(["size", "mean"]).round(3).to_string())

print("\n== counterfactual items: source chemical's passage retrieved? ==")
cf = df[(df.fam == "d") & (df.truth == "no")]
for j in ("NZ", "AU"):
    x = cf[cf.jur == j]
    print(f"{j}: source passage in top3 for {int(x.src_in_top.sum())}/{len(x)}; own passage in top3 for {int((x.own_rank>0).sum())}/{len(x)}")
    for s in (True, False):
        y = x[x.src_in_top == s]
        if len(y):
            print(f"   src_in_top={s}: n={len(y)} retrieval 'yes'={int((y.ret=='yes').sum())} ({(y.ret=='yes').mean():.2f}); abstain 'yes'={int((y.abst=='yes').sum())} not_stated={int((y.abst=='not stated').sum())}")
scr = pd.read_csv(RUN / "results/tables/nz_counterfactual_screen.csv").set_index("id").screen
cfn = cf[cf.jur == "NZ"].assign(screen=lambda t: t.id.map(scr))
print("\nNZ CF retrieval 'yes' by screen label x source-in-top:")
print(cfn.groupby(["screen", "src_in_top"]).agg(n=("id", "size"), ret_yes=("ret", lambda r: int((r == "yes").sum())), zero_yes=("zero", lambda r: int((r == "yes").sum()))).to_string())

print("\n== the AU family-(b) retrieval misses ==")
m = df[(df.jur == "AU") & (df.fam == "b") & (~df.ret_ok)]
print(len(m), "misses; truth counts", m.truth.value_counts().to_dict(), "own_rank counts", m.own_rank.value_counts().to_dict())
print("passage_tokens of missed items: median", int(m.passage_tokens.median()), " vs all AU (b):", int(df[(df.jur=='AU')&(df.fam=='b')].passage_tokens.median()))
print("ctx_tokens of missed items: median", int(m.ctx_tokens.median()), " vs all AU (b):", int(df[(df.jur=='AU')&(df.fam=='b')].ctx_tokens.median()))
print(m[["id", "chemical", "truth", "ret", "abst", "own_rank", "passage_tokens", "ctx_tokens"]].to_string())
# what does the passage line say for these?
bychem = {(p["jurisdiction"], p["chemical"]): p["text"] for p in pas}
for r in m.head(4).itertuples():
    txt = bychem[("AU", r.chemical)]
    print(f"\n{r.id} {r.chemical}: passage starts: {txt[:300]}")
    print("   mentions 'varies':", "varies" in txt, " listed lines:", len(re.findall(r"Listed:", txt)))
