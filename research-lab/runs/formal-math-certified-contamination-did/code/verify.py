"""Verify sampled proofs in each prover's Lean environment (plan section 4). For every output: take the last ```lean4
block; it must restate the theorem with the same name and the same normalised statement as the version sampled
(otherwise it is rejected as a changed statement); compile it under the standard header; reject errors, sorry, admit,
native_decide and any axiom outside propext / Classical.choice / Quot.sound. Truncated outputs count as failures.
Usage: VAC_TOOLCHAIN=<v49|v415> verify.py <prover> <workers>. Writes data/verified/<prover>.jsonl."""
import json
import multiprocessing as mp
import os
import re
import sys
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN.parent / "formal-math-selfplay-vacuity-drift" / "code"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract import normalise, statement  # noqa: E402
from lean_repl import Repl, axioms, errors, uses_sorry  # noqa: E402

ALLOWED = {"propext", "Classical.choice", "Quot.sound"}
BANNED = re.compile(r"\b(native_decide|admit|sorry)\b|^\s*axiom\s", re.M)
HDR = "open BigOperators Real Nat Topology Rat\n\n"
PI = re.compile(r"(?<![\w.])π(?![\w])")  # D4: bare pi read as Real.pi in statement and proof


def block(text):
    m = re.findall(r"```lean4?\n(.*?)```", text or "", re.S)
    return m[-1] if m else None


def check_one(repl, code, want_norm):
    if code is None:
        return "no code"
    code = PI.sub("Real.pi", code)
    s = statement(code)
    if s is None or normalise(s) != want_norm:
        return "changed statement"
    if BANNED.search(code):
        return "banned"
    body = "\n".join(l for l in code.splitlines() if not re.match(r"\s*import\s", l))
    name = re.search(r"(?:theorem|lemma)\s+(\S+)", s).group(1)
    r = repl.run(f"{HDR}{body}\n\n#print axioms {name}", timeout=150)
    if "timeout" in r or "dead" in r:
        return "timeout"
    if errors(r) or uses_sorry(r):
        return "error"
    ax = axioms(r, name)
    return "ok" if ax is not None and set(ax) <= ALLOWED else "axioms"


_repl = None


def init():
    global _repl
    _repl = Repl()


def work(item):
    key, idx, text, finish, want, stmt = item
    try:
        code = (stmt + " := by" + (text or "")) if PROVER == "stp" else block(text)  # STP writes only the tactic block
        st = "truncated" if finish == "length" else check_one(_repl, code, want)
    except Exception as e:  # noqa: BLE001
        st = "worker error"
        try:
            _repl.restart()
        except Exception:  # noqa: BLE001
            pass
    return dict(key=key, idx=idx, status=st)


PROVER = None


def main(prover, workers):
    global PROVER
    PROVER = prover
    ref = pd.read_parquet(RUN / "data" / "reforms.parquet").set_index("id")
    out = RUN / "data" / "verified" / f"{prover}.jsonl"
    out.parent.mkdir(exist_ok=True)
    done = {(j["key"], j["idx"]) for j in map(json.loads, open(out))} if out.exists() else set()
    items = []
    for line in open(RUN / "data" / "samples" / f"{prover}.jsonl"):
        r = json.loads(line)
        if "outputs" not in r:
            continue
        iid, ver = r["key"].split("|")
        stmt = ref.loc[iid, "orig" if ver == "orig" else ver]
        want = normalise(statement(PI.sub("Real.pi", stmt) + " := by"))
        for i, o in enumerate(r["outputs"]):
            if (r["key"], i) not in done:
                items.append((r["key"], i, o["text"], o["finish"], want, stmt))
    print(f"{prover}: {len(items)} outputs to verify ({os.environ.get('VAC_TOOLCHAIN', 'v49')})", flush=True)
    with mp.Pool(workers, initializer=init) as pool, open(out, "a") as f:
        for k, res in enumerate(pool.imap_unordered(work, items, chunksize=4)):
            f.write(json.dumps(res) + "\n")
            if (k + 1) % 2000 == 0:
                f.flush(); print(k + 1, flush=True)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
