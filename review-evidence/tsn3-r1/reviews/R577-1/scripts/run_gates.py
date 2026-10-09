#!/usr/bin/env python3
"""Run independent source gates concurrently; keep all children joined."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--dependencies', type=Path, required=True)
p.add_argument('--compiler-bin', type=Path, required=True)
p.add_argument('--jobs', type=int, default=2)
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
source = a.source.resolve()
env = os.environ.copy()
env.update(PKG_CONFIG_PATH=str(a.dependencies / 'lib/pkgconfig'),
           CMAKE_PREFIX_PATH=str(a.dependencies),
           LD_LIBRARY_PATH=str(a.dependencies / 'lib'),
           PATH=str(a.compiler_bin) + os.pathsep + env['PATH'],
           PYTHONDONTWRITEBYTECODE='1')
for key in ('CPATH', 'CPLUS_INCLUDE_PATH', 'C_INCLUDE_PATH', 'LIBRARY_PATH'):
    env.pop(key, None)
def run(name, argv):
    start = time.time()
    with (root / 'scratch' / (name + '.raw.log')).open('w') as out:
        result = subprocess.run(argv, cwd=source, env=env, stdout=out, stderr=subprocess.STDOUT)
    (root / 'receipts' / (name + '.rc')).write_text(str(result.returncode) + '\n')
    record = dict(gate=name, rc=result.returncode, elapsed_seconds=round(time.time()-start, 3))
    print(json.dumps(record), flush=True)
    return record
tasks = [
    ('validation', ['python3', 'scripts/validate.py', '--work', str(root / 'scratch/validation'), '--jobs', str(a.jobs), '--graphs']),
    ('rv32', ['python3', 'scripts/baremetal.py', '--work', str(root / 'scratch/rv32'), '--jobs', str(a.jobs)]),
]
with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(lambda t: run(*t), tasks))
(root / 'receipts/gate-run.json').write_text(json.dumps(results, indent=2) + '\n')
raise SystemExit(int(any(r['rc'] for r in results)))
