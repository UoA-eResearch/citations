#!/bin/bash
# All first-level models (plan.md sec 3), P jobs at a time over manifest rows FIRST..LAST (inclusive; default: all), in
# manifest order or reversed (ORDER=rev). Downloads dominate (about 130 KB/s per connection from OpenNeuro's S3 bucket
# here, scaling with the number of connections), so many jobs run concurrently and two runners may share the manifest:
# a per-subject lock (data/tmp/*.lock) keeps them apart. Rerunnable: finished subjects are skipped.
# Usage: run_first_levels.sh [P=72] [FIRST=0] [LAST=end] [ORDER=fwd|rev]
set -u
cd "$(dirname "$0")/.."
P=${1:-72}
N=$(($(wc -l < data/manifest.tsv) - 1))
FIRST=${2:-0}
LAST=${3:-$((N - 1))}
ORDER=${4:-fwd}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
if [ "$ORDER" = rev ]; then seq "$LAST" -1 "$FIRST"; else seq "$FIRST" "$LAST"; fi |
  xargs -P "$P" -I{} venv/bin/python code/first_level.py {} 2>/dev/null
echo "first levels done: $(ls data/first_level/*/*.npz | wc -l) ok, $(ls data/first_level/*/*.err 2>/dev/null | wc -l) failed"
