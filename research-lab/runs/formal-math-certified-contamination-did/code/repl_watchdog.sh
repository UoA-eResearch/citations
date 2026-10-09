#!/bin/bash
# D6: memory safety net during verification. Kills any single Lean REPL whose resident memory exceeds 20 GB (one runaway
# proof check); the verifier then records that output as a failure ("timeout"/dead REPL), like the 150 s time limit.
while true; do
  ps -eo pid,rss,args | awk '$3 ~ /lean\/repl(_v415)?\/.lake\/build\/bin\/repl$/ && $2 > 20000000 {print $1, $2}' | while read pid rss; do
    kill -9 "$pid" && echo "$(date '+%F %T') killed repl $pid at $((rss/1000000)) GB"
  done
  sleep 5
done
