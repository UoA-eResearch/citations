#!/bin/bash
# Download GHCN-Daily per-station files (NCEI by_station, current release) for every station whose inventory TMAX
# coverage spans 1951 to 2025 or longer (plan.md sec 3). 8 parallel workers; resumable; atomic renames.
R=/mnt/citations/research-lab/runs/climate-earth-record-margin-obs
cd $R/data/raw
awk '$4=="TMAX" && $5<=1951 && $6>=2025 {print $1}' ghcnd-inventory.txt | sort -u > stations_candidate.txt
echo "candidates: $(wc -l < stations_candidate.txt)"
fetch() {
  f=by_station/$1.csv.gz
  [ -s "$f" ] && return 0
  for a in 1 2 3 4 5; do
    curl -sS --max-time 600 -o "$f.part" "https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/$1.csv.gz" && mv "$f.part" "$f" && return 0
    sleep $((a * 10))
  done
  echo "FAILED $1"
}
export -f fetch
cat stations_candidate.txt | xargs -P 8 -I{} bash -c 'fetch {}'
echo "FETCH DONE: $(ls by_station/*.csv.gz | wc -l) files"
