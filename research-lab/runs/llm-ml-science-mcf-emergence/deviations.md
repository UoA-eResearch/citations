# Deviations log: MCF-emergence deep dive

Every departure from `plan.md`, with a timestamp (NZDT) taken from `date`. Newest last.

### D0. Preregistration (2026-10-02 12:22:52)
`plan.md` committed as 3173c01, before any checkpoint was evaluated.

### D1. Checkpoint counts, long prompts and the step-0 check (logged 2026-10-02 12:33:33)
**Checkpoint counts.** Mapping the formula targets to the nearest available branch merges some early targets
(`code/choose_checkpoints.py`, `data/checkpoints.csv`):

- Every Pythia run gets 14 checkpoints (plan: 16), from step 512 to 143,000.
- OLMo-2-0425-1B gets 16 (plan: 20); its first is at 1B tokens.
- OLMo-2-1124-7B, OLMo-7B-0424 and OLMo-1B-0724 get 20 each.
- 412 checkpoints in total. The list was fixed before any evaluation.

**Long prompts.** Some MMLU five-shot prompts exceed Pythia's 2,048-token context (up to 3,000 tokens). Rule, fixed
before any evaluation: drop the earliest shots until the prompt is at most 1,900 tokens under both the GPT-NeoX and
OLMo-2 tokenizers. This affected 15 of 500 MMLU MCF items (2–4 shots kept) and 5 of 200 MMLU CF items. Every other item
keeps five shots. The number kept is recorded per item (`shots_mcf`, `shots_cf`).

**Step-0 sanity check** (plan §6). On random-initialisation checkpoints (pythia-1b step0, OLMo-2-0425-1B step 0), MCF
accuracy is within 3 points of chance on every task and format but one. Pythia-1B five-shot ARC-Challenge is chance +3.2
points; with 500 items the binomial standard error is about 1.9 points, so this is sampling noise. Letter mass is about 0
at step 0, as expected.

### D2. Pipeline validation against OLMES (logged 2026-10-02 12:53:24)
**Final OLMo-7B-0424 checkpoint, five-shot MCF against OLMES Table 6** (`results/evals/OLMo-7B-0424-hf/main.parquet`):

| Task | This study | OLMES | Gap |
|---|---|---|---|
| ARC-C | 67.2 | 66.9 | +0.3 |
| ARC-E | 81.0 | 83.6 | −2.6 |
| CSQA | 85.8 | 85.8 | 0.0 |
| PIQA | 61.6 | 65.6 | −4.0 |
| MMLU | 48.6 | 54.4 | −5.8 |

MMLU misses the plan's 5-point criterion by 0.8 points. HellaSwag, not one of the preregistered checks, is 36.4 against
50.0. Pythia-6.9B (final checkpoint) is within 2.6 points of OLMES's Pythia-6.7B on all six tasks, all near chance.

**The investigation the plan requires.** `code/validate_mmlu.py` is a diagnostic only; the study's prompts are unchanged.
It evaluates the final OLMo-7B-0424 on 2,000 MMLU items:

| Prompt | Pooled | Averaged over subjects |
|---|---|---|
| The study's prompt | 50.7 | 53.5 |
| With OLMES's "questions about {subject}" header | 51.2 | 54.8 |

The −5.8 gap is therefore sampling error in the 500-item set (standard error about 2.2) plus pooled versus per-subject
averaging (OLMES reports the subject average). The missing header accounts for about 1 point. No pipeline bug; the
full runs go ahead with the preregistered prompts.

The HellaSwag gap is noted as a limitation. OLMES preprocesses HellaSwag contexts; this study does not. Lower MCF
accuracy on that task would make departure later or less likely.

### D3. Disk filled during the runs; prefetch bounded (logged 2026-10-02 14:08:32)
**What happened.** `code/pipeline.py` submitted every download to its thread pool at once. The pool size limited
concurrent downloads, but not how far downloads ran ahead of evaluation. Once the Hugging Face token made downloads
(about 130 MB/s) much faster than GPU evaluation, prefetched checkpoints piled up. They filled `/mnt` (524 GB in
`data/ckpt`), leaving 191 MB free around 14:00–14:10.

- One evaluation (pythia-1.4b step22000) failed to write its results file. Several downloads failed.
- Both pipelines were stopped and `data/ckpt` was deleted (re-downloadable weights only).
- Free space is back to 524 GB.
- All 33 results files written so far were checked: complete and readable.

**Fix.** The pipeline now starts download i + PREFETCH only once checkpoint i is in hand, so at most PREFETCH
checkpoints wait beyond the one being evaluated. No download starts while free disk is below 150 GB. The study design
is unchanged; failed checkpoints are simply re-run.

### D4. Primary results and exploratory analyses defined after seeing them (logged 2026-10-02 22:49:43)
**Evaluations.** All 412 planned checkpoints, plus 3 validation checkpoints, were evaluated with no failures. Each
results file has 7,200 rows. GPU work ended at 22:48.

**Primary results** (`results/tables/hypotheses.csv`, `units.csv`):

- **Who departs.** 168 units (28 runs × 6 tasks). Only 12 depart from chance in five-shot MCF, and all come from 2 runs:
  OLMo-7B-0424 and OLMo-2-1124-7B, on all six tasks each.
  - No Pythia, PolyPythias or 160M unit departs (0 of 144). Neither do the two OLMo 1B runs, despite 3–4T tokens.
- **H1 supported.** No violations. But five-shot letter mass crosses 0.5 in 167 of 168 units: by 21B tokens in 163,
  and at 754–1,069B in four OLMo-1B-0724 units. 155 of the crossing units never depart. In departing units the mass
  crossed at 4–16B tokens, and the lead time to departure is 31–244 times the tokens (median 77). (Corrected after D5;
  the numbers do not change with the pythia-2.8b re-run.)
- **H2 not testable.** The plan requires ≥ 3 runs with both events; only 2 have them.
- **H3.** The one never-crossing unit (OLMo-1B-0724, PIQA) does not depart.
- **Zero-shot indicator** (secondary). One violation (OLMo-7B-0424 PIQA, departure at 1,375B before mass crossing at
  1,937B). 103 units never cross.

**Not recoverable.** Item-level predicted labels and correct-label probabilities were not stored, only correctness and
letter mass. So continuous MCF metrics and label-bias indicators cannot be computed without re-running the evaluations.
This is a limitation, not a change.

**Exploratory analyses, defined now** (`code/explore.py`):

- **E1, within-run synchrony.** The spread, in checkpoints and tokens, of departure across the six tasks of each
  departing run.
- **E2, zero-shot versus five-shot lead time**, for the departing units.
- **E3, matched tokens.** MCF accuracy above chance at the checkpoint nearest 300B tokens: Pythia-6.9B (end of training)
  against OLMo-2-7B and OLMo-7B-0424 (mid-training), and the 1B OLMo runs at their final checkpoints.
- **E4, the CF crossover rule.** How often MCF "beats" CF at the first checkpoint only because CF accuracy is below
  chance.

### D5. Stale duplicate weights in pythia-2.8b's Hugging Face branches; 11 checkpoints re-run (logged 2026-10-02 22:52:42)
**How it was found.** Figure F1 showed a flat letter-mass line for one run. Eleven pythia-2.8b checkpoints (steps
512–46000) had identical results, and identical to the final checkpoint.

**Cause: the upstream repository** (`results/tables/weight_file_audit.csv`). Each of these 11 branches contains a
single `model.safetensors` with the same hash (ab496f1c…) in every branch; it evaluates exactly like the final
model. The step-specific weights sit alongside it:

- steps 512–22000: in sharded `model-0000X-of-00002.safetensors` files;
- steps 32000 and 46000: in `pytorch_model.bin`, which differs by step.

The downloader fetched every `*.safetensors` file, and the loader used the stale single file.

**Scope.** An audit of all 412 planned checkpoints, using hub file metadata and duplicate-result detection, found no
other run or branch with this problem.

**Fix.** `data/weight_overrides.csv` (copied to `results/tables/`) names the correct weight files for these 11
branches, and `code/pipeline.py` honours it. The invalid results were moved to `data/invalid_evals/` and the 11
checkpoints re-evaluated (completed 2026-10-02 at about 23:25; log `data/run_rerun_2p8b.log`). The step-0 and
validation results are unaffected. The corrected checkpoints trace a normal trajectory: letter mass 0.08 at step 512
rising to 0.99, CF accuracy rising from 0.30 to 0.55, MCF accuracy at chance throughout.

### D6. Independent review and the checks it led to (logged 2026-10-02 23:48:11)
**Review.** An independent reviewer agent (Fable 5.1) recommended *publish with edits*.

- It found no pipeline bug. It verified the label tokens, prompt positions, padding, the CF continuation alignment
  (0 of 4,595 fallbacks), prompt lengths, all 412 files (7,200 rows each, no duplicates), token conversions, the OLMES
  comparison, and nearly every number.
- Its major points were:
  1. The preregistered "two in a row" mass-crossing rule is fragile for OLMo-7B-0424, whose mass falls back below 0.5
     at 7 of the next 11 checkpoints.
  2. "Data and scale, not training length" overreaches; only the OLMo-2-7B versus Pythia-6.9B pair excludes training
     length.
  3. OLMo-1B-0724's letter mass is erratic and ends near zero.

**Checks added** (`code/review_checks.py`, `code/newline_check.py`, `code/newline_trajectory.py`; exploratory):

- **Sustained-crossing sensitivity** (`results/tables/review_sustained_mass.csv`). The first checkpoint after which mass
  stays above 0.5 to the end. It gives zero violations, but OLMo-7B-0424's lead times shrink to 1.4–3.9× (mass sustained
  from 125–348B against departures at 490–976B). OLMo-2-7B is unchanged at 54–160×. The two acquiring runs therefore
  disagree on whether letter mass leads. The preregistered rule remains primary.
- **Crossover anatomy** (`review_crossover.csv`). Of 78 defined crossovers, 68 are in runs that never leave chance and 6
  are at the first checkpoint of the two 7B runs. Only 4 are genuine (ARC-Easy and CSQA in the 7B runs).
- **Unit-level spread.** Final MCF accuracy above chance in units that never depart ranges from −3.8 to +4.2 points;
  the ±1.5 in the draft is the six-task average per run.
- **OLMo-1B-0724 diagnostic** (`review_olmo1b_top5.csv`). At its final checkpoint this model puts 84–100% of its
  next-token probability on a newline after "Answer:", not on " A"–" E".
  - Read after the newline (`review_newline_check.csv`), its final checkpoint scores above chance: +18.6 points on
    CSQA, +12.5 on ARC-Easy, +6.8 on ARC-Challenge; about chance on HellaSwag, MMLU and PIQA.
  - Its at-chance result under the preregistered prompt is a formatting artefact, not an absence of MCF ability.
  - E5 scores its whole trajectory in this newline variant (`results/evals_newline/`).
- **E5 result** (`results/tables/explore_newline_units.csv`, `explore_newline_trajectory.csv`). Read after a newline,
  OLMo-1B-0724 is at chance on every task at every checkpoint through 2,150B tokens. It rises only at its final
  checkpoint (3,048B): +6.8 points on ARC-C, +12.5 on ARC-E, +18.6 on CSQA. A rise at the last checkpoint cannot be
  confirmed by a next one, so no departure is counted. Its letter mass after the newline is about 0.99 from 4B.

## Correction after publication (2026-10-06 02:02 NZDT)

The lab's self-audit (`research-lab/paper/`) found a rounding error in the report's results table. For "all other
26 runs", the range of six-task mean MCF accuracy minus chance was printed as "−1.3 to +1.5". From
`results/tables/units.csv` the values are −1.25 to +1.449, which round to −1.3 to +1.4. The "+1.5" came from rounding
twice (1.449 → 1.45 → 1.5). The report is corrected; no conclusion changes.
