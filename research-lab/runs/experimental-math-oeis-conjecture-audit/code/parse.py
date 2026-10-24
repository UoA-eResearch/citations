"""Parse conjectured recurrences and generating functions from OEIS %F lines (plan sections 1-2).

  parse.py run   -> data/interim/conjectures.parquet: one row per candidate line with class (C, G, D or none),
                    parse status, data-check status, and a JSON-encoded predictor
  parse.py test  unit checks on hand-made lines

Predictors:
  rec  {"lags": [[k, [poly coeffs in n, low->high]], ...], "lead": [poly coeffs], "const": [poly coeffs], "start": n0}
       meaning lead(n)*a(n) = sum_k c_k(n)*a(n-k) + const(n) for n >= n0
  gf   {"num": [...], "den": [...]} integer coefficients, low -> high power of x, aligned to the entry's offset
"""
import json
import re
import signal
import sys
from fractions import Fraction
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
SEQ = RUN / "data" / "raw" / "oeisdata" / "seq"
INT = RUN / "data" / "interim"

CAND = re.compile(r"\b(conjecture[ds]?|empirical(ly)?)\b", re.I)
SIG = re.compile(r"\s+-\s+_[^_]+_.*$")          # trailing " - _Name_, date"


class Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise Timeout()


def read_entry(path):
    e = {"F": [], "terms": []}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if len(line) < 3 or line[0] != "%":
            continue
        tag, rest = line[1], line[3:]
        body = rest.split(" ", 1)[1] if " " in rest else ""
        if tag in "STU":
            e["terms"] += [int(x) for x in body.replace(" ", "").split(",") if x.strip().lstrip("-").isdigit()]
        elif tag == "O":
            e["offset"] = int(body.split(",")[0])
        elif tag == "F":
            e["F"].append(body)
        elif tag == "K":
            e["K"] = body
        elif tag == "N":
            e["N"] = body
    return e


def poly_coeffs(expr, n):
    import sympy as sp
    p = sp.Poly(sp.nsimplify(sp.expand(expr)), n)
    c = p.all_coeffs()[::-1]
    return [str(sp.Rational(x)) for x in c]


def parse_gf(text):
    import sympy as sp
    m = re.search(r"g\.\s*f\.?\s*[:=]?\s*(?:A\(x\)\s*=\s*)?(.+)", text, re.I)
    if not m:
        return None
    s = m.group(1).strip().rstrip(".").split(";")[0]
    s = s.replace("^", "**").replace("[", "(").replace("]", ")")
    if re.search(r"[a-wyzA-Z]", re.sub(r"\bx\b", "", s)):
        return None
    x = sp.Symbol("x")
    e = sp.sympify(s, locals={"x": x})
    num, den = sp.fraction(sp.together(e))
    pn, pd = sp.Poly(sp.expand(num), x), sp.Poly(sp.expand(den), x)
    cn, cd = pn.all_coeffs()[::-1], pd.all_coeffs()[::-1]
    if not all(sp.Rational(c).q == 1 for c in cn + cd) or cd[0] == 0:
        # allow a common rational factor
        L = sp.ilcm(*[sp.Rational(c).q for c in cn + cd])
        cn, cd = [c * L for c in cn], [c * L for c in cd]
        if cd[0] == 0:
            return None
    return {"num": [str(sp.Rational(c)) for c in cn], "den": [str(sp.Rational(c)) for c in cd]}


A_TERM = re.compile(r"a\(\s*n\s*([+-]\s*\d+)?\s*\)")


def parse_rec(text):
    import sympy as sp
    t = text.replace("^", "**").replace("[", "(").replace("]", ")")
    t = re.sub(r"d-finite with recurrence[:]?", "", t, flags=re.I)
    m0 = re.search(r"for\s+n\s*(>=|>|≥)\s*(-?\d+)", t)
    start = None
    if m0:
        start = int(m0.group(2)) + (1 if m0.group(1) == ">" else 0)
    t = re.split(r",?\s*(for|with|where|if|when)\b", t, flags=re.I)[0]
    t = t.strip().rstrip(".;,: ").strip()
    if "=" not in t or "a(n" not in t.replace(" ", ""):
        return None
    shifts = [int(s.replace(" ", "")) if s else 0 for s in A_TERM.findall(t)]
    if not shifts:
        return None
    top = max(shifts)
    n = sp.Symbol("n")
    names = {}

    def rep(mm):
        k = int(mm.group(1).replace(" ", "")) if mm.group(1) else 0
        lag = top - k
        names[lag] = sp.Symbol(f"A{lag}")
        return f"A{lag}"
    t2 = A_TERM.sub(rep, t)
    if re.search(r"[a-mo-zB-Z]", re.sub(r"A\d+", "", t2)):
        return None
    lhs, rhs = t2.split("=", 1)
    if "=" in rhs:
        return None
    rel = sp.expand(sp.sympify(lhs, locals={"n": n, **{str(v): v for v in names.values()}})
                    - sp.sympify(rhs, locals={"n": n, **{str(v): v for v in names.values()}}))
    rel = rel.subs(n, n - top)       # index the relation so that A0 is a(n)
    syms = [names[k] for k in sorted(names)]
    lin = sp.Poly(rel, *syms)
    if lin.total_degree() > 1:
        return None
    lead = sp.expand(rel.coeff(names[0])) if 0 in names else 0
    if lead == 0:
        return None
    lags, const = [], sp.expand(rel.subs({s: 0 for s in syms}))
    for k in sorted(names):
        if k == 0:
            continue
        lags.append([k, poly_coeffs(-rel.coeff(names[k]), n)])
    cls = "C" if all(len(c) == 1 for _, c in lags) and len(poly_coeffs(lead, n)) == 1 else "D"
    return cls, {"lags": lags, "lead": poly_coeffs(lead, n), "const": poly_coeffs(-const, n), "start": start}


def evalp(c, n):
    s = Fraction(0)
    for i, x in enumerate(c):
        s += Fraction(x) * n ** i
    return s


def run_rec(p, terms, offset, upto):
    """Return (data_ok, predicted list from offset to offset+upto-1, first data mismatch index or None)."""
    order = max([k for k, _ in p["lags"]], default=0)
    start = p["start"] if p["start"] is not None else offset + order
    start = max(start, offset + order)
    a = {offset + i: Fraction(v) for i, v in enumerate(terms)}
    pred = dict(a)
    mism = None
    for nn in range(start, offset + upto):
        lead = evalp(p["lead"], nn)
        if lead == 0:
            return False, None, nn
        if any(nn - k not in pred for k, _ in p["lags"]):
            return False, None, nn
        v = (sum(evalp(c, nn) * pred[nn - k] for k, c in p["lags"]) + evalp(p["const"], nn)) / lead
        if nn in a:
            if v != a[nn] and mism is None:
                mism = nn
        else:
            if v.denominator != 1:
                pred[nn] = v
                break
            pred[nn] = v
    out = [pred.get(offset + i) for i in range(upto)]
    return mism is None, out, mism


def run_gf(p, terms, offset, upto):
    num = [Fraction(x) for x in p["num"]]
    den = [Fraction(x) for x in p["den"]]
    # power series coefficients s_j of num/den, j = 0..
    s = []
    for j in range(upto + offset + 5):
        v = num[j] if j < len(num) else Fraction(0)
        for i in range(1, min(j, len(den) - 1) + 1):
            v -= den[i] * s[j - i]
        s.append(v / den[0])
    # align: a(offset + i) = s[offset + i] if the g.f. is in x^n convention
    seq = s[offset:offset + upto] if offset >= 0 else s[:upto]
    mism = next((offset + i for i, v in enumerate(terms) if i < len(seq) and seq[i] != v), None)
    if mism is not None:
        # try the other common convention: series starts at x^0 for a(offset)
        seq2 = s[:upto]
        mism2 = next((offset + i for i, v in enumerate(terms) if seq2[i] != v), None)
        if mism2 is None:
            return True, seq2, None
    return mism is None, seq, mism


def classify(line):
    body = SIG.sub("", line)
    body = re.sub(r"\((conjectured|empirical|conjecture)\)", " CONJ ", body, flags=re.I)
    m = CAND.search(body) or re.search(r"CONJ", body)
    txt = body[m.end():].lstrip(" :.,") if m else body
    if m and not re.search(r"=|g\.\s*f\.", txt, re.I):
        txt = body[:m.start()]                      # formula written before the keyword ("... (conjectured)")
    txt = txt.replace("CONJ", "")
    if re.search(r"g\.\s*f\.", txt, re.I):
        g = parse_gf(txt)
        return ("G", g) if g else (None, None)
    r = parse_rec(txt)
    return r if r else (None, None)


def _dir(d):
    signal.signal(signal.SIGALRM, _alarm)
    rows = []
    for f in sorted(Path(d).glob("A*.seq")):
        e = read_entry(f)
        inblock = False
        for li, line in enumerate(e["F"]):
            starts = bool(CAND.search(line)) and "(Start)" in line
            member = inblock and not starts
            if "(End)" in line:
                inblock = False
            if starts:
                inblock = True
                continue                                 # the block header itself holds no formula
            if not (CAND.search(line) or member):
                continue
            row = {"anum": f.stem, "line_no": li, "offset": e.get("offset", 0), "nterms": len(e["terms"]),
                   "keywords": e.get("K", ""), "cls": None, "status": "not_parsed", "data_ok": None, "first_mismatch": None,
                   "pred": None, "in_block": member}
            signal.alarm(5)
            try:
                cls, p = classify(line)
                if cls:
                    upto = len(e["terms"])
                    ok, _, mism = (run_gf if cls == "G" else run_rec)(p, e["terms"], row["offset"], upto)
                    row.update({"cls": cls, "status": "parsed", "data_ok": bool(ok), "first_mismatch": mism, "pred": json.dumps(p)})
            except Timeout:
                row["status"] = "timeout"
            except Exception:
                row["status"] = "parse_error"
            finally:
                signal.alarm(0)
            rows.append(row)
    return rows


def run():
    import os
    import pandas as pd
    from concurrent.futures import ProcessPoolExecutor
    dirs = sorted(str(d) for d in SEQ.glob("A*") if d.is_dir())
    rows = []
    with ProcessPoolExecutor(int(os.environ.get("WORKERS", "16"))) as ex:
        for k, r in enumerate(ex.map(_dir, dirs), 1):
            rows += r
            if k % 50 == 0:
                print(k, "of", len(dirs), "dirs", len(rows), "candidate lines", flush=True)
    d = pd.DataFrame(rows)
    d.to_parquet(INT / "conjectures.parquet", index=False)
    print(d.groupby(["status", "cls"], dropna=False).size().to_string())
    print("data_ok", d.data_ok.value_counts(dropna=False).to_dict())


def test():
    fib = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
    c, p = classify("Conjecture: a(n) = a(n-1) + a(n-2) for n > 1. - _Somebody_, Jan 01 2020")
    assert c == "C" and run_rec(p, fib, 0, 15)[0], p
    assert run_rec(p, fib, 0, 15)[1][14] == 377
    c, p = classify("Empirical G.f.: x/(1-x-x^2). - _Somebody_, Jan 01 2020")
    assert c == "G" and run_gf(p, fib, 0, 15)[0] and run_gf(p, fib, 0, 15)[1][13] == 233, p
    cat = [1, 1, 2, 5, 14, 42, 132, 429, 1430]
    c, p = classify("Conjecture: D-finite with recurrence (n+1)*a(n) +2*(-2*n+1)*a(n-1)=0. - _R. J. Mathar_, Jan 01 2020")
    assert c == "D" and run_rec(p, cat, 0, 12)[0] and run_rec(p, cat, 0, 12)[1][9] == 4862, (c, p)
    c, p = classify("Conjecture: a(n) = 2*a(n-1) + 1 for n >= 1.")
    ok, out, _ = run_rec(p, [0, 1, 3, 7, 15], 0, 8)
    assert ok and out[7] == 127, (p, out)
    c, p = classify("Conjecture: a(n) = 3*a(n-1) for n > 0.")
    ok, out, mism = run_rec(p, [1, 3, 9, 28], 0, 4)
    assert not ok and mism == 3
    print("parse tests pass")


if __name__ == "__main__":
    {"run": run, "test": test}[sys.argv[1]]()
