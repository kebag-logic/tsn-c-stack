#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Reviewer-written mapper plants, applied to disposable copies of the exact head.

Usage: python3 -I probe_plants.py CLONE WORK [--jobs N]

Each plant edits scripts/milan_entity.py in its own `git archive` copy (one unique
fragment, or a whole-file revert), then runs the named killer test with unittest.
A catch requires: the killer passes on the unplanted copy, the killer reports
FAIL (an AssertionError) on the planted copy, and no ERROR or skip is reported.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import re
import subprocess
import sys

FW = "'entity_capabilities', 'firmware_rev'}"
PLANTS = {
    # item-1 reverts (firmware_rev / firmware_version / unknown-key naming)
    'I1-fw-rev-key-dropped': ([(FW, "'entity_capabilities'}")], ['test_mapping_firmware_rev_zero', 'test_mapping_firmware_rev_one']),
    'I2-fw-rev-bool-accepted': ([('type(revision) is not int', 'type(revision) not in (int, bool)')], ['test_mapping_refuse_firmware_rev_boolean', 'test_mapping_refuse_firmware_rev_false']),
    'I3-fw-rev-negative-accepted': ([('revision < 0', 'revision < -1')], ['test_mapping_refuse_firmware_rev_negative']),
    'I4-fw-version-pointer-removed': ([("        if 'firmware_version' in source:\n            raise Invalid('milan.entity.firmware_version: remove it; the source derives this value; use entity.firmware_rev')\n", '')],
                                      ['test_mapping_refuse_firmware_version']),
    'I5-unknown-key-unnamed': ([("f'milan.entity.{unknown[0]}: unknown field'", "'milan.entity: unknown field'")], ['test_mapping_refuse_unknown_entity_key']),
    'I6-fw-rev-default-required': ([("source.get('firmware_rev', 0)", "source['firmware_rev']")], ['test_mapping_firmware_rev_omitted']),
    'I7-fw-rev-string-accepted': ([('type(revision) is not int or revision < 0', 'not isinstance(revision, (int, str)) or int(revision) < 0')], ['test_mapping_refuse_firmware_rev_string']),
    # The omitted form is not a killer here: the prior mapper also accepted an omitted key.
    'I8-whole-item1-revert': ('REVERT', ['test_mapping_firmware_rev_zero', 'test_mapping_firmware_rev_one',
                                         'test_mapping_refuse_firmware_version', 'test_mapping_refuse_unknown_entity_key']),
    # two-plus of the original eight, in reviewer-chosen forms
    'O1-digit-only-decimal': ([('return int(digits, 16)', 'return int(digits, 10 if digits.isdigit() else 16)')], ['test_mapping_digit_only_entity_id']),
    'O2-vendor-default-changed': ([("source.get('vendor_name', 'Kebag Logic')", "source.get('vendor_name', 'Kebag Logic ')")], ['test_mapping_default_vendor_name']),
    'O3-double-underscore': ([('(?:_?[0-9A-Fa-f])*', '(?:_{0,2}[0-9A-Fa-f])*')], ['test_mapping_refuse_entity_id_double_underscore']),
}
PRIOR = '6f4ecc9036f9ac2694b05a749cc9105d9c15c05f'


def sh(*args, **kw):
    return subprocess.run(args, check=True, capture_output=True, **kw)


def copy_head(clone, target):
    target.mkdir(parents=True)
    archive = subprocess.run(['git', '-C', str(clone), 'archive', 'HEAD'], check=True, capture_output=True).stdout
    subprocess.run(['tar', '-x', '-C', str(target)], input=archive, check=True)


def run_test(tree, name, tmp):
    env = dict(os.environ, TMPDIR=str(tmp), PYTHONDONTWRITEBYTECODE='1')
    r = subprocess.run([sys.executable, '-m', 'unittest', '-v', 'entity_selftest.EntityTests.' + name],
                       cwd=tree / 'scripts', env=env, capture_output=True, text=True, timeout=600)
    out = r.stderr + r.stdout
    status = 'ok' if re.search(rf'^{name} .*\.\.\. ok$', out, re.M) else \
             'FAIL' if f'FAIL: {name} ' in out else 'ERROR' if 'ERROR:' in out else 'other'
    return status, r.returncode, out


def one(clone, work, label, spec):
    tree = work / label
    copy_head(clone, tree)
    tmp = work / (label + '.tmp')
    tmp.mkdir()
    edits, killers = spec
    lines = [f'== {label}']
    control = [run_test(tree, k, tmp) for k in killers]
    target = tree / 'scripts/milan_entity.py'
    text = target.read_text()
    if edits == 'REVERT':
        new = subprocess.run(['git', '-C', str(clone), 'show', PRIOR + ':scripts/milan_entity.py'], check=True, capture_output=True, text=True).stdout
    else:
        new = text
        for old, rep in edits:
            assert new.count(old) == 1, (label, old, new.count(old))
            new = new.replace(old, rep)
    assert new != text
    target.write_text(new)
    planted = [run_test(tree, k, tmp) for k in killers]
    ok = True
    for k, c, p in zip(killers, control, planted):
        caught = c[0] == 'ok' and p[0] == 'FAIL' and 'AssertionError' in p[2] and 'ERROR:' not in p[2] and 'skipped' not in p[2]
        ok &= caught
        reason = [ln for ln in p[2].splitlines() if ln.startswith('AssertionError')][:1]
        lines.append(f"  {'CAUGHT' if caught else 'MISSED'} {k}: control={c[0]} planted={p[0]} rc={p[1]} {reason[0][:160] if reason else ''}")
    lines.insert(1, f"  RESULT {'CAUGHT' if ok else 'NOT-CAUGHT'}")
    return ok, '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clone', type=Path)
    ap.add_argument('work', type=Path)
    ap.add_argument('--jobs', type=int, default=8)
    a = ap.parse_args()
    a.work.mkdir(parents=True, exist_ok=False)
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        results = list(pool.map(lambda item: one(a.clone.resolve(), a.work.resolve(), *item), PLANTS.items()))
    for _, text in results:
        print(text)
    caught = sum(ok for ok, _ in results)
    print(f'{caught}/{len(results)} reviewer plants caught by their named tests')
    return 0 if caught == len(results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
