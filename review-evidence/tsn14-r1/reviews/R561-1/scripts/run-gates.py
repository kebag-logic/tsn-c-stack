#!/usr/bin/env python3
"""Run both target gates concurrently; remain attached until both exit."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root, packet = (Path(p).resolve() for p in sys.argv[1:3])
scratch = packet / 'scratch'
bindir = scratch / 'bin'
bindir.mkdir(exist_ok=True)
wrapper = bindir / 'clang++'
wrapper.write_text('''#!/usr/bin/env python3
import os
from pathlib import Path
import sys
scratch = Path(__file__).resolve().parent.parent
compiler = scratch / 'sdk/usr/lib/llvm-18/bin/clang++'
args = ['-nostdinc++']
for path in ['usr/include/c++/13', 'usr/include/x86_64-linux-gnu/c++/13', 'usr/include/c++/13/backward']:
    args += ['-isystem', str(scratch / 'sdk' / path)]
os.execv(str(compiler), [str(compiler), *args, *sys.argv[1:]])
''')
wrapper.chmod(0o755)
env = dict(os.environ)
for key in ('CPATH', 'CPLUS_INCLUDE_PATH', 'C_INCLUDE_PATH', 'LIBRARY_PATH'):
    env.pop(key, None)
env['PATH'] = str(bindir) + os.pathsep + str(scratch / 'sdk/usr/lib/llvm-18/bin') + os.pathsep + env['PATH']
env['LD_LIBRARY_PATH'] = str(scratch / 'sdk/usr/lib/x86_64-linux-gnu')
env['TSN_CLANG'] = str(scratch / 'sdk/usr/lib/llvm-18/bin/clang-18')
env['CMAKE_PREFIX_PATH'] = str(scratch / 'gtest')
env['PKG_CONFIG_PATH'] = str(scratch / 'gtest/lib/pkgconfig')
for cmd in (['clang', '--version'], ['pkg-config', '--modversion', 'gtest', 'gmock'], ['riscv64-elf-gcc', '--version']):
    print(subprocess.check_output(cmd, env=env, text=True), flush=True)

def run(item):
    name, script, extra = item
    command = [sys.executable, 'scripts/' + script, '--work', str(scratch / name), '--jobs', '4', *extra]
    start = time.monotonic()
    with (scratch / (name + '.log')).open('w') as log:
        completed = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
    (scratch / (name + '.rc')).write_text(str(completed.returncode) + '\n')
    result = {'gate': name, 'rc': completed.returncode, 'seconds': round(time.monotonic() - start, 2)}
    print(json.dumps(result), flush=True)
    return result

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(run, [('validate-compatible', 'validate.py', ['--graphs']), ('baremetal-compatible', 'baremetal.py', [])]))
(packet / 'receipts/target-runs.json').write_text(json.dumps(results, indent=2) + '\n')
raise SystemExit(int(any(r['rc'] for r in results)))
