#!/bin/bash
# run_large.sh : the H4 pipeline for Whisper-large-v3 (plan section 5, D2), run after the Whisper-small queues
cd "$(dirname "$0")/.." || exit 1
export HF_HOME=/mnt/data/asr-accent-parity/hf
M=large-v3
code/run_queue.sh $M test fp16
code/run_queue.sh $M validation fp16
venv/bin/python -I code/score.py valgroups $M > logs/valgroups_$M.log 2>&1
venv/bin/python -I code/manifest.py worst $M > logs/manifest_worst_$M.log 2>&1
code/run_queue.sh $M test rtn_w4 gptq_w4_us_s0 gptq_w4_balanced_s0 gptq_w4_us_s1 gptq_w4_balanced_s1 gptq_w4_us_s2 gptq_w4_balanced_s2 gptq_w4_worst_s0 gptq_w4_worst_s1 gptq_w4_worst_s2
venv/bin/python -I code/score.py analyze $M > logs/analyze_${M}_w4.log 2>&1
if venv/bin/python -I -c "import json,sys; a=json.load(open('results/tables/analysis_$M.json')); sys.exit(0 if a['H1_w4'].get('positive_control_holds') else 1)"; then
  echo "W4 positive control holds for $M; no W3 fallback"
else
  echo "W4 positive control fails for $M; W3 fallback (D2)"
  code/run_queue.sh $M test gptq_w3_us_s0 gptq_w3_balanced_s0 gptq_w3_us_s1 gptq_w3_balanced_s1 gptq_w3_us_s2 gptq_w3_balanced_s2 gptq_w3_worst_s0 gptq_w3_worst_s1 gptq_w3_worst_s2
  venv/bin/python -I code/score.py analyze $M > logs/analyze_${M}_w3.log 2>&1
fi
echo "large pipeline done $(date '+%H:%M:%S')"
