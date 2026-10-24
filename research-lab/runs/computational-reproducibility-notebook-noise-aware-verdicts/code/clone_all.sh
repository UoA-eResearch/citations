#!/bin/bash
# Parallel blob-less clones of the sampled repositories (no checkout); select_nb.py then checks out the AS-OF commit.
cd "$(dirname "$0")/.."
one() { d=data/repos/$(echo "$1" | sed 's#/#__#'); [ -d "$d/.git" ] && return; GIT_TERMINAL_PROMPT=0 timeout 1800 git clone -q --filter=blob:none --no-checkout "https://github.com/$1" "$d" 2>/dev/null && echo "ok $1" || { rm -rf "$d"; echo "fail $1"; }; }
export -f one
xargs -a data/interim/repos.txt -P 8 -I{} bash -c 'one "$@"' _ {}
echo complete
