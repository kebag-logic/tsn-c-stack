#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Refuse another test-library version and require the checked package flags."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from assertion_forms import package_flags, require_version

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=16)
    args = parser.parse_args()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    require_version()
    other = work / 'other/lib/cmake/GTest'
    other.mkdir(parents=True, exist_ok=True)
    (other / 'GTestConfig.cmake').write_text('message(FATAL_ERROR "wrong package selected")\n')
    (other / 'GTestConfigVersion.cmake').write_text(
        'set(PACKAGE_VERSION "1.18.0")\nset(PACKAGE_VERSION_COMPATIBLE FALSE)\n'
        'set(PACKAGE_VERSION_EXACT FALSE)\n')
    result = subprocess.run(['cmake', '-S', str(ROOT), '-B', str(work / 'wrong-version'),
                             '-DGTest_DIR=' + str(other), '-DCMAKE_FIND_ROOT_PATH=' + str(work / 'other'),
                             '-DCMAKE_FIND_ROOT_PATH_MODE_PACKAGE=ONLY'], capture_output=True, text=True)
    (work / 'wrong-version.log').write_text(result.stdout + result.stderr)
    if result.returncode == 0 or '1.18.0' not in result.stderr or '1.14.0' not in result.stderr:
        raise RuntimeError('another package version was not refused')
    print('dependency control: only another package version available; configure refused')
    flags = {'--cflags': package_flags('--cflags'), '--libs': package_flags('--libs')}
    header = work / 'required flags.hpp'
    header.write_text('extern "C" void tsn_dependency_control();\n'
                      '__attribute__((constructor)) static void tsn_check_dependency() { tsn_dependency_control(); }\n')
    source = work / 'dependency.cpp'
    source.write_text('extern "C" void tsn_dependency_control() {}\n')
    obj = work / 'required flags.o'
    subprocess.run([os.environ.get('CXX', 'g++'), '-c', str(source), '-o', str(obj)], check=True)
    flags['--cflags'] += ['-include', str(header)]
    flags['--libs'] += [str(obj)]
    bindir = work / 'bin'
    bindir.mkdir(exist_ok=True)
    proxy = bindir / 'pkg-config'
    proxy.write_text('#!' + sys.executable + '\nimport os,sys\nflags = ' + repr(flags) +
                     '\nfor option, flags in flags.items():\n'
                     ' if option in sys.argv:\n  print(__import__("shlex").join(flags)); sys.exit(0)\n'
                     'os.execv(' + repr(shutil.which('pkg-config')) + ', ["pkg-config", *sys.argv[1:]])\n')
    proxy.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if k not in ('CPLUS_INCLUDE_PATH', 'C_INCLUDE_PATH', 'LIBRARY_PATH')}
    env['PATH'] = str(bindir) + os.pathsep + env['PATH']
    table = json.loads((ROOT / 'tests/mutations.json').read_text())
    plant = next(p['name'] for p in table if p['path'].endswith('.h'))
    campaign = work / 'campaign'
    subprocess.run([sys.executable, str(ROOT / 'scripts/mutation.py'), '--work', str(campaign),
                    '--select', plant, '--jobs', str(args.jobs)], env=env, check=True)
    results = json.loads((campaign / 'results.json').read_text())
    if not results or any(p['status'] != 'CAUGHT' for p in results):
        raise RuntimeError('package-flag campaign did not catch its plant')
    for path in [* (campaign / 'baseline').glob('*.cpp.o'), campaign / 'baseline/main.o',
                 *campaign.glob('*/*.test.o')]:
        symbols = subprocess.check_output(['nm', '-u', str(path)], text=True)
        if 'tsn_dependency_control' not in symbols:
            raise RuntimeError('checked compile flags missing from ' + path.name)
    print('dependency control: baseline and header plant use checked compile/link flags without ambient paths')


if __name__ == '__main__':
    main()
