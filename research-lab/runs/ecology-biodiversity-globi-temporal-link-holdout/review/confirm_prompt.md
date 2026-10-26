Confirmation pass. You reviewed this study earlier today (verdict: fix first; review/review.md). The fixes are in
deviations.md D2, and the first version's tables are in results/tables/v1_pre_review/. Check that each finding is
resolved, that nothing new is wrong, and give a verdict (publish / publish with edits / fix first). Be economical:
read the diffs and tables, re-run only what you need. Append your confirmation to review/review.md. Paraphrase
rather than quote any source text.

What changed, by your finding:
1. **trophiCH.** Disclosed in the title, verdict, plain terms and limits. model.py reports the result without
   trophiCH positives with the same paired cluster bootstrap: A_temporal 0.0585 (0.050–0.068), ρ 1.46 (1.05–2.08).
   - This is narrower than your bound-by-bound 0.92–2.3, because the draws are paired. Please check that the pairing
     is right.
   - The title now says "keeps its edge"; "grows" is gone. The GloBI self-citation share (51,465, from your review)
     is in the limits. Ledger L9 covers the trophiCH abstract.
2. **Degree-matched sampler.** It is rewritten (model.py sample_negatives): every decile is filled without
   replacement, from uniform and degree-proportional candidates.
   - MATCH_REPORT in primary.json (degree_matched_sampler) shows every decile filled in every class and holdout.
     Negatives' mean log degree is within 0.13 of the positives'.
   - Effort is now 0.50 random and 0.51 temporal; taxgb 0.93 and 0.83. The advantage shrinks out of time under
     matched negatives (0.43 to 0.32, ratio 0.74), and the report says so.
   - F2 is redone: legend moved, title corrected, a without-trophiCH group added.
3. **Citation leak.** Disclosed in D2 and the limits with your measured effect; not re-run.
4. **Re-resolution and turnover.** The caveat is replaced by your measured 1.1%, with the turnover explained
   (removed, refuted, re-typed).
5. **Clusters.** 266 clusters, largest 44.7%, top three 73.8%. results/tables/per_dataset.csv gives the advantage
   for the 26 datasets with at least 1,000 positives (24 positive).
6. **Small points.** Both noted in the limits.
7. **Gates.**
   - G1 audit in D2.
   - G2: code/coverage_build.py accounts for every record per snapshot (coverage.json build_v0.6 and build_v0.11);
     graph_summary.json and eval_sets_summary.json are now written.
   - G3: results/plausibility.md.
   - G5: regenerated, 42 rows, passes. G6: 9 claims, passes.

Note: the primary rerun gives taxgb temporal 0.9474 (first version 0.9476): thread nondeterminism in
HistGradientBoosting. ρ 1.677. Check the report's numbers against primary.json, per_class.csv, per_dataset.csv and
coverage.json.
