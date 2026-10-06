# Preregistration: did DOT's published rules become LLM-written after its Gemini drafting plan?

Lead: `legal-digital-humanities-federal-register-llm-drafting` (research-lab/leads.json). Written 2026-10-06 and
committed before any LLM-fraction estimate has been computed on Federal Register text from 2022 or later.

## What has been seen before writing (disclosure)

- **Novelty check (6 October 2026).** Web searches found no measurement of LLM-written text in Federal Register rules
  by agency. The closest work is Atkinson & O'Bryan (arXiv 2607.04543), a 10-stream pilot with no agency breakdown.
  The DOT plan was reported by ProPublica in January 2026.
- **Metadata.** All 38,833 RULE and PRORULE documents from 2019-01 to 2026-09 were fetched from the Federal Register
  API (`code/fetch_meta.py`). Counts by group and period of the non-templated documents are in
  `results/tables/counts_by_group_period.csv`. That includes the outcome window: 290 DOT and 1,973 other-cabinet
  documents in February to September 2026. Titles were used only to flag templated classes.
- **Text.**
  - GovInfo daily issues before 2026-01-01 are in `data/raw/daily/`.
  - Issues from 2026-01-01 onward (188 daily issues) are sealed in `data/sealed/daily/`, unparsed. Their hashes are in
    `data/SEALED_MANIFEST.sha256`, digest b8a470f981699b7d80d89edb6112d4efb26d7c81cb759a91a41ac158bddca053.
  - One 2019 document's XML structure was inspected. No text from 2022 or later has been analysed.

## 1. Question and hypothesis

In January 2026 DOT said it would use Google Gemini to draft most new regulations. The hypothesis, from the lead:

> In Federal Register proposed and final rules published February to September 2026, the estimated fraction of
> LLM-assisted preamble sentences for DOT, excluding templated actions, rises over its 2024-2025 baseline by at least
> 5 percentage points more than the pooled change for the other 14 cabinet departments.

## 2. Units, groups and periods

**Documents.** RULE and PRORULE documents, attributed to a cabinet department through Federal Register agency metadata,
including sub-agencies (`code/groups.py`).

**Groups.**

- **DOT:** the department and its operating administrations.
- **Comparison:** the 14 other cabinet departments, pooled.
- **Excluded:** independent agencies.

**Templated classes are removed** by a title regex, fixed now in `code/groups.py`. They include airworthiness
directives, airspace actions, instrument approach procedures, safety and security zones, special local regulations,
drawbridge operations, anchorages, restricted and danger areas, pesticide tolerances, and state implementation plan
approvals. Near-duplicate clustering (MinHash, Jaccard ≥ 0.8 on 5-shingles of the preamble) then removes any further
template families: within each family only one document per quarter is kept.

**Text.** Paragraphs (`<P>`) of the SUPPLEMENTARY INFORMATION section. Paragraphs under procedural headings are
excluded from the primary analysis and analysed separately. Procedural headings are those matching Regulatory
Flexibility, Paperwork Reduction, Executive Order, Unfunded Mandates, Congressional Review, National Environmental
Policy, Federalism, Tribal, Energy Effects, Environmental Justice, Privacy Act, Technical Standards, Information
Collection, Plain Language, Statutory and Executive Order Reviews, and List of Subjects. Paragraphs are split into
sentences with NLTK punkt.

**Periods.**

- **Human reference pool:** 2019-01 to 2021-12.
- **Pre:** 2024-01 to 2025-12.
- **Excluded:** January 2026, the month of the announcement.
- **Post:** 2026-02 to 2026-09.

## 3. Estimator

The estimator is a population-scale distributional maximum-likelihood estimate (Liang et al. 2024, 2025),
reimplemented openly.

**Vocabulary.** Words whose most frequent WordNet sense is an adjective or adverb, keeping those that occur in at least
50 sentences of the human reference and at least 20 sentences of the LLM reference.

**Model.** Each sentence is a Bernoulli occurrence vector over the vocabulary. p_H(w) and p_A(w) are estimated from
the reference corpora, with add-0.5 smoothing. The fraction α maximises
Σ_s log[(1 − α) P_H(s) + α P_A(s)] on [0, 1].

**References.** The 2019-2021 preamble paragraphs are split at random by document into three disjoint pools:

- a human reference pool (60% of documents);
- a generation pool (20%);
- a validation pool (20%).

**LLM reference.** Generation-pool paragraphs (up to 4,000 sampled per generator) go to three open models:

- Qwen2.5-32B-Instruct;
- OLMo-2-0325-32B-Instruct;
- NVIDIA Nemotron-3-Nano-Omni, served locally, with thinking disabled.

Each model performs two tasks:

- **Polish:** "Revise this paragraph from a federal rule preamble for clarity and readability, keeping every fact,
  citation and number."
- **Draft:** the model first writes a one-sentence summary, then drafts a preamble paragraph from that summary alone.

The prompts are fixed in `code/generate.py` before generation, with temperature 0.7 and top-p 0.95. Model revisions are
recorded at download. Outputs of the three models and both tasks are pooled into one LLM reference, so that no single
model's style is assumed.

## 4. Validation (before unsealing)

These checks use 2019-2021 data and generated text only.

**V1. Synthetic mixtures.** Validation-pool human sentences are mixed with held-out generated sentences at
α ∈ {0, 2, 5, 10, 25}%, 50 replicates each, at the sentence counts of the real DOT post period. The estimator must meet:

| Criterion | Requirement |
|---|---|
| Absolute bias at α ≤ 10% | under 1 pp |
| Bootstrap 95% CI coverage | at least 90% |

**V2. Power (minimum detectable effect).** Synthetic LLM sentences are injected into the 2019-2021 validation pool,
arranged into four groups with the sentence and document counts of DOT-pre, DOT-post, other-pre and other-post. The
minimum detectable DiD is computed at 80% power and a two-sided 5% level, with the document-cluster bootstrap. It is
recorded in `deviations.md` before unsealing.

If V1 fails, the estimator is fixed with 2019-2021 data only and V1 is rerun. Every change is logged.

## 5. Primary test and decision rule

**Estimand.** DiD = (α_DOT,post − α_DOT,pre) − (α_other,post − α_other,pre), with a 95% CI from a document-cluster
bootstrap (2,000 replicates; documents resampled within each group and period).

| Verdict | Condition |
|---|---|
| **Supported** | DiD ≥ 5 pp, and the 95% CI excludes 0. |
| **Refuted** | DiD < 2 pp, the upper end of the 95% CI is below 5 pp, and the V2 minimum detectable effect is at most 5 pp. |
| **Inconclusive** | Anything else. Includes every case where the minimum detectable effect exceeds 5 pp, unless the result is Supported. |

**Placebos.** The DiD is also computed for:

- **P1:** 2022 against 2019-2021 (before or at ChatGPT's release);
- **P2:** January-June 2025 against 2024 (an administration change, before any DOT announcement).

If either placebo |DiD| is 2 pp or more, the verdict is reported with that placebo as a primary caveat, and a
Supported verdict is downgraded to Inconclusive.

## 6. Secondary analyses (labelled secondary)

- Quarterly event study for DOT and the comparison group, 2019Q1 to 2026Q3.
- α by agency and quarter for every cabinet department: the monitoring series.
- Splits: final against proposed rules; deregulatory (title or abstract matching rescind, remove, withdraw or
  deregulat) against other rules.
- Procedural paragraphs analysed separately.
- A model-free cross-check: excess-vocabulary frequencies (Kobak et al. 2025 style) for marker words, against
  2019-2021 baselines.
- Leave-one-generator-out: α recomputed with each generator's outputs removed from the LLM reference.

## 7. Reporting

- The report opens with "In plain terms".
- The pre-review draft is committed before review.
- The reviewer's prompt and full review are saved in `review/`.
- The sealed outcome issues are public GovInfo files; their hash manifest lets anyone check that the analysed files are
  the ones sealed.
