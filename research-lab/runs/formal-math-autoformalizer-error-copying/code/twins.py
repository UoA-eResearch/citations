"""Plan section 3: twins (T) and paraphrases (P), their checks, and the frozen catalogue.

  twins.py prepare            -> results/catalogue/twins/in_NN.json (items for the twin builder) and
                                 results/catalogue/paraphrase/in_NN.json (NL only); items = included + one-rater set
  twins.py diffcheck          -> checks 3-4 for every built twin (numerals-only diffs, answer script)
  VAC_TOOLCHAIN=v49 twins.py lean 22  -> checks 1, 2, 5 and truth-certified, results/catalogue/twins/lean.jsonl
  twins.py judge_prepare      -> results/catalogue/paraphrase/judge_NN.md (blinded pairs) + key in data/
  twins.py freeze             -> results/catalogue/frozen.jsonl and attrition tables"""
import json
import multiprocessing as mp
import random
import re
import subprocess
import sys
import tempfile
import time
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
CAT = RUN / "results" / "catalogue"
TW, PA = CAT / "twins", CAT / "paraphrase"
PY = str(RUN.parent / "formal-math-certified-contamination-did" / "venv" / "bin" / "python")
SEED, SIZE = 20261012, 20
TOK = re.compile(r"\d+(?:\.\d+)?|<ANS>|\w+|\S")
NUM = re.compile(r"^\d+(?:\.\d+)?$")
sys.path.insert(0, str(Path(__file__).resolve().parent))


def items():
    f = pd.read_json(CAT / "filtered.jsonl", lines=True).set_index("item")
    t = pd.read_json(CAT / "tags.jsonl", lines=True)
    t = t[t.included | t.one_rater].copy()
    t["set"] = t.included.map({True: "included", False: "one_rater"})
    return t.join(f, on="item")


def prepare():
    TW.mkdir(parents=True, exist_ok=True)
    PA.mkdir(parents=True, exist_ok=True)
    df = items().sort_values("item").reset_index(drop=True)
    recs = []
    for r in df.itertuples():
        reasons = "; ".join(x for x in (r.A_D_reason, r.B_D_reason) if isinstance(x, str))
        recs.append(dict(id=r.tid, N=r.nl, D=r.D.strip(), C=r.C.strip(), defect=reasons))
    for b in range(0, len(recs), SIZE):
        json.dump(recs[b:b + SIZE], open(TW / f"in_{b // SIZE:02d}.json", "w"), indent=1, ensure_ascii=False)
        json.dump([dict(id=x["id"], statement=x["N"]) for x in recs[b:b + SIZE]],
                  open(PA / f"in_{b // SIZE:02d}.json", "w"), indent=1, ensure_ascii=False)
    print(len(recs), "items;", (len(recs) + SIZE - 1) // SIZE, "batches")


def toks(s, ans=None):
    if ans and ans in s:
        s = s.replace(ans, " <ANS> ")
    return TOK.findall(s)


def numerals_only(a, b, ans=None):
    """True if b differs from a only in numerals, apart from regions aligned with the declared answer span in b."""
    ta, tb = toks(a), toks(b, ans)
    for op, i1, i2, j1, j2 in SequenceMatcher(None, ta, tb, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        if "<ANS>" in tb[j1:j2]:
            continue
        if not all(NUM.match(x) for x in ta[i1:i2] + tb[j1:j2]):
            return False
    return True


def script_ok(script, value):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "a.py"
        p.write_text(script)
        try:
            r = subprocess.run([PY, str(p)], capture_output=True, text=True, timeout=60, cwd=d)
        except subprocess.TimeoutExpired:
            return False
    out = r.stdout.strip().splitlines()
    return bool(out) and re.sub(r"\s+", "", out[-1]) == re.sub(r"\s+", "", str(value))


def built():
    rows = []
    for f in sorted(TW.glob("out_*.json")):
        rows += json.load(open(f))
    return {r["id"]: r for r in rows}


def diffcheck():
    src = {x["id"]: x for f in sorted(TW.glob("in_*.json")) for x in json.load(open(f))}
    out = []
    for tid, t in built().items():
        s = src[tid]
        r = dict(id=tid, skip=t.get("skip"))
        if not t.get("skip"):
            ans = t.get("answer_span") or None
            r["N_numerals_only"] = numerals_only(s["N"], t["N_twin"], ans)
            r["D_numerals_only"] = numerals_only(s["D"], t["D_twin"], ans)
            r["C_numerals_only"] = numerals_only(s["C"], t["C_twin"], ans)
            r["N_changed"] = any(NUM.match(x) for x in toks(s["N"])) and toks(s["N"]) != toks(t["N_twin"])
            r["script_ok"] = script_ok(t.get("answer_script") or "", t.get("answer_value"))
        out.append(r)
    pd.DataFrame(out).to_json(TW / "diffcheck.jsonl", orient="records", lines=True)
    d = pd.DataFrame(out)
    print(d.drop(columns=["id"]).describe(include="all").T[["count", "top", "freq"]])


_repl = None


def init():
    global _repl
    from lean_check import Repl
    _repl = Repl()


def lwork(task):
    import lean_check as L
    tid, D2, C2, oD, oC = task
    out = dict(id=tid)
    try:
        out["D_elab"] = L.elaborates(_repl, D2, oD)
        out["C_elab"] = L.elaborates(_repl, C2, oC)
        if out["D_elab"] and out["C_elab"]:
            out["DC"] = L.implies(_repl, D2, C2, oD, oC)
            out["CD"] = L.implies(_repl, C2, D2, oC, oD)
            out["C_refuted"] = L.refuted(_repl, C2, oC)
            out["C_proved"] = L.provable(_repl, C2, oC)
    except Exception as e:  # noqa: BLE001
        out["error"] = repr(e)[:300]
        try:
            _repl.restart()
        except Exception:  # noqa: BLE001
            pass
    return out


def lean(workers):
    import lean_check as L
    df = items().set_index("tid")
    tasks = []
    for tid, t in built().items():
        if t.get("skip"):
            continue
        r = df.loc[tid]
        tasks.append((tid, t["D_twin"], t["C_twin"], L.opens_of(r.D_header), L.opens_of(r.C_header)))
    path = TW / "lean.jsonl"
    done = {json.loads(l)["id"] for l in open(path)} if path.exists() else set()
    tasks = [x for x in tasks if x[0] not in done]
    print(len(tasks), "twins to check", flush=True)
    with mp.Pool(workers, initializer=init) as pool, open(path, "a") as f:
        for o in pool.imap_unordered(lwork, tasks, chunksize=1):
            f.write(json.dumps(o) + "\n")
            f.flush()
    print("TWIN LEAN DONE", flush=True)


def judge_prepare():
    rng = random.Random(SEED + 1)
    src = {x["id"]: x["statement"] for f in sorted(PA.glob("in_*.json")) for x in json.load(open(f))}
    para = {x["id"]: x["paraphrase"] for f in sorted(PA.glob("out_*.json")) for x in json.load(open(f))}
    key, ids = {}, sorted(para)
    for b in range(0, len(ids), 40):
        lines = [f"# Paraphrase judging batch {b // 40:02d}\n"]
        for tid in ids[b:b + 40]:
            first = rng.random() < 0.5
            key[tid] = "original_first" if first else "paraphrase_first"
            t1, t2 = (src[tid], para[tid]) if first else (para[tid], src[tid])
            lines.append(f"## {tid}\n\n**Text 1**\n\n{t1}\n\n**Text 2**\n\n{t2}\n")
        (PA / f"judge_{b // 40:02d}.md").write_text("\n".join(lines))
    (RUN / "data" / "paraphrase_key.json").write_text(json.dumps(key, indent=1))
    print(len(ids), "paraphrases in", (len(ids) + 39) // 40, "judge batches")


def freeze():
    df = items()
    tw = built()
    dc = pd.read_json(TW / "diffcheck.jsonl", lines=True).set_index("id")
    ln = pd.read_json(TW / "lean.jsonl", lines=True).set_index("id")
    para = {x["id"]: x["paraphrase"] for f in sorted(PA.glob("out_*.json")) for x in json.load(open(f))}
    judged = {x["id"]: x["same"] for f in sorted(PA.glob("judge_out_*.json")) for x in json.load(open(f))}
    recs, att = [], []
    for r in df.itertuples():
        t = tw.get(r.tid, {})
        fate = "not built"
        if t.get("skip"):
            fate = "skipped by builder"
        elif r.tid in dc.index:
            d = dc.loc[r.tid]
            l = ln.loc[r.tid] if r.tid in ln.index else None
            if not (d.N_numerals_only and d.D_numerals_only and d.C_numerals_only and d.N_changed):
                fate = "check 3: non-numeral diff"
            elif not d.script_ok:
                fate = "check 4: answer script"
            elif l is None or not (l.D_elab and l.C_elab):
                fate = "check 1: does not elaborate"
            elif l.DC and l.CD:
                fate = "check 2: defect dissolved"
            elif l.C_refuted:
                fate = "check 5: corrected twin refuted"
            else:
                fate = "valid"
        valid = fate == "valid"
        rec = dict(item=r.item, tid=r.tid, source=r.source, role="primary", set=r.set, category=r.category, env=r.env,
                   nl=r.nl, D=r.D, D_header=r.D_header, C=r.C, C_header=r.C_header, twin_fate=fate,
                   N_twin=t.get("N_twin") if valid else None, D_twin=t.get("D_twin") if valid else None,
                   C_twin=t.get("C_twin") if valid else None,
                   twin_truth_certified=bool(valid and ln.loc[r.tid].C_proved),
                   paraphrase=para.get(r.tid) if judged.get(r.tid) else None,
                   paraphrase_fate=("judged same" if judged.get(r.tid) else "judged different" if r.tid in judged
                                    else "none"))
        recs.append(rec)
    ctl = pd.read_json(CAT / "filtered.jsonl", lines=True)
    for r in ctl[(ctl.role == "control") & (ctl.fate == "kept")].itertuples():
        recs.append(dict(item=r.item, tid=None, source=r.source, role="control", set="control", category=None, env=r.env,
                         nl=r.nl, D=r.D, D_header=r.D_header, C=r.C, C_header=r.C_header, twin_fate=None, N_twin=None,
                         D_twin=None, C_twin=None, twin_truth_certified=False, paraphrase=None, paraphrase_fate=None))
    out = pd.DataFrame(recs)
    out.to_json(CAT / "frozen.jsonl", orient="records", lines=True, force_ascii=False)
    a = out[out.role == "primary"].groupby(["set", "source", "twin_fate"]).size().unstack(fill_value=0)
    a.to_csv(CAT / "attrition_twins.csv")
    print(a)
    print(out[out.role == "primary"].groupby(["set", "paraphrase_fate"]).size())


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "lean":
        lean(int(sys.argv[2]))
    else:
        {"prepare": prepare, "diffcheck": diffcheck, "judge_prepare": judge_prepare, "freeze": freeze}[cmd]()
