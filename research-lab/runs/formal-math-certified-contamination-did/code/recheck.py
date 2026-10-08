"""D3: informativeness recheck for every certified implication. For a certified a => b, run the identical command with
a replaced by True (same portfolio, 60 s). If that also succeeds, or times out, the certificate does not depend on a
and the implication is not informative (fail-closed). Supersedes D1's smaller self-provability portfolio, which failed
open on timeouts. Usage: VAC_TOOLCHAIN=<v49|v415> recheck.py <bench> <workers>.
Writes data/certify/recheck_<bench>__<corpus>.jsonl with key, ab_inf, ba_inf."""
import json
import multiprocessing as mp
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import certify as C  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def informative(repl, b, timeout=60):
    """True if (True -> forall b) is NOT provable by the portfolio within the timeout; False if it is or times out."""
    try:
        pb = C.prop(b)
    except Exception:  # noqa: BLE001
        return False
    r = repl.run(f"{C.HDR}theorem chk : True → {pb} := by\n  intro h\n  intros\n  {C.PORTFOLIO}\n\n#print axioms chk", timeout=timeout)
    if "timeout" in r or "dead" in r:
        return False
    proved = not C.errors(r) and not C.uses_sorry(r) and (C.axioms(r, "chk") is not None)
    return not proved


def work(item):
    key, a, b, ab, ba = item
    try:
        return dict(key=key, ab_inf=informative(C._repl, b) if ab else None, ba_inf=informative(C._repl, a) if ba else None)
    except Exception as e:  # noqa: BLE001
        try:
            C._repl.restart()
        except Exception:  # noqa: BLE001
            pass
        return dict(key=key, error=repr(e)[:200])


def main(bench, workers):
    tc = os.environ.get("VAC_TOOLCHAIN", "v49")
    b = pd.read_parquet(RUN / "data" / "statements" / f"{bench}.parquet").drop_duplicates("id").set_index("id").stmt
    for f in sorted((RUN / "data" / "certify").glob(f"{bench}__*.jsonl")):
        corp = f.stem.split("__")[1]
        if ("v415" if corp in C.LEAN415 else "v49") != tc:
            continue
        c = pd.read_parquet(RUN / "data" / "statements" / f"{corp}.parquet").drop_duplicates("id").set_index("id").stmt
        items = []
        for line in open(f):
            r = json.loads(line)
            if r.get("status") == "checked" and (r.get("ab") or r.get("ba")):
                item, _, cid = r["key"].split("|", 2)
                items.append((r["key"], c[cid], b[item], bool(r.get("ab")), bool(r.get("ba"))))
        out = RUN / "data" / "certify" / f"recheck_{bench}__{corp}.jsonl"
        done = {json.loads(l)["key"] for l in open(out)} if out.exists() else set()
        todo = [it for it in items if it[0] not in done]
        print(corp, len(items), "certified implications,", len(todo), "to recheck", flush=True)
        with mp.Pool(workers, initializer=C.init) as pool, open(out, "a") as fo:
            for res in pool.imap_unordered(work, todo, chunksize=1):
                fo.write(json.dumps(res) + "\n"); fo.flush()


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
