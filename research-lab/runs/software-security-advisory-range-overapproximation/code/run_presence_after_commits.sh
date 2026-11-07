#!/bin/bash
cd "$(dirname "$0")/.."
until grep -q "^commits ok" logs/commits.log 2>/dev/null; do sleep 30; done
venv/bin/python -I code/presence.py run > logs/presence.log 2>&1
echo "== presence chain done $(date)" >> logs/presence.log
