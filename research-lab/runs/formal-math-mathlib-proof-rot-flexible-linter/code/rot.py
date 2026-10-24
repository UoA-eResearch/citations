"""Mathlib proof rot (plan sections 2-4).

  rot.py test                  parser and feature unit checks
  rot.py decls O N             parse both snapshots; population of matched declarations -> data/work/pop_<O>_<N>.parquet
  rot.py label O               compile population files of O with -Dlinter.flexible=true -> data/work/label_<O>.parquet
  rot.py replay O N            replay O proof bodies into N files and compile -> data/work/replay_<O>_<N>.parquet
"""
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
SNAPS, WORK = D / "snaps", D / "work"
WORK.mkdir(parents=True, exist_ok=True)
ELAN = Path.home() / ".elan" / "bin"
CMD = re.compile(r"^(theorem|lemma|def|instance|example|abbrev|structure|class|inductive|namespace|section|end|variable|"
                 r"open|universe|noncomputable|private|protected|nonrec|@\[|/--|/-!|#|attribute|alias|set_option|macro|syntax|"
                 r"elab|notation|local|scoped|irreducible_def|deriving|initialize|mutual|omit|include|suppress_compilation|"
                 r"unseal|export|library_note|assert_not_exists|import|module|public|meta|opaque|axiom|add_decl_doc|"
                 r"register_|recall|unif_hint|instance|termination_by)")
DECL = re.compile(r"^(?:@\[[^\]]*\]\s*)*(?:(?:private|protected|nonrec|noncomputable)\s+)*(theorem|lemma)\s+([^\s(:{\[⦃]+)")
SIMP_ANY = re.compile(r"\b(simp_all|simpa|dsimp|field_simp|simp)\b")
SIMP_UNR = re.compile(r"\b(simp_all|simp)\b(?!\?)(?!\s+only)(?!_)")


def strip_comments(s):
    s = re.sub(r"/-.*?-/", lambda m: "\n" * m.group(0).count("\n"), s, flags=re.S)
    return re.sub(r"--[^\n]*", "", s)


def parse(text):
    """Declarations: qualified name, statement (normalised), proof body, 1-based line span [start, end]."""
    lines = text.split("\n")
    starts = [i for i, l in enumerate(lines) if l and not l[0].isspace() and CMD.match(l)]
    starts.append(len(lines))
    ns, out = [], []
    clean = strip_comments(text).split("\n")
    for k, i in enumerate(starts[:-1]):
        l = clean[i] if i < len(clean) else lines[i]
        m = re.match(r"^namespace\s+(\S+)", l)
        if m:
            ns.append(("ns", m.group(1))); continue
        if re.match(r"^(?:@\[[^\]]*\]\s*)?(?:(?:public|private|noncomputable|meta)\s+)*section\b", l):
            ns.append(("sec", "")); continue
        m = re.match(r"^end\b\s*(\S*)", l)
        if m and ns:
            ns.pop(); continue
        m = DECL.match(l)
        if not m:
            continue
        j = starts[k + 1]
        while j - 1 > i and not lines[j - 1].strip():
            j -= 1
        block = "\n".join(lines[i:j])
        bclean = strip_comments(block)
        pos = re.search(r":=\s*by\b", bclean)
        if not pos:
            continue
        name = m.group(2)
        qual = ".".join([n for t, n in ns if t == "ns"] + [name])
        head = bclean[m.end():pos.start()]
        body = block[len(block) - len(bclean) + pos.end():] if len(block) == len(bclean) else block[pos.end():]
        out.append({"name": qual, "statement": " ".join(head.split()), "body": body, "start": i + 1, "end": j,
                    "body_offset_line": i + 1 + bclean[:pos.end()].count("\n")})
    return out


def features(body):
    b = strip_comments(body)
    ls = [x for x in b.split("\n") if x.strip()]
    tactics = len(ls) + b.count(";") + b.count("<;>")
    nsimp = len(SIMP_ANY.findall(b))
    nonterm = False
    for idx, ln in enumerate(ls):
        for mm in SIMP_UNR.finditer(ln):
            rest = ln[mm.end():]
            if re.search(r"(;|<;>)\s*\S", rest):
                nonterm = True
                break
            ind = len(ln) - len(ln.lstrip())
            nxt = ls[idx + 1] if idx + 1 < len(ls) else None
            if nxt is not None:
                nind = len(nxt) - len(nxt.lstrip())
                if nind >= ind and not (nind == ind and nxt.lstrip().startswith(("·", "case ", "next"))):
                    nonterm = True
                    break
        if nonterm:
            break
    return {"tactics": max(tactics, 1), "n_simp": nsimp, "nonterm_simp": nonterm}


def decls(o, n):
    rows = []
    for f in sorted((SNAPS / o / "Mathlib").rglob("*.lean")):
        rel = f.relative_to(SNAPS / o)
        fn = SNAPS / n / rel
        if not fn.exists():
            continue
        try:
            do = parse(f.read_text())
        except Exception:
            continue
        cand = [d for d in do if features(d["body"])["nonterm_simp"]]
        if not cand:
            continue
        dn = {d["name"]: d for d in parse(fn.read_text())}
        for d in cand:
            m = dn.get(d["name"])
            if m is None or m["statement"] != d["statement"]:
                continue
            rows.append({"file": str(rel), "name": d["name"], "o_start": d["start"], "o_end": d["end"],
                         "body_o": d["body"], "same_body": d["body"].strip() == m["body"].strip(), **features(d["body"])})
    P = pd.DataFrame(rows)
    P.to_parquet(WORK / f"pop_{o}_{n}.parquet", index=False)
    print(len(P), "population declarations in", P.file.nunique() if len(P) else 0, "files;", int(P.same_body.sum()) if len(P) else 0, "with unchanged bodies")


def lean(snap, path, extra=(), timeout=1800):
    env = dict(os.environ, PATH=f"{ELAN}:{os.environ['PATH']}")
    try:
        r = subprocess.run(["lake", "env", "lean", *extra, str(path)], cwd=SNAPS / snap, capture_output=True, timeout=timeout, env=env)
        return r.returncode, r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return -9, "TIMEOUT"


MSG = re.compile(r"^(.*?):(\d+):(\d+): (error|warning)(?:\([^)]*\))?: (.*)$")


def messages(out):
    res, cur = [], None
    for ln in out.split("\n"):
        m = MSG.match(ln)
        if m:
            cur = {"line": int(m.group(2)), "sev": m.group(4), "msg": m.group(5)}
            res.append(cur)
        elif cur is not None:
            cur["msg"] += "\n" + ln
    return res


def label(o):
    pops = [pd.read_parquet(p) for p in WORK.glob(f"pop_{o}_*.parquet")]
    P = pd.concat(pops).drop_duplicates(["file", "name"])
    files = sorted(P.file.unique())

    inject = "FlexibleLinter" not in (SNAPS / o / "Mathlib" / "Init.lean").read_text()     # D1
    tmp = WORK / f"label_{o}"
    tmp.mkdir(exist_ok=True)

    def one(f):
        if inject:
            t = tmp / f.replace("/", "__")
            t.write_text("import Mathlib.Tactic.Linter.FlexibleLinter\n" + (SNAPS / o / f).read_text())
            code, out = lean(o, t, ["-Dweak.linter.flexible=true"])
            ms = messages(out)
            for m in ms:
                m["line"] -= 1
        else:
            code, out = lean(o, SNAPS / o / f, ["-Dweak.linter.flexible=true"])
            ms = messages(out)
        rows = []
        for r in P[P.file == f].itertuples():
            inside = [m for m in ms if r.o_start <= m["line"] <= r.o_end]
            rows.append({"file": f, "name": r.name, "flagged": any("linter.flexible" in m["msg"] for m in inside),
                         "o_errors": sum(1 for m in inside if m["sev"] == "error"), "o_timeout": out == "TIMEOUT"})
        return rows
    rows = []
    with ThreadPoolExecutor(int(os.environ.get("WORKERS", "14"))) as ex:
        for k, r in enumerate(ex.map(one, files), 1):
            rows += r
            if k % 100 == 0:
                print(k, "of", len(files), "files", flush=True)
    L = pd.DataFrame(rows)
    L.to_parquet(WORK / f"label_{o}.parquet", index=False)
    print("flagged", int(L.flagged.sum()), "of", len(L), "| O-side error-free", round(float((L.o_errors == 0).mean()), 4))


ERR = [("unknown_identifier", r"unknown (identifier|constant)|unknown namespace"), ("function_expected", r"function expected"),
       ("no_goals", r"no goals( to be (solved|proved))?"), ("simp_no_progress", r"simp made no progress|simp_all made no progress"),
       ("rewrite_failed", r"did not find instance of the pattern|motive is not type correct|rewrite failed"),
       ("type_mismatch", r"type mismatch"), ("unsolved_goals", r"unsolved goals"), ("timeout", r"heartbeats|TIMEOUT|deterministic")]


def eclass(msgs):
    for k, pat in ERR:
        if any(re.search(pat, m, re.I) for m in msgs):          # D2: case-insensitive (newer Lean capitalises)
            return k
    return "other"


def replay(o, n):
    P = pd.read_parquet(WORK / f"pop_{o}_{n}.parquet")
    out_dir = WORK / f"replay_{o}_{n}"
    out_dir.mkdir(exist_ok=True)

    def one(f):
        text = (SNAPS / n / f).read_text()
        dn = {d["name"]: d for d in parse(text)}
        lines = text.split("\n")
        sub = P[P.file == f]
        reps = []
        for r in sub.itertuples():
            d = dn.get(r.name)
            if d:
                reps.append((d, r.body_o))
        # replace bottom-up: the body runs from the ":= by" position to the end of the declaration block
        for d, body in sorted(reps, key=lambda x: -x[0]["start"]):
            block = "\n".join(lines[d["start"] - 1:d["end"]])
            pos = re.search(r":=\s*by\b", strip_comments(block))
            new_block = block[:pos.end()] + body
            lines[d["start"] - 1:d["end"]] = new_block.split("\n")
        new = "\n".join(lines)
        tgt = out_dir / (f.replace("/", "__"))
        tgt.write_text(new)
        code, outp = lean(n, tgt)
        ms = messages(outp)
        spans = {d["name"]: d for d in parse(new)}
        rows = []
        for r in sub.itertuples():
            d = spans.get(r.name)
            if d is None:
                rows.append({"file": f, "name": r.name, "fail": True, "eclass": "lost_in_rewrite", "n_err": 0}); continue
            errs = [m["msg"] for m in ms if m["sev"] == "error" and d["start"] <= m["line"] <= d["end"]]
            to = outp == "TIMEOUT"
            rows.append({"file": f, "name": r.name, "fail": bool(errs) or to, "eclass": "timeout" if to else (eclass(errs) if errs else ""),
                         "n_err": len(errs), "only_unknown_id": bool(errs) and all(re.search(ERR[0][1], e, re.I) for e in errs),
                         "msgs": " || ".join(e[:200].replace("\n", " ") for e in errs[:3])})
        return rows
    rows = []
    files = sorted(P.file.unique())
    with ThreadPoolExecutor(int(os.environ.get("WORKERS", "14"))) as ex:
        for k, r in enumerate(ex.map(one, files), 1):
            rows += r
            if k % 100 == 0:
                print(k, "of", len(files), "files", flush=True)
    R = pd.DataFrame(rows)
    R.to_parquet(WORK / f"replay_{o}_{n}.parquet", index=False)
    print("fail", round(float(R.fail.mean()), 4), "of", len(R), R.eclass.value_counts().to_dict())


def test():
    src = """namespace Foo

/-- doc -/
@[simp] theorem bar (x : Nat) : x + 0 = x := by
  simp
  rfl

lemma baz : True := by
  simp only [foo]
  trivial

theorem qux (n : Nat) :
    n = n := by
  simp at h
  exact rfl

end Foo
"""
    ds = parse(src)
    names = [d["name"] for d in ds]
    assert names == ["Foo.bar", "Foo.baz", "Foo.qux"], names
    assert features(ds[0]["body"])["nonterm_simp"] and not features(ds[1]["body"])["nonterm_simp"]
    assert features(ds[2]["body"])["nonterm_simp"] and ds[2]["statement"] == "(n : Nat) : n = n", ds[2]["statement"]
    assert not features("\n  constructor\n  · simp\n  · simp")["nonterm_simp"]
    assert features("\n  simp; ring_nf")["nonterm_simp"]
    src2 = "namespace A\n\n@[expose] public section\n\ntheorem t : True := by\n  simp\n  trivial\n\nend\n\ntheorem u : True := by\n  simp\n  trivial\n\nend A\n"
    assert [d["name"] for d in parse(src2)] == ["A.t", "A.u"], [d["name"] for d in parse(src2)]
    print("rot tests pass")


if __name__ == "__main__":
    a = sys.argv
    {"test": lambda: test(), "decls": lambda: decls(a[2], a[3]), "label": lambda: label(a[2]),
     "replay": lambda: replay(a[2], a[3])}[a[1]]()
