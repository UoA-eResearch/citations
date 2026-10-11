"""D9: per benchmark item (miniF2F, Lean 4.9): (a) automation-provable, i.e. provable alone by the D3a FREE portfolio
(60 s); (b) vacuous, i.e. its hypotheses are contradictory: `theorem v B : C := by exfalso; <automation>` (as in the
vacuity study's v2 certificate). Vacuous items are dropped from the DiD units. Writes results/tables/bench_items.csv."""
import multiprocessing as mp
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import certify as C  # noqa: E402
import recheck as R  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
EXF = ["omega", "linarith", "(norm_num at *)", "simp_all", "nlinarith", "aesop"]
NAME = re.compile(r"\(([^():]+?)\s*:")


def exf(binders):
    """D9 addendum: each branch must close the goal; hypotheses are also instantiated at 0-3 (e.g. h0 : forall n, n | 7
    is refuted by h0 3), as in the explosion guard."""
    names = [n for g in NAME.findall(binders) for n in g.split()]
    br = [f"({t}; done)" for t in EXF]
    br += [f"(have := {n} {w}; norm_num at this; done)" for n in names for w in (0, 1, 2, 3)]
    return "first\n" + "\n".join(f"    | {b}" for b in br)


def _proved_refutation(stmt):
    """witness_refutable() counts a timeout as refutable (fail-closed for the guard); here only a kernel-checked
    refutation counts (D9 addendum: a benchmark statement that is false as formalised, e.g. valid/aime_1988_p3)."""
    r = C._repl.run(f"{C.HDR}theorem chk : ¬ {C.prop(stmt)} := by\n  intro h\n  {R.WITNESS}\n\n#print axioms chk", timeout=60)
    return "timeout" not in r and "dead" not in r and not C.errors(r) and not C.uses_sorry(r) and C.axioms(r, "chk") is not None


def work(item):
    iid, stmt = item
    try:
        provable = not R.informative(C._repl, stmt)
        b, c = C.split(stmt)
        r = C._repl.run(f"{C.HDR}set_option maxHeartbeats 100000 in\ntheorem v {b} : {c} := by\n  exfalso\n  {exf(b)}\n\n#print axioms v", timeout=60)
        vac = "timeout" not in r and "dead" not in r and not C.errors(r) and not C.uses_sorry(r) and C.axioms(r, "v") is not None
        refuted = R.witness_refutable(C._repl, stmt) is True and _proved_refutation(stmt)
        return dict(item=iid, automation_provable=provable, vacuous=vac, refuted=refuted)
    except Exception as e:  # noqa: BLE001
        return dict(item=iid, error=repr(e)[:150])


def main(workers):
    b = pd.read_parquet(RUN / "data" / "statements" / "bench_minif2f.parquet")
    with mp.Pool(int(workers), initializer=C.init) as pool:
        res = pool.map(work, list(zip(b.id, b.stmt)), chunksize=1)
    d = pd.DataFrame(res)
    d.to_csv(RUN / "results" / "tables" / "bench_items.csv", index=False)
    print(d[["automation_provable", "vacuous", "refuted"]].sum().to_dict(), "errors", int(d.get("error", pd.Series()).notna().sum()))


if __name__ == "__main__":
    main(sys.argv[1])
