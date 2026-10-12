#!/usr/bin/env python3
"""Run bounded, foreground review checks; all disposable output is in scratch."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import time

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--phase', choices=('build', 'checks'), required=True)
a = p.parse_args()
packet = Path(__file__).resolve().parents[1]
source = a.source.resolve()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
env = {k: v for k, v in env.items() if not k.startswith('GTEST_')}
results = []

def run(label, command, cwd):
    log = packet / 'receipts' / (label + '.log')
    start = time.monotonic()
    with log.open('w') as out:
        out.write('COMMAND ' + repr(command) + '\n'); out.flush()
        rc = subprocess.run(command, cwd=cwd, env=env, stdout=out,
                            stderr=subprocess.STDOUT, timeout=540).returncode
    (packet / 'receipts' / (label + '.rc')).write_text(str(rc) + '\n')
    result = dict(label=label, rc=rc, seconds=round(time.monotonic()-start, 2))
    results.append(result)
    print(json.dumps(result), flush=True)
    return rc

targets = [('port', source), ('integration', packet/'scratch/integration')]
if a.phase == 'build':
    for name, root in targets:
        build = packet/'scratch'/('build-'+name)
        if run(name+'-configure', ['cmake','-S',str(root),'-B',str(build),
                                  '-DCMAKE_BUILD_TYPE=Debug','-DTSN_COVERAGE=ON'],root):
            continue
        run(name+'-build', ['make','-C',str(build),'-j16'],root)
else:
    def hosted():
        for name,root in targets:
            build=packet/'scratch'/('build-'+name)
            run(name+'-hosted', ['ctest','--test-dir',str(build),'--output-on-failure','-j4'],root)
            run(name+'-coverage', [sys.executable,'scripts/coverage.py',str(build)],root)
            run(name+'-needles', [sys.executable,'scripts/needle_audit.py','--selftest'],root)
            run(name+'-traceability', [sys.executable,'scripts/traceability.py','--selftest','--build',str(build),'--jobs','4'],root)
            run(name+'-test-inventory', [sys.executable,'scripts/test_inventory.py','--build',str(build),'--jobs','4'],root)
            run(name+'-port-contracts', [sys.executable,'scripts/check_port_contracts.py','--selftest'],root)
    def cache():
        for name,root in targets:
            run(name+'-cache-controls', [sys.executable,'scripts/check_acmp_cache.py','--selftest','--work',str(packet/'scratch'/('cache-'+name)),'--jobs','4'],root)
    def mutation():
        for name,root in targets:
            run(name+'-publication-mutations', [sys.executable,'scripts/mutation.py','--work',str(packet/'scratch'/('mutations-'+name)),'--jobs','4','--select','acmp-publish-'],root)
    def rv32():
        for name,root in targets:
            # The driver builds Debug and Release concurrently: two jobs each.
            run(name+'-rv32', [sys.executable,'scripts/baremetal.py','--work',str(packet/'scratch'/('rv32-'+name)),'--jobs','2'],root)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(f) for f in (hosted,cache,mutation,rv32)]
        for f in futures: f.result()
(packet/'receipts'/('focused-'+a.phase+'.json')).write_text(json.dumps(results,indent=2)+'\n')
sys.exit(any(r['rc'] for r in results))
