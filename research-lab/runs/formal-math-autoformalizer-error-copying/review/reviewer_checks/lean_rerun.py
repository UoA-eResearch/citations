"""Re-run a few equivalence checks in Lean (v49) independently: (1) Herald's division-chain form vs D on
induction_sum_1oktkp1; (2) Kimina's 8.3.6a output vs D'; (3) a ZMOD-vs-MOD 'other' on Ireland-Rosen 3.10;
(4) asymmetry probe: D vs a trivially reworded D with the twin's larger numbers (amc12a_2021_p25)."""
import json, sys, time
sys.path.insert(0, "code")
import lean_check as L
fz = {json.loads(l)["item"]: json.loads(l) for l in open("results/catalogue/frozen.jsonl")}
r = L.Repl()
def eq(a, b, oa, ob, label):
    t0 = time.time()
    ab = L.implies(r, a, b, oa, ob); ba = L.implies(r, b, a, ob, oa)
    print(f"{label}: A->B={ab} B->A={ba}  ({time.time()-t0:.1f}s)", flush=True)
MF = L.MINIF2F_OPENS
it = fz["minif2f/induction_sum_1oktkp1"]
oD = L.opens_of(it["D_header"])
print("elab D:", L.elaborates(r, it["D"], oD))
hera = "open BigOperators\nopen Real Nat Topology\ntheorem X (n : ℕ) : ∑ k in Finset.range n, (1 : ℝ) / (k + 1) / (k + 2) = n / (n + 1) := by sorry"
print("elab herald-form:", L.elaborates(r, hera, oD))
eq(hera, it["D"], oD, oD, "induction_sum_1oktkp1: herald 1/(k+1)/(k+2) vs D")
hera2 = "open BigOperators\nopen Real Nat Topology\ntheorem X (n : ℕ) : ∑ k in Finset.range n, (1 : ℝ) / ((k + 1) * (k + 2)) = n / (n + 1) := by sorry"
eq(hera2, it["D"], oD, oD, "induction_sum_1oktkp1: herald product form vs D (control)")
it = fz["proofnet/Dummit-Foote|exercise_8_3_6a"]; oD = L.opens_of(it["D_header"])
kim = "open Fintype Subgroup Set Polynomial Ideal\nopen scoped BigOperators\ntheorem X {R : Type} [Ring R] (hR : R = (GaussianInt ⧸ span ({⟨0, 1⟩} : Set GaussianInt))) : IsField R ∧ ∃ finR : Fintype R, @card R finR = 5 := by sorry"
eq(kim, it["D_twin"], oD, oD, "8.3.6a twin: kimina ⟨0,1⟩ output vs D'")
kim2 = kim.replace("⟨0, 1⟩", "⟨2, 1⟩")
eq(kim2, it["D_twin"], oD, oD, "8.3.6a twin: a ⟨2,1⟩ (correct generator) output vs D'")
eq(kim2, it["C_twin"], oD, L.opens_of(it["C_header"]), "8.3.6a twin: ⟨2,1⟩ output vs C'")
it = fz["proofnet/Ireland-Rosen|exercise_3_10"]; oD = L.opens_of(it["D_header"])
zm = "open Bool Subtype\nopen Nat\ntheorem X {n : ℕ} (hn : ¬ n.Prime) : n ≠ 4 → (n - 1)! ≡ 0 [ZMOD n] := by sorry"
print("elab zmod-form:", L.elaborates(r, zm, oD))
eq(zm, it["D"], oD, oD, "Ireland-Rosen 3.10: ZMOD form vs D")
it = fz["minif2f/amc12a_2021_p25"]; oD = L.opens_of(it["D_header"])
for cond, D in (("O", it["D"]), ("T", it["D_twin"])):
    rew = D.replace("(List.sum (Nat.digits 10 N))", "(Nat.digits 10 N).sum")
    eq(rew, D, oD, oD, f"amc12a_2021_p25 {cond}: reworded digit-sum vs D")
r.kill()
