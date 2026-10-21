You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/legal-phantom-citations-judicial-opinions/ (read-only except your output in
review/).

**The question.** How many US judicial opinions filed 2023-01-01 to 2026-09-30 rely on citations to cases that do not
exist? It is measured by a systematic screen of the CourtListener 2026-09-30 snapshot (1,665,327 opinions, 23.96
million full citations), with 2019-2022 as a placebo.

- **Reported:**
  - H1 Refuted by rule: 0 verified reliance opinions in a seeded sample of 300 of 3,182, with a sample upper bound
    of 40. Flagged as not robust, because recall for judge incidents is 0 of 4.
  - H2 not scorable: both periods are zero.
  - Courts flag litigants' nonexistent citations in 45 opinions in 2023-2026 and none in 2019-2022; 19 of the 45 are
    not matched to the Charlotin database.
  - The opinion corpus contains party filings (D8).
  - Proposed tag: Inconclusive.

**What to read:**
- plan.md, deviations.md (D1-D8), report.md;
- code/: build_index.py, build_names.py, extract.py, screen_shards.py, parse.py (the screening logic, `judge()`),
  analysis.py, verify_aid.py, figures.py;
- results/tables/ and results/figures/;
- results/verification/: the hand labels per sheet, verified.csv and verified_misattributions.csv;
- data/screen/: candidates.jsonl, the verification sheets verify_*.csv, volumes.json, opinions.tsv;
- data/opinions/: 32 gzip shards of opinion text, by cluster_id % 32 (field `raw`).

**Git.** Read-only git is fine. Check that:
- plan.md preceded extraction;
- the screen was frozen (D6) before the full run;
- analysis.py's sampling rule (VERIFY_ALL_UP_TO = 300, seed) preceded the sheets;
- D8 and the labels preceded `analysis.py score`.

**Environment.** Python: /mnt/citations/research-lab/runs/legal-phantom-citations-judicial-opinions/venv/bin/python
(eyecite, rapidfuzz, numpy), with -I. Do NOT pip install. Put scripts and outputs under review/reviewer_checks/.
You may query CourtListener's public search API politely
(https://www.courtlistener.com/api/rest/v4/search/?q=...&type=o).

Check at least:

1. **Verification.** Re-verify a random sample of at least 40 labelled rows across the four sheets. Include every
   row labelled phantom, phantom-party-filing, party-filing-unverified or unverifiable. Are the "real" calls on court
   typos and OCR damage right? Is any "real" actually a phantom?
2. **H1 and the sample.** Is the sampled estimate (0 of 300, scaled to 3,182) computed correctly? Given the 0-40
   interval, is "Refuted by rule" the right reading, or should the verdict be Inconclusive?
3. **Recall.** Is the recall analysis right: 453 of 854 incident orders flagged, and 0 of 4 judge incidents
   producing reliance candidates? Is the explanation supported (an existence-only screen, Westlaw citations, the
   completeness filter)?
4. **The completeness filter**, which drops 99% of candidates. Is the coverage computation correct
   (leave-one-opinion-out, D6)? Does it remove the very volumes where judicial phantoms would show?
5. **Flag-type counts.** Are the 45 opinions right: one document per cluster and no double counting? Is "19 not
   matched to Charlotin" fairly worded?
6. **Party filings (D8).** Is excluding them from judicial reliance justified and applied consistently? How large
   could the share of filings among the 1.67 million documents be? Sample a few.
7. **The report.** Check every number against the tables, the plain-terms section, and whether the headline is
   supported.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.
