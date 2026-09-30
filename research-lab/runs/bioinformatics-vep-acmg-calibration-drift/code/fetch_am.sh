#!/bin/bash
# Resumable download of the AlphaMissense hg38 release (Zenodo 8208688); loops until the size matches.
cd /mnt/citations/research-lab/runs/bioinformatics-vep-acmg-calibration-drift/data/raw/scores
WANT=642961469
until [ "$(stat -c %s AlphaMissense_hg38.tsv.gz.part 2>/dev/null || echo 0)" = "$WANT" ]; do
  curl -sS -L -C - --retry 10 --retry-all-errors -o AlphaMissense_hg38.tsv.gz.part "https://zenodo.org/api/records/8208688/files/AlphaMissense_hg38.tsv.gz/content" || sleep 15
done
mv AlphaMissense_hg38.tsv.gz.part AlphaMissense_hg38.tsv.gz && echo "AM DONE"
