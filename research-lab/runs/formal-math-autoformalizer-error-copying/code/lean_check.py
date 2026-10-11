"""Lean checks (plan sections 2.2, 3.1 and 5): statement parsing, elaboration and the bidirectional equivalence test.

Conventions follow ../formal-math-certified-contamination-did/code/certify.py: autoImplicit off, bare π read as
Real.pi, the same tactic portfolio and 20 s per direction, and only the standard axioms. Implementation (deviations.md
D1): each statement is elaborated as `def stmtX : Prop := ∀ binders, concl` inside its own section, with its own
`open` lines (or the item's default opens if it has none), because miniF2F and ProofNet statements rely on different
namespaces. `Type*`/`Type u` is read as `Type`, so that the two sides of an implication quantify over the same universe.
The toolchain is chosen by VAC_TOOLCHAIN (v49 or v415) before import, as in lean_repl."""
import re
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
VAC = RUN.parent / "formal-math-selfplay-vacuity-drift" / "code"
sys.path.insert(0, str(VAC))
from lean_repl import Repl, axioms, errors, uses_sorry  # noqa: E402,F401
from vacuity import mask_comments  # noqa: E402

ALLOWED = {"propext", "Classical.choice", "Quot.sound"}
PORTFOLIO = ("first\n    | (apply h <;> (first | assumption | norm_num | linarith | simp_all))\n    | (simp_all; done)\n    | aesop\n"
             "    | (simp_all <;> nlinarith [h])")
DECL = re.compile(r"(?m)^[ \t]*(?:@\[[^\]]*\]\s*)?(?:protected\s+|private\s+|nonrec\s+)?(theorem|lemma|example)\b\s*([^\s(\[{⦃:]*)")
OPEN_LINE = re.compile(r"(?m)^[ \t]*open\s+[^\n]*?(?:\s+in)?[ \t]*$")
PI = re.compile(r"(?<![\w.])π(?![\w])")
UNIV = re.compile(r"\b(Type|Sort)\s*\*|\b(Type|Sort)\s+(?:_|[uvw](?:_\d+)?|u_\d+)\b")
OPEN_BR, CLOSE_BR = "([{⦃⟨", ")]}⦄⟩"
MINIF2F_OPENS = ["open BigOperators Real Nat Topology Rat"]


class ParseError(ValueError):
    pass


def opens_of(header):
    """The `open` lines of a header or snippet, with any trailing `in` removed."""
    return [re.sub(r"\s+in\s*$", "", m.group(0).strip()) for m in OPEN_LINE.finditer(header or "")]


def parse(text):
    """Split a Lean snippet into (opens, binders, conclusion). The snippet may hold imports, opens, options and one
    theorem/lemma (the last one is used), with or without a proof; the statement ends at the first top-level `:=`."""
    body = re.sub(r"(?m)^\s*import\s+\S+\s*$", "", text)
    ms = list(DECL.finditer(body))
    if not ms:
        raise ParseError("no theorem")
    m = ms[-1]
    pre, rest = body[:m.start()], body[m.end():]
    masked = mask_comments(rest)
    depth, colon, end = 0, None, None
    for i, ch in enumerate(masked):
        if ch in OPEN_BR:
            depth += 1
        elif ch in CLOSE_BR:
            depth -= 1
        elif depth == 0 and ch == ":":
            nxt, prv = masked[i + 1:i + 2], masked[i - 1:i]
            if nxt == "=":
                if colon is not None:
                    end = i
                    break
            elif nxt != ":" and prv != ":" and colon is None:
                colon = i
    if colon is None:
        raise ParseError("no top-level colon")
    if end is None:  # no proof given
        end = len(masked)
    binders, concl = rest[:colon].strip(), mask_comments(rest[colon + 1:end]).strip()
    if not concl:
        raise ParseError("empty conclusion")
    return opens_of(pre), binders, concl


def prop(binders, concl):
    b, c = UNIV.sub("Type", PI.sub("Real.pi", binders)), UNIV.sub("Type", PI.sub("Real.pi", concl))
    return f"∀ {b}, {c}" if b else c


def wrap(name, text, default_opens):
    """`def name : Prop := ...` in its own section; raises ParseError if the snippet has no statement."""
    opens, b, c = parse(text)
    lines = "\n".join(opens or default_opens)
    return f"section\nset_option autoImplicit false\n{lines}\ndef {name} : Prop := {prop(b, c)}\nend\n"


def elaborates(repl, text, default_opens, timeout=60):
    try:
        cmd = wrap("stmtA", text, default_opens)
    except ParseError:
        return False
    r = repl.run(cmd, timeout=timeout)
    return not ("timeout" in r or "dead" in r or errors(r) or uses_sorry(r))


def implies(repl, a, b, opens_a, opens_b, timeout=20):
    """True if (statement a) → (statement b) is kernel-checked by the portfolio with the standard axioms only. Both
    sides must already be known to elaborate."""
    cmd = (wrap("stmtA", a, opens_a) + wrap("stmtB", b, opens_b) +
           f"theorem chk : stmtA → stmtB := by\n  unfold stmtA stmtB\n  intro h\n  intros\n  {PORTFOLIO}\n\n#print axioms chk")
    r = repl.run(cmd, timeout=timeout)
    if "timeout" in r or "dead" in r or errors(r) or uses_sorry(r):
        return False
    ax = axioms(r, "chk")
    return ax is not None and set(ax) <= ALLOWED


def refuted(repl, text, opens, timeout=20):
    """Plan 3.1 check 5: True if the portfolio proves the negation of the closed statement."""
    cmd = (wrap("stmtA", text, opens) + "theorem chk : ¬ stmtA := by\n  unfold stmtA\n  first\n    | (push_neg; simp_all; done)"
           "\n    | (push_neg; norm_num)\n    | decide\n    | (simp_all; done)\n    | aesop\n\n#print axioms chk")
    r = repl.run(cmd, timeout=timeout)
    if "timeout" in r or "dead" in r or errors(r) or uses_sorry(r):
        return False
    ax = axioms(r, "chk")
    return ax is not None and set(ax) <= ALLOWED


def provable(repl, text, opens, timeout=20):
    """Plan 8 (truth-certified twins): True if the portfolio proves the closed statement outright."""
    cmd = (wrap("stmtA", text, opens) + "theorem chk : stmtA := by\n  unfold stmtA\n  intros\n  first\n    | (simp_all; done)"
           "\n    | (norm_num; done)\n    | decide\n    | linarith\n    | nlinarith\n    | aesop\n\n#print axioms chk")
    r = repl.run(cmd, timeout=timeout)
    if "timeout" in r or "dead" in r or errors(r) or uses_sorry(r):
        return False
    ax = axioms(r, "chk")
    return ax is not None and set(ax) <= ALLOWED
