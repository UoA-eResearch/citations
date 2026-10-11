"""Re-verify outputs rejected as 'changed statement' where the only difference from the sampled statement is whitespace
(e.g. the stray space before ')' in R2). Compiles the model's code exactly as verify.py would, skipping the textual match.
Usage: VAC_TOOLCHAIN=v49 reverify_ws.py <prover> <workers> <out.jsonl>"""
import json, os, re, sys
import multiprocessing as mp
from pathlib import Path
import pandas as pd

RUN = Path("/mnt/citations/research-lab/runs/formal-math-certified-contamination-did")
sys.path.insert(0, str(RUN / "code"))
sys.path.insert(0, str(RUN.parent / "formal-math-selfplay-vacuity-drift" / "code"))
from extract import normalise, statement  # noqa
import verify as V  # noqa

prover, workers, out_path = sys.argv[1], int(sys.argv[2]), Path(sys.argv[3])


def loose(x):
    return re.sub(r"\s+", "", x)


def work(item):
    key, idx, code = item
    try:
        code = V.PI.sub("Real.pi", code)
        if V.BANNED.search(code):
            return dict(key=key, idx=idx, status="banned")
        body = "\n".join(l for l in code.splitlines() if not re.match(r"\s*import\s", l))
        s = statement(code)
        name = re.search(r"(?:theorem|lemma)\s+(\S+)", s).group(1)
        r = V._repl.run(f"{V.HDR}{body}\n\n#print axioms {name}", timeout=150)
        if "timeout" in r or "dead" in r:
            return dict(key=key, idx=idx, status="timeout")
        if V.errors(r) or V.uses_sorry(r):
            return dict(key=key, idx=idx, status="error", err=[m["data"][:200] for m in V.errors(r)][:2])
        ax = V.axioms(r, name)
        return dict(key=key, idx=idx, status="ok" if ax is not None and set(ax) <= V.ALLOWED else "axioms")
    except Exception as e:
        try:
            V._repl.restart()
        except Exception:
            pass
        return dict(key=key, idx=idx, status="worker error", err=repr(e)[:200])


def main():
    ref = pd.read_parquet(RUN / "data/reforms.parquet").set_index("id")
    v = pd.DataFrame([json.loads(l) for l in open(RUN / f"data/verified/{prover}.jsonl")])
    s = {r["key"]: r for r in map(json.loads, open(RUN / f"data/samples/{prover}.jsonl"))}
    items = []
    for r in v[v.status == "changed statement"].itertuples():
        iid, ver = r.key.split("|")
        stmt = ref.loc[iid, "orig" if ver == "orig" else ver]
        want = normalise(statement(V.PI.sub("Real.pi", stmt) + " := by"))
        code = V.block(s[r.key]["outputs"][r.idx]["text"])
        st = statement(V.PI.sub("Real.pi", code)) if code else None
        if st and loose(normalise(st)) == loose(want):
            items.append((r.key, r.idx, code))
    print(prover, len(items), "whitespace-only rejections to re-verify", flush=True)
    with mp.Pool(workers, initializer=V.init) as pool, open(out_path, "a") as f:
        for o in pool.imap_unordered(work, items, chunksize=1):
            f.write(json.dumps(o) + "\n"); f.flush()
    print("done", flush=True)


if __name__ == "__main__":
    main()
