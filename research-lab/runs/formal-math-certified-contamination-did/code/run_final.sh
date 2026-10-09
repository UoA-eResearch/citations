#!/bin/bash
# D7: after STP verification and the DeepSeek-Prover-V2 resampling, verify DeepSeek-Prover-V2 (10 workers, REPL restart
# every 40 commands; the 20 GB watchdog stays on), then run the committed analysis (all provers incl. STP).
cd "$(dirname "$0")/.."
until grep -q "stp verified" logs/cpu_verify.log && grep -q "dsp_v2 done" logs/gpu_dsp.log; do sleep 120; done
export VERIFY_MAX_CMDS=40
VAC_TOOLCHAIN=v49 taskset -c 4-27 ./venv/bin/python code/verify.py dsp_v2 10
echo "dsp_v2 verified $(date)"
taskset -c 0-3 ./venv/bin/python code/analysis.py > logs/analysis.log 2>&1
echo "final done $(date)"
