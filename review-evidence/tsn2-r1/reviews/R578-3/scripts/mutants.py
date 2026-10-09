#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Reviewer-owned file-level mutants for the round-3 mapper delta.

Usage: mutants.py <exported head tree> <scratch root> <receipt file> [--jobs N]

Each mutant copies the exported tree, replaces exactly one unique fragment
(count must be 1) in one file, and runs the full scripts/entity_selftest.py.
A mutant is CAUGHT only if every expected (named) test is reported FAIL by an
assertion and none of them is reported ERROR, and the run exits non-zero.
CAUGHT+COLL marks a catch whose mutant also makes unrelated tests ERROR
(collateral, e.g. a mutant that refuses the base fixture). Meta mutants weaken a
killer test and expect the in-repo plant control for it to FAIL.
Exit 0 iff every mutant has its expected outcome.
"""
import argparse
import concurrent.futures
import re
import shutil
import subprocess
import sys
from pathlib import Path

M = 'scripts/milan_entity.py'
S = 'scripts/entity_selftest.py'
# name: (group, file, old, new, expected FAIL tests)
MUTANTS = {
    # Item-1 reverts (five required).
    'R1-firmware-rev-not-accepted': ('item1', M, ", 'firmware_rev'}", '}',
                                     ['test_mapping_firmware_rev_zero', 'test_mapping_firmware_rev_one']),
    'R2-bool-and-float-accepted': ('item1', M, 'type(revision) is not int', 'not isinstance(revision, (int, float))',
                                   ['test_mapping_refuse_firmware_rev_boolean', 'test_mapping_refuse_firmware_rev_false',
                                    'test_mapping_refuse_firmware_rev_float']),
    'R3-negative-accepted': ('item1', M, ' or revision < 0:', ':', ['test_mapping_refuse_firmware_rev_negative']),
    'R4-firmware-version-generic': ('item1', M,
                                    "        if 'firmware_version' in source:\n            raise Invalid('milan.entity.firmware_version: remove it; the source derives this value; use entity.firmware_rev')\n",
                                    '', ['test_mapping_refuse_firmware_version']),
    'R5-unknown-key-unnamed': ('item1', M, "raise Invalid(f'milan.entity.{unknown[0]}: unknown field')",
                               "raise Invalid('milan.entity: unknown field or invalid mapping')",
                               ['test_mapping_refuse_unknown_entity_key']),
    # Further item-1 rule mutants not in the in-repo registry.
    'X1-no-default-zero': ('item1-extra', M, "source.get('firmware_rev', 0)", "source.get('firmware_rev')",
                           ['test_mapping_firmware_rev_omitted']),
    'X2-null-means-default': ('item1-extra', M, "source.get('firmware_rev', 0)", "(source.get('firmware_rev') or 0)",
                              ['test_mapping_refuse_firmware_rev_null']),
    'X3-string-accepted': ('item1-extra', M, 'if type(revision) is not int or revision < 0:',
                           'if isinstance(revision, str):\n            revision = int(revision)\n        if type(revision) is not int or revision < 0:',
                           ['test_mapping_refuse_firmware_rev_string']),
    'X4-identity-changed': ('item1-extra', M, "        raw = source['entity_model_id']\n",
                            "        if revision:\n            identity['serial_number'] = identity['serial_number'] + '-r' + str(revision)\n        raw = source['entity_model_id']\n",
                            ['test_mapping_firmware_rev_one']),
    'X5-wrong-key-named': ('item1-extra', M, "f'milan.entity.{unknown[0]}: unknown field'",
                           "f'milan.entity.{sorted(fields)[0]}: unknown field'", ['test_mapping_refuse_unknown_entity_key']),
    'X6-firmware-version-pointer-dropped': ('item1-extra', M, '; use entity.firmware_rev', '',
                                            ['test_mapping_refuse_firmware_version']),
    'X7-zero-refused': ('item1-extra', M, 'revision < 0:', 'revision < 1:',
                        ['test_mapping_firmware_rev_zero']),
    # Original eight (two required; three applied, two as variants of the registry edit).
    'O1-base-zero': ('original', M, 'return int(digits, 16)', 'return int(digits, 0)', ['test_mapping_digit_only_entity_id']),
    'O2-digit-bound-off-by-one': ('original', M, 'if len(digits) > bits // 4:', 'if len(digits) > bits // 4 + 1:',
                                  ['test_mapping_refuse_entity_id_extra_zero']),
    'O3-vendor-default-case': ('original', M, "source.get('vendor_name', 'Kebag Logic')", "source.get('vendor_name', 'Kebag logic')",
                               ['test_mapping_default_vendor_name']),
    # Meta: weaken a killer; its in-repo plant control must then fail.
    'T1-weak-firmware-version-killer': ('meta', S,
                                        "self.mapping_refuse(doc, 'milan.entity.firmware_version: remove it; the source derives this value; use entity.firmware_rev')",
                                        'self.assertRaises(entity.Invalid, self.mapped, doc)',
                                        ['test_mapper_plant_firmware_version_pointer']),
    'T2-weak-unknown-key-killer': ('meta', S, "self.mapping_refuse(doc, 'milan.entity.typo: unknown field')",
                                   'self.assertRaises(entity.Invalid, self.mapped, doc)',
                                   ['test_mapper_plant_unknown_key_generic']),
    'T3-weak-boolean-killer': ('meta', S, "('boolean', True), ('false', False), ('negative', -1)",
                               "('boolean', -2), ('false', False), ('negative', -1)", ['test_mapper_plant_firmware_rev_boolean']),
}

LINE = re.compile(r'^(test_\S+) \(.*\) \.\.\. (ok|FAIL|ERROR|skipped.*|expected failure|unexpected success)$')
SUB = re.compile(r'^(FAIL|ERROR): (test_\S+) ')


def run(tree, root, name, spec):
    group, rel, old, new, expected = spec
    work = root / name
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(tree, work / 'tree', symlinks=True)
    path = work / 'tree' / rel
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        return name, group, 'FRAGMENT-COUNT-%d' % count, [], [], expected, None
    path.write_text(text.replace(old, new))
    proc = subprocess.run([sys.executable, str(work / 'tree/scripts/entity_selftest.py'), '--work', str(work / 'build')],
                          capture_output=True, text=True, timeout=900, cwd=work / 'tree',
                          env={'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1', 'LANG': 'C.UTF-8'})
    (work / 'selftest.log').write_text(proc.stdout + proc.stderr)
    fails, errors = set(), set()
    for line in (proc.stdout + proc.stderr).splitlines():
        m = LINE.match(line)
        if m and m[2] == 'FAIL':
            fails.add(m[1])
        elif m and m[2] == 'ERROR':
            errors.add(m[1])
        s = SUB.match(line)
        if s:
            (fails if s[1] == 'FAIL' else errors).add(s[2])
    caught = proc.returncode != 0 and all(t in fails and t not in errors for t in expected)
    verdict = ('CAUGHT' if not errors else 'CAUGHT+COLL') if caught else 'NOT-CAUGHT'
    return name, group, verdict, sorted(fails), sorted(errors), expected, proc.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tree', type=Path)
    ap.add_argument('root', type=Path)
    ap.add_argument('receipt', type=Path)
    ap.add_argument('--jobs', type=int, default=16)
    a = ap.parse_args()
    a.tree, a.root = a.tree.resolve(), a.root.resolve()
    a.root.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(a.jobs, 16)) as pool:
        results = list(pool.map(lambda kv: run(a.tree, a.root, *kv), MUTANTS.items()))
    bad = 0
    out = []
    for name, group, verdict, fails, errors, expected, rc in results:
        bad += verdict == 'NOT-CAUGHT'
        out.append(f'{verdict:12} {group:12} {name}  rc={rc}\n    expected FAIL: {expected}\n    reported FAIL ({len(fails)}): {fails}\n    reported ERROR ({len(errors)}): {errors}')
    out.append(f'mutants: {len(results)}, caught: {len(results) - bad}, not caught: {bad}')
    a.receipt.write_text('\n'.join(out) + '\n')
    print('\n'.join(out))
    return int(bad != 0)


if __name__ == '__main__':
    raise SystemExit(main())
