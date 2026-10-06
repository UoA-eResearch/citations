# Independent review: "Can one A100 recover the hidden answers of the 98-qubit peaked circuits?"

Reviewer: independent adversarial reviewer agent · 6 October 2026, 14:20 NZDT · Brief: `review/prompt.md`
Scope: plan.md (ff1996a), deviations.md (D1–D6), report.md (296bd03), code/, results/, logs/, git history, the vendored
Kremer & Dupuis repository, and the public record (tracker issues, arXiv). The sealed file `data/sealed/answers.json`
was not opened; its SHA-256 and mtime were checked. Web fetches of the Helios-1 issues were instructed to return no
bitstrings, so the reviewer also remains blind.

## Recommendation: **fix first**

The study's internal machinery is sound: blinding held, the candidates were committed before the answers were read, the
A1 code matches the authors' notebook parameter for parameter, every runtime and count in report.md traces to a
results file or log, and the six deviations are timestamped to the minute by their commits. But the report cannot be
published as drafted, for three reasons.

1. **The circuits were cracked classically during the study.** On 5 October 2026, between the preregistration (4 Oct)
   and the draft report (6 Oct), tracker issues #251 and #252 reported blind classical recoveries of P11 (89 s) and P12
   (182 s) on a 16-vCPU shared VM, matching the Helios-1 strings bit for bit and accepted by the BlueQubit portal. The
   report's central framing — "these two circuits survived this attack and this budget. That is evidence they are hard
   to simulate classically" — is false in the sense a reader will take it. The result still stands as a refutation of
   the three *preregistered* attacks, but it must be reframed as a negative result about the MPO-unswapping heuristic,
   not about the circuits.
2. **The P12 "Contradicted" verdict misapplies the preregistered rule.** Plan §4 requires Hamming ≥ 5 *when the budget
   is exhausted*; P12 used 30.7 of 72 hours and the planned A2 grid was not run.
3. **"Within 72 A100-hours" overstates the compute actually delivered.** Under the D3 convention three concurrent
   processes sharing one GPU were each charged full wall-clock, so P11's 71.0 "A100-hours" correspond to about 44
   GPU-wall-hours, 27 of them shared three ways, with GPU utilisation never measured. The convention is conservative for
   spending but it is what triggered the "budget exhausted" condition.

None of the fixes changes the Hamming distances or the blinded verdict for P11; they change what the report claims the
verdict means.

## What held up (verified)

- **Blinding chain.** `answers.json` mtime 2026-10-04 12:29; its SHA-256 (`0c588228…7da1`) matches `SEALED_SHA256.txt`
  and plan.md, both committed in ff1996a at 12:32:44 and pushed at 12:32:46 NZDT (GitHub push event 23:32:46Z). The
  first attack run started 12:33:18. No file in `code/` other than `seal_answers.py` (write) and `score.py` (read)
  references the sealed path; no log mentions it. `select_candidates.py` reads only `results/*_A*.json`.
- **Commitment before scoring.** `final_candidates.json` was committed in 0bf21f0 (14:02:24) and is byte-identical at
  HEAD; `score.json` (committed 296bd03, 14:05:03) records `candidates_commit = 0bf21f0…`. Both candidate strings equal
  the strings in `P11_A1_mb8192_c0.002_s123.json` (committed 2bc5e9c, 5 Oct 07:51) and `P12_A2_chi256_s1234.json`
  (committed c31b284, 14:02:03); their SHA-256s recompute correctly. `score.py` refuses to run on an uncommitted or
  modified candidates file and refuses a second run.
- **Decision rule for P11.** Hamming 47 ≥ 5 with 71.0/72 h used under the declared convention: "Contradicted" as the
  plan defines it (subject to issue 3 on what the hours mean).
- **A1 is the authors' method, unchanged.** Vendored repo at 9a77ed8 = `KREMER_COMMIT.txt`, working tree clean. All
  nine `mpo_compress_unswap` arguments, `layers_left[:-2]`, the MPS cutoff 0.002 and 1,000 samples are identical to
  `peaked-circuit-unswapping.ipynb`. The notebook's P9 run time is 2,721.90 s (plan: 2,722 s).
- **Validation gate.** 6,267 s < 8,166 s; candidate equals the notebook's `true_bs`; top count 107/1000 (notebook 106).
- **Deviation timestamps** D1–D6 equal the commit times of 2f8d209, 2bc5e9c, 18322bf, f0c5505, 0bf21f0 to the minute.
  D4 (tie rule) was committed 5 Oct 09:06, after the first P11 candidate existed but 25 h before any follow-up could
  have produced one; with single candidates per instance the rule had no effect.
- **The 27 h caps** are real: all three follow-up logs run 07:19:23 (5 Oct) to 10:19:12–15 (6 Oct), 26.998 h.
- **"Most of the work goes into unswapping."** Classifying log lines by phase: unswapping accounts for 62 % (P9),
  69 % (P11, 0.002), 72–73 % (P11 follow-ups) and 70 % (P12) of wall time.
- **Bit-order convention.** Tracker issue #241 (P9, same submitter as #246/#247) prints the P9 peak in the same
  q[0]→q[n−1] order as the Kremer notebook and as `attack_unswap.py`'s permuted output, so the convention used by
  `score.py` is at least consistent for P9 (see issue 11 for the residual).

## Numbered issues

### 1. The report's headline framing is overtaken by events (critical; fix before anything else)

**Location.** report.md "In plain terms" ¶1 ("remain listed as open challenges for classical computers"), ¶3 ("That is
evidence they are hard to simulate classically"); Caveats bullet 1 ("No classical recovery of P11 or P12 had been
reported … as of 4 October 2026"); plan.md §4 ("reported as hardness evidence"); leads.json title ("the unsolved
98-qubit peaked-circuit challenge") and plain_summary ("No ordinary computer has found it yet").

**Finding.** Tracker issues #251 (P11) and #252 (P12), opened 5 October 2026 by Dylan Neve (with Claude), report a
classical solution by *structural de-obfuscation plus exact tensor-network contraction*: every 2-qubit block has the
pattern `u a; u b; cz a,b; u a; u b`; single-qubit rotations in the second half are exact inverses of partners in the
first half, which fingerprints the inserted identity blocks (419 anchor pairs in P11, 569 in P12); the hidden
permutation is a fixed-point-free involution of 49 transpositions; 1,716 of P11's 1,999 gates are a permutation in
disguise; the remaining core (~280 two-qubit gates) has treewidth ≈ 15 and its exact single-qubit marginals contract in
seconds with quimb/cotengra. Runtimes 88.6 s (P11, peak probability 0.303) and 181.9 s (P12, 0.205) on a shared
16-vCPU Xeon VM; the solver ran blind; both strings matched Helios-1 (98/98) and were accepted by the BlueQubit portal.
The issues are open and assigned to the tracker maintainers (MSRudolph, matteoacrossi). Code: `solve_peaked.py` in
github.com/dylanneve1/qsim-lab (`research/simulability/peaked-circuits.md`).

The caveat "as of 4 October 2026" is literally true and the preregistered hypothesis (leads.json: *these three*
attacks recover the peak within 72 A100-hours) is still contradicted. But a reader of the plain-terms summary will
conclude that the circuits resist classical simulation, which the public record now contradicts by five orders of
magnitude in runtime.

**Fix.** (a) Rewrite "In plain terms" ¶1 and ¶3: the circuits are *not* hard classically; the best published
*heuristic* (MPO middle-out cancellation with greedy unswapping) does not scale from P9 to P11/P12 at this budget, while
a structural attack that removes the obfuscation analytically solves both in minutes on a CPU. (b) Add a dated section
"Overtaken by events (5 October 2026)" summarising #251/#252 with their method, runtime, blind protocol and portal
acceptance, and stating that the tracker had not yet reviewed them at the time of writing. (c) Delete every use of
"hardness evidence" and withdraw the plan §4 interpretation explicitly. (d) Restate the verdict's scope in one
sentence: "Refuted for the three preregistered attacks at this budget; the broader question — can an open classical
method recover the peaks? — was answered affirmatively by an independent party during the study." (e) Update the
leads.json title/plain_summary and consider whether the one-word verdict_tag needs a qualifier (see issue 9).
(f) Add a "what we missed" paragraph: `structure.py` computed pair counts and degree sequences; it did not look for
U/U† inverse-pair fingerprints between consecutive CZs, which is the structure #251 exploited. A reviewer's own check
confirms that naive consecutive same-pair CZ runs are absent (0 runs of length ≥ 3 in P11), so the lead's "not naive
SWAP insertion" was correct on its own terms but the obfuscation was still removable.

### 2. P12 is scored "Contradicted" although the plan's condition is not met (major)

**Location.** report.md Scoring table, row P12 ("Contradicted (≥ 5)"); score.json `P12.verdict_rule`; D5/D6.

**Finding.** Plan §4: "Contradicted: Hamming distance ≥ 5 **when the budget is exhausted**." P12 used 30.7 of 72 h.
The plan's A2 specification (χ ∈ {64, 256, 1024}, several qubit orderings) was run once, at χ 256 and one ordering,
although χ 512 (~8× the 3.7 h) and alternative orderings would have fitted in the remaining 41.3 h. D1 justified a
single A2 run for *P11*; D5 applied it to P12 "as D1 specified", which D1 did not say. `score.py` applies the Hamming
thresholds without the exhaustion condition, so the label is mechanical.

**Fix.** Report P12 as: Hamming 57 (chance); the Contradicted condition is not met because 41.3 h were unspent; the
secondary result is therefore *not scored* under the preregistered rule (or "Inconclusive by budget"). Add a deviation
entry for the unrun A2 grid on P12 with its justification (A2 at chance on P9; CircuitPermMPS distillation is the
authors' method for unpermuted circuits, README "moderate-depth circuits"). Optionally patch `score.py` to take a
`budget_exhausted` flag so the rule cannot be misapplied again.

### 3. "72 A100-hours" is a process-hour count, not GPU time; the convention triggered the verdict (major)

**Location.** report.md title/abstract ("72 hours on one A100"), Results ("P11 used 71.0 of its 72 A100-hours"),
Caveats bullet 4 ("Conservative accounting"); D3 "GPU-hour accounting (conservative)"; D5 "P11 budget".

**Finding.** Wall-clock windows from the logs: P11's first run 14:18:38 (4 Oct) → 07:14:49 (5 Oct), 16.94 h, alone on
the GPU except for P9 A2 (14:39–16:01) and CPU-side A3 tests; the three follow-ups 07:19:23 → 10:19:15, 27.0 h, three
processes on one GPU. GPU-wall-hours in which P11 attacks ran: 16.9 + 27.0 ≈ 44; if the GPU were saturated the P11
share would be ≈ 35. P12: 27 h shared + 3.7 h alone ≈ 31 wall, ≈ 13 saturated-equivalent. GPU utilisation was not
logged (`nvidia-smi` sampling absent; peak memory < 2 GB per process suggests the unswapping phase is small-tensor and
CPU/Python bound, i.e. contention was probably mild — the follow-ups reached 50 absorbed blocks at 0.94 h versus 1.59 h
for the solo run — but this is inference, not measurement). The plan did not define the accounting; D3 fixed it after
the first run and before the follow-up results, so it is not outcome-driven in intent, but in effect it is the sole
reason the "budget exhausted" clause was satisfied for P11 with ≈ 44 GPU-wall-hours.

**Fix.** In the Results table add a column "GPU wall-hours (sharing)". Restate the verdict as "within 71 process-hours
(≈ 44 GPU-wall-hours, 27 of them shared three ways)". Recast Caveats bullet 4: the convention under-delivers compute
relative to the plan's natural reading of "A100-hours", which weakens the refutation rather than strengthening it.
State that utilisation was not measured. (Spending the remaining real GPU budget is moot given issue 1; say so.)

### 4. The environment is 1.5–2.3× slower than the authors' hardware, and the report cites the faster number (major)

**Location.** report.md "In plain terms" ¶1 ("in under an hour"); plan.md §2 (3× 2,722 s); Caveats.

**Finding.** The validation took 6,267 s against the notebook's 2,721.90 s (2.3×) and the paper's reported 4,059 s on
an A100 80 GB (1.5×; arXiv:2604.21908 states "completed in 4,059 seconds"). So 72 h here ≈ 31–47 "author-A100-hours".
The paper's own number for P9 is "approximately one hour and 10 minutes", not "under an hour".

**Fix.** Cite both figures (notebook 2,722 s; paper 4,059 s), change "under an hour" to "about an hour", and add a
caveat that this environment ran the reference attack 1.5–2.3× slower, so the effective budget in author-equivalent
GPU-hours was correspondingly smaller.

### 5. The structural inference ("more thoroughly scrambled permutation") is a qubit-count artefact (moderate)

**Location.** report.md "Why A1 fails on P11", second paragraph; `results/tables/structure.csv` column
`halves_shared_pairs`.

**Finding.** The halves share 111 pairs (P11) versus 340 (P9). Under independent uniform pairing the expected overlap
is |L|·|R| / C(n,2): P9 703·706/1540 = 322 (observed 340, ratio 1.06); P11 768·699/4753 = 113 (observed 111, ratio
0.98); P12 955·865/4753 = 174 (observed 172, ratio 0.99). The entire difference is explained by 98 versus 56 qubits.
There is no evidence for a "more thoroughly scrambled permutation" in this statistic; and the obfuscation in all three
circuits is in fact the same construction (issue 1).

**Fix.** Delete the sentence or replace it with the chance baseline above. Keep the CZ-per-qubit comparison (41 vs 68)
as a plain description.

### 6. "Truncation had discarded the peak" is inferred, not shown; the promised truncation curve is missing (moderate)

**Location.** report.md "Why A1 fails on P11" ¶1; plan.md §5 bullet 1 ("Bond dimension and truncation against
absorbed layers").

**Finding.** The inference is reasonable — the paper states the SVD cutoff "is the only source of approximation in the
method", and the final MPS had bond 18 (P9: 1, a product state) with 1,000 distinct samples — but no discarded-weight or
truncation-error series was logged or plotted, and the figure plots tensor elements against wall-clock, not bond
against absorbed layers. Whether greedy unswapping chose a poor permutation that *made* the operator truncate badly
cannot be separated from truncation at a fixed permutation. The 15-hour acceleration claim is supported (500 blocks at
15.56 h, 1,000 at 16.42 h; P9: 500 at 1.21 h, 1,000 at 1.39 h). The solo-versus-shared confound for the follow-up
stalls (issue 3) is not mentioned.

**Fix.** Soften to "the only approximation in the method is the SVD cutoff, so the loss of the peak must be
truncation; we did not log the discarded weight". Add the bond-versus-absorbed-layers panel the plan promised (the
stats CSVs contain `u_consumed_total` and `max_bond`), or state explicitly that truncation was not recorded. Note the
sharing confound and the evidence that it was mild.

### 7. No extrapolated cost for the unfinished runs, although plan §5 promised one (moderate)

**Location.** plan.md §5 bullet 2; report.md Results; D5 ("would far exceed the remaining 45 h").

**Finding.** The report gives GPU-hours but not peak memory (in the JSONs: 1.62 GB P11 A1, 0.40 GB P12 A2) nor any
extrapolation. The completed P11 run shows why extrapolation is unreliable (107 blocks at 7 h, all 1,984 at 17 h), but
the report should say that rather than omit it.

**Fix.** Add peak memory to the Results table. Add one sentence: "Progress is non-monotone (107 → 1,984 blocks in the
last 10 h of the completed run), so no time-to-completion can be extrapolated for the capped runs; the only bound is
that none would have finished within the remaining budget at any rate observed in its final 10 h" — and give that rate
(e.g. P11 cutoff 0.001: 81 → 81 blocks between 18.8 h and 27 h).

### 8. `results/tables/A1_progress.csv` has a wrong peak bond and no generating script (minor)

**Location.** `results/tables/A1_progress.csv`, row `P11_A1_mb8192_c0.002_s123`, `peak_max_bond = 8192`.

**Finding.** 8192 is the `max_bond` *parameter* echoed in the run's final summary line (`'max_bond': 8192`), parsed as
a bond value. The true peak is 511 (stats CSV and `a1_progress_series.csv`; reached at 1.59 h). D3 and report.md say
511 and are right; the table contradicts them. The follow-up rows (512, 512, 774) are consistent with the series. No
script in `code/` produces this table (figures.py writes `a1_progress_series.csv` only).

**Fix.** Regenerate the table from the series or stats CSVs with a committed script; correct 8192 → 511.

### 9. Verdict vocabulary: plan says "Contradicted", report says "Refuted" (minor)

**Location.** report.md "Verdict: Refuted"; plan.md §4 table; leads.json verdict_tag (currently null).

**Finding.** The mapping is implicit. The lab's verdict_tag vocabulary includes "Refuted", so the intent is clear, but
the hypothesis sentence the report refutes ("at least one open classical attack recovers P11's peak within 72
A100-hours") is from leads.json, not plan.md, which poses a question and defines labels only.

**Fix.** Write "Contradicted under plan §4, i.e. verdict_tag **Refuted**", cite leads.json for the hypothesis wording,
and — given issue 1 — add the scope qualifier in the same sentence. If the lab prefers a tag that signals the external
development, "Refuted (superseded)" or an explicit note field is better than a bare "Refuted".

### 10. Blinding and provenance claims are slightly stronger than what is recorded (minor)

**Location.** report.md "In plain terms" ¶2 ("we stored Helios-1's answers without reading them"); "What was done"
("committed and pushed (commit 0bf21f0)").

**Finding.** (a) The sealing script never displayed the strings, but leads.json describes the post-processing in
#246/#247 (clustering, medoid), so those issue pages — which display the strings — were consulted when the lead was
written, before sealing. (b) At review time (14:18 NZDT) GitHub's `main` is at 296bd03 and both 0bf21f0 and 296bd03
exist there, but the public events feed shows no push after 21:20Z on 5 Oct, so whether 0bf21f0 was pushed *before*
scoring cannot be confirmed (the feed lags; this is not evidence of a problem). (c) `score.py` output was not saved to
`logs/`. None of this matters for a Contradicted outcome — the blinding guards against help toward the answer, and both
candidates are at chance — but it would matter for a Supported one.

**Fix.** Rephrase to "the sealing script never displayed them; the issue pages had been consulted for metadata when
the lead was researched; blinding protected the attack and selection steps". Replace "and pushed" with "committed
(0bf21f0, 14:02:24; scored and committed 296bd03, 14:05:03)" unless push evidence is added. Save scoring stdout to
`logs/score.log` in future runs. State that the verdict is insensitive to blinding failures.

### 11. Bit-order convention was not verified for P11/P12 and `score.py` tests one order only (minor)

**Location.** `code/score.py` line 31; `code/seal_answers.py` regex.

**Finding.** The sealed strings are whatever 98-bit strings appear in the issue text. For P9 the convention is
consistent (issue #241 prints the notebook's string unreversed). For P11/P12 it was not checked and cannot be without
a second read. `attack_pauli.py` computes `hamming_reversed`, so the author was aware of the ambiguity. Harmless here:
the P11 candidate is one of 1,000 distinct samples and both distances are within 1.7 σ of 49.

**Fix.** Note the P9 convention check in the report. In future, have `score.py` report both orders and the plan declare
which counts.

### 12. The A2 deviation is under-documented and D1/D5 are inconsistent (minor)

**Location.** D1 ("On P11 it is therefore run once, at chi 256"); D5 ("A2 at chi 256 was started … as D1 specified"
for P12); report.md Deviations summary.

**Fix.** Add to the summary: "A2 grid (χ 64/1024, multiple orderings) dropped for both instances after chance-level
P9 result; run once on P12 only." Also record the complex64 → complex128 change as a departure from the notebook (it is
in D1 but not labelled as such).

### 13. Small numerical and presentational points (minor)

- Scoring table: add the chance SD (√(98/4) = 4.95) so 47 and 57 read as −0.4 σ and +1.6 σ.
- P12 A2 "mean margin 0.15" exceeds P9's 0.11, which was at chance; say that the margin is not a reliability signal.
- `final_candidates.json` source `P12_A2_mb256_cNone_s1234`: cosmetic; `cutoff` is undefined for A2.
- "P12 was further out of reach" (plain terms): the only like-for-like comparison is 177/2,433 blocks (7 %) in 27 h
  shared versus P11's 177 at 11 h solo; given issue 1, delete.
- "1,000 samples were all different" is supported only by the top-20 list (all counts 1); fine, but say "the most
  frequent sample occurred once".

## Numbers recomputed

| Quantity | Report / deviations | Recomputed | Source | Agrees |
|---|---|---|---|---|
| P9 A1 runtime | 6,267 s | 6,266.5 s | `P9_A1_mb8192_c0.002_s123.json` seconds_total | yes |
| Validation limit | 8,166 s | 3 × 2,721.90 s = 8,165.7 s | notebook cell 22 | yes |
| Paper's P9 runtime | not cited | 4,059 s | arXiv:2604.21908 full text | see issue 4 |
| P9 A1 top frequency | 0.107 | 107/1000 | JSON top20 | yes |
| P9 A1 peak GPU memory | 1.8 GB | 1.798 GB | JSON | yes |
| P9 A1 candidate = published | exact | True | JSON vs notebook `true_bs` | yes |
| P9 A2 Hamming | 30/56 | 30 (26 reversed) | JSON vs notebook | yes |
| P9 A2 runtime | 1.4 h | 4,930 s = 1.37 h | JSON | yes |
| P11 A1 runtime | 17.0 h | 61,120 s = 16.98 h | JSON; log 14:18:38 → 07:14:49 | yes |
| P11 A1 peak MPO bond | 511 | 511 at 1.59 h; final 31 | stats CSV, series CSV | yes (A1_progress.csv says 8192: wrong, issue 8) |
| P11 A1 samples distinct | all 1,000 | most common count = 1 | JSON top20 | yes |
| P11 blocks at 7.3 h | 107 | 107 (first reached at 6.04 h, 108 at 8.0 h) | stats CSV | yes |
| Follow-up progress | 81, 89, 177 | 81/1984, 89/1984, 177/2433 | logs, last `t_u` | yes |
| Follow-up duration | 27 h | 26.998 h each (07:19:23 → 10:19:12–15) | logs | yes |
| P11 budget (D3 convention) | 71.0 h | 16.98 + 27.0 + 27.0 = 70.98 h | logs | yes |
| P11 GPU-wall-hours (alt.) | not given | ≈ 44 (16.9 solo + 27.0 shared ×3) | logs | issue 3 |
| P12 A2 runtime | 3.7 h | 13,263 s = 3.68 h | JSON | yes |
| P12 A2 mean margin | 0.15 | 0.1497 (3 bits at exactly 0.5) | JSON bit_probs | yes |
| P12 budget | 30.7 h | 27.0 + 3.68 = 30.68 h | logs, JSON | yes |
| Hamming 47 / 57 | 47 / 57 | not recomputed (would need a second read); chain verified: strings = result JSONs, SHA-256 match, `candidates_commit` = 0bf21f0, file unchanged since | score.json, git | chain intact |
| Chance baseline | 49 | 49 ± 4.95; z = −0.40, +1.62 | binomial(98, ½) | yes |
| CZ per qubit | 41 vs 68 | 40.80 vs 68.46 | QASM | yes |
| Shared pairs | 111 vs 340 | 111 vs 340; chance 113 vs 322 | QASM | numbers yes, inference no (issue 5) |
| Two-qubit blocks | 1,984 / 2,433 / (P9) 1,885 | same | logs "Total unitaries" | yes |
| Gate counts | P9 1,917 RZZ; P11 1,999 CZ; P12 2,457 CZ | 1,917 rzz; 1,999 cz; 2,457 cz | QASM | yes |
| Unswapping share of wall time | "most of the work" | 62 % / 69 % / 72–73 % / 70 % | log phase classification | yes |
| Acceleration onset | P9 ≤ 1.5 h; P11 ≈ 15 h | P9: 500 blocks at 1.21 h; P11: 500 at 15.56 h | series CSV | yes |
| A3 progress | 16–18 of 207 slices | unfinished 189–191 of 207 | `P9_A3_*_subset.json` | yes |
| Sealed file hash | `0c588228…` | `0c588228f5216eaa21bb04116b2806f667d87ec2bf5a9fbabebcf96f10be7da1` | sha256sum | yes |
| QASM hashes | recorded | all three OK | `sha256sum -c` | yes |
| Kremer commit | pinned | 9a77ed8…, clean tree | vendored repo | yes |
| Deviation times | D1–D6 | = commit author times (2f8d209, 2bc5e9c, 18322bf, f0c5505, 0bf21f0) | git log | yes |

## What a quantum-simulation expert would add

- The decisive objection is issue 1: the obfuscation is removable analytically, so no amount of MPO budget was the
  right lever; the study tested one heuristic family, and its negative result says nothing about classical hardness.
- Issue 3: "A100-hours" means GPU-hours; three processes on one under-utilised GPU for 27 h are 27 GPU-hours, not 81.
- The P9 → P11 slowdown of the *same* method at the *same* cutoff (1.7 h → 17 h, final MPS bond 1 → 18) is the one
  genuinely informative number in the study about the unswapping heuristic, and deserves the mechanistic paragraph more
  than the structural statistics do.
- A2 (bit-marginal distillation at χ 256) was never a credible attack on permuted circuits; the authors' README scopes
  it to unpermuted circuits. Including it as one of "the best published classical attacks" overstates the attack
  portfolio.

## Sources consulted

- Tracker issues #246, #247 (Helios-1, 18 Sep 2026), #251, #252 (classical, 5 Oct 2026), #241 and #153 (P9 classical),
  github.com/quantum-advantage-tracker/quantum-advantage-tracker.github.io/issues/
- Kremer & Dupuis, arXiv:2604.21908 (abstract and full text, v1 23 Apr 2026); vendored repository at 9a77ed8
- github.com/dylanneve1/qsim-lab, `research/simulability/peaked-circuits.md` and `solve_peaked.py` (summarised without
  bitstrings)
- github.com/MonitSharma/peaked_circuits (Helios-1 recovery pipeline)
- GitHub REST API for UoA-eResearch/citations: commits 0bf21f0, 296bd03 on `main`; push-event feed to 21:20Z 5 Oct
