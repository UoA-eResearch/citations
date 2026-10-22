You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/ancestral-dsi-origin-recoverability/ (read-only except your output in
review/).

**The question.**
- **Limb 1:** did the June 2023 INSDC rule raise the share of NCBI BioSamples with a usable country of origin?
  This is a regression discontinuity on 20.9 million non-human samples.
- **Limb 2:** can missing origins be recovered automatically? This uses a 500-record gold set labelled by the
  agent in two blind passes plus a third, and three recovery arms (gazetteer, TF-IDF classifier, local LLM).

**Reported:**
- **H1** (usable jump under 10 points): **Inconclusive**, +2.9 points (−5.9 to +10.8). Placeholders rose +9.1
  points, absent fields fell −12.0 points, and the placebo dates swing ±16 points.
- **H2** (an arm recovers at least 40% at 90% precision): **Refuted**.
  - Only 24 of 300 test records have a determinable country. The tuned arms recover 0%, 1.7% and 0%.
  - Projected over untagged samples: 61% laboratory material, 30% not stated, 9% with a findable country.
- **Post hoc (D7):** among natural samples, the LLM reaches 77% precision and finds 73% of the determinable ones.
- **Proposed tag:** Refuted (on H2), with H1 Inconclusive.

**What to read:**
- plan.md, deviations.md (D1–D9), report.md;
- code/: parse.py, countries.py, analysis_rd.py, analysis_rd_posthoc.py, goldset.py, arms.py, score.py,
  posthoc_natural.py, mirror.py, decomposition.py, gold_cut_audit.py;
- results/tables/ (rd_*.json, gold_agreement.json, limb2_*.json, limb2_rows.csv, mirror_agreement.json,
  fulltext_check.json, gold_pass2_cut_audit.txt);
- results/gold/: pass1/2/3 labels and keys;
- results/figures/;
- data/gold/: records.jsonl (the evidence per record), pass1.md, pass2.md and pass3.md (the sheets), arms.jsonl.

**Git.** Read-only git is fine. Check that:
- plan.md preceded parsing;
- score.py and arms.py were committed before pass 2 and before the arms ran;
- the pass-1 seal (gold_pass1_seal.txt) matches results/gold/pass1_labels.csv;
- D5 and D6 preceded the arms run.

**Environment.** Python: /mnt/citations/research-lab/runs/ancestral-dsi-origin-recoverability/venv/bin/python
(pandas, numpy, pyarrow, sklearn), with -I. Do NOT pip install. The local LLM at localhost:8000 is shared: do not
stop it, and keep any calls to a handful. Put scripts and outputs under review/reviewer_checks/.

Check at least:

1. **Gold labels.** Re-label a random sample of at least 40 records from data/gold/records.jsonl, blind to the final
   labels at first, then compare. Include every record whose final label is a country and every judgement call
   (search the basis column for "JUDGEMENT CALL").
   - Is "inapplicable" (laboratory material) applied consistently?
   - Are any "not stated" records actually determinable from the evidence?
   - Are the three pass-3 readings in D5 §5 defensible? These are livestock at a named farm, F1 crosses from wild
     broodstock, and genebank accessions.
2. **The construct.** Is treating laboratory material as having no country of origin the right construct for H2? Or
   does it make H2 unreachable by definition? Is "Refuted" the right reading, or should a ceiling-bound result be
   Inconclusive? Is the plan's wording (recovery over all 300 test records) applied as written?
3. **Arms.** Check arms.py for leakage: submitter institutions or affiliations entering the evidence, or gold labels
   leaking into the classifier's training data. Was the LLM given a fair budget (D6)? Are the tuning thresholds
   computed as the plan says?
4. **Limb 1.** Check analysis_rd.py: the local-linear fit, the kernel, the donut and the owner-cluster bootstrap. Do
   the placebo jumps (+17.6 and −15.7) mean the design cannot support any causal reading? Is the report's "the rule
   produced placeholders" claim itself supported, given those placebos and the within-owner result?
5. **Projection.** Is the stratified projection right, with the population counts, the strata weights and the
   intervals? Is the 9.2% figure fairly worded given the evidence caps (D5 §3, D8)?
6. **D5 display truncation.** Is the audit convincing that the pass-2 cut enters no final label? Re-run
   code/gold_cut_audit.py.
7. **The report.** Check every number against the tables, the plain-terms section, and the comparison with the
   CBD's 44% figure.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.
