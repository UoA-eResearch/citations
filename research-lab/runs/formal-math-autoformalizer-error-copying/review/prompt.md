You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/formal-math-autoformalizer-error-copying/ (read-only except your output in
review/). Read plan.md (preregistration, commit 9afb62b), NOTES_pre_plan.md, deviations.md (D1-D7), report.md (draft,
commit db0689f), code/ (candidates.py, lean_check.py, tagging.py, twins.py, sample.py, classify.py, refcheck.py,
analysis.py, figures.py, prompts/ and the run_*.sh scripts), results/catalogue/ (frozen.jsonl, tags.jsonl, the tagging
batches and key, twins/, paraphrase/, refcheck.jsonl, attrition tables), results/tables/, results/figures/ and logs/.
You may run read-only git commands in /mnt/citations, for example to check that each stage's code and the frozen
catalogue were committed before the outcomes they could affect.

Python: ../formal-math-certified-contamination-did/venv/bin/python (pandas, numpy). Raw model outputs are in
data/samples/<model>.jsonl (also results/outputs/*.gz); per-statement classifications in data/classified/. Lean: you can
re-run checks with `VAC_TOOLCHAIN=v49` and code/lean_check.py (it starts a Lean REPL from
../formal-math-selfplay-vacuity-drift; each REPL needs several GB of RAM, so use at most 4 at once, and pin them with
`taskset -c 0-3`). Do not start or stop any Docker container and do not use the GPU.

Check at least:

1. **Timing and disclosure.** Were the plan, the Lean filters, the tags, the twins and paraphrases (frozen catalogue),
   the sampling and classification code, and the analysis code committed before the outcomes they could affect?
   D6 claims it was written before any outcome was computed; D7 lists the post-hoc analyses. Is anything post hoc
   presented as confirmatory? Is anything done but not disclosed?
2. **The catalogue.**
   - Spot-check about 10 included items: is D really defective and C faithful for the informal statement?
   - Spot-check the twins: is each twin's N′ the same problem with new numbers, is D′ the same defect, is C′ correct?
     Look especially at t237, t262 and t284 (flagged), and at whether twins of "weakened conclusion" items keep a
     defect of the same kind.
   - Is excluding items without numbers a source of bias for the primary question?
3. **Classification.** Spot-check by hand about 15 outputs classed "copy" and 15 classed "other" in conditions O and T,
   for at least two models: is a copy really the same statement as D (or D′)? Is an "other" really different from both
   references, or an equivalence the portfolio missed? Re-run a few equivalence checks in Lean. Is there any asymmetry
   between conditions O and T in what the certifier can recognise (e.g. larger numbers in twins making norm_num slower
   or time out)? Check the extraction rules in classify.py (last code block, `</think>`, truncated outputs) and the
   verbatim test.
4. **The statistic.** Recompute the primary RR, its bootstrap interval and the verdict from
   data/classified/*_outputs.jsonl and data/classified/*.jsonl independently of analysis.py. Check the denominator
   (every requested temperature sample) and the item-cluster bootstrap. Recompute the by-model and O-vs-P numbers.
5. **The D6 informativeness check.** Is the check right (provable / refuted portfolios)? Are there references that are
   uninformative in a way it misses (e.g. D whose equivalence class is easy to hit by accident because its conclusion
   is weak)? Does that change the reading?
6. **Interpretation.**
   - Is "Refuted" the right verdict by the preregistered rule, and is it stated with the right scope? The twins keep
     the original wording; is the report's caveat about wording-keyed recall adequate, or does it undercut the
     headline?
   - The exploratory O vs P result (1.57) and the two readings offered: are they fair? Is there a better test in the
     data the study already has (e.g. per-item analysis of what the paraphrase changed)?
   - The negative-control reading and the claim that models "do not reproduce v1 statements verbatim on demand".
   - The paragraph on the miniF2F-v2 paper's contamination remark: is it accurate and fair?
   - Use web search to check novelty (error-copying or memorization tests for autoformalizers) and facts stated about
     the models, benchmarks and papers cited.
7. **Numbers.** Does every number in report.md, results/tables/tiles.json and the figures match the results files?
8. **Plain-language summary.** Is "## In plain terms" accurate and not overstated?

Write your review to review/review.md with:

- a recommendation (publish / publish with edits / fix first);
- numbered issues, each with its location and a concrete fix;
- a table of the numbers you recomputed.

Reply with the recommendation and the number of issues.
