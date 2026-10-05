# Coder prompts (verbatim)

These are the exact prompts the executing agent (Claude Opus 5.5, `claude-opus-5-5`) sent to the coder agents. All
coders were subagents spawned inside the executing agent's own Claude Code session.

**Coders:**

- **Coder A:** Claude Fable 5.1 (`claude-fable-5-1`).
- **Coder B:** Claude Opus 5.5.
- **Inventory coder:** Claude Opus 5.5.

**What is not published.** The coders' transcripts are not in the repository; their outputs are under `audit/`. Each
later task was sent to the same coder instance through a follow-up message, so the coder kept its earlier context.

The two coders received identical prompts, except that each was told not to read the other's folder and to write to
its own. The text below is coder A's version.

## Task B and C: deviations and reviews (initial prompt)

> You are an independent coder for a self-audit of an AI-run research lab. Another coder is doing the same task separately, and agreement between you will be measured, so work only from the files named here and apply the codebook literally. Do not read anything under /mnt/citations/research-lab/paper/audit/coder_B/ or /mnt/citations/research-lab/paper/audit/coder_A/ other than writing your own outputs. Also do not read /mnt/citations/research-lab/related-efforts.md.
>
> Repository: /mnt/citations. The studies are the 19 directories listed in /mnt/citations/research-lab/paper/audit/runs.txt, each under /mnt/citations/research-lab/runs/<run>/ with plan.md, deviations.md and, for 17 of them, report.md. quantum-simulation-peaked-98q-classical-crack and formal-math-selfplay-vacuity-drift are still in progress (no report): code their deviations (task B) but skip them in task C.
>
> TASK B: code every numbered deviation entry in every deviations.md. Entries are the numbered items such as D1, D2, D2b, D27c (headers like "## D3. ..." or bullets like "* D5 ..."). If a file has unnumbered items, treat each top-level item as an entry and give it an id like U1, U2. Codes for each entry:
> 1. category (one primary): C1 bug or numerical fix; C2 data problem (availability, quality, definitions); C3 change to the primary analysis specification (estimator, sample, outcome, test); C4 change to the decision rule or its thresholds; C5 added secondary or sensitivity analysis; C6 environment, compute or logistics; C7 clarification, disclosure or documentation only; C8 withdrawal or correction of a claim.
> 2. trigger: T1 executor during the work; T2 validation or positive-control check; T3 the independent reviewer; T4 external event or data release.
> 3. timing: before (the primary outcome had not yet been seen), after, or unclear.
> 4. verdict_relevance: could this deviation plausibly change the preregistered verdict? yes / no / unclear.
>
> TASK C: for each of the 17 reported studies, using report.md (especially its review section), deviations.md, and the git history of report.md (you may run `git -C /mnt/citations log -p --follow -- research-lab/runs/<run>/report.md` and similar read-only git commands), record:
> - recommendation: the independent review's recommendation (e.g. FIX FIRST, accept with changes, accept; "not stated" if absent)
> - confirmation_pass: yes / no / unclear
> - n_issues: number of distinct substantive issues the review raised (integer, or blank if not determinable)
> - counts of issues by category: R1 computational or numerical error; R2 analysis or model error (incl. local optima); R3 leakage or blinding; R4 overclaiming or wording; R5 missing analysis or robustness check; R6 documentation
> - headline_changed: did the headline estimate change after review? yes / no / unclear
> - verdict_changed: did the verdict change after review? yes / no / unclear; plus pre_verdict and final_verdict if determinable
> - assumed_effect and mde: if the study states an effect size assumed when the lead was scouted/planned and a minimum detectable effect, copy them (short text); otherwise blank
>
> Use only read-only commands (cat, sed, grep, git log/show). Write your outputs as CSV (comma-separated, double-quote any field containing a comma) to:
> - /mnt/citations/research-lab/paper/audit/coder_A/B_deviations.csv with columns: run,entry_id,entry_title,category,trigger,timing,verdict_relevance,note
> - /mnt/citations/research-lab/paper/audit/coder_A/C_review.csv with columns: run,recommendation,confirmation_pass,n_issues,R1,R2,R3,R4,R5,R6,headline_changed,verdict_changed,pre_verdict,final_verdict,assumed_effect,mde,note
> Keep entry_title under 80 characters and note under 200 characters. Be complete: every entry in every one of the 19 deviations.md files. When done, reply with the number of entries coded per run and any entries you found ambiguous.

## Task D: untraced numbers (follow-up message)

> One more independent coding task (same rules: do not read coder_B/ or any other coder's output). The file /mnt/citations/research-lab/paper/audit/D_sample_untraced.csv lists 85 numbers printed in study reports that an automated script could NOT match to any value in that study's results/ files, plan.md or deviations.md. Columns: sample_id, run, token (the number as printed), context (text around it). For each row, look at the report (/mnt/citations/research-lab/runs/<run>/report.md) and the study's results/, plan.md, deviations.md, code/ and the lead in /mnt/citations/research-lab/leads.json as needed, and classify where the number comes from:
> U1 arithmetic derived from traced numbers (e.g. a difference, ratio, sum or percentage computed from numbers that are in the results);
> U2 from cited literature, data documentation or the lead (an external number, not computed by the study);
> U3 a design parameter (sample size, threshold, seed, setting);
> U4 not traceable (you cannot find where it comes from);
> U5 inconsistent with the results (you find the corresponding quantity and it differs beyond rounding).
> Write /mnt/citations/research-lab/paper/audit/coder_A/D_untraced_classified.csv with columns sample_id,run,token,class,source,note (source = file and column/key or citation where found; note under 160 characters). Reply with counts per class and list every U4 and U5 case.

## Same-commit classification (follow-up message, added after review)

> One more independent coding task (same rules: do not read coder_B/ or other coders' outputs). In four studies, plan.md was first committed in the same git commit as some files under results/. For each commit below, list every file under the run's results/ added in that commit (use `git -C /mnt/citations show --stat --format= <commit>` and `git show <commit>:<path>` read-only), and classify each file as PRE-OUTCOME (contains no information about the primary outcome: e.g. data inventories, coverage tables, pre-period-only statistics, power/MDE, hashes of sealed files) or OUTCOME (contains or reveals primary-outcome results), with a one-line reason. Then give a per-commit verdict: "pre-outcome only" or "contains outcome material".
> Commits: 258616c (astronomy-gwtc4-q-chieff-copula-stress-test), e74eaea (auckland-nz-speed-limit-reversal-crashes), 311bd7e (auckland-nz-wastewater-testing-gap-deprivation), 1f0956b (health-econ-wastewater-flusight-value). Use each study's plan.md to decide what its primary outcome is.
> Write /mnt/citations/research-lab/paper/audit/coder_A/A_same_commit.csv with columns commit,run,file,class,reason, plus one row per commit with file="VERDICT" and class set to the per-commit verdict. Reply with the four verdicts.

## Direct verification of a random sample of numbers (follow-up message, added after review)

> After the same-commit task, one more independent coding task (same rules: do not read coder_B/ or other coders' outputs). /mnt/citations/research-lab/paper/audit/D_verify_sample.csv lists 119 numbers drawn at random from the 17 study reports (7 per report): columns verify_id, run, token (number as printed), context (short text around it). For each, find the number in /mnt/citations/research-lab/runs/<run>/report.md, work out what quantity it states, and locate its specific source: a file and cell/key under the run's results/ (preferred), or the data/code computation that produces it, or plan.md/deviations.md, or an external citation. Recompute if needed (read-only; you may run the run's own venv python on its files). Classify:
> V1 exact source found and the printed value is consistent with it (within rounding);
> V2 derived (arithmetic on located values, or recomputed from data/code) and consistent;
> V3 design parameter or external (literature/data documentation) and consistent with that source;
> V4 inconsistent: you located the quantity and the printed value differs beyond rounding (give both values);
> V5 not verifiable: you cannot locate or reproduce it.
> Write /mnt/citations/research-lab/paper/audit/coder_A/D_verify.csv with columns verify_id,run,token,class,source,located_value,note (note < 160 chars). Reply with counts per class and list every V4 and V5 case with details.

## Inventory coder (Opus 5.5, one prompt)

> You are a coder for a self-audit of an AI-run research lab. Work only from the files named here, read-only. Do not read anything under /mnt/citations/research-lab/paper/audit/coder_A/ or coder_B/, and do not read /mnt/citations/research-lab/related-efforts.md.
>
> For each of the 19 study directories listed in /mnt/citations/research-lab/paper/audit/runs.txt (each at /mnt/citations/research-lab/runs/<run>/), read plan.md (and, where needed to resolve a question, deviations.md and report.md), and record which safeguards the PLAN (as committed) specified. Code each item yes / no / partial, with a short quote or location as evidence:
>
> 1. disclosure: does the plan state what data/results had already been seen before it was written?
> 2. decision_rule: does it state explicit verdict criteria (thresholds that map results to supported/refuted/inconclusive or similar)?
> 3. power: does it state a power analysis, minimum detectable effect, or expected precision for the primary test BEFORE results? (report the MDE/precision if given)
> 4. outcome_blinding: how were outcomes kept from the analyst before the analysis was fixed? Code one of: sealed (outcome data stored unread, e.g. with a recorded hash), prospective (outcome data did not yet exist when the plan was committed), formal (outcome is a machine-checked proof/certificate), none (outcome data were available to the analyst), partial (explain).
> 5. validation: does the plan require validating the method before the primary analysis (synthetic data with known truth, positive/negative controls, reproduction of a published number)? yes/no/partial.
> 6. multiplicity: if there are several primary tests, does the plan control or address multiplicity? yes / no / not applicable (single primary test).
> 7. independent_review: does the plan (or the report) state that an independent reviewer agent reviews before the verdict? yes / no.
> 8. data_open: are all primary data openly available without registration? yes / no / partial (explain).
> 9. primary_type: one of confirmatory-hypothesis-test, estimation, replication/reanalysis, prospective-forecast, other.
>
> Write a CSV (comma-separated; double-quote fields containing commas) to /mnt/citations/research-lab/paper/audit/inventory/plan_inventory.csv with columns:
> run,disclosure,decision_rule,power,power_detail,outcome_blinding,outcome_blinding_detail,validation,multiplicity,independent_review,data_open,data_open_detail,primary_type,evidence_notes
> (create the directory if needed). Keep each detail field under 160 characters. Reply with a one-line count per column of yes/no/partial values.

## Paper reviewer

The reviewer was Claude Fable 5.1, spawned in the same session. Its full prompt is `paper/review/prompt.md`, and its
review is `paper/review/review.md`, published unedited.
