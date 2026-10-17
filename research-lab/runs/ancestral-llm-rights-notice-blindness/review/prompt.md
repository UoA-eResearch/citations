You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/ancestral-llm-rights-notice-blindness/ (read-only except your output in review/).

The question: do open-weight LLMs pass on Local Contexts Notices/Labels (Indigenous data-governance elements) present in
a dataset's repository metadata, compared with conventional rights clauses? A within-record experiment: 221 real DataCite
records x 10 conditions swapped into one rightsList slot x 3 framings x 3 models (Qwen3-32B, Mistral-Small-24B,
OLMo-2-13B), 19,890 responses, all generated locally.

**What to read:**

- plan.md (preregistration, commit 1c953ad, before any generation);
- deviations.md (D1-D6). D1 predates the plan; D2-D3 are GPU-stage failures and a max_tokens change; D4 is the pilot
  adjudication and scorer freeze; D5 a bootstrap bug; D6 post hoc;
- report.md and report.html (pre-review draft, commit c80be7b);
- code/: build_corpus.py, prompts.py, generate.py, run_gpu*.sh, score.py, analysis.py, test_scoring.py, pilot_sample.py,
  supplementary.py, figures.py;
- results/tables/ (primary_main.json, scored_main.csv, supplementary.json, pilot_adjudication*.csv/jsonl,
  pilot_validation.json), results/corpus/, results/generations/ (every response), results/figures/.

**Git.** Read-only git in /mnt/citations is fine. Sequence: 1c953ad (plan + code) -> 617d884 / e936b83 / 88c6972 / 80c3de7
/ 74a278b (D2-D3 operational) -> 3f119ce (pilot adjudicated, scorer frozen) -> b5b86c0 (D5) -> 7d6b7a7 (results + D6
code unrun) -> c80be7b (draft). Check the scorer was frozen before main-set scoring and that no element-condition
response was read before D3's max_tokens change.

**Environment:** venv/bin/python in the run directory (pandas, numpy, scipy, statsmodels, matplotlib). Do NOT pip
install into it; make your own venv under review/reviewer_checks/ if needed. No GPU is needed; do not start or stop
any Docker container.

Check at least:

1. **Design (D1).** Is the within-record manipulation a fair test of the lead's question? Does inserting element types
   that almost no real record carries (BC/TK Notices, TK NC, TK CO) with name + URI only (no Notice text) make the test
   too easy, or unrepresentative? Neotoma is 200 of 221 base records - does that matter? The conventional clauses lack
   URIs; the LC ones have them (LC_CB_NOURI addresses part of this).
2. **The scorer.** Read score.py. Are the patterns too generous (e.g. GEN_LC matches "indigenous", "\btk\b";
   CONTACT matches "collaborat")? Could a response that merely echoes the rights list verbatim count as a "mention"
   when the model says nothing about it? (strip_echo removes fenced JSON with "rightsList" only; the agent framing
   lists the element string verbatim in "conditions" - is that a meaningful "mention"?) Re-score a random sample of
   main-set responses yourself (at least 150, stratified by model, framing, condition) and estimate the scorer's
   accuracy, especially for OLMo researcher responses where omissions occur.
3. **Pilot adjudication (D4).** The agent adjudicated 200 pilot responses itself, all 200 "mention". Was it blind to
   the scorer? Is an agent adjudicating its own study's outcome acceptable here, and is it disclosed properly? With no
   negatives, specificity is unestimated - is the NONE false-positive rate an adequate substitute?
4. **H1-H3 and the decision rules.** Recompute the three estimates and intervals from scored_main.csv / the generations.
   Is the record-cluster bootstrap right (D5 fix)? H3 counts any change in either agent field relative to NONE,
   including yes->unclear - is "Refuted" a meaningful verdict when most changes are to "unclear"?
5. **Post hoc (D6).** Recompute the verdict tables. Is the matched-invitation comparison (LC_CB vs CV_CONTACT) fair -
   the conventional clause literally says "contact the data providers before reuse", while the TK CB label says the
   community is open to collaboration? Is the report's normative reading ("under-read", "softened") supported by
   Local Contexts' published texts (data/raw/localcontexts/)? Is the "not binding" lexical measure valid? Is the OLMo
   "invented CC terms" finding (51%) right - check the regexes against actual responses.
6. **Operational deviations (D2, D3).** Did the GPU-stage failures or the max_tokens change touch outcomes? The 204
   discarded Qwen rows: were any read? Is generation reproducible (greedy, seed, image recorded)?
7. **Novelty and facts.** Web-search for any study of LLMs and Local Contexts / TK Labels / Indigenous data governance
   metadata, or LLMs surfacing licence/rights fields. Verify the quoted Local Contexts texts and the Neotoma
   Label/Notice URI point.
8. **Scope and care.** Is the framing respectful and non-stigmatising? Any overclaim about what communities want? Is
   the disclosure about adjudication passing through the agent's model service adequate given plan section 3?
9. **Numbers.** Does every number in report.md and the figures match the results files?
10. **Plain-language summary.** Accurate and not overstated? Especially "It does not reliably treat Indigenous notices
    as conditions in the way it treats ordinary ones."

Write your review to review/review.md with:

- a recommendation (publish / publish with edits / fix first);
- numbered issues, each with its location and a concrete fix;
- a table of the numbers you recomputed.
