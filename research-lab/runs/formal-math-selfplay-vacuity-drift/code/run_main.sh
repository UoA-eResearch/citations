#!/bin/bash
# Main STP run (plan.md section 2; deviations D1): primary windows with triviality, then other iterations, then statements.
cd "$(dirname "$0")/.."
W=${W:-12}; CORES=${CORES:-16-27}
taskset -c $CORES ./venv/bin/python code/run_rows.py data/samples/stp_conjecture.parquet results/rows/stp_conjecture.jsonl $W --trivial-iters 1-9,38-47 --filter "(iteration <= 9) or (iteration >= 38)"
taskset -c $CORES ./venv/bin/python code/run_rows.py data/samples/stp_conjecture.parquet results/rows/stp_conjecture.jsonl $W --trivial-iters 1-9,38-47
taskset -c $CORES ./venv/bin/python code/run_rows.py data/samples/stp_statement.parquet results/rows/stp_statement.jsonl $W
