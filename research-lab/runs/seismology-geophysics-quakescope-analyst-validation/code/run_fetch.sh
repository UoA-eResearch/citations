#!/bin/bash
# Downloads (plan section 8, steps 1-2). No matching.
cd "$(dirname "$0")/.."
export PYTHONUNBUFFERED=1
./venv/bin/python code/fetch.py meta && echo "meta done $(date)"
./venv/bin/python code/fetch.py phases && echo "phases step done $(date)"
./venv/bin/python code/fetch.py picks && echo "picks step done $(date)"
echo "FETCH DONE $(date)"
