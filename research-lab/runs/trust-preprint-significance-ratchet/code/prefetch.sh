#!/bin/bash
# Prefetch the Europe PMC preprint full-text shards and the PreprintToPaper linkage set; record the vintage.
set -u
cd "$(dirname "$0")/.."
B=https://ftp.ebi.ac.uk/pub/databases/pmc/preprints
for f in PPR7001_PPR208218 PPR208220_PPR298000 PPR298020_PPR410482 PPR410483_PPR517560 PPR517566_PPR634539 \
         PPR634565_PPR806423 PPR806431_PPR1083379 PPR1083383_PPR1317105; do echo "$f.xml.gz"; done | \
  xargs -P 4 -I{} sh -c '[ -s data/raw/europepmc_preprints/{} ] || curl -sS -L -f --retry 4 -o data/raw/europepmc_preprints/{} '"$B"'/{}'
[ -s data/raw/europepmc_preprints/pprid.txt.gz ] || curl -sS -L -f -o data/raw/europepmc_preprints/pprid.txt.gz $B/pprid.txt.gz
curl -sS "https://zenodo.org/api/records/17992421" > data/raw/preprinttopaper/record.json
python3 -c "
import json; r=json.load(open('data/raw/preprinttopaper/record.json'))
for f in r['files']: print(f['key'], f['links']['self'])" | while read k u; do [ -s "data/raw/preprinttopaper/$k" ] || curl -sS -L -f --retry 4 -o "data/raw/preprinttopaper/$k" "$u"; done
find data/raw -type f | sort | while read f; do echo "$(sha256sum "$f" | cut -c1-64)  $(stat -c %s "$f")  $f"; done > data/raw/VINTAGE.txt
echo "prefetch done $(date -u +%FT%TZ)"
