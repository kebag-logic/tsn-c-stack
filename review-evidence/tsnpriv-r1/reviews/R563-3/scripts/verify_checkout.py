#!/usr/bin/env python3
"""Check exact tracked bytes, executable modes, index, detached head and gitlinks.

Usage: python3 scripts/verify_checkout.py SOURCE PACKET
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

source = Path(sys.argv[1]).resolve()
packet = Path(sys.argv[2]).resolve()
head = 'b7c6b7ba0007aaa5791df68d30296423127b003e'
tree = '611e16d1d01f6fe901ceb2eb0c07b7be4acaa284'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=source)


assert git('rev-parse', 'HEAD').decode().strip() == head
assert git('rev-parse', 'HEAD^{tree}').decode().strip() == tree
assert subprocess.run(['git', 'symbolic-ref', '-q', 'HEAD'], cwd=source, capture_output=True).returncode == 1
index = git('ls-files', '--stage')
assert index == (packet / 'receipts/initial-gitlinks.txt').read_bytes()
entries = []
gitlinks = []
for row in git('ls-tree', '-rz', 'HEAD').split(b'\0'):
    if not row: continue
    metadata, name = row.split(b'\t', 1)
    mode, kind, oid = metadata.decode().split()
    name = name.decode()
    if kind == 'commit':
        gitlinks.append({'path': name, 'oid': oid, 'mode': mode})
        continue
    assert kind == 'blob'
    path = source / name
    if mode == '120000':
        assert path.is_symlink()
        data = os.readlink(path).encode()
        actual_mode = '120000'
    else:
        assert stat.S_ISREG(path.lstat().st_mode)
        data = path.read_bytes()
        actual_mode = '100755' if path.stat().st_mode & stat.S_IXUSR else '100644'
    actual_oid = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    assert actual_oid == oid and actual_mode == mode, name
    entries.append({'path': name, 'oid': oid, 'mode': mode, 'raw_bytes_match': True})
assert len(entries) == 74
assert not gitlinks and not (source / '.gitmodules').exists()
assert not git('status', '--porcelain=v1', '--ignored')
result = {'head': head, 'tree': tree, 'detached': True, 'index_unchanged_from_initial': True,
          'tracked_blobs': entries, 'gitlinks': gitlinks, 'gitmodules_present': False,
          'status_including_ignored': 'clean'}
(packet / 'receipts/checkout-integrity.json').write_text(json.dumps(result, indent=2) + '\n')
print('Exact head/tree, detached checkout, 74 tracked blob bytes and modes, unchanged index: PASS')
print('Required gitlinks: 0; .gitmodules absent; status including ignored files: clean')
