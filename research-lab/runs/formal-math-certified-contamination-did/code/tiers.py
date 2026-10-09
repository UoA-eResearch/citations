"""Leak tiers from the certification results (plan section 3, deviations D1-D2) and the minimum detectable effect
(plan section 5), computed before any main prover sampling.
Tier per (benchmark item, corpus statement): L0 identical normalised text; L1 certified both ways, neither conclusion
automation-provable; L2 train => test certified, the test statement not automation-provable. Items whose statement the
portfolio proves on its own are "automation-provable" and can be leaked only through L0. Informativeness follows D3 (recheck.py).
Writes results/tables/leak_pairs.csv, leak_rates.csv, leak_status_by_prover.csv and mde.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
PROVER_CORPORA = {"goedel_v2": ["goedel_pset", "sft_v2", "goedel_lwproofs"], "kimina": ["numina_lean"], "dsp_v2": ["dsp_v1"]}
ALL = ["dsp_v1", "goedel_lwproofs", "goedel_pset", "lean_workbook", "numina_lean", "sft_v2", "stp"]
RANK = {"L0": 0, "L1": 1, "L2": 2}


def tiers(bench):
    rows, trivial = [], set()
    for corp in ALL:
        cand = RUN / "data" / "candidates" / f"{bench}__{corp}.parquet"
        if cand.exists():
            c = pd.read_parquet(cand)
            for x in c[c.via == "L0"].itertuples():
                rows.append(dict(item=x.bench_id, corpus=corp, corpus_id=x.corpus_id, tier="L0"))
        f = RUN / "data" / "certify" / f"{bench}__{corp}.jsonl"
        rc = RUN / "data" / "certify" / f"recheck_{bench}__{corp}.jsonl"
        if not f.exists():
            continue
        inf = {}
        if rc.exists():  # D3: informativeness from the True-substitution recheck (fail-closed)
            for line in open(rc):
                q = json.loads(line)
                inf[q["key"]] = (q.get("ab_inf"), q.get("ba_inf"))
        for line in open(f):
            r = json.loads(line)
            if r.get("status") != "checked":
                continue
            item, _, cid = r["key"].rsplit("|", 2)  # ProofNet# ids contain "|"
            if r.get("b_trivial"):
                trivial.add(item)
            if not rc.exists():
                raise SystemExit(f"recheck missing for {bench} x {corp}")
            ab_inf, ba_inf = inf.get(r["key"], (None, None))
            ab = bool(r.get("ab")) and ab_inf is True  # train => test, informative (D3)
            ba = bool(r.get("ba")) and ba_inf is True  # test => train, informative (D3)
            if ab and ba:
                rows.append(dict(item=item, corpus=corp, corpus_id=cid, tier="L1"))
            elif ab:
                rows.append(dict(item=item, corpus=corp, corpus_id=cid, tier="L2"))
    return pd.DataFrame(rows, columns=["item", "corpus", "corpus_id", "tier"]), trivial


def main(bench="bench_minif2f"):
    items = pd.read_parquet(RUN / "data" / "statements" / f"{bench}.parquet").id.tolist()
    p, trivial = tiers(bench)
    p.drop_duplicates().to_csv(TAB / f"leak_pairs_{bench}.csv", index=False)
    best = p.assign(r=p.tier.map(RANK)).sort_values("r").drop_duplicates(["item", "corpus"])
    rates = []
    for corp in ALL:
        b = best[best.corpus == corp]
        row = dict(bench=bench, corpus=corp, n_items=len(items))
        for t in ("L0", "L1", "L2"):
            row[f"items_{t}"] = int((b.tier == t).sum())
        row["items_any"] = int(b.item.nunique())
        row["share_any"] = row["items_any"] / len(items)
        rates.append(row)
    rates.append(dict(bench=bench, corpus="any corpus", n_items=len(items), items_any=int(best.item.nunique()), share_any=best.item.nunique() / len(items)))
    out = TAB / "leak_rates.csv"
    old = pd.read_csv(out) if out.exists() else pd.DataFrame()
    if len(old):
        old = old[old.bench != bench]
    pd.concat([old, pd.DataFrame(rates)]).to_csv(out, index=False)
    print(pd.DataFrame(rates).to_string())
    print("automation-provable items:", len(trivial))
    if bench != "bench_minif2f":
        return
    st = []
    for prov, corps in PROVER_CORPORA.items():
        for scope, cs in (("own corpora", corps), ("all corpora", ALL)):
            leaked = set(best[best.corpus.isin(cs)].item)
            for it in items:
                st.append(dict(prover=prov, scope=scope, item=it, leaked=it in leaked, automation_provable=it in trivial))
    st = pd.DataFrame(st)
    st.to_csv(TAB / "leak_status_by_prover.csv", index=False)
    own = st[st.scope == "own corpora"]
    n_leak = int(own.leaked.sum())
    n_clean = int((~own.leaked).sum())
    mde = 2.49 * 0.30 * np.sqrt(1 / max(n_leak, 1) + 1 / n_clean)
    res = dict(n_leaked_pairs_own=n_leak, n_clean_pairs_own=n_clean, MDE_pp=100 * mde, per_prover_leaked=own.groupby("prover").leaked.sum().to_dict(),
               n_leaked_pairs_all_corpora=int(st[st.scope == "all corpora"].leaked.sum()), automation_provable_items=len(trivial),
               note="pairs = (item, prover); sampling-level availability (certified reformulations) not yet applied")
    json.dump(res, open(TAB / "mde.json", "w"), indent=1, default=int)
    print(json.dumps(res, indent=1, default=int))


if __name__ == "__main__":
    main(*sys.argv[1:])
