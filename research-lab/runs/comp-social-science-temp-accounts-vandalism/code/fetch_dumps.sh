#!/bin/bash
# Download the 2026-08 mediawiki_history files covering 2024-01 onward for the 40 sampled wikis (plan.md sec 2), from
# the ftp.acc.umu.se mirror (the main site rate-limits with HTTP 429; deviations.md D3). The file list comes from the
# main site's index. Each file must pass `bzip2 -t`; failures are deleted and retried (up to 3 times).
set -u
cd "$(dirname "$0")/.."
MAIN=https://dumps.wikimedia.org/other/mediawiki_history/2026-08
MIRROR=https://ftp.acc.umu.se/mirror/wikimedia.org/other/mediawiki_history/2026-08
mkdir -p data/raw/dumps
tail -n +2 results/tables/wikis.csv | cut -d, -f1 > data/raw/sample_wikis.txt
if [ ! -s data/raw/files.txt ]; then
  : > data/raw/files.txt
  while read -r w; do
    curl -s --max-time 120 "$MIRROR/$w/" | grep -o 'href="[^"]*\.tsv\.bz2"' | cut -d'"' -f2 | sed 's#.*/##' | \
      grep -E "\.(all-time|2024|2025|2026)(-[0-9]{2})?\.tsv\.bz2$" | sort -u | sed "s#^#$w/#" >> data/raw/files.txt
  done < data/raw/sample_wikis.txt
fi
echo "files: $(wc -l < data/raw/files.txt)"
fetch() {
  f=$1; out=data/raw/dumps/$(basename "$f")
  for try in 1 2 3; do
    if [ -s "$out" ] && bzip2 -tq "$out" 2>/dev/null; then echo "ok $f"; return; fi
    rm -f -- "$out"
    curl -s --retry 5 --retry-delay 15 -o "$out" "$MIRROR/$f"
  done
  if bzip2 -tq "$out" 2>/dev/null; then echo "ok $f"; else echo "FAILED $f"; fi
}
export -f fetch; export MIRROR
xargs -P 4 -I{} bash -c 'fetch {}' < data/raw/files.txt
echo ALL_DOWNLOADS_FINISHED
