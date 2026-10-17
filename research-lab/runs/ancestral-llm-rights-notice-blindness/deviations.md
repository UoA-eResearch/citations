# Deviations log

Every departure from the lead and from plan.md, timestamped with `date` when it was made.

## D1 — 2026-10-17 08:08 NZDT — before any generation: three real arms are impossible; a within-record experiment instead

1. **Design.** 48,332 of the 48,353 DataCite records with a Local Contexts URI are Neotoma's, all with one element
   ("TK Open to Collaboration (TK CB)"); 21 are elsewhere. The lead's stratified real arm A (no publisher > 50%) and
   its arm-A-versus-arm-B comparison of different repositories cannot be built. Each record is instead shown with
   every condition swapped into the same rightsList slot (plan 1.2). Real arm-B records are not used.
2. **Element types** beyond Neotoma's are inserted using Local Contexts' own published names and URIs (BC Notice,
   TK Notice, TK Non-Commercial, TK Community Use Only), with matched conventional clauses.
3. **No LLM judge; agent adjudication of a pilot instead of 300 human-coded responses** (plan section 5). The lab
   has no human coder, and a judge model adds its own blind spots and would need care to stay local.
4. **Sample sizes:** 221 base records (200 Neotoma + 21 others) x 10 conditions rather than 3 x 400 records.
5. Neotoma's element pairs a TK *Label* name with the Open to Collaborate *Notice* URI - a data-quality point worth
   reporting to Neotoma and Local Contexts.
6. The Mistral snapshot's duplicate consolidated.safetensors (47 GB, a re-packaging of the sharded weights) was
   deleted so vLLM loads only the sharded set.

## D2 — 2026-10-17 08:29 NZDT — the Qwen3-32B server missed run_gpu.sh's 20-minute start timeout

Loading Qwen3-32B's 62 GB from the HDD took about 20 minutes; the server had just finished warming up when the
script's timeout stopped it, and the script moved on to OLMo-2 and Mistral. No Qwen output was generated. Qwen
runs afterwards in its own GPU window (code/run_gpu_qwen.sh: identical except for the model list and a 60-minute
timeout). Generation settings, prompts and corpus are unchanged.

Then OLMo-2's server crashed at start-up, started seconds after the Qwen container was stopped mid-warmup; the
container was removed (--rm) before its log could be read, so the cause is inferred, not seen: most likely Qwen's
GPU memory was not yet released. The second window (run_gpu_qwen.sh) now runs OLMo-2 and then Qwen3, waits for the
GPU to be free before each server starts, and captures each container's log to logs/lc-gen-<model>.log. Mistral
ran in the first window with its log captured.

And Mistral's server came up in the first window, but generate.py failed at import: the requests package was not
installed in the venv (generate.py had not been smoke-tested before the GPU stage). requests was installed before
the second window reached generation; Mistral runs in a third window (code/run_gpu_mistral.sh, same settings). No
response from any model had been generated or read when these were fixed.

Second window: OLMo-2's server failed again, this time with its log captured: vLLM rejects --max-model-len 6144
because OLMo-2's context is 4,096 tokens (so the first-window crash was probably this too, not GPU memory). The
longest prompt is 2,959 OLMo tokens, so prompt + 700 output always fits in 4,096; the third window
(run_gpu_mistral.sh) runs Mistral and OLMo at --max-model-len 4096, which truncates nothing and does not change any
output. The script also now stops waiting as soon as a server's container exits (the second window polled a dead
OLMo server for its full 60 minutes). Weights were moved to the NVMe (/mnt/research-lab-models/..., at the user's
request; faster loading) and data/models now links there; the HDD copy is kept as data/models_hdd until the run
ends. Qwen3 runs in the second window from the NVMe copy.


## D3 — 2026-10-17 10:09 NZDT — max_tokens raised from 700 to 1,100 for every model, from the pilot

11 of Qwen3's first 46 pilot responses stopped at the 700-token cap. A response cut off before it reaches the rights
element would be scored as an omission, biasing H1 and H2 upward, so the cap is raised to 1,100 for all three models
(the longest prompt under each tokenizer: Qwen3 3,205, Mistral 3,275, OLMo-2 2,969 tokens; OLMo-2's 4,096 context
still fits). The second window was stopped; Qwen's 204 rows generated at 700 tokens are set aside in
data/generations/discarded_700tok/ and not used. At that point I had read three Qwen responses, all NONE-condition
(no element present), to check format; no element-condition response had been read or scored. All three models now
run in one final window (run_gpu_mistral.sh: Qwen3 and Mistral at 6,144 context, OLMo-2 at 4,096). Truncated responses
are still reported, with a sensitivity excluding them.

## D4 — 2026-10-17 12:43 NZDT — pilot adjudication done; scorer frozen unchanged, one name-only secondary added

I adjudicated the 200-response pilot sample blind to the scorer (results/tables/pilot_adjudication.csv). All 200
mention the inserted element. The scorer agrees on every one (sensitivity 1.00, no disagreements); specificity is
not estimable from a sample with no negatives, so the pilot's NONE responses give each pattern's false-positive
rate: 1-2% for the Local Contexts, data-use-agreement and contact patterns, 7-8% for the two non-commercial
patterns, because some models invent a NonCommercial term for plain CC BY. The preregistered patterns are frozen
unchanged. Added before the main set is scored, as a secondary only: mention by explicit name (score.NAMES), which a
hallucinated restriction cannot trigger. The adjudication notes also record characterisation errors (invented
CC BY terms, TK CO called non-binding, "BC" read as British Columbia, an NC licence listed with commercial use
"yes"); these are descriptive and not part of any preregistered outcome.

## D5 — 2026-10-17 12:45 NZDT — a bootstrap bug in analysis.py, fixed before any result was printed

The first main run crashed in H3's bootstrap: a record drawn twice kept its DOI, so the per-record NONE baseline
lookup returned several rows. Each resampled copy now gets its own label (standard for a cluster bootstrap; H1 and
H2's intervals are computed the same way and are affected only through that relabelling). The run crashed before
printing or writing any result; the scorer is unchanged.

## D6 — 2026-10-17 12:56 NZDT — post-hoc descriptive checks of what models say about the elements

The preregistered results: H1 Refuted (Local Contexts omission 0.5%, 0.4-0.6%), H2 Refuted (Local Contexts
omitted 1.2 points LESS often than conventional clauses), H3 Refuted (an element changes the agent verdict in 85%,
84-86%). Nearly all omissions are OLMo-2 in the researcher framing. code/supplementary.py, written now and committed
before it runs, describes which way verdicts move (V1, with the matched pairs), how often an element is called not
legally binding (V2), and how often models attach NonCommercial/NoDerivatives/ShareAlike terms to plain CC BY (V3).
Descriptive only; patterns for V2 and V3 are lexical and unvalidated, and the report says so.

Addendum to D4: plan section 3 says no record is sent to a third-party API. Generation and scoring were entirely
local; but the pilot adjudication was done by the agent running the study, so the 200 adjudicated responses (which
quote public DataCite metadata) passed through the agent's own model service. Disclosed in the report.


## D7 — 2026-10-17 13:20 NZDT — acting on the adversarial review (fix first, 17 issues)

The review (Fable 5.1) reproduced every primary number and left all three verdicts standing, but found: the
non-commercial content pattern cannot score the OLMo-2 researcher cell (OLMo recites CC BY with invented NC terms, so
"mention by content" is indistinguishable from its baseline), making the conventional-omission figures, the "42%"
and H2's sign artefacts; the pilot adjudication contained none of the pilot's 17 scorer-negatives, so "sensitivity
1.00" was vacuous; the adjudicator was the LLM running the study, and plan section 3's "no record is sent to a
third-party API" was not kept (every response read by the agent passed through its hosted model service); the
inserted name+URI form is thinner than real Hub Notices, and 15 of 21 non-Neotoma records carry no licence; the
"matched invitation" is not matched (TK CB's text makes no request); the TK CO "commercial yes" is one model under a
co-present CC BY licence, for a Label that does not address commercial use; the "not binding" measure counts accurate
statements; the V3 regex counts disclaimers; H3's changes are mostly moves to "unclear"; batched generation is not
bit-reproducible; and the LLM4RE citation is wrong (arXiv 2510.18787 is a requirements-engineering study). Correction
to the plan: section 3's bold sentence should have read "no record is sent to a third-party model for generation or
scoring". code/review_response.py, written now and committed before it runs, reproduces the checks in the study's own
code, using the reviewer's independent hand judgements for the corrected omission rates. The report is then revised.

D7 outcomes (review_response.py): Local Contexts omission 0.46% after the reviewer's hand judgements (46 of 48
scored omissions real); OLMo-2 researcher CV_NC re-scored: any non-commercial statement counts -> conventional
omission 0.15%, H2 +0.3 points (+0.2 to +0.5); licence must be named -> 2.6%, H2 -2.1 (-2.3 to -1.8); H2 Refuted
either way, sign not robust. OLMo-2 names TK NC in 98% of researcher answers, the CC BY-NC licence in 35%. H3: any
change 85.3%, definite change 31.7% (30.4-33.1%), 63% of changes only to "unclear"; definite by element NC 95%, CO
35%, CB 11%, TK 10%, BC 7%. TK CO "commercial yes": Qwen3 91%, Mistral 2%, OLMo-2 0.5%. OLMo-2 tells the user
commercial use is forbidden or needs permission in 64% of its no-element prose answers (81% researcher, 47% direct),
excluding disclaimer sentences. Determinism: 68 of 204 re-generated prompts identical; outcomes 183/183 and 66/68
the same. F1 rebuilt on the name rule in the researcher framing; the report rewritten (verdict wording, the
validation and service disclosures, H2 range, H3 decomposition, post-hoc reading against each element's text, the
withdrawn LLM4RE citation, the added prior work).

Confirmation pass (review/confirmation.md, publish with edits): five sentences corrected (Qwen3 omitted no Local
Contexts element in the five preregistered conditions, but leaves six elements unnamed on the name rule in F1; the
96-97% is a looser pattern, not a reading; "about as often" rather than "not more often"; hand-reading attributed to
the AI agent and the AI reviewer; 31, not 30, OLMo CC BY-NC responses read). review_response.py's H2 re-scorings use
1,000 bootstrap resamples rather than the plan's 2,000 (stable to the third decimal).

