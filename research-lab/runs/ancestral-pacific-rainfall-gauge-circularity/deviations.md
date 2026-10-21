# Deviations from plan.md

Timestamps are Pacific/Auckland, from `date`.

## D1 — 2026-10-18 15:07 NZDT — faster, parallel pixel reads (operational; no value changes; before any skill was computed)

The single-stream extraction ran at 49 CHIRP and 253 CHIRPS pentads an hour, which put CHIRP alone at about 66 hours.

- **CHIRP reader.** CHIRP pentads are uncompressed striped float32 GeoTIFFs, so each file is now read directly:
  1. its tags and strip offsets;
  2. one multi-range request for the 4 bytes of each gauge's cell, the same cell rasterio's `sample()` reads.

  `code/check_chirp_reader.py` compared the direct reader with the GDAL values already extracted for 12 random
  pentads: 1,776 cells, 0 mismatches.
- **Parallel workers.** Both products are read by workers on disjoint year ranges (3 for CHIRP, 4 for CHIRPS)
  instead of plan §2's one stream at a time. That is seven concurrent range-request streams to the CHC server.
- **Resumption.** The 258 CHIRP and 1,341 CHIRPS pentads already read are kept. No pentad was left partly written.

## D1 addendum — 2026-10-18 15:42 NZDT — the server refused the parallel workers

About 30 minutes after the seven workers started, the CHC server began answering HTTP 403. It then refused single
requests too. The workers were stopped.

By then:
- CHIRP had 423 pentads read;
- CHIRPS had 1,360.

**Changes:**
- Extraction resumes with **one request stream at a time**, as plan §2 originally said: CHIRP first, then CHIRPS.
- There is a 1-second pause after each pentad, and a worker now stops at the first 403 instead of retrying.
- A background probe waits until the server answers again.

The direct CHIRP reader is kept, because it makes 3 small requests per pentad instead of whole-strip reads. Error
rows are retried on resumption and are never read as values.

## D2 — 2026-10-21 17:23 NZDT — after independent review

An independent adversarial review (`review/review.md`) re-implemented the pipeline without importing the study's
code and reproduced the primary results. Four changes followed, each re-run; both verdicts are unchanged.

1. **No-estimate stations.** The plan's "masked" category (§3: CHIRPS has no estimate there) was implemented as
   "every CHIRPS value empty", but the product fills cells without a climatology with near-zero values, not nodata.
   At such a cell the blending gain is zero by construction. A station now counts as no-estimate if CHIRP averages
   under 2 mm/pentad or under 10% of the gauge. The rule's thresholds were set after the review had identified the
   affected stations; they fall in a clear gap (the nine stations caught sit at 0–6% of the gauge, the next lowest at
   13% is a gauge error, item 2). Nine stations are caught: five Palau, Johnston, Lukunoch, Chuuk WSO AP, Woleai.
   With them removed (and the screen in item 2), the ratio is 0.12 (−0.17 to 0.39) and ΔKGE +0.046 (+0.017 to
   +0.073), against 0.10 and +0.034 in the draft.
2. **Gauge plausibility.** The QC had no plausibility screen. A well-sampled station-year (at least 30 matched
   pentads) in which gauge and satellite-only product disagree by more than fivefold in either direction is now
   dropped: Koumac 1981–2003 (about ten times too high), seven French Polynesia stations in 1981 (far too low) and
   ten other station-years. The first version of this screen was one-sided and had no pentad minimum; the
   confirmation pass showed it removed single-pentad years and years where the product rather than the gauge had
   failed, while leaving the French Polynesia 1981 errors in. Either version moves the results by under 0.01 in the
   ratio. With the revised screen: ratio 0.12 (−0.17 to 0.39), ΔKGE +0.046 (+0.017 to +0.073).
3. **Shares** are now computed over station-months in which the gauge reported, with "ingested" at 10 km as well as
   5 km, because 6.7% of Pacific entries in the input lists are rounded to 0.1°. The draft's "about a third" becomes
   half to two-thirds, which strengthens the circularity finding.
4. **Preregistered outputs** the draft computed or implied but did not report: the co-located ≤5 km case, the
   per-country table and the countries that cannot be evaluated. The within-station contrast is added as a
   post-review analysis; it addresses station selection directly.

Wording: "tenfold" becomes "several-fold, at least threefold on the interval"; the label-resolution caveat now
applies to H2 as well as H1.
