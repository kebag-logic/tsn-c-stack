#!/usr/bin/env python3
"""Verify the review checkout against the expected tree without updating it."""
import argparse
import hashlib
import os
from pathlib import Path
import stat
import subprocess

HEAD = '61fb7c9a523b89cb96d493c5baf9f7f866ebed85'
TREE = 'adbb235a09246169ab95756fba0a7f163131924d'
BASE = '18d737832c376f32660eb21fe2796e0b611507e3'
EXPECTED = {'docs/IMPORT.md', 'docs/VERIFICATION.md', 'scripts/check_privacy.py', 'scripts/validate.py'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--initial-index', type=Path, required=True)
    args = p.parse_args()
    repo = args.repo.resolve()
    def git(*argv):
        return subprocess.check_output(['git', '-C', str(repo), *argv])
    if git('rev-parse', 'HEAD', 'HEAD^{tree}').decode().splitlines() != [HEAD, TREE]:
        raise RuntimeError('head or tree changed')
    if git('ls-files', '--stage') != args.initial_index.read_bytes():
        raise RuntimeError('index differs from initial index')
    if git('status', '--porcelain=v1'):
        raise RuntimeError('checkout is not clean')
    if git('diff', '--cached', '--raw', HEAD):
        raise RuntimeError('index differs from head')
    changed = set(git('diff', '--name-only', BASE, HEAD).decode().splitlines())
    if changed != EXPECTED:
        raise RuntimeError('unexpected changed paths')
    print('head', HEAD)
    print('tree', TREE)
    print('index: all stage entries match the initial index and HEAD')
    print('status: clean; detached:', subprocess.run(['git', '-C', str(repo), 'symbolic-ref', '-q', 'HEAD'], stdout=subprocess.DEVNULL).returncode == 1)
    print('path\tgit_mode\tworktree_mode\tblob_id\tsha256\tresult')
    count, gitlinks, rtl = 0, [], []
    for entry in git('ls-tree', '-r', '-z', HEAD).split(b'\0'):
        if not entry:
            continue
        info, raw_name = entry.split(b'\t', 1)
        mode, kind, oid = info.decode().split()
        name = raw_name.decode()
        if mode == '160000':
            gitlinks.append((name, oid))
            continue
        path = repo / name
        if kind != 'blob':
            raise RuntimeError('unexpected tree entry')
        s = path.lstat()
        if mode == '120000':
            data = os.readlink(path).encode()
            actual_mode = '120000' if stat.S_ISLNK(s.st_mode) else 'invalid'
        else:
            data = path.read_bytes()
            actual_mode = ('100755' if s.st_mode & 0o111 else '100644') if stat.S_ISREG(s.st_mode) else 'invalid'
        actual_oid = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if actual_oid != oid or actual_mode != mode:
            raise RuntimeError(name + ': bytes or mode differ')
        print('\t'.join([name, mode, actual_mode, oid, hashlib.sha256(data).hexdigest(), 'PASS']))
        count += 1
        if path.suffix.lower() in {'.v', '.sv', '.vhd', '.vhdl', '.xdc', '.sdc'}:
            rtl.append(name)
    if gitlinks:
        raise RuntimeError('unexpected submodule gitlinks')
    print('PASS:', count, 'tracked blobs match exact head bytes and modes')
    print('required submodule gitlinks: none; HEAD contains zero mode-160000 entries')
    print('RTL/timing-constraint files:', len(rtl))
    print('Only the four scoped files differ from base; production sources, headers, examples, build files, target gate, and workflow are byte-identical.')


if __name__ == '__main__':
    main()
