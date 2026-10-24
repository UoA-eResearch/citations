#!/bin/bash
# Runs the build stages in order; stops at the first failure.
set -e
cd "$(dirname "$0")/.."
for s in passA passB select1 passC select2 passD; do
  echo "== $s $(date +%H:%M:%S)"
  env WORKERS=${WORKERS:-14} venv/bin/python -I code/build.py $s
done
echo "== done $(date +%H:%M:%S)"
