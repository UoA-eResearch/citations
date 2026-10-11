"""Final tally of the reviewer's Lean re-checks."""
import json, glob
from pathlib import Path
import pandas as pd

S = Path("/tmp/claude-1001/-mnt-citations/14121cdb-aa2a-421c-926d-b1c71589d0e4/scratchpad")
RUN = Path("/mnt/citations/research-lab/runs/formal-math-certified-contamination-did")

rows = []
for f in ["neg_v49.jsonl", "neg_v415.jsonl"]:
    if (S / f).exists():
        rows += [json.loads(l) for l in open(S / f)]
r = pd.DataFrame(rows)
r["item"] = r.key.str.split("|").str[0]
r["corpus"] = r.key.str.split("|").str[1]
r["spurious"] = (r.a_implies_not_b == True) | (r.train_refutable_witness == True) | (r.b_implies_not_a == True) | (r.test_free_provable == "proved")
print("=== NEGATION / WITNESS TEST on all L1/L2 pairs")
print("rows", len(r), "errors", r.get("error", pd.Series(dtype=object)).notna().sum() if "error" in r else 0, "by tier", r.tier.value_counts().to_dict())
print("ab reproduced:", r.ab.value_counts(dropna=False).to_dict(), "| ba on L1:", r[r.tier == "L1"].ba.value_counts(dropna=False).to_dict())
print("a=>not b:", r.a_implies_not_b.value_counts(dropna=False).to_dict(), "| b=>not a (L1):", r[r.tier == "L1"].b_implies_not_a.value_counts(dropna=False).to_dict())
print("train refutable (study guard):", r.train_refutable_study.value_counts(dropna=False).to_dict(), "| witness:", r.train_refutable_witness.value_counts(dropna=False).to_dict())
print("test FREE-provable:", r.test_free_provable.value_counts(dropna=False).to_dict())
print("spurious pairs:", int(r.spurious.sum()), "of", len(r))
print(r.groupby(["corpus", "tier"]).spurious.agg(["size", "sum"]).to_string())
print(r[r.spurious][["key", "tier", "a_implies_not_b", "train_refutable_witness", "b_implies_not_a", "test_free_provable"]].to_string())
# effect on leak status: items whose own-corpus leak rests only on spurious pairs
pairs = pd.read_csv(RUN / "results/tables/leak_pairs_bench_minif2f.csv")
sp = set(r[r.spurious].key)
pairs["key"] = pairs.item + "|" + pairs.corpus + "|" + pairs.corpus_id
good = pairs[~pairs.key.isin(sp)]
OWN = {"goedel_v2": ["goedel_pset", "sft_v2", "goedel_lwproofs"], "kimina": ["numina_lean"], "dsp_v2": ["dsp_v1"], "stp": ["stp"]}
for p, cs in OWN.items():
    before = set(pairs[pairs.corpus.isin(cs)].item); after = set(good[good.corpus.isin(cs)].item)
    print(f"{p}: leaked items before {len(before)} after removing spurious pairs {len(after)} (lost: {sorted(before - after)})")
print("any corpus: before", pairs.item.nunique(), "after", good.item.nunique())
for c in ["dsp_v1", "goedel_lwproofs", "goedel_pset", "numina_lean", "sft_v2", "stp"]:
    print(f"  {c}: items before {pairs[pairs.corpus == c].item.nunique()} after {good[good.corpus == c].item.nunique()}")

if (S / "free_v49.jsonl").exists():
    f = pd.DataFrame([json.loads(l) for l in open(S / "free_v49.jsonl")])
    print("\n=== FREE on all 488 miniF2F items (Lean 4.9):", f.free.value_counts().to_dict() if "free" in f else f)
    st = pd.read_csv(RUN / "results/tables/leak_status_by_prover.csv")
    d1 = set(st[st.automation_provable].item)
    fp = set(f[f.free == "proved"].key)
    print("   D1-flag items", len(d1), "| FREE-provable", len(fp), "| overlap", len(d1 & fp), "| FREE-provable but not D1-flagged", len(fp - d1), "| D1 but not FREE", len(d1 - fp))
    U = pd.read_csv(RUN / "results/tables/units.csv")
    print("   leaked units whose item is FREE-provable (should be L0 only):", U[U.leaked & U["item"].isin(fp)].groupby("prover").size().to_dict())

for f in ["rejected_v49.jsonl", "rejected_v415.jsonl"]:
    if (S / f).exists():
        q = pd.DataFrame([json.loads(l) for l in open(S / f)])
        print(f"\n=== {f}: {len(q)} rows")
        print(q.groupby("kind").apply(lambda g: pd.Series(dict(n=len(g), ab_now=int((g.ab == True).sum()), ba_now=int((g.ba == True).sum()),
              test_informative=int((g.get("test_informative") == True).sum()) if "test_informative" in g else None,
              train_refutable=int((g.get("train_refutable") == True).sum()) if "train_refutable" in g else None,
              test_free=g.get("test_free").value_counts().to_dict() if "test_free" in g else None))).to_string())

for p in ["goedel", "dsp"]:
    if (S / f"ws_{p}.jsonl").exists():
        w = pd.DataFrame([json.loads(l) for l in open(S / f"ws_{p}.jsonl")])
        print(f"\n=== whitespace re-verification {p}: {w.status.value_counts().to_dict()}")
        if "err" in w:
            print(w[w.status == "error"].err.head(5).tolist())
