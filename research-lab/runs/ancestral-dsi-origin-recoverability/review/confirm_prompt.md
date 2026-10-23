You are the independent reviewer of /mnt/citations/research-lab/runs/ancestral-dsi-origin-recoverability/, doing the
CONFIRMATION PASS. Your review is review/review.md (verdict "publish with edits", 10 findings). Your reviewer_checks
are in review/reviewer_checks/. The four evidence dumps that quote record and publication text were moved to
data/review_evidence/ and kept out of git. The fixes are in commit b0149e2, logged as D10. Be economical: verify the
fixes; do not redo the review.

Check, finding by finding:
- **F1.** The title, verdict, plain terms and "What this does and does not show" no longer present the placeholder
  shift as an effect of the rule. The placebo sd is reported beside the interval.
- **F2/F4.** The nine relabelled records (D10_NOT_STATED in code/score.py) are applied in final_labels(), and the
  pre-D10 tables are kept (*_pre_d10). Check the new figures:
  - ceiling 19/300;
  - all arms 0% at the preregistered thresholds;
  - projection 60.7 / 31.6 / 7.7%;
  - D7: 147 natural records, 19% ceiling, LLM 23/35.
  Also check that the report says what changed.
- **F3.** The "inapplicable" category is described as "no collection origin applies or none is recorded", and the 21
  field, agricultural or genebank records are counted.
- **F5.** The comparison with the CBD's 44% uses stated sampling countries in the publication-linked stratum (3/250).
- **F6.** "Six in ten" appears, and the LLM's zero calls at the preregistered threshold are mentioned.
- **F7.** The geo_location count and the "already recorded" caveat are present.
- **F8.** The two discarded LLM answers are reported.
- **F9.** The one-sided rule and the raw fall from 85.3% to 79.4% are reported.
- **F10.** The frame-mismatch sentence is present.

Also look for any NEW problem the fixes introduced, for example numbers in the report or figure captions that still
show the pre-D10 values.

Write review/confirmation.md: a verdict (publish / publish with edits / fix first), one line per finding (fixed /
partly fixed / not fixed, with evidence), then any new issues. Do not write publication text into files under
review/. Reply with the verdict line and the new issues only.
