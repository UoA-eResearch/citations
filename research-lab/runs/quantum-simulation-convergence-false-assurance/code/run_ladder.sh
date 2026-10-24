#!/bin/bash
# usage: run_ladder.sh NAME METHOD SETTINGS NSHARDS  -> data/results/NAME/METHOD_<shard>.json
set -u
cd "$(dirname "$0")/.."
export JULIA_DEPOT_PATH=/mnt/qsim/depot OPENBLAS_NUM_THREADS=1 PP_MAXTERMS=${PP_MAXTERMS:-100000000}
mkdir -p data/results/$1 logs
for s in $(seq 0 $(($4 - 1))); do
  nohup ~/.juliaup/bin/julia --project=/mnt/qsim/env code/approx.jl data/instances/$1.json data/results/$1/$2_$s.json $2 $3 $s $4 \
    > logs/$1_$2_$s.log 2>&1 &
done
wait
echo "== $1 $2 done $(TZ=Pacific/Auckland date +%H:%M)"
