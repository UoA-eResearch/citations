# Confirmation pass on the revised draft (commit 1fb4144, D7)

Reviewer: Claude Fable 5.1, 2026-10-17. I read the rewritten report.md, D7, code/review_response.py and
results/tables/review_response.json, the figures.py diff, both rebuilt figure captions and the rebuilt F1, and
compared report.html with report.md. score.py, analysis.py, supplementary.py, scored_main.csv and primary_main.json are
unchanged since the freeze, and plan.md is untouched (D7 records the plan-§3 correction, which is the right place).

## Recommendation: publish with edits

All 17 issues are resolved or honestly disclosed, every new number in the report matches review_response.json or my
own recomputation, and the plain-language summary is now supported by the data. Five one-sentence edits remain; none
touches a verdict or a table.

## Remaining edits

1. **"Named every element every time" is contradicted by F1 itself.** Abstract: "Qwen3-32B and Mistral-Small-24B
   named every element every time"; F1 title "Only OLMo-2 leaves elements unnamed"; F1 caption "Qwen3 and Mistral name
   every element". On the name rule in the researcher framing, Qwen3 leaves the no-URI variant unnamed in 4 of 221
   answers (1.8%) and the contact clause in 2 (0.9%); both points are visible in the rebuilt figure. Mistral is at 0%
   everywhere in that framing (and 2.6% in the agent framing, where it lists "Non-commercial use only" instead of the
   licence name). Fix: "Qwen3-32B and Mistral-Small-24B omitted no Local Contexts element in the five preregistered
   conditions"; title "Only OLMo-2 leaves elements unnamed to any extent"; caption "Qwen3 and Mistral name every
   element but six (Qwen3: 4 no-URI, 2 contact clause)".
2. **Misattribution.** "Of its researcher answers to records with no extra element, 81% contain a sentence saying
   commercial use is forbidden or needs permission (the reviewer, reading them, put it at 96%, 212 of 221)". I did not
   read those 221; 212/221 was a looser lexical count that includes disclaimer sentences (review_response.py's own
   `none_nc_statement` gives 97%). Fix: "(a looser count of any non-commercial statement, including sentences that say
   the clause does not apply, gives 96–97%)".
3. **"Not omitted more often" versus the +0.3 bound.** Abstract bullet "No penalty for being Indigenous. Local
   Contexts elements were not omitted more often than conventional clauses: the difference is between +0.3 and −2.1
   points". Under scoring (a) Local Contexts elements were omitted 0.3 points *more* often. Fix: "were omitted about as
   often as conventional clauses: the difference is between +0.3 and −2.1 points, against a predicted +25".
4. **"Samples were read by hand"** (plain terms) implies a human. Fix: "samples were read by the AI agent running the
   study and by an independent AI reviewer".
5. **30 → 31.** "all 30 OLMo-2 CC BY-NC 'omissions' it read were not": 31 (30 in the omission stratum plus one in the
   stratified cell, r094).

Optional: review_response.py's H2 re-scorings use 1,000 bootstrap resamples rather than the plan's 2,000; the intervals
are stable to the third decimal, but say so or set 2,000.

## Issue-by-issue

| # | issue | status | where |
| --- | --- | --- | --- |
| 1 | OLMo-2 researcher CV_NC artefact; 42%; CV 1.7%; H2 sign | resolved: two scorings, range reported, sign withdrawn, 42% withdrawn, naming 98% / 35% | Results H1/H2; F1 rebuilt on name rule; R1 |
| 2 | pilot "sensitivity 1.00" vacuous | disclosed: sample had none of 17 scorer-negatives; validation now rests on the 270-response re-scoring | "Disclosure about validation"; "does not show" 5 |
| 3 | LLM adjudicator; plan §3 not kept | disclosed: same LLM that wrote the scorer, blind to output not rule; hosted service for every read response; D7 corrects plan §3 | Methods; D7. Edit 4 above |
| 4 | name+URI vs Hub Notice text; 15 of 21 no licence; CC BY beside every element | disclosed: 12/21, 15/21, 206/221 | Methods; "does not show" 3–4 |
| 5 | framings conflated; "named as such 99.9%" | resolved: researcher framing primary; spelled-out shares 68–77% / 100% / 1–2% | Methods; Naming paragraph; F1 |
| 6 | CC BY co-presence and CV_NC "yes" | resolved | "does not show" 4; TK CO bullet |
| 7 | matched invitation not matched | resolved: "only one makes a request ... follows the difference in texts"; F2 caption rewritten | Post hoc; F2 caption |
| 8 | TK CO "softened" is one model | resolved: Qwen3 91% / Mistral unclear 91% / OLMo unclear 72%; circulation-not-commercial; CC BY | Post hoc; plain terms |
| 9 | "not binding" treated as failure | resolved: "matches Local Contexts' own description ... not an error" | Post hoc |
| 10 | V3 regex counts disclaimers | resolved: 64% excluding disclaimer sentences (81 / 47 by framing); agent corroboration 17% / 11% | Post hoc; R6. Edit 2 above |
| 11 | H3 mostly "unclear"; headline contradiction | resolved: decomposition table, 31.7% (30.4–33.1), by element and model; verdict reworded | Verdict; H3 section |
| 12 | recomputation | n/a (reproduced) | — |
| 13 | determinism | disclosed: 68/204, 183/183, 66/68 | Methods; R7 |
| 14 | LLM4RE wrong; prior work missing | resolved: withdrawn with a note; 2411.01136, LiCoEval, Longpre 2024 added; Liggins quoted | "What was already known" |
| 15 | normative verbs | resolved: element-by-element reading against each text; normative caveat first | Post hoc; "does not show" 1 |
| 16 | numbers | resolved (see table below); "4–12%" fixed; html matches md (html also embeds the figure captions) | — . Edit 1 above |
| 17 | plain-language summary | resolved; supported (see below) | "In plain terms". Edits 3–4 above |

## Numbers checked against the results files

| report statement | source | matches |
| --- | --- | --- |
| 0.5% (0.4–0.6%) of 9,945; 0.46% after re-scoring | primary_main H1; R1 (46/9,945) | yes |
| H2 range +0.3 (+0.2 to +0.5) / −2.1 (−2.3 to −1.8); CV 0.15% / 2.6%; preregistered −1.2 (−1.5 to −1.0) | R1_H2_a/b; primary_main | yes |
| OLMo names TK NC 98%, CC BY-NC 35% | R1_olmo_researcher_names (0.982 / 0.348) | yes |
| OLMo researcher LC omission 4.3%; agent/direct CV ≤ 0.6% | R4 (0.0434; 0.0045, 0.0060) | yes |
| 85.3% (84.1–86.4), 3,265 pairs, 50 unparseable; definite 31.7% (30.4–33.1); 63% only to unclear; NC 95 / CO 35 / CB 11 / TK 10 / BC 7; any change by model 98 / 95 / 61 | R2 | yes |
| spelled out 68–77% (Labels, researcher), 100% (Notices), 1–2% (agent) | R4_spelled_out_share | yes |
| F2 table (100/0/0; 100/0/0; 28/64/8; 2/64/33; 3/68/29; 2/80/18; 4/6/91) | supplementary + my recompute | yes |
| TK CB contact: Mistral unclear 100%, Qwen unclear 86%, OLMo no 93% | R5 | yes |
| TK CO commercial: Qwen yes 91%, Mistral unclear 91%, OLMo unclear 72%; contact yes 72 / 8 / 5% | R5; supplementary V1 | yes |
| TK NC "no commercial" 98%, CC BY-NC 91% | supplementary V1 | yes |
| "not binding" 4–12% | supplementary V2 (min 3.5%) | yes |
| OLMo forbids/needs-permission 64% (81 researcher, 47 direct); agent NONE 17% / 11% | R6; V1 NONE|olmo | yes |
| determinism 68/204; 183/183; 66/68 | R7 | yes |
| 19,890; 0 errors; 14 truncated; 206 CC BY; 15 of 21; 12 of 21; 48,353 / 48,332 / 21 | generations; corpus; raw DataCite | yes |
| reviewer judgements 191 / 46 / 2 / "30" | reviewer_judgements.csv | 31, not 30 (edit 5) |
| Qwen3 and Mistral "named every element every time" | name rule, researcher: Qwen 4 + 2 unnamed | no (edit 1) |
| TK NC template text "designated as being available for non-commercial use"; TK CB, TK CO, Notice quotes | data/raw/localcontexts | yes, verbatim |
| Liggins et al. 2021, Mol. Ecol. 30:2477, "highly visible, machine-readable icons" | abstract | yes |
| arXiv 2411.01136 (43,200 samples), 2408.02487, Longpre 2024 NeurIPS | web | yes |

## Plain-language summary

Each sentence now has a number behind it: "almost always mentioned" (0.5%); "only one model, answering an open
question, sometimes left one out" (48/48 OLMo researcher); "treated like an ordinary non-commercial licence" (98% vs
91%); "mostly answered 'unclear'" for Notices and TK CB (64–80%); "always turned into 'contact required'" (100%);
"one model said commercial use was allowed nine times in ten" (Qwen3 91%); "one model often added restrictions"
(64%). The earlier overstatements ("asking for the same kind of collaboration", "a third of the time", "does not
reliably treat Indigenous notices as conditions in the way it treats ordinary ones") are gone. The only wording to
change is "read by hand" (edit 4).

## Process

Reading of responses for this pass was limited to what review_response.py and the figures expose; no new responses
were read. No file outside `review/` was modified; no git state was changed; no container was touched.
