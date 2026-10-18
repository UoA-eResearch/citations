# Deviations from plan.md

Timestamps are Pacific/Auckland, from `date`.

## D1 — 2026-10-18 15:35 NZDT — faster, parallel pixel reads (operational; no value changes; before any skill was computed)

The single-stream extraction ran at 49 CHIRP and 253 CHIRPS pentads an hour, which put CHIRP alone at about 66 hours.

- **CHIRP reader.** CHIRP pentads are uncompressed striped float32 GeoTIFFs, so each file is now read directly:
  1. its tags and strip offsets;
  2. one multi-range request for the 4 bytes of each gauge's cell, the same cell rasterio's `sample()` reads.

  `code/check_chirp_reader.py` compared the direct reader with the GDAL values already extracted for 12 random
  pentads: 1,776 cells, 0 mismatches.
- **Parallel workers.** Both products are read by workers on disjoint year ranges (3 for CHIRP, 4 for CHIRPS)
  instead of plan §2's one stream at a time. That is seven concurrent range-request streams to the CHC server.
- **Resumption.** The 258 CHIRP and 1,341 CHIRPS pentads already read are kept. No pentad was left partly written.
