"""Reformulations (plan section 4). R1: every bound variable and hypothesis renamed (fresh names), variable groups first
and hypothesis groups in reverse order. R2: R1 plus every top-level equality flipped (a = b -> b = a) in hypotheses and
the conclusion. Each is kept only if the Lean kernel certifies original <=> reformulation in both directions, in the
environment of each prover (Lean 4.9 and 4.15). Run with VAC_TOOLCHAIN=v49 and v415 separately:
  reform.py build            -> data/reforms.parquet (text only)
  reform.py certify <workers>  -> data/certify/reforms_<toolchain>.jsonl"""
import os
import re
import sys
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
OPEN, CLOSE = "([{⦃", ")]}⦄"
IDCH = r"[\w'₀-₉Ͱ-Ͽ]"
FRESH_VARS = ["u", "v", "w", "s", "t", "p", "q", "r", "m", "k", "j", "i", "e", "g", "z", "y", "x", "d", "c", "b", "a"]


def groups(binders):
    out, depth, cur = [], 0, ""
    for ch in binders:
        if ch in OPEN:
            if depth == 0 and cur.strip():
                out.append(cur.strip()); cur = ""
            depth += 1
        cur += ch
        if ch in CLOSE:
            depth -= 1
            if depth == 0:
                out.append(cur.strip()); cur = ""
    if cur.strip():
        out.append(cur.strip())
    return out


def names_type(g):
    inner = g[1:-1]
    if ":" not in inner:
        return [], inner
    n, t = inner.split(":", 1)
    return n.split(), t


def rename(text, mapping):
    for old, new in sorted(mapping.items(), key=lambda kv: -len(kv[0])):
        text = re.sub(rf"(?<![\w.'₀-₉]){re.escape(old)}(?!{IDCH})", new, text)
    return text


def flip_eq(t):
    """Flip a single top-level '=' (not part of ≠, :=, ==, <=, >=)."""
    depth, pos = 0, []
    for i, ch in enumerate(t):
        if ch in OPEN:
            depth += 1
        elif ch in CLOSE:
            depth -= 1
        elif ch == "=" and depth == 0 and t[i - 1:i] not in (":", "=", "<", ">", "!", "≠") and t[i + 1:i + 2] != "=":
            pos.append(i)
    if len(pos) != 1 or any(op in t for op in ("↔", "∧", "∨", "→", "∀", "∃")):
        return t
    i = pos[0]
    return f" {t[i + 1:].strip()} = {t[:i].strip()} "


def reformulate(stmt):
    from vacuity import parse  # noqa: E402
    p = parse("```lean4\n" + stmt + " := by")
    gs = groups(p["binders"])
    var_groups, hyp_groups, mapping, used = [], [], {}, set(re.findall(rf"{IDCH}+", stmt))
    fresh_v = [f for f in FRESH_VARS for _ in [0] if f + "₁" not in used]
    hk = 0
    for g in gs:
        ns, t = names_type(g)
        is_hyp = bool(ns) and all(n.startswith("h") for n in ns)
        for n in ns:
            if n == "_" or n in mapping:
                continue
            if is_hyp:
                hk += 1
                mapping[n] = f"hyp{hk}"
            else:
                mapping[n] = (fresh_v.pop(0) + "₁") if fresh_v else n + "₁"
        (hyp_groups if is_hyp else var_groups).append(g)
    name = re.match(r"\s*(?:theorem|lemma)\s+(\S+)", stmt).group(1)
    b1 = " ".join(rename(g, mapping) for g in var_groups + hyp_groups[::-1])
    c1 = rename(p["concl"], mapping)
    r1 = f"theorem {name} {b1} : {c1}"

    def flip_group(g):
        ns, t = names_type(g)
        return g if not ns else g[0] + " ".join(ns) + " :" + flip_eq(t) + g[-1]
    b2 = " ".join(flip_group(rename(g, mapping)) for g in var_groups + hyp_groups[::-1])
    r2 = f"theorem {name} {b2} : {flip_eq(c1).strip()}"
    return r1, r2


def build():
    b = pd.read_parquet(RUN / "data" / "statements" / "bench_minif2f.parquet")
    rows = []
    for r in b.itertuples():
        try:
            r1, r2 = reformulate(r.stmt)
        except Exception as e:  # noqa: BLE001
            r1 = r2 = None
            print("fail", r.id, repr(e)[:100])
        rows.append(dict(id=r.id, orig=r.stmt, R1=r1, R2=r2 if r2 != r1 else None))
    d = pd.DataFrame(rows)
    d.to_parquet(RUN / "data" / "reforms.parquet")
    print(len(d), "R1", d.R1.notna().sum(), "R2 distinct from R1", d.R2.notna().sum())


REFORM_PORTFOLIO = ("first\n    | (apply h <;> (first | assumption | (symm; assumption) | norm_num | linarith | simp_all))\n"
                    "    | (symm; apply h <;> (first | assumption | (symm; assumption) | norm_num | linarith | simp_all))\n"
                    "    | (simp_all; done)\n    | aesop")


def certify(workers):
    import certify as C
    C.PORTFOLIO = REFORM_PORTFOLIO
    tc = os.environ.get("VAC_TOOLCHAIN", "v49")
    d = pd.read_parquet(RUN / "data" / "reforms.parquet")
    items = []
    for r in d.itertuples():
        for k in ("R1", "R2"):
            s = getattr(r, k)
            if s:
                items.append((f"{r.id}|{k}", r.orig, s, "both"))
    C.run(items, RUN / "data" / "certify" / f"reforms_{tc}.jsonl", workers, tc)


if __name__ == "__main__":
    sys.path.insert(0, str(RUN.parent / "formal-math-selfplay-vacuity-drift" / "code"))
    if sys.argv[1] == "build":
        build()
    else:
        certify(int(sys.argv[2]))
