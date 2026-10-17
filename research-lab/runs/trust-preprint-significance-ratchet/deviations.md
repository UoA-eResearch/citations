# Deviations log

Every departure from the lead and from plan.md, timestamped with `date` when it was made.

## D1 — 2026-10-17 15:51 NZDT — before any statistic was extracted

1. **Linkage routes are not independent.** Europe PMC's "Preprint of" links say "CrossRef Pre-print loader";
   PreprintToPaper's "Published" label is bioRxiv's own link; Crossref's is-preprint-of on bioRxiv DOIs is deposited
   by bioRxiv ("asserted-by subject"). The lead's ">= 2 of 4 routes" would mostly count one assertion twice. Every
   server-asserted link is instead confirmed by an independent title-similarity check (Jaccard >= 0.5): 28,597 of
   31,261 candidates pass.
2. **Version.** 57% of usable pairs have no version in Europe PMC; Research Square DOIs encode it (/vN), bioRxiv and
   medRxiv DOIs do not. The primary uses pairs known to be version 1 (about 11,500); all 23,220 pairs are a labelled
   sensitivity.
3. **No embedding model** for alignment residue; masked TF-IDF plus exact tuple matching, validated blind (plan 6).
4. **Bulk route note.** The bioRxiv /pubs route is slow (~6 s per 100 links) and was still running when linkage was
   confirmed; Crossref carries the same bioRxiv-deposited links, so its absence changes few pairs. If it finishes before
   the pipeline, confirm is not re-run (the pair set is fixed here).
5. **Validation by the agent, not a human**, as plan section 6 states, blind to version order and stratum.

## D2 — 2026-10-17 15:58 NZDT — after the validation was adjudicated, before analysis.py was run

1. **Validation display changed before adjudication began.** The first draw showed the two sentences but not which
   statistic in each had been aligned, so a sentence holding several p-values could not be judged. The display now
   shows the aligned statistic for each side. The redraw used the same seed and produced an identical sample and order
   (`key.csv` compared byte for byte with `cmp`); no item had been judged before the change.
2. **Outcome: the abort rule triggers.** 200 blind pairs were adjudicated (`results/tables/alignment_validation_raw.csv`,
   merged with the key in `alignment_validation.csv`). Precision among crossings is **12 of 100 (0.12)**, far below
   0.90; among other aligned pairs it is 79 of 100. Per plan section 6, H1 is tested on exact tuple matches only and
   the all-crossings estimate is reported as unreliable.
3. **Why crossings fail.** Most failures are alignment: in tables, figure legends and sentences with several p-values,
   the right sentence is found but the wrong p within it, or a dropped row shifts every later cell. About a fifth are
   extraction errors that manufacture a crossing on one side: mojibake exponents ("1.0Ã10â5" read as p = 1 or as the
   mantissa), middle-dot decimals ("p=0·76" read as p = 0), comma decimals ("p=0,33"), partial eta squared read as p,
   and lost exponents. Because a crossing needs a change in status, it selects for exactly these errors.
4. **One adjudication corrected on re-check** (v072, the wrong p in the same sentence, 1 → 0) before any statistic was
   computed. Adjudication is by the agent, not a human (D1.5).
5. **Disclosure.** After the adjudications were written and before this commit, I printed the class tally by match type
   over all versions (not the v1 primary): exact tuple matches give 8 crossings up and 5 down; similarity matches 1,490
   up and 1,437 down. This shows the direction of the exact subset before `analysis.py` ran. The analysis and its
   verdict rule are fixed in the committed code and are not changed by it. With at most 13 exact crossings, the
   primary is expected to be too imprecise for a Supported or Refuted verdict.
