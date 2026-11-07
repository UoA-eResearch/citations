"""Audit of the parsed conjectures contradicted by their own data (G4; rewritten in D2 after the independent review's
finding 3). Each contradicted line is put in one class, tested in this order:

  stated_range_too_early   a "for n > k" start was applied, and the relation holds on the data from a start up to 10
                           indices later (with >= 3 data terms checked): false as written, by a boundary slip
  holds_from_later_index   no start was stated, and the relation holds from a start up to 10 indices later
  gf_offset_slip           a g.f. whose expansion matches the data when shifted by 1-3 places
  parity_or_residue        the line mentions a parity or residue condition the parser ignores
  no_simple_fix            none of the above: contradicted as written with no mechanical explanation; listed by
                           A-number (public facts, useful to editors) in contradicted_no_simple_fix.csv

It also counts how many of the first draft's contradicted lines stop being contradicted under the D2 parser
(vanishing leading polynomial, a(n+k) start), using data/interim/conjectures_v1.parquet. Line text is not written out.
"""
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import parse as P  # noqa: E402

TAB, INT = RUN / "results" / "tables", RUN / "data" / "interim"
PARITY = re.compile(r"\bn (is )?(even|odd)\b|\bfor (even|odd) n\b|\bn ?== ?\d|mod \d", re.I)


def later_start(p, terms, off, s0):
    for s in range(s0 + 1, s0 + 11):
        ok, _, _, chk = P.run_rec(p, terms, off, len(terms), start_override=s)
        if ok and chk >= 3:
            return s - s0
    return None


def gf_shift(p, terms, off):
    num = [Fraction(x) for x in p["num"]]
    den = [Fraction(x) for x in p["den"]]
    s = []
    for j in range(len(terms) + abs(off) + 10):
        v = num[j] if j < len(num) else Fraction(0)
        for i in range(1, min(j, len(den) - 1) + 1):
            v -= den[i] * s[j - i]
        s.append(v / den[0])
    T = [Fraction(t) for t in terms]
    for base in (max(off, 0), 0):
        for k in (1, -1, 2, -2, 3, -3):
            a = base + k
            if a >= 0 and a + len(T) <= len(s) and s[a:a + len(T)] == T:
                return k
    return None


def main():
    C = pd.read_parquet(INT / "conjectures.parquet")
    bad = C[(C.status == "parsed") & (C.data_status == "contradicted")]
    rows = []
    for r in bad.itertuples():
        e = P.read_entry(P.SEQ / r.anum[:4] / f"{r.anum}.seq")
        terms, off, p = e["terms"], int(r.offset), json.loads(r.pred)
        text = e["F"][int(r.line_no)] if int(r.line_no) < len(e["F"]) else ""
        kind, shift = None, None
        if r.cls != "G":
            order = max([k for k, _ in p["lags"]], default=0)
            s0 = max(p["start"] if p["start"] is not None else off + order, off + order)
            shift = later_start(p, terms, off, s0)
            if shift is not None:
                kind = "stated_range_too_early" if p["start"] is not None else "holds_from_later_index"
        else:
            shift = gf_shift(p, terms, off)
            if shift is not None:
                kind = "gf_offset_slip"
        if kind is None:
            kind = "parity_or_residue" if PARITY.search(text) else "no_simple_fix"
        rows.append({"anum": r.anum, "line_no": int(r.line_no), "cls": r.cls, "kind": kind, "shift": shift,
                     "first_mismatch": r.first_mismatch, "nterms": int(r.nterms), "in_block": bool(r.in_block),
                     "flagged_wrong": bool(r.flagged_wrong)})
    D = pd.DataFrame(rows)
    out = {"contradicted_lines": int(len(D)),
           "by_kind": D.kind.value_counts().to_dict(),
           "by_kind_and_class": {k: g.cls.value_counts().to_dict() for k, g in D.groupby("kind")},
           "stated_range_too_early_in_block": int(D[D.kind == "stated_range_too_early"].in_block.sum()),
           "stated_range_shift_median": float(D[D.kind == "stated_range_too_early"]["shift"].median()) if (D.kind == "stated_range_too_early").any() else None,
           "flagged_wrong": int(D.flagged_wrong.sum())}
    v1p = INT / "conjectures_v1.parquet"
    if v1p.exists():
        V1 = pd.read_parquet(v1p)
        v1bad = V1[(V1.status == "parsed") & (V1.data_ok == False)][["anum", "line_no"]]   # noqa: E712
        m = v1bad.merge(C[["anum", "line_no", "cls", "data_status"]], on=["anum", "line_no"], how="left")
        out["first_draft_contradicted"] = int(len(v1bad))
        out["first_draft_contradicted_now"] = m.data_status.fillna("not parsed").value_counts().to_dict()
    nf = D[D.kind == "no_simple_fix"].drop(columns=["kind", "shift"])
    nf.to_csv(TAB / "contradicted_no_simple_fix.csv", index=False)
    out["no_simple_fix_listed_in"] = "results/tables/contradicted_no_simple_fix.csv"
    (TAB / "contradicted_audit.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
