#!/bin/bash
# Pull the three sources and record a sealed vintage: PortWatch revises its history, so the retrieval time
# and hash of exactly what was analysed matter (plan section 3).
set -u
cd "$(dirname "$0")/.."
log=data/raw/VINTAGE.txt
: > "$log"
get () {  # url, path
  curl -sS -L --retry 5 --retry-delay 10 -o "$2" "$1" && \
    echo "$(date -u +%FT%TZ)  $(sha256sum "$2" | cut -c1-64)  $(stat -c %s "$2")  $2  $1" >> "$log"
}
get "https://hub.arcgis.com/api/v3/datasets/acc668d199d1472abaaf2467133d4ca4_0/downloads/data?format=csv&spatialRefId=4326&where=1%3D1" data/raw/portwatch/ports.csv
get "https://hub.arcgis.com/api/v3/datasets/83b1bbc7b3354c5fb1f40673bb8f852e_0/downloads/data?format=csv&spatialRefId=4326&where=1%3D1" data/raw/portwatch/daily.csv
get "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.since1980.list.v04r01.csv" data/raw/ibtracs/ibtracs.since1980.csv
echo "downloads done"
cat "$log"
