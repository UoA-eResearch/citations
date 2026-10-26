# Deviations from plan.md

## D1 — 2026-10-27 05:31 NZDT — before any expression value was read

- **Contrast counts.** The plan's metadata counts (869 primary contrasts, 33 datasets, 47 disease labels; 359
  replication pairs, 112 groups) came from a preliminary tally. That tally did not yet apply the plan's own rules
  (section 1):
  - exclude donors with more than one disease label in a dataset;
  - sum a donor's cells across assay and sex rows before the 10-cell threshold.
- Applying them (`code/stream.py list`) gives:
  - **799 primary contrasts in 25 datasets, 42 disease labels;**
  - 277 replication contrasts forming **340 cross-collection pairs in 99 groups, 9 diseases.**
- No threshold, statistic or band changes.
- **Data route.** This host gets about 120 KB/s per connection from the Census S3 bucket; throughput scales with
  connections (32 connections gave 4.3 MB/s). TileDB's sparse reader stayed near 0.1 MB/s even with 192 parallel S3
  operations allowed (`code/stream.py`, kept for the record). So the study instead:
  - downloads the Census source H5AD of each needed dataset (the same release, cells and raw counts) with 384 parallel
    range requests (`code/fetch_h5ad.py`);
  - sums raw counts locally (`code/pb_h5ad.py`), using `raw.X` where X is normalised;
  - maps tissue terms to `tissue_general` from the Census obs table.
  - On the first dataset, cells match the metadata exactly (22,502), with no non-integer counts and every gene present
    in Census var.
- **DE image.** The Bioconductor 3.22 base image does not ship edgeR or limma, so `code/docker/Dockerfile` installs
  them: edgeR 4.8.2, limma 3.66.0, R 4.5.2. They run without network access.

Recorded 2026-10-27 05:40 NZDT. At that time no DE result existed; pseudobulk sums had been computed for two datasets,
for coverage only.
