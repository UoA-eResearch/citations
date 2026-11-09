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

## Confirmation pass

Reviewer: Fable 5.1, 2026-11-09.

Scope: the D4 re-run against the first review's five findings, following `review/confirmation_prompt.md`. I made no refits
and wrote nothing into the run. Every check used `venv/bin/python -I` (or `python3 -I`) with paths passed as arguments,
ran from a scratch directory outside `data/`, and used at most 4 duckdb threads. Scripts and outputs are in
`review/reviewer_checks/confirm_*`.

What was checked, and which file backs it:

- **Frozen outputs are the preregistered ones.** All 11 `frozen_flags_*` / `provenance_flags_frozen.csv` files are
  byte-identical to the versions committed in 7f6441f (read-only `git show`). The amended `provenance_flags.csv`
  differs from the frozen list by three rows: NSW BioNet and SA Flora added as core, and the Danish portal promoted to
  core. That gives 30 core and 2 broad datasets, covering 13 core source databases.
- **Republication scan.** `code/republication_scan.py` is the reviewer's script, with the frozen flag list and the
  MIN_HI = 20 rule added. `results/tables/republication_scan.csv` is byte-identical to the first review's
  `hidden_republication_summary.csv`. That fits a deterministic re-run, but there is no scan log. Applying the rule to
  the CSV selects exactly NSW BioNet (664), SA Flora (96) and the Danish portal (45). No other non-core dataset has
  20 or more hits; next are PLADIAS.SK with 6 and a core Ukrainian dataset with 6. France_sophy has 0 hits.
- **H2, recomputed independently** (`confirm_h2.py/.txt`). I recomputed H2 from `support.parquet` and the eval
  targets and range masks, using the same seeded cell bootstrap: 13,622 cells, 268,972 presences, 16.56%
  (15.95–17.22%). The by-source shares match `audit.json` exactly. The corrected broad sensitivity is 14,381 cells,
  15.65% (15.05–16.24%). A second numerator, built straight from the `core/` record files by datasetkey, gives the same
  44,552. The eligible population is 2,833 species, and the seeded sample of 2,000 reproduces `population.csv`
  exactly.
- **Fit cache and H1** (`confirm_fit_cache.py/.txt`, `confirm_h1_impact.py/.txt`). I checked that each stored AUROC
  was computed on the corrected source cells, then recomputed the H1, matched-restriction, by-source, Australian and
  Danish contrasts from `rf_auroc.csv`.
- **Shortfall and neutral variant** (`confirm_shortfall_neutral.py/.txt`). I split the random-removal shortfall by
  country, and checked whether the neutral variant actually changed any species' background.
- **G5 and G6** (`confirm_gates.txt`).
  - `tools/overclaim_check.py --verify` passes (46 rows). Re-extracting from the current `report.md` gives an
    identical table.
  - `tools/attribution.py check --show` passes (12 claims), and all ids resolve to the named works. Both tools were
    run on copies.
- **Report text.** I compared `report.md` and `report.html` against every number above. The HTML was rebuilt from the
  current Markdown.

### Final verdict: fix first

Both hypothesis verdicts survive everything I checked. H2 is Supported at 16.6%, recomputed exactly. H1 is Refuted:
leaving out the stale-cache species described below gives −0.0076 (−0.0104 to −0.0049).

The re-run has a pipeline defect, though. It hides the result for the source with the highest co-location, Denmark.
Several report passages are also stale or wrong, and fixing both needs refits (about 2,100) that only the study can run.

### Original findings

- **1. Missed republications: partly fixed.**
  - The flags, the audit and the population are correct (`confirm_h2.txt`).
  - The H1 fits are not all on the corrected definition. `rf.py` keys its cache on the training inputs only, but each
    cached result carries the frozen run's source-cell AUROCs.
    - 2,080 of the 14,000 stored fits are frozen-run fits: all 1,248 C0 rows of species shared with the frozen
      population, plus 832 C1–C6 rows. Their `auroc_db` lacks the Australia and Denmark keys, and 1,984 of them equal
      a frozen C0 AUROC exactly.
    - 553 species are evaluated on different source-cell sets in different conditions. The median difference is 257
      cells, which is the Danish source cells.
    - For 207 species, C1 and the random arms are on different masks within the DiD itself.
    - Excluding those 207 species, H1 DiD is −0.0076 (−0.0104 to −0.0049), so the verdict holds. The matched
      restriction is +0.0008 (−0.0011 to +0.0026).
    - The reported mean C0 AUROC on source cells (0.865) mixes the two masks.
  - **Denmark is missing from the by-source H1.** It has the highest co-location (98.6%) and the largest C1 removal
    (1.68M presences, more than Australia's 1.50M).
    - Under the corrected source cells, 249 population species would have a defined Denmark AUROC, but only 2 have
      one in all seven conditions. That is below `analyse.py`'s 50, so Denmark silently drops out. Those 2 species
      show DiD +0.156.
    - The report's "the other databases' intervals include zero" therefore does not cover Denmark.
    - Per-database AUROCs for the frozen-era sources (TAVA, Ukraine, Netherlands, etc.) are unaffected, because their
      cells did not change.
- **2. Broad tier: fixed.** `audit.py` now builds the sensitivity's source cells from core and broad sources. The
  15.6% (15.1–16.2%) is reproduced exactly (`confirm_h2.txt`), and the report says the first version was vacuous.
- **3. Neutral counterfactual: fixed as specified, but the reading needs a sentence.**
  - The `fit_neutral` variants run for both arms (2,292 fits). +0.118 (TAVA) and +0.052 (Ukraine) reproduce from
    `rf_auroc_neutral.csv`.
  - All 382 species sit at the 10,000 background cap. Their removed cells are a median 644 of a 1.57M-cell pool
    (0.07%), so only about 7 removed cells were expected in a standard background. Neutral n_bg equals standard n_bg
    for all 2,292 fits.
  - So the variant mostly re-draws the background. The right conclusion is that induced pseudo-absences were too few
    to matter. "The effect is lost information" is acceptable, but the report should give this reason.
    (`confirm_h1_impact.txt`, `confirm_shortfall_neutral.txt`)
- **4. SOPHY: mostly fixed.** The report says no dataset republishes SOPHY relevés, which the scan confirms (no
  France_sophy hits). The PLADIAS.SK line (6 of 628 Slovak plots, below the rule) that the brief says is "stated" is
  not in `report.md`.
- **5. Post hoc checks re-run: fixed, but the interpretation built on them is not.**
  - The shortfall, H2-training, same-relevé and distance outputs are refreshed, and their numbers match the report
    (14.8%, 13.1%, 29.3%, 370 m, 0.02%).
  - However, "Australia's negative DiD is a control artefact" is not supported:
    - A shortfall makes random removal remove less, which biases the DiD upward, not downward. The first review
      noted this.
    - Among Australian species where random removal reached at least 90% of C1, the DiD is still −0.013 (−0.021 to
      −0.005; n = 243).
    - The per-species median random/C1 ratio is 0.80. The "about half" is a pooled ratio dominated by large species.
    - The matched restriction's +0.001 still contains 476 Australian species. Excluding Australian-source species,
      the DiD is +0.005 (+0.003 to +0.007).

### Remaining issues

1. **Stale cached fits (2,080).** Re-run them with the source-cell definition (or a hash of the flag list) in the
   cache key. Then re-run `analyse.py`, `posthoc_shortfall.py` and `coverage.json`, and report the Denmark by-source
   DiD (249 evaluable species). Add a G3 invariant: n_src is constant across conditions within a species. Record this
   in D4.
2. **Denmark by-source H1 is absent from the report.** Denmark has the largest removal and 98.6% co-location. The
   sentence "the other databases' intervals include zero" needs revisiting once it is computed.
3. **Australia "control artefact" claim (What this does and does not show; G5 rows 24 and 35 context).** The claim is
   unsupported. Rewrite it as an unexplained negative DiD that persists in matched species. Describe the removal ratio
   as a pooled ratio, not "half as many" per species.
4. **"Random draws fall 2.0 million short, almost all in Australia" is false.** Denmark accounts for 58% of the
   shortfall (1.15M) and Australia for 35% (0.70M).
5. **Stale text in "How it was done", "Coverage" and "Reproducing it":**
   - "27 core datasets republish 11 sPlotOpen source databases; 3 broad" should be 30 core, 13 sources, 2 broad.
   - "1,115,257 presences (2.0%): Netherlands, Poland, Ukraine" should be 4,302,471 (7.5%): Denmark 1.68M, Australia
     1.50M, Netherlands 0.90M. As written, it contradicts the Results.
   - "13% of the C1 count could not be matched" should be 46%.
   - G2's "609 undefined AUROCs" should be 5,389, and the non-source contrast has 1,230 species.
   - The reproduction steps still describe 12,215 fits and "flags frozen in provenance_flags.csv", and omit
     `republication_scan.py`, `rf.py fit_neutral` and `posthoc_neutral.py`.
6. **G3 `results/plausibility.md` was not refreshed for D4.** All its figures and invariants are frozen-run values
   (1,745 species, 1.12M, 12,215 fits, 609).
7. **Neutral variant.** Add the reason the result is unsurprising: the background cap, and removed cells being 0.07%
   of the pool.
8. **Minor:**
   - Add the PLADIAS.SK line (finding 4).
   - The G6 ledger has no rows for the three scan-added registry datasets.
   - The scan has no run log.
