# Deviations from plan.md

## D1 — 2026-11-07 — implementation details and an ID bug (found after the first detection pass, before any write-up)

1. **Float-rounded Gaia IDs.** `sample.py` cast every catalogue column through float64, so `source_id` values were
   rounded (Gaia IDs need 19 digits).
   - 41 pairs of different stars shared a rounded ID, and their light curves were stored together.
   - The Gaia DR3 variability query had been run on the rounded IDs and matched only 23 of the flagged stars.
   - Found while comparing the positive-control IDs after the first detection pass.
   - Fixed: `sample.py` now reads the IDs as int64. `code/fix_ids.py` remaps the light-curve shards to the true IDs
     (`data/lc_v2/`) and re-fetches the 82 colliding stars by position.
   - Detection, the variability query, the injections and the occurrence were all re-run. The first pass's
     outputs were overwritten and are not reported (eligible 109,040; flagged 923; 15 of 18 known recovered, as
     now).
2. **One ZTF object per filter.** The plan says "the ZTF object with the most epochs within 2 arcsec". ZTF assigns
   separate objects per filter, so the fetcher keeps, per filter, the object with the most good epochs, and pools
   the filters.
3. **Injection details** not fixed by the plan were set in `code/detect.py`'s docstring before any detection run:
   box-shaped dips, magnitude errors scaled by (flux)^−½, injected epochs fainter than 21.0 mag dropped,
   seasons as runs of epochs separated by gaps over 60 days, and flagged stars not used for injection. The
   occurrence function (completeness by G × epoch bins, Garwood intervals, best class per star for the combined
   rate) was added after detection had run, following plan section 0.
4. **Known-variable lists.** Name lists of known CVs and AM CVn systems were not obtained; only Gaia DR3 classes
   were used. The Gaia archive rejected synchronous queries when overloaded, so the query uses asynchronous jobs.
5. **Positive controls** were compiled from the discovery papers' tables by a separate agent session that did not
   see the light curves, and were committed before detection. Known systems are assigned a signal class from the
   dip type their papers describe.

## D2 — 2026-11-09 — edits after the independent review (verdict: publish with edits)

1. **g and r only** (finding 2). The first draft pooled ZTF i-band epochs into eligibility and both rules, against
   the plan's "g and r". `detect.py` now keeps only zg and zr (`FILTERS`) and everything was re-run: 108,493
   eligible, 1,006 flagged, 970 candidates, 15 of 18 known systems recovered, lower rate 2.1e-4, upper 1.4e-2.
   H1 stays Inconclusive. The as-run outputs are kept as `results/tables/withzi_*`.
2. **Tiered lower rates** (finding 1; `code/posthoc_review.py`): confirmed transiters only, 4.2e-5; plus the Guidry
   candidates, 7.0e-5; all published systems and candidates, 2.1e-4. The title and text no longer call 2.1e-4 a
   floor.
3. **SBSS 1232+563** (finding 3). A fresh IRSA query keeping every object and flag finds 35 good epochs after April
   2023, and the stored light curve has 29. The miss comes from sparse sampling of the 2023 event (one qualifying low
   bin; the rule needs two), not from dimming that is too sporadic or from missing epochs.
4. **G4 and the calendar test** (finding 4).
   - The planned g/r coincidence check was not run before the review. Run now, 94% of the long-dip candidates' low
     bins with at least 3 g and 3 r epochs are low in both bands, so the check barely discriminates.
   - Calendar clustering: 454 of 769 long-dip candidates have a low bin in the same ten 30-day windows (140 in June
     2020), where random quiet stars are also 0.1–0.7% faint.
5. **The verdict** now says that Supported or Refuted was all but unreachable with this design (finding 5).
6. **G5** (finding 6). The title and floor rows are rewritten. Row 3 ("committed before detection") is relabelled
   partially supported: `known_systems.csv` was committed before detection, but its Gaia IDs were corrected after
   the first detection pass (D1).

## D3 — 2026-11-10 — edits after the confirmation pass (verdict: publish with edits)

1. **"About 1 in 80"** is the with-zi upper rate; under g and r, 1/1.38e-2 = 73, so "about 1 in 70".
2. **SBSS 1232+563, like for like** (`code/posthoc_d3_sbss.py`): good g and r epochs at MJD ≥ 60068, 32 stored
   against 34 in IRSA; the 2 missing come from the second field's g object (1824102200002193), which loses to the
   most-epochs object. D2's "29 against 35" compared a windowed all-filter count with an unwindowed one. SBSS is no
   longer listed under "shallow or sporadic dimming".
3. **"Mostly systematics" softened to "many"** (`code/posthoc_d3.py`): re-drawing each long-dip candidate's low bins
   among its own bins with at least 5 epochs puts 215 (196–238) in the ten crowded windows by coverage alone, against
   454 observed.
4. **G4 under three readings** (`posthoc_d3.py`): the plan's night-level rule (23 of 26 testable random flags pass;
   81% of all testable flags; 14 of 14 testable known systems), both bands more than 2.5% below the pooled median
   (94%, D2's reading) and both at least 5% below their own median (71%).
5. **coverage.json** regenerated for g and r (116,911 with light curves, 108,493 eligible), by re-running
   `handtrace.py`, which now reads the failed-query count from the fetch logs.
6. **D2 item 6 misdescribed G5 row 3.** It was not relabelled; with the ID correction disclosed in the sentence,
   Supported stands.
7. **The first review's minor findings 7–12**, which D2 did not mention:
   - 7 (hand traces): four g- and r-only traces, two chosen and two random, including a long-rule trace of a random
     long-only candidate; all match the pipeline exactly.
   - 8 (ZTF–Gaia magnitude mismatch): 186 eligible stars more than 0.75 mag brighter in g or r than Gaia predicts,
     flagged at 9.1% against 0.9%; 15 candidates, no known system. Listed in `zg_gaia_mismatch.csv` and stated as a
     limit, not vetoed (a veto would be a new post hoc rule). The reviewer's count (257) used a different colour
     relation.
   - 9 (combined rate and class labels): the sum-of-class lower rate, 2.5e-4, is reported beside the preregistered
     best-class 2.1e-4, and class labels are called approximate.
   - 10 (injection realism): stated as a limit, quoting the reviewer's background-limited re-scoring (one-off recovery
     53% to 45%; lower rate 2.06 to 2.13e-4). Not re-implemented here.
   - 11 (asymmetry by G): reported (28% of stars with a negative excess at G < 17, 92% at G 19.5–20; short-rule flag
     rate 0.85% to 0.016%).
   - 12 (provenance): the report states that the in-sample Gaia IDs were matched from the sample by position and that
     `source_location` names the paper each ID was checked against. The committed control list is not rewritten.

