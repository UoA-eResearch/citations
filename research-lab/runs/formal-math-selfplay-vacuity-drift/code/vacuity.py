"""Per-row vacuity pipeline (plan.md section 3): parse, re-verify, split check, goal swap (a), automation (b), and
optional triviality (c). `check_row(repl, prompt, target, trivial=False)` returns a flat dict of outcomes."""
import re

from lean_repl import axioms, errors, uses_sorry

ALLOWED = {"propext", "Classical.choice", "Quot.sound"}
AUTO = ["omega", "linarith", "norm_num at *", "simp_all", "nlinarith", "aesop", "decide"]
TRIV = "first\n  | (norm_num; done)\n  | (simp; done)\n  | omega\n  | linarith\n  | nlinarith\n  | positivity"
OPEN, CLOSE = "([{⦃⟨", ")]}⦄⟩"
DECL = re.compile(r"(?m)^(theorem|lemma)\s+([^\s(\[{⦃:]+)")


def mask_comments(s):
    """Replace comment text with spaces (same length) so bracket scanning ignores it."""
    out, i, n = list(s), 0, len(s)
    while i < n:
        if s.startswith("--", i):
            j = s.find("\n", i)
            j = n if j < 0 else j
            out[i:j] = " " * (j - i)
            i = j
        elif s.startswith("/-", i):
            j = s.find("-/", i + 2)
            j = n if j < 0 else j + 2
            out[i:j] = [c if c == "\n" else " " for c in s[i:j]]
            i = j
        else:
            i += 1
    return "".join(out)


def parse(prompt):
    """Returns dict(code, imports, preamble, name, binders, concl, stmt_start) or raises ValueError."""
    code = prompt.split("```lean4\n", 1)[1]
    imports = re.findall(r"(?m)^import\s+(\S+)\s*$", code)
    body = re.sub(r"(?m)^import\s+\S+\s*\n", "", code)
    ms = list(DECL.finditer(body))
    if not ms:
        raise ValueError("no theorem")
    m = ms[-1]
    rest = body[m.end():]
    masked = mask_comments(rest)
    end = masked.rstrip().rfind(":=")
    if end < 0:
        raise ValueError("no :=")
    depth, colon = 0, None
    for i, ch in enumerate(masked[:end]):
        if ch in OPEN:
            depth += 1
        elif ch in CLOSE:
            depth -= 1
        elif ch == ":" and depth == 0 and masked[i + 1:i + 2] != "=" and masked[i - 1:i] != ":" and masked[i + 1:i + 2] != ":":
            colon = i
            break
    if colon is None:
        raise ValueError("no top-level colon")
    return dict(body=body, imports=imports, preamble=body[:m.start()], name=m.group(2), decl_start=m.start(),
                name_end=m.end(), binders=rest[:colon].strip(), concl=rest[colon + 1:end].strip())


def cert_ok(r, name):
    if "timeout" in r or "dead" in r or errors(r) or uses_sorry(r):
        return False, None
    ax = axioms(r, name)
    return (ax is not None and set(ax) <= ALLOWED), ax


def check_row(repl, prompt, target, trivial=False, t_long=100, t_short=30):
    out = dict(parsed=False)
    try:
        p = parse(prompt)
    except Exception as e:  # noqa: BLE001
        out["parse_error"] = str(e)[:200]
        return out
    out["parsed"] = True
    if any(not (i == "Aesop" or i == "Mathlib" or i.startswith("Mathlib.")) for i in p["imports"]):  # env 0 imports all of Mathlib
        out["foreign_imports"] = True
        return out
    pre, B, C = p["preamble"], p["binders"], p["concl"]
    orig = "orig_thm"
    # 1) re-verify (prompt text with only the name replaced) + split check in the same REPL session
    body = p["body"]
    orig_cmd = body[:p["decl_start"]] + body[p["decl_start"]:p["name_end"]].rsplit(p["name"], 1)[0] + orig + body[p["name_end"]:] + target + f"\n\n#print axioms {orig}"
    repl.ensure(2)
    r = repl.run(orig_cmd, timeout=t_long)
    ok, ax = cert_ok(r, orig)
    out.update(reverify=ok, reverify_timeout="timeout" in r, reverify_s=r.get("seconds"), orig_axioms=ax)
    if not ok:
        out["reverify_errors"] = [m["data"][:300] for m in errors(r)][:2]
        return out
    split = f"example : {'∀ ' + B + ', ' if B else ''}{C} := {orig}"
    r2 = repl.run(split, env=r["env"], timeout=t_short)
    out["split_ok"] = not ("timeout" in r2 or "dead" in r2 or errors(r2))
    if not out["split_ok"]:
        out["split_errors"] = [m["data"][:300] for m in errors(r2)][:2]
        return out
    # 2a) goal swap
    v = "vac_thm"
    r = repl.run(f"{pre}theorem {v} {B} : False := by{target}\n\n#print axioms {v}", timeout=t_long)
    ok, ax = cert_ok(r, v)
    out.update(swap=ok, swap_axioms=ax if ok else None, swap_timeout="timeout" in r, swap_s=r.get("seconds"))
    # 2b) automation portfolio, stop at first success
    out["auto"], out["auto_s"] = None, 0.0
    for tac in AUTO:
        if tac == "decide":
            if not B:
                continue
            stmt = f"theorem {v} : ∀ {B}, False := by\n  decide"
        else:
            stmt = f"theorem {v} {B} : False := by\n  {tac}"
        r = repl.run(f"{pre}set_option maxHeartbeats 100000 in\n{stmt}\n\n#print axioms {v}", timeout=t_short)
        out["auto_s"] += r.get("seconds", 0.0)
        ok, ax = cert_ok(r, v)
        if ok:
            out["auto"], out["auto_axioms"] = tac, ax
            break
    out["vacuous"] = bool(out["swap"] or out["auto"])
    # 3) triviality (conclusion with hypotheses cleared)
    if trivial:
        t = "triv_thm"
        r = repl.run(f"{pre}set_option maxHeartbeats 100000 in\ntheorem {t} {B} : {C} := by\n  intros\n  clear * -\n  {TRIV}\n\n#print axioms {t}", timeout=t_short)
        out["trivial"], _ = cert_ok(r, t)
        out["trivial_s"] = r.get("seconds")
    return out
