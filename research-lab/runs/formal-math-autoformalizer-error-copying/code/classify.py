"""Plan section 5: classify every sampled output in Lean.

For each output: extract the statement (last ```lean/```lean4 block, else the whole text, after any </think>), parse
it, and in the item's environment test elaboration and equivalence with the condition's references (D and C for O and
P; D' and C' for T): O -> D and D -> O, O -> C and C -> O (certify-style portfolio, 20 s per direction). Identical
normalised statements within an item x condition are checked once. Also records the verbatim test (normalised binders
and conclusion equal to D's, hypothesis names kept).
Usage: VAC_TOOLCHAIN=v49 classify.py <model> <workers>  ->  data/classified/<model>.jsonl (one line per unique
statement per item x condition) and data/classified/<model>_outputs.jsonl (one line per output, pointing to it)."""
import json
import multiprocessing as mp
import re
import sys
import time
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
CAT = RUN / "results" / "catalogue"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lean_check as L  # noqa: E402

BLOCK = re.compile(r"```(?:lean4|lean)?[ \t]*\n(.*?)```", re.S)


def extract(text):
    if not text:
        return None
    t = text.split("</think>")[-1]
    blocks = BLOCK.findall(t)
    code = blocks[-1] if blocks else t
    try:
        L.parse(code)
    except L.ParseError:
        # an unterminated final block (truncated output): try the text after the last fence
        if "```" in t:
            code = re.split(r"```(?:lean4|lean)?[ \t]*\n", t)[-1]
            try:
                L.parse(code)
            except L.ParseError:
                return None
        else:
            return None
    return code


def norm_stmt(code):
    opens, b, c = L.parse(code)
    return re.sub(r"\s+", " ", f"{' | '.join(opens)} || {b} : {c}").strip()


def verbatim_key(code):
    _, b, c = L.parse(code)
    return re.sub(r"\s+", " ", f"{b} : {c}").strip()


def refs():
    out = {}
    for r in map(json.loads, open(CAT / "frozen.jsonl")):
        o = L.opens_of(r["D_header"])
        oc = L.opens_of(r["C_header"])
        out[f"{r['item']}|O"] = out[f"{r['item']}|P"] = dict(D=r["D"], C=r["C"], oD=o, oC=oc)
        if r.get("D_twin"):
            out[f"{r['item']}|T"] = dict(D=r["D_twin"], C=r["C_twin"], oD=o, oC=oc)
    return out


_repl = None


def init():
    global _repl
    _repl = L.Repl()


def work(task):
    uid, code, ref = task
    t0 = time.time()
    out = dict(uid=uid)
    try:
        out["elab"] = L.elaborates(_repl, code, ref["oD"])
        if out["elab"]:
            # an output with no `open` lines of its own gets the item's default opens (the defective reference's)
            od = ref["oD"]
            a = L.implies(_repl, code, ref["D"], od, ref["oD"])
            out["copy"] = bool(a and L.implies(_repl, ref["D"], code, ref["oD"], od))
            b = L.implies(_repl, code, ref["C"], od, ref["oC"])
            out["correct"] = bool(b and L.implies(_repl, ref["C"], code, ref["oC"], od))
            out["to_D"], out["to_C"] = bool(a), bool(b)
    except Exception as e:  # noqa: BLE001
        out["error"] = repr(e)[:300]
        try:
            _repl.restart()
        except Exception:  # noqa: BLE001
            pass
    out["s"] = round(time.time() - t0, 1)
    return out


def main(model, workers):
    R = refs()
    vkey = {k: verbatim_key(v["D"]) for k, v in R.items()}
    dst = RUN / "data" / "classified"
    dst.mkdir(parents=True, exist_ok=True)
    unique, rows = {}, []
    for line in open(RUN / "data" / "samples" / f"{model}.jsonl"):
        s = json.loads(line)
        key = s["key"]
        outs = [(str(i), o) for i, o in enumerate(s.get("outputs") or [])] + [("g", o) for o in (s.get("greedy") or [])]
        for idx, o in outs:
            code = extract(o.get("text"))
            row = dict(key=key, idx=idx, finish=o.get("finish"), extracted=code is not None)
            if code is not None:
                n = norm_stmt(code)
                uid = f"{key}#{len(unique)}" if (key, n) not in unique else unique[(key, n)][0]
                if (key, n) not in unique:
                    unique[(key, n)] = (uid, code)
                row["uid"] = uid
                row["verbatim"] = verbatim_key(code) == vkey[key]
            rows.append(row)
    with open(dst / f"{model}_outputs.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    path = dst / f"{model}.jsonl"
    done = {json.loads(l)["uid"] for l in open(path)} if path.exists() else set()
    tasks = [(uid, code, R[uid.split("#")[0]]) for (key, n), (uid, code) in unique.items() if uid not in done]
    print(f"{model}: {len(rows)} outputs, {len(unique)} unique statements, {len(tasks)} to check", flush=True)
    with mp.Pool(workers, initializer=init) as pool, open(path, "a") as f:
        for i, o in enumerate(pool.imap_unordered(work, tasks, chunksize=1)):
            f.write(json.dumps(o) + "\n")
            f.flush()
            if (i + 1) % 500 == 0:
                print(i + 1, time.strftime("%H:%M:%S"), flush=True)
    print(f"{model} CLASSIFY DONE", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
