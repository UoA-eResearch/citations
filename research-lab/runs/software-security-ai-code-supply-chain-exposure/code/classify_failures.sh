#!/bin/bash
# Re-try each failed clone once and classify the failure (D1): inactive (no commits since 2024-01-01), missing, other.
# usage: code/classify_failures.sh logs/clone1.log data/interim/clone_failures.tsv
LOG=$1; OUT=$2; export REPOS=$(cd "$(dirname "$0")/.." && pwd)/data/repos
one() {
  r=$1; t=$(mktemp -d)
  err=$(GIT_TERMINAL_PROMPT=0 timeout 600 git clone -q --bare --filter=tree:0 --shallow-since=2024-01-01 "https://github.com/$r" "$t/x.git" 2>&1)
  rc=$?
  if [ $rc -eq 0 ]; then
    d=$REPOS/$(echo "$r" | sed 's#/#__#').git
    mv "$t/x.git" "$d" 2>/dev/null && echo -e "$r\tok_on_retry" || echo -e "$r\tok_on_retry_move_failed"
  elif echo "$err" | grep -q "shallow info"; then echo -e "$r\tinactive"
  elif echo "$err" | grep -qiE "not found|terminal prompts disabled|could not read Username|Repository not found"; then echo -e "$r\tmissing"
  else echo -e "$r\tother: $(echo "$err" | tail -1 | cut -c1-80)"; fi
  rm -rf "$t"
}
export -f one
grep "^fail" "$LOG" | cut -d' ' -f2 | xargs -P 6 -I{} bash -c 'one "$@"' _ {} > "$OUT"
echo complete
