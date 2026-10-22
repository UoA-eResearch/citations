You are the independent reviewer of /mnt/citations/research-lab/runs/legal-phantom-citations-judicial-opinions/,
doing the CONFIRMATION PASS. Your earlier review is in review/review.md (verdict "fix first", 12 findings; your
scripts and outputs are in review/reviewer_checks/). The fixes were applied in commits 7a6e6b8 and its predecessors
(see `git log --oneline -8 -- .`), and are logged as D9 in deviations.md. Be economical: verify the fixes; do not
redo the review.

Check, finding by finding:
1. H1 is now Inconclusive (report.md, results/tables/primary.json "H1": the rule for a sampled sheet).
2. The screen's blind spots for the known judicial incidents (the empty California name, misattribution, the shared
   surname) are reported, with sensitivity 0 of 3 on the in-corpus documents.
3. Recall is given per distinct cluster, before (465/869) and after (42/869) the filter; the recall-corrected bound
   (~830) is stated; the matcher fix (New Mexico, same-day caption rule) is in code/match_charlotin.py.
4. The judge-incident documents are classified (JUDGE_DOC in code/analysis.py), and reliance recall is 1/1 before
   and 0/1 after the filter. Does this match your reading of the documents?
5. The flag-versus-database comparison is in code (`flag_vs_database()`), now 43 of 43 in the database, 2 found by
   hand (HAND_DB). Spot-check the name matches and the two hand matches.
6. Labels: the vocabulary (phantom-flag, phantom-party-asserted); k=115 and k=156 are party-asserted; the two F.R.D.
   rows are real; code/assemble_verified.py reproduces verified.csv. Check that the label commit preceded re-scoring
   (git log).
7. The flag count is 43 plus 2 party-asserted; the 2019–2022 wording is qualified.
8. The reporter table is in the report.
9. The party-filing floor (your shard-00 scan) is reported.
10. The empty court field and the capture–recapture estimate are recorded in D9.
11. Provenance: are the labels committed before the scoring commit?
12. Wording and numbers: re-check every number in report.md against primary.json, and that the title and the
    plain-terms section match the new verdict.

Also look for any NEW problem the fixes introduced, for example the same-day caption rule creating false matches
(inspect the 15 newly matched incidents in data/screen/charlotin_matched.csv against charlotin.csv dates).

Write review/confirmation.md: a verdict (publish / publish with edits / fix first), then one line per finding
(fixed / partly fixed / not fixed, with evidence), then any new issues with the fix. Reply with the verdict line and the
new issues only.
