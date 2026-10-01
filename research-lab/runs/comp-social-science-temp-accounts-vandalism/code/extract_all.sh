#!/bin/bash
# Run extract.awk over every downloaded dump file that passed `bzip2 -t` (listed as "ok" in the download log given as $1)
# into the output directory $2 (default data/processed/agg_v2, deviations.md D5),
# 16 in parallel; files already extracted are skipped, so it can be re-run as downloads complete.
set -u
cd "$(dirname "$0")/.."
LOG=$1
OUT=${2:-data/processed/agg_v2}
mkdir -p "$OUT"
grep '^ok ' "$LOG" | awk '{print $2}' | xargs -n1 basename | sort -u | \
  xargs -P 16 -I{} sh -c 'f=data/raw/dumps/{}; o='"$OUT"'/$(basename {} .tsv.bz2).tsv; [ -s "$o" ] || (bzcat "$f" | awk -f code/extract.awk > "$o.tmp" && mv "$o.tmp" "$o")'
echo "EXTRACT_DONE $(ls "$OUT"/*.tsv 2>/dev/null | wc -l) files"
