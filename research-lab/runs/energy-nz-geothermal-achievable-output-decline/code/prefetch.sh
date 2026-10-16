#!/bin/bash
# Prefetch EMI unit-level half-hourly generation, 2000-01 to 2026-09, twelve connections in parallel, and record
# the vintage (EMI files can be re-issued, so the retrieval time and hash of what was analysed matter).
set -u
cd "$(dirname "$0")/.."
# the EMI page 302-redirects to blob storage; the first run, without -L, saved 321 redirect stubs
BASE="https://emidatasets.blob.core.windows.net/publicdata/Datasets/Wholesale/Metered_data/Unit_level_generation_IR"
for y in $(seq 2000 2026); do for m in 01 02 03 04 05 06 07 08 09 10 11 12; do
  [ "$y$m" -le 202609 ] && echo "$y$m"; done; done | \
  xargs -P 12 -I{} sh -c '[ -s data/raw/emi_unit/{}.csv ] || curl -sS -L -f --retry 4 -o data/raw/emi_unit/{}.csv "'"$BASE"'/{}_Unit_level_generation.csv"'
ls data/raw/emi_unit/*.csv | while read f; do echo "$(sha256sum "$f" | cut -c1-64)  $(stat -c %s "$f")  $f"; done > data/raw/VINTAGE_emi_unit.txt
echo "prefetch done $(date -u +%FT%TZ): $(ls data/raw/emi_unit/*.csv | wc -l) files"
