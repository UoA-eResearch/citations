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
