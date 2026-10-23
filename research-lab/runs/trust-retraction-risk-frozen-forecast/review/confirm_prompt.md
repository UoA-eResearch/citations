You are the independent reviewer of /mnt/citations/research-lab/runs/trust-retraction-risk-frozen-forecast/, doing
the CONFIRMATION PASS. Your review is review/review.md ("fix first"), and your scripts are in review/reviewer_checks/.
The fixes are logged as D3 in deviations.md.
- code/posthoc_review.py adds: fit curves; the PMC-host audit; exclusions without PMC, without Hindawi and without
  both; an iid contrast; H2 composition; the H3 inputs, with SHA-256 of the sealed (wid, doi) key and of the works
  already retracted at sealing.
- The output is results/tables/posthoc_review.json.
- report.md is rewritten.

Be economical. Check that:
- each finding is addressed, or its non-fix is justified;
- the post hoc numbers in report.md match posthoc_review.json;
- every post hoc result is labelled as such and the preregistered verdicts are unchanged;
- the H3 addendum is unambiguous and the hashes match the files in data/forecast/;
- no per-paper risk scores and no quoted paper text are in tracked files.

Write review/confirmation.md: a verdict (publish / publish with edits / fix first), one line per finding (fixed / partly
fixed / not fixed), then any new issues. Reply with the verdict line and the new issues only.
