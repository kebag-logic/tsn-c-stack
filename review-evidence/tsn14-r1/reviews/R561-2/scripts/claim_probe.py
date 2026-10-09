#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Plant one disposable defect in an exported copy of a commit and list every failing GoogleTest.

Usage: claim_probe.py REPO COMMIT WORKDIR NAME PATH OLD NEW
OLD must occur exactly once in PATH. The repository itself is never modified.
Requires cmake, a C/C++ compiler and GoogleTest 1.14.0 discoverable by CMake.
Writes WORKDIR/NAME/result.json with the build rc and the failing test names.
"""
import json
import subprocess
import sys
from pathlib import Path

repo, commit, work, name, path, old, new = sys.argv[1:8]
root = Path(work).resolve() / name
src = root / 'src-tree'
build = root / 'build'
src.mkdir(parents=True, exist_ok=True)
archive = subprocess.run(['git', '-C', repo, 'archive', commit], check=True, stdout=subprocess.PIPE).stdout
subprocess.run(['tar', '-x', '-C', str(src)], input=archive, check=True)
target = src / path
text = target.read_text()
if text.count(old) != 1:
    raise SystemExit(f'{name}: OLD occurs {text.count(old)} times in {path}')
if new != '__BASELINE__':
    target.write_text(text.replace(old, new))
log = open(root / 'build.log', 'w')
rc = subprocess.run(['cmake', '-S', str(src), '-B', str(build), '-DCMAKE_BUILD_TYPE=Debug'], stdout=log, stderr=subprocess.STDOUT).returncode
if rc == 0:
    rc = subprocess.run(['cmake', '--build', str(build), '-j4'], stdout=log, stderr=subprocess.STDOUT).returncode
failed = []
binaries = ['adp_tests', 'acmp_tests', 'maap_tests', 'port_tests', 'adp_release', 'adp_debug', 'maap_debug']
if rc == 0:
    for b in binaries:
        out = root / (b + '.json')
        with open(root / (b + '.log'), 'w') as blog:
            subprocess.run([str(build / b), '--gtest_output=json:' + str(out)], stdout=blog, stderr=subprocess.STDOUT)
        if not out.exists():
            failed.append(b + ':no-report')
            continue
        for suite in json.loads(out.read_text())['testsuites']:
            for case in suite['testsuite']:
                if case.get('failures'):
                    failed.append(suite['name'] + '.' + case['name'])
result = {'probe': name, 'path': path, 'old': old, 'new': new, 'build_rc': rc, 'failed': sorted(failed)}
(root / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
