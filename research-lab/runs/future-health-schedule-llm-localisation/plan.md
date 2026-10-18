# Preregistration: does a medical-capable LLM know which medicines New Zealand funds?

Lead: `future-health-schedule-llm-localisation` (Future Health). Written 2026-10-18, before any question was
generated or any model was queried.

**Examined beforehand (no model output):**
- the Pharmac Pharmaceutical Schedule XML, October 2026, already downloaded for the medicine-access-lag study. It has
  958 chemicals in nested ATC sections with formulations, brands, packs and 1,451 rule elements;
- one response each from the PBS API v3 `/schedules` and `/items` endpoints: 13 schedules, 191,591 item records.

**Novelty** (search 2026-10-18). The closest work is a Korean reimbursement-eligibility benchmark for anticancer
drugs (JMIR 2026). It found that models fill information gaps rather than abstain. No benchmark of New Zealand or
Australian funding rules was found.

## 1. Question and hypotheses

How accurately does a general LLM answer factual questions about New Zealand's funded medicines, compared with the same
kinds of question about Australia's larger scheme? Does reading the jurisdiction's own document fix it? Does the model
invent eligibility criteria?

**The model.** Nemotron 3 Nano Omni (the lab's locally served open model, temperature 0, JSON-constrained answers).
It is the only model the lab can serve without displacing the user's server. The study is a single-model case study,
and the report says so.

**Hypotheses:**
- **H1 (localisation gap).** Zero-shot accuracy on NZ questions is lower than on matched AU questions. The measure is
  the NZ − AU accuracy difference, with a chemical-cluster bootstrap (2,000 resamples, seed 20261018).
  - Supported: the upper bound is < 0.
  - Refuted: the lower bound is ≥ 0.
  - Inconclusive otherwise.
- **H2 (retrieval closes it).** With retrieval from the jurisdiction's own document, at least half the zero-shot gap
  closes. The measure is the closure share, 1 − gap_retrieval / gap_zero-shot.
  - It is evaluated only if H1 is Supported; otherwise H2 is Inconclusive.
  - Supported: the lower bound is ≥ 0.5.
  - Refuted: the upper bound is < 0.5.
- **H3 (fabrication).** Zero-shot, the model affirms a plausible but absent eligibility criterion for at least 20% of
  NZ counterfactual-criterion items.
  - Supported: the Wilson lower bound is ≥ 0.20.
  - Refuted: the upper bound is < 0.20.

## 2. Sources and the item universe

**Sources:**
- **NZ:** Pharmac Schedule XML, Community section (B):
  - October 2026, for the answers;
  - October 2025, for the stability rule.
- **AU:** PBS API v3 (public unregistered-user key, read at run time, never stored):
  - `items` and `restrictions` for the October 2026 schedule, for the answers;
  - the earliest available schedule, for the stability rule.

**Matching.** Chemicals are matched across jurisdictions by lower-cased INN name, after removing salt words (the
medicine-access-lag study's normaliser). Only chemicals present in both jurisdictions are used, so the comparison is
like-for-like.

**Stability rule.** An item's answer must be the same in both the earlier and the later edition in its jurisdiction.
This applies symmetrically, so that recent listing changes do not masquerade as localisation errors.

## 3. Question families (`code/generate.py`)

Each item is a yes/no question with a known answer from the structured data.

- **(a) Listed presentation:** "Is [chemical] [formulation] listed for subsidy on the [New Zealand Pharmaceutical
  Schedule / Australian PBS]?"
  - Positives: the jurisdiction's listed formulations.
  - Negatives: formulations of the same chemical listed in the other jurisdiction but absent from this one in both
    editions.
  - 150 positives and 150 negatives per jurisdiction.
- **(b) Restriction:** "Does subsidy of [chemical] [formulation] require [a Special Authority / an Authority Required
  prescription]?"
  - The answer comes from the structured restriction flags.
  - 100 yes and 100 no per jurisdiction.
- **(d) Counterfactual criterion:** "Under the [Special Authority / PBS restriction] criteria for [chemical], is
  [criterion] one of the criteria?"
  - The criterion is a sentence from another chemical's restriction in the same ATC level-2 group, confirmed absent
    from this chemical's text by normalised string match. Answer: no.
  - 100 such items per jurisdiction.
  - Paired with 100 true criteria (a sentence from the chemical's own restriction; answer: yes) as controls.

**Sampling.** Items are sampled at random (seed 20261018), with at most 3 per chemical per family. The plan's
"single-criterion" family is dropped: its scoring needs free-text grading. The WHO eEML reference set is descoped.

## 4. Conditions and scoring (`code/run.py`, `code/analysis.py`)

**Conditions:**
- **zero-shot:** the question alone;
- **retrieval:** the question with the top 3 passages from a BM25 index over the jurisdiction's own document, one
  passage per chemical rendering its listed formulations, restriction flags and criteria text;
- **retrieval with abstention:** retrieval plus the option "not stated".

**Answers.** JSON-constrained: yes / no (/ not stated). Scored by exact match.

**Analysis:**
- **Primary:** H1 and H2 on families (a) and (b) pooled; H3 on family (d) negatives.
- **Reported alongside:**
  - accuracy by family, condition and jurisdiction;
  - the abstention rate, and accuracy among answered items;
  - the true-criterion control accuracy (a model that says "yes" to everything is not rewarded).

## 5. Validation before the main runs

A random 200 of the generated items (100 per jurisdiction) are checked by hand against the source documents (Schedule
PDF/XML, PBS website text).

**Abort rule.** If the answer key is wrong for more than 5% of them, the generator is fixed once and a fresh 200 are
checked. If it fails again, the study reports the benchmark as not constructible from these open data.

## 6. Threats and care

- **One model.** Results describe this model, not "medical AI".
- **Training staleness.** The model's knowledge predates the October 2026 editions. The stability rule removes
  12-month changes, not older ones. The direction of any bias is the same in both jurisdictions.
- **Prompt sensitivity.** One fixed template per family and jurisdiction, with the jurisdiction's own terminology
  ("Special Authority" / "Authority Required"). A paraphrase check on 100 items is reported.
- **No clinical advice** is evaluated. These are facts about funding rules, and the report says so.
