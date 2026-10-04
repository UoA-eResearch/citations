"""Validation on hand-written controls (plan.md section 6): 20 vacuous statements (inconsistent hypotheses) and 20
satisfiable ones, in STP prompt format with a working proof. Criteria: >= 18/20 vacuous certified, 0/20 satisfiable
certified, split check passes on all 40. Writes results/tables/validation_controls.csv."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lean_repl import Repl  # noqa: E402
from vacuity import check_row  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
HDR = "Complete the following Lean 4 code:\n\n```lean4\nimport Mathlib\nimport Aesop\nset_option maxHeartbeats 0\nopen BigOperators Real Nat Topology Rat\n\n"
VAC = [
    ("(n : ℕ) (h : n < 0) : n = 5", "omega"),
    ("(x : ℝ) (h1 : x > 5) (h2 : x < 3) : x = 0", "linarith"),
    ("(n : ℕ) (h : [1, 2, 3].count n = 2) (hn : n < 5) : n = 7", "revert h\n  revert hn\n  revert n\n  decide"),
    ("(a b : ℤ) (h1 : a + b = 3) (h2 : a + b = 4) : a * b = 100", "omega"),
    ("(x : ℝ) (h : x ^ 2 < 0) : x = 1", "nlinarith [sq_nonneg x]"),
    ("(n : ℕ) (h : n % 2 = 3) : n = 1", "omega"),
    ("(f : ℕ → ℕ) (h : ∀ x, f x = f x + 1) : f 0 = 7", "have := h 0\n  omega"),
    ("(x : ℝ) (h1 : 0 < x) (h2 : x ≤ -1) : Real.log x = 2", "linarith"),
    ("(n : ℕ) (h1 : 2 ≤ n) (h2 : n ≤ 1) : n ! = 3", "omega"),
    ("(p : ℕ) (hp : p.Prime) (h : p = 4) : p = 2", "subst h\n  norm_num at hp"),
    ("(a : ℤ) (h : a ^ 2 = -1) : a = 0", "nlinarith [sq_nonneg a]"),
    ("{x y : ℝ} (h1 : x + y = 2) (h2 : x + y = 5) : x = y", "linarith"),
    ("(n : ℕ) (h : n - 3 = 5) (h2 : n < 4) : n = 10", "omega"),
    ("(S : Finset ℕ) (h : S.card = 3) (h2 : S = ∅) : 1 = 2", "subst h2\n  simp at h"),
    ("(x : ℝ) (h : |x| < 0) : x = 3", "have := abs_nonneg x\n  linarith"),
    ("(a b : ℕ) (h1 : a < b) (h2 : b < a) : a + b = 9", "omega"),
    ("(k : ℕ) (h : 2 * k = 7) : k = 3", "omega"),
    ("(x : ℝ) (hx : Real.sqrt x < 0) : x = 0", "have := Real.sqrt_nonneg x\n  linarith"),
    ("(n : ℤ) (h1 : n > 10) (h2 : n * n < 50) : n = 0", "nlinarith"),
    ("(m : ℕ) [Fact (1 < 2)] (h : (m : ℤ) < 0) : m = 2", "omega"),
]
SAT = [
    ("(n : ℕ) (h : n = 3) : n + 1 = 4", "omega"),
    ("(x : ℝ) (h : 2 * x = 6) : x = 3", "linarith"),
    ("(a b : ℤ) (h1 : a + b = 5) (h2 : a - b = 1) : a = 3", "omega"),
    ("(x : ℝ) (hx : 0 < x) : 0 < x ^ 2", "positivity"),
    ("(n : ℕ) (h : n % 2 = 1) : n ≠ 0", "omega"),
    ("{f : ℕ → ℕ} (h : ∀ x, f x = 2 * x) : f 3 = 6", "rw [h]"),
    ("(x : ℝ) (h1 : 1 < x) : 0 < Real.log x", "exact Real.log_pos h1"),
    ("(n : ℕ) (h : n = 3) : n ! = 6", "subst h\n  rfl"),
    ("(p : ℕ) (hp : p.Prime) (h : p = 2) : p % 2 = 0", "subst h\n  norm_num"),
    ("(a : ℤ) (h : a ^ 2 = 4) (ha : 0 < a) : a = 2", "nlinarith"),
    ("(x y : ℝ) (h1 : x + y = 4) (h2 : x - y = 2) : x = 3", "linarith"),
    ("(n : ℕ) (h : n - 3 = 5) : n = 8", "omega"),
    ("(S : Finset ℕ) (h : S = {1, 2}) : S.card = 2", "subst h\n  rfl"),
    ("(x : ℝ) (h : |x| = 2) (hx : 0 < x) : x = 2", "rw [abs_of_pos hx] at h\n  exact h"),
    ("(a b : ℕ) (h1 : a < b) : a + 1 ≤ b", "omega"),
    ("(k : ℕ) (h : 2 * k = 8) : k = 4", "omega"),
    (": (2 : ℕ) + 2 = 4", "norm_num"),
    ("(n : ℤ) (h1 : n > 1) (h2 : n * n < 10) : n ≤ 3", "nlinarith"),
    ("(m : ℕ) [Fact (1 < 2)] (h : (m : ℤ) = 2) : m = 2", "omega"),
    ("(n : ℕ) (h : [1, 2, 3].count n = 1) (hn : n < 5) : n ≤ 3", "revert h\n  revert hn\n  revert n\n  decide"),
]


def main():
    repl = Repl()
    rows = []
    for kind, items in (("vacuous", VAC), ("satisfiable", SAT)):
        for i, (stmt, proof) in enumerate(items):
            prompt = HDR + f"theorem control_{kind}_{i} {stmt} := by"
            o = check_row(repl, prompt, "\n  " + proof, trivial=True)
            rows.append(dict(kind=kind, i=i, stmt=stmt, **{k: o.get(k) for k in ("parsed", "reverify", "split_ok", "swap", "auto", "vacuous", "trivial", "reverify_errors", "split_errors")}))
            print(kind, i, {k: o.get(k) for k in ("reverify", "split_ok", "swap", "auto", "vacuous", "trivial")}, o.get("reverify_errors") or o.get("split_errors") or "")
    repl.kill()
    d = pd.DataFrame(rows)
    d.to_csv(RUN / "results" / "tables" / "validation_controls.csv", index=False)
    v, s = d[d.kind == "vacuous"], d[d.kind == "satisfiable"]
    print("vacuous certified", int(v.vacuous.fillna(False).sum()), "/ 20 | satisfiable certified", int(s.vacuous.fillna(False).sum()),
          "/ 20 | split ok", int(d.split_ok.fillna(False).sum()), "/ 40 | reverify ok", int(d.reverify.fillna(False).sum()), "/ 40")


if __name__ == "__main__":
    main()
