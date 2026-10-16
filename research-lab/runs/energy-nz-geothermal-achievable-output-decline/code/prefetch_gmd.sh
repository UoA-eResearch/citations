#!/bin/bash
# Prefetch EMI Generation_MD (half-hourly metered generation by plant, with fuel and technology codes),
# 2000-01 to 2026-09, from the blob store the EMI page redirects to; record the vintage.
set -u
cd "$(dirname "$0")/.."
BASE="https://emidatasets.blob.core.windows.net/publicdata/Datasets/Wholesale/Generation/Generation_MD"
for y in $(seq 2000 2026); do for m in 01 02 03 04 05 06 07 08 09 10 11 12; do
  [ "$y$m" -le 202609 ] && echo "$y$m"; done; done | \
  xargs -P 12 -I{} sh -c '[ -s data/raw/emi_gmd/{}.csv ] || curl -sS -L -f --retry 4 -o data/raw/emi_gmd/{}.csv "'"$BASE"'/{}_Generation_MD.csv"'
ls data/raw/emi_gmd/*.csv | while read f; do echo "$(sha256sum "$f" | cut -c1-64)  $(stat -c %s "$f")  $f"; done > data/raw/VINTAGE_emi_gmd.txt
echo "prefetch done $(date -u +%FT%TZ): $(ls data/raw/emi_gmd/*.csv | wc -l) files; stubs: $(grep -l 'Object moved' data/raw/emi_gmd/*.csv | wc -l)"
