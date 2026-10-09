#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check named regression failures in disposable mapper copies."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import sys

repo, work = (Path(arg).resolve() for arg in sys.argv[1:])
work.mkdir(parents=True, exist_ok=True)
plants = [
    ('base-zero', 'return int(digits, 16)', 'return int(digits, 0)', 'test_mapping_digit_only_entity_id'),
    ('unbounded-digits', 'if len(digits) > bits // 4:', 'if False:', 'test_mapping_refuse_entity_id_extra_zero'),
    ('unquoted-accepted', 'def hex_text(value, bits, path):\n', 'def hex_text(value, bits, path):\n    if isinstance(value, int):\n        return value\n', 'test_mapping_refuse_entity_id_integer'),
    ('double-underscore', '(?:_?[0-9A-Fa-f])*', '(?:_*[0-9A-Fa-f])*', 'test_mapping_refuse_entity_id_double_underscore'),
    ('vendor-default', "source.get('vendor_name', 'Kebag Logic')", "source.get('vendor_name', 'Wrong vendor')", 'test_mapping_default_vendor_name'),
    ('group-default', "source.get('group_name', '')", "source.get('group_name', 'Wrong group')", 'test_mapping_default_group_name'),
    ('entity-default', "source.get('entity_id', 'mac-derived')", "source.get('entity_id', '1')", 'test_mapping_default_entity_id'),
    ('pin-agreement', 'if declared is not None and declared != model_id:', 'if False:', 'test_mapping_refusals'),
]
files = subprocess.check_output(['git', '-C', str(repo), 'ls-files', '-z']).decode().split('\0')

def run(plant):
    name, old, new, killer = plant
    directory = work / name
    directory.mkdir()
    for relative in filter(None, files):
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / relative, target)
    script = directory / 'scripts/milan_entity.py'
    text = script.read_text()
    assert text.count(old) == 1, name
    script.write_text(text.replace(old, new))
    result = subprocess.run([sys.executable, 'scripts/entity_selftest.py', '--work', str(directory / 'work')], cwd=directory, text=True, capture_output=True)
    (directory / 'selftest.log').write_text(result.stdout + result.stderr)
    caught = result.returncode == 1 and 'FAIL: ' + killer + ' ' in result.stderr
    return dict(plant=name, killer=killer, rc=result.returncode, status='CAUGHT' if caught else 'ESCAPED')

with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(run, plants))
(work / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps(results, indent=2))
raise SystemExit(int(any(row['status'] != 'CAUGHT' for row in results)))
