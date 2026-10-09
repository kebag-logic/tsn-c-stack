#!/usr/bin/env python3
"""Verify detached head, index entries, tracked bytes/modes, and all gitlinks.

Usage: check_integrity.py SOURCE INITIAL_INDEX OUTPUT_JSON
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

root, initial, output = (Path(p).resolve() for p in sys.argv[1:])
head = 'b7c6b7ba0007aaa5791df68d30296423127b003e'
tree = '611e16d1d01f6fe901ceb2eb0c07b7be4acaa284'

def git(*args):
    return subprocess.check_output(['git', '-C', str(root), *args])

errors = []
actual_head = git('rev-parse', 'HEAD').decode().strip()
actual_tree = git('rev-parse', 'HEAD^{tree}').decode().strip()
if (actual_head, actual_tree) != (head, tree):
    errors.append('head/tree mismatch')
detached = subprocess.run(['git', '-C', str(root), 'symbolic-ref', '-q', 'HEAD'], capture_output=True).returncode == 1
if not detached:
    errors.append('checkout is not detached')
if git('ls-files', '--stage') != initial.read_bytes():
    errors.append('index changed from recorded initial entries')
expected_index = []
checked = []
gitlinks = []
for entry in git('ls-tree', '-rz', 'HEAD').split(b'\0'):
    if not entry:
        continue
    meta, name = entry.split(b'\t', 1)
    mode, kind, oid = meta.decode().split()
    filename = os.fsdecode(name)
    expected_index.append((mode, oid, filename))
    path = root / filename
    if mode == '160000':
        gitlinks.append({'path': filename, 'expected': oid})
        if git('-C', str(path), 'rev-parse', 'HEAD').decode().strip() != oid:
            errors.append('gitlink mismatch: ' + filename)
        continue
    if mode == '120000':
        data = os.fsencode(os.readlink(path))
        actual_mode = '120000' if path.is_symlink() else 'invalid'
    else:
        data = path.read_bytes()
        st = path.stat()
        actual_mode = '100755' if st.st_mode & stat.S_IXUSR else '100644'
        if not stat.S_ISREG(st.st_mode):
            actual_mode = 'invalid'
    calculated = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if calculated != oid or actual_mode != mode:
        errors.append('tracked byte/mode mismatch: ' + filename)
    checked.append({'path': filename, 'blob': oid, 'mode': mode, 'verified': calculated == oid and actual_mode == mode})
actual_index = []
for entry in git('ls-files', '--stage', '-z').split(b'\0'):
    if entry:
        meta, name = entry.split(b'\t', 1)
        mode, oid, stage = meta.decode().split()
        if stage != '0':
            errors.append('unmerged index entry')
        actual_index.append((mode, oid, os.fsdecode(name)))
if sorted(actual_index) != sorted(expected_index):
    errors.append('index differs from exact-head tree')
status = git('status', '--porcelain=v1', '--untracked-files=all', '--ignored').decode()
if status:
    errors.append('nonempty worktree status')
baseline_gitlinks = {}
for ref in ['18d737832c376f32660eb21fe2796e0b611507e3', '61fb7c9a523b89cb96d493c5baf9f7f866ebed85', head]:
    baseline_gitlinks[ref] = [line for line in git('ls-tree', '-r', ref).decode().splitlines() if line.startswith('160000 ')]
result = dict(head=actual_head, tree=actual_tree, detached=detached,
              initial_index_equal=git('ls-files', '--stage') == initial.read_bytes(),
              tracked_count=len(checked), tracked=checked, gitlinks=gitlinks,
              gitlinks_at_required_revisions=baseline_gitlinks, status=status, errors=errors)
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ['head', 'tree', 'detached', 'initial_index_equal', 'tracked_count', 'gitlinks', 'status', 'errors']}, indent=2))
raise SystemExit(int(bool(errors)))
