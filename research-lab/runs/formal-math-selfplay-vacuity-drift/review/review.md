# Independent review: "Do self-play provers drift toward vacuous conjectures?"

Reviewer: independent adversarial review (Claude Fable 5.1), 2026-10-06, of the draft at commit 6da94a2. Brief:
`review/prompt.md`. Everything below was checked against `plan.md` (86f1489), `deviations.md` (D1–D6), `report.md`,
`code/`, `results/`, the row files, the Lean 4.9 and 4.15 environments, STP's public code, and the STP and NuminaMath
dataset cards and papers. My re-check scripts and their outputs are in the session scratchpad; the commands and results
are reproduced here in enough detail to be re-run from `code/`.

## Recommendation: **fix first**

The preregistered decision rule was applied correctly, every number in `report.md` matches `results/tables/`, and no
analysis choice followed sight of outcomes. The verdict direction (no doubling; vacuity falls within each self-play
phase) is very likely to survive. But the measurement behind the numbers has three defects that change the reported
rates, one of which is a soundness hole in the certificate, and the report omits a result that cuts against its own
dynamics story. These should be repaired before any verdict is published:

1. **The vacuity certificate is unsound for statements with auto-bound (autoImplicit) variables.** The goal swap and the
   automation step re-elaborate the hypotheses with the conclusion replaced by `False`, so a variable whose type was
   fixed only by the conclusion (e.g. `ℝ` via `Real.sqrt` or a cast) silently defaults to `ℕ`, and hypotheses that are
   satisfiable over `ℝ` or `ℤ` become contradictory over `ℕ`. I re-checked every one of the 1,207 certified rows in the
   primary windows against the *original* statement's elaboration: 18 (1.5%) are false positives (17 of 725
   early, 1 of 482 late). The 0/20 satisfiable controls could not catch this because every control declares its
   variables. 201 of the 1,207 certified rows (16.7%) involve auto-bound variables: 189 of 725 (26.1%) early, 12 of 482 (2.5%) late.
2. **The Lean environment is not STP's.** STP's verifier (`RL/utils/prover/lean/verifier.py`, line 32) compiles under
   `import miniF2F` (a curated 55-module subset, `assets/setup/miniF2F.lean`) plus per-row headers, not `import Mathlib`.
   This is why 4.5% of STP's own verified proofs fail here: 2,382 sampled rows fail on `π` (ambiguous between `Real.pi`
   and `Nat.primeCounting` only when all of Mathlib is imported; all 8 I tested re-verify under `import miniF2F`), about
   900 fail on identifiers whose per-row `open` header the released corpus dropped, and 427 prompts are truncated and
   never parse. The report attributes these to "did not re-verify" and says the rows were "checked in STP's own Lean
   environment". The exclusions are structured by topic and by iteration (truncated prompts: 388 early vs 11 late;
   dropped headers: 4 early vs 490 late).
3. **The certificate cannot examine 25% of early rows but 1% of late rows.** Statements with no binders (hypotheses
   inside the conclusion as `∀ …, … → …`) can never be certified by this pipeline. They are 24–41% of eligible rows in
   iterations 1–4 and ~1% in 38–47. The per-iteration curve therefore mixes coverage with prevalence; among checkable
   rows the primary ratio is 0.44 (0.40–0.50), not 0.60.
4. **An unreported control result.** `summary.json` contains the statement-control contrast 38–47 vs 0–9: RR 0.54
   (0.32–0.93). The LeanWorkbook control, whose vacuity the report treats as fixed, fell by about half over training.
   Since 90% of certificates come from the released proof (goal swap), a falling control rate means detection
   sensitivity or pool composition changed with the prover, which is a confound for the dynamics interpretation. The
   report says only "no clear trend (ρ = −0.22, p = 0.12)".

Fixing 1–3 changes the headline rates, the 1,207 count, the "8–10% after each restart" claim and the per-iteration
figure; fixing 4 changes the interpretation. The decision rule itself needs no change.

## Numbered issues

Severity: **A** = must fix before publication; **B** = must edit (disclosure, hedging, wording); **C** = minor.

### A1. Certificate soundness: auto-bound implicit variables change type under the goal swap

**Where.** `code/vacuity.py` lines 100 and 109–112 (`theorem vac_thm {B} : False`, `theorem vac_thm : ∀ {B}, False`);
`code/repair_split.py` line 46; `plan.md` section 3 step 4; `report.md` "Certificate".

**What.** The REPL elaborates commands with Lean's default `autoImplicit true` (mathlib's `lakefile` only disables it
for mathlib's own modules). STP's conjecturer often omits variable declarations, e.g. `theorem foo (h₀ : 0 < x)
(h₁ : 0 < y) (h₂ : 0 < z) (h₃ : x + y + z = 1) : √1 / (1 + x^2 * y^2) + … ≤ 9`. In the original, `Real.sqrt` in the
conclusion forces `x y z : ℝ`. In `theorem vac_thm (h₀ : 0 < x) … : False` nothing constrains the type, Lean's numeral
default makes `x y z : ℕ`, and `0 < x ∧ 0 < y ∧ 0 < z ∧ x + y + z = 1` is contradictory over `ℕ`. `omega` certifies it;
the kernel checks it; the axioms are fine. The statement is satisfiable. The split check (`example : ∀ B, C := orig`)
passes because it elaborates B *with* C. Minimal reproduction in this toolchain:

```
theorem orig_demo (h1 : 0 < x) (h2 : x < 1) : (x : ℝ) ^ 2 < 1 := by nlinarith   -- @orig_demo : ∀ {x : ℝ}, …
theorem vac_demo  (h1 : 0 < x) (h2 : x < 1) : False := by omega                 -- @vac_demo  : ∀ {x : ℕ}, …  [propext, Quot.sound]
```

**Evidence.** For every certified row in the primary windows I rebuilt the certificate exactly as the pipeline did
(env 0), added the original theorem on top, and ran

```
theorem chk B : C := by exfalso; exact vac_thm (n₁ := n₁) (n₂ := n₂) …   -- every named binder of B passed by name
```

which succeeds iff the certificate refutes the original statement's hypotheses as elaborated in the original statement.
Validated on 15 hand-inspected rows (5 known false positives flagged, 10 benign cases pass). Result over the
1,207 certified rows: all 1,207 certificates reproduce in env 0; 18 (1.5%) are false positives (17 of 725 in 1–9,
2.3%; 1 of 482 in 38–47, 0.2%; row ids at the end). Type pairs: 10 ℝ→ℕ, 4 ℤ→ℕ, 4 with the auto-bound variable
unresolved in the swapped statement (e.g. `θ < 0`); methods: omega 9, goal swap 4, nlinarith 2, aesop 2, simp_all 1;
all 18 are flagged by the autoImplicit probe. By iteration the false-positive share of certificates is 5.7% (it 1),
1.3%, 1.4%, 2.6%, 7.6% (it 5), 2.2%, 1.2%, so the early peaks are inflated more than the window average. Nine further
rows reuse a binder name (three `h₀`), which the named-argument check cannot handle; their printed telescopes agree
with the original, so they are genuine. Two rows' original proofs are context-sensitive (`maxRecDepth`) in the
reversed environment order; their telescopes agree too. Removing the 18 from the numerators (same denominators) gives
p_E = 4.19%, p_L = 2.55%, RR = 0.610 (0.543–0.685): the verdict is unchanged, the rates and the 1,207 count are not. Confirmed examples: 682372, 364393, 333422 (ℝ → ℕ), 174691 (ℤ → ℕ, `b < 0`), 84593 (iteration
45, ℝ → ℕ). A probe `set_option autoImplicit false in theorem t B : C := by sorry` shows 16.7% (201 of 1,207) of certified
rows have at least one auto-bound variable (26.1% (189 of 725) early vs 2.5% (12 of 482) late). Not every such row is a false
positive: when the conclusion does not fix the type, the *original* statement is also over `ℕ` and genuinely vacuous
(e.g. 1353597, `a < 0` with `a` undeclared), which is itself a mechanism the report should name.

**Fix.** Elaborate the certificate in the original statement's context instead of swapping the goal:
`theorem v B : C := by exfalso; <released proof>` and `theorem v B : C := by exfalso; <tactic>` (and, for the
automation route, `by intros; exfalso; <tactic>`, which also covers A3). A proof of C that goes through `exfalso` is
a kernel-checked proof of `False` from exactly the original hypotheses. Keep the axiom check. Re-run on all rows (the
false-negative direction is also possible: a hypothesis like `x * x = -1` is contradictory over `ℝ` but fails to
elaborate over `ℕ`). Record the autoImplicit probe per row and report the share of certified rows that involve
auto-bound variables, by iteration, as a cause category. Apply the same fix to the four other corpora before quoting
their rates. Add two satisfiable controls with undeclared variables whose type is fixed only by the conclusion.

### A2. The environment is not STP's; 4.5% re-verification failures are mostly name-resolution mismatches

**Where.** `plan.md` "Environment" and section 3 step 2; `code/lean_repl.py` line 17 (`HEADER = "import
Mathlib\nimport Aesop"`); `report.md` "What was done" ("checked in STP's own Lean environment"), "Validation", "Caveats".

**What.** STP's verifier is DeepSeek-Prover-V1.5's: `LEAN_HEADER = 'import miniF2F\nimport Aesop\nset_option
maxHeartbeats 0\nopen BigOperators Real Nat Topology Rat\n'` (kfdong/STP, `RL/utils/prover/lean/verifier.py` line 32),
with `header = test_info.get('header')` overriding it per row (`RL_utils.py`, `group_by_header`). `miniF2F.lean`
imports 55 specific Mathlib modules and not `Mathlib.NumberTheory.PrimeCounting`, so `π` is unambiguous there. Under
`import Mathlib` with `open Real Nat`, `π` is ambiguous even when the type is forced (`#check (π : ℝ)` works,
`example (x : ℝ) (h : x = π / 6) : x > 0` does not). Taxonomy of the 92,000 sampled rows (my classification of the
recorded error messages):

| Class | Early 1–9 | Late 38–47 | Other | Share of sample |
|---|---|---|---|---|
| Eligible | 16,706 (92.8%) | 18,726 (93.6%) | 51,208 (94.8%) | 94.2% |
| `π` ambiguous (environment) | 531 (2.95%) | 310 (1.55%) | 1,541 | 2.6% |
| Unknown identifier / `function expected` (per-row header dropped: `card`, `Bijective`, `Tendsto`, `is_topology`) | 4 (0.02%) | 490 (2.45%) | 408 | 1.0% |
| Parse error: truncated prompt (`(hA : A.Finite:= by`) | 388 (2.16%) | 11 (0.06%) | 28 | 0.5% |
| Split-check failure | 334 | 362 | 554 | 1.4% |
| Re-verify timeout (100 s) | 28 | 23 | 103 | 0.2% |
| Other re-verify error | 9 | 78 | 158 | 0.3% |

I compiled STP's `miniF2F.lean` against the local mathlib and started the REPL with `import miniF2F\nimport Aesop`:
`#check π` gives `π : ℝ`, `Nat.primeCounting` is unknown, and 8 of 8 randomly chosen failing `π` rows re-verify. The
`card`-type rows still fail; they are ProofNet-style conjectures (`exercise_2_12_1 … p ∣ card G`) whose original
`open Fintype …` header the released corpus replaced with the fixed four-line header. The 427 truncated prompts are a
corpus defect (STP cut the prompt at an inner `:=`), heavily concentrated in iterations 1–9.

**Sensitivity I ran.** The 846 excluded `π` rows in the two windows, with bare `π` replaced by `Real.pi`, through the
study's own `check_row`: 99.2% (839 of 846) re-verify; certified vacuous 1 of 531 (0.19%) early and 1 of 308 (0.32%) late. Adding them
to the primary contrast gives RR 0.609 (0.543–0.684), p_E 4.14%, p_L 2.52%. So this exclusion did not bias toward refutation (it slightly favoured the
hypothesis), but it removed almost every trigonometry/geometry conjecture from the measurement.

**Fix.** Build `miniF2F.lean` into the workspace and re-verify under STP's header (it is STP's environment; the
corpus's `import Mathlib` prompt header is not what was verified). Report the exclusion taxonomy above by iteration in
the report, not "did not re-verify". State plainly that the released corpus contains rows that cannot compile under its
own header (dropped per-row headers; truncated prompts) and that these are iteration-dependent. Replace "checked in
STP's own Lean environment" with the exact environment used. The plan's claim that fork 2f65ba7 differs from upstream
d1d1e4b72 only in lake files cannot be verified any more (the commit is no longer served by GitHub); say so.

### A3. Coverage: binder-less statements are never checkable, and their share is 25% early vs 1% late

**Where.** `code/vacuity.py` lines 100, 107–108 (`if not B: continue` for `decide`; swap and other tactics run with an
empty telescope and cannot succeed); `report.md` primary table, dynamics table, figure, "In plain terms".

**What.** A conjecture written as `theorem foo : ∀ x y : ℝ, 0 < x → x + y = 1 → …` has all its hypotheses in the
conclusion. The goal swap becomes `theorem v : False := by intro …` (fails), and no automation tactic proves `False`
from nothing. Such rows count in the denominator and can never count in the numerator. Share of eligible rows with
empty binders: early window 24.9%, late window 1.0%; by iteration 23.8%, 34.1%, 40.3%, 40.9%, 25.8% for iterations
1–5, then ~10% through iteration 23; 20.5% and 14.0% at iterations 25–26, under 3% from iteration 30. Of the 8,515
binder-less eligible rows, 65% begin with `∀` and 53% contain `→`. The conjecturer learned to put hypotheses in binders;
the measured "rate" rises mechanically as it does so.

**Effect.** Restricting the primary contrast to rows with binders: p_E = 5.81%, p_L = 2.59%, RR = 0.44 (0.40–0.50).
The iteration-3 peak of 8.1% is ~13.5% among checkable rows. The two phases are not comparable in coverage either
(phase 2 starts at 20% binder-less, phase 1 at 24–41%).

**Fix.** Report coverage (share of rows the certificate can examine) per iteration alongside the rate, and the rate
among checkable rows. Better, close the gap: for the automation route use `theorem v B : C := by intros; exfalso;
<tactic>`, which refutes the full hypothesis set including premises inside C and is sound (see A1 fix). For the goal
swap this is not possible (the released proof expects C), so report swap and automation separately with their
coverage.

### A4. The statement control also fell by half, and the report does not say so

**Where.** `results/tables/summary.json` → `statement_control_38_47_vs_0_9`: p_late 1.52%, p_early 2.81%, RR 0.54
(0.317–0.931), k 30 vs 60; `report.md` "Control" paragraph; `code/analysis.py` lines 165–167 compute it.

**What.** The report presents the LeanWorkbook statement rows as a fixed-pool control with "no clear trend". The
preregistered-style contrast on the same rows shows the certified rate halving from the early to the late window, with
a CI excluding 1. For a fixed pool of statements, true vacuity cannot change; what can change is (a) which statements
get proved in which iteration (STP targets unproved statements, so easy, including vacuous, statements leave the pool),
and (b) the certificate's sensitivity, because 90% of certificates come from the released proof and the prover's proof
style changes with training. Either way the control says the measurement is not stationary, which bears directly on
the within-phase "decline" and on the pass-rate-filter story.

**Fix.** Report the control contrast next to the primary one. Separate the proof-independent signal: the automation-only
rate falls from 1.1% (early) to 0.15% (late) while the swap rate falls from 3.7% to 2.5%; show both per iteration for
conjectures and statements. If the control still declines on the automation-only rate, say that the pool composition
shifts; if it declines only on the swap rate, say that detection sensitivity drifts and treat within-phase slopes as
upper bounds on real change.

### B1. Exclusions are under-reported and the "could differ systematically" caveat is too weak

**Where.** `report.md` "Validation" ("95.5% … 94.2%"), "Caveats → Exclusions".

**What.** The 427 parse errors (0.46%) are not mentioned anywhere; 388 of them are in the early window. The report's
"4.5% did not re-verify" bundles three different mechanisms (A2 table) whose iteration profiles differ in opposite
directions. The split-repair sensitivity (991 rows, 2 vacuous, 0.2%) shows that excluded rows *do* differ
systematically, in that case toward low vacuity; the `π` rows likewise (1 of 531 (0.19%) / 1 of 308 (0.32%)).

**Fix.** Replace the two percentages with the taxonomy table by window and add the two sensitivities (split repair,
`π` recovery) to the sensitivity list in "Results".

### B2. "Each time self-play restarted … jumped to 8–10%" overstates phase 1 and mislabels its start

**Where.** `report.md` "In plain terms" bullets; `results/tables/tiles.json` ("After each restart 8–10%");
`code/figures.py` line 26 (label "self-play restart" at x = 0).

**What.** Phase 1 begins at 2.8% (iteration 1), 4.2% (2), and peaks at 8.1% (3); only phase 2 starts high (8.1%,
10.0%). Iteration 0/1 is the initial start, not a restart from a re-trained model; the report's own "What was done"
says there is one restart. The figure labels x = 0 "self-play restart".

**Fix.** "Vacuity peaked early in each phase (8% at iteration 3; 10% at iteration 26) and then declined"; relabel x = 0
"self-play start"; fix the tile.

### B3. The pass-rate-filter mechanism is one of at least four candidate explanations

**Where.** `report.md` "In plain terms" ("A likely reason is STP's own filter"), "Caveats → Final training data only".

**What.** STP keeps conjectures whose pass rate lies in (0, 1/4] and discards the lowest-20% proof-length/statement-length
ratio (paper, section 3; no vacuity filter). That is a plausible mechanism, and the report hedges it. But the review
found three others that the report cannot currently rule out and does not mention: coverage (A3), false positives
concentrated early (A1), and detection drift (A4). A fourth is in the data: the conjecturer stops omitting variable
declarations (auto-bound rows fall from 26.1% (189 of 725) to 2.5% (12 of 482) of certified rows), so vacuity-by-`ℕ`-default
disappears as a side effect of learning Lean syntax, not of any filter.

**Fix.** List the candidate mechanisms; mark which the data can and cannot distinguish; move the filter explanation
out of "In plain terms" or hedge it there.

### B4. Training-weight claim: correct but presented in an uninterpretable unit; regression specification deviates from plan

**Where.** `report.md` "Training weight"; `code/analysis.py` line 154; `plan.md` 5.5.

**What.** The released `weight` is exactly `exp(−0.001 × len(target))` (correlation 1.000 on 86,640 rows), so the
regression of V on weight is a regression on proof length, as the report says. The paper's full SFT weighting also
includes a 1/#proofs term and `exp(−0.01 × verification time)`; the release carries only the length term. The plan
specified "logistic regression of V on the row's STP weight"; the code adds `C(iteration)` fixed effects (sensible, not
disclosed). "Odds ratio 1.79 per 0.1 of weight" is hard to read; the plain fact is that vacuous rows average 0.775 vs
0.637, i.e. 22% more weight.

**Fix.** Report the mean weights and the 22% difference; disclose the fixed effects as a deviation; say that the
released weight is the length term only.

### B5. NuminaMath win-rate: "the training signal favoured them" is not supported by a 0.73 vs 0.67 mean pass rate

**Where.** `report.md` "In plain terms" last paragraph and "Other corpora" bullets.

**What.** `win_rate` is `n_correct_proofs / n_proofs` for Kimina-Prover 72B during RL (dataset card). A higher pass
rate means vacuous statements were easier; whether that "favoured" them in training depends on the algorithm: with
group-normalised advantages (GRPO-style, as Kimina used) a prompt solved every time contributes zero gradient. The
sample is also conditioned on having a proof at all, so 6.2% is the rate among solved problems, as the report says in
the plain-terms text but not in the table header.

**Fix.** "Vacuous statements were solved more often (mean pass rate 0.73 vs 0.67), consistent with their being easier;
whether this translated into a training bias depends on the RL objective." Label the table column "among statements
with a model proof".

### B6. No related work

**Where.** `report.md` has no related-work paragraph.

**What.** An expert would expect: Ammanamanchi, Bhat & Biderman, "Faults in Our Formal Benchmarking" (ICML 2026,
arXiv:2606.29493), which audits miniF2F, ProofNet, FormalMath, CombiBench and ProverBench with certified checkers and
finds only one certified vacuous theorem in ~10,000 benchmark problems, against 1–6% here in *training* corpora, a
contrast worth making (their vacuity checker is also weaker than a goal swap with the released proof); the DeepSeek-
Prover V1 negation filter, which cannot remove vacuous statements because ¬(∀ B, C) requires exhibiting a witness for
B, which explains why DeepSeek-Prover-V1 still has 2.0%; Goedel-Prover-V2's deliberate negation statements (the SFT v2
exclusion); and the statement-quality literature on ProofNet#/FormalMATH. One line each.

### B7. Reproducibility: the row files the whole report rests on are untracked

**Where.** `.gitignore` line 144; `deviations.md` D3 ("will be committed in compressed form when they finish").

**What.** `results/rows/*.jsonl` (45 MB) is git-ignored and untracked at 6da94a2; `analysis.py` cannot be re-run from
the repository. The review's re-check outputs should also be kept.

**Fix.** Commit the row files compressed (and the sealed pilot), plus the review's re-check row lists, before publishing.

### B8. Units: "92,000 problems" are rows; weighted rates sit next to raw counts

**Where.** `report.md` "In plain terms" ("92,000 problems"), primary table.

**What.** 92,000 rows contain 79,722 distinct statements among eligible rows (8% within-iteration duplicates). The
primary table prints weighted rates beside raw counts (482/18,726 = 2.57%, 725/16,706 = 4.34%; weighted 2.56%, 4.28%).
The statement-level analysis samples statements with probability proportional to their number of proofs.

**Fix.** "92,000 proofs of 80,000 conjectures"; label rates "population-weighted" and give unweighted in parentheses;
one sentence on the size-biased statement sample.

### C1. Certificates are context-sensitive

Row 2797907's goal-swap certificate (`nlinarith [...]`) succeeds in env 0 (the pipeline's condition, reproduced three
times) and fails when `orig_thm` is already in the environment. Not a soundness problem (when it succeeds the kernel
checked it), but the certified rate has a small nondeterministic component; note it, and fix the REPL env for the
certificate step as the pipeline already does.

### C2. Cause coding lacks the two mechanisms the Lean data reveal

`vacuous_causes.csv` has three rows flagged "autoImplicit … default to Nat" but the report's cause table has no such
category, and no "coverage" category can exist because binder-less rows are never certified. Add "undeclared variable
defaulted to ℕ" as a category (the probe in A1 gives an exact count), and re-code the 100 after A1's fix since some of
the 100 may be false positives (47 of the 100 coded rows fall in the primary windows; one of them, row 2468022, is a confirmed false positive).

### C3. Minor

- The one-sided test uses unpooled stratum variances; the plan's "two-proportion z-test" usually pools under H0.
  Immaterial here (z = −8.6) but say which was used.
- `plan.md` and the report call 2f65ba7 "DeepSeek's fork"; the fork is `xinhjBrant/mathlib4@deepseek` and STP's own
  `lakefile.lean` adds `require REPL … xinhjBrant/repl @ deepseek`; cite it.
- SFT v2 re-verifies at 83%; "possibly because of version differences" should be checked with the same error
  taxonomy as A2 before its 1.0% is quoted.
- "Conclusions provable with all hypotheses discarded fell from 3.8% to 0.1%" is also affected by A3 (binder-less
  rows' premises are introduced and then cleared), so it measures something different in early vs late windows.
- Figure: Wilson bands are fine; add the coverage series (A3) as a second panel.

## What I checked and found correct

- **Decision rule.** `analysis.py` implements plan section 4 exactly: strata weights N_h/N_window from the full
  corpus counts (`stp_counts.csv` matches the sample's `N_iter`), variance Σ W_h² p̂(1−p̂)/n_h, delta-method CI on log RR,
  the three-way verdict with the <10-certificate guard. Refuted because RR_hi = 0.672 < 2. Recomputed independently
  from `per_iteration.csv` (table below).
- **No outcome-dependent changes.** `analysis.py` differs from its pre-outcome commit c9f1baa only by the D4 guard on
  the repair file; `vacuity.py` only by the `Mathlib.*` import rule (D2); `repair_split.py` only by the D5 `#check`
  form; `plan.md` is byte-identical to 86f1489. The deviations are logged with timestamps and are what they say.
- **Exclusion handling as preregistered** (re-verify and split failures excluded, rates per iteration in
  `per_iteration.csv`); the D2 repair sensitivity was defined before outcomes and reported (+991 rows, 2 vacuous).
- **Certificates reproduce.** 50 random certified rows: 50/50 reproduce under the pipeline's conditions (one needed env
  0, see C1); allowed axioms only. 50 random non-certified rows: 0/50 certify on re-running swap and the full
  automation portfolio. Kernel/axiom handling (`#print axioms` parsing, `sorryAx`, `Lean.ofReduceBool`) is correct;
  the REPL env numbering is used correctly; the parser's split check is a genuine guard against dropped binders.
- **Controls.** 20/20 and 0/20 reproduce in `validation_controls.csv`; the D1 note on `decide` and binder order is
  accurate.
- **Every number in `report.md` matches the results files** (table below), including the cause counts (59/21/18/1/1,
  85 local, 97 real-looking) against `vacuous_causes.csv`, whose 100 row ids equal `vacuous_sample_100.csv`.

## Recomputed numbers

| Quantity | Report | Recomputed | Source / note |
|---|---|---|---|
| p_L, p_E (weighted) | 2.56%, 4.28% | 0.02559, 0.04275 | per_iteration.csv, plan weights |
| p_L, p_E (unweighted) | — | 2.57%, 4.34% | 482/18,726; 725/16,706 |
| Primary RR (95% CI) | 0.60 (0.53–0.67) | 0.5986 (0.5334–0.6717), z = −8.64 | matches contrasts.csv |
| Statement level | 0.61 (0.54–0.68) | 0.6066 (0.5379–0.6841) | contrasts.csv |
| Unweighted | 0.59 (0.53–0.66) | 0.5887 (0.5258–0.6592) | contrasts.csv |
| Split repair | 0.60 (0.53–0.67), +991 | 0.5965 (0.5316–0.6694); 991 repaired, 2 vacuous | repair jsonl |
| Phase 1 late/early; phase 2; phase 2 vs 1 | 0.20; 0.37; 2.19 | 0.205 (0.173–0.242); 0.370 (0.333–0.411); 2.190 (2.021–2.373) | CIs absent from report |
| Peaks / final five | 8.1% (it 3), 10.0% (it 26); 0.7%, 2.1% | 0.0805, 0.1001; 0.68%, 2.13% | per_iteration.csv |
| Spearman all / p1 / p2 | −0.004; −0.89; −0.94 | −0.0038; −0.894; −0.936 | trend.csv |
| Statement control overall; ρ | 1.9%; −0.22 (p 0.12) | 174/9,427 = 1.85%; −0.225 (0.125) | statement_per_iteration.csv |
| **Statement control 38–47 vs 0–9** | **not reported** | **RR 0.54 (0.32–0.93)** | summary.json |
| Methods | 1,207; 994 / 123 / 90 | 1,207; 994 / 123 / 90 | methods.csv |
| Trivial early / late | 3.8% / 0.1% | 0.0382 / 0.0013 | methods.csv |
| Weight OR per 0.1 | 1.79 (1.73–1.85) | 1.792 (1.734–1.853); mean weight V 0.775 vs 0.637 | summary.json; weight = exp(−0.001·len) exactly |
| Re-verified / split | 95.5% / 94.2% | 95.53% / 94.17%; **plus 427 parse errors (0.46%) not reported** | rows |
| Numina; workbook; DSP1; SFTv2 | 6.2 (5.8–6.8); 2.8 (2.4–3.3); 2.0 (1.7–2.4); 1.0 (0.8–1.2); 1.2 excl. negation | 550/8,818; 134/4,809; 100/4,990; 76/7,644; 1.17% | Wilson recomputed, match |
| Numina autoformalizer / human | 7.4% of 7,051; 1.6% of 1,767 | 0.0739; 0.0164 | other_corpora.csv |
| Numina win rate | 0.73 vs 0.67, p = 2×10⁻⁸ | 0.7305 vs 0.6657; 1.8×10⁻⁸ | other_corpora.csv |
| Causes | 59 / 21 / 18 / 1 / 1; 85 local; 97 real | K2 59, K5 21, K3 18, K1 1, K4 1; 85; 97 | vacuous_causes.csv |
| Corpus size, iterations | 3,262,558; 46 conjecture iterations | 2,751,225 + 404,412 + 106,921; 46 | stp_counts.csv |
| **Primary RR, rows with binders only** | — | **0.44 (0.40–0.50)**; p_E 5.81%, p_L 2.59% | A3 |
| **Binder-less share of eligible rows** | — | **24.9% early, 1.0% late** | A3 |
| **False-positive certificates (auto-bound type flip)** | — | **18 (1.5%) of 1,207 (17 of 725 early, 1 of 482 late)** | A1 |
| **Primary RR after removing false positives** | — | **0.610 (0.543–0.685); p_E 4.19%, p_L 2.55%; k = 708 / 481** | A1 (same denominators) |
| **Certified rows with auto-bound variables** | — | **16.7% (201 of 1,207) (26.1% (189 of 725) early, 2.5% (12 of 482) late)** | A1 probe |
| **`π` rows recovered (`Real.pi`)** | — | **99.2% (839 of 846) re-verify; vacuous 1 of 531 (0.19%) early, 1 of 308 (0.32%) late; RR with them 0.609 (0.543–0.684), p_E 4.14%, p_L 2.52%** | A2 |
| Re-check 50 certified / 50 non-certified | plan 7 | 50/50 reproduce; 0/50 certify | this review |

## Re-check protocol (for the record)

1. 50 certified and 50 non-certified rows drawn with seed 20261006 from eligible primary-window rows; certificates
   rebuilt from `prompt`/`target` with the study's `parse`, `cert_ok`, `AUTO`; axioms inspected.
2. All 1,207 certified primary-window rows (plus coder-flagged 1974838): certificate rebuilt in env 0, original theorem
   added, named-argument consistency theorem compiled, `#print axioms` on it; autoImplicit probe recorded.
3. 846 excluded `π` rows in the two windows re-run through `check_row` with `π → Real.pi` (token-level substitution).
4. STP's `assets/setup/miniF2F.lean` compiled against the local mathlib; REPL started with `import miniF2F\nimport
   Aesop`; 8 random failing `π` rows and 4 `card` rows re-verified.

False-positive row ids (A1): early: 174691, 333422, 364393, 682372, 760556, 1064402, 1219391, 1280388, 1618564, 1655837, 1802958, 2088927, 2444670, 2468022, 2719539, 2720027, 2882263; late: 84593.

## Confirmation pass

Reviewer: the same independent reviewer, 2026-10-08, on commit 4563a5a (D7, D8, `analysis.py` v2 at 3e4ebf6, rewritten
`report.md`). Checked: the v2 code against D7; `vacuity.py`, `lean_repl.py` and `analysis.py` are byte-identical to
their pre-rerun commits (78e9674, 3e4ebf6), so nothing in the analysis changed after the v2 outcomes existed;
`lean/stp_env/miniF2F.lean` has the stated sha256 (b59fe463…) and its olean is in the workspace; every committed
`rows*/*.jsonl.gz` decompresses to the byte-identical `.jsonl` the tables were built from; every number in `report.md`
was recomputed from `results/rows_v2/` (table below); and a Lean spot-check on cores 0–3 with the study's own v2
`check_row` under `import miniF2F`.

**Lean spot-check.** 30 v2-certified primary-window rows (the 12 certificates v2 added, the 2 of my 18 that v2 kept, 16
random): 30/30 reproduce by the same route with only `propext`/`Classical.choice`/`Quot.sound`, and in all 30 the
pretty-printed type of `vac_thm` is identical to that of `orig_thm`, which is what makes the v2 certificate sound by
construction. 15 random non-certified rows: 0/15 certify. 8 secondary-only rows: 7/8 reproduce (`intros; exfalso; tac`
compiles, final target not `False`, primary certificate fails); the eighth timed out at re-verification on the loaded
cores (106 s against a 100 s limit), which is load, not a disagreement. The two rows I flagged that v2 kept, 1064402 and
1802958, elaborate over `ℤ` (`∀ {x y : ℤ}, 2x² + 3y² = 1 → …`; `∀ {a c b d : ℤ}, …, a² + b² = 1 → c² + d² = 1 → …`)
and are genuinely vacuous there; v1's certificate for them was unsound (over `ℕ`) but its conclusion happened to be
right. The two v1 certificates that v2 dropped although they were not type flips (375452, 2017089) are wall-clock timeouts: both have `swap_timeout: True` at 102.6 s in the v2 run, where v1's swap took 9.4 s and 80.1 s, and in my rerun the v1 form still succeeds while the v2 form exceeds 100 s. Swap-time distributions are otherwise identical between runs (early/late p95 7.6 s / 19.3 s in both) and v2 has fewer swap timeouts overall (25 vs 42), so this is run-to-run timing variance under the heavier v2 load (22 workers), not a property of the `False.elim (by …)` form; it costs 2 of 1,207 certificates. v2 also gained 23 swap certificates v1 lacked (12 in the early window), rows where the ℕ-default had made the released proof fail.

### Status of the original issues

| Issue | Status | Evidence / remaining edit |
|---|---|---|
| A1 certificate unsound under auto-bound variables | **Resolved** | `theorem v B : C := False.elim (by …)` and `by exfalso; tac` in the original context; `decide` after reverting all hypotheses; autoImplicit probe recorded; new controls 0/4 satisfiable-undeclared and 1/1 vacuous-undeclared certified in both environments. On rows eligible under both versions v2 removes 18 v1 certificates (16 of my 18 flips; the other two are genuinely vacuous over ℤ and stay) and adds 12. Spot-check above. Edit: say that the 18 removed are 16 type flips plus 2 certificates (375452, 2017089) lost to the 100 s limit in the v2 run, not 18 flips. |
| A2 environment not STP's | **Resolved, with two wording edits** | STP's `miniF2F` compiled in, `VAC_HEADER` switch, all-of-Mathlib fallback (1,152 rows; 44 re-verify, 33 pass the split check, 0 vacuous); 905 primary-window rows recovered (841 `π`, 64 other), 5 vacuous; exclusion taxonomy by window in `exclusions.csv` and the report (recomputed, matches). Edits: "33 then re-verified" → "44 re-verified and 33 became eligible"; "Mathlib at DeepSeek's pinned version" → "upstream mathlib d1d1e4b72 (DeepSeek's fork 2f65ba7 can no longer be fetched, see Caveats)". |
| A3 coverage | **Resolved as measurement; one new overclaim** | Coverage per iteration (figure lower panel), checkable-row ratio 0.45 (0.40–0.50), binder-less shares 25.5% / 1.0%, secondary certificate 0.57 (0.51–0.64). See N1 below for the sentence "So the coverage gap hid little vacuity". |
| A4 unreported control contrast | **Resolved** | 0.57 (0.33–0.97) reported with swap-only 0.65 (0.37–1.16) and automation-only 0.47 (0.18–1.19); within-phase declines read as upper bounds; "Measurement drift" caveat. |
| B1 exclusions under-reported | **Resolved** | Taxonomy table incl. 427 truncated prompts; split-repair and `π` sensitivities listed. |
| B2 "jumped to 8–10% after each restart"; figure label | **Resolved** | "peaked early in each phase, 8% in round 3 and 10% in round 26"; x = 0 now "self-play start"; tiles updated. |
| B3 single mechanism | **Resolved** | Three candidates, "None is tested here", plain-terms hedged. |
| B4 training weight | **Resolved** | Mean weights 0.776 vs 0.637 (22%), length-term-only stated, `C(iteration)` disclosed. |
| B5 NuminaMath win rate | **Resolved** | Hedged; group-normalised-advantage point made; column labelled "among statements with a proof". |
| B6 related work | **Resolved (brief)** | Optional: add that the benchmark audit found one certified vacuous theorem in ~10,000 items, against 1–6% here. |
| B7 reproducibility | **Resolved** | `rows/` and `rows_v2/` committed compressed; gz = jsonl verified. Optional: `analysis.py` reads `.jsonl`, so document `gunzip -k results/rows_v2/*.gz` or read the gz directly. |
| B8 units | **Resolved; one number wrong** | "92,000 proofs of about 80,000 distinct conjectures"; weighted/unweighted labelled; size-biased statement sample noted. See N2. |
| C1 context sensitivity | **Disclosed** | Caveat present; certificates are built in a fresh env 0. The two lost certificates are wall-clock timeouts under load, a related but distinct effect worth one clause in the caveat. |
| C2 cause coding | **Resolved; one caveat to add** | Re-coded 100 v2 rows with K6, prompt saved, 9 auto-bound rows identified, the false positive left the sample. See N6. |
| C3 minor | **Mostly resolved** | Fork cited; trivial-rate caveat added; coverage panel added. Not done, optional: state that the z-test uses unpooled stratum variances; the SFT v2 error taxonomy is in `other_corpora.csv` (978 other errors, 346 dropped-header identifiers, 238 timeouts) but not in the report. |

### New issues (all wording or single numbers; no rerun needed)

- **N1 (must edit).** `report.md` "What else changes over training → Coverage": "The secondary certificate … adds few
  certificates (ratio 0.57). So the coverage gap hid little vacuity." This does not follow. The secondary certificate
  has only automation sensitivity. Among early-window eligible rows, automation certifies 0.91% of binder-less rows
  (40 of 4,403) against 1.35% of checkable rows, where the full certificate (swap + automation) finds 5.63%. By the one
  yardstick that applies to both groups, binder-less rows are about two-thirds as vacuous as checkable rows, and the
  goal swap, which supplies three-quarters of all certificates, cannot be applied to them. So the gap plausibly hides
  of the order of 150 early certificates (4,403 × ~3.8%), which is why the checkable-row ratio (0.45) differs from the
  primary (0.61). Replace the sentence with that comparison and point to the checkable-row ratio as the better-matched
  one.
- **N2 (must edit).** Primary table: "(4.22%; 724 of 17,272)" and "(2.53%; 482 of 19,064)". 724/17,272 = 4.19% and
  482/19,064 = 2.53%. The 4.22% is the equal-iteration-weight rate from the "unweighted" sensitivity (each iteration
  weighted 1/9), not the pooled rate. Print 4.19% / 2.53%, or label the bracketed figure "equal iteration weights".
- **N3 (edit).** "The 1,152 rows that did not re-verify there were retried under all of Mathlib, and 33 then re-verified":
  44 re-verified, 33 also passed the split check (became eligible); none is vacuous.
- **N4 (edit).** "Mathlib at DeepSeek's pinned version" in "Environment" overstates what the Caveats admit; the local
  build is upstream d1d1e4b72.
- **N5 (edit).** The header says "D1-D7" and the Deviations summary stops at D7; D8 exists. `build_report_html.py` hard-
  codes "Report · 2026-10-06" while `report.md` is dated 8 October; the HTML masthead should carry the revision date.
- **N6 (edit).** Coder stability: the v1 coding judged 97 of 100 statements "real claims", the v2 coding 76 of 100, on
  two random samples of nearly the same population by the same model class. "About three in four vacuous problems read
  like genuine competition questions" (plain terms) should say the judgement varied between 76% and 97% across two
  coder runs, or drop the figure to the Causes section with that caveat. The cause distribution itself is similar
  across runs (K2 59 → 52, K5 21 → 33, K3 18 → 9), which is worth one sentence too.
- **N7 (edit).** "v2 removes 18 of v1's 1,207 certificates" should say what they are (see A1 row): 16 type flips and 2
  genuine certificates (375452, 2017089) lost to the 100 s wall-clock limit in the v2 run; otherwise a reader infers
  18 flips, which contradicts "Two of the reviewer's 18 … v2 confirms". The 12 added are rows where v1's ℕ-default
  had made the released proof fail; both counts are a timing/elaboration effect, not a change of definition.

### Recomputed numbers (v2)

| Quantity | Report | Recomputed from `rows_v2/` |
|---|---|---|
| Primary RR | 0.61 (0.54–0.68); 2.51% vs 4.13% | 0.6093 (0.5430–0.6837); p_L 0.02514, p_E 0.04126; k 482/724; n 19,064/17,272 |
| Pooled unweighted rates | 2.53%, 4.22% | **2.53%, 4.19%** (N2) |
| Sensitivities (statement, unweighted, repair +986, miniF2F-only, excl. auto-bound, checkable, secondary, swap-only, auto-only) | 0.62, 0.60, 0.61, 0.61, 0.72, 0.45, 0.57, 0.65, 0.19 | 0.617, 0.598, 0.607, 0.610, 0.715, 0.449, 0.574, 0.649, 0.189 (CIs match) |
| Phase contrasts | 0.20, 0.37, 2.23 | 0.204 (0.172–0.241), 0.367 (0.331–0.407), 2.235 (2.063–2.421) |
| Peaks / starts / final five | 2.9%, 7.8%, 8.0%, 9.8%; 0.6%, 2.1% | 0.0287, 0.0782, 0.0804, 0.0984; 0.0064, 0.0208 |
| Spearman all / p1 / p2 | −0.006, −0.90, −0.93 | −0.0061, −0.902, −0.933 |
| Coverage: binder-less early/late; it 3–4; checkable it-3 peak | 25.5%, 1.0%; 41%; 13.2% | 0.2549, 0.0104; 0.409, 0.411; 0.1324 |
| Auto-bound share of certified early/late | 186 of 724, 11 of 482 | 186/724, 11/482 |
| Control 0–9 vs 38–47; swap; auto; overall; ρ | 0.57 (0.33–0.97); 0.65; 0.47; 1.8% (172/9,594); −0.24 (0.10) | 0.5657 (0.3288–0.9732); 0.650; 0.465; 172/9,594 = 1.79%; −0.244 (0.095) |
| Routes | 1,206; 1,004 / 112 / 90 | 1,206; 1,004 / 112 / 90 |
| Trivial early/late | 3.8% / 0.1% | 0.0383 / 0.0013 |
| Weight | 0.776 vs 0.637; OR 1.81 (1.75–1.88) | 0.7760 vs 0.6373; 1.814 (1.755–1.875) |
| Exclusions (early / late): truncated, dropped header, split, other | 388/11, 4/495, 334/363, 2/67 | 388/11, 4/495, 334/363, (2+0+0)/(61+5+1) = 2/67 |
| Fallback | 1,152 retried, 33 re-verified | 1,152; **44 re-verified, 33 eligible**, 0 vacuous (N3) |
| v1→v2 on both-eligible rows; newly eligible | 18 removed, 12 added; 905 (5 vacuous) | 18 removed, 12 added; 905 (841 `π`), 5 vacuous |
| Causes | 52/33/9/2/2/2; 88 local; 76 real; 9 auto-bound | same; `vacuous_sample_100.csv` auto_bound = 9; ids match |
| Other corpora | 6.2 (5.7–6.7); 2.8 (2.4–3.3); 2.0 (1.7–2.5); 1.0 (0.8–1.2), 1.2 | 549/8,818; 134/4,806; 101/4,990; 75/7,638; 1.15% (match) |
| Numina author / pass rate | 7.4% of 7,051; 1.6% of 1,767; 0.73 vs 0.67, 2×10⁻⁸ | 0.0739; 0.0158; 0.7304 vs 0.6656; 1.7×10⁻⁸ |

### Final recommendation: **publish with edits**

The four measurement defects are fixed as D7 describes and the fixes are verified in Lean; the decision rule is
unchanged; the verdict (Refuted, RR 0.61, upper CI 0.68) stands and now rests on a sound certificate in STP's
environment with its coverage and control confounds disclosed. The remaining items are N1–N7: one sentence that
overclaims (N1), one mislabelled number (N2), and five small wording/date/consistency edits. None requires a rerun.
