#!/bin/bash
# Split-repair sensitivity pass (D2), after the secondary corpora run.
cd "$(dirname "$0")/.."
while kill -0 "$(cat logs/other.pid)" 2>/dev/null; do sleep 60; done
taskset -c ${CORES:-16-27} ./venv/bin/python code/repair_split.py data/samples/stp_conjecture.parquet results/rows/stp_conjecture.jsonl results/rows/stp_conjecture_repair.jsonl ${W:-12}
taskset -c ${CORES:-16-27} ./venv/bin/python code/repair_split.py data/samples/stp_statement.parquet results/rows/stp_statement.jsonl results/rows/stp_statement_repair.jsonl ${W:-12}
