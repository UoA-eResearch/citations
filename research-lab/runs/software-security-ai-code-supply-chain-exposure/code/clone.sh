#!/bin/bash
# Bare, treeless, shallow-since-2024 clones of the study repositories (plan section 1); 8 in parallel, one retry.
# usage: code/clone.sh data/interim/repos.txt data/repos
LIST=$1; OUT=$2
one() {
  r=$1; d=$2/$(echo "$r" | sed 's#/#__#').git
  [ -d "$d" ] && [ -f "$d/HEAD" ] && { echo "skip $r"; return; }
  for k in 1 2; do
    rm -rf "$d"
    if GIT_TERMINAL_PROMPT=0 timeout 1200 git clone -q --bare --filter=tree:0 --shallow-since=2024-01-01 "https://github.com/$r" "$d" 2>/dev/null; then
      echo "ok $r"; return
    fi
    sleep 3
  done
  rm -rf "$d"; echo "fail $r"
}
export -f one
xargs -a "$LIST" -P 8 -I{} bash -c 'one "$@"' _ {} "$OUT"
echo complete
