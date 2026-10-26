# Deviations from the preregistration

## Data acquisition — 2026-10-24 03:54 NZDT (before any graph is built)

- **The v0.6 interactions file.** Two complete parallel-range downloads of `interactions.tsv.gz` (Zenodo 8284068)
  both failed the MD5 check, with different wrong 32 MB chunks:
  - chunk 42 in the first copy;
  - chunks 3, 23, 41, 43 and 56 in the second.

  A third, single-connection fetch of those six chunks agreed with the correct copy for each. The file assembled by
  majority matches Zenodo's MD5 (445b2c97e2e44d2dbc4aa93084ecacfc). Every other file is MD5-checked the same way.
- **v0.7 and v0.9 are not downloaded.** Zenodo serves about 100–200 KB/s in total, and the plan does not use them.
- **The v0.11 interactions file.** The first download failed the MD5 check, with four wrong chunks against the second
  copy. The second, independent download passed (c07ce1a5895b5bbcb822c7fb90f920c9) and is used.

## D1 — 2026-10-24 08:34 NZDT — secondary 4 not run (after the primary result)

The v0.8 rolling origin needs a further 3 GB from Zenodo at about 100–200 KB/s, plus the same chunk verification. It
is not run. The edge turnover between v0.6 and v0.11 is reported descriptively instead: by class, 26–42% of v0.6
pairs are absent from v0.11.

## Pre-review gate (G5, G6, plus a G3 gap) — 2026-10-25 22:45 NZDT, after all results (wording, attribution, one descriptive table)

The lab's METHODS.md gates were run before this draft's review. No result changed.
- **G5 overclaim check** (`review/overclaim_check.md`, passes):
  - the title said "species-interaction predictors" beat effort, but only the taxonomic model does (RDPG trails
    effort), so it now names that model;
  - "genuinely new records" became "records first seen in the newer snapshot", given the turnover caveat;
  - "are old ones under new names" became "may be";
  - an unclear sentence about what future records favour was replaced by the measured loss comparison.
- **G6 attribution ledger** (`results/attribution_ledger.csv`, 8 claims, passes): the report's "none was found" now
  carries the lead's own limitation (the search could not include a final 2026 check).
- **G3 gap.** The 26–42% edge-turnover figure in D1 had no generating code. `code/turnover.py` now writes
  `results/tables/turnover.json` (host 36%, pollination 42%, trophic 26%), which reproduces it.

## D2 — 2026-10-26 22:05 NZDT — after independent review ("fix first"); POST-RESULT

The first version's tables and figures are kept in `results/tables/v1_pre_review/` and `results/figures/v1_pre_review/`.

- **trophiCH (review finding 1).**
  - 183,892 of the 411,702 temporal positives (44.7%) come from trophiCH, a Swiss national metaweb (Scientific Data
    2025).
  - Only 30% of its species-level links are empirically documented; the rest are inferred from coarser taxonomic
    records using habitat co-occurrence (paper abstract). GloBI indexes the inferred links unfiltered.
  - `model.py` now reports the advantage without trophiCH positives, using the same cluster bootstrap (ratio percentiles per replicate, holdouts resampled independently):
    A_temporal 0.0585 (0.050 to 0.068) and ρ 1.46 (1.05 to 2.08).
  - The review's bound-by-bound combination (0.92 to 2.3) is more conservative than the per-replicate ratio interval.
  - H1 stays Refuted. The title no longer says the advantage "grows": it holds.
- **Degree-matched sampler (finding 2).** The first version starved the top degree deciles and drew with
  replacement (host negatives 73% of the required count; top deciles at 1–5% instead of 10%).
  - The sampler now fills every decile without replacement, from uniform and degree-proportional candidates. Every
    class fills completely, with negatives' mean log degree product within 0.13 of the positives'.
  - Corrected results: effort falls to chance (0.50 random, 0.51 temporal). Taxonomy + structure scores 0.93 random
    and 0.83 temporal.
  - **Under degree-matched negatives the advantage shrinks out of time:** 0.43 to 0.32, a ratio of 0.74.
  - The first version's "grows with degree-matched negatives" was an artefact of the broken sampler.
- **Citation counts in the random holdout (finding 3, G1).** Species citation counts were computed over all v0.6
  records, so hidden and inner-label edges contributed to their endpoints' effort feature.
  - The review measured the effect by recomputing citations from training records only: A_random 0.0409 to 0.0407,
    effort 0.9501 to 0.9497.
  - This is disclosed, not re-run. The random-holdout effort baseline is marginally optimistic.
- **Name re-resolution (finding 4).** The review measured that 1.1% of positives have any v0.6 record behind them by
  verbatim name or taxon ID. Dropping them moves A_temporal from 0.0662 to 0.0658.
  - The 26–42% turnover is dominated by pairs removed (mycoportal −48k), refuted (13k) or re-typed (`hasHost` records
    remapped). The report now says so.
- **Per-dataset results (finding 5).**
  - `results/tables/per_dataset.csv`: the advantage per dataset with at least 1,000 positives (266 clusters; the
    largest holds 44.7%, the top three 73.8%).
  - The advantage is positive for 24 of 26 such datasets and slightly negative for 2 (DoPI −0.003, YSU −0.035).
- **Small points (finding 6), both negligible by the review's count:** inner-split negatives can contain evaluation
  positives; temporal negatives exclude v0.11 edges, which uses future information. Both are noted in the limits.
- **G2:** `code/coverage_build.py` accounts for every record.
  - v0.6: 13,668,469 of 19,981,541 kept. 2,931,507 have an interaction type outside the three classes, 3,363,236 lack
    a species name or are self-loops, and 18,329 are refuted pairs.
  - v0.11: 8,142,528 of 24,453,954 kept. 8,775,804 have other types, 6,882,620 lack a species name or are
    self-loops, and 653,002 are refuted.
  - `graph_summary.json` and `eval_sets_summary.json` (planned, never written) are now written.
- **Reproducibility note:** the primary rerun gives taxonomy + structure 0.9474 temporal (0.9476 in the first
  version), from thread-level nondeterminism in gradient boosting. ρ is 1.677 against 1.68.

**G1 leakage audit (added here; the study predates the gates).**
- Temporal features use v0.6 only.
- Random-holdout citation counts leak (above; negligible).
- Re-resolved names are 1.1% of positives (above).
- Negatives exclude edges from either snapshot (a mild use of future information).
- trophiCH's inferred links are a label-quality issue rather than a leak: the review found its positives are not
  disproportionately genus-neighbours of v0.6 edges.
- No LLM or agent judges any unit.
