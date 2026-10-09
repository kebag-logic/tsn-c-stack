#!/usr/bin/env python3
"""Verify worktree bytes, modes, index entries and gitlinks against an exact head."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

p = argparse.ArgumentParser()
p.add_argument('repo', type=Path)
p.add_argument('--head', default='6f4ecc9036f9ac2694b05a749cc9105d9c15c05f')
a = p.parse_args()
def git(*args):
    return subprocess.check_output(['git', '-C', str(a.repo), *args])
assert git('rev-parse', 'HEAD').decode().strip() == a.head
tree = git('rev-parse', 'HEAD^{tree}').decode().strip()
assert tree == '49585d392468cbf85cdf21ef5c7546cec079c8be'
expected = {}
for row in git('ls-tree', '-rz', a.head).split(b'\0'):
    if row:
        meta, path = row.split(b'\t', 1)
        mode, kind, oid = meta.decode().split()
        expected[path.decode()] = (mode, kind, oid)
index = {}
for row in git('ls-files', '--stage', '-z').split(b'\0'):
    if row:
        meta, path = row.split(b'\t', 1)
        mode, oid, stage = meta.decode().split()
        assert stage == '0'
        index[path.decode()] = (mode, oid)
assert set(expected) == set(index)
verified = []
gitlinks = []
for name, (mode, kind, oid) in expected.items():
    assert index[name] == (mode, oid), name
    file = a.repo / name
    if mode == '160000':
        actual = subprocess.check_output(['git', '-C', str(file), 'rev-parse', 'HEAD']).decode().strip()
        assert actual == oid, name
        gitlinks.append({'path': name, 'commit': oid})
        continue
    data = os.readlink(file).encode() if mode == '120000' else file.read_bytes()
    actual_oid = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert actual_oid == oid, name
    actual_mode = '120000' if file.is_symlink() else ('100755' if file.stat().st_mode & stat.S_IXUSR else '100644')
    assert actual_mode == mode, name
    verified.append({'path': name, 'mode': mode, 'git_blob': oid, 'sha256': hashlib.sha256(data).hexdigest()})
status = git('status', '--porcelain=v1', '--untracked-files=all').decode()
assert not status, status
print(json.dumps({'head': a.head, 'tree': tree, 'tracked_files': len(verified),
                  'index_matches_head': True, 'worktree_bytes_and_modes_match_head': True,
                  'gitlinks': gitlinks, 'status': status, 'files': verified}, indent=2))
