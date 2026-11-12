#!/usr/bin/env bash
# Rebuild everything. Usage: run_all.sh <SRA3 Topics & Topic Clusters workbook.xlsx> [stakeholder engagement workbook.xlsx]
# PY needs requests, numpy, networkx, openpyxl (see README). Keys: ~/.config/openalex/api_key and
# ~/.config/elsevier/api_key (Scopus/SciVal; calls must come from the University network).
# Internal inputs (git-ignored): the SRA3 workbook, the engagement workbook (default
# $BPH_WORK/engagement/stakeholder_engagement.xlsx), $BPH_WORK/engagement/workshop2_maps.json and photos,
# and bph/probes.local.txt (the SRA's list of missing areas; probes.txt holds public examples).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/mnt/citations/impact/.venv/bin/python}"
"$PY" "$here/parse_scival.py" "$1"
"$PY" "$here/fetch_works.py"
"$PY" "$here/fetch_awards.py"
"$PY" "$here/fetch_marsden.py"
"$PY" "$here/fetch_mfat.py"
"$PY" "$here/analyse.py"
"$PY" "$here/engaged.py" ${2:+"$2"}
"$PY" "$here/fetch_scival.py"
"$PY" "$here/scival_topics.py"
"$PY" "$here/probe_keywords.py"
"$PY" "$here/world.py"
"$PY" "$here/bundle.py"
