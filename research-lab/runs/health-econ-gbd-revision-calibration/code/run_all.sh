#!/bin/bash
# Full pipeline after the plan commit: build the panel, quality covariates, synthetic tests, then the analysis.
set -e
cd "$(dirname "$0")/.."
./venv/bin/python code/build.py
./venv/bin/python code/quality.py
./venv/bin/python tests/synthetic_test.py
./venv/bin/python code/analysis.py > logs/analysis.log 2>&1
echo "ANALYSIS DONE $(date)"
