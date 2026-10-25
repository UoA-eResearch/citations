Confirmation pass. You reviewed this study earlier (review/review.md, verdict "fix first"). The agent has made fixes,
logged as D1 in deviations.md, and rewritten report.md. Check only whether your findings are resolved and whether the
fixes introduced new problems. Be brief and economical.

What changed:
- **Finding 1 (KBAZ).**
  - dvv.py segments now break on dip changes and on station data gaps > 7 days; segments.csv is used everywhere.
  - Dead-channel days (zero coda energy) leave references and stacks, and negative zero-stretch days are dropped.
  - coverage.json counts every drop.
- **Finding 2 (Brenguier).** Ledger A2 is now "supports", from the published abstract; the report is rewritten.
  METHODS.md G6 now requires checking the version of record. A5 is fixed.
- **Finding 3 (floors).** The no-model 2 SD (0.074%) and the season-only residual (0.067%) are reported beside the
  residual floor (0.076%), and the title is rewritten.
- **Finding 4.** Stretching now uses a cubic spline; the grid is stated.
- **Finding 5.** A post hoc breakdown by zero-stretch coherence of the 11-day stack (cc0 ≥ 0.7: 22 pairs, median
  −0.27).
- **Finding 6.** RULE=every_epoch recomputes dv/v with every-epoch references (−0.18).
- **Finding 7.** results/plausibility.md, code/handtrace.py (3 pair-days), coverage.json.
- **Finding 8.** Minor numbers, the F1 title, the 11-day stack and the guarded lockdown.
- **New primary:** −0.27 (−0.35 to −0.15), 31 scored pairs; still Refuted.
- v1 outputs are in results/tables/v1_pre_review/.

Environment as before (venv/bin/python -I; no installs; data/ccf for correlations; keep reviewer caches out of git).
Append a "## Confirmation pass" section to review/review.md with a verdict (publish / publish with edits / fix
first), then numbered items: resolved, not resolved, or new problems, each with the fix if needed.
