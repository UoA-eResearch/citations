# Independent review: "Do AI models pass on Indigenous data-governance notices?"

Reviewer: Claude Fable 5.1, 2026-10-17. Pre-review draft at commit c80be7b. Scripts, the 270-response re-scoring
sample, my per-response judgements and all recomputed tables are in `review/reviewer_checks/`. I read every file the
prompt lists, the git history 1c953ad -> c80be7b, the raw DataCite harvest, the saved Local Contexts pages and the
live pages, and 270 main-set responses in full or at the matched span.

## Recommendation: fix first

The three preregistered verdicts (H1, H2, H3 Refuted) stand: I reproduce every primary number to the third decimal
with my own bootstrap, and the Local Contexts omission rate (0.5%) survives hand re-scoring (46 of the 48 scored
omissions are real). But the draft cannot be published as written, for five reasons:

1. The conventional-clause omission figures are scorer artefacts. All 93 OLMo-2 researcher-framing CV_NC
   "omissions" state the non-commercial restriction in words the NC regex does not match; 31 of 31 that I read are
   false omissions. The "42% drops a CC BY-NC licence", "conventional 1.7%", "slightly *less* often than
   conventional clauses" and the sign of H2's point estimate all rest on this (issue 1).
2. The pilot validation is vacuous: the 200-response adjudication sample contained none of the pilot's 17
   scorer-negatives, so "sensitivity 1.00" has FN = 0 by construction (issue 2).
3. The post-hoc centrepiece, "the matched invitation is not honoured", compares a clause that asks users to contact
   providers *before reuse* with a Label whose own template text asks for nothing of the kind. Models reading TK CB as
   "unclear" are reading it as Local Contexts wrote it (issue 6).
4. The prior-work anchor is wrong: arXiv 2510.18787 is a requirements-engineering mapping study, and a closer prior
   study (models respecting a copyright notice in the prompt, arXiv 2411.01136) is missing (issue 12).
5. The report does not say that the adjudicator was an LLM, that the plan's "no record sent to a third-party API"
   was not kept, or that generation was not bit-reproducible (issues 3, 11).

None of these changes a verdict. All of them change sentences in the abstract, the plain-language summary, a figure
caption and a table. The fixes are specific and mostly short.

## Issues

### Scorer

**1. The NC content pattern cannot score the OLMo-2 researcher cell; the conventional-clause omission numbers are
artefacts.** *Location:* report.md abstract bullet "slightly *less* often than conventional clauses (1.7%)"; Results
table rows "conventional omission 1.7%", "OLMo-2-13B 1.4% / 5.0%", "researcher 1.4% / 4.8%", H2 "-1.2 points"; the
sentence "In that cell it drops the BC Notice 11% of the time and a CC BY-NC licence 42%"; F1 and its caption;
primary_main.json `matched_pairs.nc_restriction`.
*Evidence:* In OLMo-2's researcher answers to records with **no** extra element, 212 of 221 (96%) already state a
non-commercial restriction (OLMo recites CC BY with invented SA/NC/ND clauses). The NC pattern fires on 29.4% of those
NONE answers (the report gives the pooled 7-8%), and it fires on an arbitrary subset of OLMo's phrasings: "no
commercial", "non-commercial use only" and "prohibits commercial" count; "You may not use the dataset for commercial
purposes" and "The dataset can be used for non-commercial purposes. If your project is commercial ... contact" do not.
So in that cell "mention by content" is indistinguishable from the baseline hallucination and the 42%/58% split is
regex luck. Every one of the 93 scored omissions in the cell contains a non-commercial statement
(`nc_cell_check.py`); none names the CC BY-NC licence; only 77 of the cell's 221 responses (35%) name it at all.
*Consequence:* Under plan section 4's own rule ("names the element OR states what it asks") the conventional omission
is 9 / 5,967 = 0.15% and H2's point estimate is +0.3 points (Local Contexts omitted slightly *more*). Under a
name-only rule for that cell it is 2.6% and H2 is -2.1 points. H2 is Refuted either way; the sign and the sentence
are not robust.
*Fix:* (a) Report the CV_NC and LC_NC rows for OLMo-2's researcher framing by name only and say why: OLMo names the
TK NC Label in 98% of its researcher answers and the CC BY-NC licence in 35%; it folds the licence into its
(frequently wrong) recitation of CC BY. That is a real and more interesting finding than "drops it 42%". (b) Replace
the 1.7% / -1.2 figures with the range above and delete "slightly less often". (c) Replace the 42% in the text, F1 and
its caption. (d) Give false-positive rates per model x framing (table in `nc_cell_check` output: OLMo researcher NC
29%, CONTACT 16%; Qwen direct DUA 12%), not pooled.

**2. The pilot validation could not estimate sensitivity.** *Location:* report.md "the rule agreed on every one
(sensitivity 1.00)"; deviations D4; pilot_validation.json; plan section 5.
*Evidence:* The pilot set has 17 scorer omissions (13 of them OLMo-2 researcher CV_NC). The 200-response sample was
drawn at random within condition, without regard to the scorer's verdict, and contains 0 of the 17 and 0 OLMo-researcher
CV_NC responses at all. With no scorer-negative in the sample, FN = 0 and TN = 0 by construction; sensitivity and
specificity were both undefined, and the one failure mode that matters (issue 1) was invisible. The report presents
1.00 as a validation result.
*Fix:* Adjudicate all 169 main-set scorer omissions (I did 79: 33 false) and a matched random sample of scored
mentions; report sensitivity among scorer-negatives and precision among scorer-positives; or re-draw the pilot sample
stratified by scorer verdict (unblinded at sampling, blind at judging). State in the report that the original
validation had no negatives. My re-scoring: precision of a scored mention 191/191; of the 79 scored omissions read,
46 true, 33 false (31/31 in OLMo researcher CV_NC, 2/48 in Local Contexts conditions, one borderline).

**3. The adjudicator was an LLM, and the report does not say so.** *Location:* report.md "I adjudicated 200 pilot
responses, blind to the rule"; plain-terms "we ... checked nearly 20,000 answers"; deviations D1.3, D4, D6 addendum;
plan sections 3 and 5.
*Evidence:* Plan section 5 rejected an LLM judge because "a judge model adds its own blind spots". The adjudicator was
the agent running the study (commit trailers: Claude Opus 5.5), which also wrote the scorer and the hypotheses.
File timestamps put the sample draw at 12:41 and the finished CSV at 12:42:59, under two minutes for 200 responses
(an LLM reading one 330 KB file; a human could not). The adjudication notes carry one of the blind spots in question:
"hallucinates SA/NC/ND for CC BY" is written where OLMo in some responses says explicitly that NC "is not activated in
CC-BY 4.0" (see issue 10). The 19,890 answers were scored by a regular expression, not "checked".
*Fix:* Say plainly: adjudication was by the LLM running the study, which authored the scorer; the 20,000 were scored
lexically; the 200 adjudicated responses, and every response read during D6, report writing and this review, passed
through a hosted model service, so plan section 3's bold "No record is sent to a third-party API" was not kept
(deviations should annotate the plan line, not leave the report to carry it). Blindness was to the regex output, not
to the regex.

### Design (D1)

**4. The inserted form is not how BC/TK Notices appear in real records, and 15 base records carry no licence.**
*Location:* report.md "after its CC BY licence, and nothing else changes"; "Conditions (wording and URIs from
localcontexts.org)"; "does not show" item 4; plan 1.2 and 3.
*Evidence:* Of the 21 real non-Neotoma records, 12 carry the full Notice text in `rights` ("The BC (Biocultural)
Notice is a visible notification that there are accompanying cultural rights and responsibilities ...") with a
localcontextshub.org project URI; Zenodo carries the bare string "BC-Notice"; iPlaces carries name + URL. The study
inserts name + localcontexts.org URI (Neotoma's form) for every element, so the Notices are tested on a thinner
signal than Hub deposits carry, and "unclear" is the expected reading of a bare name. After stripping the real
element, 15 of the 21 non-Neotoma records have an empty rightsList, so the inserted element is their only rights
entry and "after its CC BY licence" is false for them (`has_cc` in the corpus).
*Fix:* State both facts in "How it was done" and "does not show"; report the Neotoma / other split that is already in
primary_main.json (`by_record_source`: 0.48% / 0.53%); if the study is rerun, add a condition with the Hub's Notice
text.

**5. 19,890 responses conflate three framings of very different difficulty, and "named as such 99.9%" is
lexical.** *Location:* abstract "19,890 responses"; Results "When a Local Contexts element is mentioned, it is named
as such (Local Contexts, TK, BC, Indigenous or cultural rights) 99.9% of the time"; F1 (pools framings).
*Evidence:* The agent and direct framings ask the model to list every condition; copying the rightsList string
counts. There are 0 Local Contexts omissions in 13,260 agent + direct responses, and 98% of Label mentions in the
agent framing are the bare string "TK ..." listed in `conditions` (spelled-out Indigenous / Local Contexts /
Traditional Knowledge: LC_CB 1.8%, LC_NC 1.8%, LC_CO 0.9%). The pilot notes say the same ("named, no Indigenous
framing"). In the researcher framing the spelled-out shares are 66% (CB), 75% (NC), 77% (CO), 96-99% (Notices, whose
names contain the words). Only the researcher framing tests whether a model volunteers the element.
*Fix:* Present the researcher framing as the primary evidence (LC 1.4%; CV per issue 1) with agent / direct as a
floor; replace "named as such 99.9%" with "repeats the element's name, which contains 'TK' or 'Local Contexts'", and
give the spelled-out shares by framing.

**6. The CC BY licence sits beside every inserted element.** *Location:* post-hoc section, "softened", "CC BY-NC
licence ... 8% yes", D4 "an NC licence listed with commercial use 'yes'" as an error.
*Evidence:* 206 of 221 records keep CC BY, which permits commercial use. CV_NC therefore creates a dual-licence
contradiction (CC BY and CC BY-NC on one record), and TK CO sits beside a licence that says the opposite. "commercial
use allowed: yes" under CV_NC is a defensible dual-licence reading, not necessarily an error; under TK CO it is
following the legal licence over the Label.
*Fix:* Say so where the verdict tables are interpreted; do not list the CV_NC "yes" as a characterisation error.

### Post hoc (D6)

**7. The "matched invitation" is not matched on the construct the field measures.** *Location:* abstract bullets 2
and 3; Results "The matched invitation is not [honoured]", "under-read", "the same kind of ask gets different
treatment"; plain terms "An Indigenous label asking for the same kind of collaboration almost never was"; F2 caption
"the matched equivalent of the contact request"; plan 1.2.
*Evidence:* Verified against data/raw/localcontexts and the live pages. TK CB template text: "This Label is being
used to make clear [community name or authorizing body] is open to future engagement, collaboration, and partnership
around research opportunities." Its "why use" text: "the community is open to research collaborations". The URI the
study attaches (Neotoma's) points to the Open to Collaborate Notice, an institutional statement: "Our institution is
committed to the development of new modes of collaboration, engagement, and partnership with Indigenous Peoples ...".
Neither asks the user to contact anyone before reuse. CV_CONTACT says "Users are asked to contact the data providers
before reuse". A model answering "permission_or_contact_required: unclear" (Mistral 100%, Qwen 86%) or "no" (OLMo 93%)
for TK CB is reading the Label as written; a model answering "yes" for CV_CONTACT is reading a request as a
requirement. The pair was preregistered as "the same invitation"; it is not, and the post-hoc reading inherits the
error.
*Fix:* Remove the four phrases above and the plain-terms sentence. Reframe: "The conventional request to contact
providers is read as a requirement by every model; the TK CB Label, whose text expresses openness to collaboration and
makes no request, is read as uncertain (64%) or as no requirement (33%). The Label is treated as what its text says it
is." If a matched pair is wanted, it is a conventional clause with no request ("The data providers are open to
collaboration").

**8. "Softened" for TK CO is one model, under a co-present CC BY licence, for a Label that does not mention
commercial use.** *Location:* abstract bullet "commercial use allowed in 31%"; Results "The strongest restriction is
often softened"; plain terms "about a third of the time".
*Evidence:* "yes" under TK CO is Qwen3 91%, Mistral 2%, OLMo 0.5%; the report gives only the "no" shares by model
(28 / 7 / 5%) and the pooled 31%. The Label's text concerns circulation ("specific conditions for circulation within
the community ... not, and never was, free, public, or available for everyone ... asks you to think about how you are
going to use this material"); it does not address commercial use, and CC BY on the same record does. "unclear"
(Mistral 91%, OLMo 72%) is the most defensible structured answer.
*Fix:* Give the per-model split for "yes"; attribute the finding to Qwen3; note the CC BY co-presence and that the
Label does not speak to commercial use; replace "softened" with a description.

**9. The "not binding" measure counts accurate statements as if they were failures.** *Location:* Results "Prose
framings"; D4 "TK CO called non-binding" among "characterisation errors"; supplementary V2.
*Evidence:* Local Contexts describes the TK Labels as "an educative and informational strategy to help non-community
users ... understand"; no Label or Notice page claims legal force; the Notices are institutional acknowledgements. Qwen's
typical sentence, "not a legal restriction, but a moral and ethical guideline", is accurate. The regex is otherwise
sound: "courtesy" alone adds at most 1.2 points, and the sampled matches are genuine.
*Fix:* Present V2 as neutral description (which models flag the elements' non-legal status, and how often), drop it
from the error list, and do not place it under "Read against what each element says" as a shortfall.

**10. The "invented CC terms" regex counts OLMo explaining that NC does *not* apply; the direction holds.**
*Location:* Results "OLMo-2-13B attaches NonCommercial, NoDerivatives or ShareAlike terms to the licence in 51% of its
prose answers"; supplementary V3.
*Evidence:* Of 225 OLMo NONE prose hits, 17 are entirely disclaimers ("NonCommercial (NC - Not Applicable): The
NonCommercial clause is not activated in CC-BY 4.0"), 137 mix a disclaimer and an assertion, 71 assert with no
disclaimer; 11 of 12 no-disclaimer hits I read are genuine inventions ("NonCommercial: You may not use the dataset for
commercial purposes without permission from the rights holder. This condition is part of the CC-BY 4.0 license").
A stricter check (the answer tells the user commercial use is forbidden or needs permission) fires in 293 / 442 = 66%
of OLMo NONE prose answers. The framing split is large and unreported: 96% researcher, 6% direct. The structured
corroboration exists: OLMo's NONE agent verdicts give commercial_no 17% and contact_yes 11% (Qwen, Mistral 0%).
*Fix:* Report "about half, after excluding answers that say the clause does not apply", give the researcher / direct
split, and cite the agent-framing NONE verdicts.

### H1-H3 and decision rules

**11. H3 "Refuted" is driven by moves to "unclear" and by TK NC; the headline contradicts the verdict.**
*Location:* abstract "The notices are passed on; they are not acted on" versus "H3: Refuted. Elements change the
verdict"; Results H3 paragraph.
*Evidence (recomputed):* 2,784 of 3,265 pairs change; 1,748 of the changes (63%) are only to "unclear" (contact
no->unclear 1,917 field moves; commercial yes->unclear 411). Definite-direction change is 31.7% (30.4-33.1%). By
element: TK NC 95%, TK CO 35%, TK CB 11%, TK Notice 10%, BC Notice 7%; under a definite-change reading the Notices
and TK CB would meet H3's <= 20% line. By model: OLMo 61%, Mistral 95%, Qwen 98%, and OLMo's NONE baseline is itself
noisy (see issue 10), which inflates "change" for it.
*Fix:* Keep the preregistered verdict (the rule was clear and any change counts), add the decomposition table and
the definite-change rate with its interval, and rewrite the headline so it agrees with the numbers: "they are passed
on; they change the advice, mostly to 'unclear'".

**12. Recomputation.** H1, H2, H3, all omission tables, the verdict crosstabs, V2 and V3 reproduce exactly from the
released generations with the frozen scorer (`recompute.py`, own bootstrap, seed 7; intervals differ in the fourth
decimal). The D5 relabelling fix is correct: the per-record NONE baseline lookup needs unique record labels, and the
H1/H2 statistics are invariant to the label. scored_main.csv matches a fresh scoring of results/generations in all
19,890 rows; data/ and results/ copies of generations and corpus are byte-identical. The 50 unparseable H3 pairs are
10 OLMo NONE agent responses with broken JSON x 5 conditions. `strip_echo` never fires on any main-set response
(no fenced block contains "rightsList"), so the echo question is moot here; the agent-framing "mention" is a verbatim
listing in `conditions`, which is the point of issue 5.

### Operational (D2, D3)

**13. Generation is greedy but not bit-reproducible; say so.** *Location:* report.md "Three models at greedy
decoding"; "Reproducing it"; D3.
*Evidence:* The 204 discarded 700-token Qwen pilot rows against the final 1,100-token rerun of the same prompts:
identical 68 (64 of them agent-framing JSON), diverging 136, often within the first 100 characters (vLLM batching
changes bf16 reductions). Outcomes are stable: mention 183/183 identical, agent fields 66/68. The 204 rows include 183
element-condition responses; D3 says none was read, which is consistent with the timeline (pilot draw 12:41 after all
generation ended 12:40) but cannot be verified. The image digest and seed are recorded; weights are pinned.
*Fix:* State that outputs are not deterministic under batched serving and that outcome-level reproducibility was
checked incidentally on 204 rows; note that the discarded rows were generated, not read. D2's failures touched no
outcome (no response existed before the final window; all 19,890 come from one window with one image).

### Novelty and facts

**14. The prior-work anchor is wrong and a closer prior study is missing.** *Location:* plan section 2; report
"What was already known".
*Evidence:* arXiv 2510.18787 is Motger, Catot & Franch, "Characterizing Datasets for LLM-based Requirements
Engineering: A Systematic Mapping Study" (RE = requirements engineering); it has nothing to do with licences or rights
expressions. Closer work the searches missed: "Do LLMs Know to Respect Copyright Notice?" (arXiv 2411.01136; whether
models honour a copyright notice supplied in the prompt, 43,200 samples), LiCoEval (arXiv 2408.02487; licence
information for generated code), Copyright-Bench (ICML 2026; agents choosing copyrighted over public-domain
material), and Longpre et al., "Consent in Crisis" (NeurIPS 2024; machine-readable consent signals and AI use). I
found nothing on LLMs and Local Contexts, TK Labels or Indigenous data-governance metadata; the Indigenous-governance
arm is novel. "Nothing tests whether a model surfaces a rights element it was given" is too strong given 2411.01136.
Liggins, Hudson & Anderson 2021 exists (Mol. Ecol. 30:2477-2482, doi 10.1111/mec.15918); its abstract calls the
Notices "highly visible, machine-readable icons"; "designed to travel with data" is a paraphrase I could not verify
verbatim. The Local Contexts quotations in the report are verbatim (checked against the saved pages and the live
pages). The Neotoma point is correct: 48,332 raw records pair "TK Open to Collaboration (TK CB)" with
localcontexts.org/notice/open-to-collaborate/, and the Open to Collaborate Notice is an institutional instrument.
*Fix:* Remove the LLM4RE citation; add 2411.01136 and Longpre 2024; quote "machine-readable" for Liggins et al.

### Scope and care

**15. Normative language goes beyond what the lab said it would do.** *Location:* report "Read against what each
element says" ("over-read", "under-read", "softened", "not translated into conditions"); plan section 8.
*Evidence:* Plan section 8 says the elements' meaning is taken from Local Contexts' published definitions and that
the lab will not judge for the communities. Those definitions describe the Notices as acknowledgements that
"appropriate permissions may need to be sought" and the Labels as educative; the report's verbs presuppose that the
right structured answer was "required" or "no commercial use", which the texts do not establish (issues 7-9). The
framing of communities and repositories is otherwise respectful and results are attributed to models. The
model-service disclosure is present but partial (issue 3).
*Fix:* Replace evaluative verbs with descriptions; keep "does not show" item 3 and move it up; name the model service.

### Numbers and figures

**16. Every number matches the results files except the artefacts above; three small items.** 0 errors, 14
truncated, 50 unparseable pairs, 85.3% (84.1-86.4), 0.5% (0.4-0.6), -1.2 (-1.5 to -1.0), the F2 crosstab (28/64/8,
2/64/33, 3/68/29, 2/80/18, 4/6/91), the commercial crosstab (98/2/0, 91/1/8, 13/56/31, 6/9/86), 99.9%, 0.6% / 1.0%,
4% / never, 51%, 11/46 = "a quarter", 48,353 / 48,332 / 21: all reproduce. Items: (a) "3-12%" for "not binding"
should be 4-12% (minimum 3.5%, TK CO); (b) F1's caption and the text carry the 42% (issue 1); (c) report.html's
percentages are the same set as report.md's (the only extra "97%" string is a URL-encoded byte in the favicon data
URI, not content); figures F1 and F2 render the recomputed values.

### Plain-language summary

**17. Three sentences overstate.** "checked nearly 20,000 answers" (scored by a keyword rule; 200 hand-checked by the
AI agent, none of them scorer-negatives); "An Indigenous label asking for the same kind of collaboration almost never
was" (the Label does not ask for contact; issue 7); "about a third of the time" (one model, nine times in ten;
issue 8). The closing line, "It does not reliably treat Indigenous notices as conditions in the way it treats ordinary
ones", is contradicted by the one Indigenous element that states a restriction: TK NC is honoured like CC BY-NC (98%
vs 91% "no commercial use", and Qwen reads it as needing contact 100% of the time). What the data show is: the one
Label that states a condition is treated like the equivalent licence; the Notices and the collaboration Label, which
by Local Contexts' own text are acknowledgements and invitations, are passed on and then marked uncertain rather than
turned into requirements. "Only one model, in one style of question, occasionally left it out" is right.

### Minor

- CONTACT's `collaborat*` alternative decides exactly one response on its own (an OLMo LC_CB researcher answer);
  "Collaborators" appears in 10 records' creator lists but models rarely reproduce it outside the stripped echo.
- GEN_LC fires on 1% of NONE responses: "Indigenous" and "Local Contexts" appear spontaneously in Qwen and OLMo
  answers to Pacific-station records and, oddly, to some Neotoma ones (30 hits). Harmless.
- CO's `(within|to)\s+the\s+(source\s+)?community` is broad but fires on 0.9% of OLMo NONE answers at most.
- pilot_sample.py gives 23 to the first two conditions alphabetically (CV_CONTACT, CV_DUA): fine, just not "22-23
  each" by design.
- deviations D2 and the report disagree slightly: the report says "two model servers failed to start"; D2 describes
  a Qwen timeout, an OLMo context-length crash and a missing package. Fine, but align the wording.

## Recomputed numbers

| quantity | report / results files | recomputed | note |
| --- | --- | --- | --- |
| H1 LC omission | 0.48% (0.35-0.64) | 0.48% (0.35-0.63), n 9,945 | own bootstrap, seed 7 |
| H1 after hand re-scoring | - | 0.46% (46 / 9,945) | 2 false omissions in LC_NC |
| H2 LC - CV | -1.23 pts (-1.49 to -0.96); CV 1.71% | -1.23 (-1.49 to -0.96) | reproduces |
| H2 under plan's content rule, OLMo-researcher CV_NC re-scored | - | CV 0.15%; diff +0.31 pts | 93/93 state the restriction |
| H2 with name-only scoring in that cell | - | CV 2.56%; diff -2.08 pts | 77/221 name CC BY-NC |
| H3 any change | 85.3% (84.1-86.4), 50 unparsed | 85.3% (84.2-86.4), 3,265 pairs, 50 unparsed | reproduces |
| H3 definite-direction change | - | 31.7% (30.4-33.1) | 1,748 of 2,784 changes are only to "unclear" |
| H3 definite by element | - | NC 95%, CO 35%, CB 11%, TK 10%, BC 7% | |
| H3 by model | - | OLMo 61%, Mistral 95%, Qwen 98% | |
| OLMo researcher CV_NC omission | 42.1% | 42.1% content; 65.2% name-only; 0% if any NC statement counts | artefact |
| NC pattern FP on NONE, OLMo researcher | 7.8% (pooled) | 29.4% | CONTACT 16.3% in the same cell |
| contact field, TK CB by model | - | Mistral unclear 100%; OLMo no 93%; Qwen unclear 86%, yes 7% | |
| commercial "yes", TK CO by model | 31% pooled | Qwen 91%, Mistral 2%, OLMo 0.5% | |
| spelled-out Indigenous/LC/TK in Label mentions, agent framing | "named as such 99.9%" | CB 1.8%, NC 1.8%, CO 0.9% | researcher: 66 / 75 / 77% |
| V2 "not binding" by condition | 3-12% LC; 30% CV_CONTACT | same (min 3.5%); courtesy-only <= 1.2 pts | |
| V3 OLMo invented terms | 51% | 51% regex; 17 all-disclaimer, 137 mixed, 71 assertive of 225 hits; 66% by stricter "forbidden/needs permission" check; 96% researcher vs 6% direct | |
| determinism, 204 Qwen pilot rows | "greedy" | 68 identical, 136 diverge; mention 183/183 same; agent fields 66/68 same | |
| pilot scorer-negatives in adjudication sample | sensitivity 1.00 | 0 of 200 (pilot set has 17) | vacuous |
| re-scoring sample | - | 270: 191 scored mentions all genuine; 79 scored omissions: 46 true, 33 false | `reviewer_judgements.csv` |
| non-Neotoma records with empty rightsList after stripping | "after its CC BY licence" | 15 of 21 | |
| real non-Neotoma elements carrying Notice text | name + URI inserted | 12 of 21 (plus 2 "BC-Notice", 2 name+URL) | |
| arXiv 2510.18787 | "LLM4RE ... extracts licences" | requirements-engineering mapping study | wrong citation |

## Files

`review/reviewer_checks/`: `recompute.py` -> `recompute.json` (H1-H3, decomposition, crosstabs, V2, V3);
`draw_sample.py` -> `sample.jsonl` (270 responses, stratified 2 per model x framing x condition + all 48 LC scored
omissions + 30 OLMo CV_NC scored omissions + 30 OLMo researcher mentions); `view_sample.py` -> `sample_view.txt`
(what I read); `judgements.py` -> `reviewer_judgements.csv`, `rescoring_summary.json`; `nc_cell_check.py` (the
OLMo-researcher cell, FP rates by cell, corrected H2); `v3_check.py` (invented-terms regex audit). No file outside
`review/` was modified; no git state was changed; no container was started or stopped. The responses I read passed
through my own model service, as the study's adjudicated ones did.
