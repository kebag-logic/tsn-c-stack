#!/bin/sh
# Verify a review clone is at the exact head with untouched tracked bytes, modes, index and no gitlinks.
# Usage: clone_integrity.sh <review-clone>   (prints a text receipt)
set -u
cd "$1" || exit 2
echo "HEAD $(git rev-parse HEAD) tree $(git rev-parse HEAD^{tree})"
echo "status --porcelain --ignored entries: $(git status --porcelain --ignored | wc -l)"
echo "index vs HEAD tree (diff-index --cached): $(git diff-index --cached HEAD | wc -l) entries"
echo "worktree vs index (diff-files): $(git diff-files | wc -l) entries"
echo "index tree == HEAD tree: $( [ "$(git write-tree)" = "$(git rev-parse HEAD^{tree})" ] && echo yes || echo NO)"
echo "gitlinks (mode 160000) in HEAD tree: $(git ls-tree -r HEAD | awk '$1==160000' | wc -l)"
echo ".gitmodules present: $( [ -e .gitmodules ] && echo yes || echo no)"
python3 -I scripts/check_privacy.py --selftest; echo "selftest rc $?"
python3 -I scripts/check_privacy.py | tail -1; echo "gate rc $?"
python3 -I scripts/check_privacy.py --bogus; echo "bogus-arg rc $?"
python3 -I - <<'EOF'
import os, stat, subprocess
out = subprocess.check_output(["git", "ls-files", "-s", "-z"]).decode().split("\0")
n = bad = 0
for rec in filter(None, out):
    meta, path = rec.split("\t", 1)
    mode, oid, st = meta.split()
    head = subprocess.check_output(["git", "rev-parse", "HEAD:" + path]).decode().strip()
    work = subprocess.check_output(["git", "hash-object", "--no-filters", "--", path]).decode().strip()
    wmode = "100755" if os.lstat(path).st_mode & stat.S_IXUSR else "100644"
    n += 1
    if not (st == "0" and oid == head == work and mode == wmode):
        bad += 1
        print("MISMATCH", path, mode, wmode, oid, head, work, st)
print(f"tracked entries: {n}; index oid == HEAD oid == work-tree raw-byte oid and mode match for all: {bad == 0} (mismatches {bad})")
EOF
