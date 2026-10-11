"""D9: re-check outputs rejected as "changed statement" with a comparison that ignores spaces next to brackets, colons
and commas (e.g. "v₁ )" vs "v₁)"). Outputs whose statement then matches are compiled as in verify.py. Writes
data/verified/<prover>_ws.jsonl with the new status for each re-checked (key, idx); analysis.py applies these overrides."""
import json
import multiprocessing as mp
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify as V  # noqa: E402
from extract import normalise, statement  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
SP = re.compile(r"\s*([()\[\]{}:,⦃⦄])\s*")


def loose(s):
    return SP.sub(r"\1", s)


def work(item):
    key, idx, code, want = item
    try:
        code = V.PI.sub("Real.pi", code)
        s = statement(code)
        if s is None or loose(normalise(s)) != loose(want):
            return dict(key=key, idx=idx, status="changed statement")
        # same statement up to spacing: compile exactly as verify.check_one does, minus the strict comparison
        if V.BANNED.search(code):
            return dict(key=key, idx=idx, status="banned")
        body = "\n".join(l for l in code.splitlines() if not re.match(r"\s*import\s", l))
        name = re.search(r"(?:theorem|lemma)\s+(\S+)", s).group(1)
        r = V._repl.run(f"{V.HDR}{body}\n\n#print axioms {name}", timeout=150)
        if "timeout" in r or "dead" in r:
            return dict(key=key, idx=idx, status="timeout")
        if V.errors(r) or V.uses_sorry(r):
            return dict(key=key, idx=idx, status="error")
        ax = V.axioms(r, name)
        return dict(key=key, idx=idx, status="ok" if ax is not None and set(ax) <= V.ALLOWED else "axioms")
    except Exception as e:  # noqa: BLE001
        return dict(key=key, idx=idx, status="worker error", error=repr(e)[:100])


def main(prover, workers):
    ref = pd.read_parquet(RUN / "data" / "reforms.parquet").set_index("id")
    changed = {(j["key"], j["idx"]) for j in map(json.loads, open(RUN / "data" / "verified" / f"{prover}.jsonl")) if j["status"] == "changed statement"}
    items = []
    for line in open(RUN / "data" / "samples" / f"{prover}.jsonl"):
        r = json.loads(line)
        iid, ver = r["key"].split("|")
        stmt = ref.loc[iid, "orig" if ver == "orig" else ver]
        want = normalise(statement(V.PI.sub("Real.pi", stmt) + " := by"))
        for i, o in enumerate(r.get("outputs", [])):
            if (r["key"], i) in changed:
                code = V.block(o["text"]) if prover != "stp" else (stmt + " := by" + (o["text"] or ""))
                if code:
                    items.append((r["key"], i, code, want))
    with mp.Pool(int(workers), initializer=V.init) as pool:
        res = pool.map(work, items, chunksize=1)
    with open(RUN / "data" / "verified" / f"{prover}_ws.jsonl", "w") as f:
        for x in res:
            f.write(json.dumps(x) + "\n")
    print(prover, len(items), "re-checked:", pd.Series([x["status"] for x in res]).value_counts().to_dict())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
