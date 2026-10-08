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

## D3a. The D3 recheck also failed open; replaced by a hypothesis-free portfolio (2026-10-08 14:41 NZDT)

The D3 recheck (14:37-14:40) still counted closed arithmetic facts as L2 leaks. For example, the training statement
1 + 1/(1 + 1/(1 + 1/(1 + 1/2))) = 8/5 "implied" the test statement 1 + 1/(1 + 1/(1 + 1)) = 5/3.

**The cause.** With the hypothesis replaced by `True`, `simp_all` clears `h : True` from the context, so the
portfolio's `nlinarith [h]` branch fails on an unknown identifier. A conclusion that `simp_all` plus `nlinarith`
proves on its own therefore looked informative.

**The fix.** The counterfactual is now the conclusion on its own, with no hypothesis, under every hypothesis-free
branch of the certification portfolio plus `norm_num`, `linarith`, `nlinarith` and `decide` (60 s;
fail-closed). This is at least as strong as anything the certification portfolio could do without the training
statement. The D3 outputs are kept in `data/certify/recheck_D3_true_variant/`.

No prover sampling or verification has taken place.

## D3b. Explosion guard: implications from refutable training statements do not count (2026-10-08 14:45 NZDT)

After D3a, a spot-check of Goedel-Pset L2 pairs still found unrelated statements. Each training statement was false,
for example "∀ a : ℝ, a = 0" and "n = 20 → n − 2 = 18 → 18 + 1 = 19 → n − 18 = 1". `simp_all` or `aesop` derives
a contradiction from the false hypothesis and then proves the benchmark statement by explosion. This was checked
branch by branch in Lean on three pairs. Goedel-Pset contains false formalisations, as other autoformalised corpora
do.

**The extra condition.** An implication a ⇒ b counts only if a is not refutable: `(∀ a) → False` must not be provable
by the certification portfolio within 60 s. A refutation or a timeout makes the implication uninformative
(fail-closed). For L1 the same applies in the other direction.

The D3a outputs are kept in `data/certify/recheck_D3a/`. No prover sampling or verification has taken place.

## D4. Leak tiers final; sampling plan and minimum detectable effect, before main sampling (2026-10-08 14:52 NZDT)

**Leak tiers for the 488 miniF2F items** (D1-D3b; `results/tables/leak_rates.csv`, `leak_pairs_bench_minif2f.csv`):

| Corpus | Items leaked (L0/L1/L2) | Share |
|---|---|---|
| STP_Lean_0320 | 179 (174 / 3 / 2; 173 of the 174 L0 items are validation items) | 36.7% |
| Goedel-Pset-v1 | 67 (10 / 36 / 21) | 13.7% |
| SFT_dataset_v2 | 61 (0 / 31 / 30) | 12.5% |
| NuminaMath-LEAN | 55 (5 / 37 / 13; the 5 L0 items are all test items) | 11.3% |
| DeepSeek-Prover-V1 | 16 (0 / 15 / 1) | 3.3% |
| Goedel's Lean-workbook-proofs | 10 | 2.0% |
| Lean Workbook | 0 | 0% |
| Any corpus | 252 | 51.6% |

69 items are automation-provable.

**Leaked (item, prover) pairs against each prover's own corpora:** Goedel-Prover-V2 99, Kimina 55, DeepSeek-Prover-V2
16; 170 in all. Every one has at least one certified reformulation in its prover's environment.

**The pilot** (13:06-13:39 NZDT, 8 October). 20 items, 8 samples per version, at the plan's 4,096-token cap. **No
pilot output was verified or scored.** Only finish reasons and lengths were read. Truncated outputs:

| Prover | Truncated |
|---|---|
| DeepSeek-Prover-V2 | 24% |
| Goedel-Prover-V2 | 44% |
| Kimina | 36% |

The model cards recommend 8,192 (DeepSeek), 8,096 (Kimina) and 32,768 (Goedel) tokens. Throughput implies that the
plan's full design (488 items × about 2.7 versions × 32 samples × 3 provers) would take about 35 GPU-hours at 4,096
tokens and 45 or more at 8,192. That is a long outage of the lab owner's shared vLLM service.

**Sampling plan.**

1. **Token cap: 8,192** for all three provers, close to the DeepSeek and Kimina model cards. Goedel's documented
   32,768 is not affordable, so some of its outputs will still be truncated. Truncation is treated identically
   across versions, so the DiD is not biased by it.
2. **Items per prover:**
   - every own-leaked item;
   - **150 clean items** drawn at random (seed 20261008) from that prover's clean items with a certified
     reformulation.

   The leaked arm dominates the DiD's variance, so dropping clean items costs little precision. **pass@32 is kept.**
3. **Secondary, pre-specified now: the STP prover** (kfdong/STP_model_Lean_0320, revision ae7751cc).
   - Its own corpus, STP_Lean_0320, holds 179 leaked items, nearly all miniF2F-valid statements verbatim.
   - All 488 items, 32 samples per version, completion-style prompt as in STP's corpus.
   - Temperature 1.0, top-p 0.95, at most 2,048 tokens.
   - Analysed separately and not pooled into H1.
4. **Verification** uses all of Mathlib, with bare `π` read as `Real.pi` in both statement and proof (as in D1).
   Lean 4.9 serves DeepSeek, Goedel and STP; Lean 4.15 serves Kimina.

**Minimum detectable effect (plan section 5), recorded before sampling.** With n_leaked = 170 and n_clean = 450:

  MDE = 2.49 × 0.30 × sqrt(1/170 + 1/450) = **6.7 pp**

That is at most 10 pp, so all three verdicts remain reachable.

## D5. STP tokenizer configuration fixed; the first STP outputs discarded unverified (2026-10-08 14:59 NZDT)

**The problem.** STP's released `tokenizer_config.json` declares `LlamaTokenizer`, a SentencePiece class, but its
`tokenizer.json` is DeepSeek's byte-level BPE. Loaded that way:

- prompts were encoded to the wrong token ids;
- outputs were decoded as raw byte-level symbols ("Ġ", "Ċ").

The first 21 STP requests returned English prose instead of Lean tactics. They are kept as
`data/samples/stp_broken_tokenizer.jsonl` and are **not verified or scored**. The run was stopped after 90 seconds.

**The fix.** The local copy's `tokenizer_class` is set to `PreTrainedTokenizerFast`, which uses `tokenizer.json` as
released. The original is kept as `tokenizer_config.orig.json`.

- Checked on CPU: a prompt round-trips exactly, and the BOS token (100000) is added by the post-processor.
- STP is resampled in full after the three main provers (`code/run_gpu_stp.sh`), with the same restart guarantee for
  the owner's vLLM.

**Also.** The CPU chain (`run_cpu_main.sh`) was stopped and restarted from the edited script. bash had kept the old
copy open after the in-place edit. Every step resumes from its output file.
