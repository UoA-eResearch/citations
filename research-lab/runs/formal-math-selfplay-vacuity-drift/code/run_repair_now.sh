#!/bin/bash
# Split-repair sensitivity pass (D2), run on cores 0-11 while the secondary corpora run on 16-27 (D3).
cd "$(dirname "$0")/.."
taskset -c 0-11 ./venv/bin/python code/repair_split.py data/samples/stp_conjecture.parquet results/rows/stp_conjecture.jsonl results/rows/stp_conjecture_repair.jsonl 10
taskset -c 0-11 ./venv/bin/python code/repair_split.py data/samples/stp_statement.parquet results/rows/stp_statement.jsonl results/rows/stp_statement_repair.jsonl 10
