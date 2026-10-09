#!/bin/sh
# SPDX-License-Identifier: MIT
# Usage: integrity.sh <clone> <expected head> <expected tree>
# Verifies HEAD, index tree, clean worktree, every tracked blob's bytes and mode, and gitlinks.
set -u
cd "$1" || exit 99
fail=0
[ "$(git rev-parse HEAD)" = "$2" ] && echo "head ok $2" || { echo "HEAD MISMATCH"; fail=1; }
[ "$(git rev-parse 'HEAD^{tree}')" = "$3" ] && echo "head tree ok $3" || { echo "TREE MISMATCH"; fail=1; }
[ "$(git write-tree)" = "$3" ] && echo "index tree ok" || { echo "INDEX MISMATCH"; fail=1; }
s=$(git status --porcelain --untracked-files=all); [ -z "$s" ] && echo "worktree clean (untracked included)" || { echo "DIRTY: $s"; fail=1; }
n=0; bad=0
git ls-tree -r HEAD | while read mode type oid path; do
  if [ "$type" = commit ]; then echo "gitlink $path $oid"; continue; fi
  h=$(git hash-object --no-filters -- "$path")
  if [ -x "$path" ]; then m=100755; else m=100644; fi
  [ -L "$path" ] && m=120000
  if [ "$h" != "$oid" ] || [ "$m" != "$mode" ]; then echo "BLOB MISMATCH $path"; fi
done > /tmp/integrity.$$ 2>&1
grep -q MISMATCH /tmp/integrity.$$ && { cat /tmp/integrity.$$; fail=1; }
echo "tracked blobs: $(git ls-tree -r HEAD | grep -c ' blob ') ; gitlinks: $(git ls-tree -r HEAD | grep -c ' commit ')"
echo "ignored files present: $(git status --porcelain --ignored | grep -c '^!!')"
rm -f /tmp/integrity.$$
echo "integrity rc $fail"; exit $fail
