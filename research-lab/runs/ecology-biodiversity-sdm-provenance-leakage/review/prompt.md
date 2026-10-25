You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/ecology-biodiversity-sdm-provenance-leakage/ (read-only except your output
in review/).

**The question.** SAGE (arXiv 2609.31082) trains species distribution models on GBIF presence-only records and
evaluates them on sPlotOpen plots, treating the two as independent. Some GBIF datasets republish the vegetation-plot
databases that supply its test plots. Does removing those provenance-shared training records lower source-plot AUROC
(SAGE's Random Forest baseline) by at least 0.02 more than matched random removal (H1)? Do at least 10% of
source-plot test presences have a provenance-shared record in the same 1 km cell (H2)?

**Reported:**
- **H1 Refuted:** DiD +0.006 (+0.005 to +0.008), 1,745 species. By database: TAVA West Africa +0.164 (53 species),
  Ukraine +0.055, Netherlands +0.016.
- **H2 Refuted:** 8.3% (7.7–8.9%). Netherlands 88%, TAVA 87%.
- **Post hoc:**
  - Co-location falls to 6.1% when counting only records that reached SAGE's training data.
  - Distance to plots is no closer than random.
  - Species-list matches in single-plot cells show the TAVA test plots are in the training data (87% exact). Dutch
    plots probably are too (same-day recall 1.0).
  - The DiD restricted to species with matched removal counts is +0.005.

**What to read:**
- plan.md, deviations.md, report.md, results/plausibility.md and results/attribution_ledger.csv.
- results/tables/: audit.json, primary.json, removals.json, coverage.json, posthoc_*.json, handtrace*.json,
  provenance_flags.csv, species_did.csv and rf_auroc.csv.
- code/: registry.py, flag_search.py, s3_extract.py, species_keys.py, cells.py, audit.py, rf.py, analyse.py,
  posthoc_*.py, handtrace*.py and figures.py.
- **Data:** SAGE's benchmark is in /mnt/sage/bench, the GBIF snapshot extract in /mnt/sage/gbif_s3 and SAGE's
  repository in /mnt/sage/repo.
- **Work files** are in data/work/: support.parquet, core/, prov_only.parquet, the removal sets and rf/C*.json, one
  JSON per species and condition.

**Git.** Read-only git is fine. Verify the order: the plan, then the frozen flags, then the audit code, then D1, D2
and analyse.py, all before any RF result. The fit log is logs/rf_fit2.log. D3 records an uncommitted job-order
change in rf.py; check that it cannot affect results.

**Environment.** Use venv/bin/python with -I. Do NOT pip install. The machine is shared (vLLM on the GPU), so keep
CPU use moderate: at most 8 workers. One RF refit takes about a minute. `code/rf.py test <sp>` returns the stored
results when they exist; `code/handtrace.py` shows how to bypass the cache and restore it safely.

Check at least:

1. **Flags (frozen before overlap).**
   - Were the 27 core datasets correctly identified, and were obvious republications missed? The prime suspects are
     SOPHY relevés through French aggregators, and other sPlot sources with GBIF copies.
   - Is the lead's Czech claim correctly handled?
2. **Snapshot substitution.** How faithful is the 2026-02-01 snapshot plus SAGE's two filters to SAGE's download?
   Is 96.1% matching enough? Which way does each discrepancy bias the result?
3. **Grid and joins.**
   - cells.py's EPSG:6933 cell definition against SAGE's geo_utils.py.
   - The train_cells centre rounding in audit.py, and the eval-cell floor mapping.
   - Species-key matching.
   - Re-derive a few presences by hand.
4. **Conditions.**
   - Does C1 remove exactly the provenance-only presences?
   - Random matching by species and majority country, and the 13% shortfall.
   - Emptied cells and background reconstruction: C1 empties 4,923 cells, the random draws about 9,700.
   - A removed presence in a cell that keeps other species becomes a background point for that species. That is what
     excluding the datasets upstream would do, but in C1 it happens at the test cells and in C2–C6 elsewhere. Does
     it exaggerate the DiD?
   - Could the shortfall or the different emptied-cell counts bias the DiD in either direction?
5. **RF reimplementation.** Fidelity to SAGE's randomforest config: subsample index, caps, background, normalisation,
   BalancedRandomForest settings. The fit cache keys: can a reused fit be wrong?
6. **Analysis.**
   - The species bootstrap, per-database AUROC (cells counted for several databases), and the non-source placebo.
   - Is "Refuted" right for H1 and H2?
   - Is H2's snapshot-record definition what the plan said, and is the post hoc 6.1% fair?
7. **Post hoc same-relevé check** (posthoc_same_releve.py).
   - Single-plot cells and recall/precision on SAGE species.
   - TAVA's GBIF records are undated. Does an exact 8-for-8 species match really show the same relevé? A neighbouring
     plot would not.
   - Are the report's duplication claims (TAVA certain, Dutch "probably", Ukraine partial) calibrated?
8. **Report.** Check every number against the tables. Check that the title, verdict and plain-terms section are fair,
   including "the overall Random Forest scores hold up" given that the DeepSDM was not run.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.

**Gate checks (METHODS.md G1–G7).** Verify:
- **G1:** the leakage audit (deviations.md D2) is real and complete; look for label-correlated fields it missed.
- **G2:** `results/tables/coverage.json` exists, and no unplanned fallback entered a statistic.
- **G3:** `results/plausibility.md` traces three units, and the asserted invariants hold.
- **G4:** does not apply (no labelling or classifier validation); confirm.
- **G5:** `review/overclaim_check.md` passes and is honest; re-label any sentence you disagree with.
- **G6:** `results/attribution_ledger.csv` passes `python3 -I ../../tools/attribution.py check . --show`; spot-check
  5 claims against their sources, including the role and conditions.
- **G7:** does not apply (no labels); confirm.

Report any gate that is missing or hollow as a finding.
