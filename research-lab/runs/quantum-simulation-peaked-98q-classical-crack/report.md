# Can one A100 recover the hidden answers of the 98-qubit peaked circuits?

*A preregistered classical attack on BlueQubit's P11 and P12 quantum-advantage candidates, scored against the
hardware answers, which were sealed unread*

Run directory: `research-lab/runs/quantum-simulation-peaked-98q-classical-crack` · Preregistration:
[`plan.md`](plan.md) (commit ff1996a) · Every departure from it: [`deviations.md`](deviations.md) (D1–D6) ·
6 October 2026, draft for independent review

## In plain terms

A "peaked circuit" is a quantum program built so that one particular 98-bit answer comes out far more often than any
other. A quantum computer can find that answer by running the program and counting. The open question is whether an
ordinary computer can find it too: if it can, the circuit does not demonstrate an advantage for quantum computers.
In 2026 a classical method cracked a smaller, 56-qubit circuit of this kind (P9) in under an hour. Two larger
circuits, P11 and P12, were later solved by Quantinuum's Helios-1 quantum computer and remain listed as open
challenges for classical computers.

We gave the best published classical attacks a fixed budget of 72 hours on one A100 graphics card for each circuit.
Before running anything, we stored Helios-1's answers without reading them. The attack first reproduced the
published P9 solution exactly. On the larger circuits it failed. On P11 the main attack finished in 17 hours but lost
the answer along the way: its 1,000 samples were all different. Tighter settings ran out of time after absorbing only
4% of the circuit. P12 was further out of reach. When we finally opened the sealed answers, our best guesses
were 47 and 57 bits wrong out of 98, no better than chance.

So these two circuits survived this attack and this budget. That is evidence they are hard to simulate classically,
not proof: better algorithms, more hardware or more time could still succeed.

## What was done

**Circuits and answers.** The QASM files for P9 (56 qubits, 1,917 RZZ gates), P11 (98 qubits, 1,999 CZ) and P12
(98 qubits, 2,457 CZ) were downloaded from the Quantum Advantage Tracker, with their hashes recorded. The Helios-1
peak strings for P11 and P12 (tracker issues #246 and #247) were extracted by script into a sealed file. Only their
hashes were printed, and the file was read once, by `code/score.py`, after the final candidates had been committed
and pushed (commit 0bf21f0).

**Attacks**, all with the authors' own code where it exists:

- **A1, MPO middle-out cancellation with greedy unswapping.** Kremer & Dupuis (arXiv:2604.21908), code at a pinned
  commit, unchanged. It contracts both halves of the circuit into a central operator, undoes hidden qubit
  permutations, and samples from the result.
- **A2, low-bond MPS simulation with per-bit majority vote.** The same authors' distillation method.
- **A3, Heisenberg-picture propagation of each Z_i with Pauli truncation.** qiskit-addon-obp.

**Budget.** 72 A100-hours per instance, with every concurrent process charged its full wall-clock time
(conservative). The final candidate for each instance was chosen by a rule fixed before any candidate existed
(D4).

**Validation gate.** Before P11 or P12, A1 had to reproduce the published P9 answer within three times the published
runtime.

## Results

| Instance | Attack | Outcome | A100-hours |
|---|---|---|---|
| P9 (validation) | A1, cutoff 0.002 | Published peak recovered exactly; top sample frequency 0.107 | 1.7 |
| P9 (validation) | A2, χ 256 | 30 of 56 bits wrong: chance level | 1.4 |
| P9 (validation) | A3 | Pauli growth exhausted 20,000–200,000 terms within 18 of 207 depth slices | CPU only |
| P11 | A1, cutoff 0.002 | Completed in 17.0 h; operator bond peaked at 511; **all 1,000 samples distinct** (no peak) | 17.0 |
| P11 | A1, cutoff 0.001 | Stopped at the 27 h cap after absorbing 81 of 1,984 two-qubit blocks | 27.0 |
| P11 | A1, cutoff 0.0005 | Stopped at the 27 h cap after absorbing 89 of 1,984 | 27.0 |
| P12 | A1, cutoff 0.002 | Stopped at the 27 h cap after absorbing 177 of 2,433 | 27.0 |
| P12 | A2, χ 256 | Candidate from per-bit majority vote; mean margin 0.15 | 3.7 |

**Validation passed.** A1 reproduced the published P9 peak in 6,267 s, within the 8,166 s limit. A2 is at chance on
P9, so a correct answer was not expected from it on P11 or P12. A3 was infeasible and was not run on P11 or P12 (D2).

**Scoring.**

| | Final candidate | Hamming distance to the Helios-1 peak (of 98) | Preregistered rule |
|---|---|---|---|
| **P11 (primary)** | A1, cutoff 0.002 | **47** | Contradicted (≥ 5) |
| P12 (secondary) | A2, χ 256 | 57 | Contradicted (≥ 5) |

Two random 98-bit strings differ in 49 bits on average, so both candidates are at chance.

**Verdict: Refuted.** The preregistered hypothesis was that at least one open classical attack recovers P11's peak
within 72 A100-hours. It is refuted at this budget: the best candidate is 47 bits from the peak. P11 used 71.0 of its
72 A100-hours and P12 30.7.

![A1 progress: core-operator size and two-qubit blocks absorbed against wall-clock hours](results/figures/a1_progress.png)

**Why A1 fails on P11.** The figure shows the mechanism, which is the same in every run. Most of the work goes into
unswapping, which searches for the hidden permutations that let the two halves cancel. Absorption of the circuit's
two-qubit blocks then accelerates once enough structure has cancelled. On P9 that happened within 1.5 hours. On P11
at cutoff 0.002 it happened after about 15 hours, but by then truncation had discarded the peak: the final state
gave 1,000 distinct samples. At tighter cutoffs, which keep more of the operator, the unswapping phase did not get
past the first 4–5% of the circuit in 27 hours.

The structural statistics are consistent with this. P11 has fewer two-qubit gates per qubit than P9 (41 against 68),
but its two halves share far fewer qubit pairs (111 against 340), as a more thoroughly scrambled permutation would
produce (`results/tables/structure.csv`).

## Caveats

- **A bounded refutation, not a proof of hardness.** The claim is limited to these open methods on one GPU within
  72 A100-hours. More compute, larger bond dimensions, better unswapping heuristics, or attacks designed for P11 could
  succeed. No classical recovery of P11 or P12 had been reported on the tracker or arXiv as of 4 October 2026.
- **The budget forced choices.** max_bond 16,384 was not run, because the bond dimension never approached the 8,192
  cap (D3). The tighter cutoffs ran concurrently and were capped at 27 h each. A2 was run only at χ 256, and not at
  all on P11 because the budget ran out (D5).
- **The reference answer is Helios-1's.** We assume the strings recovered on the quantum hardware are the true peaks.
  If they were wrong, a correct classical answer would score badly, but our candidates would still be at chance
  relative to any fixed string.
- **Conservative accounting.** Concurrent processes shared one GPU but were each charged their full wall-clock time,
  so the effective compute was below the charged hours.

## Deviations (summary)

- **D1:** A2 run in complex128 after NaN failures; A2 at chance on P9.
- **D2:** A3 not run (infeasible on P9).
- **D3:** the first P11 run resolved no peak; tighter cutoffs replaced the planned max_bond 16,384.
- **D4:** a tie rule for candidate selection, fixed before any follow-up candidate existed.
- **D5:** the follow-up runs hit their 27 h caps, closing P11's budget.
- **D6:** final candidates committed before scoring.

The decision rule never changed.
