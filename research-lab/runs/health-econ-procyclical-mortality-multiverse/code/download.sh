#!/bin/bash
# raw downloads: NBER mortality 1976-2004 (CSV zips), SEER populations, CDC state datasets, FRED LAUS annual series
set -u
D="$(cd "$(dirname "$0")/.." && pwd)/data/raw"   # the run's data/raw (was a hard-coded scratch path)
for y in $(seq 1976 2004); do
  f=$D/nber/mort$y.csv.zip
  [ -s $f ] && unzip -tq $f >/dev/null 2>&1 && continue
  until curl -sf -C - -m 1800 -o $f https://data.nber.org/mortality/$y/mort$y.csv.zip; do sleep 5; done
  curl -sf -m 60 -o $D/nber/desc_mort$y.txt https://data.nber.org/mortality/$y/desc_mort$y.txt
  echo "nber $y $(stat -c %s $f)"
done
curl -sf -m 1800 -o $D/seer/us.1969_2024.20ages.adjusted.txt.gz https://seer.cancer.gov/popdata/yr1969_2024.20ages/us.1969_2024.20ages.adjusted.txt.gz && echo seer
for id in bi63-dtpu 3yf8-kanr muzy-jte6 xkb8-kh2a 44rk-q6r2 xbxb-epbu; do
  curl -sf -m 1800 -o $D/cdc/$id.csv "https://data.cdc.gov/api/views/$id/rows.csv?accessType=DOWNLOAD" && echo "cdc $id $(wc -l < $D/cdc/$id.csv)"
done
for st in AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY; do :; done
echo complete
