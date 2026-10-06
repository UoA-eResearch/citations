"""Lean certification (plan sections 3-4). For a pair of statements a, b proves (forall B_a, C_a) -> (forall B_b, C_b) with
a bounded tactic portfolio (20 s), with autoImplicit off (an undeclared variable would otherwise be shared between the
two sides) and bare pi read as Real.pi. Used for leak tiers (train => test and test => train) and for certifying the
reformulations R1/R2 against the original. Run: certify.py leaks <bench> <workers> | certify.py reforms <workers>.
Environments: Lean 4.9 (all corpora but NuminaMath-LEAN) and Lean 4.15 (NuminaMath-LEAN), via VAC_TOOLCHAIN."""
import json
import multiprocessing as mp
import os
import re
import sys
import time
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
VAC = RUN.parent / "formal-math-selfplay-vacuity-drift" / "code"
sys.path.insert(0, str(VAC))
from lean_repl import Repl, axioms, errors, uses_sorry  # noqa: E402
from vacuity import parse  # noqa: E402

HDR = "open BigOperators Real Nat Topology Rat\nset_option autoImplicit false\n\n"
ALLOWED = {"propext", "Classical.choice", "Quot.sound"}
PORTFOLIO = ("first\n    | (apply h <;> (first | assumption | norm_num | linarith | simp_all))\n    | (simp_all; done)\n    | aesop\n"
             "    | (simp_all <;> nlinarith [h])")
PI = re.compile(r"(?<![\w.])π(?![\w])")
LEAN415 = {"numina_lean"}


def split(stmt):
    p = parse("```lean4\n" + PI.sub("Real.pi", stmt) + " := by")
    return p["binders"], p["concl"]


def prop(stmt):
    b, c = split(stmt)
    return f"(∀ {b}, {c})" if b else f"({c})"


def check(repl, a, b, timeout=20):
    """True if (forall a) -> (forall b) is kernel-checked with allowed axioms; None if either side does not elaborate."""
    try:
        pa, pb = prop(a), prop(b)
    except Exception:  # noqa: BLE001
        return None
    cmd = f"{HDR}theorem chk : {pa} → {pb} := by\n  intro h\n  intros\n  {PORTFOLIO}\n\n#print axioms chk"
    r = repl.run(cmd, timeout=timeout)
    if "timeout" in r or "dead" in r:
        return False
    errs = errors(r)  # each side was checked to elaborate on its own, so any error here is a failed proof
    if errs or uses_sorry(r):
        return False
    ax = axioms(r, "chk")
    return ax is not None and set(ax) <= ALLOWED


SELF = ("first\n    | (simp_all; done)\n    | aesop\n    | (norm_num; done)\n    | linarith\n    | nlinarith")


def selfprove(repl, stmt, timeout=20):
    """D1: True if the statement is provable by the portfolio without any hypothesis. Then an implication into it is
    uninformative and cannot count towards a leak tier."""
    try:
        pa = prop(stmt)
    except Exception:  # noqa: BLE001
        return None
    r = repl.run(f"{HDR}theorem triv : {pa} := by\n  intros\n  {SELF}\n\n#print axioms triv", timeout=timeout)
    if "timeout" in r or "dead" in r or errors(r) or uses_sorry(r):
        return False
    ax = axioms(r, "triv")
    return ax is not None and set(ax) <= ALLOWED


def elaborates(repl, stmt):
    try:
        pa = prop(stmt)
    except Exception:  # noqa: BLE001
        return False
    r = repl.run(f"{HDR}example : {pa} → True := fun _ => trivial", timeout=30)
    return not ("timeout" in r or "dead" in r or errors(r))


_repl = None


def init():
    global _repl
    _repl = Repl()


def work(item):
    key, a, b, mode = item
    t0 = time.time()
    try:
        out = dict(key=key)
        if not elaborates(_repl, a) or not elaborates(_repl, b):
            out["status"] = "unchecked"
        else:
            out["ab"] = check(_repl, a, b)  # a => b
            out["ba"] = check(_repl, b, a) if mode == "both" else None
            out["status"] = "checked"
            if out["ab"]:
                out["b_trivial"] = selfprove(_repl, b)  # D1: the conclusion side of a => b
            if out["ba"]:
                out["a_trivial"] = selfprove(_repl, a)
    except Exception as e:  # noqa: BLE001
        out = dict(key=key, status="error", error=repr(e)[:200])
        try:
            _repl.restart()
        except Exception:  # noqa: BLE001
            pass
    out["s"] = time.time() - t0
    return out


def run(items, out_path, workers, toolchain):
    assert os.environ.get("VAC_TOOLCHAIN", "v49") == toolchain, "set VAC_TOOLCHAIN before starting (lean_repl reads it at import)"
    done = set()
    if out_path.exists():
        done = {json.loads(l)["key"] for l in open(out_path)}
    todo = [it for it in items if it[0] not in done]
    print(f"{len(items)} pairs, {len(done)} done, {len(todo)} to run ({toolchain})", flush=True)
    with mp.Pool(workers, initializer=init) as pool, open(out_path, "a") as f:
        for i, o in enumerate(pool.imap_unordered(work, todo, chunksize=1)):
            f.write(json.dumps(o) + "\n"); f.flush()
            if (i + 1) % 200 == 0:
                print(i + 1, flush=True)


def leaks(bench, workers, toolchain):
    b = pd.read_parquet(RUN / "data" / "statements" / f"{bench}.parquet").set_index("id").stmt
    out_dir = RUN / "data" / "certify"
    out_dir.mkdir(exist_ok=True)
    for f in sorted((RUN / "data" / "candidates").glob(f"{bench}__*.parquet")):
        corp = f.stem.split("__")[1]
        if ("v415" if corp in LEAN415 else "v49") != toolchain:
            continue
        c = pd.read_parquet(RUN / "data" / "statements" / f"{corp}.parquet").set_index("id").stmt
        cand = pd.read_parquet(f).drop_duplicates(["bench_id", "corpus_id"])
        # train => test (a = corpus, b = bench) and test => train
        items = [(f"{x.bench_id}|{corp}|{x.corpus_id}", c[x.corpus_id], b[x.bench_id], "both") for x in cand.itertuples()]
        run(items, out_dir / f"{bench}__{corp}.jsonl", workers, "v415" if corp in LEAN415 else "v49")


if __name__ == "__main__":
    if sys.argv[1] == "leaks":
        leaks(sys.argv[2], int(sys.argv[3]), os.environ.get("VAC_TOOLCHAIN", "v49"))
