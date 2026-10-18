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
