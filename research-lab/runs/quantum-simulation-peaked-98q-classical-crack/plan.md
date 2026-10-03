# Preregistration: can one A100 recover the hidden peak of the 98-qubit peaked circuits P11 and P12?

Lead: `quantum-simulation-peaked-98q-classical-crack` (research-lab/leads.json). Written 2026-10-04 and committed to
git before any attack has been run on P11 or P12.

## What has been seen before writing (disclosure)

**Circuits.** The QASM files for P9 (56 qubits), P11 (98 qubits, 1999 CZ) and P12 (98 qubits, 2457 CZ), downloaded
from the Quantum Advantage Tracker. SHA-256 sums are in `data/QASM_SHA256SUMS`. Only the file headers were viewed.

**Answers (sealed, never displayed).** The Helios-1 recovered peak bitstrings from tracker issues #246 (P11) and #247
(P12) were extracted by `code/seal_answers.py` into `data/sealed/answers.json`. Only their counts (one string each)
and hashes were printed:

- file: `0c588228f5216eaa…`;
- P11: `ebb2cbc3566d51a2…`;
- P12: `4696512cbb788ec3…`.

**Prior work and status** (web, 4 Oct 2026).

- Kremer & Dupuis (arXiv:2604.21908) code at commit HEAD of d-kremer/peaked-circuit-simulation. Its unswapping
  notebook breaks P9 in 2,722 s on an A100 with the parameters reproduced below.
- No classical P11/P12 recovery is posted on the tracker or arXiv. The only recoveries are the Helios-1 issues
  #246/#247.

## 1. Question

BlueQubit's 98-qubit peaked circuits P11 and P12 were posted after the 56-qubit P9 was broken classically. They
remain listed as active quantum-advantage candidates. Can open classical attacks recover their 98-bit peaks within a
fixed single-GPU budget?

## 2. Validation step (must pass before P11/P12)

Reproduce the P9 recovery with the published unswapping parameters:

- seed 123, cutoff 0.002, max_bond 8192;
- unswap_threshold 1e6, center_ratio 0.5;
- MPS cutoff 0.002, 1,000 samples.

The pipeline must recover the published P9 peak exactly within 3× the published runtime (8,166 s). If it fails, the
environment is fixed using P9 only.

## 3. Attacks on P11 (primary) and P12 (secondary)

The budget is **72 A100-hours per instance** in total across all attacks. Each attack's GPU time is logged.

| Attack | Description |
|---|---|
| A1 | **MPO middle-out cancellation with greedy unswapping** (Kremer & Dupuis code, unchanged): the P9 parameters first, then max_bond 16384 if memory allows, and cutoff 0.001. |
| A2 | **Low-bond MPS bit-marginal distillation** (Kremer & Dupuis distillation method): χ ∈ {64, 256, 1024}, several qubit orderings, and per-bit majority vote over ≥ 1,000 samples per run. |
| A3 | **Heisenberg-picture propagation of each Z_i** with coefficient truncation. Only if a working implementation is available within the budget; otherwise reported as not run. |

**Final candidate.** Each attack produces one candidate 98-bit string and its own confidence measure:

- A1: the most frequent sample and its frequency;
- A2: the mean per-bit majority margin;
- A3: the mean |⟨Z_i⟩|.

The final candidate per instance is the attack candidate with the highest confidence, ranked A1 > A2 > A3 when
confidences are not comparable. It is chosen and its SHA-256 committed to git **before** the sealed answers are read.

## 4. Scoring and decision rule

`code/score.py` reads `data/sealed/answers.json` exactly once, after the candidates are committed. It reports the
Hamming distance between each committed candidate and the sealed Helios string.

| Verdict | Condition on the final P11 candidate |
|---|---|
| Supported | Hamming distance 0 |
| Contradicted | Hamming distance ≥ 5 when the budget is exhausted |
| Inconclusive | Hamming distance 1–4 |

P12 is scored under the same rule as a secondary result. If no attack produces any candidate within the budget, the
verdict is Contradicted, and the bond-growth and cost curves are reported as hardness evidence.

## 5. Reporting

- Bond dimension and truncation against absorbed layers.
- GPU-hours, peak memory and extrapolated cost for attacks that did not finish.
- An independent reviewer agent checks code and the blinding before any verdict.
- The report opens with "In plain terms". If successful, a tracker submission is drafted for the lab owner to post.
