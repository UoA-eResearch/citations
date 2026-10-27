Confirmation pass. You reviewed this study earlier today (verdict: fix first; review/review.md). The fixes are in
report.md (rewritten), deviations.md D2, code/analyse.py (PEP 440 version canonicalisation), code/posthoc_review.py
(results/tables/posthoc_review.json, coverage.json), code/audit_strata.py (results/tables/precision_audit_strata.json),
code/extract.py (matched_line), code/figures.py, results/plausibility.md and results/attribution_ledger.csv (S11). v1
tables are in results/tables/v1_pre_review/. Check that each finding is addressed correctly, that nothing new is wrong,
and give a verdict (publish / publish with edits / fix first). Be economical; the machine is busy (at most 2
processes). Append your confirmation to review/review.md. Paraphrase rather than quote any source text; do not copy
commit messages or personal names.

By your finding:
1. **R.** Title, verdict, plain terms and "What this does" now use the like-for-like tree multiplier: 1.61 (1.51–1.73)
   npm, 1.58 (1.43–1.78) PyPI, joint bootstrap. A decomposition row is in the exposure table. R is kept as the
   preregistered statistic, with the caveat.
2. **npm repository-level p.** The 6.0% / 38.6% split is in the verdict and table; p among packages that released in
   the window (30.9% / 24.0%); top-5 exclusion; the no-monorepo R labelled a lower bound.
3. **G2.** coverage.json stages: release_ranges (date fallback, 22,747 empty ranges), packages_in_p (4,937 with no
   release in the window), tree_nodes (by version, with reasons). Flag rate by range size. The mislabelled key is
   renamed releases_analysed.
4. **H2.** Distinct commits (89,401), same-release share (80%), the different-release ratio 0.90, unmatched latency
   (4.8 vs 6.8 days), the plan-wording ratio 1.12 (1.05–1.19). The deviation is logged in D2.
5. **Hubs.** Replaced by leave-one-out (at most 1.7 points) and the top-10 list.
6. **Precision.** matched_line fixed (not re-extracted). A stratified 120-item audit (7 strata, risky rules
   oversampled), matched text re-derived with `git cat-file` (local only). Two fresh blind labellers, separate shuffled
   orders: both 120/120 AI, 100% agreement (kappa undefined, one class). Per-stratum Clopper-Pearson bounds. Labels
   and items stay in data/interim (not committed).
7. **Review bots.** "AI-signed" wording; suggestions counted for Copilot/gemini but not CodeRabbit/Greptile, stated.
   Copilot split: your re-derived count (about two thirds) is cited.
8. **False negatives:** about 3%, stated.
9. **Claude-model signatures,** mostly Claude Code.
10. **Text fixes:** "a fifth to a third"; provenance one-second note; monorepo definition (D2).
11. **PyPI version padding fixed:** P_w 36.1%, R 1.94 (1.67–2.24); node coverage by version in coverage.json.
12. **Tags:** acknowledged as a limit, with your counts; not re-extracted.
13. **Trend:** repository-level share (28% / 33% in September 2026) in F1 and the text; concentration and
    self-hosting agents stated.
- **Gates:** G3 plausibility.md added; G5 regenerated (51 rows, passes); G6 passes (11 claims; S11 is the census's
  bot-lookup recall, checked against the abstract; the ledger tool now falls back to OpenAlex when arXiv rate-limits).

Note: an early draft of the audit script used `git show`, which lazily fetched objects from GitHub for some commits.
It was stopped and replaced by `git cat-file`; this is recorded in D2.
