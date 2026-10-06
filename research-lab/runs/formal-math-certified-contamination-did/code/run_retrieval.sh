#!/bin/bash
# Candidate retrieval for every benchmark over every corpus, after the large-corpus extraction finishes.
cd "$(dirname "$0")/.."
while kill -0 3054989 2>/dev/null; do sleep 30; done
for b in bench_minif2f bench_putnam bench_proofnet bench_minif2f_v2c; do
  taskset -c 0-3 ./venv/bin/python code/retrieve.py $b
done
echo "retrieval done $(date)"
