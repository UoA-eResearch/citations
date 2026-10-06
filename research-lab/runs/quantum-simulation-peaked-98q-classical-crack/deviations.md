# Deviations and implementation details

The plan (plan.md) was committed in ff1996a at 2026-10-04 12:32 NZDT. Entries are timestamped with `date`.

## D1. Validation results and attack A2 precision (2026-10-04 16:01 NZDT)

**A1 validation gate: passed.** The P9 reproduction with the published unswapping parameters recovered the published
P9 peak exactly, in 6,267 s (the limit was 3x 2,722 s = 8,166 s), with 1.8 GB peak GPU memory
(results/P9_A1_mb8192_c0.002_s123.json).

**A2 precision.** Run in complex64 as in the authors' notebook, distillation on P9 crashed with NaN sampling
probabilities. It is now run in complex128.

**A2 on P9 (chi 256, 1,000 samples, 4,930 s).** The voted string is 30 of 56 bits away from the published P9 peak,
which is chance level. Bit-marginal distillation does not work on these permuted (Hqap) circuits. On P11 it is
therefore run once, at chi 256, only after A1 has finished, so that it does not slow A1. It cannot outrank an A1
candidate under the plan's ordering.

## D2. Attack A3 not run: infeasible within the budget (2026-10-05 07:51 NZDT)

Heisenberg-picture back-propagation of Z_i with qiskit-addon-obp was tried on P9:

- with max_paulis 20,000 (truncation budget 0.05), each observable stopped after 16-18 of 207 depth slices;
- with max_paulis 200,000 (truncation budget 1.0), qubit 0 stopped after 18 of 207 slices, after 1,754 s.

Pauli growth through these random two-qubit unitaries is far beyond any budget available here. As plan section 3
allows, A3 is reported as not run. The test outputs are in results/P9_A3_*_subset.json.

## D3. First P11 A1 run resolves no peak; follow-up A1 runs (2026-10-05 07:51 NZDT)

**First run.** A1 on P11 with the P9 parameters (cutoff 0.002, max_bond 8192) took 61,120 s (17.0 h). The core MPO
peaked at bond dimension 511 and ended at 31. All 1,000 samples drawn from the final MPS were distinct, so the top
frequency is 0.001 (P9 reached 0.107). The run did not resolve a peak. Its candidate is recorded unscored in
results/P11_A1_mb8192_c0.002_s123.json.

**Follow-up runs** (started 2026-10-05 07:19, running concurrently on the single A100, each capped at 27 h by
`timeout`):

- P11 at cutoff 0.001;
- P11 at cutoff 0.0005;
- P12 at the P9 parameters.

**Departures from plan section 3.**

- **max_bond 16384 is not run.** The bond dimension never came near the 8,192 cap (peak 511), so the cap is not what
  limits accuracy. The SVD cutoff is.
- **Cutoff 0.0005 is added** below the planned 0.001 for the same reason.

**GPU-hour accounting (conservative).** Each concurrent process is charged its full wall-clock time as A100-hours,
although they share one GPU (peak memory under 2 GB each). On that basis P11 has used 17.0 h. Its two follow-ups can
use at most 54 h more, which stays within the 72 h budget. P12 can use at most 27 h.

## D4. Candidate selection and scoring code, written before any follow-up candidate exists (2026-10-05 09:06 NZDT)

**`code/select_candidates.py`** implements plan section 3 and fixes a tie rule that the plan left open. Candidates
are ordered:

1. by attack, A1 > A2 > A3;
2. then by the attack's confidence, highest first (A1: top-sample frequency);
3. then by the smaller SVD cutoff;
4. then by the larger max_bond.

Ties are likely: a run that resolves no peak has a top frequency of 0.001.

**Commitment.** The selected candidates and their SHA-256 hashes go to `results/final_candidates.json`, which is
committed before scoring.

**`code/score.py`** reads the sealed answers. It refuses to run unless that file is committed and unmodified, and it
refuses a second run, so the answers are read once. It applies the plan's rule:

- distance 0: Supported;
- distance 1-4: Inconclusive;
- distance 5 or more: Contradicted.

## D5. Follow-up A1 runs hit the 27 h cap; budget closes for P11 (2026-10-06 10:20 NZDT)

**The runs.** All three follow-up A1 runs were stopped by `timeout` at 27 h, at 2026-10-06 10:19, without writing a
candidate:

| Run | Unitaries consumed at the cap |
|---|---|
| P11, cutoff 0.001 | 81 of 1,984 |
| P11, cutoff 0.0005 | 89 of 1,984 |
| P12, cutoff 0.002 | 177 of 2,433 |

Details are in `results/tables/A1_progress.csv`. Progress is not linear in time. The completed P11 run at cutoff
0.002 had consumed 107 unitaries after 7.3 h and finished all 1,984 at 17 h, once unswapping had simplified the
operator. Tighter cutoffs keep more of the operator, and in these runs the unswapping phase ran slowly.

**P11 budget.** Under D3's accounting, P11 has used 17.0 + 27 + 27 = 71.0 of its 72 A100-hours. A2 on P11 needs more
than the 1 h left (A2 on P9, a smaller circuit, took 1.4 h) and is therefore not run. P11's only candidate is the one
from its first A1 run: top-sample frequency 0.001, so no peak was resolved.

**P12 budget.** P12 has used 27 of its 72 h. A2 at chi 256 was started at 10:20 (`timeout 10h`), as D1 specified. A2
was at chance on P9, so it is not expected to recover the peak. No further A1 run on P12 is planned: at the observed
rate it would far exceed the remaining 45 h.

## D6. Attacks complete; final candidates are committed before scoring (2026-10-06 14:02 NZDT)

**P12 A2.** A2 on P12 at chi 256 finished in 13,263 s (3.7 h), with a mean per-bit margin of 0.15. P12 has used
27 + 3.7 = 30.7 A100-hours.

**Selection.** No further attack is run. The final candidates are selected by `code/select_candidates.py` under the
D4 rule and committed with their SHA-256 before `code/score.py` reads the sealed answers:

- **P11:** the only candidate is from the first A1 run, which resolved no peak (top-sample frequency 0.001).
- **P12:** the only candidate is from A2.
