# Do AI models pass on Indigenous data-governance notices?

*A within-record experiment on 221 real repository records: Local Contexts Notices and Labels, or matched
conventional rights clauses, swapped into the same metadata slot and given to three open-weight models under three
framings. 19,890 responses.*

**Verdict: Refuted, on all three preregistered hypotheses. The notices are passed on; they are not acted on.**
The lead predicted that models would omit Local Contexts elements in at least 70% of reuse advice, 25 points more
often than conventional clauses, and that an element would rarely change the advice.

- **Omission:** the models omitted a Local Contexts element in **0.5%** of responses (95% interval 0.4–0.6%),
  slightly *less* often than conventional clauses (1.7%).
- **Who omits:** almost every omission came from one model in one framing.
- **Verdict change:** in the structured "agent" framing, an element changed the stated reuse verdict **85%** of the
  time.

But post-hoc analysis shows what that change usually is: a move to *"unclear"*.

- A conventional "please contact the data providers before reuse; collaboration is welcome" becomes "permission or
  contact required: yes" in **100%** of agent summaries.
- The TK Open to Collaboration Label, the matched Indigenous-governance invitation, becomes "yes" in **2%**.
- A data use agreement becomes "yes" in 100%. TK Community Use Only, which Local Contexts describes as material
  "not, and never was, free, public, or available for everyone", becomes "yes" in 28%, and "commercial use
  allowed" in 31%.

## In plain terms

Indigenous communities and institutions can attach "Notices" and "Labels" to datasets in online repositories:
short, machine-readable statements such as *TK Community Use Only* or *Traditional Knowledge Notice*. They tell
anyone reusing the data that there are cultural rights or community rules attached. Researchers increasingly ask
AI assistants whether they can reuse a dataset. We wanted to know whether the AI passes these notices on.

We took 221 real dataset records and made copies of each with a different notice inserted: five kinds of Local
Contexts notice, three ordinary conditions (such as "non-commercial use only"), or nothing. We gave them to three
openly available AI models, asking in three different ways, and checked nearly 20,000 answers.

The models almost always mentioned the notice. Only one model, in one style of question, occasionally left it out.
So the worry that AI simply ignores these notices is not borne out.

What the models did with them is another matter. When asked to fill in a short reuse summary, a plain request to
"contact the providers before reuse" was always turned into "contact required". An Indigenous label asking for the
same kind of collaboration almost never was; the models mostly answered "unclear". A label saying the material is
for community use only still produced "commercial use allowed" about a third of the time.

The AI passes on the words. It does not reliably treat Indigenous notices as conditions in the way it treats
ordinary ones.

## What was asked

The lead (scouted 2026-10-16, University of Auckland Ancestral Futures signature research area) asked whether
open-weight models are "notice-blind". Do they omit Local Contexts elements they are given, more often than
conventional non-standard rights clauses, without the element changing their advice?

The harvest made the lead's design impossible (D1). Of the 48,353 DataCite records carrying a Local Contexts URI,
48,332 are from one repository, Neotoma, and all of those carry one element. Only 21 records anywhere else carry
one. So the study became a **within-record experiment**. Each sampled record is shown with every condition in the
same rightsList slot, after its CC BY licence, and nothing else changes.

| hypothesis | prediction | decision rule |
| --- | --- | --- |
| H1 | pooled Local Contexts omission ≥ 70% | Supported if the 95% interval's lower end ≥ 0.70; Refuted if its upper end < 0.70 |
| H2 | Local Contexts omission exceeds conventional omission by ≥ 25 points | Supported if lower end ≥ 0.25; Refuted if upper end < 0.25 |
| H3 | an element changes the agent verdict, relative to the same record without it, in ≤ 20% | Supported if upper end ≤ 0.20; Refuted if lower end > 0.20 |

## What was already known

Three searches by the scouting critic found nothing that tests whether a model surfaces a rights element it was
given, and nothing with an Indigenous-governance arm. The nearest work extracts licences into rights vocabularies
(LLM4RE, arXiv 2510.18787), or documents reference fabrication that disadvantages marginalised scholarship. The
Notices were designed to travel with data (Liggins, Hudson & Anderson 2021, *Mol. Ecol.*). DataCite documents them
as part of its schema.

## How it was done

**Records.** 200 Neotoma records drawn at random, plus all 21 non-Neotoma records (Pacific research stations at
Gump and Tetiaroa, iPlaces, Zenodo). Existing Local Contexts elements were removed, and long lists were capped
identically across conditions. A disjoint 20 Neotoma records formed a pilot set.

**Conditions** (wording and URIs from localcontexts.org):

- *Local Contexts:* TK Open to Collaboration (Neotoma's real form), TK Non-Commercial, BC Notice, TK Notice, TK
  Community Use Only, and TK Open to Collaboration without its URI.
- *Conventional:* a CC BY-NC licence, "A data use agreement is required before reuse", and "Users are asked to
  contact the data providers before reuse; collaboration is welcome".
- *None.*

Matched pairs: TK NC against CC BY-NC (the same restriction), and TK CB against the contact clause (the same
invitation).

**Models and framings.** Three models at greedy decoding, up to 1,100 new tokens, all run locally on vLLM. No record went to a
third-party model for generation or scoring. The pilot adjudication was done by the agent running the study,
so those 200 responses, which quote public metadata, did pass through the agent's own model service:

- Qwen3-32B (non-thinking mode);
- Mistral-Small-24B-Instruct-2501;
- OLMo-2-1124-13B-Instruct.

Three framings:

- a researcher asking "can I reuse this, and under what conditions?";
- an agent producing a JSON summary with fields for commercial use and for whether permission or contact is
  required;
- "list every condition, notice or restriction".

221 records × 10 conditions × 3 framings × 3 models = 19,890 responses. 0 errors; 14 truncated.

**Scoring.** A preregistered lexical rule per condition: does the response name the element or state what it asks?
Before the main set was scored, I adjudicated 200 pilot responses, blind to the rule (D4). All 200 mentioned the
element, and the rule agreed on every one (sensitivity 1.00). Specificity comes from each pattern's hit rate on
responses with no element: 1–2% for most patterns, 7–8% for the two non-commercial ones. A name-only secondary
measure guards against that.

**Operational deviations** (D2, D3), all before any element-condition response was read:

- Two model servers failed to start in the first GPU window (one a context-length mismatch).
- One script lacked a package.
- The generation cap was raised from 700 to 1,100 tokens after a quarter of the first pilot responses hit it.

## Results

### H1 and H2: Refuted. The elements are passed on, almost always

| | Local Contexts omission | conventional omission |
| --- | --- | --- |
| all (H1, H2) | **0.5% (0.4–0.6%)** | 1.7% |
| difference, Local Contexts minus conventional (H2) | **−1.2 points (−1.5 to −1.0)** | |
| Qwen3-32B | 0.0% | 0.0% |
| Mistral-Small-24B | 0.0% | 0.2% |
| OLMo-2-13B | 1.4% | 5.0% |
| researcher framing | 1.4% | 4.8% |
| agent / direct framing | 0.0% / 0.0% | 0.4% / 0.0% |
| name-only measure (secondary) | 0.5% | 4.0% |
| excluding the 14 truncated responses | 0.5% | 1.7% |

Every omission of a Local Contexts element comes from OLMo-2-13B's researcher answers. In that cell it drops the
BC Notice 11% of the time and a CC BY-NC licence 42%. When a Local Contexts element is mentioned, it is named as
such (Local Contexts, TK, BC, Indigenous or cultural rights) 99.9% of the time. Removing the localcontexts.org URI
barely matters (TK CB omission 0.6% with it, 1.0% without).

![Omission rate by element and model](results/figures/F1_omission.png)

### H3: Refuted. Elements change the verdict, mostly to "unclear"

In the agent framing an element changes at least one of the two verdict fields, against the same record and model
without it, in **85.3% (84.1–86.4%)** of cases (50 of 3,315 pairs unparseable). The direction of the change is the
substantive result, described post hoc below.

### Post hoc: conditions become "required", Local Contexts elements become "unclear" (D6)

Agent framing, "permission_or_contact_required" (F2):

| element | yes | unclear | no |
| --- | --- | --- | --- |
| contact providers; collaboration welcome | **100%** | 0% | 0% |
| data use agreement required | **100%** | 0% | 0% |
| TK Community Use Only | 28% | 64% | 8% |
| TK Open to Collaboration | **2%** | 64% | 33% |
| TK Notice | 3% | 68% | 29% |
| BC Notice | 2% | 80% | 18% |
| no extra element | 4% | 6% | 91% |

![The agent verdict on permission or contact, by element](results/figures/F2_contact_verdict.png)

Agent framing, "commercial_use_allowed":

| element | no | unclear | yes |
| --- | --- | --- | --- |
| TK Non-Commercial | **98%** | 2% | 0% |
| CC BY-NC licence | **91%** | 1% | 8% |
| TK Community Use Only | 13% | 56% | **31%** |
| no extra element | 6% | 9% | 86% |

Read against what each element says:

- **The matched restriction is honoured equally.** TK Non-Commercial and a CC BY-NC licence both produce "no
  commercial use" over 90% of the time.
- **The matched invitation is not.** The conventional request to contact the providers is read as a requirement
  every time, by every model. The TK Open to Collaboration Label, whose template text says the community "is open
  to future engagement, collaboration, and partnership", is read as one 2% of the time. Arguably the conventional
  request is over-read and the Label under-read; either way, the same kind of ask gets different treatment.
- **The strongest restriction is often softened.** Local Contexts' template for TK Community Use Only says the
  material "has specific conditions for circulation within the community" and "is not, and never was, free,
  public, or available for everyone". Models answer "commercial use allowed: yes" in 31% of agent summaries:
  OLMo-2 28%, Mistral 7% and Qwen3 5% chose "no", with the rest "unclear" or "yes".
- **The Notices are acknowledged, not translated into conditions.** The BC and TK Notices say that "appropriate
  permissions may need" to be sought; models mostly answer "unclear", and 18–29% answer "no".
- **Prose framings** (lexical, unvalidated). Local Contexts elements are described as "not legally binding" or
  similar in 3–12% of responses that mention them (BC Notice 12%, TK CB 12%). The conventional contact request is
  described that way 30% of the time, which is accurate for a request.

A separate finding: in the responses with no extra element, where the record carries only CC BY, **OLMo-2-13B
attaches NonCommercial, NoDerivatives or ShareAlike terms to the licence in 51% of its prose answers**. Qwen3 does
so in 4%, Mistral never. The pilot adjudication noted further characterisation errors: "BC" read as British
Columbia, TK Community Use Only taken to mean "the paleoecology research community", and a CC BY-NC licence listed
with "commercial use allowed: yes".

## What this does and does not show

**It shows** that three current open-weight models, given a repository record's metadata, almost always pass on a
Local Contexts Notice or Label, and by name. The "notice-blind" hypothesis is refuted for this setting. It also
shows, post hoc, that in a structured reuse summary these models treat Local Contexts elements as uncertain far
more often than conventional clauses that ask the same kind of thing.

**It does not show**:

1. **Hosted assistants.** These are three open-weight models at greedy decoding, not the hosted assistants most
   researchers use.
2. **Other presentations.** The element sits in a metadata JSON. A landing page, a PDF, or a record with many
   fields may be harder.
3. **Whether "unclear" is the right answer.** For some elements it is defensible. What each element asks is taken
   from Local Contexts' published text, but whether a given answer respects it is a normative judgement this lab
   has not made with the communities concerned. That engagement is a care point, not a precondition (plan §8).
4. **Real-world element variety.** Element types other than Neotoma's are inserted experimentally, using Local
   Contexts' own names, because almost no real records carry them.
5. **Validated post-hoc measures.** The verdict tables use the models' own structured fields, but the
   "not binding" and invented-term counts are lexical and were not validated.

## Scope and care

The study used only public repository metadata and never asked a model to produce or elaborate Indigenous
knowledge; only reuse statements were scored. The results describe models, not the communities, institutions or
repositories involved.

One data-quality point is worth passing to Neotoma and Local Contexts. Neotoma's element pairs the name of a TK
*Label* ("TK Open to Collaboration (TK CB)") with the URI of the Open to Collaborate *Notice*, a different
instrument.

## Process and deviations

Six logged deviations (`deviations.md`):

- D1: within-record design; no LLM judge, with agent adjudication of the pilot instead.
- D2: GPU-stage failures: a start timeout, a context-length mismatch, a missing package.
- D3: generation cap raised to 1,100 tokens.
- D4: pilot adjudicated; scorer frozen unchanged; name-only secondary added.
- D5: a bootstrap relabelling bug, fixed before any result was printed.
- D6: post-hoc verdict and wording checks.

Commits: plan 1c953ad, scorer frozen 3f119ce, results 7d6b7a7.

## Reproducing it

    venv/bin/python code/harvest_lc.py          # all DataCite records with a Local Contexts URI
    venv/bin/python code/build_corpus.py        # 221 + 20 records x 10 conditions
    venv/bin/python code/test_scoring.py        # 20 checks of the scorer and decision rules
    bash code/run_gpu_mistral.sh                # local vLLM, three models (stops and restarts the host's vllm)
    venv/bin/python code/pilot_sample.py sample # then adjudicate; `compare` checks the scorer
    venv/bin/python code/analysis.py main       # H1-H3 -> results/tables/primary_main.json
    venv/bin/python code/supplementary.py       # post-hoc verdicts and wording
    venv/bin/python code/figures.py

Released: the corpus (public metadata, `results/corpus/`), prompts, every response, every score, the pilot
adjudication, and all code. Model weights are pinned by revision in `code/download_models.py`.
