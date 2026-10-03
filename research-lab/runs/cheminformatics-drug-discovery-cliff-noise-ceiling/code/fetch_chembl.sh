#!/bin/bash
# Download the ChEMBL 37 SQLite dump with parallel HTTP range requests (EBI serves about 90 KB/s per connection here),
# verify it against EBI's published checksum, and unpack it. Rerunnable: finished parts are kept.
# Usage: fetch_chembl.sh [PARTS=64]
set -u
cd "$(dirname "$0")/../data"
U=https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/chembl_37
F=chembl_37_sqlite.tar.gz
P=${1:-64}
SIZE=$(curl -sI "$U/$F" | awk 'tolower($1)=="content-length:"{print $2}' | tr -d '\r')
echo "size $SIZE bytes in $P parts"
mkdir -p parts
CHUNK=$(( (SIZE + P - 1) / P ))
for i in $(seq 0 $((P - 1))); do
  s=$((i * CHUNK)); e=$((s + CHUNK - 1)); [ $e -ge $SIZE ] && e=$((SIZE - 1))
  want=$((e - s + 1))
  f=parts/part_$(printf "%03d" $i)
  ( for try in 1 2 3 4 5 6; do
      [ -f $f ] && [ $(stat -c %s $f) -eq $want ] && break
      curl -s --retry 3 -r $s-$e -o $f "$U/$F"
    done ) &
done
wait
for i in $(seq 0 $((P - 1))); do
  s=$((i * CHUNK)); e=$((s + CHUNK - 1)); [ $e -ge $SIZE ] && e=$((SIZE - 1))
  f=parts/part_$(printf "%03d" $i)
  [ $(stat -c %s $f) -eq $((e - s + 1)) ] || { echo "part $i incomplete"; exit 1; }
done
cat parts/part_* > $F
curl -s "$U/checksums.txt" > checksums.txt
want=$(grep " $F\$\|$F" checksums.txt | awk '{print $1}' | head -1)
got=$(sha256sum $F | awk '{print $1}')
echo "checksum file: $want"
echo "computed     : $got"
if [ "$want" = "$got" ]; then echo "CHECKSUM OK"; rm -rf parts; tar -xzf $F && echo "unpacked"; else
  got_md5=$(md5sum $F | awk '{print $1}'); echo "md5 $got_md5"; [ "$want" = "$got_md5" ] && { echo "CHECKSUM OK (md5)"; rm -rf parts; tar -xzf $F && echo "unpacked"; } || echo "CHECKSUM MISMATCH"; fi
