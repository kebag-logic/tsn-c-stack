#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Meta-probe of the registered mapper plant controls in scripts/entity_selftest.py.

Usage: python3 -I probe_registry.py CLONE WORK

Each case edits one MAPPER_PLANTS entry in a disposable `git archive` copy and
runs only that registry test. The registry must report FAIL (not ok) when the
plant crashes the killer, when the plant is semantically inert, and when the
fragment is ambiguous. Exit 0 only if all three are refused.
"""
import os
from pathlib import Path
import re
import subprocess
import sys

clone, work = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
OLD = "    'firmware-rev-negative': (' or revision < 0:', ':', 'test_mapping_refuse_firmware_rev_negative'),\n"
CASES = {
    'M1-plant-crashes-killer': OLD.replace("':', 'test", "' or 1 // 0:', 'test"),
    'M2-plant-inert': OLD.replace("':', 'test", "' or revision < 0 :', 'test"),
    'M3-fragment-ambiguous': OLD.replace("(' or revision < 0:', ':'", "('revision', 'rev'"),
}
ok = True
for label, new in CASES.items():
    tree = work / label
    tree.mkdir(parents=True)
    archive = subprocess.run(['git', '-C', str(clone), 'archive', 'HEAD'], check=True, capture_output=True).stdout
    subprocess.run(['tar', '-x', '-C', str(tree)], input=archive, check=True)
    path = tree / 'scripts/entity_selftest.py'
    text = path.read_text()
    assert text.count(OLD) == 1
    path.write_text(text.replace(OLD, new))
    name = 'test_mapper_plant_firmware_rev_negative'
    r = subprocess.run([sys.executable, '-m', 'unittest', '-v', 'entity_selftest.EntityTests.' + name], cwd=tree / 'scripts',
                       env=dict(os.environ, TMPDIR=str(tree), PYTHONDONTWRITEBYTECODE='1'), capture_output=True, text=True, timeout=600)
    out = r.stderr + r.stdout
    refused = r.returncode != 0 and f'FAIL: {name} ' in out
    ok &= refused
    reason = [ln for ln in out.splitlines() if ln.startswith('AssertionError')][:1]
    print(f"{'REFUSED' if refused else 'ACCEPTED'} {label}: rc={r.returncode} {reason[0][:200] if reason else ''}")
print('registry meta-probe:', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
