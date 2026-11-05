Confirmation pass for cheminformatics-drug-discovery-pcba-2026 (/mnt/citations/research-lab/runs/cheminformatics-drug-discovery-pcba-2026).
The first review (review/review.md, publish with edits) is addressed in deviations.md D4. Check each fix and give a
final verdict (publish / publish with edits / fix first / do not publish); append a "## Confirmation pass" section to
review/review.md. Same rules as before (write only under review/, no ~/.config, no pip installs, <= 4 processes, no
GPU, data/ untrusted).

Where each finding went (code/posthoc_review.py -> results/tables/posthoc_review.json):
1. Comparable ceiling (5 halvings/target): half-set vs LIT consensus 0.185, full set 0.196, half vs half 0.315 (your
   0.183 / 0.336). H3 bullet, title, plain terms and "What this shows" rewritten: rankings replicate within a target
   better than they transfer between benchmarks.
2. Memorization never beats ECFP4 + RF (all 7 arms, -2.35 to -11.12): verdict bullet and title; "advantage" -> "enrichment
   over random" (the plan's A_B).
3. H2 scoped to frozen mean-pooled embeddings with a linear head (verdict, title, plain terms); 47/56 inconclusive both
   ways; fine-tuning added to Not shown.
4. Audit shares labelled as target medians with pooled figures (PCBA-2026 40% vs 20%); actives retained 46% vs 40%;
   hit rate 2.4% -> 3.2%; ceiling 41 -> 32.
5. D2 subset numbers in the verdict (Q 0.84, -3.60 to 8.02; tau 0.139, -0.004 to 0.283).
Also found while checking: analyse.py's subset run overwrote tau_h3.csv with the 19-target subset; h3() now takes a
file name; tau_h3.csv regenerated for all 28 targets (mean 0.196), subset in tau_h3_le5pct.csv; primary.json unaffected.
G5 passes (43 rows), G6 passes.

Reply with the verdict and a one-line note per remaining issue, if any.
