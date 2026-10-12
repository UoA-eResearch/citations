"""D6: informativeness of the references. For every primary item in the frozen catalogue, test whether the defective
reference D (and, for items with a twin, D') is proved outright or refuted by the portfolios of lean_check (the same
`provable` and `refuted` used for the twins' truth screen). If a reference is portfolio-provable, any portfolio-provable
output is certified equivalent to it; if it is refuted, `D -> O` may hold by explosion. Either way "equivalent to D"
then does not mean "copies D". Writes results/catalogue/refcheck.jsonl.
Usage: VAC_TOOLCHAIN=v49 refcheck.py <workers>"""
import json
import multiprocessing as mp
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
CAT = RUN / "results" / "catalogue"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lean_check as L  # noqa: E402

_repl = None


def init():
    global _repl
    _repl = L.Repl()


def work(task):
    item, ref, text, opens = task
    out = dict(item=item, ref=ref)
    try:
        out["proved"] = L.provable(_repl, text, opens)
        out["refuted"] = L.refuted(_repl, text, opens)
    except Exception as e:  # noqa: BLE001
        out["error"] = repr(e)[:300]
        try:
            _repl.restart()
        except Exception:  # noqa: BLE001
            pass
    return out


def main(workers):
    tasks = []
    for r in map(json.loads, open(CAT / "frozen.jsonl")):
        if r["role"] != "primary":
            continue
        oD, oC = L.opens_of(r["D_header"]), L.opens_of(r["C_header"])
        tasks += [(r["item"], "D", r["D"], oD), (r["item"], "C", r["C"], oC)]
        if r.get("D_twin"):
            tasks += [(r["item"], "D_twin", r["D_twin"], oD), (r["item"], "C_twin", r["C_twin"], oC)]
    print(len(tasks), "references", flush=True)
    with mp.Pool(workers, initializer=init) as pool, open(CAT / "refcheck.jsonl", "w") as f:
        for o in pool.imap_unordered(work, tasks, chunksize=1):
            f.write(json.dumps(o) + "\n")
            f.flush()
    print("REFCHECK DONE", flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]))
