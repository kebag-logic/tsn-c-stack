#!/usr/bin/env python3
"""Run the two required gates concurrently while retaining every return code."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('checkout', type=Path)
p.add_argument('packet', type=Path)
p.add_argument('--dependency-prefix', type=Path, required=True)
p.add_argument('--lexer-bin', type=Path, required=True)
p.add_argument('--jobs', type=int, default=3)
p.add_argument('--driver-bin', type=Path)
p.add_argument('--work-name', default='gates')
a = p.parse_args()
root, packet = a.checkout.resolve(), a.packet.resolve()
env = {k: v for k, v in os.environ.items() if not k.startswith('GTEST_') and k not in
       ('CPATH', 'CPLUS_INCLUDE_PATH', 'C_INCLUDE_PATH', 'LIBRARY_PATH')}
env.update(PKG_CONFIG_PATH=str(a.dependency_prefix / 'lib/pkgconfig'),
           CMAKE_PREFIX_PATH=str(a.dependency_prefix),
           LD_LIBRARY_PATH=str(a.dependency_prefix / 'lib'),
           PATH=str(a.lexer_bin) + os.pathsep + env['PATH'])
if a.driver_bin:
    env['PATH'] = str(a.lexer_bin) + os.pathsep + str(a.driver_bin) + os.pathsep + os.environ['PATH']
work = packet / 'scratch' / a.work_name
work.mkdir(parents=True, exist_ok=True)
def run(item):
    name, command = item
    started = time.time()
    with (work / (name + '.log')).open('w') as f:
        rc = subprocess.run(command, cwd=root, env=env, stdout=f,
                            stderr=subprocess.STDOUT, timeout=1800).returncode
    (work / (name + '.rc')).write_text(str(rc) + '\n')
    print(name, 'rc', rc, flush=True)
    return {'name': name, 'rc': rc, 'seconds': round(time.time() - started, 3)}
tasks = [
    ('validate', ['python3', 'scripts/validate.py', '--graphs', '--jobs', str(a.jobs),
                  '--work', str(work / 'linux')]),
    ('baremetal', ['python3', 'scripts/baremetal.py', '--jobs', '2',
                   '--work', str(work / 'rv32')]),
]
with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(run, tasks))
(work / 'summary.json').write_text(json.dumps(results, indent=2) + '\n')
raise SystemExit(any(x['rc'] for x in results))
