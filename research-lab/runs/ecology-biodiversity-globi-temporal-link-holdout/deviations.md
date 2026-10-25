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
