Second confirmation pass for ecology-biodiversity-sdm-provenance-leakage (/mnt/citations/research-lab/runs/ecology-biodiversity-sdm-provenance-leakage).
Your confirmation pass (review/review.md, fix first; 8 remaining issues) is addressed in deviations.md D5. Give a final
verdict and append a "## Second confirmation pass" section to review/review.md. Same rules as before (no refits).

1. Stale cache: rf.py cache key now includes EVAL_VERSION; the 2,086 reused per-condition results were moved to
   data/work/rf_stale_d4/ and refit; analyse.py and posthoc_shortfall.py re-run. Only C0 rows of 553 species changed
   (n_src changed); C1-C6 and the DiD are unchanged (-0.00645, -0.00903 to -0.00402). n_src is constant across
   conditions for all 2,000 species. (Your "207 species with C1 and random arms on different masks" did not show up
   after the refit: no C1-C6 row changed. Please re-check against results/tables/rf_auroc.csv.)
2. Denmark: by-source DiD +0.031 (+0.014 to +0.048), 249 species; verdict and table updated (three databases > 0.02).
3. Australia: "control artefact" withdrawn; unexplained; pooled ratio 0.47 vs per-species median 0.80; your matched
   -0.013 and no-Australia +0.005 cited as confirmation-pass figures.
4. Shortfall: Denmark 58%, Australia 35% (cited from your pass).
5. Stale text fixed (30 core / 13 sources / 2 broad; 4,302,471 = 7.5%; 46%; 5,390 undefined, 1,230 species;
   reproduction steps).
6. plausibility.md section 4 for the corrected run, with the n_src invariant.
7. Neutral variant: background cap / 0.07% stated.
8. PLADIAS.SK line, ledger rows R13-R15, results/republication_scan_log.txt.
G5 passes, G6 passes (15 claims).

Reply with the verdict and a one-line note per remaining issue, if any.
