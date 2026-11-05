# Review: ecology-biodiversity-sdm-provenance-leakage

Reviewer: independent adversarial review (Fable 5.1), 2026-11-05. Scripts and outputs in `review/reviewer_checks/`
(`hidden_republication_scan.py/.txt`, `hidden_republication_summary.csv`, `hidden_republication_pairs.csv`,
`h2_with_missed_sources.py/.txt`). Checks used `venv/bin/python -I` with `code/` on `sys.path`, duckdb at 8 threads
over the study's own GBIF snapshot extract; no RF was refitted.

## Verdict: do not publish in this form; re-run with corrected provenance flags

The pipeline itself is careful and reproducible: grid conventions match SAGE's `geo_utils.py` (floor-divide in
EPSG:6933; stored locations are cell centres to ±0.7 m, so the centre rounding in `audit.train_cells` is exact),
the RF reimplementation matches SAGE's `sklearn_train.py` (BalancedRandomForest, 1,000 trees, `sampling_strategy
"all"`, no replacement, bootstrap; `max_features` 7 = floor(sqrt(52)), SAGE's "sqrt"), the removal sets and fit
cache are sound, every number in the report matches its table, the timeline is as stated, and the G2/G3 gates are
real. But the frozen flag list, which defines both hypotheses' populations, misses the two republications that
matter most after the Netherlands. A same-day, same-cell species-list scan over every dataset in the snapshot
(the study's own post hoc method, applied to all 30,681 single-plot dated test cells rather than to flagged datasets
only) shows that the Australian source database (8,431 evaluation plots, the second-largest source) is
republished in two unflagged GBIF datasets, and the Danish source in a dataset the study flagged only "broad" and
therefore never counted. Adding them, H2 rises from 8.3% to 16.6%, above the preregistered 10% bar. The report's
"We found every GBIF dataset that republishes one of the survey databases used for testing" is false, and H1's
population omits the Australian species entirely.

## Findings

### 1. (Major) Two republished source databases are missing from the flags; H2 crosses its threshold once they are counted

Evidence: `hidden_republication_scan.txt`, `h2_with_missed_sources.txt`. For each single-plot, dated test cell of
every sPlotOpen source, I took all snapshot records (SAGE's two filters applied) in the same 1 km cell on the
plot's recording date and computed, per GBIF dataset, recall and precision of the plot's species list.

| sPlotOpen source | GBIF dataset | flag | cells with same-day records | cells with recall ≥ 0.8 and precision ≥ 0.5 | median recall / precision |
|---|---|---|---|---|---|
| Australia (AU-AU-002, 5,383 such cells) | NSW BioNet Atlas (3.4M records in the download) | none | 2,011 | 664 | 0.78 / 0.59 |
| Australia | SA Flora (0.8M) | none | 126 | 96 | 1.00 / 0.87 |
| Denmark (EU-DK-002, 246 cells) | Danmarks Miljøportals Naturdatabase (12.0M) | broad | 242 | 45 | 1.00 / 0.28 |
| Netherlands (629 cells) | Dutch Vegetation Database | core | 464 | 196 | 1.00 / 0.42 |

The Australian and Danish signatures are the same as the Dutch one the report uses to conclude "the Dutch test
plots are republished too": the plot's full species list recorded that day in that cell, alongside other records.
The frozen screen could not find them because the registry descriptions of BioNet and SA Flora say "flora and
fauna sightings" and never name a vegetation-plot database (`flag_search.csv` has no hit for AU-AU-002 beyond a
583-record TERN dataset). Co-location with H2's definition: Australian source cells 5,899, test presences 99,615,
27.1% (26.0–28.2%) with a record of the same species from the two datasets in the cell; Denmark 257 cells, 3,935
presences, 98.6%. Pooled with the reported 13,713 of 165,422: 44,555 of 268,972 = 16.6%, so H2 is Supported, not
Refuted, under a complete flag list. H1 was never run on Australian species (none are in the 1,745), so the
report's overall DiD and its "scores hold up" conclusion do not cover the largest republished source.

Fix: add the three datasets (core for the Australian pair; Denmark promoted to core on this evidence) to
`provenance_flags.csv` as a dated, post-result amendment; re-run `audit.py`, `rf.py removals` and the fits for the
added species; report both the preregistered (frozen-flag) and the corrected results, with the latter as primary
and the registry-only screen named as the reason the former is incomplete. The scan script can be reused as a
general flag check.

### 2. (Major) The "broad" tier can never change anything, so the broad sensitivity is vacuous

Evidence: `audit.py:88-91, 112`. Source cells are defined from core-flagged sources only; broad flags enter only as
`core_or_broad` on test presences of those same cells. A broad-flagged dataset that republishes a *different*
source (Denmark) adds no source cells, so "the broad aggregator flags add nothing (8.3% either way)" is true by
construction. The plan's "Broad flag (sensitivity only)" needed broad sources to define cells in the sensitivity.

Fix: in the sensitivity, define source cells from core ∪ broad sources (that alone brings Denmark in at 98.6%).

### 3. (Moderate) In C1 a removed presence becomes a pseudo-absence at the test cell; the random arms do this elsewhere

Evidence: `rf.py:161-167`. The target-group background is the species' in-range training cells minus its capped
presences; a cell whose provenance-only presence is removed, but which keeps other species, is therefore drawn as
background for that species. In C1 those cells are, by construction, the source test cells (TAVA: 80% of test
presences are provenance-only in the same cell); in C2–C6 the new pseudo-absences fall wherever the random
removals fall. This mirrors what excluding the datasets upstream would do, so it is defensible as the
preregistered counterfactual, but it means the TAVA DiD of +0.164 combines "lost information" with "trained to
predict absence at the test location". A neutral counterfactual (remove the presence and exclude the cell from that
species' background) would isolate the first. It cannot raise H1's verdict, but it changes how 0.164 should be read.

Fix: run the neutral variant for the 53 TAVA and 452 Ukrainian species (about 500 fits) and report both.

### 4. (Minor) SOPHY: the hidden-aggregator worry can be answered, positively

Evidence: `hidden_republication_summary.csv`. Across 3,098 single-plot dated SOPHY test cells no dataset, flagged
or not, reproduces plot species lists on the recording day (the only French hits are isolated sightings). Within
the snapshot's scope, SOPHY relevés are not republished through other GBIF datasets, and the report can say so
instead of leaving two possibilities open. Slovakia: an unflagged PLADIAS.SK dataset ("Complex information and
monitoring system of the SNC SR", 2.1M records) reproduces 6 of 628 plots; negligible but worth a line.

### 5. (Minor) Checks that passed, for the record

- Numbers: every figure in the verdict, tables and plain-terms section matches `audit.json`, `primary.json`,
  `removals.json`, `posthoc_*.json` (e.g. 53% positive DiD = 0.528; France 93,380/165,422 = 56%).
- Timeline: plan 11:41 → flags 17:42 → audit code 18:11 → audit/removals/RF code 18:21 → D1 18:21 → analysis
  18:22 → D2 19:11; fits 18:45–06:12; the abandoned first fit pass (18:28–18:42) and the uncommitted job-order
  change are harmless because fits are seeded and keyed by an input hash (D3).
- Czech claim: dataset 5b514765 is absent from `download_datasets.json`; the lead's claim is correctly refuted.
- Species keys: 5,771 of 5,771 matched (15 fuzzy); cells: floor-divide as SAGE.
- Shortfall direction: random arms remove fewer records, which biases the DiD upward (toward Supported); the
  post hoc restriction (+0.005) confirms H1's reading.

## Gate checks

- **G1:** the leakage audit in D2 is real; no label-correlated field enters training. The missing flags
  (finding 1) are a population error, not a leak.
- **G2:** `coverage.json` present; 12,215 of 12,215 fits; 609 undefined AUROCs on non-source cells only.
- **G3:** `plausibility.md` traces three units; invariants hold (C1 count 1,115,257 in both tables; refits match).
- **G4, G7:** not applicable, confirmed (no labelling or classifier validation).
- **G5:** `review/overclaim_check.md` is honest about what it checked; rows 3, 11–13, 37 and 39 are Overstated
  after finding 1 (row 37's "every" and row 12's verdict).
- **G6:** `python3 -I ../../tools/attribution.py check . --show` → "G6 passed (12 claims)". Spot-checked A3–A7
  (registry pages match the flags), A8 (download list), A9/A10 (titles resolve; roles and conditions sensible).
  A2 (SAGE "deliberately keeps" in-cell training records) cites the arXiv HTML Data section; I could not verify it
  offline (`data/repo_docs` does not contain that text), so it rests on the agent's reading.
