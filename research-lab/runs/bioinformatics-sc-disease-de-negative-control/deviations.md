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

## D2 — 2026-10-28 00:58 NZDT — the primary statistic has almost no power (G3); before any H1 result was computed

The plan's G3 power check (plan section 7) injected a twofold change into 5% of expressed genes in the pseudo-disease
donors of 100 null draws across 20 primary contrasts, and ran the identical pipeline
(`code/power_check.py`, `results/tables/power_check.json`). Against each contrast's own null distribution:

| statistic | power at p < 0.05 | injected median | null median |
|---|---|---|---|
| **π1** (preregistered primary) | **0.08** | 0.110 | 0.038 |
| **number of DE genes at BH FDR < 0.05** (preregistered secondary) | **0.87** | 217 | 0 |
| mean abs logFC of the 100 smallest-p genes (secondary) | 0.50 | 1.081 | 0.704 |

- **π1 cannot support the headline.** A real twofold change in one gene in twenty is missed 92% of the time, because
  π1's null distribution across matched healthy draws is wide (null median 0.038, and far higher in some contrasts).
  So "indistinguishable from the matched null" under π1 would mean little.
- **Decision.** The report gives both:
  - **H1 as preregistered, on π1,** with its 8% power stated beside it, so the preregistered verdict stands on the
    record;
  - **H1 on the number of DE genes,** the preregistered secondary that the power check shows is sensitive, with the
    same bands, bootstrap and BH correction. The interpretation leads with this one.
- **Why this is not outcome-driven.** The power check uses only healthy-donor null draws and synthetic injections.
  No disease contrast's result entered the choice. (For the record: while debugging a CSV-parsing bug I saw one
  contrast's numbers, c0017, before this decision.)
- The same reporting applies to the disease-gene enrichment secondary, whose power is not measured by this check.

- **G6 note.** The Open Targets ledger row first carried a DOI that resolves to an unrelated crystallography paper.
  The resolver accepted it because the identifier exists; the title check caught it. It is now
  10.1093/nar/gkae1128 (Buniello et al., the Open Targets Platform paper).
