#!/bin/bash
# Download the raw inputs listed in plan.md sec 3 (ClinVar variant_summary snapshots, AlphaMissense hg38).
R=/mnt/citations/research-lab/runs/bioinformatics-vep-acmg-calibration-drift
B=https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/archive
cd $R/data/raw/clinvar
for s in 2019-12 2020-12 2021-12 2022-12 2023-12 2024-12 2025-12 2026-09; do
  y=${s%%-*}
  if [ "$y" -ge 2025 ]; then url=$B/variant_summary_$s.txt.gz; else url=$B/$y/variant_summary_$s.txt.gz; fi
  [ -s variant_summary_$s.txt.gz ] || curl -sS --retry 5 -o variant_summary_$s.txt.gz "$url" &
done
wait
ls -la
cd $R/data/raw/scores
curl -sS "https://zenodo.org/api/records/8208688" -o zenodo_8208688.json
url=$(python3 -c "import json;d=json.load(open('zenodo_8208688.json'));print([f['links']['self'] for f in d['files'] if f['key']=='AlphaMissense_hg38.tsv.gz'][0])")
[ -s AlphaMissense_hg38.tsv.gz ] || curl -sS -L --retry 5 -o AlphaMissense_hg38.tsv.gz "$url"
ls -la
echo "FETCH DONE"
