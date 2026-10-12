#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Plant regressions in the ACMP cache gate and require its in-memory selftest (or check) to refuse each.
usage: gate_mutants.py <pristine-tree> <work>"""
import json, shutil, subprocess, sys
from pathlib import Path
src, work = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
MUTANTS = [
 ('identity-compares-literal', 'scripts/check_acmp_cache.py',
  "        matches = [message.identity for message", "        matches = [message.literal for message"),
 ('identity-drops-column', 'scripts/assertion_messages.py',
  "identity = (owner, path, line, column)", "identity = (owner, path, line, 0)"),
 ('identity-drops-line-and-column', 'scripts/assertion_messages.py',
  "identity = (owner, path, line, column)", "identity = (owner, path, 0, 0)"),
 ('identity-drops-owner', 'scripts/assertion_messages.py',
  "identity = (owner, path, line, column)", "identity = ('', path, line, column)"),
 ('identity-per-literal', 'scripts/assertion_messages.py',
  "messages.append(Message(value, identity))", "messages.append(Message(value, identity + (at,)))"),
 ('helper-owner-lost', 'scripts/assertion_messages.py',
  "messages += collect(owner, helpers[word][0], visited)", "messages += collect(word, helpers[word][0], visited)"),
 ('ownership-check-disabled', 'scripts/check_acmp_cache.py',
  "            if matches[0] in owners:", "            if False:"),
 ('owners-never-recorded', 'scripts/check_acmp_cache.py',
  "            owners.add(matches[0])", "            pass"),
]
HARNESS = r'''
import json, sys
sys.path.insert(0, 'scripts')
import check_acmp_cache as c
from pathlib import Path
h = Path('include/acmp.h').read_text(); s = Path('src/acmp.c').read_text()
m = json.loads(Path('tests/mutations.json').read_text())
msgs = c.inventory(Path('tests/test_acmp.cpp').read_text(), 'tests/test_acmp.cpp')
e = c.check(h, s, m, msgs)
if e: print('check refused head:', e); sys.exit(3)
c.selftest(h, s, m, msgs)
'''
rows, bad = [], 0
for name, path, old, new in MUTANTS:
    t = work / name
    shutil.rmtree(t, ignore_errors=True)
    shutil.copytree(src, t, ignore=shutil.ignore_patterns('__pycache__', 'build*'))
    f = t / path
    text = f.read_text()
    if text.count(old) != 1:
        rows.append(dict(mutant=name, status='NOT-APPLIED')); bad += 1; continue
    f.write_text(text.replace(old, new))
    r = subprocess.run([sys.executable, '-c', HARNESS], cwd=t, capture_output=True, text=True,
                       env={'PATH': __import__('os').environ['PATH'], 'PYTHONDONTWRITEBYTECODE': '1'})
    status = 'REFUSED' if r.returncode != 0 else 'ESCAPED'
    bad += status != 'REFUSED'
    last = (r.stdout + r.stderr).strip().splitlines()[-1:] or ['']
    rows.append(dict(mutant=name, rc=r.returncode, status=status, last=last[0][:200]))
    print(f'{status} {name} rc={r.returncode} :: {last[0][:160]}')
print(json.dumps(dict(mutants=len(rows), not_refused=bad)))
sys.exit(1 if bad else 0)
