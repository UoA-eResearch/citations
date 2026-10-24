# Plan (preregistration): how much of "notebook irreproducibility" is just run-to-run noise?

Lead: `computational-reproducibility-notebook-noise-aware-verdicts`. Written before any notebook is executed and
before the dataset is opened. The Zenodo record's file list was read.

## 0. Hypotheses

Among Python notebooks from PubMed Central-linked repositories that run to completion in a reconstructed environment
but do not reproduce their stored outputs exactly:

- **H1.** In at least 30%, every mismatching output cell is explained by run-to-run variability in one environment:
  the cell's output differs among three replicate executions, or the stored value lies inside the replicates'
  envelope.
  - **Supported** if the Wilson 95% lower bound (with a repository-clustered bootstrap as a check) is at least
    0.30.
  - **Refuted** if the upper bound is below 0.30.
  - **Inconclusive** otherwise.
- **H2.** Exact-match verdicts overstate irreproducibility by a factor of at least 1.4. The factor is the share of
  completing notebooks that fail exact matching, divided by the share that fail noise-aware matching.
  - **Supported** if the repository-bootstrap 95% lower bound is at least 1.4.
  - **Refuted** if the upper bound is below 1.4.
  - **Inconclusive** otherwise.

## 1. Sample

- **Source.** Samuel and Mietchen's PMC notebook reproducibility dataset (Zenodo 8226725, `db.sqlite`).
- **Eligible.**
  - Python-kernel notebooks whose execution in that dataset ran to completion but did not reproduce all stored
    outputs. The exact fields are recorded in D1 after reading the schema, before any execution here.
  - The repository must be at most 500 MB when cloned and still exist on GitHub.
- **Draw.** 300 notebooks at random (seed 20261025), at most two per repository.

## 2. Environments and execution (safety-first)

All third-party code runs inside Docker containers, with no host credentials or home directory mounted.

- **Build** (network on, needed for PyPI).
  - In `python:{version}-slim`, where the version is the notebook's `language_info.version` (major.minor); 3.8 for
    older or missing versions; capped at 3.12.
  - `uv` creates a virtual environment and installs:
    - the repository's `requirements.txt` (or `requirements/*.txt`, or the pip section of `environment.yml`); or,
      if none,
    - the notebook's imports mapped through a fixed import-to-package table (`code/import_map.json`, written before
      execution).
  - **AS-OF arm:** `--exclude-newer` the repository's last commit date before the article's publication date (from
    the dataset). **LATEST arm:** no limit.
  - The repository's own package is **not** installed (no `setup.py` execution).
- **Execute** (network off). `docker run --network none --cpus 2 --memory 6g`:
  - the environment and a fresh copy of the repository are mounted;
  - nbclient runs with a 20-minute limit and a fresh kernel per run, with no seeds set;
  - **3 runs in AS-OF and 1 in LATEST.**
  - A notebook **completes** if no cell raises in the first AS-OF run.

## 3. Comparing outputs

- **Per cell, stored against rerun outputs:**
  - **text** (stream, `text/plain`, `text/html` stripped of tags): compare after masking volatile tokens (memory
    addresses, dates and times, durations, temporary paths, process ids);
  - **numbers:** compared at the stored output's displayed precision;
  - **images** (`image/png`): equal if the 64-bit perceptual hash differs by at most 6 bits.
- **A cell is an exact mismatch** if its stored and AS-OF-run-1 outputs differ under these rules.
- **It is intrinsic** if the cell's output differs among the 3 AS-OF runs, or if each number in the stored output
  lies within the min–max of the replicates.
- **Notebooks:**
  - **all-intrinsic:** at least one mismatching cell, and every mismatching cell intrinsic;
  - **fails noise-aware matching:** at least one mismatching cell that is not intrinsic.
- **Validation.** The comparator is checked on 100 hand-labelled cell pairs, drawn before results are computed. The
  agreement is reported.

## 4. Secondary (labelled as such)

1. **Environment drift:** for cells stable and matching across AS-OF runs, the share that differ in LATEST.
2. **What predicts intrinsic variability:** unseeded random calls, `set`/`dict` iteration, and multithreaded
   libraries (logistic, by cell).
3. **The selection flow:** sampled → cloned → environment built → completed → mismatching.
4. **Hidden state:** execution-count gaps in the stored notebook as a flag for out-of-order execution.

## 5. Limits stated in advance

- **Execution without network** fails notebooks that download data. Those count as not completing, so the completing
  set leans toward self-contained analyses.
- **Three replicates** can miss rare variability, which biases H1 downward.
- **Environment reconstruction is approximate.** AS-OF dependency resolution is not the authors' environment.
- **Coverage.** The sample is 300 notebooks, not the full dataset.
