# Preregistration — Do AI models pass on Indigenous data-governance notices?

*A within-record experiment: real repository metadata, with Local Contexts Notices and Labels or matched
conventional rights clauses swapped into the same slot, given to three open-weight models under three framings.*

Committed before any model output was generated. Examined beforehand, deliberately, because none involves an
outcome: the DataCite records carrying a Local Contexts element, their publishers and element types, Local
Contexts' published wording, and the corpus built from them. All code is committed with this plan; the scorer has
been checked only on crafted text.

## 1. The question

Local Contexts Notices and Labels are machine-readable elements that Indigenous communities and institutions attach
to data records, designed to travel with the data into reuse. When a researcher or an AI agent asks a model about
reusing a dataset, does the model pass the element on? Is it less likely to do so for an Indigenous-governance
element than for a conventional rights clause asking the same thing?

### 1.1 Hypotheses

Each response is scored for whether it **mentions** the inserted element, by its name or by what it asks (§5).
Omission = no mention.

- **H1 (primary).** The pooled omission rate for the five Local Contexts conditions, across models and framings,
  is ≥ 70%. Supported if the 95% interval's lower end is ≥ 0.70; Refuted if its upper end is < 0.70; Inconclusive
  otherwise.
- **H2.** Local Contexts omission exceeds conventional-clause omission by ≥ 25 percentage points. Supported if the
  interval's lower end is ≥ 0.25; Refuted if its upper end is < 0.25; Inconclusive otherwise.
- **H3.** In the agent framing, a Local Contexts element changes the model's stated reuse verdict (commercial use
  allowed; permission or contact required) relative to the same record without it in ≤ 20% of cases. Supported if
  the interval's upper end is ≤ 0.20; Refuted if its lower end is > 0.20; Inconclusive otherwise.

Intervals: 2,000 bootstrap resamples of records, each keeping all its conditions, framings and models.

### 1.2 How this differs from the lead, and why

The lead proposed three arms of real records: (A) 400 with a Local Contexts element, (B) 400 with a conventional
non-standard clause, (C) 400 plain, with arm A stratified so no publisher exceeds 50%. The DataCite harvest
(2026-10-16, all 48,353 records whose rightsList carries a Local Contexts URI) makes that impossible:

- 48,332 of the 48,353 are from one repository, the Neotoma Paleoecology Database.
- All Neotoma records carry one element, "TK Open to Collaboration (TK CB)". That is a TK *Label* name, with a URI
  pointing to the Open to Collaborate *Notice* page.
- Only 21 records outside Neotoma carry any Local Contexts element: Pacific research stations (Gump, Tetiaroa),
  iPlaces and Zenodo.

Real-world variation in element type is therefore almost nil, and any arm-A versus arm-B contrast would compare
Neotoma with other repositories. The design becomes a **within-record experiment**. Every sampled record is shown
with each condition swapped into the same rightsList slot, after its open licence, and nothing else changes.
Element type is manipulated rather than inherited from one publisher, and record content is held fixed across the
contrast.

Matched pairs isolate framing from content:

- TK Non-Commercial against a Creative Commons NC licence (the same restriction);
- TK Open to Collaboration against "contact the providers; collaboration is welcome" (the same invitation).

Logged as D1, with the other changes:

- Real arm-B records are not used.
- There is no LLM judge (§6).
- The pilot uses separate records.

## 2. What is already known

The scouting critic and three searches found nothing that tests whether a model surfaces a rights element it was
given, and nothing with an Indigenous-governance arm. The closest work extracts licences into rights vocabularies
(LLM4RE, arXiv 2510.18787), or documents models fabricating references in ways that disadvantage marginalised
scholarship. DataCite documents Local Contexts elements as part of its schema. Liggins, Hudson & Anderson (2021,
*Mol. Ecol.*) describe the Notices as designed to travel with data.

## 3. Materials

| item | source | vintage |
| --- | --- | --- |
| Local Contexts records | DataCite REST, `rightsList.rightsUri:*localcontexts*`, cursor-paged | 48,353 records, sha256 3d034def…, 2026-10-16T13:22Z (`data/raw/datacite/VINTAGE_lc.txt`) |
| non-Neotoma records | the 21 outside the 10.21233 prefix, one query | 2026-10-17 |
| element wording | localcontexts.org Notice and Label pages | 2026-10-17 (`data/raw/localcontexts/`) |
| models | Qwen3-32B (rev 9216db57), OLMo-2-1124-13B-Instruct (rev 3a5c85ba), Mistral-Small-24B-Instruct-2501 (rev 9527884b), bf16 | Hugging Face, ungated |

**Corpus** (`code/build_corpus.py`, seed 20261017): 200 Neotoma records drawn at random, plus all 21
non-Neotoma records (main set). A disjoint 20 Neotoma records form the pilot set. From each record, any
existing Local Contexts element is removed. Long lists (related identifiers > 10, creators > 15, locations > 5,
subjects > 15) and abstracts > 1,500 characters are capped identically across conditions. That gives 221 records ×
10 conditions in the main set.

**Conditions** (wording and URIs from localcontexts.org):

| condition | element appended to rightsList |
| --- | --- |
| NONE | — |
| LC_CB | "TK Open to Collaboration (TK CB)", localcontexts.org/notice/open-to-collaborate/ (Neotoma's real form) |
| LC_NC | "TK Non-Commercial (TK NC)", localcontexts.org/label/tk-non-commercial/ |
| LC_BC | "Local Contexts Biocultural (BC) Notice", localcontexts.org/notice/bc-notice/ |
| LC_TK | "Local Contexts Traditional Knowledge (TK) Notice", localcontexts.org/notice/tk-notice/ |
| LC_CO | "TK Community Use Only (TK CO)", localcontexts.org/label/tk-community-use-only/ |
| CV_NC | "Creative Commons Attribution Non Commercial 4.0 International", creativecommons.org BY-NC 4.0 |
| CV_DUA | "A data use agreement is required before reuse." |
| CV_CONTACT | "Users are asked to contact the data providers before reuse; collaboration is welcome." |
| LC_CB_NOURI | LC_CB without its URI (is the localcontexts.org link the cue?) |

**Framings** (`code/prompts.py`, verbatim in the code):

- *researcher*: "Can I reuse this data … and under what conditions?";
- *agent*: a JSON reuse summary with fixed fields;
- *direct*: "List every condition, notice or restriction … that affects how the data may be reused".

**Generation** (`code/generate.py`, `code/run_gpu.sh`):

- vLLM on the local A100, greedy decoding, at most 700 new tokens.
- Qwen3 in non-thinking mode, each model's own chat template, no system prompt added.
- Main set: 221 × 10 × 3 × 3 = 19,890 responses. Pilot: 1,800.
- **All inference is local. No record is sent to a third-party API.**

## 4. Outcomes

- **Mention** (`code/score.py`): a lexical rule per condition. It matches the instrument's name (Local Contexts,
  Traditional Knowledge/TK, Biocultural/BC, Indigenous, cultural rights or protocols) or the element's content: a
  non-commercial restriction (not "commercial and non-commercial purposes"), a request to contact or collaborate, a
  community-only restriction, or a data use agreement. A verbatim echo of the metadata does not count.
- **False-positive rate:** each pattern applied to the NONE responses.
- **Named as Indigenous governance:** among Local Contexts mentions, the share that use the instrument's name
  rather than only its content.
- **Agent verdict:** the JSON fields commercial_use_allowed and permission_or_contact_required, normalised to
  yes/no/unclear; unparseable responses are excluded and counted.

## 5. Validation of the scorer, before the main set is scored

The lead specified LLM judges plus 300 human-adjudicated responses. There is no human adjudicator in this lab, and
an LLM judge would add a model's own blind spots and conflict with keeping inference local. So:

1. **Pilot first.** The scorer is applied to the pilot set's 1,800 responses.
2. **Adjudication.** I (the agent running the study) adjudicate a stratified random 200 of them: for each, does the
   response mention the inserted element? Each response is judged with the condition label visible, as a human
   coder would be.
3. **Sensitivity and specificity** of each pattern are estimated. Patterns may be revised **only on pilot
   evidence**, and are then frozen and committed before any main-set response is scored. The pilot is not part of
   any estimate.
4. **Report the correction.** The report gives the pilot's sensitivity and specificity and the main estimates
   corrected for them (Rogan–Gladen) as a sensitivity analysis.

The main-set generations exist before the scorer is frozen, but no main-set response is read or scored until it is.

## 6. Also reported

- Omission by condition, model and framing.
- The matched pairs (TK NC vs CC NC; TK CB vs contact clause) and the URI cue (LC_CB vs LC_CB_NOURI).
- Neotoma against non-Neotoma base records.
- The false-positive rates.
- Truncated responses (finish = length).

## 7. Threats to validity

1. **Lexical scoring** can miss paraphrase or credit an incidental word. The pilot validation and the
   false-positive rates measure both.
2. **"Mention" is the minimum, not "respect".** A model can name an element and still advise reuse contrary to it.
   H3 and the agent fields look at the verdict, not at whether it is right. What a Notice asks is set by Local
   Contexts' published text, not by this lab.
3. **Three open-weight models** at greedy decoding are not the hosted assistants most researchers use.
4. **The rightsList slot and the JSON presentation** are one way an element reaches a model; a landing page or a
   PDF is another.
5. **The conventional clauses lack URIs** where the Local Contexts elements have them (as in real records).
   LC_CB_NOURI measures how much the URI matters.
6. **Neotoma dominates the base records** (200 of 221), but the element is manipulated, so this limits the range of
   record types, not the contrast.

## 8. Scope and care

The study uses only public repository metadata and never asks a model to produce or elaborate Indigenous
knowledge; the only outputs scored are reuse statements. The elements' meaning is taken from Local Contexts'
published definitions. Engagement with Local Contexts and Māori and Pacific data-governance advisers is not
something this lab can carry out. It is noted as a care point, not a precondition. The report will describe
results as a property of models, not of the communities or repositories involved.

## 9. Process commitments

- `build_corpus.py`, `prompts.py`, `generate.py`, `run_gpu.sh`, `score.py` (provisional patterns), `analysis.py`
  and `test_scoring.py` (20/20) are committed with this plan; no response has been generated.
- Departures go in deviations.md, timestamped with `date`.
- The scorer is frozen after pilot adjudication and before main scoring (§5).
- An independent adversarial review (Fable 5.1) runs on the pre-review draft.
- Released: the corpus (public metadata), prompts, all responses, scores and code.
