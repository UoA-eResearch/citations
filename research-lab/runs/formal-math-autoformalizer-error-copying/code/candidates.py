"""Plan section 2.1-2.2: candidate items and their Lean filters.

  candidates.py build           -> results/catalogue/candidates.jsonl (no Lean)
  VAC_TOOLCHAIN=v49 candidates.py lean v49 22   -> results/catalogue/lean_v49.jsonl
  VAC_TOOLCHAIN=v415 candidates.py lean v415 22 -> results/catalogue/lean_v415.jsonl (only items not settled in v49)
  candidates.py merge           -> results/catalogue/filtered.jsonl (environment, equivalence, attrition)

Each Lean record: elaboration of D and C, and, if both elaborate, D → C and C → D by the portfolio."""
import difflib
import json
import multiprocessing as mp
import os
import re
import sys
import time
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
CAT = RUN / "results" / "catalogue"
sys.path.insert(0, str(Path(__file__).resolve().parent))


def nl_of(prefix):
    return re.sub(r"^\s*/--\s*|\s*-/\s*$", "", prefix.strip()).strip()


def norm(stmt):
    from lean_check import ParseError, parse
    try:
        _, b, c = parse(stmt)
        s = f"{b} : {c}"
    except ParseError:
        s = stmt
    s = re.sub(r"([∑∏]\s*[^,]*?)\s+in\s+", r"\1 ∈ ", s)
    return re.sub(r"\s+", " ", s).strip()


def build():
    CAT.mkdir(parents=True, exist_ok=True)
    rows = []
    v1 = {d["name"]: d for d in map(json.loads, open(RAW / "dsp15/datasets/minif2f.jsonl"))}
    v2 = {d["name"]: d for d in map(json.loads, open(RAW / "miniF2F_v2/datasets/miniF2F_v2s.jsonl"))}
    for n, a in v1.items():
        b = v2[n]
        rows.append(dict(item=f"minif2f/{n}", source="minif2f", name=n, split=a["split"], nl=nl_of(a["informal_prefix"]),
                         nl_v2=b["informal statement"].strip(), D=a["formal_statement"], D_header=a["header"],
                         C=b["formal_statement"], C_header=b["header"], role="primary"))
    # negative control: audit items whose defect the v2 edit introduced (D = v2s, C = v1)
    for f in map(json.loads, open(RAW / "minif2f-v2-audit/findings.jsonl")):
        if f["v2_miscorrection"] and "miniF2F_v2s" in f["source"]:
            a, b = v2[f["id"]], v1[f["id"]]
            rows.append(dict(item=f"control/{f['id']}", source="minif2f", name=f["id"], split=b["split"],
                             nl=nl_of(b["informal_prefix"]), nl_v2=a["informal statement"].strip(), D=a["formal_statement"],
                             D_header=a["header"], C=b["formal_statement"], C_header=b["header"], role="control"))
    pn = [json.loads(l) for l in open(RAW / "dsp15/datasets/proofnet.jsonl")]
    ps = pd.concat([pd.read_parquet(RAW / f"proofnet_sharp/{s}.parquet").assign(split=s) for s in ("valid", "test")])
    ps["name"] = ps.id.str.split("|").str[1]
    used = set()
    for a in pn:
        nl = nl_of(a["informal_prefix"])
        cands = ps[(ps.split == a["split"]) & (ps.name == a["name"]) & ~ps.id.isin(used)]
        if not len(cands):
            continue
        ratio = [difflib.SequenceMatcher(None, nl, x).ratio() for x in cands.nl_statement]
        k = max(range(len(cands)), key=lambda i: ratio[i])
        if ratio[k] < 0.8:
            continue
        b = cands.iloc[k]
        used.add(b.id)
        rows.append(dict(item=f"proofnet/{b.id}", source="proofnet", name=a["name"], split=a["split"], nl=nl,
                         nl_v2=b.nl_statement.strip(), D=a["formal_statement"], D_header=a["header"],
                         C=b.lean4_formalization, C_header=b.lean4_src_header, role="primary", nl_ratio=round(ratio[k], 4)))
    df = pd.DataFrame(rows)
    df["changed"] = [norm(d) != norm(c) for d, c in zip(df.D, df.C)]
    df["nl_changed"] = [re.sub(r"\s+", " ", a) != re.sub(r"\s+", " ", b) for a, b in zip(df.nl, df.nl_v2)]
    df.to_json(CAT / "all_pairs.jsonl", orient="records", lines=True, force_ascii=False)
    cand = df[df.changed | (df.role == "control")]
    cand.to_json(CAT / "candidates.jsonl", orient="records", lines=True, force_ascii=False)
    print(df.groupby(["source", "role"]).agg(n=("item", "size"), changed=("changed", "sum"), nl_changed=("nl_changed", "sum")))
    print("ProofNet pairs matched:", (df.source == "proofnet").sum(), "of", len(pn))


_repl = None


def init():
    global _repl
    from lean_check import Repl
    _repl = Repl()


def work(row):
    import lean_check as L
    t0 = time.time()
    oD, oC = L.opens_of(row["D_header"]), L.opens_of(row["C_header"])
    out = dict(item=row["item"])
    try:
        out["D_elab"] = L.elaborates(_repl, row["D"], oD)
        out["C_elab"] = L.elaborates(_repl, row["C"], oC)
        if out["D_elab"] and out["C_elab"]:
            out["DC"] = L.implies(_repl, row["D"], row["C"], oD, oC)
            out["CD"] = L.implies(_repl, row["C"], row["D"], oC, oD)
    except Exception as e:  # noqa: BLE001
        out["error"] = repr(e)[:300]
        try:
            _repl.restart()
        except Exception:  # noqa: BLE001
            pass
    out["s"] = round(time.time() - t0, 1)
    return out


def lean(tc, workers):
    assert os.environ.get("VAC_TOOLCHAIN", "v49") == tc
    cand = pd.read_json(CAT / "candidates.jsonl", lines=True)
    if tc == "v415":  # only items not settled in v49 (D or C failed to elaborate)
        v49 = pd.read_json(CAT / "lean_v49.jsonl", lines=True)
        ok = set(v49[v49.D_elab & v49.C_elab].item)
        cand = cand[~cand.item.isin(ok)]
    path = CAT / f"lean_{tc}.jsonl"
    done = {json.loads(l)["item"] for l in open(path)} if path.exists() else set()
    todo = [r for r in cand.to_dict("records") if r["item"] not in done]
    print(f"{len(cand)} candidates, {len(todo)} to run in {tc}", flush=True)
    with mp.Pool(workers, initializer=init) as pool, open(path, "a") as f:
        for i, o in enumerate(pool.imap_unordered(work, todo, chunksize=1)):
            f.write(json.dumps(o) + "\n")
            f.flush()
            if (i + 1) % 50 == 0:
                print(i + 1, time.strftime("%H:%M:%S"), flush=True)
    print(f"LEAN {tc} DONE", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "build":
        build()
    elif cmd == "lean":
        lean(sys.argv[2], int(sys.argv[3]))
