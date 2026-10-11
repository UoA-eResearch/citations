"""D9 diagnostics for the report (no Lean): retrieval recall on the study's own certified reformulations, the unchecked
share of candidate pairs, the composition of L2 pairs, leaked items by best tier, and clean-arm solve rates by split.
Writes results/tables/diagnostics.json."""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import certify as C  # noqa: E402
from extract import features, normalise, statement  # noqa: E402
from retrieve import signature  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
ALL = ["dsp_v1", "goedel_lwproofs", "goedel_pset", "lean_workbook", "numina_lean", "sft_v2", "stp"]


def retrieved(a, b):
    """The retrieval rule of retrieve.py applied to one pair of normalised statements (before the top-10 cut)."""
    jac = float(np.mean(signature(a) == signature(b)))
    na, ia = features(a)
    nb, ib = features(b)
    ia, ib = set(ia.split()), set(ib.split())
    num = bool(na) and na == nb and bool(ia) and len(ia & ib) >= 0.5 * len(ia)
    return jac, jac >= 0.3 or num


def recall():
    ref = pd.read_parquet(RUN / "data" / "reforms.parquet").set_index("id")
    ok = set()
    for line in open(RUN / "data" / "certify" / "reforms_v49.jsonl"):
        r = json.loads(line)
        if r.get("status") == "checked" and r.get("ab") and r.get("ba"):
            ok.add(r["key"])
    n = lambda s: normalise(statement(s + " := by"))  # noqa: E731
    out = {}
    for ver in ("R1", "R2"):
        rows = []
        for iid, x in ref.iterrows():
            if f"{iid}|{ver}" not in ok or not isinstance(x[ver], str):
                continue
            o, v = n(x.orig), n(x[ver])
            if o == v:
                continue  # identical R1 (D9)
            jac, hit = retrieved(o, v)
            rows.append((jac, hit))
        a = np.array(rows, dtype=float)
        out[ver] = dict(n=len(a), recall=float(a[:, 1].mean()), median_jaccard=float(np.median(a[:, 0])))
    return out


def unchecked():
    out = {}
    for corp in ALL:
        f = RUN / "data" / "certify" / f"bench_minif2f__{corp}.jsonl"
        s = pd.Series([json.loads(l).get("status") for l in open(f)]) if f.exists() else pd.Series(dtype=str)
        out[corp] = dict(pairs=int(len(s)), unchecked=int((s == "unchecked").sum()))
    tot = sum(v["pairs"] for v in out.values())
    unc = sum(v["unchecked"] for v in out.values())
    return dict(by_corpus=out, pairs=tot, unchecked=unc, share=unc / tot if tot else None)


def squash(s):
    return re.sub(r"\s+", "", s)


def l2_types():
    p = pd.read_csv(TAB / "leak_pairs_bench_minif2f.csv")
    p = p[p.tier == "L2"]
    bench = pd.read_parquet(RUN / "data" / "statements" / "bench_minif2f.parquet").drop_duplicates("id").set_index("id").stmt
    corp = {}
    kinds = []
    for r in p.itertuples():
        if r.corpus not in corp:
            corp[r.corpus] = pd.read_parquet(RUN / "data" / "statements" / f"{r.corpus}.parquet", columns=["id", "stmt"]).drop_duplicates("id").set_index("id").stmt
        try:
            _, ca = C.split(corp[r.corpus][r.corpus_id])
            _, cb = C.split(bench[r.item])
        except Exception:  # noqa: BLE001
            kinds.append("unparsed")
            continue
        ca, cb = squash(ca), squash(cb)
        if ca == cb:
            kinds.append("same conclusion, fewer or weaker hypotheses")
        elif cb in ca and "∧" in ca:
            kinds.append("benchmark conclusion with extra conjuncts")
        elif cb in ca and "↔" in ca:
            kinds.append("iff form")
        else:
            kinds.append("other (more general, or textually different)")
    return dict(n=len(p), by_type=pd.Series(kinds).value_counts().to_dict())


def best_tier():
    p = pd.read_csv(TAB / "leak_pairs_bench_minif2f.csv")
    rank = {"L0": 0, "L1": 1, "L2": 2}
    b = p.assign(r=p.tier.map(rank)).groupby("item").r.min().map({v: k for k, v in rank.items()})
    return b.value_counts().to_dict()


def split_rates():
    u = pd.read_csv(TAB / "units.csv")
    u["split"] = np.where(u["item"].str.startswith("valid/"), "valid", "test")
    g = u.groupby(["prover", "leaked", "split"]).agg(n=("item", "size"), pass32=("pass32", "mean"), rate=("rate", "mean")).reset_index()
    return g.to_dict(orient="records")


def main():
    out = dict(retrieval_recall_on_reformulations=recall(), unchecked_minif2f=unchecked(), l2_composition=l2_types(),
               leaked_items_by_best_tier=best_tier(), solve_rates_by_split=split_rates())
    json.dump(out, open(TAB / "diagnostics.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "solve_rates_by_split"}, indent=1))


if __name__ == "__main__":
    main()
