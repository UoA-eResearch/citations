# Deviations and implementation details

The plan (plan.md) was committed in 6bfdc63 at 2026-10-07 09:32 NZDT. Entries are timestamped with `date`.

## D1. Certification safeguards, defined before certification runs at scale (2026-10-07 09:42 NZDT)

A test on 16 retrieved pairs (benchmark × DeepSeek-Prover-V1) showed that the plan's tier logic can certify an
implication without using the hypothesis at all. If the conclusion side is provable by the portfolio on its own, then
"train ⇒ test" (or "test ⇒ train") holds for any training statement. Several "test ⇒ train" certifications for one
AM-GM item came from training statements that `aesop` proves alone. Three safeguards are therefore added
(`code/certify.py`):

1. **Self-provability.** Whenever an implication a ⇒ b is certified, b is also tried on its own with the portfolio
   (`simp_all`, `aesop`, `norm_num`, `linarith`, `nlinarith`; 20 s).
   - If b is provable alone, the implication is uninformative and does not count.
   - **L1** requires both directions to be informative.
   - **L2** requires train ⇒ test to be informative.
   - Benchmark items provable alone are reported as "automation-provable". They can be leaked only through L0.
2. **autoImplicit off.** Otherwise an undeclared variable in either statement would be auto-bound once at the outer
   level and shared between the two sides. Statements that need it are "unchecked".
3. **`π` read as `Real.pi`.** Under all of Mathlib with `open Real Nat`, a bare `π` is ambiguous. The vacuity study
   found this made 2.6% of rows fail.

Each side is first checked to elaborate on its own, so any error in the combined theorem is a failed proof.

**In the test.** Of the 16 pairs, 10 high-similarity pairs certified as non-trivial L1 equivalences; 2 were unchecked
(undeclared variables); and 3 "test ⇒ train" certifications were trivial.

## D2. Cap on numeral-only candidates, before certification (2026-10-08 12:03 NZDT)

Retrieval over the seven corpora gave 110,226 unique candidate pairs for the 488 miniF2F items. 85% of them are
numeral matches: statements with the same multiset of numerals that share half the item's identifiers. For simple
items the rule matches thousands of statements; one item matched 3,192 STP statements. Certifying them all would
take about 21 CPU-hours for miniF2F alone, almost all on unrelated pairs.

**The cap.** Numeral-only candidates are capped at 20 per benchmark item and corpus. They are ranked by the Jaccard
similarity of the identifier sets, then by corpus id, which is deterministic. L0 and MinHash candidates are not
capped.

**How many items it affects** (more than 20 numeral matches):

| Corpus | Items |
|---|---|
| Goedel-Pset | 79 |
| STP | 75 |
| SFT v2 | 73 |
| NuminaMath-LEAN | 29 |
| Lean-Workbook | 26 |
| Goedel's Lean-workbook-proofs | 8 |
| DeepSeek-Prover-V1 | 2 |

**What this may miss.** A certified equivalent that shares an item's numerals but has low character overlap and
falls outside the top 20. Such misses would understate the leak rate.

**Retrieval results seen so far:** counts only (`results/tables/retrieval_counts.csv`). STP has 174 miniF2F items
at L0, Goedel-Pset 10, NuminaMath-LEAN 5 and Goedel's Lean-workbook-proofs 1. No certification has been run except the
16-pair test in D1.

## D3. The D1 informativeness guard replaced, before any prover sampling (2026-10-08 14:36 NZDT)

**What was found.** A spot-check of certified L2 pairs (miniF2F × Goedel-Pset and × NuminaMath-LEAN) found
implications that cannot reflect the same problem. Examples:

- a training statement that 8^2012 % 10 = 2 "implies" the test statement (k² + 2^k) % 10 = 6 with k = 2008² + 2^2008;
- one closed fraction computation "implies" another.

The D1 guard missed these for two reasons:

1. It tried a *smaller* portfolio on the conclusion alone than the implication check uses, so a conclusion provable by
   `simp_all` with an extra hypothesis present looked non-trivial.
2. It failed open: a timeout counted as "not provable alone". Timeouts were frequent for about 20 minutes while two
   certification runs (44 workers) competed for 24 cores, after an interrupted restart.

The spot-checked L1 pairs were genuine: the same problem with renamed hypotheses or a reworded conclusion.

**New guard** (`code/recheck.py`). For every certified implication a ⇒ b, the *identical* command is rerun with a
replaced by `True`, with the same portfolio and a 60 s limit, on uncontended cores.

- If it succeeds, or times out, the certificate does not depend on a. The implication is not informative and does
  not count (fail-closed).
- **L1** requires both directions informative. **L2** requires train ⇒ test informative.
- The D1 flags are kept in the data but no longer used.

**Status.** No prover output has been generated beyond the D-pilot (truncation only; next entry), and no proof has
been verified. The secondary-benchmark certification is paused and will resume after the recheck.
