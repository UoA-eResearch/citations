"""Split-repair sensitivity pass (deviations.md D2). For re-verified rows that failed the split check: re-verify,
check `example : ∀ B, _ := orig` (B is the hypothesis telescope; conclusion inferred), and if it passes run only the
automation portfolio (b) on `theorem v B : False`. Usage: repair_split.py <sample.parquet> <rows.jsonl> <out.jsonl> <workers>"""
import json
import multiprocessing as mp
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lean_repl import Repl, errors  # noqa: E402
from vacuity import AUTO, cert_ok, parse  # noqa: E402

_repl = None


def init():
    global _repl
    _repl = Repl()


def repair(item):
    rid, prompt, target = item
    out = dict(row_id=int(rid))
    try:
        p = parse(prompt)
        B, pre, body = p["binders"], p["preamble"], p["body"]
        if not B:
            out.update(repair_ok=False, repair_reason="no binders")
            return out
        orig = "orig_thm"
        cmd = body[:p["decl_start"]] + body[p["decl_start"]:p["name_end"]].rsplit(p["name"], 1)[0] + orig + body[p["name_end"]:] + target
        _repl.ensure(2)
        r = _repl.run(cmd, timeout=100)
        if "timeout" in r or "dead" in r or errors(r):
            out.update(repair_ok=False, repair_reason="reverify failed")
            return out
        r2 = _repl.run(f"example : ∀ {B}, _ := {orig}", env=r["env"], timeout=30)
        out["repair_ok"] = not ("timeout" in r2 or "dead" in r2 or errors(r2))
        if not out["repair_ok"]:
            out["repair_reason"] = "telescope check failed"
            return out
        v, out["auto"] = "vac_thm", None
        for tac in AUTO:
            stmt = f"theorem {v} : ∀ {B}, False := by\n  decide" if tac == "decide" else f"theorem {v} {B} : False := by\n  {tac}"
            r = _repl.run(f"{pre}set_option maxHeartbeats 100000 in\n{stmt}\n\n#print axioms {v}", timeout=30)
            ok, ax = cert_ok(r, v)
            if ok:
                out["auto"], out["auto_axioms"] = tac, ax
                break
        out["vacuous_repair"] = bool(out["auto"])
    except Exception as e:  # noqa: BLE001
        out["worker_error"] = repr(e)[:300]
        try:
            _repl.restart()
        except Exception:  # noqa: BLE001
            pass
    return out


def main(sample, rows, outp, workers):
    d = pd.DataFrame([json.loads(line) for line in open(rows)])
    ids = set(d[(d.reverify == True) & (d.split_ok == False)].row_id)  # noqa: E712
    s = pd.read_parquet(sample)
    s = s[s.row_id.isin(ids)]
    items = [(r.row_id, r.prompt, r.target) for r in s.itertuples()]
    print(len(items), "rows to repair", flush=True)
    with mp.Pool(int(workers), initializer=init) as pool, open(outp, "w") as f:
        for o in pool.imap_unordered(repair, items):
            f.write(json.dumps(o) + "\n")
    print("done", flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:])
