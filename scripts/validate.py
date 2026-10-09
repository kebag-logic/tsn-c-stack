#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Run the full standalone validation kit and keep each command's exit status."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=Path('build-validation'))
    parser.add_argument('--jobs', type=int, default=16)
    parser.add_argument('--graphs', action='store_true', help='Require and render Mermaid diagrams')
    args = parser.parse_args()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    (work / 'temp').mkdir(exist_ok=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith('GTEST_')}
    env.update(TMPDIR=str(work / 'temp'), ASAN_OPTIONS='detect_leaks=1:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1')
    python = sys.executable
    def command(name, argv):
        with (work / (name + '.log')).open('w') as log:
            result = subprocess.run(argv, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        (work / (name + '.rc')).write_text(str(result.returncode) + '\n')
        print(f'{name}: rc {result.returncode}', flush=True)
        return {'gate': name, 'rc': result.returncode}
    def build(kind, cc, cxx, options):
        directory = work / kind
        results = [command(kind + '-configure', ['cmake', '-S', str(ROOT), '-B', str(directory), '-DCMAKE_BUILD_TYPE=Debug', '-DCMAKE_C_COMPILER=' + cc, '-DCMAKE_CXX_COMPILER=' + cxx, *options])]
        if results[-1]['rc'] == 0:
            results.append(command(kind + '-build', ['cmake', '--build', str(directory), '-j' + str(args.jobs)]))
        if results[-1]['rc'] == 0:
            # Coverage must describe this run, including removals of test cases.
            for path in directory.rglob('*.gcda'):
                path.unlink()
            results.append(command(kind + '-test', ['ctest', '--test-dir', str(directory), '--output-on-failure', '-j' + str(args.jobs)]))
        if kind == 'gcc' and results[-1]['rc'] == 0:
            results.append(command('coverage', [python, 'scripts/coverage.py', str(directory)]))
        return results
    tasks = [lambda: build('gcc', 'gcc', 'g++', ['-DTSN_COVERAGE=ON']),
             lambda: build('clang-sanitizers', 'clang', 'clang++', ['-DTSN_SANITIZERS=ON']),
             lambda: [command('mutation', [python, 'scripts/mutation.py', '--work', str(work / 'mutations'), '--jobs', str(args.jobs)])],
             lambda: [command('static-analysis', [python, 'scripts/static_analysis.py'])],
             lambda: [command('mutation-controls', [python, 'scripts/mutation_selftest.py', '--work', str(work / 'mutation-controls'), '--jobs', str(args.jobs)])]]
    results = []
    # Fail fast on source/metadata gates before compiling independent configurations.
    for name, script, switches in (
        ('boundary', 'check_boundary.py', ['--selftest', '--work', str(work / 'boundary'), '--jobs', str(args.jobs)]),
        ('needles', 'needle_audit.py', ['--selftest']),
        ('comments', 'check_comments.py', ['--selftest', '--work', str(work / 'comment-controls')]),
        ('conditionals', 'check_conditionals.py', ['--selftest', '--work', str(work / 'conditionals'), '--jobs', str(args.jobs)]),
        ('port-contracts', 'check_port_contracts.py', ['--selftest']),
        ('registration-controls', 'registration_selftest.py', ['--work', str(work / 'registration-controls')]),
        ('license', 'check_license.py', ['--selftest']),
        ('traceability', 'traceability.py', ['--selftest', '--build', str(work / 'registration'), '--jobs', str(args.jobs)]),
        ('test-inventory', 'test_inventory.py', ['--build', str(work / 'registration'), '--jobs', str(args.jobs)]),
        ('coverage-controls', 'coverage_selftest.py', []),
        ('privacy', 'check_privacy.py', [])):
        results.append(command(name, [python, 'scripts/' + script, *switches]))
    if not any(r['rc'] for r in results):
        with ThreadPoolExecutor(max_workers=4) as pool:
            for group in pool.map(lambda task: task(), tasks):
                results += group
        if args.graphs:
            results.append(command('graphs', [python, 'scripts/render_graphs.py', '--output', str(work / 'graphs')]))
    (work / 'gates.json').write_text(json.dumps(results, indent=2) + '\n')
    return int(any(r['rc'] != 0 for r in results))

if __name__ == '__main__':
    raise SystemExit(main())
