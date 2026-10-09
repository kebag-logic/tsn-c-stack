#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Plant reviewer-chosen defects in scripts/milan_entity.py and require
scripts/entity_selftest.py to fail for each one.

Usage: probe_mapper_mutants.py <disposable tsn-c-stack clone> <work dir> [jobs]

Each plant is an exact single-occurrence text replacement. Every plant runs in
its own copy of the clone's scripts directory, so plants never overlap. The
original clone bytes are never modified. Exit 0 iff every plant is caught and
the unplanted control passes.
"""
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

clone, work = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
jobs = int(sys.argv[3]) if len(sys.argv) > 3 else 8
TARGET = 'scripts/milan_entity.py'

PLANTS = {
    'decimal-digit-only': ("    return int(digits, 16)\n",
                           "    return int(digits, 10) if digits.isdigit() else int(digits, 16)\n"),
    'accept-unquoted-int': ("    if not isinstance(value, str):\n        raise Invalid(f'{path}: quote the hexadecimal value as a YAML string')\n    match",
                            "    if type(value) is int:\n        return value\n    if not isinstance(value, str):\n        raise Invalid(f'{path}: quote the hexadecimal value as a YAML string')\n    match"),
    'repeated-underscores': ("([0-9A-Fa-f](?:_?[0-9A-Fa-f])*)", "([0-9A-Fa-f](?:_*[0-9A-Fa-f])*)"),
    'digit-bound-plus-one': ("    if len(digits) > bits // 4:\n", "    if len(digits) > bits // 4 + 1:\n"),
    'bound-ignores-leading-zeros': ("    if len(digits) > bits // 4:\n", "    if len(digits.lstrip('0')) > bits // 4:\n"),
    'prefix-required': ("r'(?:0[xX])?([0-9A-Fa-f]", "r'(?:0[xX])([0-9A-Fa-f]"),
    'vendor-default-empty': ("vendor_name=source.get('vendor_name', 'Kebag Logic')", "vendor_name=source.get('vendor_name', '')"),
    'group-default-vendor': ("group_name=source.get('group_name', '')", "group_name=source.get('group_name', 'Kebag Logic')"),
    'entity-id-required': ("entity_id=source.get('entity_id', 'mac-derived')", "entity_id=source['entity_id']"),
    'mac-dash-refused': ("[0-9A-Fa-f]{2}([:-])[0-9A-Fa-f]{2}", "[0-9A-Fa-f]{2}(:)[0-9A-Fa-f]{2}"),
    'mac-length-unchecked': ("        if len(digits) != 12:\n            raise Invalid(f'{path}: expected exactly 12 hexadecimal digits (48 bits)')\n", ""),
    'reserved-model-accepted': ("    if number in (0, (1 << 64) - 1):\n", "    if number in (0,):\n"),
    'oui-ig-accepted': ("            if oui & 0x010000:\n", "            if oui & 0:\n"),
    'oui-contradiction-ignored': ("            if oui != model_id >> 40:\n", "            if oui != oui:\n"),
    'pin-ignored-with-literal': ("        if 'model_id_pin' in source:\n", "        if 'model_id_pin' in source and declared is None:\n"),
    'literal-unchecked-under-pin': ("        declared = None if raw == 'hash-derived' else model_identity(raw, 'milan.entity.entity_model_id')\n",
                                    "        declared = None\n"),
    'capability-width-64': ("hex_text(source['entity_capabilities'], 32,", "hex_text(source['entity_capabilities'], 64,"),
    'oui-width-32': ("hex_text(source['vendor_oui'], 24,", "hex_text(source['vendor_oui'], 32,"),
    'mac-octet-case-folded-wrong': ("        digits = f'{number:012X}'\n", "        digits = f'{number:012X}'[::-1]\n"),
}

original = (clone / TARGET).read_text()
work.mkdir(parents=True, exist_ok=True)


def run(name, old, new):
    tree = work / name
    if tree.exists():
        shutil.rmtree(tree)
    shutil.copytree(clone, tree, ignore=shutil.ignore_patterns('.git', 'build*', '__pycache__'))
    text = original
    if name != 'control':
        count = original.count(old)
        if count != 1:
            return dict(plant=name, status='BAD-PLANT', occurrences=count)
        text = original.replace(old, new)
    (tree / TARGET).write_text(text)
    result = subprocess.run([sys.executable, 'scripts/entity_selftest.py', '--work', str(tree / 'build-entity')],
                            cwd=tree, capture_output=True, text=True, timeout=900)
    log = result.stdout + result.stderr
    (work / f'{name}.log').write_text(log)
    failed = sorted({line.split(' ')[1] for line in log.splitlines() if line.startswith(('FAIL: ', 'ERROR: '))})
    if name == 'control':
        status = 'PASS' if result.returncode == 0 else 'CONTROL-FAILED'
    else:
        status = 'CAUGHT' if result.returncode != 0 else 'ESCAPED'
    shutil.rmtree(tree)
    return dict(plant=name, status=status, rc=result.returncode, failing_tests=failed[:12], failing_count=len(failed))


tasks = [('control', '', '')] + [(n, o, w) for n, (o, w) in PLANTS.items()]
with ThreadPoolExecutor(max_workers=jobs) as pool:
    results = list(pool.map(lambda t: run(*t), tasks))
for r in results:
    print(json.dumps(r))
ok = results[0]['status'] == 'PASS' and all(r['status'] == 'CAUGHT' for r in results[1:])
print(f'plants: {len(results) - 1}, caught: {sum(r["status"] == "CAUGHT" for r in results[1:])}, control: {results[0]["status"]}')
sys.exit(0 if ok else 1)
