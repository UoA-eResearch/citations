#!/bin/bash
# depth-1 checkout of a mathlib4 commit plus its prebuilt olean cache
set -e
name=$1; sha=$2
export PATH=$HOME/.elan/bin:$PATH
mkdir -p snaps/$name && cd snaps/$name
[ -d .git ] || git init -q
git remote add origin https://github.com/leanprover-community/mathlib4.git 2>/dev/null || true
git fetch -q --depth 1 origin $sha
git checkout -q FETCH_HEAD
echo "$name toolchain $(cat lean-toolchain)"
lake exe cache get > ../../cache_$name.log 2>&1 || echo "$name cache get FAILED"
echo "$name done $(du -sh .lake 2>/dev/null | cut -f1)"
