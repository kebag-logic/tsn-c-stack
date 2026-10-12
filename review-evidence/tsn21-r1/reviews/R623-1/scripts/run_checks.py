#!/usr/bin/env python3
"""Foreground review runner; all children are joined, with bounded concurrency."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
p.add_argument('--gtest', type=Path, required=True)
p.add_argument('--phase', choices=['build', 'checks'], required=True)
a = p.parse_args()
root = a.root.resolve()
packet = Path(__file__).resolve().parents[1]
scratch = packet / 'scratch'
receipts = packet / 'receipts/local'
receipts.mkdir(parents=True, exist_ok=True)
env = {k: v for k, v in os.environ.items() if not k.startswith('GTEST_')}
env['CMAKE_PREFIX_PATH'] = str(a.gtest)
env['PKG_CONFIG_PATH'] = str(a.gtest / 'lib/pkgconfig')
env['LD_LIBRARY_PATH'] = str(scratch / 'clang18/usr/lib/x86_64-linux-gnu')
env['TSN_CLANG'] = str(scratch / 'clang18/usr/bin/clang-18')
env['TMPDIR'] = str(scratch / 'temp')
Path(env['TMPDIR']).mkdir(exist_ok=True)
gcc = scratch / 'gcc'

def run(name, argv):
    started = time.monotonic()
    with (receipts / (name + '.log')).open('w') as log:
        log.write('COMMAND ' + repr(argv) + '\n')
        log.flush()
        r = subprocess.run(argv, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=550)
    (receipts / (name + '.rc')).write_text(str(r.returncode) + '\n')
    row = {'name': name, 'rc': r.returncode, 'seconds': round(time.monotonic()-started, 2)}
    print(json.dumps(row), flush=True)
    return row

def command(name, script, extra=()):
    return run(name, ['python3', 'scripts/' + script, *extra])

def suite():
    r = run('gcc-tests', ['ctest', '--test-dir', str(gcc), '--output-on-failure', '-j1'])
    if r['rc'] == 0:
        return [r, command('coverage', 'coverage.py', [str(gcc)])]
    return [r]

def source_gates():
    return [command(name, script, extra) for name, script, extra in [
        ('comments', 'check_comments.py', ['--selftest', '--work', str(scratch/'comments')]),
        ('needles', 'needle_audit.py', ['--selftest']),
        ('port-contracts', 'check_port_contracts.py', ['--selftest']),
        ('traceability', 'traceability.py', ['--selftest', '--build', str(gcc), '--jobs', '1']),
        ('test-inventory', 'test_inventory.py', ['--build', str(gcc), '--jobs', '1'])]]

if a.phase == 'build':
    results = [run('gcc-configure', ['cmake', '-S', '.', '-B', str(gcc), '-DCMAKE_BUILD_TYPE=Debug', '-DTSN_COVERAGE=ON'])]
    if results[0]['rc'] == 0:
        results.append(run('gcc-build', ['make', '-C', str(gcc), '-j16']))
else:
    # Six mutation workers, at most eight RV32 compile workers, one source-gate
    # worker and one test worker: at most sixteen active workers in total.
    tasks = [suite, source_gates,
             lambda: [command('publish-mutations', 'mutation.py', ['--work', str(scratch/'mutations'), '--jobs', '6', '--select', 'acmp-publish'])],
             lambda: [command('rv32', 'baremetal.py', ['--work', str(scratch/'rv32'), '--jobs', '4'])]]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = [r for group in pool.map(lambda f: f(), tasks) for r in group]
(receipts / (a.phase + '.json')).write_text(json.dumps(results, indent=2) + '\n')
raise SystemExit(int(any(r['rc'] for r in results)))
