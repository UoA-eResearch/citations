You are the independent reviewer of /mnt/citations/research-lab/runs/trust-corrected-record-machine-readable/, doing
the CONFIRMATION PASS. Your earlier review is in review/review.md (verdict "fix first", 9 findings; your scripts are in
review/reviewer_checks/; the xml_pass outputs are now committed without their snippet column, and the originals sit in
data/review_snippets/). The fixes are in commit 9ba23d6 and are logged as D5 in deviations.md. Be economical: verify
the fixes; do not redo the review.

Check, finding by finding:
1. code/pes2o_secondary.py: the D5 rule. "notice of retraction" has no closing boundary, and a run-together title
   prefix is accepted. Does it reproduce your corrected share (47.2% here against your 47.4% broad)? Is it faithful
   to the plan's §2 rules without over-matching? Spot-check documents that only v2 marks.
2. The staleness claim is now reported within retraction years ≥2015 as null. The by-year text and the downstream
   test are on the PMC-overlap subset (3,235 here against your 3,238; drop_duplicates on DOI). Are the title,
   verdict, plain terms and F4 now fair?
3. These secondary results are now produced by committed code: pes2o_secondary.py → pes2o_secondary.json.
4. code/post_review.py: the 412 self-update-dated documents are moved to the undated stratum. Check H1 1.85%
   (0.96–3.28), H2 96.9%, H3 0.76 pp, D3 own 2.16%, residue 382 + 119, and the publisher table.
5. The 0.4% notice contamination is stated, and the 8a misses are reworded.
6–8. The number edits, the cluster-key note and the validation wording.

Also look for any NEW problem the fixes introduced: for example, the report mixing D5-cohort figures with
preregistered-cohort figures without saying which is which.

Write review/confirmation.md: a verdict (publish / publish with edits / fix first), one line per finding (fixed / partly
fixed / not fixed, with evidence), then any new issues. Reply with the verdict line and the new issues only.
