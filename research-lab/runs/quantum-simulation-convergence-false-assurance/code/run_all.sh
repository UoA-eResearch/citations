#!/bin/bash
# Full pipeline (after code/fetch of Julia packages; see report "Reproducing it").
set -eu
cd "$(dirname "$0")/.."
venv/bin/python -I code/instances.py test
venv/bin/python -I code/instances.py lattice
venv/bin/python -I code/instances.py make pilot 30 7
venv/bin/python -I code/instances.py make main 300 20261025
THREADS=14 venv/bin/python -I code/instances.py exact main
code/run_ladder.sh main bp 4,8,16 6
code/run_ladder.sh main pp 0.01,0.003,0.001,0.0003,0.0001 6
venv/bin/python -I code/instances.py crosscheck main
venv/bin/python -I code/analyse.py
venv/bin/python -I code/figures.py
