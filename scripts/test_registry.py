# SPDX-License-Identifier: MIT
"""Read executable test registration and reconcile it with source declarations."""
import json
import os
from pathlib import Path
import subprocess


def environment():
    return {k: v for k, v in os.environ.items() if not k.startswith('GTEST_')}


def registered(binary, filters=()):
    command = [str(binary), '--gtest_list_tests']
    if filters:
        command.append('--gtest_filter=' + ':'.join(filters))
    result = subprocess.run(command, text=True, capture_output=True,
                            env=environment(), timeout=120, check=True)
    names = []
    suite = ''
    for line in result.stdout.splitlines():
        value = line.split('#', 1)[0].strip()
        if not value:
            continue
        if not line[0].isspace() and value.endswith('.'):
            suite = value
        elif line.startswith('  ') and suite:
            names.append(suite + value)
    if not names or len(set(names)) != len(names):
        raise RuntimeError('empty or duplicate executable registration')
    return names


def canonical(name):
    suite, case = name.split('.', 1)
    return suite.split('/')[-1] + '.' + case.split('/')[0]


def reconcile(rows, names):
    declared = {row[0] for row in rows}
    executed = {canonical(name) for name in names}
    return ['registration mismatch: ' + name for name in sorted(declared ^ executed)]


def read_build(root, build, jobs=16):
    build = Path(build).resolve()
    subprocess.run(['cmake', '-S', str(root), '-B', str(build), '-DTSN_TESTS=ON'],
                   check=True, env=environment())
    subprocess.run(['cmake', '--build', str(build), '-j' + str(jobs)],
                   check=True, env=environment())
    listing = subprocess.check_output(['ctest', '--test-dir', str(build),
                                       '--show-only=json-v1'], text=True,
                                      env=environment())
    tests = json.loads(listing)['tests']
    if not tests:
        raise RuntimeError('no test binaries registered with CTest')
    names = []
    for test in tests:
        names += registered(Path(test['command'][0]))
    print(f'registration: {len(tests)} binaries; {len(names)} instances')
    return names
