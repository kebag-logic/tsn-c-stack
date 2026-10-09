#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Differential probe: pinned source entity loader versus the tsn-c-stack mapper.

Usage: python3 -I probe_differential.py TSN_CHECKOUT SOURCE_DIR

SOURCE_DIR holds, fetched at the pinned source revision:
  endstation_builder.py, aem_descriptors.py, milan_csr.sv,
  endstation_ax7101_1x1_tdm8.yaml
The source functions are extracted by AST and executed unchanged; only
ROOT-relative file access (RTL version path) is redirected to SOURCE_DIR and
_verify_entity_capabilities is replaced by a stub that fails if exercised.
Exit 0 only if every expectation holds.
"""
import ast
import copy
import re
import sys
from pathlib import Path
from typing import Any

import yaml

tsn, src = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
sys.path.insert(0, str(tsn / 'scripts'))
import entity_yaml  # noqa: E402
import milan_entity  # noqa: E402


def extract(path, names):
    tree = ast.parse(path.read_text())
    keep = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names:
            keep.append(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Name) and t.id in names for t in targets):
                keep.append(node)
    found = {getattr(n, 'name', None) or (n.targets[0].id if isinstance(n, ast.Assign) else n.target.id) for n in keep}
    missing = set(names) - found
    assert not missing, (path, missing)
    return ast.Module(body=keep, type_ignores=[])


aem = {'re': re, 'Path': Path, 'MILAN_CSR_SV': src / 'milan_csr.sv'}
exec(compile(extract(src / 'aem_descriptors.py', {'_VERSION_RE', 'rtl_version', 'firmware_version_string'}), 'aem_descriptors.py', 'exec'), aem)

ns = {'re': re, 'Any': Any, 'sys': sys}
exec(compile(extract(src / 'endstation_builder.py', {
    'ConfigError', '_req', 'HEX_TEXT', '_hex_text', 'EUI64_MAX', '_eui64', '_fmt64', 'AEM_STRING_BYTES',
    '_aem_string', '_declared_uint', '_load_entity'}), 'endstation_builder.py', 'exec'), ns)
ns['rtl_firmware_version'] = lambda rev=0: aem['firmware_version_string'](rev)


def no_caps(ent):
    assert 'entity_capabilities' not in ent, 'stub exercised'


ns['_verify_entity_capabilities'] = no_caps
ConfigError = ns['ConfigError']

fixture = __import__('json').loads((tsn / 'configs/compat/ax7101.json').read_text())
real = yaml.safe_load((src / 'endstation_ax7101_1x1_tdm8.yaml').read_text())
golden = entity_yaml.load(tsn / 'configs/ax7101.yaml')
adp = fixture['expected_adp']
MID, CAPS = adp['entity_model_id'], adp['entity_capabilities']
print('rtl firmware_version(0) =', aem['firmware_version_string'](0))


def source(doc):
    try:
        return 'accept', ns['_load_entity'](doc, 'probe.yaml')
    except ConfigError as error:
        return 'refuse', str(error)


def mapper(doc):
    try:
        return 'accept', milan_entity.project(doc, MID, CAPS)
    except entity_yaml.Invalid as error:
        return 'refuse', str(error)
    except Exception as error:  # a crash is a failure, never a refusal
        return 'crash', f'{type(error).__name__}: {error}'


results = []


def case(label, doc, want_source, want_mapper, message=None, identity_unchanged=None):
    s, m = source(copy.deepcopy(doc)), mapper(copy.deepcopy(doc))
    ok = s[0] == want_source and m[0] == want_mapper
    if message is not None:
        ok = ok and m[0] == 'refuse' and m[1] == message
    if identity_unchanged:
        ok = ok and m[0] == 'accept' and m[1] == golden
    results.append(ok)
    detail_s = s[1] if s[0] != 'accept' else 'firmware_version=' + repr(s[1]['firmware_version'])
    detail_m = m[1] if m[0] != 'accept' else ('identity unchanged' if m[1] == golden else 'MAPPED DIFFERS FROM GOLDEN')
    print(f"{'PASS' if ok else 'FAIL'} {label}: source={s[0]} ({detail_s}) mapper={m[0]} ({detail_m})")


def with_entity(base, **changes):
    doc = copy.deepcopy(base)
    for key, value in changes.items():
        doc['entity'][key] = value
    return doc


def from_text(base, line):
    """Insert one YAML line into the entity section and parse with each loader."""
    text = yaml.safe_dump(base, sort_keys=False).replace('entity:\n', 'entity:\n  ' + line + '\n', 1)
    return yaml.safe_load(text), entity_yaml.Loader, text


assert 'firmware_rev' not in fixture['input']['entity'] and 'firmware_rev' not in real['entity']
assert fixture['input']['entity'] == real['entity'], 'fixture entity differs from pinned source YAML'

base = fixture['input']
case('E1 firmware_rev omitted', base, 'accept', 'accept', identity_unchanged=True)
case('E2 firmware_rev: 1', with_entity(base, firmware_rev=1), 'accept', 'accept', identity_unchanged=True)
case('E3 firmware_version present', with_entity(base, firmware_version='1.22.0'), 'refuse', 'refuse',
     'milan.entity.firmware_version: remove it; the source derives this value; use entity.firmware_rev')
for label, value in (('0', 0), ('7', 7), ('2**64', 2 ** 64), ('58 digits', 10 ** 57)):
    case('E2b firmware_rev: ' + label, with_entity(base, firmware_rev=value), 'accept', 'accept', identity_unchanged=True)
for label, value in (('true', True), ('false', False), ('-1', -1), ("'1'", '1'), ('1.0', 1.0), ('null', None), ('[]', [])):
    case('E4 firmware_rev: ' + label, with_entity(base, firmware_rev=value), 'refuse', 'refuse',
         'milan.entity.firmware_rev: expected a non-negative integer')
case('E5 firmware_version and typo', with_entity(base, firmware_version='x', typo=1), 'refuse', 'refuse',
     'milan.entity.firmware_version: remove it; the source derives this value; use entity.firmware_rev')
case('E6 unknown key typo', with_entity(base, typo=1), 'accept', 'refuse', 'milan.entity.typo: unknown field')
case('E6b two unknown keys', with_entity(base, zz=1, aa=2), 'accept', 'refuse', 'milan.entity.aa: unknown field')
case('E7 real pinned AX7101 YAML', real, 'accept', 'accept', identity_unchanged=True)

# YAML spellings: both loaders must resolve the same scalar, then both sides must agree.
for line in ('firmware_rev: 0x1F', 'firmware_rev: 017', 'firmware_rev: 1_000', 'firmware_rev: 1:00', 'firmware_rev: +3',
             'firmware_rev: 0o7', 'firmware_rev: !!int "3"', 'firmware_rev: yes', 'firmware_rev: ~', 'firmware_rev: -0'):
    safe, loader, text = from_text(base, line)
    ours = yaml.load(text, Loader=loader)
    same = safe == ours
    s, m = source(copy.deepcopy(safe)), mapper(copy.deepcopy(ours))
    ok = same and s[0] == m[0] and (m[0] != 'accept' or m[1] == golden)
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} Y {line!r}: value={safe['entity']['firmware_rev']!r} loaders_agree={same} source={s[0]} mapper={m[0]}")

# Recorded divergence (not an expectation failure): the source also bounds the derived
# firmware_version string to 63 bytes; the mapper does not derive it.
huge = 10 ** 60
s, m = source(with_entity(base, firmware_rev=huge)), mapper(with_entity(base, firmware_rev=huge))
print(f"INFO D1 firmware_rev: 10**60 (61 digits): source={s[0]} ({s[1] if s[0] != 'accept' else ''}) mapper={m[0]}")

print(f"{sum(results)}/{len(results)} expectations held")
sys.exit(0 if all(results) else 1)
