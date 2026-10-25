Confirmation pass. You reviewed this study earlier (review/review.md, verdict "fix first"). The agent has made fixes,
logged as D2 in deviations.md, and rewritten report.md. Check only whether your findings are resolved and whether the
fixes introduced new problems. Be brief and economical.

What changed:
- **Renewal matching (registrations.py).** Your finding 6 was partly off. The auth/titl schema covers 1950s–60s
  registrations and cannot match 1923–1930 numbers within ±1 year. The 1,405 date-matched rows with no title are
  first-schema rows with an empty title field, so the fix falls back to full_text and ignores author-name tokens.
  1,278 registrations were reclassified (144 linked). The links file is byte-identical.
- **Reference-cell separation** handled in did.py fit(). nopod drops cohorts 2022–24 and lag drops 2025.
- **did.py sensitivity:** results/tables/sensitivity.csv (count, binary, cap5 × LOCO, year limits, no reprints,
  nopod, lag, placebo). did.py binary and cells modes were added.
- **OLS** is now on a relative scale (secondary_ols.json, secondary.json).
- **validate_links.py score:** unshown links are excluded. Precision is 73/74; recall is conditional.
- **Gutenberg rates per 1,000 at risk by lag.** These show no early burst once normalised, contrary to your finding
  11. Please check that computation (secondary.py gutenberg).
- **Report rewritten:** title, verdict, plain terms, tables. The verdict stays Inconclusive for the count outcome,
  and the binary outcome is reported as exploratory.
- **v1 tables** are in results/tables/v1_pre_review/.

Environment as before (venv/bin/python -I; no installs). Append a "## Confirmation pass" section to review/review.md
with a verdict (publish / publish with edits / fix first), then numbered items: resolved, not resolved, or new
problems, each with the fix if needed.
