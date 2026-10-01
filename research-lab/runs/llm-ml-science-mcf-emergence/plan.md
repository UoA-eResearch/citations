# Preregistration: does answer-letter probability mass predict when a language model learns multiple-choice format?

Lead: `llm-ml-science-mcf-emergence` (research-lab/leads.json). Written 2026-10-02 and committed to git before any model
checkpoint was evaluated.

## Probes made before writing

- **Literature search** (§1).
- **Hugging Face listings.** Checkpoint branch names and file sizes for every run in §2. Download speed: about 3.5 MB/s
  per connection, 27 MB/s with 8.
- **Benchmarks.** The six datasets load. Counts and fields were read; no model was run on them.
- **Tokenizers.** " A" to " E" are single tokens in the GPT-NeoX, OLMo-1 and OLMo-2 tokenizers.
- **No model output** of any kind was computed before this plan was committed.

**Prior knowledge (disclosed), and the reason for added runs.** OLMES (Gu et al. 2024, Tables 6–7) reports that the
*final* Pythia-1B and Pythia-6.7B checkpoints score near chance in multiple-choice format (MCF) on ARC, CSQA,
HellaSwag, MMLU, OBQA and PIQA. OLMo-7B-0424, by contrast, starts answering in MCF after about 400B training tokens
(OLMES, Figure 1).

The lead's runs (Pythia 410M–6.9B, PolyPythias, OLMo-2) are kept. But Pythia runs are likely never to leave chance, so
the timing hypothesis could be untestable on them. Two OLMo runs with dense public checkpoints are therefore added:
OLMo-7B-0424 and OLMo-1B-0724.

Every later departure goes to `deviations.md` with a timestamp taken from `date`.

## 1. Background and gap

- **The two formats.** Language-model benchmarks are scored either in cloze format (CF: the likelihood of each answer's
  text) or in MCF (options labelled A, B, C…, scored by the probability of the label).
  - Weak or early models answer MCF at chance even when CF shows they know the answer.
  - OLMES therefore takes the better of the two formats, and leaderboards that score small models in MCF may be ranking
    format skill, not knowledge.
- **Closest work.**
  - Wiegreffe et al. (2024, arXiv:2407.15018) localise answer-symbol binding in one OLMo-7B run.
  - Wiegreffe et al. (2023, EMNLP) show that more probability mass on answer choices does not always mean higher
    accuracy.
- **The gap.** No study was found that describes the onset of MCF ability across model scales and random seeds, or that
  tests a cheap leading indicator for when a checkpoint's MCF scores become meaningful.

## 2. Runs and checkpoints

| Group | Runs | Checkpoints |
|---|---|---|
| Lead: Pythia scale | pythia-1b, -1.4b, -2.8b, -6.9b | 16, log-spaced in step from 512 to 143,000 |
| Lead: PolyPythias 410M | pythia-410m (seed 0) and pythia-410m-seed1 … seed9 | the same 16 steps |
| Lead: OLMo-2 | OLMo-2-0425-1B, OLMo-2-1124-7B (stage 1) | 20, log-spaced in tokens from about 4B to the end of stage 1 |
| Floor: Pythia 160M | pythia-160m and pythia-160m-seed1 … seed9 | the same 16 steps |
| Added (see above) | OLMo-7B-0424-hf, OLMo-1B-0724-hf | 20, log-spaced in tokens as for OLMo-2 |

- **Checkpoint choice.** The target values are fixed by formula. Each is mapped to the nearest available branch
  (`code/choose_checkpoints.py`), and the list is written before any evaluation.
- **Tokens.** Pythia trains on 2,097,152 tokens per step. OLMo branch names give tokens directly.

## 3. Evaluation

**Tasks and items** (fixed random subsets, seed 0):

| Task | Split | Options |
|---|---|---|
| ARC-Easy | test | 3–5, mostly 4 |
| ARC-Challenge | test | 3–5, mostly 4 |
| CommonsenseQA | validation | 5 |
| PIQA | validation | 2 |
| HellaSwag | validation | 4 |
| MMLU | test, all subjects pooled | 4 |

- **Item counts.** 500 items per task for MCF and 200 per task for CF.
- **Shots.** Five fixed examples from each task's training or dev split. For MMLU, the five dev examples of the item's
  own subject.

**MCF prompt** (OLMES style):

```
Question: {question}
 A. {option 1}
 B. {option 2}
 ...
Answer: {label}
```

- The five shots come first, separated by blank lines, then the test item ending at `Answer:`.
- HellaSwag uses the context as the question. PIQA uses the goal.
- At the next position, with the full-vocabulary softmax:
  - **Letter mass** is the total probability on the item's valid labels (" A", " B", …).
  - **MCF prediction** is the valid label with the highest logit.

**CF:** the same five shots in cloze form. Each option is scored by its summed log-probability per character
(character-normalised).

**Zero-shot control:** MCF accuracy and letter mass with no shots, on the same 500 items.

**Numerics.** Models run in their training dtype on GPU: fp16 for Pythia, bf16 for OLMo.

## 4. Quantities (per unit = run × task, five-shot unless stated)

- **Chance.** The mean over items of 1/(number of options).
- **Departure step.** The first checkpoint at which MCF accuracy exceeds chance + 0.05 *and* stays above it at the next
  checkpoint. It is undefined if this never happens.
- **Mass crossing step.** The first checkpoint at which mean letter mass exceeds 0.5 *and* stays above it at the next
  checkpoint. It is undefined if this never happens.
- **Crossover step.** The first checkpoint at which MCF accuracy exceeds CF accuracy, with persistence as above.
- **Units of time.** All steps are converted to training tokens.

## 5. Hypotheses (from the lead) and decision rules

**H1 (necessity).** In no unit does MCF departure occur at a strictly earlier checkpoint than the mass crossing. This
includes units that depart without the mass ever crossing.

| H1 verdict | Condition |
|---|---|
| Supported | no violation |
| Contradicted | violations in ≥ 2 units and in ≥ 10% of the units that depart |
| Inconclusive | otherwise |

**H2 (prediction).** Among units with both a departure and a mass crossing, the Spearman ρ between log tokens at mass
crossing and log tokens at departure is ≥ 0.7. The interval is a 95% bootstrap over *runs* (2,000 resamples), because
units of one run are dependent.

| H2 verdict | Condition |
|---|---|
| Not testable | fewer than 8 such units, or fewer than 3 runs |
| Supported | ρ ≥ 0.7 and the lower bound > 0 |
| Contradicted | upper bound < 0.7 |
| Inconclusive | otherwise |

**H3 (never crossing means never departing).** No unit whose letter mass never exceeds 0.5 departs from chance.
Reported as the count of such units, out of all never-crossing units.

**Secondary:**

- the lead time (tokens at departure ÷ tokens at mass crossing);
- the spread of departure and crossing steps across the ten PolyPythias 410M seeds, and the ten 160M seeds;
- whether zero-shot letter mass is a better indicator, using the same rules;
- CF–MCF crossover steps;
- MCF accuracy at the last checkpoint of each run.

## 6. Validation before the main runs

- **Pipeline check.** On the final checkpoints of OLMo-7B-0424 and Pythia-6.9B, five-shot MCF accuracy on ARC-C, ARC-E,
  CSQA, MMLU and PIQA must be within 5 points of OLMES Tables 6–7 (Pythia-6.7B there). A larger gap is logged and
  investigated before the full runs.
  - CF is reported alongside but not required to match. OLMES chooses a length normalisation per task; this study uses
    per-character normalisation throughout.
- **Sanity check.** A step-0 (random-initialisation) checkpoint must give MCF accuracy within 3 points of chance on
  every task.

## 7. Not done (scope)

The lead's plan also listed a LoRA "format-only" fine-tuning experiment and permuted-letter controls. These are left
out to keep the study to roughly one day of GPU time.

## 8. Review and reporting

- An independent reviewer agent checks code, deviations and the draft before any verdict is stated.
- The report opens with an "In plain terms" section.
- Per-checkpoint evaluation tables are committed.
